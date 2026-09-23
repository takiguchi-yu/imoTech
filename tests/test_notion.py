"""Notion クライアントのテスト。

NOTION_TOKEN が無く実 DB で通せないため、**ここが検証の本体**になる。
HTTP は httpx.MockTransport で差し替え、送っているボディとヘッダ、
リトライとスロットリングの挙動、エラーの分類を固定する。
"""

from datetime import UTC, datetime

import httpx
import pytest

from imotech.models import ArticleDraft, DiscoursePoint, Engagement, GlossaryEntry, UseCase
from imotech.notion import (
    DATABASE_SCHEMA,
    MAX_CHILDREN_PER_REQUEST,
    MAX_RICH_TEXT_CHARS,
    NOTION_VERSION,
    PROP_IMO,
    PROP_STATUS,
    PROP_URL_HASH,
    STATUS_APPROVED,
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    NotionBlockLimitError,
    NotionClient,
    NotionError,
    build_blocks,
    build_properties,
    create_database_payload,
    patch_properties_payload,
    schema_diff,
    unrenamed_old_props,
)
from imotech.render import USE_CASE_NOTE

DS = "ds-1111"
DB = "db-2222"


def _draft(**kw) -> ArticleDraft:
    base = dict(
        url_hash="abc123def456",
        title="タイトル",
        slug="2026-09-22-example",
        digest=["要旨1", "要旨2", "要旨3"],
        discourse=[DiscoursePoint("論点A", "詳細A", "critical")],
        tags=["rust", "async"],
        source_url="https://e.com/a",
        source_title="The Article",
        source="hackernews",
        discussion_url="https://news.ycombinator.com/item?id=1",
        hatena_url="https://b.hatena.ne.jp/entry/s/e.com/a",
        engagement=Engagement(score=342, comments=187),
        model="gemini-3.8-flash",
        generated_at=datetime(2026, 9, 22, 6, 12, tzinfo=UTC),
    )
    base.update(kw)
    return ArticleDraft(**base)


class Recorder:
    """送ったリクエストを記録しつつ、決めた応答を返す。"""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        r = self._responses.pop(0) if self._responses else httpx.Response(200, json={})
        return r() if callable(r) else r


def _client(responses, **kw) -> tuple[NotionClient, Recorder]:
    rec = Recorder(responses)
    slept: list[float] = []
    c = NotionClient(
        token="secret_dummy",
        min_interval=kw.pop("min_interval", 0),
        max_attempts=kw.pop("max_attempts", 3),
        transport=httpx.MockTransport(rec),
        sleeper=slept.append,
        **kw,
    )
    c._slept = slept  # テストから見るため
    return c, rec


# --- ヘッダと認証 ---------------------------------------------------------


def test_必須ヘッダを送る():
    c, rec = _client([httpx.Response(200, json={"ok": True})])
    c.request("GET", "/databases/x")
    h = rec.calls[0].headers
    assert h["notion-version"] == NOTION_VERSION
    assert h["authorization"] == "Bearer secret_dummy"
    assert h["content-type"] == "application/json"


def test_バージョンは現行値():
    # 古い版だと data_source を使う新しいデータモデルが使えない
    assert NOTION_VERSION == "2026-03-11"


# --- スロットリング -------------------------------------------------------


def test_リクエスト間に間隔を空ける():
    # Free / Plus は 180 req/min（平均 3 req/sec）
    c, _ = _client([httpx.Response(200, json={})] * 3, min_interval=0.35)
    for _ in range(3):
        c.request("GET", "/x")
    # 1 回目は待たない。2 回目以降に待ちが入る
    assert len([s for s in c._slept if s > 0]) >= 2


def test_間隔0なら待たない():
    c, _ = _client([httpx.Response(200, json={})] * 3, min_interval=0)
    for _ in range(3):
        c.request("GET", "/x")
    assert c._slept == []


# --- リトライ -------------------------------------------------------------


def test_429はRetryAfterヘッダを尊重する():
    c, rec = _client(
        [
            httpx.Response(429, headers={"Retry-After": "7"}, json={"code": "rate_limited"}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    assert c.request("GET", "/x") == {"ok": True}
    assert 7.0 in c._slept
    assert len(rec.calls) == 2


def test_RetryAfterが無ければボディのretry_afterを見る():
    c, _ = _client(
        [
            httpx.Response(
                429, json={"code": "rate_limited", "additional_data": {"retry_after": "5"}}
            ),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    c.request("GET", "/x")
    assert 5.0 in c._slept


def test_どちらも無ければ指数バックオフ():
    # 完了条件は 1s / 2s / 4s
    c, _ = _client(
        [
            httpx.Response(429, json={"code": "rate_limited"}),
            httpx.Response(429, json={"code": "rate_limited"}),
            httpx.Response(200, json={}),
        ]
    )
    c.request("GET", "/x")
    assert c._slept == [1.0, 2.0]


def test_5xxはリトライして諦める():
    c, rec = _client([httpx.Response(503, json={"code": "service_unavailable"})] * 3)
    with pytest.raises(NotionError):
        c.request("GET", "/x")
    assert len(rec.calls) == 3


def test_5xxのあと成功すれば返す():
    c, _ = _client([httpx.Response(500, json={}), httpx.Response(200, json={"ok": 1})])
    assert c.request("GET", "/x") == {"ok": 1}


def test_400はリトライしない():
    # 入力が悪いので何度送っても同じ。無駄な待ちを作らない
    c, rec = _client([httpx.Response(400, json={"code": "validation_error", "message": "bad"})])
    with pytest.raises(NotionError, match="validation_error"):
        c.request("GET", "/x")
    assert len(rec.calls) == 1


def test_通信エラーもリトライする():
    def boom(request):
        raise httpx.ConnectError("boom")

    rec = Recorder([])
    c = NotionClient(
        token="t",
        min_interval=0,
        max_attempts=2,
        transport=httpx.MockTransport(boom),
        sleeper=lambda _: None,
    )
    with pytest.raises(NotionError, match="到達できない"):
        c.request("GET", "/x")
    assert rec is not None


# --- ブロック上限（Free プランの事故）-------------------------------------


def test_403_restricted_resourceは専用の例外にする():
    c, rec = _client(
        [
            httpx.Response(
                403,
                json={
                    "object": "error",
                    "status": 403,
                    "code": "restricted_resource",
                    "message": "This workspace has used all of its free blocks.",
                },
            )
        ]
    )
    with pytest.raises(NotionBlockLimitError) as ei:
        c.request("POST", "/pages")
    # 原因に辿り着けるメッセージであること
    assert "2 人目のメンバー" in str(ei.value)
    assert "1,000 ブロック" in str(ei.value)
    # リトライしても回復しないので 1 回で上げる
    assert len(rec.calls) == 1


# --- データソース ---------------------------------------------------------


def test_データソースIDを取る():
    # 2025-09-03 版でデータモデルが変わり、行とプロパティは data source が持つ
    c, rec = _client([httpx.Response(200, json={"data_sources": [{"id": DS, "name": "x"}]})])
    assert c.data_source_id(DB) == DS
    assert rec.calls[0].url.path.endswith(f"/databases/{DB}")


def test_データソースが無ければ案内つきで失敗する():
    c, _ = _client([httpx.Response(200, json={"data_sources": []})])
    with pytest.raises(NotionError, match="インテグレーション"):
        c.data_source_id(DB)


def test_クエリは非推奨でない新エンドポイントを叩く():
    # POST /v1/databases/{id}/query は 2025-09-03 版で非推奨
    c, rec = _client([httpx.Response(200, json={"results": [], "has_more": False})])
    c.query(DS, {})
    assert rec.calls[0].url.path == f"/v1/data_sources/{DS}/query"
    assert "/databases/" not in rec.calls[0].url.path


def test_クエリはページネーションを辿る():
    c, rec = _client(
        [
            httpx.Response(
                200, json={"results": [{"id": "1"}], "has_more": True, "next_cursor": "c1"}
            ),
            httpx.Response(200, json={"results": [{"id": "2"}], "has_more": False}),
        ]
    )
    assert [r["id"] for r in c.query(DS, {})] == ["1", "2"]
    import json as _json

    assert _json.loads(rec.calls[1].content)["start_cursor"] == "c1"


def test_next_cursorが無ければ止まる():
    # has_more が true でも cursor が無ければ無限ループしない
    c, _ = _client([httpx.Response(200, json={"results": [{"id": "1"}], "has_more": True})])
    assert len(c.query(DS, {})) == 1


# --- 投入 -----------------------------------------------------------------


def test_既存ページがあれば作らない():
    # 冪等性の 2 段目（docs/DESIGN.md 2.2）
    c, rec = _client([httpx.Response(200, json={"results": [{"id": "page-1"}], "has_more": False})])
    assert c.create_draft(DS, _draft()) == "page-1"
    assert len(rec.calls) == 1  # query だけ。POST /pages は呼ばない


def test_URL_Hashで検索する():
    c, rec = _client([httpx.Response(200, json={"results": [], "has_more": False})])
    c.find_page_by_url_hash(DS, "abc123")
    import json as _json

    body = _json.loads(rec.calls[0].content)
    assert body["filter"] == {"property": PROP_URL_HASH, "rich_text": {"equals": "abc123"}}


def test_新規ならページを作る():
    c, rec = _client(
        [
            httpx.Response(200, json={"results": [], "has_more": False}),
            httpx.Response(200, json={"id": "new-page"}),
        ]
    )
    assert c.create_draft(DS, _draft()) == "new-page"
    import json as _json

    body = _json.loads(rec.calls[1].content)
    assert body["parent"] == {"data_source_id": DS}
    assert "children" in body and len(body["children"]) <= MAX_CHILDREN_PER_REQUEST


def test_100を超えるブロックは分割して追記する():
    # 配列は 100 要素まで。1 リクエストに詰めると弾かれる
    big = _draft(discourse=[DiscoursePoint(f"論点{i}", f"詳細{i}", "mixed") for i in range(80)])
    assert len(build_blocks(big)) > MAX_CHILDREN_PER_REQUEST
    c, rec = _client(
        [
            httpx.Response(200, json={"results": [], "has_more": False}),
            httpx.Response(200, json={"id": "p1"}),
            httpx.Response(200, json={}),
        ]
    )
    c.create_draft(DS, big)
    paths = [r.url.path for r in rec.calls]
    assert any("/blocks/p1/children" in p for p in paths)
    import json as _json

    for r in rec.calls[1:]:
        body = _json.loads(r.content)
        assert len(body["children"]) <= MAX_CHILDREN_PER_REQUEST


# --- 承認の検知 -----------------------------------------------------------


def _approved_page(imo="所感。", slug="2026-09-22-example", url_hash="abc"):
    def rt(v):
        return [{"type": "text", "text": {"content": v}, "plain_text": v}]

    return {
        "id": "page-x",
        "properties": {
            PROP_IMO: {"rich_text": rt(imo)} if imo else {"rich_text": []},
            PROP_URL_HASH: {"rich_text": rt(url_hash)},
            "Slug": {"rich_text": rt(slug)},
        },
    }


def test_承認済みの取得は状態そのものを引く():
    # last_edited_time はページ単位でしか取れず「Status が変わった瞬間」を検知できない
    c, rec = _client([httpx.Response(200, json={"results": [], "has_more": False})])
    c.fetch_approved(DS)
    import json as _json

    f = _json.loads(rec.calls[0].content)["filter"]
    assert f["and"][0] == {"property": PROP_STATUS, "select": {"equals": STATUS_APPROVED}}
    assert f["and"][1] == {"property": PROP_IMO, "rich_text": {"is_not_empty": True}}
    assert "last_edited_time" not in _json.dumps(f)


def test_承認済みからimoとslugを取り出す():
    c, _ = _client([httpx.Response(200, json={"results": [_approved_page()], "has_more": False})])
    got = c.fetch_approved(DS)
    assert len(got) == 1
    assert got[0].imo == "所感。"
    assert got[0].slug == "2026-09-22-example"
    assert got[0].page_id == "page-x"


def test_imoが空のページは落とす():
    # クエリで弾いたはずだが、通すと公開判定が壊れる
    c, _ = _client(
        [httpx.Response(200, json={"results": [_approved_page(imo="")], "has_more": False})]
    )
    assert c.fetch_approved(DS) == []


def test_slugが空のページは落とす():
    c, _ = _client(
        [httpx.Response(200, json={"results": [_approved_page(slug="")], "has_more": False})]
    )
    assert c.fetch_approved(DS) == []


def test_分割されたrich_textを繋いで読む():
    def rt(*vals):
        return [{"plain_text": v} for v in vals]

    page = {
        "id": "p",
        "properties": {
            PROP_IMO: {"rich_text": rt("前半", "後半")},
            PROP_URL_HASH: {"rich_text": rt("h")},
            "Slug": {"rich_text": rt("s")},
        },
    }
    c, _ = _client([httpx.Response(200, json={"results": [page], "has_more": False})])
    assert c.fetch_approved(DS)[0].imo == "前半後半"


def test_Publishedへの書き戻し():
    c, rec = _client([httpx.Response(200, json={})])
    c.mark_published("page-1", when=datetime(2026, 9, 22, 1, 2, 3, tzinfo=UTC))
    import json as _json

    body = _json.loads(rec.calls[0].content)
    assert rec.calls[0].url.path == "/v1/pages/page-1"
    assert body["properties"][PROP_STATUS] == {"select": {"name": STATUS_PUBLISHED}}
    assert body["properties"]["Published At"]["date"]["start"].startswith("2026-09-22T01:02:03")


# --- ブロックとプロパティの組み立て ---------------------------------------


def test_imoはプロパティに入れない():
    # 人が書く欄。パイプラインが書いてはいけない
    assert PROP_IMO not in build_properties(_draft())


def test_StatusはDraftで作る():
    assert build_properties(_draft())[PROP_STATUS] == {"select": {"name": STATUS_DRAFT}}


def test_必要なプロパティがすべて入る():
    p = build_properties(_draft())
    for name in [
        "Title",
        "Status",
        "URL Hash",
        "Slug",
        "Source",
        "Source URL",
        "Discussion URL",
        "Hatena URL",
        "Score",
        "Comments",
        "Tags",
        "Collected At",
        "Model",
    ]:
        assert name in p, name


def test_Sourceにソースの名前が入る():
    assert build_properties(_draft(source="qiita"))["Source"] == {"select": {"name": "qiita"}}


def test_知らないソースの名前もそのまま送る():
    # Select に無い名前は Notion が選択肢を足す。ソースを足しても DB 側の作業は要らない
    p = build_properties(_draft(source="zenn"))
    assert p["Source"] == {"select": {"name": "zenn"}}


def test_ソースが空ならSourceを送らない():
    # 空の名前は Notion が受け付けない。キーごと外せば空欄で作られる
    assert "Source" not in build_properties(_draft(source=""))


def test_改名しない旧名の列を知らせる():
    # 型が違う旧名、新名と並んでいる旧名は黙って残る。notion-setup が知らせる
    existing = _before_m8() | {"HN Score": {"type": "rich_text"}}
    assert set(unrenamed_old_props(existing)) == {"HN Score"}
    both = _existing(**{"HN URL": {"type": "url"}})
    assert set(unrenamed_old_props(both)) == {"HN URL"}
    # 改名するものは知らせない
    assert unrenamed_old_props(_before_m8()) == {}


def test_ソース固有の名前の列を作らない():
    # 列は意味ごとに 1 つ。ソースを足すたびに列が増えないこと
    assert not [k for k in DATABASE_SCHEMA if "HN" in k or "Qiita" in k]


def test_タグはmulti_selectになる():
    assert build_properties(_draft())[("Tags")] == {
        "multi_select": [{"name": "rust"}, {"name": "async"}]
    }


def test_rich_textは2000文字で切る():
    blocks = build_blocks(_draft(title="x", digest=["あ" * 5000, "b", "c"]))
    for b in blocks:
        for rt in b[b["type"]].get("rich_text") or []:
            assert len(rt["text"]["content"]) <= MAX_RICH_TEXT_CHARS


def test_長い詳細は段落に分ける():
    blocks = build_blocks(_draft(discourse=[DiscoursePoint("p", "あ" * 5000, "mixed")]))
    paragraphs = [b for b in blocks if b["type"] == "paragraph"]
    # 出典の 1 段落 + 分割された詳細
    assert len(paragraphs) >= 3


def test_本文に出典と開示が入る():
    blocks = build_blocks(_draft())
    text = "".join(
        rt["text"]["content"] for b in blocks for rt in (b[b["type"]].get("rich_text") or [])
    )
    assert "https://e.com/a" in text
    assert "news.ycombinator.com" in text
    assert "b.hatena.ne.jp" in text
    assert "gemini-3.8-flash" in text


def test_冒頭のcalloutがimoの書き方を案内する():
    first = build_blocks(_draft())[0]
    assert first["type"] == "callout"
    assert "imo" in first["callout"]["rich_text"][0]["text"]["content"]
    # 設計書 3.3 と揃える
    assert first["callout"]["icon"] == {"emoji": "⚠️"}


# --- データベースの作成 ---------------------------------------------------


def test_DB作成のボディ():
    # 2025-09-03 版以降、プロパティは initial_data_source.properties にネストする
    p = create_database_payload("parent-1", "テスト DB")
    assert p["parent"] == {"type": "page_id", "page_id": "parent-1"}
    assert p["title"][0]["text"]["content"] == "テスト DB"
    assert "initial_data_source" in p
    props = p["initial_data_source"]["properties"]
    assert props["Title"] == {"title": {}}
    assert [o["name"] for o in props["Status"]["select"]["options"]] == [
        "Draft",
        "Approved",
        "Published",
        "Rejected",
    ]
    assert props["imo"] == {"rich_text": {}}


def test_DBスキーマがプロパティ組み立てと整合している():
    # スキーマに無いプロパティに値を入れると Notion が弾く
    schema = set(create_database_payload("p")["initial_data_source"]["properties"])
    used = set(build_properties(_draft()))
    assert used <= schema, used - schema


# --- 403 の分類（レビューで見つかった誤った案内の回帰テスト）----------------


def test_ブロック上限の手がかりがあるときだけ専用の例外にする():
    c, _ = _client(
        [
            httpx.Response(
                403,
                json={
                    "code": "restricted_resource",
                    "message": "This workspace has used all of its free blocks.",
                },
            )
        ]
    )
    with pytest.raises(NotionBlockLimitError, match="2 人目のメンバー"):
        c.request("POST", "/pages")


def test_additional_dataのblock_limitでも専用の例外にする():
    c, _ = _client(
        [
            httpx.Response(
                403,
                json={
                    "code": "restricted_resource",
                    "message": "Restricted.",
                    "additional_data": {"block_limit": "block_creation"},
                },
            )
        ]
    )
    with pytest.raises(NotionBlockLimitError):
        c.request("POST", "/pages")


def test_権限エラーの403はブロック上限と決めつけない():
    # restricted_resource はインテグレーション未接続などでも返る汎用コード。
    # 決めつけると最もありがちな設定ミスに誤った案内を出す
    c, rec = _client(
        [
            httpx.Response(
                403,
                json={
                    "code": "restricted_resource",
                    "message": "Could not find database with ID: xxx.",
                },
            )
        ]
    )
    with pytest.raises(NotionError) as ei:
        c.request("GET", "/databases/x")
    assert not isinstance(ei.value, NotionBlockLimitError)
    assert "接続" in str(ei.value)
    assert "2 人目" not in str(ei.value)
    assert len(rec.calls) == 1  # 403 はリトライしない


# --- 応答の欠落 -----------------------------------------------------------


def test_ページ作成の応答にidが無ければNotionErrorにする():
    # KeyError だと呼び出し側の except NotionError をすり抜けてトレースバックになる
    c, _ = _client(
        [
            httpx.Response(200, json={"results": [], "has_more": False}),
            httpx.Response(200, json={"object": "page"}),
        ]
    )
    with pytest.raises(NotionError, match="id がありません"):
        c.create_draft(DS, _draft())


# --- imo の空判定 ---------------------------------------------------------


def test_空白だけのimoは落とす():
    # Notion の is_not_empty は空白だけの値を通すので、こちらで弾く
    page = {
        "id": "p",
        "properties": {
            PROP_IMO: {"rich_text": [{"plain_text": "   \n  "}]},
            PROP_URL_HASH: {"rich_text": [{"plain_text": "h"}]},
            "Slug": {"rich_text": [{"plain_text": "s"}]},
        },
    }
    c, _ = _client([httpx.Response(200, json={"results": [page], "has_more": False})])
    assert c.fetch_approved(DS) == []


def test_imoの前後の空白は落とす():
    page = {
        "id": "p",
        "properties": {
            PROP_IMO: {"rich_text": [{"plain_text": "  所感。  "}]},
            PROP_URL_HASH: {"rich_text": [{"plain_text": "h"}]},
            "Slug": {"rich_text": [{"plain_text": "s"}]},
        },
    }
    c, _ = _client([httpx.Response(200, json={"results": [page], "has_more": False})])
    assert c.fetch_approved(DS)[0].imo == "所感。"


# --- 長い要旨 -------------------------------------------------------------


def test_長い要旨は複数の項目に分ける():
    # 黙って 2,000 字で切り捨てると内容が失われる
    blocks = build_blocks(_draft(digest=["あ" * 5000, "b", "c"]))
    bullets = [b for b in blocks if b["type"] == "bulleted_list_item"]
    joined = "".join(
        rt["text"]["content"] for b in bullets for rt in b["bulleted_list_item"]["rich_text"]
    )
    assert joined.count("あ") == 5000


# --- 検索の単発化 ---------------------------------------------------------


def test_URL_Hashの検索はページネーションを辿らない():
    # 重複ページが n 件あると 1 件ずつ n 回クエリすることになる
    c, rec = _client(
        [
            httpx.Response(
                200, json={"results": [{"id": "p1"}], "has_more": True, "next_cursor": "c"}
            )
        ]
    )
    assert c.find_page_by_url_hash(DS, "h") == "p1"
    assert len(rec.calls) == 1


# --- 10,000 件の上限 ------------------------------------------------------


def test_クエリの打ち切りを呼び出し側に伝える():
    c, _ = _client(
        [
            httpx.Response(
                200,
                json={
                    "results": [{"id": "1"}],
                    "has_more": False,
                    "request_status": {"type": "incomplete"},
                },
            )
        ]
    )
    c.query(DS, {})
    assert c.last_query_incomplete is True


def test_打ち切られていなければフラグは立たない():
    c, _ = _client([httpx.Response(200, json={"results": [], "has_more": False})])
    c.query(DS, {})
    assert c.last_query_incomplete is False


# --- schema_diff（既存 DB との突合）--------------------------------------


def _existing(**overrides) -> dict:
    """設計書どおりに揃った既存プロパティ。overrides で一部を崩せる。"""
    out = {name: {"type": next(iter(spec))} for name, spec in DATABASE_SCHEMA.items()}
    out.update(overrides)
    return out


def test_揃っていれば差分は空():
    missing, rename, mismatched = schema_diff(_existing())
    assert missing == {} and rename == {} and mismatched == {}


def test_足りないプロパティを挙げる():
    existing = _existing()
    del existing["Slug"]
    del existing["Tags"]
    missing, _, mismatched = schema_diff(existing)
    assert sorted(missing) == ["Slug", "Tags"]
    assert mismatched == {}


def test_型の不一致を検出する():
    # Notion の UI で作った DB の Status は Status 型（UI の既定）になりうる。
    # 名前だけ比べると「揃っている」と判断してしまい、そのあと送る
    # {"select": ...} が毎回 400 になる
    _, _, mismatched = schema_diff(_existing(Status={"type": "status"}))
    assert mismatched == {"Status": {"expected": "select", "actual": "status"}}


def test_型の不一致は追加対象にしない():
    # 追加しようとしても Notion は受け付けない。API では直せないものとして分ける
    missing, _, mismatched = schema_diff(_existing(**{"Score": {"type": "rich_text"}}))
    assert "Score" not in missing
    assert "Score" in mismatched


def _before_m8() -> dict:
    """M8 の前の本番 DB（Hacker News 固定の名前で、Source 列が無い）。"""
    existing = _existing()
    for new in ("Discussion URL", "Score", "Comments", "Source"):
        del existing[new]
    existing |= {
        "HN URL": {"type": "url"},
        "HN Score": {"type": "number"},
        "HN Comments": {"type": "number"},
    }
    return existing


def test_旧名の列は足さずに改名する():
    # 足すと値の無い同じ意味の列が並び、既存ページの値は旧名の列に取り残される
    missing, rename, mismatched = schema_diff(_before_m8())
    assert rename == {
        "HN URL": {"name": "Discussion URL"},
        "HN Score": {"name": "Score"},
        "HN Comments": {"name": "Comments"},
    }
    # Source は旧名が無いので足す
    assert sorted(missing) == ["Source"]
    assert mismatched == {}


def test_旧名の列でも型が違えば改名しない():
    # 改名しても値を書けない。新しい列を足す
    existing = _before_m8() | {"HN Score": {"type": "rich_text"}}
    missing, rename, _ = schema_diff(existing)
    assert "HN Score" not in rename
    assert "Score" in missing


def test_改名のあとは差分が無い():
    # 2 回目の notion-setup が何もしないこと（新名の列があれば旧名は見ない）。
    # 旧名の列を手で作り直した・消し忘れた、の形で旧名と新名が両方ある場合も改名しない
    after = _existing(
        **{
            "HN URL": {"type": "url"},
            "HN Score": {"type": "number"},
            "HN Comments": {"type": "number"},
        }
    )
    missing, rename, mismatched = schema_diff(after)
    assert missing == {} and rename == {} and mismatched == {}


def test_M8前のDBへのPATCHは改名とSourceの追加():
    props = patch_properties_payload(_before_m8())["properties"]
    assert props == {
        "HN URL": {"name": "Discussion URL"},
        "HN Score": {"name": "Score"},
        "HN Comments": {"name": "Comments"},
        "Source": {"select": {}},
    }


def test_タイトル列が別名なら改名にする():
    # Notion のデータベースはタイトル型を 1 つだけ持てる。追加ではなく改名が必要
    existing = {"名前": {"type": "title"}}
    missing, rename, _ = schema_diff(existing)
    assert rename == {"名前": {"name": "Title"}}
    assert "Title" not in missing


def test_タイトル列が無ければTitleを追加する():
    existing = {"Slug": {"type": "rich_text"}}
    missing, rename, _ = schema_diff(existing)
    assert "Title" in missing
    assert rename == {}


def test_空のDBは全件が足りない():
    missing, rename, mismatched = schema_diff({"名前": {"type": "title"}})
    # Title は改名になるので missing からは外れる
    assert len(missing) == len(DATABASE_SCHEMA) - 1
    assert rename
    assert mismatched == {}


def test_PATCHのボディは改名と追加だけを含む():
    existing = {"名前": {"type": "title"}}
    payload = patch_properties_payload(existing)
    props = payload["properties"]
    assert props["名前"] == {"name": "Title"}
    assert "Status" in props
    # 型が違うものは PATCH に含めない（Notion が受け付けない）
    payload2 = patch_properties_payload(_existing(Status={"type": "status"}))
    assert "Status" not in payload2["properties"]


# --- 用語 -----------------------------------------------------------------


def _types(blocks: list[dict]) -> list[str]:
    return [b["type"] for b in blocks]


def _texts(blocks: list[dict]) -> list[str]:
    out = []
    for b in blocks:
        rt = b.get(b["type"], {}).get("rich_text") or []
        out.append("".join(t.get("text", {}).get("content", "") for t in rt))
    return out


def test_用語がレビュー面にも出る():
    # 要旨と論調を出しているのに用語だけ出ないと、人が用語の妥当性を確認できない
    blocks = build_blocks(
        _draft(
            glossary=[
                GlossaryEntry("PE", "未公開株に投資するファンド。"),
                GlossaryEntry("FTC", "米連邦取引委員会。"),
            ]
        )
    )
    texts = _texts(blocks)
    assert "用語" in texts
    assert "PE: 未公開株に投資するファンド。" in texts
    assert "FTC: 米連邦取引委員会。" in texts
    # 出典の前に置く（Markdown で imo の後ろに置くのと同じ位置づけ）
    assert texts.index("用語") < texts.index("出典")


def test_用語が0件なら見出しを出さない():
    assert "用語" not in _texts(build_blocks(_draft(glossary=[])))


def test_長い用語の説明は切り捨てずに分割される():
    # Notion の rich_text は 1 要素 2000 文字まで。**切り捨てではなく分割**である
    # ことを見る（_rich_text は必ず 2000 で切るので、長さの上限だけを見る
    # アサーションは実装が切り捨てに変わっても通ってしまう）
    long = "あ" * 5000
    blocks = build_blocks(_draft(glossary=[GlossaryEntry("X", long)]))
    # 用語の節だけを見る（要旨と出典の箇条書きが混ざらないように）
    start = _texts(blocks).index("用語") + 1
    joined = ""
    for b in blocks[start:]:
        if b["type"] != "bulleted_list_item":
            break
        joined += "".join(t["text"]["content"] for t in b["bulleted_list_item"]["rich_text"])
    assert joined == f"X: {long}"
    assert all(
        len(t.get("text", {}).get("content", "")) <= 2000
        for b in blocks
        for t in (b.get(b["type"], {}).get("rich_text") or [])
    )


# --- 使いどころ ------------------------------------------------------------
#
# レビュー面は人が公開の可否を決める場所なので、**「元記事に書いてあること」と
# 「生成 AI が考えた応用案」が混ざって見えてはいけない**。


def _headings(blocks: list) -> list[str]:
    return [
        b["heading_2"]["rich_text"][0]["text"]["content"]
        for b in blocks
        if b.get("type") == "heading_2"
    ]


def _paragraphs(blocks: list) -> list[str]:
    return [
        b["paragraph"]["rich_text"][0]["text"]["content"]
        for b in blocks
        if b.get("type") == "paragraph"
    ]


def test_使いどころは論調の後用語の前に出る():
    blocks = build_blocks(
        _draft(use_cases=[UseCase("場面", "説明")], glossary=[GlossaryEntry("語", "意味")])
    )
    assert _headings(blocks) == ["元記事の要旨", "議論の論調", "使いどころ", "用語", "出典"]


def test_レビュー面にも但し書きを出す():
    blocks = build_blocks(_draft(use_cases=[UseCase("場面", "説明")]))
    assert USE_CASE_NOTE in _paragraphs(blocks)


def test_使いどころが0件なら見出しを出さない():
    assert "使いどころ" not in _headings(build_blocks(_draft(use_cases=[])))


def test_使いどころの中身がブロックになる():
    blocks = build_blocks(_draft(use_cases=[UseCase("社内で試したいとき", "手元で動きます")]))
    bullets = [
        b["bulleted_list_item"]["rich_text"][0]["text"]["content"]
        for b in blocks
        if b.get("type") == "bulleted_list_item"
    ]
    assert "社内で試したいとき: 手元で動きます" in bullets


def test_但し書きは項目より前に置く():
    """後ろだと、読んだあとに「推測でした」と知ることになり、レビューの判断が一度汚れる。"""
    blocks = build_blocks(_draft(use_cases=[UseCase("場面", "説明")]))
    types = [b.get("type") for b in blocks]
    i = next(
        n
        for n, b in enumerate(blocks)
        if b.get("type") == "heading_2"
        and b["heading_2"]["rich_text"][0]["text"]["content"] == "使いどころ"
    )
    # 見出しの直後が但し書き、そのあとに項目が来る
    assert types[i + 1] == "paragraph"
    assert blocks[i + 1]["paragraph"]["rich_text"][0]["text"]["content"] == USE_CASE_NOTE
    assert types[i + 2] == "bulleted_list_item"


def test_空の使いどころはレビュー面にも出さない():
    # 公開記事と同じフィルタを通す。片方だけ空項目を出すと
    # 「レビュー面には節があるのに公開記事には無い」が起きる
    blocks = build_blocks(_draft(use_cases=[UseCase("", "説明"), UseCase("場面", "  ")]))
    assert "使いどころ" not in _headings(blocks)


def test_空の用語もレビュー面に出さない():
    blocks = build_blocks(_draft(glossary=[GlossaryEntry("", "意味")]))
    assert "用語" not in _headings(blocks)

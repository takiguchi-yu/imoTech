"""Qiita クライアントのテスト。

ネットワークは httpx.MockTransport で差し替える。Hacker News との違い
（記事そのものが Story／議論の場所が記事ページ自身／LGTM で絞れない／
**記事 URL に著者のハンドルが入る**）をここで担保する。
"""

from datetime import UTC, datetime, timedelta, timezone

import httpx
import pytest

from imotech.models import SourceRef, Thresholds
from imotech.sources import ReactionSource, StoryFeed, profile_url_patterns
from imotech.sources.qiita import PER_PAGE, PROFILE_URL_RE, SEARCH_MIN_STOCKS, Qiita

ITEM_ID = "a" * 20
# window_hours=24 の内側に入る時刻。**実行日に依存させない**ため現在時刻から作る。
# Qiita は +09:00 付きで返すので、そのタイムゾーンで書く
JST = timezone(timedelta(hours=9))
RECENT = (datetime.now(UTC) - timedelta(hours=1)).astimezone(JST).isoformat()
OLD = "2020-01-01T10:00:00+09:00"


def _item(iid=ITEM_ID, *, likes=50, comments=0, user="alice", created=RECENT, private=False):
    return {
        "id": iid,
        "url": f"https://qiita.com/{user}/items/{iid}",
        "title": f"title {iid}",
        "likes_count": likes,
        "stocks_count": 10,
        "comments_count": comments,
        "created_at": created,
        "updated_at": created,
        "user": {"id": user, "permanent_id": 1},
        "private": private,
    }


def _comment(cid="c" * 20, *, body="<p>なるほど</p>", user="bob"):
    return {
        "id": cid,
        "body": "なるほど",
        "rendered_body": body,
        "user": {"id": user, "permanent_id": 2},
        "created_at": RECENT,
    }


def _client(handler):
    return Qiita(transport=httpx.MockTransport(handler))


def _routed(*, items=None, item=None, comments=None):
    """パスごとに応答を返すハンドラ。"""

    def handler(request):
        path = request.url.path
        if path.endswith("/comments"):
            return httpx.Response(200, json=comments if comments is not None else [])
        if path == "/api/v2/items":
            return httpx.Response(200, json=items if items is not None else [])
        return httpx.Response(200, json=item if item is not None else _item())

    return handler


# --- Protocol ---------------------------------------------------------------


def test_Protocolを満たす():
    with _client(_routed()) as q:
        assert isinstance(q, StoryFeed)
        assert isinstance(q, ReactionSource)


def test_コメント数を見ない閾値を既定で持つ():
    # Qiita はコメントがほぼ付かない（実測で 82% が 0 件）。共通の既定
    # （comments>=30）を当てると 1 件も通らないので、ソース側で持つ
    assert Qiita.default_thresholds == Thresholds(min_score=30, min_comments=0)
    assert Qiita.default_thresholds.min_comments == 0


# --- PII --------------------------------------------------------------------


def test_プロフィールURLは伏せ字の対象になる():
    from imotech.anonymize import PLACEHOLDER, scrub

    with _client(_routed()) as q:
        patterns = profile_url_patterns(q)
    out = scrub("see https://qiita.com/carol123 for more", frozenset(), patterns)
    assert "carol123" not in out
    assert PLACEHOLDER in out


def test_記事URLはプロフィールのパターンで丸ごと消さない():
    """出典のリンクが消えては困る。記事 URL 内のハンドルは `Story.author` 経由で伏せる。"""
    from imotech.anonymize import scrub

    with _client(_routed()) as q:
        patterns = profile_url_patterns(q)
    url = f"https://qiita.com/alice/items/{ITEM_ID}"
    assert scrub(f"see {url}", frozenset(), patterns) == f"see {url}"


def test_記事の著者を伏せ字に渡せる():
    """**PII の回帰テスト。** 記事プラットフォームでは URL 自体に著者名が入る。

    著者が 1 度もコメントしていなくても伏せる必要があるので、`Story.author` に入れる。
    """
    from imotech.anonymize import scrub_url

    with _client(_routed(items=[_item(user="carol123")])) as q:
        (story,) = q.fetch_stories()
    assert story.author == "carol123"
    # 反応が 1 件も無くても、著者を渡せば伏せられる
    assert "carol123" not in scrub_url(story.url, [], frozenset({story.author}))


@pytest.mark.parametrize(
    ("text", "hidden"),
    [
        ("https://qiita.com/alice", True),
        ("https://qiita.com/alice/", True),
        ("http://qiita.com/alice", True),
        ("https://www.qiita.com/alice", True),
        (f"https://qiita.com/alice/items/{ITEM_ID}", False),
    ],
)
def test_プロフィールURLのパターンは記事URLに当たらない(text, hidden):
    assert bool(PROFILE_URL_RE.search(text)) is hidden


# --- StoryFeed --------------------------------------------------------------


def test_記事そのものがStoryになる():
    with _client(_routed(items=[_item()])) as q:
        (story,) = q.fetch_stories()
    assert story.ref == SourceRef("qiita", ITEM_ID)
    # **議論の場所は記事ページ自身。** Hacker News と違いスレッドが別に無い
    assert story.discussion_url == story.url
    # 注目度は LGTM。ストック数は検索で絞るためだけに使う
    assert story.engagement.score == 50


def test_非公開記事は除外される():
    with _client(_routed(items=[_item(private=True), _item(iid="b" * 20)])) as q:
        got = q.fetch_stories()
    assert [s.ref.id for s in got] == ["b" * 20]


def test_期間の外の記事は除外される():
    # created: は日付単位なので、境界の記事を取りこぼさないよう 1 日広く問い合わせる。
    # 溢れた分はここで落とす
    with _client(_routed(items=[_item(created=OLD), _item(iid="b" * 20)])) as q:
        got = q.fetch_stories(window_hours=24)
    assert [s.ref.id for s in got] == ["b" * 20]


def test_収集時はLGTMで切らない():
    """**Qiita の記事は投稿直後に LGTM が付かない**（実測: 直近 24h で最大 6）。

    収集時の値で切ると候補が 1 件も残らない。絞り込みは熟成後の再評価に任せる。
    """
    with _client(_routed(items=[_item(likes=0), _item(iid="b" * 20, likes=80)])) as q:
        got = q.fetch_stories(min_points=10)
    assert {s.ref.id for s in got} == {"a" * 20, "b" * 20}


def test_LGTMの多い順に並ぶ():
    items = [_item(iid="a" * 20, likes=10), _item(iid="b" * 20, likes=99)]
    with _client(_routed(items=items)) as q:
        got = q.fetch_stories()
    assert [s.engagement.score for s in got] == [99, 10]


def test_必須項目を欠く記事は除外される():
    broken = {**_item(), "created_at": "not a date"}
    with _client(_routed(items=[broken])) as q:
        assert q.fetch_stories() == []


def test_1ページ未満なら次を取りに行かない():
    seen = []

    def handler(request):
        if request.url.path == "/api/v2/items":
            seen.append(int(dict(request.url.params)["page"]))
            return httpx.Response(200, json=[_item()])
        return httpx.Response(200, json=[])

    with _client(handler) as q:
        q.fetch_stories()
    assert seen == [1]


def test_満杯なら次のページを追う():
    seen = []

    def handler(request):
        page = int(dict(request.url.params)["page"])
        seen.append(page)
        # 満杯のページを返し続ける。max_pages で打ち切られるはず
        return httpx.Response(200, json=[_item(iid=f"{page:020d}")] * PER_PAGE)

    with _client(handler) as q:
        q.fetch_stories(max_pages=2)
    assert seen == [1, 2]


def test_limitで全体を切る():
    items = [_item(iid=f"{i:020d}", likes=i) for i in range(1, 6)]
    with _client(_routed(items=items)) as q:
        assert len(q.fetch_stories(limit=2)) == 2


# --- HTTP の失敗 -------------------------------------------------------------


def test_レート上限はリトライしない(monkeypatch):
    # Qiita の上限は時間単位でのリセット。数秒待っても回復しないので次回に回す
    monkeypatch.setattr("imotech.sources.qiita.time.sleep", lambda _: None)
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(429)

    with _client(handler) as q:
        assert q.fetch_stories() == []
    assert len(calls) == 1


def test_5xxは3回リトライして諦める(monkeypatch):
    monkeypatch.setattr("imotech.sources.qiita.time.sleep", lambda _: None)
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(503)

    with _client(handler) as q:
        assert q.fetch_stories() == []
    assert len(calls) == 3


@pytest.mark.parametrize("bad", [b"not json", b"{"])
def test_壊れた応答でも例外を投げない(monkeypatch, bad):
    monkeypatch.setattr("imotech.sources.qiita.time.sleep", lambda _: None)
    with _client(lambda r: httpx.Response(200, content=bad)) as q:
        assert q.fetch_stories() == []


# --- ReactionSource ----------------------------------------------------------


def test_コメントを取れる():
    handler = _routed(item=_item(comments=2), comments=[_comment(), _comment(cid="d" * 20)])
    with _client(handler) as q:
        story, reactions = q.fetch_reactions(SourceRef("qiita", ITEM_ID))
    assert story is not None
    assert [r.comment_id for r in reactions] == ["c" * 20, "d" * 20]
    # **20 桁の 16 進**。int では表せないので文字列で持つ
    assert all(isinstance(r.comment_id, str) for r in reactions)


def test_コメントはフラットとして扱う():
    # Qiita は返信の親子関係を API が返さない。全件 0 なら元の並び順が保たれる
    with _client(_routed(item=_item(comments=1), comments=[_comment()])) as q:
        _, (reaction,) = q.fetch_reactions(SourceRef("qiita", ITEM_ID))
    assert (reaction.depth, reaction.reply_count) == (0, 0)


def test_本文が空のコメントは捨てる():
    handler = _routed(item=_item(comments=2), comments=[_comment(body=""), _comment(cid="d" * 20)])
    with _client(handler) as q:
        _, reactions = q.fetch_reactions(SourceRef("qiita", ITEM_ID))
    assert [r.comment_id for r in reactions] == ["d" * 20]


def test_コメントが0件でも記事は返る():
    # これが Qiita の普通の状態（実測で 82%）。呼び出し側は論調なしの記事にする
    with _client(_routed(comments=[])) as q:
        story, reactions = q.fetch_reactions(SourceRef("qiita", ITEM_ID))
    assert story is not None
    assert reactions == []


def test_別のソースの候補には触らない():
    calls = []

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, json=_item())

    with _client(handler) as q:
        assert q.fetch_reactions(SourceRef("hackernews", "123")) == (None, [])
    assert calls == []


def test_記事が取れなければコメントも取りに行かない(monkeypatch):
    monkeypatch.setattr("imotech.sources.qiita.time.sleep", lambda _: None)
    calls = []

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(500)

    with _client(handler) as q:
        assert q.fetch_reactions(SourceRef("qiita", ITEM_ID)) == (None, [])
    assert not any(p.endswith("/comments") for p in calls)


# --- 認証 --------------------------------------------------------------------


def test_トークンを渡すとAuthorizationが付く():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers.get("Authorization")
        return httpx.Response(200, json=[])

    with Qiita(transport=httpx.MockTransport(handler), token="tok") as q:
        q.fetch_stories()
    assert seen["auth"] == "Bearer tok"


def test_トークンが無ければAuthorizationを付けない():
    # 非認証でも 60 req/h 使える。1 回の実行で使うのは数リクエスト
    seen = {}

    def handler(request):
        seen["auth"] = request.headers.get("Authorization")
        return httpx.Response(200, json=[])

    with _client(handler) as q:
        q.fetch_stories()
    assert seen["auth"] is None


# --- レート上限 --------------------------------------------------------------


def test_コメントが0件なら問い合わせない():
    """**実測で 82% がこれに当たる。** 非認証は 60 req/h しかないので、
    1 候補あたりのリクエストを 2 から 1 に減らす。"""
    paths = []

    def handler(request):
        paths.append(request.url.path)
        return httpx.Response(200, json=_item(comments=0))

    with _client(handler) as q:
        story, reactions = q.fetch_reactions(SourceRef("qiita", ITEM_ID))
    assert story is not None and reactions == []
    assert not any(p.endswith("/comments") for p in paths)


def test_403のレート超過はリトライしない(monkeypatch):
    # Qiita は超過時に 429 ではなく 403 + type: rate_limit_exceeded を返す（実測）
    monkeypatch.setattr("imotech.sources.qiita.time.sleep", lambda _: None)
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(
            403, json={"message": "Rate limit exceeded", "type": "rate_limit_exceeded"}
        )

    with _client(handler) as q:
        assert q.fetch_stories() == []
    assert len(calls) == 1


@pytest.mark.parametrize("status", [403, 404, 400])
def test_レート超過でない4xxはリトライしない(monkeypatch, status):
    """**待っても変わらないのに 1 件で 3 リクエスト食う。**

    非認証の 60 req/h が実運用の天井なので、無駄打ちが直接効く。
    403 は権限エラーでもあるので、本文の type でレート超過と見分ける。
    """
    monkeypatch.setattr("imotech.sources.qiita.time.sleep", lambda _: None)
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(status, json={"message": "no", "type": "forbidden"})

    with _client(handler) as q:
        assert q.fetch_stories() == []
    assert len(calls) == 1


def test_上限に達したら以降は撃たない(monkeypatch):
    """気づかず撃ち続けると、残りの候補ぶんが全部無駄になる。"""
    monkeypatch.setattr("imotech.sources.qiita.time.sleep", lambda _: None)
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(403, json={"type": "rate_limit_exceeded"})

    with _client(handler) as q:
        q.fetch_stories()
        assert q.fetch_reactions(SourceRef("qiita", ITEM_ID)) == (None, [])
        assert q.fetch_stories() == []
    assert len(calls) == 1


def test_残量が0のヘッダでも以降は撃たない():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(200, json=[], headers={"Rate-Remaining": "0", "Rate-Limit": "60"})

    with _client(handler) as q:
        q.fetch_stories()
        assert q.rate_remaining == 0
        q.fetch_stories()
    assert len(calls) == 1


def test_残量を覚える():
    def handler(request):
        return httpx.Response(200, json=[], headers={"Rate-Remaining": "42"})

    with _client(handler) as q:
        q.fetch_stories()
    assert q.rate_remaining == 42


def test_上限の警告は1度だけ出す(capsys, monkeypatch):
    # 候補の数だけ warn が並ぶとログが読めない
    monkeypatch.setattr("imotech.sources.qiita.time.sleep", lambda _: None)

    def handler(request):
        return httpx.Response(403, json={"type": "rate_limit_exceeded"})

    with _client(handler) as q:
        q.fetch_stories()
        q.fetch_reactions(SourceRef("qiita", ITEM_ID))
    assert capsys.readouterr().out.count("レート上限") == 1


def test_コメントの取得に失敗したら判定不能として返す():
    """**「取れなかった」を「0 件だった」と混同しない。**

    混同すると、議論のある記事が「反応なし」の記事として確定的に書き出され、
    候補は drafted になって二度と作り直されない。
    """

    def handler(request):
        if request.url.path.endswith("/comments"):
            return httpx.Response(403, json={"type": "rate_limit_exceeded"})
        return httpx.Response(200, json=_item(comments=9))

    with _client(handler) as q:
        # story も返さない。呼び出し側は候補を pending のまま次回に回す
        assert q.fetch_reactions(SourceRef("qiita", ITEM_ID)) == (None, [])


def test_コメントが本当に0件なら記事を返す():
    # 上のテストと対になる。0 件は正常な状態（実測で 82%）
    with _client(_routed(item=_item(comments=0))) as q:
        story, reactions = q.fetch_reactions(SourceRef("qiita", ITEM_ID))
    assert story is not None and reactions == []


def test_上限の警告に回復時刻と次の一手を書く(capsys, monkeypatch):
    """無人実行のログを後から読む人が、放っておけば直るのか設定を変えるべきかを判断できるように。"""
    monkeypatch.setattr("imotech.sources.qiita.time.sleep", lambda _: None)
    # 2026-09-23 17:08:46 JST にあたる UNIX 秒
    reset = int(datetime(2026, 9, 23, 8, 8, 46, tzinfo=UTC).timestamp())

    def handler(request):
        return httpx.Response(
            403, json={"type": "rate_limit_exceeded"}, headers={"Rate-Reset": str(reset)}
        )

    with _client(handler) as q:
        q.fetch_stories()
        assert q.rate_reset == reset
    out = capsys.readouterr().out
    assert "17:08（JST）以降" in out
    assert "IMOTECH_MAX_PROBES_PER_RUN" in out


def test_Rate_Resetが無くても警告は出る(capsys, monkeypatch):
    monkeypatch.setattr("imotech.sources.qiita.time.sleep", lambda _: None)
    with _client(lambda r: httpx.Response(403, json={"type": "rate_limit_exceeded"})) as q:
        q.fetch_stories()
    assert "レート上限" in capsys.readouterr().out


def test_壊れたレートヘッダは無視する():
    def handler(request):
        return httpx.Response(200, json=[], headers={"Rate-Remaining": "lots"})

    with _client(handler) as q:
        q.fetch_stories()
        assert q.rate_remaining is None
        # 2 回目も撃てる（壊れたヘッダで止まらない）
        q.fetch_stories()


def test_ページ間で重複した記事は1件にする():
    """ページを追っている間に新着が入るとオフセットがずれ、同じ記事が 2 ページに現れる。"""
    pages = {
        1: [_item(iid=f"{i:020d}") for i in range(PER_PAGE)],
        # 2 ページ目の先頭に 1 ページ目と同じ記事が混ざる
        2: [_item(iid=f"{PER_PAGE - 1:020d}"), _item(iid="z" * 20)],
    }

    def handler(request):
        page = int(dict(request.url.params)["page"])
        return httpx.Response(200, json=pages.get(page, []))

    with _client(handler) as q:
        got = q.fetch_stories(max_pages=2, limit=1000)
    ids = [s.ref.id for s in got]
    assert len(ids) == len(set(ids)) == PER_PAGE + 1


def test_タイトルが空の記事は除外される():
    # 見出しも slug も作れないので拾っても使えない
    with _client(_routed(items=[{**_item(), "title": "  "}, _item(iid="b" * 20)])) as q:
        assert [s.ref.id for s in q.fetch_stories()] == ["b" * 20]


def test_検索の問い合わせが仕様どおりか():
    """**外部との契約でいちばん壊れやすいところ。**

    `stocks:>0` を `stocks:0` に書き換えても他のテストは緑のままなので、
    送信するパラメータ自体をここで押さえる。
    """
    seen = {}

    def handler(request):
        seen.update(dict(request.url.params))
        return httpx.Response(200, json=[])

    with _client(handler) as q:
        q.fetch_stories(window_hours=24)

    assert seen["per_page"] == "100"  # API の上限
    assert seen["page"] == "1"  # 1 始まり
    # LGTM では絞れないのでストック数を使う
    assert f"stocks:>{SEARCH_MIN_STOCKS}" in seen["query"]
    # created は日付単位なので、境界を取りこぼさないよう 1 日広く取る
    expected = (datetime.now(UTC) - timedelta(hours=24) - timedelta(days=1)).strftime("%Y-%m-%d")
    assert f"created:>={expected}" in seen["query"]

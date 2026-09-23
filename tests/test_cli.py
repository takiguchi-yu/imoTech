"""CLI のテスト。ネットワークに出ない部分の挙動を固定する。"""

import contextlib
import io
from datetime import UTC, datetime, timedelta

import pytest

from imotech.cli import (
    _apply_skips,
    _format_thresholds,
    _resolve_thresholds,
    build_parser,
    cmd_compose,
    cmd_publish,
    cmd_stats,
)
from imotech.config import Settings
from imotech.llm import GenerationResult, LLMError
from imotech.models import (
    ApprovedPage,
    ArticleDraft,
    ArticleSource,
    Candidate,
    CandidateState,
    DiscoursePoint,
    Engagement,
    SkipReason,
    SourceRef,
    Story,
    Thresholds,
)
from imotech.notion import NotionBlockLimitError, NotionError
from imotech.render import IMO_PROMPT, set_imo, write_article
from imotech.store import CandidateStore
from imotech.urlhash import url_hash


def _c(h: str, hours_ago: int = 30) -> Candidate:
    return Candidate(
        url_hash=h,
        ref=SourceRef("hackernews", h),
        url=f"https://e.com/{h}",
        title="t",
        collected_at=datetime.now(UTC) - timedelta(hours=hours_ago),
        score_at_collect=10,
        comments_at_collect=2,
    )


def test_dry_runでは打ち切りを書き込まない(tmp_path, capsys):
    store = CandidateStore(tmp_path / "c.jsonl")
    store.append_new([_c("aa")])
    _apply_skips(store, [(_c("aa"), SkipReason.BELOW_THRESHOLD)], dry_run=True)
    assert store.load()[0].state is CandidateState.PENDING
    assert "書き込みません" in capsys.readouterr().out


def test_dry_runでなければ打ち切りを書き込む(tmp_path, capsys):
    store = CandidateStore(tmp_path / "c.jsonl")
    store.append_new([_c("aa")])
    _apply_skips(store, [(_c("aa"), SkipReason.BELOW_THRESHOLD)], dry_run=False)
    row = store.load()[0]
    assert row.state is CandidateState.SKIPPED
    assert row.skip_reason == "below_threshold"
    # 理由の内訳を出さないと、何がどう打ち切られたか追えない
    assert "below_threshold=1" in capsys.readouterr().out


def test_打ち切りが空なら何もしない(tmp_path, capsys):
    store = CandidateStore(tmp_path / "c.jsonl")
    _apply_skips(store, [], dry_run=False)
    assert capsys.readouterr().out == ""


def test_statsは空ストアで次の一手を示す(tmp_path, capsys):
    s = Settings(candidates_path=tmp_path / "none.jsonl")
    assert cmd_stats(s, None) == 0
    out = capsys.readouterr().out
    assert "空です" in out
    assert "imotech collect" in out
    # どのファイルを見ているかを出さないと、パスの打ち間違いに気づけない
    assert str(tmp_path / "none.jsonl") in out


def test_statsが状態の内訳を出す(tmp_path, capsys):
    store = CandidateStore(tmp_path / "c.jsonl")
    a, b = _c("aa"), _c("bb")
    b.state = CandidateState.SKIPPED
    b.skip_reason = "below_threshold"
    b.score_at_evaluate = 40
    store.append_new([a, b])
    cmd_stats(Settings(candidates_path=tmp_path / "c.jsonl"), None)
    out = capsys.readouterr().out
    assert "pending=1" in out and "skipped=1" in out
    assert "below_threshold=1" in out


# --- パーサ ---------------------------------------------------------------


def test_サブコマンドは必須():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_limitの既定値が環境変数名つきでヘルプに出る():
    # 「既定は設定値」だけでは、どこを変えればよいか分からない
    p = build_parser(Settings(max_drafts_per_run=7))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), pytest.raises(SystemExit):
        p.parse_args(["compose", "--help"])
    assert "既定 7" in buf.getvalue()
    assert "IMOTECH_MAX_DRAFTS_PER_RUN" in buf.getvalue()


def test_dry_runの既定はFalse():
    assert build_parser().parse_args(["compose"]).dry_run is False
    assert build_parser().parse_args(["compose", "--dry-run"]).dry_run is True


# --- compose の終了コード -------------------------------------------------
#
# 無人実行（.github/workflows/daily.yml）は compose の終了コードだけを見て Issue を
# 立てる。「次回も同じ結果になる失敗」だけが非 0 になることを、ここで固定する。


class _FakeFeed:
    """閾値を十分に超える現在値を返すソース。反応は使わないので空で返す。

    `cli` は具象を知らず `create_feed` が返すものを使うだけなので、
    テストもその口を差し替える（`StoryFeed` / `ReactionSource` を満たしていればよい）。
    """

    name = "fake"

    def __init__(self, **_kw) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_a) -> bool:
        return False

    def fetch_stories(self, **_kw) -> list[Story]:
        return []

    #: 記事の著者。記事プラットフォーム（Qiita など）を模すときに差し替える
    author: str | None = None
    #: 元記事の URL。著者のハンドルを含む形にできる
    url_template = "https://e.com/{id}"
    title_template = "t"

    def fetch_reactions(self, ref: SourceRef) -> tuple[Story, list]:
        story = Story(
            ref=ref,
            url=self.url_template.format(id=ref.id),
            title=self.title_template,
            engagement=Engagement(score=500, comments=200),
            created_at=datetime.now(UTC) - timedelta(hours=30),
            discussion_url=f"https://news.ycombinator.com/item?id={ref.id}",
            author=self.author,
        )
        return story, []


def _fake_fetcher_class(outcomes: list | None):
    """ArticleFetcher の差し替え。outcomes に None を混ぜると本文取得の失敗になる。"""
    seq = list(outcomes) if outcomes is not None else None

    class _F:
        #: fetch に渡された extra_handles の記録（PII の配線を見るため）
        seen_handles: list = []

        def __init__(self, **_kw) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_a) -> bool:
            return False

        def fetch(self, _url: str, extra_handles: frozenset[str] = frozenset()):
            # 本物と同じく著者のハンドルを受け取る。渡された値は
            # test_composeは著者のハンドルを本文の匿名化に渡す で確かめる
            self.seen_handles.append(extra_handles)
            if seq is None:
                return ArticleSource(text="本文" * 100, via="test")
            return seq.pop(0)

    return _F


class _FakeNotion:
    """create_draft の結果を outcomes の順に返す。例外インスタンスなら投げる。"""

    def __init__(self, outcomes: list) -> None:
        self._outcomes = list(outcomes)
        self.closed = False

    def create_draft(self, _ds, _draft, *, collected_at=None) -> str:
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def close(self) -> None:
        self.closed = True


def _generation_result(url_hash: str) -> GenerationResult:
    draft = ArticleDraft(
        url_hash=url_hash,
        title=f"タイトル {url_hash}",
        slug=f"2026-01-01-{url_hash}",
        digest=["要旨1", "要旨2"],
        discourse=[DiscoursePoint(point="論点", detail="詳細", stance="mixed")],
    )
    return GenerationResult(draft=draft, model="test-model", attempts=1)


def _fake_generator_class(outcomes: list):
    """DraftGenerator の差し替え。generate が outcomes を 1 件ずつ消費する。"""
    seq = list(outcomes)

    class _G:
        def __init__(self, **_kw) -> None:
            pass

        def generate(self, *_a, **_kw) -> GenerationResult:
            outcome = seq.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

    return _G


def _compose_env(
    tmp_path,
    monkeypatch,
    *,
    candidates: int,
    llm_outcomes: list,
    notion_outcomes: list | None,
    fetch_outcomes: list | None = None,
    notion_configured: bool = False,
    dry_run: bool = False,
) -> tuple[Settings, object, _FakeNotion | None]:
    """compose を外部通信なしで動かすための一式を組む。

    notion_configured は「設定は揃っている」状態。notion_outcomes を None にすると、
    設定はあるのに _open_notion が開けなかった状況（トークン失効・DB ID の誤り）になる。
    """
    store = CandidateStore(tmp_path / "c.jsonl")
    store.append_new([_c(f"h{i}") for i in range(candidates)])

    monkeypatch.setattr("imotech.cli.create_feed", lambda _names, **_kw: _FakeFeed())
    monkeypatch.setattr("imotech.cli.ArticleFetcher", _fake_fetcher_class(fetch_outcomes))
    monkeypatch.setattr("imotech.llm.DraftGenerator", _fake_generator_class(llm_outcomes))

    notion = _FakeNotion(notion_outcomes) if notion_outcomes is not None else None
    monkeypatch.setattr("imotech.cli._open_notion", lambda _s, *, dry_run: (notion, "ds"))

    settings = Settings(
        candidates_path=tmp_path / "c.jsonl",
        articles_dir=tmp_path / "articles",
        gemini_api_key="dummy",
        notion_token="t" if notion_configured else "",
        notion_database_id="d" if notion_configured else "",
    )
    argv = ["compose", "--dry-run"] if dry_run else ["compose"]
    args = build_parser().parse_args(argv)
    return settings, args, notion


def test_composeは記事化できれば0を返す(tmp_path, monkeypatch):
    settings, args, _ = _compose_env(
        tmp_path,
        monkeypatch,
        candidates=1,
        llm_outcomes=[_generation_result("h0")],
        notion_outcomes=None,
    )
    assert cmd_compose(settings, args) == 0


def test_composeは生成が全滅したら1を返す(tmp_path, monkeypatch, capsys):
    # Gemini のキー失効やモデルの全滅は、次回の実行でも同じ結果になる。
    # pending に残して黙って 0 を返すと、毎朝 1 本も出ないまま誰も気づかない
    settings, args, _ = _compose_env(
        tmp_path,
        monkeypatch,
        candidates=2,
        llm_outcomes=[LLMError("boom"), LLMError("boom")],
        notion_outcomes=None,
    )
    assert cmd_compose(settings, args) == 1
    assert "Gemini" in capsys.readouterr().err


def test_composeは一部だけ生成に失敗しても0を返す(tmp_path, monkeypatch):
    # 1 件でも記事になったなら失敗ではない。残りは pending のまま次回が拾う
    settings, args, _ = _compose_env(
        tmp_path,
        monkeypatch,
        candidates=2,
        llm_outcomes=[LLMError("boom"), _generation_result("h1")],
        notion_outcomes=None,
    )
    assert cmd_compose(settings, args) == 0


def test_composeはNotion投入が全滅したら1を返す(tmp_path, monkeypatch, capsys):
    # 不正な NOTION_DATABASE_ID やトークン失効がこれに当たる。Markdown は書けて
    # いるので記事化は成功しており、警告だけでは無人実行から気づけない
    settings, args, notion = _compose_env(
        tmp_path,
        monkeypatch,
        candidates=2,
        llm_outcomes=[_generation_result("h0"), _generation_result("h1")],
        notion_outcomes=[NotionError("403"), NotionError("403")],
    )
    assert cmd_compose(settings, args) == 1
    assert "NOTION_TOKEN" in capsys.readouterr().err
    assert notion is not None and notion.closed


def test_composeはNotion投入が1件でも通れば0を返す(tmp_path, monkeypatch):
    settings, args, _ = _compose_env(
        tmp_path,
        monkeypatch,
        candidates=2,
        llm_outcomes=[_generation_result("h0"), _generation_result("h1")],
        notion_outcomes=[NotionError("403"), "page-id"],
    )
    assert cmd_compose(settings, args) == 0


def test_composeはブロック上限なら成功があっても1を返す(tmp_path, monkeypatch, capsys):
    # ブロック上限は人が課金するまで回復しない。その日たまたま 1 件通っていても、
    # 翌日まで黙っていると上限に気づくのが遅れる。
    # 上限に当たると以降の候補では Notion を叩かない（notion=None になる）ので、
    # outcomes は 2 件目を渡していない
    settings, args, _ = _compose_env(
        tmp_path,
        monkeypatch,
        candidates=2,
        llm_outcomes=[_generation_result("h0"), _generation_result("h1")],
        notion_outcomes=["page-id", NotionBlockLimitError("block limit")],
    )
    assert cmd_compose(settings, args) == 1
    assert "ブロック上限" in capsys.readouterr().err


def test_composeはNotionを開けなかったら1を返す(tmp_path, monkeypatch, capsys):
    # 不正な NOTION_DATABASE_ID とトークン失効はここに落ちる。_open_notion が
    # warn を出して Markdown 直書きに倒すため、create_draft には到達しない
    settings, args, _ = _compose_env(
        tmp_path,
        monkeypatch,
        candidates=1,
        llm_outcomes=[_generation_result("h0")],
        notion_outcomes=None,
        notion_configured=True,
    )
    assert cmd_compose(settings, args) == 1
    assert "NOTION_DATABASE_ID" in capsys.readouterr().err


def test_composeはNotion未設定なら開けなくても0を返す(tmp_path, monkeypatch):
    # Notion を使わない運用。設定が無いのだから失敗ではない
    settings, args, _ = _compose_env(
        tmp_path,
        monkeypatch,
        candidates=1,
        llm_outcomes=[_generation_result("h0")],
        notion_outcomes=None,
        notion_configured=False,
    )
    assert cmd_compose(settings, args) == 0


def test_composeは内容不足で全滅したら1を返す(tmp_path, monkeypatch, capsys):
    # 要旨も論調も空の応答が続くのは、プロンプトかレスポンススキーマの破損。
    # この候補は skipped になって次回に持ち越されないので、黙ると毎朝焼き続ける
    empty_draft = GenerationResult(
        draft=ArticleDraft(url_hash="h0", title="t", slug="2026-01-01-t", digest=[], discourse=[]),
        model="test-model",
        attempts=1,
    )
    settings, args, _ = _compose_env(
        tmp_path,
        monkeypatch,
        candidates=1,
        llm_outcomes=[empty_draft],
        notion_outcomes=None,
    )
    assert cmd_compose(settings, args) == 1
    assert "内容不足 1" in capsys.readouterr().err


def test_composeは本文が取れないだけなら0を返す(tmp_path, monkeypatch):
    # 元記事側の事情で、その候補は skipped になる。次回は別の候補が選ばれるので
    # 人が直すものは無い
    settings, args, _ = _compose_env(
        tmp_path,
        monkeypatch,
        candidates=2,
        llm_outcomes=[],
        notion_outcomes=None,
        fetch_outcomes=[None, None],
    )
    assert cmd_compose(settings, args) == 0


def test_composeはdry_runなら常に0を返す(tmp_path, monkeypatch):
    # Gemini を呼ばないので失敗しようがない。判定に混ぜると
    # 「キー無しで確認する」用途が壊れる
    settings, args, _ = _compose_env(
        tmp_path,
        monkeypatch,
        candidates=1,
        llm_outcomes=[],
        notion_outcomes=None,
        notion_configured=True,
        dry_run=True,
    )
    assert cmd_compose(settings, args) == 0


# --- publish の終了コード -------------------------------------------------
#
# 無人実行（.github/workflows/publish.yml）は publish の終了コードだけを見て
# Issue を立てる。「承認されたのに 1 件も反映できなかった」を失敗として扱う。


class _FakeNotionClient:
    """cmd_publish が使う分だけを持つ Notion クライアント。"""

    def __init__(self, approved: list[ApprovedPage]) -> None:
        self._approved = approved
        self.published: list[str] = []
        self.closed = False

    def data_source_id(self, _db_id: str) -> str:
        return "ds"

    def fetch_approved(self, _ds: str) -> list[ApprovedPage]:
        return list(self._approved)

    def mark_published(self, page_id: str, *, when=None) -> None:
        self.published.append(page_id)

    def close(self) -> None:
        self.closed = True


def _write_article_for(tmp_path, slug: str, source_url: str):
    """記事 Markdown を 1 本置き、その url_hash を返す。"""
    draft = ArticleDraft(
        url_hash=url_hash(source_url),
        title="タイトル",
        slug=slug,
        digest=["要旨1", "要旨2"],
        discourse=[DiscoursePoint(point="論点", detail="詳細", stance="mixed")],
        source_url=source_url,
    )
    path, _ = write_article(draft, tmp_path / "articles")
    return path, draft.url_hash


def _publish_env(tmp_path, monkeypatch, *, approved: list[ApprovedPage], dry_run: bool = False):
    client = _FakeNotionClient(approved)
    monkeypatch.setattr("imotech.cli._notion_client", lambda _s: client)
    settings = Settings(
        candidates_path=tmp_path / "c.jsonl",
        articles_dir=tmp_path / "articles",
        notion_token="t",
        notion_database_id="d",
    )
    argv = ["publish", "--dry-run"] if dry_run else ["publish"]
    return settings, build_parser().parse_args(argv), client


def test_publishは承認0件なら0を返す(tmp_path, monkeypatch, capsys):
    settings, args, client = _publish_env(tmp_path, monkeypatch, approved=[])
    assert cmd_publish(settings, args) == 0
    assert "処理するものはありません" in capsys.readouterr().out
    assert client.published == []


def test_publishはimoを差し込んだ回にはNotionを進めない(tmp_path, monkeypatch):
    # commit する前に Published にすると、commit できなかったときに
    # 「Notion は Published なのに Markdown は未コミット」が残り、
    # fetch_approved が二度と返さないのでその記事は永久に公開されない
    path, h = _write_article_for(tmp_path, "2026-01-01-a", "https://e.com/a")
    page = ApprovedPage(page_id="p1", url_hash=h, slug="2026-01-01-a", imo="所感です。")
    settings, args, client = _publish_env(tmp_path, monkeypatch, approved=[page])
    assert cmd_publish(settings, args) == 0
    assert "所感です。" in path.read_text(encoding="utf-8")
    assert client.published == []


def test_publishは2回目の実行でNotionを進める(tmp_path, monkeypatch):
    # commit と push が済んだあとに、もう一度実行して確定させる形
    # （publish.yml はこの順でステップを並べている）
    path, h = _write_article_for(tmp_path, "2026-01-01-a", "https://e.com/a")
    page = ApprovedPage(page_id="p1", url_hash=h, slug="2026-01-01-a", imo="所感です。")
    settings, args, client = _publish_env(tmp_path, monkeypatch, approved=[page])
    assert cmd_publish(settings, args) == 0
    assert client.published == []

    # 2 回目。Markdown には既に imo が入っているので already 分岐に入る
    settings2, args2, client2 = _publish_env(tmp_path, monkeypatch, approved=[page])
    assert cmd_publish(settings2, args2) == 0
    assert client2.published == ["p1"]
    # 2 回目でも Notion の値で上書きしない
    assert "所感です。" in path.read_text(encoding="utf-8")


def test_publishは承認を全件飛ばしたら1を返す(tmp_path, monkeypatch, capsys):
    # 記事ファイルを置かない＝ compose 前、または Notion 側で Slug が書き換えられた状態。
    # Status は Approved のまま残るので、人が直すまで次回も同じ結果になる
    page = ApprovedPage(page_id="p1", url_hash="deadbeef", slug="2026-01-01-none", imo="所感。")
    settings, args, client = _publish_env(tmp_path, monkeypatch, approved=[page])
    assert cmd_publish(settings, args) == 1
    err = capsys.readouterr().err
    assert "すべてを飛ばしました" in err
    # 反映していないので Notion 側も進めない（次回また拾えるように）
    assert client.published == []


def test_publishは一部でも反映できれば0を返す(tmp_path, monkeypatch):
    path, h = _write_article_for(tmp_path, "2026-01-01-a", "https://e.com/a")
    ok = ApprovedPage(page_id="p1", url_hash=h, slug="2026-01-01-a", imo="所感です。")
    ng = ApprovedPage(page_id="p2", url_hash="deadbeef", slug="2026-01-01-none", imo="所感。")
    settings, args, client = _publish_env(tmp_path, monkeypatch, approved=[ok, ng])
    assert cmd_publish(settings, args) == 0
    assert "所感です。" in path.read_text(encoding="utf-8")
    # 差し込んだ回では Notion を進めない（commit 後の 2 回目で進む）
    assert client.published == []


def test_publishはローカルのimoを優先してStatusだけ進める(tmp_path, monkeypatch, capsys):
    path, h = _write_article_for(tmp_path, "2026-01-01-a", "https://e.com/a")
    # 人が手で書いた imo。Notion の値で上書きしてはいけない
    path.write_text(set_imo(path.read_text(encoding="utf-8"), "手で書いた所感。"), encoding="utf-8")
    page = ApprovedPage(page_id="p1", url_hash=h, slug="2026-01-01-a", imo="Notion の所感。")
    settings, args, client = _publish_env(tmp_path, monkeypatch, approved=[page])
    assert cmd_publish(settings, args) == 0
    body = path.read_text(encoding="utf-8")
    assert "手で書いた所感。" in body and "Notion の所感。" not in body
    assert client.published == ["p1"]
    assert "ローカルの imo を優先" in capsys.readouterr().out


def test_publishはdry_runなら全件飛ばしても0を返す(tmp_path, monkeypatch):
    # 何も書いていないので失敗ではない。判定に混ぜると確認用途が壊れる
    page = ApprovedPage(page_id="p1", url_hash="deadbeef", slug="2026-01-01-none", imo="所感。")
    settings, args, client = _publish_env(tmp_path, monkeypatch, approved=[page], dry_run=True)
    assert cmd_publish(settings, args) == 0
    assert client.published == []


def test_publishはプレースホルダが残っていたらStatusを進めない(tmp_path, monkeypatch, capsys):
    # プレースホルダ行を消さずに所感を書き足した状態。行選択のミスで普通に起きる。
    # サイト側のゲートはこの記事を公開から外すので、Notion を Published に進めると
    # fetch_approved が二度と返さず、公開もされないまま誰も気づけない
    path, h = _write_article_for(tmp_path, "2026-01-01-a", "https://e.com/a")
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            IMO_PROMPT, IMO_PROMPT + "\n\n消し忘れたまま書いた所感。"
        ),
        encoding="utf-8",
    )
    page = ApprovedPage(page_id="p1", url_hash=h, slug="2026-01-01-a", imo="Notion の所感。")
    settings, args, client = _publish_env(tmp_path, monkeypatch, approved=[page])
    # 全件がこれなら「1 件も反映できなかった」— 人が直すまで回復しない
    assert cmd_publish(settings, args) == 1
    err = capsys.readouterr().err
    assert "プレースホルダ" in err and "Approved のまま" in err
    # Approved のまま残すので、消してから再実行すれば拾える
    assert client.published == []
    assert client.closed


def test_publishはNotion未設定なら2を返す(tmp_path, monkeypatch, capsys):
    settings = Settings(
        candidates_path=tmp_path / "c.jsonl",
        articles_dir=tmp_path / "articles",
        notion_token="",
        notion_database_id="",
    )
    args = build_parser().parse_args(["publish"])
    assert cmd_publish(settings, args) == 2
    assert "NOTION_TOKEN" in capsys.readouterr().err


def test_publishはNotionの呼び出しが失敗したら1を返す(tmp_path, monkeypatch, capsys):
    class _Broken(_FakeNotionClient):
        def fetch_approved(self, _ds):
            raise NotionError("HTTP 403 (restricted_resource)")

    client = _Broken([])
    monkeypatch.setattr("imotech.cli._notion_client", lambda _s: client)
    settings = Settings(
        candidates_path=tmp_path / "c.jsonl",
        articles_dir=tmp_path / "articles",
        notion_token="t",
        notion_database_id="d",
    )
    args = build_parser().parse_args(["publish"])
    assert cmd_publish(settings, args) == 1
    assert "Notion の呼び出しに失敗しました" in capsys.readouterr().err
    # 例外で抜けても finally でクライアントを閉じる
    assert client.closed


# --- ソースごとの閾値 -------------------------------------------------------


def test_閾値の上書きをJSONで読む():
    s = Settings(source_thresholds='{"qiita": {"min_score": 50, "min_comments": 0}}')
    assert s.threshold_overrides == {"qiita": Thresholds(min_score=50, min_comments=0)}


def test_閾値の上書きが無ければ空():
    assert Settings().threshold_overrides == {}


def test_片方だけの上書きは共通設定で埋める():
    s = Settings(min_score=100, min_comments=30, source_thresholds='{"qiita": {"min_comments": 0}}')
    assert s.threshold_overrides["qiita"] == Thresholds(min_score=100, min_comments=0)


@pytest.mark.parametrize(
    "raw",
    [
        "{壊れた",  # JSON として読めない
        '["qiita"]',  # オブジェクトでない
        '{"qiita": 50}',  # 値がオブジェクトでない
        '{"qiita": {"min_score": "たくさん"}}',  # 整数でない
    ],
)
def test_壊れた閾値の設定は落とす(raw):
    # 黙って無視すると、意図した数と違う記事が出続けて無人実行では気づけない
    with pytest.raises(ValueError, match="IMOTECH_SOURCE_THRESHOLDS"):
        assert Settings(source_thresholds=raw).threshold_overrides


def test_ソース自身の既定を使う():
    from imotech.sources.qiita import Qiita

    s = Settings(sources="qiita", min_score=100, min_comments=30)
    with Qiita() as feed:
        got = _resolve_thresholds(feed, s)
    # Qiita はコメントを見ない閾値を自分で持っている
    assert got["qiita"].min_comments == 0


def test_上書きはソースの既定より優先する():
    from imotech.sources.qiita import Qiita

    s = Settings(
        sources="qiita", source_thresholds='{"qiita": {"min_score": 5, "min_comments": 9}}'
    )
    with Qiita() as feed:
        got = _resolve_thresholds(feed, s)
    assert got["qiita"] == Thresholds(min_score=5, min_comments=9)


def test_HackerNewsは共通設定に倒れる():
    """後方互換。`IMOTECH_MIN_SCORE` が従来どおり効く。"""
    from imotech.sources.hackernews import HackerNews

    s = Settings(sources="hackernews", min_score=123, min_comments=45)
    with HackerNews() as feed:
        got = _resolve_thresholds(feed, s)
    assert got["hackernews"] == Thresholds(min_score=123, min_comments=45)


def test_ソースが1つならログは短い形():
    s = Settings(sources="hackernews", min_score=100, min_comments=30)
    line = _format_thresholds({"hackernews": Thresholds(100, 30)}, s)
    assert line == "score>=100 かつ comments>=30"


def test_ソースが複数ならログに内訳を出す():
    # 「なぜこの候補が落ちたか」をログだけで追えるようにする
    s = Settings(sources="hackernews,qiita")
    line = _format_thresholds({"hackernews": Thresholds(100, 30), "qiita": Thresholds(30, 0)}, s)
    assert "hackernews: score>=100 かつ comments>=30" in line
    assert "qiita: score>=30 かつ comments>=0" in line


# --- PII の配線（回帰テスト） -----------------------------------------------
#
# **このリポジトリは同じ形の回帰を 1 度出している**（コミット 4e8d781
# 「束ねたソースで PII が漏れていた」）。`cli` が著者のハンドルを匿名化へ
# 渡し忘れても、単体テストは全部通ってしまう。compose を通して確かめる。


def _compose_with_author(tmp_path, monkeypatch, author, *, url: str, title: str = "t"):
    """記事プラットフォームを模した候補で compose を dry-run する。

    **候補ストア側の URL とタイトルを差し替える**のが要点。`cli` が匿名化に通すのは
    `story.url` ではなく候補の `c.url` なので、そこを著者入りにしないと素通りする。
    """

    class _AuthoredFeed(_FakeFeed):
        pass

    _AuthoredFeed.author = author

    settings, args, _ = _compose_env(
        tmp_path,
        monkeypatch,
        candidates=1,
        llm_outcomes=[],
        notion_outcomes=None,
        notion_configured=False,
        dry_run=True,
    )
    monkeypatch.setattr("imotech.cli.create_feed", lambda _names, **_kw: _AuthoredFeed())

    store = CandidateStore(tmp_path / "c.jsonl")
    rows = store.load()
    for row in rows:
        row.url = url.format(id=row.ref.id)
        row.title = title
    store.update(rows)
    return settings, args


def _prompt_of(captured: str) -> str:
    """dry-run の出力から、LLM に渡るプロンプト本体だけを取り出す。

    処理中の候補を示すログ行（`cli` が出す生の元記事 URL）は出典と同じ扱いで
    伏せていないので、**プロンプトだけを見る**。
    """
    marker = "## ユーザープロンプト"
    assert marker in captured, "dry-run が最後まで走っていない"
    return captured[captured.index(marker) :]


def test_composeは著者のハンドルをLLMへの入力に残さない(tmp_path, monkeypatch, capsys):
    """**PII の回帰テスト。**

    記事プラットフォームでは元記事の URL 自体に著者のハンドルが入る
    （`qiita.com/<user_id>/items/<id>`）。`--dry-run` はプロンプト全文を
    標準出力に出すので、そこに著者名が出ないことが LLM 入力の検証になる。
    """
    settings, args = _compose_with_author(
        tmp_path, monkeypatch, "carol123", url="https://qiita.com/carol123/items/{id}"
    )
    assert cmd_compose(settings, args) == 0
    assert "carol123" not in _prompt_of(capsys.readouterr().out)


def test_composeは3文字の著者ハンドルも残さない(tmp_path, monkeypatch, capsys):
    # 短いハンドルは本文では伏せない規則があるが、URL のパス区画には当てない
    settings, args = _compose_with_author(
        tmp_path, monkeypatch, "abc", url="https://qiita.com/abc/items/{id}"
    )
    assert cmd_compose(settings, args) == 0
    assert "qiita.com/abc/" not in _prompt_of(capsys.readouterr().out)


def test_composeは英単語と同じ綴りの著者ハンドルも残さない(tmp_path, monkeypatch, capsys):
    # `what` は _COMMON_WORDS にあるが、URL のパス区画では伏せる
    settings, args = _compose_with_author(
        tmp_path, monkeypatch, "what", url="https://qiita.com/what/items/{id}"
    )
    assert cmd_compose(settings, args) == 0
    assert "qiita.com/what/" not in _prompt_of(capsys.readouterr().out)


def test_composeはタイトルの著者ハンドルも伏せる(tmp_path, monkeypatch, capsys):
    settings, args = _compose_with_author(
        tmp_path,
        monkeypatch,
        "carol123",
        url="https://qiita.com/carol123/items/{id}",
        title="carol123 が作った CLI の話",
    )
    assert cmd_compose(settings, args) == 0
    assert "carol123" not in _prompt_of(capsys.readouterr().out)


def test_composeは著者のハンドルを本文の匿名化に渡す(tmp_path, monkeypatch):
    # 本文は元記事＝著者本人のページなので、自分の ID を書いていることがある
    fetcher = _fake_fetcher_class(None)
    fetcher.seen_handles = []
    settings, args = _compose_with_author(
        tmp_path, monkeypatch, "carol123", url="https://qiita.com/carol123/items/{id}"
    )
    monkeypatch.setattr("imotech.cli.ArticleFetcher", fetcher)
    cmd_compose(settings, args)
    assert fetcher.seen_handles == [frozenset({"carol123"})]


def test_著者がいないソースでも動く(tmp_path, monkeypatch, capsys):
    # author が None のソース（従来の Hacker News 経路）を壊していない
    settings, args = _compose_with_author(tmp_path, monkeypatch, None, url="https://e.com/{id}")
    assert cmd_compose(settings, args) == 0
    assert _prompt_of(capsys.readouterr().out)


def test_知らないソース名の上書きは落とす():
    """**打ち間違いを黙って通さない。** どの候補にも当たらない上書きは
    「設定したのに効かない」を無言で食うことになる。"""
    from imotech.sources.hackernews import HackerNews

    s = Settings(sources="hackernews", source_thresholds='{"hackernwes": {"min_score": 1}}')
    with HackerNews() as feed:
        with pytest.raises(ValueError, match="知らないソース"):
            _resolve_thresholds(feed, s)


def test_設定から外したソースの上書きは通す():
    # 実装のあるソースなら、いま使っていなくても古い候補に効かせられる
    from imotech.sources.hackernews import HackerNews

    s = Settings(sources="hackernews", source_thresholds='{"qiita": {"min_score": 1}}')
    with HackerNews() as feed:
        assert _resolve_thresholds(feed, s)["qiita"] == Thresholds(1, 30)


def test_壊れた設定は外部への問い合わせより先に落ちる(monkeypatch, capsys):
    """**compose の中盤で落ちると、最大 60 件の問い合わせを捨ててからになる。**

    Qiita では非認証 1 時間分のレート予算がそれで消える。
    """
    from imotech.cli import main

    monkeypatch.setenv("IMOTECH_SOURCE_THRESHOLDS", "{壊れた")

    def _boom(*_a, **_kw):
        raise AssertionError("設定を検証する前にコマンドが走った")

    monkeypatch.setattr("imotech.cli.cmd_stats", _boom)
    assert main(["stats"]) == 2
    assert "IMOTECH_SOURCE_THRESHOLDS" in capsys.readouterr().err

"""ソースを足せることのテスト。

**このファイルの目的は「2 つ目のソースを足すのに `sources/` の外を触らなくて済む」
ことを実証すること。** ここで作るダミーは `models` の型を返すだけで、
`cli` も `store` も `render` も一切変えていない。
"""

from datetime import UTC, datetime

import pytest

from imotech.models import Engagement, Reaction, SourceRef, Story, Thresholds
from imotech.sources import (
    ReactionSource,
    StoryFeed,
    profile_url_patterns,
    supports_reactions,
    thresholds_for,
)
from imotech.sources.multi import MultiFeed
from imotech.sources.registry import available, create, create_feed, register


def _story(source: str, id_: str, score: int) -> Story:
    return Story(
        ref=SourceRef(source, id_),
        url=f"https://{source}.example/{id_}",
        title=f"{source} の記事 {id_}",
        engagement=Engagement(score=score, comments=score // 2),
        created_at=datetime.now(UTC),
        discussion_url=f"https://{source}.example/{id_}#comments",
    )


class FeedOnly:
    """反応を持たないソース（RSS のような）。`ReactionSource` を実装しない。"""

    name = "feedonly"

    def __init__(self, **_kw) -> None:
        pass

    def fetch_stories(self, *, window_hours=24, min_points=10, limit=50) -> list[Story]:
        return [_story(self.name, "1", 300)]


class WithReactions(FeedOnly):
    """反応も取れるソース。FeedOnly より注目度の高い話題を返す。"""

    name = "withreactions"

    def fetch_stories(self, *, window_hours=24, min_points=10, limit=50) -> list[Story]:
        return [_story(self.name, "1", 500)]

    def fetch_reactions(self, ref: SourceRef) -> tuple[Story | None, list[Reaction]]:
        return _story(self.name, ref.id, 500), [
            Reaction(comment_id="1", author="a", text="反応", depth=0, reply_count=1)
        ]


class Broken(FeedOnly):
    name = "broken"

    def fetch_stories(self, **_kw):
        raise RuntimeError("API が落ちている")


@pytest.fixture
def registered():
    """テストのあいだだけソースを登録する。Registry はグローバルなので必ず戻す。"""
    from imotech.sources import registry

    before = dict(registry._FACTORIES)
    for cls in (FeedOnly, WithReactions, Broken):
        register(cls.name, cls)
    yield
    registry._FACTORIES.clear()
    registry._FACTORIES.update(before)


# --- Protocol を満たすか ---------------------------------------------------


def test_反応を持たないソースもStoryFeedである():
    feed = FeedOnly()
    assert isinstance(feed, StoryFeed)
    # ReactionSource は満たさない＝ compose はこの候補を飛ばす
    assert not isinstance(feed, ReactionSource)
    assert supports_reactions(feed) is False


def test_反応を持つソースは両方を満たす():
    feed = WithReactions()
    assert isinstance(feed, StoryFeed) and isinstance(feed, ReactionSource)
    assert supports_reactions(feed) is True


def test_プロフィールURLのパターンは持たなくてよい():
    # 持たないソースには空が返る
    assert profile_url_patterns(FeedOnly()) == []


def test_束ねたソースでもプロフィールURLのパターンを集める():
    """**PII の回帰テスト。** MultiFeed が自分のパターンを持たないために
    伏せ字が丸ごとスキップされ、投稿者ハンドルが LLM と記事に流れた事故があった。"""
    from imotech.anonymize import scrub
    from imotech.sources.hackernews import HackerNews

    feed = MultiFeed([FeedOnly(), HackerNews()])
    patterns = profile_url_patterns(feed)
    assert len(patterns) == 1  # 子のうち HackerNews だけが持つ
    out = scrub("see https://news.ycombinator.com/user?id=patio11", frozenset(), patterns)
    assert "patio11" not in out


# --- Registry（Factory Method）---------------------------------------------


def test_登録すれば名前から作れる(registered):
    assert "feedonly" in available()
    assert isinstance(create("feedonly"), FeedOnly)


def test_知らない名前は候補を添えて落とす():
    with pytest.raises(ValueError, match="知らないソース"):
        create("nosuchsource")


def test_ソースが空なら落とす():
    with pytest.raises(ValueError, match="IMOTECH_SOURCES が空です"):
        create_feed([])


def test_1つならそのまま2つ以上ならMultiFeed(registered):
    # **呼び出し側は 1 つか複数かを意識しない。** これが Composite を入れた理由
    assert isinstance(create_feed(["feedonly"]), FeedOnly)
    assert isinstance(create_feed(["feedonly", "withreactions"]), MultiFeed)


# --- Composite -------------------------------------------------------------


def test_MultiFeedは全ソースから集めて注目度順に並べる():
    feed = MultiFeed([FeedOnly(), WithReactions()])
    got = feed.fetch_stories(limit=10)
    assert [s.ref.source for s in got] == ["withreactions", "feedonly"]  # 500 → 300
    assert isinstance(feed, StoryFeed)


def test_MultiFeedはlimitを全体の上限として扱う():
    assert len(MultiFeed([FeedOnly(), WithReactions()]).fetch_stories(limit=1)) == 1


def test_MultiFeedは1つのソースが落ちても他を使う(capsys):
    # 収集はベストエフォート。1 つのソースの障害で全部止めない
    got = MultiFeed([Broken(), WithReactions()]).fetch_stories(limit=10)
    assert [s.ref.source for s in got] == ["withreactions"]
    assert "broken からの収集に失敗" in capsys.readouterr().out


def test_MultiFeedは反応を元のソースへ振り分ける():
    feed = MultiFeed([FeedOnly(), WithReactions()])
    story, reactions = feed.fetch_reactions(SourceRef("withreactions", "9"))
    assert story is not None and story.ref.source == "withreactions"
    assert len(reactions) == 1


def test_MultiFeedは反応を持たないソースの候補を空で返す():
    # RSS のようなソースの候補。呼び出し側からは「取れなかった」と同じ扱いになる
    assert MultiFeed([FeedOnly()]).fetch_reactions(SourceRef("feedonly", "1")) == (None, [])


def test_MultiFeedは知らないソースの候補も空で返す():
    # 束ねていないソースで拾った古い候補が候補ストアに残っていても落ちない
    assert MultiFeed([WithReactions()]).fetch_reactions(SourceRef("gone", "1")) == (None, [])


def test_MultiFeedは空で作れない():
    with pytest.raises(ValueError, match="1 つも指定されていません"):
        MultiFeed([])


def test_MultiFeedのcloseはcloseを持つソースだけ呼ぶ():
    closed = []

    class Closable(FeedOnly):
        name = "closable"

        def close(self) -> None:
            closed.append(self.name)

    with MultiFeed([FeedOnly(), Closable()]):
        pass
    assert closed == ["closable"]


# --- ソースごとの閾値 -------------------------------------------------------


def test_既定を持たないソースは共通設定に倒れる():
    # **Hacker News はあえて持たない。** 共通設定が Hacker News の値そのものなので、
    # IMOTECH_MIN_SCORE が従来どおり効く（後方互換）
    from imotech.sources.hackernews import HackerNews

    common = Thresholds(min_score=100, min_comments=30)
    with HackerNews() as hn:
        assert thresholds_for(hn, "hackernews", common) == common


def test_既定を持つソースはそれを使う():
    from imotech.sources.qiita import Qiita

    common = Thresholds(min_score=100, min_comments=30)
    with Qiita() as q:
        got = thresholds_for(q, "qiita", common)
    # Qiita はコメントがほぼ付かないので、コメント数を見ない
    assert got.min_comments == 0
    assert got != common


def test_束ねたソースでは名前の一致する子に聞く():
    from imotech.sources.hackernews import HackerNews
    from imotech.sources.qiita import Qiita

    common = Thresholds(min_score=100, min_comments=30)
    with MultiFeed([HackerNews(), Qiita()]) as feed:
        assert thresholds_for(feed, "hackernews", common) == common
        assert thresholds_for(feed, "qiita", common).min_comments == 0
        # 束ねていないソースの古い候補は共通設定で判定する
        assert thresholds_for(feed, "gone", common) == common


def test_名前が違えば自分の既定を渡さない():
    # 単一ソースで動かしているときに、別ソースの候補へ誤って厳しい／緩い閾値を当てない
    from imotech.sources.qiita import Qiita

    common = Thresholds(min_score=100, min_comments=30)
    with Qiita() as q:
        assert thresholds_for(q, "hackernews", common) == common


def test_束ねたソースでもQiitaのプロフィールURLを集める():
    """**PII の回帰テスト。** ソースを足すたびにパターンを集め漏らしていないか。"""
    from imotech.anonymize import scrub
    from imotech.sources.hackernews import HackerNews
    from imotech.sources.qiita import Qiita

    with MultiFeed([HackerNews(), Qiita()]) as feed:
        patterns = profile_url_patterns(feed)
    assert len(patterns) == 2
    out = scrub(
        "a https://news.ycombinator.com/user?id=patio11 b https://qiita.com/carol123",
        frozenset(),
        patterns,
    )
    assert "patio11" not in out and "carol123" not in out

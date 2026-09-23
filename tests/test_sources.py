"""ソースを足せることのテスト。

**このファイルの目的は「2 つ目のソースを足すのに `sources/` の外を触らなくて済む」
ことを実証すること。** ここで作るダミーは `models` の型を返すだけで、
`cli` も `store` も `render` も一切変えていない。
"""

from datetime import UTC, datetime

import pytest

from imotech.models import Engagement, Reaction, SourceRef, Story
from imotech.sources import (
    ReactionSource,
    StoryFeed,
    profile_url_pattern,
    supports_reactions,
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
            Reaction(comment_id=1, author="a", text="反応", depth=0, reply_count=1)
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
    # 持たないソースには None が返る。anonymize 側がそれを見て処理を飛ばす
    assert profile_url_pattern(FeedOnly()) is None


# --- Registry（Factory Method）---------------------------------------------


def test_登録すれば名前から作れる(registered):
    assert "feedonly" in available()
    assert isinstance(create("feedonly"), FeedOnly)


def test_知らない名前は候補を添えて落とす():
    with pytest.raises(ValueError, match="知らないソース"):
        create("nosuchsource")


def test_ソースが空なら落とす():
    with pytest.raises(ValueError, match="指定されていません"):
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

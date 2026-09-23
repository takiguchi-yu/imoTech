"""値そのもののテスト。

はてブ URL の組み立ては `links.py` へ移した（`models` が特定のサービスを
知らないようにするため）。ここでは値の形だけを見る。
"""

from datetime import UTC, datetime

from imotech.links import hatena_bookmark_url
from imotech.models import Candidate, Engagement, SourceRef, Story


def _c(url: str) -> Candidate:
    return Candidate(
        url_hash="h",
        ref=SourceRef("hackernews", "1"),
        url=url,
        title="t",
        collected_at=datetime(2026, 9, 21, tzinfo=UTC),
        score_at_collect=1,
        comments_at_collect=1,
    )


def test_httpsのはてブURL():
    assert hatena_bookmark_url("https://e.com/a") == "https://b.hatena.ne.jp/entry/s/e.com/a"


def test_httpのはてブURL():
    assert hatena_bookmark_url("http://e.com/a") == "https://b.hatena.ne.jp/entry/e.com/a"


def test_scheme無しでもはてブURLになる():
    assert hatena_bookmark_url("e.com/a") == "https://b.hatena.ne.jp/entry/e.com/a"


def test_SourceRefは人が読める形になる():
    # ログとエラーメッセージに出るので、どのソースの何かが一目で分かるようにする
    assert str(SourceRef("hackernews", "123")) == "hackernews:123"


def test_議論のURLはStoryが値として持つ():
    # models はソースごとの URL の規則を知らない。ソースが組み立てて入れる
    s = Story(
        ref=SourceRef("hackernews", "123"),
        url="https://e.com",
        title="t",
        engagement=Engagement(score=1, comments=1),
        created_at=datetime.now(UTC),
        discussion_url="https://news.ycombinator.com/item?id=123",
    )
    assert s.discussion_url == "https://news.ycombinator.com/item?id=123"
    assert s.ref.source == "hackernews"


def test_Engagementの既定は0():
    e = Engagement()
    assert (e.score, e.comments) == (0, 0)

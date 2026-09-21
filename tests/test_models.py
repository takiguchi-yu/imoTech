"""値の変換のテスト。はてブ URL は文字列として組み立てるだけで API を呼ばない。"""

from datetime import UTC, datetime

from imotech.models import Candidate, Story


def _c(url: str) -> Candidate:
    return Candidate(
        url_hash="h",
        hn_item_id=1,
        url=url,
        title="t",
        collected_at=datetime(2026, 9, 21, tzinfo=UTC),
        score_at_collect=1,
        comments_at_collect=1,
    )


def test_httpsのはてブURL():
    assert _c("https://e.com/a").hatena_url == "https://b.hatena.ne.jp/entry/s/e.com/a"


def test_httpのはてブURL():
    assert _c("http://e.com/a").hatena_url == "https://b.hatena.ne.jp/entry/e.com/a"


def test_HNのスレッドURL():
    s = Story(123, "https://e.com", "t", 1, 1, datetime.now(UTC))
    assert s.hn_url == "https://news.ycombinator.com/item?id=123"
    assert _c("https://e.com/a").hn_url == "https://news.ycombinator.com/item?id=1"

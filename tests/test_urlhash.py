"""URL 正規化のテスト。冪等性の 1 段目を支えるため、衝突と非衝突の両方を押さえる。"""

import pytest

from imotech.urlhash import normalize, url_hash

# 同じ記事を指すはずの表記ゆれ。すべて同じハッシュにならなければ重複記事が出る。
SAME = [
    "https://example.com/a",
    "http://example.com/a",
    "https://www.example.com/a",
    "https://example.com/a/",
    "https://EXAMPLE.com/a",
    "https://example.com:443/a",
    "https://example.com/a#section",
    "https://example.com/a?utm_source=hn&utm_medium=social",
    "  https://example.com/a  ",
]


@pytest.mark.parametrize("url", SAME)
def test_変種はすべて同じハッシュになる(url):
    assert url_hash(url) == url_hash("https://example.com/a")


def test_意味のあるクエリは残す():
    assert url_hash("https://e.com/p?id=1") != url_hash("https://e.com/p")


def test_クエリの順序が違っても同じ():
    assert url_hash("https://e.com/p?b=2&a=1") == url_hash("https://e.com/p?a=1&b=2")


def test_別の記事は別のハッシュ():
    assert url_hash("https://example.com/a") != url_hash("https://example.com/b")


def test_ルートの末尾スラッシュは残す():
    # "/" を落とすと空パスになり、他のホストの表記と混ざる余地が生まれる
    assert normalize("https://example.com/") == "https://example.com/"


def test_既定でないポートは残す():
    assert normalize("https://example.com:8443/a") == "https://example.com:8443/a"


def test_ハッシュは16桁の16進():
    h = url_hash("https://example.com/a")
    assert len(h) == 16
    assert all(c in "0123456789abcdef" for c in h)

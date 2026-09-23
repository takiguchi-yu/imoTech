"""元記事取得のテスト。

ネットワークと名前解決を差し替える。チケットの「robots.txt の 404 許可 / 5xx 不許可」
「5MB 上限」「text/html 以外は中断」「trafilatura → og:description → None」と、
レビューで見つかった PII 流出・SSRF・リダイレクト先の robots 未検証を担保する。
"""

import httpx
import pytest

from imotech.extract import ArticleFetcher, _decode, _host_is_public, _og_description
from imotech.sources.hackernews import PROFILE_URL_RE

# autouse fixture がモジュール属性を差し替えるので、本物への参照を先に掴んでおく
_REAL_HOST_IS_PUBLIC = _host_is_public

UA = "imoTechBot/1.0"
ARTICLE_HTML = (
    "<html><head><meta property='og:description' content='OGPの説明'></head>"
    "<body><article><p>" + ("これは本文です。" * 40) + "</p></article></body></html>"
)


@pytest.fixture(autouse=True)
def _allow_all_hosts(monkeypatch):
    """既定ではすべて公開ホスト扱いにする。SSRF のテストだけ個別に上書きする。"""
    monkeypatch.setattr("imotech.extract._host_is_public", lambda url: True)


def _fetcher(handler, **kw):
    # 投稿者プロフィールの URL パターンはソースが持つ。本文の匿名化に使うので渡す
    kw.setdefault("profile_url_res", [PROFILE_URL_RE])
    return ArticleFetcher(user_agent=UA, transport=httpx.MockTransport(handler), **kw)


def _router(routes, default=None):
    def handler(request):
        for suffix, resp in routes.items():
            if str(request.url).endswith(suffix):
                return resp() if callable(resp) else resp
        return default() if callable(default) else (default or httpx.Response(404))

    return handler


# --- robots.txt -----------------------------------------------------------


def test_robotsが404なら許可():
    h = _router(
        {"/robots.txt": httpx.Response(404)},
        default=httpx.Response(200, text=ARTICLE_HTML, headers={"content-type": "text/html"}),
    )
    with _fetcher(h) as f:
        assert f.can_fetch("https://e.com/a") is True
        assert f.fetch("https://e.com/a") is not None


def test_robotsが5xxなら不許可():
    # サーバー障害時に勝手に取りにいかない（安全側に倒す）
    h = _router({"/robots.txt": httpx.Response(503)})
    with _fetcher(h) as f:
        assert f.can_fetch("https://e.com/a") is False
        assert f.fetch("https://e.com/a") is None


def test_robotsのDisallowを尊重する():
    h = _router(
        {"/robots.txt": httpx.Response(200, text="User-agent: *\nDisallow: /private/")},
        default=httpx.Response(200, text=ARTICLE_HTML, headers={"content-type": "text/html"}),
    )
    with _fetcher(h) as f:
        assert f.can_fetch("https://e.com/private/x") is False
        assert f.can_fetch("https://e.com/public/x") is True


def test_robotsはoriginごとに1回だけ取る():
    calls = []

    def handler(request):
        if str(request.url).endswith("/robots.txt"):
            calls.append(1)
            return httpx.Response(404)
        return httpx.Response(200, text=ARTICLE_HTML, headers={"content-type": "text/html"})

    with _fetcher(handler) as f:
        f.can_fetch("https://e.com/a")
        f.can_fetch("https://e.com/b")
    assert len(calls) == 1


# --- 取得 -----------------------------------------------------------------


def test_HTML以外は中断する():
    h = _router(
        {"/robots.txt": httpx.Response(404)},
        default=httpx.Response(
            200, content=b"%PDF-1.4", headers={"content-type": "application/pdf"}
        ),
    )
    with _fetcher(h) as f:
        assert f.fetch("https://e.com/a.pdf") is None


def test_サイズ上限を超えたら中断する():
    big = "<html><body>" + "x" * 5000 + "</body></html>"
    h = _router(
        {"/robots.txt": httpx.Response(404)},
        default=httpx.Response(200, text=big, headers={"content-type": "text/html"}),
    )
    with _fetcher(h, max_bytes=100) as f:
        assert f.fetch("https://e.com/a") is None


def test_4xxはNoneを返す():
    h = _router({"/robots.txt": httpx.Response(404)}, default=httpx.Response(403))
    with _fetcher(h) as f:
        assert f.fetch("https://e.com/a") is None


def test_本文が取れなければogにフォールバックする():
    thin = (
        "<html><head><meta property='og:description' content='OGPの説明'>"
        "</head><body></body></html>"
    )
    h = _router(
        {"/robots.txt": httpx.Response(404)},
        default=httpx.Response(200, text=thin, headers={"content-type": "text/html"}),
    )
    with _fetcher(h) as f:
        got = f.fetch("https://e.com/a")
    assert got is not None and got.via == "og:description"
    assert "OGPの説明" in got.text


def test_本文もogも無ければNone():
    h = _router(
        {"/robots.txt": httpx.Response(404)},
        default=httpx.Response(
            200, text="<html><body></body></html>", headers={"content-type": "text/html"}
        ),
    )
    with _fetcher(h) as f:
        assert f.fetch("https://e.com/a") is None


def test_max_charsで切り詰める():
    h = _router(
        {"/robots.txt": httpx.Response(404)},
        default=httpx.Response(200, text=ARTICLE_HTML, headers={"content-type": "text/html"}),
    )
    with _fetcher(h, max_chars=30) as f:
        got = f.fetch("https://e.com/a")
    assert got is not None and len(got.text) <= 30


# --- PII（レビューで見つかった Blocker の回帰テスト）------------------------


def test_元記事本文のPIIが伏せられる():
    # 元記事に著者の連絡先が載るのは普通にある。無料枠は入力が学習に使われるため、
    # 反応だけでなく本文も scrub を通す
    html = (
        "<html><body><article><p>"
        + "技術的な話をします。" * 20
        + "連絡先は author@example.org です。"
        + "プロフィールは https://news.ycombinator.com/user?id=someone にあります。"
        + "</p></article></body></html>"
    )
    h = _router(
        {"/robots.txt": httpx.Response(404)},
        default=httpx.Response(200, text=html, headers={"content-type": "text/html"}),
    )
    with _fetcher(h) as f:
        got = f.fetch("https://e.com/a")
    assert got is not None
    assert "author@example.org" not in got.text
    assert "user?id=someone" not in got.text
    assert "[メールアドレス]" in got.text


# --- リダイレクトと SSRF ---------------------------------------------------


def test_リダイレクト先のrobotsも検査する():
    # httpx に追従を任せると最終到達先の robots.txt を確認できない
    def handler(request):
        u = str(request.url)
        if u == "https://a.com/robots.txt":
            return httpx.Response(404)
        if u == "https://b.com/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /")
        if u == "https://a.com/x":
            return httpx.Response(302, headers={"location": "https://b.com/y"})
        return httpx.Response(200, text=ARTICLE_HTML, headers={"content-type": "text/html"})

    with _fetcher(handler) as f:
        assert f.fetch("https://a.com/x") is None


def test_リダイレクトを追って取得できる():
    def handler(request):
        u = str(request.url)
        if u.endswith("/robots.txt"):
            return httpx.Response(404)
        if u == "https://a.com/x":
            return httpx.Response(301, headers={"location": "https://b.com/y"})
        return httpx.Response(200, text=ARTICLE_HTML, headers={"content-type": "text/html"})

    with _fetcher(handler) as f:
        assert f.fetch("https://a.com/x") is not None


def test_リダイレクトが多すぎたら諦める():
    def handler(request):
        if str(request.url).endswith("/robots.txt"):
            return httpx.Response(404)
        return httpx.Response(302, headers={"location": "https://e.com/next"})

    with _fetcher(handler, max_redirects=2) as f:
        assert f.fetch("https://e.com/a") is None


def test_内部ネットワークを指すURLは取得しない(monkeypatch):
    # HN に投稿される URL は第三者が自由に決められる
    monkeypatch.setattr("imotech.extract._host_is_public", lambda url: "169.254" not in url)
    h = _router(
        {"/robots.txt": httpx.Response(404)},
        default=httpx.Response(200, text=ARTICLE_HTML, headers={"content-type": "text/html"}),
    )
    with _fetcher(h) as f:
        assert f.fetch("http://169.254.169.254/latest/meta-data/") is None


def test_リダイレクト先が内部ネットワークなら止める(monkeypatch):
    monkeypatch.setattr("imotech.extract._host_is_public", lambda url: "169.254" not in url)

    def handler(request):
        u = str(request.url)
        if u.endswith("/robots.txt"):
            return httpx.Response(404)
        if u == "https://a.com/x":
            return httpx.Response(302, headers={"location": "http://169.254.169.254/"})
        return httpx.Response(200, text=ARTICLE_HTML, headers={"content-type": "text/html"})

    with _fetcher(handler) as f:
        assert f.fetch("https://a.com/x") is None


def test_実際のIP判定():
    assert _REAL_HOST_IS_PUBLIC("http://169.254.169.254/x") is False
    assert _REAL_HOST_IS_PUBLIC("http://127.0.0.1/x") is False
    assert _REAL_HOST_IS_PUBLIC("http://10.0.0.1/x") is False
    assert _REAL_HOST_IS_PUBLIC("not-a-url") is False


# --- 文字コードと OGP ------------------------------------------------------


def test_未知のcharsetでも例外を投げない():
    # Content-Type に utf8mb4 のような実在しない charset が入ることがある
    raw = "<meta charset='utf8mb4'><meta property='og:description' content='説明'>".encode()
    assert _og_description(_decode(raw)) == "説明"


def test_shift_jisのmetaを読む():
    raw = "<meta charset='shift_jis'><meta property='og:description' content='説明'>".encode(
        "shift_jis"
    )
    assert _og_description(_decode(raw)) == "説明"


def test_og_descriptionを取り出す():
    assert (
        _og_description('<meta property="og:description" content="これが説明です">')
        == "これが説明です"
    )


def test_name属性でも取り出す():
    assert _og_description("<meta name='og:description' content='説明'>") == "説明"


def test_実体参照を戻す():
    assert _og_description('<meta property="og:description" content="A &amp; B">') == "A & B"


def test_無ければNone():
    assert _og_description("<html><head></head></html>") is None


def test_空のcontentはNone():
    assert _og_description('<meta property="og:description" content="  ">') is None


def test_他のmetaに引きずられない():
    html = (
        '<meta property="og:title" content="タイトル">'
        '<meta property="og:description" content="説明">'
    )
    assert _og_description(html) == "説明"

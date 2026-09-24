"""公式ブログ（RSS / Atom）と GitHub のソース（docs/DESIGN.md 4.1d）。通信は MockTransport。"""

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from imotech.models import SourceRef
from imotech.sources import provided_article, provides_articles, reserved_slots
from imotech.sources.feed import CLOUDFLARE, VERCEL, BlogFeed
from imotech.sources.github import PROFILE_URL_RE, GitHub
from imotech.sources.multi import MultiFeed
from imotech.sources.registry import available, create

NOW = datetime.now(UTC)


def _rss(*items: tuple[str, str, datetime]) -> bytes:
    body = "".join(
        f"<item><title>{t}</title><link>{u}</link>"
        f"<pubDate>{d.strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate></item>"
        for t, u, d in items
    )
    return f'<?xml version="1.0"?><rss version="2.0"><channel>{body}</channel></rss>'.encode()


def _atom(*entries: tuple[str, str, datetime]) -> bytes:
    body = "".join(
        f'<entry><title>{t}</title><link href="{u}"/><updated>{d.isoformat()}</updated></entry>'
        for t, u, d in entries
    )
    return f'<feed xmlns="http://www.w3.org/2005/Atom">{body}</feed>'.encode()


def _blog(spec, content: bytes) -> tuple[BlogFeed, list]:
    calls = []

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append(req.url)
        return httpx.Response(200, content=content)

    return BlogFeed(spec, transport=httpx.MockTransport(handler)), calls


def test_RSSから新着だけを拾う():
    feed, _ = _blog(
        CLOUDFLARE,
        _rss(
            ("New", "https://blog.cloudflare.com/new/", NOW - timedelta(hours=2)),
            ("Old", "https://blog.cloudflare.com/old/", NOW - timedelta(days=5)),
        ),
    )
    got = feed.fetch_stories(window_hours=24)
    assert [s.title for s in got] == ["New"]
    assert got[0].engagement.score == 0 and got[0].author is None
    assert got[0].discussion_url == got[0].url


def test_Atomはblogの記事だけを拾う():
    # Vercel の Atom は changelog（数行の告知）を含む
    feed, _ = _blog(
        VERCEL,
        _atom(
            ("Post", "https://vercel.com/blog/post", NOW - timedelta(hours=1)),
            ("Note", "https://vercel.com/changelog/note", NOW - timedelta(hours=1)),
        ),
    )
    assert [s.title for s in feed.fetch_stories(window_hours=24)] == ["Post"]


def test_ブログの問い合わせは反応0件で評価済みにする():
    feed, calls = _blog(
        CLOUDFLARE, _rss(("New", "https://blog.cloudflare.com/new/", NOW - timedelta(hours=2)))
    )
    story = feed.fetch_stories(window_hours=24)[0]
    got, reactions = feed.fetch_reactions(story.ref)
    assert got == story and reactions == []
    # フィードは 1 回の実行で 1 度だけ取る
    assert len(calls) == 1


def test_フィードから落ちた記事は評価できない():
    feed, _ = _blog(CLOUDFLARE, _rss())
    assert feed.fetch_reactions(SourceRef("cloudflare-blog", "gone")) == (None, [])


def test_ブログは枠を持ち閾値は0():
    feed, _ = _blog(CLOUDFLARE, _rss())
    assert reserved_slots(feed) == {"cloudflare-blog": 1}
    assert feed.default_thresholds.min_score == 0


# --- GitHub -----------------------------------------------------------------


def _repo(**kw) -> dict:
    base = {
        "id": 42,
        "name": "tool",
        "html_url": "https://github.com/someone/tool",
        "description": "A fast tool",
        "stargazers_count": 5000,
        "created_at": (NOW - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "owner": {"login": "someone"},
        "fork": False,
        "archived": False,
        "private": False,
    }
    base.update(kw)
    return base


def _gh(routes: dict[str, httpx.Response]) -> tuple[GitHub, list]:
    calls = []

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append(req)
        for prefix, resp in routes.items():
            if req.url.path.startswith(prefix):
                return resp
        return httpx.Response(404)

    return GitHub(transport=httpx.MockTransport(handler)), calls


def test_作成30日以内をstars順に検索する():
    gh, calls = _gh(
        {
            "/search/repositories": httpx.Response(
                200, json={"items": [_repo(), _repo(id=7, fork=True)]}
            )
        }
    )
    got = gh.fetch_stories(limit=10)
    assert [s.ref.id for s in got] == ["42"]  # フォークは捨てる
    q = calls[0].url.params["q"]
    assert "created:>=" in q and calls[0].url.params["sort"] == "stars"


def test_所有者のハンドルはタイトルに入れず伏せ字の対象にする():
    gh, _ = _gh({"/search/repositories": httpx.Response(200, json={"items": [_repo()]})})
    s = gh.fetch_stories()[0]
    assert s.title == "tool: A fast tool"
    assert "someone" not in s.title
    assert s.author == "someone"
    assert s.engagement.score == 5000 and s.engagement.comments == 0


def test_本文はREADMEをAPIで取る():
    gh, calls = _gh({"/repositories/42/readme": httpx.Response(200, text="# tool\n\nIt is fast.")})
    ref = SourceRef("github", "42")
    assert provides_articles(gh, "github")
    assert provided_article(gh, ref) == "# tool\n\nIt is fast."
    # HTML のページ（github.com）は取りに行かない
    assert all(c.url.host == "api.github.com" for c in calls)


def test_プロフィールURLだけを伏せ字にし_リポジトリURLには当てない():
    assert PROFILE_URL_RE.search("see https://github.com/someone for more")
    assert not PROFILE_URL_RE.search("https://github.com/someone/tool")


def test_検索に失敗したら例外にする():
    # MultiFeed が「このソースは失敗した」と数えられるように
    gh, _ = _gh({"/search/repositories": httpx.Response(500)})
    with pytest.raises(RuntimeError):
        gh.fetch_stories()


# --- 束ね方とレジストリ ----------------------------------------------------


def test_新しいソースを名前で作れる():
    for name in ("github", "cloudflare-blog", "vercel-blog"):
        assert name in available()
        create(name, user_agent="t").close()


def test_束ねても枠のあるソースの新着は上限で切らない():
    class _Hot:
        name = "hackernews"

        def fetch_stories(self, **kw):
            from imotech.models import Engagement, Story

            return [
                Story(
                    SourceRef("hackernews", str(i)),
                    f"https://e.com/{i}",
                    "t",
                    Engagement(900, 90),
                    NOW,
                )
                for i in range(5)
            ]

    blog, _ = _blog(
        CLOUDFLARE, _rss(("New", "https://blog.cloudflare.com/new/", NOW - timedelta(hours=2)))
    )
    got = MultiFeed([_Hot(), blog]).fetch_stories(window_hours=24, limit=3)
    assert len([s for s in got if s.ref.source == "hackernews"]) == 3
    assert [s.title for s in got if s.ref.source == "cloudflare-blog"] == ["New"]


def test_束ねて収集するとき桁の違うソースは別枠で取る():
    from imotech.models import Engagement, Story

    class _HN:
        name = "hackernews"

        def fetch_stories(self, **kw):
            return [
                Story(
                    SourceRef("hackernews", str(i)),
                    f"https://e.com/{i}",
                    "t",
                    Engagement(300, 50),
                    NOW,
                )
                for i in range(5)
            ]

    gh, _ = _gh(
        {
            "/search/repositories": httpx.Response(
                200, json={"items": [_repo(id=i, stargazers_count=20000) for i in range(1, 30)]}
            )
        }
    )
    got = MultiFeed([_HN(), gh]).fetch_stories(limit=5)
    assert len([s for s in got if s.ref.source == "hackernews"]) == 5  # GitHub に押し出されない
    assert len([s for s in got if s.ref.source == "github"]) == gh.collect_quota


@pytest.mark.parametrize(
    "resp",
    [httpx.Response(503), httpx.Response(200, content=b"<html>not xml")],
)
def test_フィードが取れなくても問い合わせで例外にしない(resp):
    # compose の問い合わせのループは例外を握らない。投げると HN も含めて 0 本になる
    calls = []

    def handler(req):
        calls.append(req)
        return resp

    feed = BlogFeed(CLOUDFLARE, transport=httpx.MockTransport(handler))
    ref = SourceRef("cloudflare-blog", "x")
    assert feed.fetch_reactions(ref) == (None, [])
    assert feed.fetch_reactions(ref) == (None, [])
    assert len(calls) == 1  # 同じ実行の中では取り直さない


def test_タイムゾーンの無い日付はUTCとして読む():
    raw = (NOW - timedelta(hours=1)).strftime("%a, %d %b %Y %H:%M:%S -0000")
    body = (
        '<?xml version="1.0"?><rss version="2.0"><channel><item><title>T</title>'
        f"<link>https://blog.cloudflare.com/t/</link><pubDate>{raw}</pubDate></item></channel></rss>"
    ).encode()
    feed, _ = _blog(CLOUDFLARE, body)
    s = feed.fetch_stories(window_hours=24)[0]
    assert s.created_at.tzinfo is not None
    assert abs((NOW - s.created_at).total_seconds() - 3600) < 120


def test_GitHubの応答が壊れていても問い合わせで例外にしない():
    gh, _ = _gh({"/repositories/42": httpx.Response(200, content=b"<html>")})
    assert gh.fetch_reactions(SourceRef("github", "42")) == (None, [])


def test_レート上限に当たったらその実行では叩かない():
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(403, headers={"x-ratelimit-remaining": "0"})

    gh = GitHub(transport=httpx.MockTransport(handler))
    assert gh.fetch_reactions(SourceRef("github", "1")) == (None, [])
    assert gh.fetch_reactions(SourceRef("github", "2")) == (None, [])
    assert gh.fetch_article(SourceRef("github", "2")) is None
    assert len(calls) == 1


def test_GitHubの5xxでも問い合わせで例外にしない():
    gh, _ = _gh({"/repositories/42": httpx.Response(502)})
    assert gh.fetch_reactions(SourceRef("github", "42")) == (None, [])

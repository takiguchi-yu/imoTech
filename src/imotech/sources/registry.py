"""名前からソースを作る（GoF: Factory Method）。

クラス階層は作らない。**「名前 → 生成関数」の辞書**が Python での素直な形で、
`oo-design` の「GoF の実装形をそのまま持ち込まず、その言語の標準的な書き方へ翻訳する」
に従っている。

ソースを足すときはこのファイルの `_FACTORIES` に 1 行足すだけでよい。
`cli.py` は触らない。
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable

from . import StoryFeed
from .feed import CLOUDFLARE, VERCEL, BlogFeed
from .github import GitHub
from .hackernews import HackerNews
from .qiita import Qiita


def _github(**kwargs: object) -> GitHub:
    # トークンは任意。GitHub Actions では secrets.GITHUB_TOKEN を GITHUB_TOKEN で渡す
    # （無くても動くが、認証なしは 60 req/h）
    return GitHub(token=os.environ.get("GITHUB_TOKEN", ""), **kwargs)  # type: ignore[arg-type]


#: 名前 → 生成関数。生成関数は `user_agent` をキーワードで受け取る。
_FACTORIES: dict[str, Callable[..., StoryFeed]] = {
    HackerNews.name: HackerNews,
    Qiita.name: Qiita,
    GitHub.name: _github,
    CLOUDFLARE.name: lambda **kw: BlogFeed(CLOUDFLARE, **kw),
    VERCEL.name: lambda **kw: BlogFeed(VERCEL, **kw),
}


def available() -> list[str]:
    """使えるソースの名前。設定の検証とエラーメッセージに使う。"""
    return sorted(_FACTORIES)


def register(name: str, factory: Callable[..., StoryFeed]) -> None:
    """ソースを足す。テストでダミーを差し込むときにも使う。"""
    _FACTORIES[name] = factory


def create(name: str, **kwargs: object) -> StoryFeed:
    """名前からソースを 1 つ作る。知らない名前なら候補を添えて落とす。"""
    try:
        factory = _FACTORIES[name]
    except KeyError:
        raise ValueError(
            f"IMOTECH_SOURCES に知らないソース {name!r} があります。"
            f"使えるのは {', '.join(available())}"
        ) from None
    return factory(**kwargs)


def create_feed(names: Iterable[str], **kwargs: object) -> StoryFeed:
    """名前の並びから `StoryFeed` を 1 つ作る。

    2 つ以上なら `MultiFeed` で束ねる。**呼び出し側は 1 つか複数かを意識しない** —
    返ってくるのはいつも 1 つの `StoryFeed` で、これが Composite を入れた理由。
    """
    from .multi import MultiFeed

    # 同名を 2 つ束ねると、同じ話題を 2 回取って limit の枠を食い、
    # fetch_reactions は先頭に固定される（振り分けが name をキーにしているため）
    wanted = list(dict.fromkeys(n.strip() for n in names if n.strip()))
    if not wanted:
        raise ValueError(f"IMOTECH_SOURCES が空です。使えるのは {', '.join(available())}")
    feeds = [create(n, **kwargs) for n in wanted]
    return feeds[0] if len(feeds) == 1 else MultiFeed(feeds)

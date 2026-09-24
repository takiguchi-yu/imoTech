"""話題と反応を拾ってくる層。

**ソースを足すときに触るのはこのパッケージの中だけ**にする。`cli.py` は
`StoryFeed` / `ReactionSource` の Protocol と `registry` だけを知り、
具象クラス（`HackerNews` など）を import しない。

## ソースによって違うこと

| | Hacker News | Zenn / Qiita / dev.to |
|---|---|---|
| Story の実体 | 外部記事への投稿（url は他所） | 記事そのもの（url は自サイト） |
| 議論の場所 | スレッド URL（記事とは別） | 記事ページ自身 |
| 注目度 | points / comments | LGTM / いいね / reactions |
| 反応 | 議論が主体 | コメントは少なめ、無いこともある |

この差は `Story.discussion_url` と `Engagement` が吸収する。**反応を持たないソース
（RSS など）は `ReactionSource` を実装しなくてよい** — `supports_reactions()` で判定する。

## 採用したパターン（GoF）

- **Strategy**: `StoryFeed` / `ReactionSource` の Protocol。Python では
  抽象基底クラスにせず Protocol で構造的に満たす
- **Factory Method**: `registry.py`。クラス階層ではなく「名前 → 生成関数」の辞書に翻訳
- **Composite**: `MultiFeed`。複数のソースを 1 つの `StoryFeed` として扱う
- **Adapter**: 各ソースの `_story_from_*` / `_reaction_from_*`。API の生の形を
  `models` の型に変換する。具象クラス自体が Adapter を兼ねる

見送ったパターンと理由は `docs/DESIGN.md` 1.3 に書いてある。
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Protocol, TypeVar, runtime_checkable

from ..models import Reaction, SourceRef, Story, Thresholds

_T = TypeVar("_T")


@runtime_checkable
class StoryFeed(Protocol):
    """話題を拾ってくる側。フィードの形式（API / RSS）を呼び出し側に見せない。"""

    name: str

    def fetch_stories(self, *, window_hours: int, min_points: int, limit: int) -> list[Story]: ...


@runtime_checkable
class ReactionSource(Protocol):
    """ある話題への反応を取ってくる側。

    **すべてのソースが実装するわけではない。** RSS のように反応を持たない
    フィードもあるので、呼び出す前に `supports_reactions()` で確かめる。
    """

    name: str

    def fetch_reactions(self, ref: SourceRef) -> tuple[Story | None, list[Reaction]]:
        """(現在の Story, 反応の一覧) を返す。Story が取れなければ (None, [])。"""
        ...


@runtime_checkable
class ArticleProvider(Protocol):
    """記事の本文を自分で渡す側。**持たないソースが普通**で、呼び出し側は元記事の URL を
    取りに行く（`extract.ArticleFetcher`）。GitHub のように、ページ（HTML）を取りに
    行ってはいけないが API で本文（README）を取れるソースだけが実装する。
    """

    name: str

    def fetch_article(self, ref: SourceRef) -> str | None: ...


def provided_article(feed: object, ref: SourceRef) -> str | None:
    """そのソースが本文を自分で渡すなら、その本文。渡さないなら None。

    束ねたソース（MultiFeed）では、名前の一致する子に聞く。
    """
    children = getattr(feed, "feeds", None)
    if isinstance(children, list):
        for child in children:
            if getattr(child, "name", None) == ref.source:
                return provided_article(child, ref)
        return None
    if getattr(feed, "name", None) != ref.source or not isinstance(feed, ArticleProvider):
        return None
    return feed.fetch_article(ref)


def provides_articles(feed: object, source: str) -> bool:
    """そのソースが本文を自分で渡すか（元記事の URL を取りに行ってはいけないか）。"""
    children = getattr(feed, "feeds", None)
    if isinstance(children, list):
        return any(
            provides_articles(c, source) for c in children if getattr(c, "name", None) == source
        )
    return getattr(feed, "name", None) == source and isinstance(feed, ArticleProvider)


def _int_attr(feed: object, attr: str) -> dict[str, int]:
    children = getattr(feed, "feeds", None)
    if isinstance(children, list):
        out: dict[str, int] = {}
        for child in children:
            out.update(_int_attr(child, attr))
        return out
    n = getattr(feed, attr, None)
    name = getattr(feed, "name", None)
    return {name: n} if isinstance(n, int) and n > 0 and isinstance(name, str) else {}


def per_run_caps(feed: object) -> dict[str, int]:
    """1 回の実行で記事にする本数の上限をソースごとに（`max_per_run`）。

    **注目度の桁が他と違うソース（GitHub の stars は数千〜数万、Hacker News の points は
    数百）が、注目度順で枠を独占しないように**する。持たないソースは上限なし。
    """
    return _int_attr(feed, "max_per_run")


def collect_quotas(feed: object) -> dict[str, int]:
    """束ねて収集するとき、全体の上限とは別に取る件数（`collect_quota`）。

    注目度の桁が他と違うソースは、全体を注目度順に切るとそのソースだけが残る（または
    消える）。そのソースは全体の枠に混ぜず、この件数だけ別に取る。
    """
    return _int_attr(feed, "collect_quota")


def reserved_slots(feed: object) -> dict[str, int]:
    """1 回の実行で、注目度に関係なく記事にする本数をソースごとに（`reserved_per_run`）。

    注目度を持たない公式ブログが使う（docs/DESIGN.md 4.1d）。持たないソースは入れない。
    """
    children = getattr(feed, "feeds", None)
    if isinstance(children, list):
        out: dict[str, int] = {}
        for child in children:
            out.update(reserved_slots(child))
        return out
    n = getattr(feed, "reserved_per_run", None)
    name = getattr(feed, "name", None)
    return {name: n} if isinstance(n, int) and n > 0 and isinstance(name, str) else {}


def profile_url_patterns(feed: object) -> list[re.Pattern[str]]:
    """そのソースの投稿者プロフィール URL のパターン。持たなければ空。

    匿名化（`anonymize.scrub`）に渡す。**URL の形はソースごとに違う**ので
    `anonymize` 側に持たせず、ソースから取る。

    **束ねたソース（MultiFeed）では子のぶんをすべて集める。** 1 つにまとめて
    返さないのは、正規表現のフラグがソースごとに違いうるため。
    """
    children = getattr(feed, "feeds", None)
    if isinstance(children, list):
        return [p for child in children for p in profile_url_patterns(child)]
    pattern = getattr(feed, "profile_url_re", None)
    return [pattern] if isinstance(pattern, re.Pattern) else []


def thresholds_for(feed: object, source: str, fallback: Thresholds) -> Thresholds:
    """そのソースで「話題になった」と言える下限。持たなければ fallback。

    **閾値の桁はソースによって違う**（Hacker News はコメント数百、Qiita はほぼ 0）。
    どの値が妥当かはソース固有の知識なので、ソース自身に `default_thresholds` として
    持たせ、持たないソースは共通の設定値に倒す。**Hacker News はあえて持たない** —
    共通設定が Hacker News の値そのものなので、`IMOTECH_MIN_SCORE` が従来どおり効く。

    束ねたソース（MultiFeed）では、名前の一致する子に聞く。
    """
    children = getattr(feed, "feeds", None)
    if isinstance(children, list):
        for child in children:
            if getattr(child, "name", None) == source:
                return thresholds_for(child, source, fallback)
        return fallback
    if getattr(feed, "name", None) != source:
        return fallback
    own = getattr(feed, "default_thresholds", None)
    return own if isinstance(own, Thresholds) else fallback


@contextmanager
def opened(feed: _T) -> Iterator[_T]:
    """ソースを使い終わったら閉じる。

    `StoryFeed` Protocol は `close()` を要求しない（HTTP を使わないソースもある）。
    一方 `cli` は `with` で使いたい。**`close()` を持つソースだけ閉じる**ことで、
    どちらの形のソースでも足せるようにする。
    """
    try:
        yield feed
    finally:
        close = getattr(feed, "close", None)
        if callable(close):
            close()


def supports_reactions(feed: object) -> bool:
    """このソースから反応を取れるか。

    **束ねたソース（MultiFeed）は子のどれかが対応していれば真。** MultiFeed 自身は
    振り分け用の `fetch_reactions` を持つので、そのまま `isinstance` を当てると
    子が全部非対応でも真になってしまう。
    """
    children = getattr(feed, "feeds", None)
    if isinstance(children, list):
        return any(supports_reactions(child) for child in children)
    return isinstance(feed, ReactionSource)

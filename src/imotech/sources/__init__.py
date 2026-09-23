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
from typing import Protocol, runtime_checkable

from ..models import Reaction, SourceRef, Story


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


def profile_url_pattern(feed: object) -> re.Pattern[str] | None:
    """そのソースの投稿者プロフィール URL のパターン。持たなければ None。

    匿名化（`anonymize.scrub`）に渡す。**URL の形はソースごとに違う**ので
    `anonymize` 側に持たせず、ソースから取る。
    """
    pattern = getattr(feed, "profile_url_re", None)
    return pattern if isinstance(pattern, re.Pattern) else None


def supports_reactions(feed: object) -> bool:
    """このソースから反応を取れるか。

    `isinstance(feed, ReactionSource)` は runtime_checkable な Protocol の
    メソッド有無だけを見るので、これで足りる。呼び出し側が
    `hasattr(feed, "fetch_reactions")` を書かずに済むよう、意図を名前にしておく。
    """
    return isinstance(feed, ReactionSource)

"""反応ソースの抽象。

初期実装は Hacker News だけだが、Bluesky / Mastodon を後から足す前提があるため
インターフェースを切ってある（docs/DESIGN.md 1.3）。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models import Reaction, Story


@runtime_checkable
class StoryFeed(Protocol):
    """話題を拾ってくる側。フィードの形式（API / RSS）を呼び出し側に見せない。"""

    name: str

    def fetch_stories(self, *, window_hours: int, min_points: int, limit: int) -> list[Story]: ...


@runtime_checkable
class ReactionSource(Protocol):
    """ある話題への反応を取ってくる側。"""

    name: str

    def fetch_reactions(self, story_id: int) -> tuple[Story | None, list[Reaction]]:
        """(現在の Story, 反応の一覧) を返す。Story が取れなければ (None, [])。"""
        ...

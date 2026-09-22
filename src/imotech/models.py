"""パイプラインが受け渡す値の定義。

このモジュールは他の imotech.* に依存しない。依存の向きを一方向に保つため、
ここに振る舞いは置かず、値と最小限の変換だけを持たせる。
用語は CONTEXT.md に対応する。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class CandidateState(StrEnum):
    """候補の状態。pending からのみ遷移し、drafted / skipped からは戻らない。"""

    PENDING = "pending"
    DRAFTED = "drafted"
    SKIPPED = "skipped"


class SkipReason(StrEnum):
    """候補を skipped にした理由。運用中の閾値調整の材料にする。"""

    BELOW_THRESHOLD = "below_threshold"
    NO_CONTENT = "no_content"
    # 生成失敗は候補を pending のまま残して翌日に回す方針（docs/DESIGN.md 5.1）なので
    # 現状は未使用。Notion 投入まで通ったあとの失敗を区別するために M2 で使う。
    LLM_FAILED = "llm_failed"
    TOO_OLD = "too_old"


class Stance(StrEnum):
    SUPPORTIVE = "supportive"
    CRITICAL = "critical"
    MIXED = "mixed"


@dataclass(frozen=True)
class Story:
    """Hacker News に投稿された 1 件の話題。記事を書く単位。"""

    hn_item_id: int
    url: str
    title: str
    points: int
    num_comments: int
    created_at: datetime

    @property
    def hn_url(self) -> str:
        return f"https://news.ycombinator.com/item?id={self.hn_item_id}"


@dataclass
class Candidate:
    """拾ってはあるが、まだ記事化していない Story。

    可変にしてあるのは state を更新するため。永続化は store.CandidateStore が持つ。
    """

    url_hash: str
    hn_item_id: int
    url: str
    title: str
    collected_at: datetime
    score_at_collect: int
    comments_at_collect: int
    state: CandidateState = CandidateState.PENDING
    evaluated_at: datetime | None = None
    score_at_evaluate: int | None = None
    comments_at_evaluate: int | None = None
    notion_page_id: str | None = None
    skip_reason: str | None = None

    @property
    def hn_url(self) -> str:
        return f"https://news.ycombinator.com/item?id={self.hn_item_id}"

    @property
    def hatena_url(self) -> str:
        """はてなブックマークのコメントページ。API は呼ばず URL を組み立てるだけ。

        収益化を前提にしたため、はてなの API / oEmbed は利用規約上使えない
        （Developer Center 利用規約 第4条1項）。リンクの設置は規約上自由。
        """
        if self.url.startswith("https://"):
            return "https://b.hatena.ne.jp/entry/s/" + self.url[len("https://") :]
        if self.url.startswith("http://"):
            return "https://b.hatena.ne.jp/entry/" + self.url[len("http://") :]
        return "https://b.hatena.ne.jp/entry/" + self.url


@dataclass(frozen=True)
class Reaction:
    """HN の生コメント。author を持つので、そのまま LLM に渡してはいけない。

    LLM へ渡してよいのは anonymize() を通した AnonymizedReaction だけ。
    """

    comment_id: int
    author: str | None
    text: str
    depth: int
    reply_count: int


@dataclass(frozen=True)
class AnonymizedReaction:
    """投稿者を特定しうる情報を落としたコメント。LLM に渡せるのはこの型だけ。

    HN の API はコメント単位の score を返さないため、議論の重みを測る手がかりは
    reply_count と depth しかない。この 2 つは残す。
    """

    label: str
    text: str
    depth: int
    reply_count: int


@dataclass(frozen=True)
class ArticleSource:
    """元記事から取れた本文。LLM への入力にのみ使い、記事には転載しない。"""

    text: str
    via: str


@dataclass(frozen=True)
class DiscoursePoint:
    point: str
    detail: str
    stance: str


@dataclass(frozen=True)
class ArticleDraft:
    """LLM が生成し、Notion に下書きとして投入する記事。imo はまだ無い。"""

    url_hash: str
    title: str
    slug: str
    digest: list[str]
    discourse: list[DiscoursePoint]
    tags: list[str] = field(default_factory=list)
    source_url: str = ""
    source_title: str = ""
    hn_url: str = ""
    hatena_url: str = ""
    hn_score: int = 0
    hn_comments: int = 0
    model: str = ""
    generated_at: datetime | None = None


@dataclass(frozen=True)
class ApprovedPage:
    """Notion 上で承認された記事。

    記事本文は持たない。本文は compose が書いた Markdown が正で、Notion からは
    人が書いた imo だけを持ってくる（docs/DESIGN.md 1.2c）。
    """

    page_id: str
    url_hash: str
    slug: str
    imo: str

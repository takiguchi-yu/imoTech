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
class SourceRef:
    """どのソースのどの投稿か。

    ソースが増えても Story の形を変えずに済むよう、識別子をここに閉じる。
    **URL の組み立ては知らない** — 議論の場所はソースごとに違う（Hacker News は
    スレッドが別 URL、Zenn や Qiita は記事ページそのもの）ので、各ソースが
    `Story.discussion_url` に入れる。
    """

    source: str
    """ソースの名前。`sources` の Registry のキーと一致する（例: "hackernews"）。"""

    id: str
    """ソース内で一意な識別子。数値 ID のソースもあるので文字列で持つ。"""

    def __str__(self) -> str:
        return f"{self.source}:{self.id}"


@dataclass(frozen=True)
class Engagement:
    """どれだけ注目されたか。

    呼び名はソースによって違う（Hacker News は points、Qiita は LGTM、
    Zenn はいいね）ので、**意味で名前を付ける**。閾値の判定はこの 2 つだけを見る。
    """

    score: int = 0
    comments: int = 0


@dataclass(frozen=True)
class Thresholds:
    """「話題になった」と言える下限。

    **ソースによって桁が違う。** Hacker News は議論そのものが目的の場なので
    コメントが数百付くが、Qiita のような記事プラットフォームでは記事に
    コメントがほとんど付かない（実測で 82% が 0 件）。同じ閾値を当てると
    片方が 1 件も通らないので、ソースごとに持てるようにしてある。

    判定はここではなく `pipeline.select` が行う。ここは値だけを持つ。
    """

    min_score: int
    min_comments: int


@dataclass(frozen=True)
class Story:
    """ソースに投稿された 1 件の話題。記事を書く単位。

    `url` は元記事、`discussion_url` は反応が付いている場所。Hacker News では
    別々だが、記事プラットフォーム（Zenn / Qiita / dev.to）では同じになる。
    """

    ref: SourceRef
    url: str
    title: str
    engagement: Engagement
    created_at: datetime
    discussion_url: str = ""
    author: str | None = None
    """投稿者のハンドル。**PII なので LLM に渡す前に伏せる**。

    Hacker News では元記事は第三者のブログなので URL に投稿者名は入らないが、
    Qiita のような記事プラットフォームでは **`url` 自体に著者のハンドルが入る**
    （`qiita.com/<user_id>/items/<id>`）。反応の投稿者一覧だけを見ていると
    著者が伏せ字から漏れるので、Story 側でも持つ。
    """


@dataclass
class Candidate:
    """拾ってはあるが、まだ記事化していない Story。

    可変にしてあるのは state を更新するため。永続化は store.CandidateStore が持つ。
    """

    url_hash: str
    ref: SourceRef
    url: str
    title: str
    collected_at: datetime
    score_at_collect: int
    comments_at_collect: int
    discussion_url: str = ""
    state: CandidateState = CandidateState.PENDING
    evaluated_at: datetime | None = None
    score_at_evaluate: int | None = None
    comments_at_evaluate: int | None = None
    notion_page_id: str | None = None
    skip_reason: str | None = None


@dataclass(frozen=True)
class Reaction:
    """ソースから取ってきた生のコメント。author を持つので、そのまま LLM に渡してはいけない。

    LLM へ渡してよいのは anonymize() を通した AnonymizedReaction だけ。
    """

    comment_id: str
    """ソース内で一意なコメント ID。**数値とは限らない**（Qiita は 20 桁の 16 進）ので
    `SourceRef.id` と同じく文字列で持つ。"""

    author: str | None
    text: str
    depth: int
    reply_count: int


@dataclass(frozen=True)
class AnonymizedReaction:
    """投稿者を特定しうる情報を落としたコメント。LLM に渡せるのはこの型だけ。

    コメント単位の score を返さないソースがある（Hacker News の API がそう）ため、
    議論の重みを測る手がかりは reply_count と depth に統一する。この 2 つは残す。
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
class GlossaryEntry:
    """記事を読むのに、意味を知らないと困る語。

    「一般に難しい語」ではなく「**この記事**を読むのに要る語」を選ぶ。
    **分野は問わない** — 技術用語に限らず、金融・法務・心理などの語も入る。
    記事ごとに必要な語は違うので、辞書を持たず記事と一緒に生成する。
    """

    term: str
    description: str


@dataclass(frozen=True)
class UseCase:
    """その話題が、誰のどんな場面で効きそうか。

    **他の節と違い、元記事に書かれていないことを含む。** 元記事の内容をもとに
    生成 AI が考えた応用案で、要旨（元記事が言ったこと）や論調（反応で言われたこと）
    とは性格が違う。**推測であることは表示層が但し書きで示す**（`render` / `notion`）
    — 値に文言を混ぜると、2 箇所で古くなる。

    `GlossaryEntry` と同じ 2 フィールドにしてあるのは、記事での見た目を
    `- **場面**: 説明` に揃えるため。
    """

    scene: str
    """どんな場面か（例: 「社内の問い合わせ対応を自動化したいとき」）。"""

    detail: str
    """その場面で何にどう効くか。"""


@dataclass(frozen=True)
class ArticleDraft:
    """LLM が生成し、Notion に下書きとして投入する記事。imo はまだ無い。"""

    url_hash: str
    title: str
    slug: str
    digest: list[str]
    discourse: list[DiscoursePoint]
    tags: list[str] = field(default_factory=list)
    # 0 件を許す。そういう語が無い記事で数を埋めさせない
    glossary: list[GlossaryEntry] = field(default_factory=list)
    # 同じく 0 件を許す。主張・意見の記事には「使いどころ」が無い
    use_cases: list[UseCase] = field(default_factory=list)
    source_url: str = ""
    source_title: str = ""
    source: str = ""
    """話題を拾ったソースの名前（例: "hackernews"）。表示の出し分けに使う。"""
    discussion_url: str = ""
    hatena_url: str = ""
    engagement: Engagement = field(default_factory=Engagement)
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

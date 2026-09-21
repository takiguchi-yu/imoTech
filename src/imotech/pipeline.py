"""候補の選別ロジック。

判定は副作用を持たない純関数にしてあり、CLI と切り離して単体テストできる。
（末尾の mark_skipped だけは候補を破壊的に更新する。書き戻しは呼び出し側の責務）。
判定の根拠は docs/DESIGN.md 4.1。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import Candidate, CandidateState, SkipReason


@dataclass(frozen=True)
class Selection:
    """選別の結果。to_skip は記事化せず打ち切るもの。"""

    matured: list[Candidate]
    selected: list[Candidate]
    to_skip: list[tuple[Candidate, SkipReason]]


def matured_candidates(
    pending: list[Candidate], *, now: datetime, maturation_hours: int
) -> list[Candidate]:
    """収集から maturation_hours が経った候補だけを返す。

    拾った直後の Story にはまだ反応が無く、話題になったかを判定できない。
    """
    deadline = now - timedelta(hours=maturation_hours)
    return [c for c in pending if c.collected_at <= deadline]


def select(
    matured: list[Candidate],
    *,
    now: datetime,
    min_score: int,
    min_comments: int,
    max_drafts: int,
    max_age_hours: int,
    evaluated: set[str] | None = None,
) -> Selection:
    """閾値を満たす上位 max_drafts 件を選ぶ。

    score_at_evaluate / comments_at_evaluate に現在値が入っている前提。収集時の値では
    「まだ誰も反応していない」段階を見ることになり判定に使えない。
    閾値を満たす候補が 0 件なら 1 本も書かない（薄い記事を量産しないための判断）。

    evaluated は現在値を取り直せた候補の url_hash。渡されたときは、そこに無い候補を
    選出しない。HN への問い合わせに失敗した候補を収集時の値で選んでしまうと、
    呼び出し側が反応を持っていないまま記事化に進んでクラッシュする。
    期限超過の打ち切りは、取り直せなかった候補にも当てる（さもないと永久に残る）。
    """
    selectable = [c for c in matured if evaluated is None or c.url_hash in evaluated]

    passing: list[Candidate] = []
    failing: list[Candidate] = []
    for c in selectable:
        score = c.score_at_evaluate if c.score_at_evaluate is not None else c.score_at_collect
        comments = (
            c.comments_at_evaluate if c.comments_at_evaluate is not None else c.comments_at_collect
        )
        if score >= min_score and comments >= min_comments:
            passing.append(c)
        else:
            failing.append(c)

    passing.sort(
        key=lambda c: (
            -(c.score_at_evaluate if c.score_at_evaluate is not None else c.score_at_collect),
            c.collected_at,
        )
    )
    selected = passing[:max_drafts]

    # 期限を過ぎて「今回も処理しなかった」ものは打ち切る。
    # 閾値未満だけでなく、閾値は満たすが上位 N 件から溢れ続けた候補も対象にする。
    # 溢れ分を放置すると pending が単調増加し、毎回 HN に問い合わせ続けることになる。
    expiry = now - timedelta(hours=max_age_hours)
    picked = {id(c) for c in selected}
    failing_ids = {id(c) for c in failing}
    to_skip = [
        (c, SkipReason.BELOW_THRESHOLD if id(c) in failing_ids else SkipReason.TOO_OLD)
        for c in matured
        if id(c) not in picked and c.collected_at <= expiry
    ]
    return Selection(matured=matured, selected=selected, to_skip=to_skip)


def mark_skipped(candidate: Candidate, reason: SkipReason) -> Candidate:
    candidate.state = CandidateState.SKIPPED
    candidate.skip_reason = reason.value
    return candidate

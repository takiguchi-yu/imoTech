"""候補の選別ロジック。

判定は副作用を持たない純関数にしてあり、CLI と切り離して単体テストできる。
（末尾の mark_skipped だけは候補を破壊的に更新する。書き戻しは呼び出し側の責務）。
判定の根拠は docs/DESIGN.md 4.1。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import Candidate, CandidateState, SkipReason, Thresholds


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


#: 問い合わせの枠のうち、話題に当たらない候補に残しておく割合（docs/DESIGN.md 4.1c）
OFF_TOPIC_PROBE_SHARE = 0.25


def probe_targets(
    matured: list[Candidate],
    *,
    limit: int,
    topics_of: Callable[[Candidate], Sequence[str]],
) -> list[Candidate]:
    """現在値を取り直す（問い合わせる）候補を、上限 limit 件まで選ぶ。

    **話題に当たる候補を先にする。** 問い合わせから漏れた候補は現在値が無く選別で選べないので、
    収集時スコアの上位だけにすると、スコアの低い話題の候補が永久に選ばれない。

    **ただし枠の OFF_TOPIC_PROBE_SHARE は話題に当たらない候補に残す。** 全部を話題の候補に
    回すと、当たらない候補は現在値を一度も取られないまま期限切れで打ち切られ、
    「当たる候補が足りない日の穴埋め」が起きなくなる。どちらかが余れば、もう一方に回す。
    それぞれの組の中は収集時スコアの降順。
    """

    def by_score(cs: list[Candidate]) -> list[Candidate]:
        return sorted(cs, key=lambda c: (-c.score_at_collect, c.collected_at))

    on = by_score([c for c in matured if topics_of(c)])
    off = by_score([c for c in matured if not topics_of(c)])
    off_quota = min(len(off), int(limit * OFF_TOPIC_PROBE_SHARE))
    on_take = min(len(on), limit - off_quota)
    off_take = min(len(off), limit - on_take)
    return on[:on_take] + off[:off_take]


def select(
    matured: list[Candidate],
    *,
    now: datetime,
    thresholds: Mapping[str, Thresholds],
    default_thresholds: Thresholds,
    max_drafts: int,
    max_age_hours: int,
    evaluated: set[str] | None = None,
    topics_of: Callable[[Candidate], Sequence[str]] | None = None,
) -> Selection:
    """閾値を満たす上位 max_drafts 件を選ぶ。

    **話題に当たる候補を先にする**（topics_of が渡されたとき。docs/DESIGN.md 4.1c）。
    当たらない候補は捨てず、当たる候補が max_drafts に足りないときだけ穴埋めに使う。
    同じ組の中は注目度の降順。

    **閾値はソースごとに引く。** Hacker News は議論そのものが目的の場なので
    コメントが数百付くが、記事プラットフォーム（Qiita など）ではほぼ 0 件で、
    同じ閾値を当てると片方が 1 件も通らない。`thresholds` に無いソースの候補
    （設定から外したソースの古い候補など）は `default_thresholds` で判定する。

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
        t = thresholds.get(c.ref.source, default_thresholds)
        if score >= t.min_score and comments >= t.min_comments:
            passing.append(c)
        else:
            failing.append(c)

    passing.sort(
        key=lambda c: (
            0 if topics_of is not None and topics_of(c) else 1,
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

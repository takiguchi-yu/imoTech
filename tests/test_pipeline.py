"""選別ロジックのテスト。ここが壊れると、薄い記事を量産するか 1 本も書かなくなる。"""

from datetime import UTC, datetime, timedelta

from imotech.models import Candidate, CandidateState, SkipReason, SourceRef
from imotech.pipeline import mark_skipped, matured_candidates, select

NOW = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)


def _c(hours_ago: int, score=None, comments=None, h=None) -> Candidate:
    return Candidate(
        url_hash=h or f"h{hours_ago}",
        ref=SourceRef("hackernews", str(hours_ago)),
        url=f"https://e.com/{hours_ago}",
        title="t",
        collected_at=NOW - timedelta(hours=hours_ago),
        score_at_collect=5,
        comments_at_collect=1,
        score_at_evaluate=score,
        comments_at_evaluate=comments,
    )


def test_熟成前の候補は除かれる():
    got = matured_candidates([_c(1), _c(23), _c(25)], now=NOW, maturation_hours=24)
    assert [c.url_hash for c in got] == ["h25"]


def test_ちょうど境界の候補は含む():
    assert len(matured_candidates([_c(24)], now=NOW, maturation_hours=24)) == 1


def test_閾値を満たすものだけ選ばれる():
    s = select(
        [_c(30, 200, 50), _c(31, 99, 50), _c(32, 200, 29)],
        now=NOW,
        min_score=100,
        min_comments=30,
        max_drafts=5,
        max_age_hours=96,
    )
    assert [c.url_hash for c in s.selected] == ["h30"]


def test_スコア降順で上位N件に絞る():
    s = select(
        [_c(30, 150, 40), _c(31, 500, 40), _c(32, 300, 40)],
        now=NOW,
        min_score=100,
        min_comments=30,
        max_drafts=2,
        max_age_hours=96,
    )
    assert [c.score_at_evaluate for c in s.selected] == [500, 300]


def test_閾値を満たす候補が無ければ0件を返す():
    # 「薄い記事を量産しない」ための設計。0 件はエラーではなく正常
    s = select(
        [_c(30, 10, 2)], now=NOW, min_score=100, min_comments=30, max_drafts=5, max_age_hours=96
    )
    assert s.selected == []


def test_期限内で閾値未満なら持ち越す():
    s = select(
        [_c(30, 10, 2)], now=NOW, min_score=100, min_comments=30, max_drafts=5, max_age_hours=96
    )
    assert s.to_skip == []


def test_期限を過ぎて閾値未満なら打ち切る():
    s = select(
        [_c(100, 10, 2)], now=NOW, min_score=100, min_comments=30, max_drafts=5, max_age_hours=96
    )
    assert [(c.url_hash, r) for c, r in s.to_skip] == [("h100", SkipReason.BELOW_THRESHOLD)]


def test_期限を過ぎても閾値を満たせば打ち切らない():
    s = select(
        [_c(100, 500, 99)], now=NOW, min_score=100, min_comments=30, max_drafts=5, max_age_hours=96
    )
    assert s.to_skip == []
    assert [c.url_hash for c in s.selected] == ["h100"]


def test_評価値が無ければ収集時の値で判定する():
    # compose が現在値を取り直せなかった候補。収集時の値に落ちるだけで例外にしない
    c = _c(30)
    s = select([c], now=NOW, min_score=1, min_comments=1, max_drafts=5, max_age_hours=96)
    assert s.selected == [c]


def test_打ち切りマークが状態と理由を書く():
    c = mark_skipped(_c(100), SkipReason.NO_CONTENT)
    assert c.state is CandidateState.SKIPPED
    assert c.skip_reason == "no_content"


# --- 取り直せなかった候補の扱い（レビューで見つかった Blocker の回帰テスト）------


def test_評価できなかった候補は選出しない():
    # fetch_reactions に失敗した候補を収集時の値で選ぶと、呼び出し側が反応を
    # 持たないまま記事化に進んで KeyError で落ちる
    ok = _c(30, 200, 50, h="ok")
    failed = _c(31, h="failed")  # 評価値なし・収集時の値は閾値超え
    failed.score_at_collect, failed.comments_at_collect = 500, 200
    s = select(
        [ok, failed],
        now=NOW,
        min_score=100,
        min_comments=30,
        max_drafts=5,
        max_age_hours=96,
        evaluated={"ok"},
    )
    assert [c.url_hash for c in s.selected] == ["ok"]


def test_評価できなくても期限超過なら打ち切る():
    # 打ち切らないと、毎回 HN に問い合わせ続ける候補が永久に残る
    old = _c(200, h="old")
    s = select(
        [old],
        now=NOW,
        min_score=100,
        min_comments=30,
        max_drafts=5,
        max_age_hours=96,
        evaluated=set(),
    )
    assert [(c.url_hash, r) for c, r in s.to_skip] == [("old", SkipReason.TOO_OLD)]


def test_閾値は満たすが溢れて期限超過した候補も打ち切る():
    # to_skip を failing だけから作ると、この候補が永久に pending のまま残る
    a = _c(200, 500, 99, h="a")
    b = _c(201, 400, 99, h="b")
    s = select(
        [a, b],
        now=NOW,
        min_score=100,
        min_comments=30,
        max_drafts=1,
        max_age_hours=96,
        evaluated={"a", "b"},
    )
    assert [c.url_hash for c in s.selected] == ["a"]
    assert [(c.url_hash, r) for c, r in s.to_skip] == [("b", SkipReason.TOO_OLD)]


def test_evaluatedを渡さなければ全件が選出対象():
    # 純関数として単体で使うときの既定
    s = select(
        [_c(30, 200, 50)],
        now=NOW,
        min_score=100,
        min_comments=30,
        max_drafts=5,
        max_age_hours=96,
    )
    assert len(s.selected) == 1

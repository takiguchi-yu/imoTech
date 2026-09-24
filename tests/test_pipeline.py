"""選別ロジックのテスト。ここが壊れると、薄い記事を量産するか 1 本も書かなくなる。"""

from datetime import UTC, datetime, timedelta

from imotech.models import Candidate, CandidateState, SkipReason, SourceRef, Thresholds
from imotech.pipeline import mark_skipped, matured_candidates, probe_targets, select

NOW = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)


def _select(matured, *, min_score, min_comments, **kw):
    """閾値を 1 組だけ指定する、このファイル用の呼び出し。

    本物の `select` はソースごとに閾値を引く。ここのテストは単一ソースの
    判定を見るものなので、全ソース共通の既定として渡す。
    ソース別に引けることは `test_ソースごとに閾値を引く` で別に確かめる。
    """
    return select(
        matured, thresholds={}, default_thresholds=Thresholds(min_score, min_comments), **kw
    )


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
    s = _select(
        [_c(30, 200, 50), _c(31, 99, 50), _c(32, 200, 29)],
        now=NOW,
        min_score=100,
        min_comments=30,
        max_drafts=5,
        max_age_hours=96,
    )
    assert [c.url_hash for c in s.selected] == ["h30"]


def test_スコア降順で上位N件に絞る():
    s = _select(
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
    s = _select(
        [_c(30, 10, 2)], now=NOW, min_score=100, min_comments=30, max_drafts=5, max_age_hours=96
    )
    assert s.selected == []


def test_期限内で閾値未満なら持ち越す():
    s = _select(
        [_c(30, 10, 2)], now=NOW, min_score=100, min_comments=30, max_drafts=5, max_age_hours=96
    )
    assert s.to_skip == []


def test_期限を過ぎて閾値未満なら打ち切る():
    s = _select(
        [_c(100, 10, 2)], now=NOW, min_score=100, min_comments=30, max_drafts=5, max_age_hours=96
    )
    assert [(c.url_hash, r) for c, r in s.to_skip] == [("h100", SkipReason.BELOW_THRESHOLD)]


def test_期限を過ぎても閾値を満たせば打ち切らない():
    s = _select(
        [_c(100, 500, 99)], now=NOW, min_score=100, min_comments=30, max_drafts=5, max_age_hours=96
    )
    assert s.to_skip == []
    assert [c.url_hash for c in s.selected] == ["h100"]


def test_評価値が無ければ収集時の値で判定する():
    # compose が現在値を取り直せなかった候補。収集時の値に落ちるだけで例外にしない
    c = _c(30)
    s = _select([c], now=NOW, min_score=1, min_comments=1, max_drafts=5, max_age_hours=96)
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
    s = _select(
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
    s = _select(
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
    s = _select(
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
    s = _select(
        [_c(30, 200, 50)],
        now=NOW,
        min_score=100,
        min_comments=30,
        max_drafts=5,
        max_age_hours=96,
    )
    assert len(s.selected) == 1


# --- ソースごとの閾値 -------------------------------------------------------


def _cs(source: str, score: int, comments: int, h: str) -> Candidate:
    return Candidate(
        url_hash=h,
        ref=SourceRef(source, h),
        url=f"https://{source}.example/{h}",
        title="t",
        collected_at=NOW - timedelta(hours=30),
        score_at_collect=0,
        comments_at_collect=0,
        score_at_evaluate=score,
        comments_at_evaluate=comments,
    )


def test_ソースごとに閾値を引く():
    """**ここが無いと Qiita は 1 件も通らない。**

    Hacker News は議論そのものが目的の場なのでコメントが数百付くが、記事
    プラットフォームではほぼ 0 件（実測で 82%）。同じ閾値を当てると片方が死ぬ。
    """
    hn = _cs("hackernews", 200, 50, "hn")
    qiita = _cs("qiita", 50, 0, "qi")
    s = select(
        [hn, qiita],
        now=NOW,
        thresholds={
            "hackernews": Thresholds(min_score=100, min_comments=30),
            "qiita": Thresholds(min_score=30, min_comments=0),
        },
        default_thresholds=Thresholds(min_score=100, min_comments=30),
        max_drafts=5,
        max_age_hours=96,
    )
    assert {c.url_hash for c in s.selected} == {"hn", "qi"}


def test_共通の閾値だけならコメントの無い候補は落ちる():
    # 回帰の向き。ソース別閾値を外すと Qiita がこうなる
    s = select(
        [_cs("qiita", 50, 0, "qi")],
        now=NOW,
        thresholds={},
        default_thresholds=Thresholds(min_score=100, min_comments=30),
        max_drafts=5,
        max_age_hours=96,
    )
    assert s.selected == []


def test_知らないソースの候補は共通の閾値で判定する():
    # 設定から外したソースの候補が候補ストアに残っていても落ちない
    s = select(
        [_cs("gone", 500, 99, "g")],
        now=NOW,
        thresholds={"qiita": Thresholds(min_score=1, min_comments=0)},
        default_thresholds=Thresholds(min_score=100, min_comments=30),
        max_drafts=5,
        max_age_hours=96,
    )
    assert [c.url_hash for c in s.selected] == ["g"]


# --- 話題で優先する（docs/DESIGN.md 4.1c） ---------------------------------


def _pick(cands, topical: set[str], max_drafts: int) -> list[str]:
    s = _select(
        cands,
        now=NOW,
        min_score=100,
        min_comments=0,
        max_drafts=max_drafts,
        max_age_hours=96,
        topics_of=lambda c: ["AI"] if c.url_hash in topical else [],
    )
    return [c.url_hash for c in s.selected]


def test_話題に当たる候補を注目度より先に選ぶ():
    cands = [_c(30, 900, 0, h="hot"), _c(31, 150, 0, h="ai1"), _c(32, 120, 0, h="ai2")]
    assert _pick(cands, {"ai1", "ai2"}, 2) == ["ai1", "ai2"]


def test_話題の候補が足りなければ注目度順に穴埋めする():
    # 0 本の日を作らない
    cands = [_c(30, 900, 0, h="hot"), _c(31, 500, 0, h="warm"), _c(32, 150, 0, h="ai1")]
    assert _pick(cands, {"ai1"}, 3) == ["ai1", "hot", "warm"]


def test_話題でも閾値を満たさなければ選ばない():
    cands = [_c(30, 900, 0, h="hot"), _c(31, 50, 0, h="ai_low")]
    assert _pick(cands, {"ai_low"}, 2) == ["hot"]


def test_話題を渡さなければ従来どおり注目度順():
    cands = [_c(30, 150, 0, h="a"), _c(31, 900, 0, h="b")]
    s = _select(cands, now=NOW, min_score=100, min_comments=0, max_drafts=2, max_age_hours=96)
    assert [c.url_hash for c in s.selected] == ["b", "a"]


def _pc(h, score, topical):
    c = _c(30, h=h)
    c.score_at_collect = score
    return c, topical


def test_問い合わせは話題の候補を先にしつつ枠の一部を話題外に残す():
    # 全部を話題の候補に回すと、話題外は現在値を取られないまま期限切れになり、穴埋めが起きない
    pairs = [_pc(f"on{i}", 10 + i, True) for i in range(10)] + [
        _pc(f"off{i}", 900 + i, False) for i in range(10)
    ]
    topical = {c.url_hash for c, t in pairs if t}
    got = probe_targets([c for c, _ in pairs], limit=8, topics_of=lambda c: c.url_hash in topical)
    on = [c.url_hash for c in got if c.url_hash in topical]
    off = [c.url_hash for c in got if c.url_hash not in topical]
    assert len(got) == 8
    assert len(off) == 2  # 枠の 25%
    assert on[0] == "on9"  # 組の中は収集時スコアの降順
    assert off[0] == "off9"


def test_片方が足りなければもう一方に回す():
    only_on = [_pc(f"on{i}", i, True)[0] for i in range(10)]
    got = probe_targets(only_on, limit=8, topics_of=lambda c: True)
    assert len(got) == 8
    only_off = [_pc(f"off{i}", i, False)[0] for i in range(10)]
    got = probe_targets(only_off, limit=8, topics_of=lambda c: False)
    assert len(got) == 8

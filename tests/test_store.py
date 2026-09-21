"""候補ストアのテスト。重複排除と状態更新が壊れると同じ記事を 2 回書く。"""

from datetime import UTC, datetime

from imotech.models import Candidate, CandidateState
from imotech.store import CandidateStore


def _c(h: str, state=CandidateState.PENDING) -> Candidate:
    return Candidate(
        url_hash=h,
        hn_item_id=int(h, 16) if all(x in "0123456789abcdef" for x in h) else 1,
        url=f"https://e.com/{h}",
        title=f"title {h}",
        collected_at=datetime(2026, 9, 21, tzinfo=UTC),
        score_at_collect=10,
        comments_at_collect=2,
        state=state,
    )


def test_空のストアは空リストを返す(tmp_path):
    assert CandidateStore(tmp_path / "none.jsonl").load() == []


def test_追記と読み戻しで内容が保たれる(tmp_path):
    s = CandidateStore(tmp_path / "c.jsonl")
    assert s.append_new([_c("aa"), _c("bb")]) == 2
    rows = s.load()
    assert [r.url_hash for r in rows] == ["aa", "bb"]
    assert rows[0].collected_at == datetime(2026, 9, 21, tzinfo=UTC)
    assert rows[0].state is CandidateState.PENDING


def test_同じハッシュは二度追加されない(tmp_path):
    s = CandidateStore(tmp_path / "c.jsonl")
    s.append_new([_c("aa")])
    assert s.append_new([_c("aa")]) == 0
    assert len(s.load()) == 1


def test_同一呼び出し内の重複も1件にまとまる(tmp_path):
    s = CandidateStore(tmp_path / "c.jsonl")
    assert s.append_new([_c("aa"), _c("aa"), _c("bb")]) == 2
    assert len(s.load()) == 2


def test_更新は該当行だけを差し替える(tmp_path):
    s = CandidateStore(tmp_path / "c.jsonl")
    s.append_new([_c("aa"), _c("bb")])
    target = _c("bb", state=CandidateState.SKIPPED)
    target.skip_reason = "below_threshold"
    s.update([target])
    rows = {r.url_hash: r for r in s.load()}
    assert rows["aa"].state is CandidateState.PENDING
    assert rows["bb"].state is CandidateState.SKIPPED
    assert rows["bb"].skip_reason == "below_threshold"


def test_pendingだけを取り出す(tmp_path):
    s = CandidateStore(tmp_path / "c.jsonl")
    s.append_new([_c("aa"), _c("bb", state=CandidateState.DRAFTED)])
    assert [c.url_hash for c in s.pending()] == ["aa"]


def test_日本語タイトルが壊れない(tmp_path):
    s = CandidateStore(tmp_path / "c.jsonl")
    c = _c("aa")
    c.title = "日本語の「タイトル」— テスト"
    s.append_new([c])
    assert s.load()[0].title == "日本語の「タイトル」— テスト"


def test_書き込みは一時ファイル経由で置換される(tmp_path):
    # 途中で落ちても本体が壊れないことの担保。tmp が残らないことを見る
    s = CandidateStore(tmp_path / "c.jsonl")
    s.append_new([_c("aa")])
    assert not (tmp_path / "c.jsonl.tmp").exists()

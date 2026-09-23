"""候補ストアのテスト。重複排除と状態更新が壊れると同じ記事を 2 回書く。"""

import json
from datetime import UTC, datetime

import pytest

from imotech.models import Candidate, CandidateState, SourceRef
from imotech.store import CandidateStore


def _c(h: str, state=CandidateState.PENDING) -> Candidate:
    return Candidate(
        url_hash=h,
        ref=SourceRef("hackernews", h),
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


# --- 旧形式との互換性 -------------------------------------------------------
#
# **本番の data/candidates.jsonl 298 行がこの経路に依存している。**
# ソースが 1 つだった頃に書かれた行（`hn_item_id`）を読めなくなると
# パイプラインが止まるので、使い捨てに見えるコードだがテストで守る。


def _legacy_row() -> dict:
    return {
        "url_hash": "abc123",
        "hn_item_id": 49782242,
        "url": "https://e.com/a",
        "title": "t",
        "collected_at": "2026-09-21T00:00:00Z",
        "score_at_collect": 10,
        "comments_at_collect": 2,
        "state": "pending",
    }


def test_旧形式の行はソース名を補って読む(tmp_path):
    path = tmp_path / "c.jsonl"
    path.write_text(json.dumps(_legacy_row()) + "\n", encoding="utf-8")
    got = CandidateStore(path).load()[0]
    assert got.ref == SourceRef("hackernews", "49782242")
    # 議論の URL は組み立てない（URL の規則はソースの知識）。次の評価で埋まる
    assert got.discussion_url == ""


def test_旧形式を読んで保存すると新形式になる(tmp_path):
    path = tmp_path / "c.jsonl"
    path.write_text(json.dumps(_legacy_row()) + "\n", encoding="utf-8")
    store = CandidateStore(path)
    store.save(store.load())
    row = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert row["source"] == "hackernews" and row["source_id"] == "49782242"
    assert "hn_item_id" not in row
    # 書き戻したものをもう一度読めること（往復の安定）
    assert CandidateStore(path).load()[0].ref == SourceRef("hackernews", "49782242")


def test_識別子を持たない行は読めない(tmp_path):
    # 黙って空の SourceRef を作ると、どの候補か分からないまま処理が進む
    path = tmp_path / "c.jsonl"
    broken = {k: v for k, v in _legacy_row().items() if k != "hn_item_id"}
    path.write_text(json.dumps(broken) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        CandidateStore(path).load()

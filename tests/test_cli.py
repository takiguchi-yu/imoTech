"""CLI のテスト。ネットワークに出ない部分の挙動を固定する。"""

import contextlib
import io
from datetime import UTC, datetime, timedelta

import pytest

from imotech.cli import _apply_skips, build_parser, cmd_stats
from imotech.config import Settings
from imotech.models import Candidate, CandidateState, SkipReason
from imotech.store import CandidateStore


def _c(h: str, hours_ago: int = 30) -> Candidate:
    return Candidate(
        url_hash=h,
        hn_item_id=1,
        url=f"https://e.com/{h}",
        title="t",
        collected_at=datetime.now(UTC) - timedelta(hours=hours_ago),
        score_at_collect=10,
        comments_at_collect=2,
    )


def test_dry_runでは打ち切りを書き込まない(tmp_path, capsys):
    store = CandidateStore(tmp_path / "c.jsonl")
    store.append_new([_c("aa")])
    _apply_skips(store, [(_c("aa"), SkipReason.BELOW_THRESHOLD)], dry_run=True)
    assert store.load()[0].state is CandidateState.PENDING
    assert "書き込みません" in capsys.readouterr().out


def test_dry_runでなければ打ち切りを書き込む(tmp_path, capsys):
    store = CandidateStore(tmp_path / "c.jsonl")
    store.append_new([_c("aa")])
    _apply_skips(store, [(_c("aa"), SkipReason.BELOW_THRESHOLD)], dry_run=False)
    row = store.load()[0]
    assert row.state is CandidateState.SKIPPED
    assert row.skip_reason == "below_threshold"
    # 理由の内訳を出さないと、何がどう打ち切られたか追えない
    assert "below_threshold=1" in capsys.readouterr().out


def test_打ち切りが空なら何もしない(tmp_path, capsys):
    store = CandidateStore(tmp_path / "c.jsonl")
    _apply_skips(store, [], dry_run=False)
    assert capsys.readouterr().out == ""


def test_statsは空ストアで次の一手を示す(tmp_path, capsys):
    s = Settings(candidates_path=tmp_path / "none.jsonl")
    assert cmd_stats(s, None) == 0
    out = capsys.readouterr().out
    assert "空です" in out
    assert "imotech collect" in out
    # どのファイルを見ているかを出さないと、パスの打ち間違いに気づけない
    assert str(tmp_path / "none.jsonl") in out


def test_statsが状態の内訳を出す(tmp_path, capsys):
    store = CandidateStore(tmp_path / "c.jsonl")
    a, b = _c("aa"), _c("bb")
    b.state = CandidateState.SKIPPED
    b.skip_reason = "below_threshold"
    b.score_at_evaluate = 40
    store.append_new([a, b])
    cmd_stats(Settings(candidates_path=tmp_path / "c.jsonl"), None)
    out = capsys.readouterr().out
    assert "pending=1" in out and "skipped=1" in out
    assert "below_threshold=1" in out


# --- パーサ ---------------------------------------------------------------


def test_サブコマンドは必須():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_limitの既定値が環境変数名つきでヘルプに出る():
    # 「既定は設定値」だけでは、どこを変えればよいか分からない
    p = build_parser(Settings(max_drafts_per_run=7))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), pytest.raises(SystemExit):
        p.parse_args(["compose", "--help"])
    assert "既定 7" in buf.getvalue()
    assert "IMOTECH_MAX_DRAFTS_PER_RUN" in buf.getvalue()


def test_dry_runの既定はFalse():
    assert build_parser().parse_args(["compose"]).dry_run is False
    assert build_parser().parse_args(["compose", "--dry-run"]).dry_run is True

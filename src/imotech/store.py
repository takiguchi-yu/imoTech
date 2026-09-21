"""候補ストア。jsonl の読み書きをこのモジュールだけに閉じる（Repository）。

永続化形式を SQLite に替えても、呼び出し側の cli.py は変わらないようにしてある。
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from .models import Candidate, CandidateState


def _to_rfc3339(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _from_rfc3339(s: str | None) -> datetime | None:
    """RFC3339 を aware な datetime にする。

    タイムゾーンの無い値が混ざっても UTC とみなす。naive を返すと、あとで
    aware な now と比較したときに TypeError になる。
    """
    if not s:
        return None
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _to_dict(c: Candidate) -> dict:
    return {
        "url_hash": c.url_hash,
        "hn_item_id": c.hn_item_id,
        "url": c.url,
        "title": c.title,
        "collected_at": _to_rfc3339(c.collected_at),
        "score_at_collect": c.score_at_collect,
        "comments_at_collect": c.comments_at_collect,
        "state": c.state.value,
        "evaluated_at": _to_rfc3339(c.evaluated_at),
        "score_at_evaluate": c.score_at_evaluate,
        "comments_at_evaluate": c.comments_at_evaluate,
        "notion_page_id": c.notion_page_id,
        "skip_reason": c.skip_reason,
    }


def _from_dict(d: dict) -> Candidate:
    return Candidate(
        url_hash=d["url_hash"],
        hn_item_id=d["hn_item_id"],
        url=d["url"],
        title=d["title"],
        collected_at=_from_rfc3339(d["collected_at"]),
        score_at_collect=d["score_at_collect"],
        comments_at_collect=d["comments_at_collect"],
        state=CandidateState(d.get("state", "pending")),
        evaluated_at=_from_rfc3339(d.get("evaluated_at")),
        score_at_evaluate=d.get("score_at_evaluate"),
        comments_at_evaluate=d.get("comments_at_evaluate"),
        notion_page_id=d.get("notion_page_id"),
        skip_reason=d.get("skip_reason"),
    )


class CandidateStore:
    """data/candidates.jsonl を読み書きする。

    件数が数千行の規模を想定しており、更新は全件を読み直して書き戻す。
    書き込みは一時ファイル経由の置換にして、途中で落ちてもファイルが壊れないようにする。
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def load(self) -> list[Candidate]:
        if not self.path.exists():
            return []
        out: list[Candidate] = []
        with self.path.open(encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(_from_dict(json.loads(line)))
                except (json.JSONDecodeError, KeyError) as e:
                    raise ValueError(f"{self.path}:{lineno} を読めない: {e}") from e
        return out

    def save(self, candidates: list[Candidate]) -> None:
        """一時ファイルに書いてから置換する。

        一時ファイル名に PID を入れるのは、cron と workflow_dispatch が重なったときに
        2 プロセスが同じ一時ファイルを奪い合って内容が混ざるのを防ぐため。
        fsync は電源断でサイズ 0 のファイルが残るのを防ぐ。
        なお read-modify-write そのものは排他していないので、同時実行では後勝ちになる
        （M3 で concurrency グループを設定して同時実行自体を防ぐ方針）。
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(f"{self.path.suffix}.{os.getpid()}.tmp")
        try:
            with tmp.open("w", encoding="utf-8") as f:
                for c in candidates:
                    f.write(json.dumps(_to_dict(c), ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
            tmp.replace(self.path)
        finally:
            tmp.unlink(missing_ok=True)

    def known_hashes(self) -> set[str]:
        return {c.url_hash for c in self.load()}

    def append_new(self, candidates: list[Candidate]) -> int:
        """まだ無い url_hash のものだけ追記し、追加した件数を返す。

        同じ実行内に重複が含まれていても 1 件にまとめる。
        """
        existing = self.load()
        seen = {c.url_hash for c in existing}
        added = 0
        for c in candidates:
            if c.url_hash in seen:
                continue
            seen.add(c.url_hash)
            existing.append(c)
            added += 1
        if added:
            self.save(existing)
        return added

    def update(self, updated: list[Candidate]) -> None:
        """url_hash が一致する行を差し替える。存在しないものは無視する。"""
        by_hash = {c.url_hash: c for c in updated}
        if not by_hash:
            return
        rows = self.load()
        for i, row in enumerate(rows):
            if row.url_hash in by_hash:
                rows[i] = by_hash[row.url_hash]
        self.save(rows)

    def pending(self) -> list[Candidate]:
        return [c for c in self.load() if c.state is CandidateState.PENDING]

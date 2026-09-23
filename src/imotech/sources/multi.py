"""複数のソースを 1 つとして扱う（GoF: Composite）。

呼び出し側（`cli.py`）はソースが 1 つでも 5 つでも同じコードで扱える。
`Candidate.ref.source` を見て、反応の取得は元のソースへ振り分ける。
"""

from __future__ import annotations

from collections.abc import Sequence

from ..models import Reaction, SourceRef, Story
from . import StoryFeed, supports_reactions


class MultiFeed:
    """束ねたソースをまとめて 1 つの `StoryFeed` / `ReactionSource` に見せる。

    **`limit` は全体の上限**。各ソースから `limit` 件ずつ取ってから、注目度の順に
    並べて上位を返す。ソースごとに件数を割り当てないのは、盛り上がりが偏る日に
    「静かなソースの枠が空いたまま」になるのを避けるため。
    """

    def __init__(self, feeds: Sequence[StoryFeed]) -> None:
        if not feeds:
            raise ValueError("ソースが 1 つも指定されていません")
        self._feeds = list(feeds)
        # 障害時にログを読む人が「何を使ったか」を追えるよう、内訳を名前に入れる
        self.name = f"multi({','.join(f.name for f in self._feeds)})"

    @property
    def feeds(self) -> list[StoryFeed]:
        return list(self._feeds)

    def fetch_stories(
        self, *, window_hours: int = 24, min_points: int = 10, limit: int = 50
    ) -> list[Story]:
        out: list[Story] = []
        failed: list[str] = []
        for feed in self._feeds:
            # 1 つのソースが落ちても他は使う。収集はベストエフォートでよい
            # （次回の実行が拾い直す — docs/DESIGN.md 5.5）
            try:
                out.extend(
                    feed.fetch_stories(
                        window_hours=window_hours, min_points=min_points, limit=limit
                    )
                )
            except Exception as e:  # noqa: BLE001 — ソース側の例外の型を呼び出し側が知らない
                failed.append(feed.name)
                print(f"  [warn] {feed.name} からの収集に失敗: {e}", flush=True)
        # **全部落ちたら握り潰さない。** 0 件で正常終了すると、候補が枯れて
        # 記事が出なくなっても無人実行では誰も気づけない（docs/DESIGN.md 5.5）
        if len(failed) == len(self._feeds):
            raise RuntimeError(f"すべてのソースからの収集に失敗しました: {', '.join(failed)}")
        out.sort(key=lambda s: (-s.engagement.score, -s.engagement.comments))
        return out[:limit]

    def fetch_reactions(self, ref: SourceRef) -> tuple[Story | None, list[Reaction]]:
        """候補が拾われたソースへ振り分ける。

        反応を持たないソース（RSS など）や、束ねていないソースの候補は `(None, [])`。
        呼び出し側から見ると「反応が取れなかった」と同じ扱いになる。
        """
        for feed in self._feeds:
            if feed.name == ref.source and supports_reactions(feed):
                return feed.fetch_reactions(ref)
        return None, []

    def close(self) -> None:
        for feed in self._feeds:
            close = getattr(feed, "close", None)
            if callable(close):
                close()

    def __enter__(self) -> MultiFeed:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

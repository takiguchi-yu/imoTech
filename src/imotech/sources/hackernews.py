"""Hacker News からの収集と反応取得。

コメント木は Algolia の /api/v1/items/<id> で 1 リクエストで取る。Firebase API で
kids を再帰的に辿ると 1 記事で数百リクエストになるため使わない（docs/DESIGN.md 5.3）。
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

import httpx

from ..models import Reaction, Story

ALGOLIA_BASE = "https://hn.algolia.com/api/v1"
NAME = "hackernews"


class HackerNews:
    """StoryFeed と ReactionSource の両方を満たす。"""

    name = NAME

    def __init__(
        self,
        *,
        timeout: float = 15.0,
        user_agent: str = "imoTechBot/1.0",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        # transport はテストからネットワークを差し替えるための口
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": user_agent},
            follow_redirects=True,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HackerNews:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # --- HTTP -------------------------------------------------------------

    def _get(self, path: str, params: dict | None = None, *, attempts: int = 3) -> dict | None:
        """指数バックオフつきの GET。全滅したら None を返し、呼び出し側で判断させる。"""
        last: Exception | None = None
        for i in range(attempts):
            try:
                r = self._client.get(f"{ALGOLIA_BASE}{path}", params=params)
                if r.status_code >= 500:
                    raise httpx.HTTPStatusError(f"{r.status_code}", request=r.request, response=r)
                r.raise_for_status()
                return r.json()
            except (httpx.HTTPError, ValueError) as e:
                last = e
                if i < attempts - 1:
                    time.sleep(2**i)
        if last is not None:
            print(f"  [warn] HN {path} の取得に失敗: {last}")
        return None

    # --- StoryFeed --------------------------------------------------------

    def fetch_stories(
        self,
        *,
        window_hours: int = 24,
        min_points: int = 10,
        limit: int = 50,
        max_pages: int = 5,
    ) -> list[Story]:
        """条件に合う story を返す。

        Algolia は 1 ページ hitsPerPage 件までしか返さない。1 ページで打ち切ると
        条件に合う話題を取りこぼす（実測で 89 件中 39 件を落としていた）。
        nbPages を見て追うが、暴走しないよう max_pages で天井を置く。
        """
        since = int((datetime.now(UTC) - timedelta(hours=window_hours)).timestamp())
        out: list[Story] = []
        page = 0
        while page < max_pages:
            data = self._get(
                "/search_by_date",
                {
                    "tags": "story",
                    "numericFilters": f"created_at_i>{since},points>{min_points}",
                    "hitsPerPage": limit,
                    "page": page,
                },
            )
            if not data:
                break
            for hit in data.get("hits") or []:
                story = _story_from_hit(hit)
                if story is not None:
                    out.append(story)
            nb_pages = int(data.get("nbPages") or 1)
            page += 1
            if page >= nb_pages:
                break
        return out

    # --- ReactionSource ---------------------------------------------------

    def fetch_reactions(self, story_id: int) -> tuple[Story | None, list[Reaction]]:
        data = self._get(f"/items/{story_id}")
        if not data:
            return None, []
        story = _story_from_item(data)
        return story, _walk_comments(data)


def _story_from_hit(hit: dict) -> Story | None:
    """search_by_date の 1 件を Story にする。url が無いもの（Ask HN 等）は捨てる。"""
    url = hit.get("url")
    if not url:
        return None
    object_id = hit.get("objectID")
    created = hit.get("created_at_i")
    if object_id is None or created is None:
        return None
    return Story(
        hn_item_id=int(object_id),
        url=url,
        title=hit.get("title") or "",
        points=int(hit.get("points") or 0),
        num_comments=int(hit.get("num_comments") or 0),
        created_at=datetime.fromtimestamp(int(created), tz=UTC),
    )


def _story_from_item(item: dict) -> Story | None:
    url = item.get("url")
    item_id = item.get("id")
    created = item.get("created_at_i")
    if not url or item_id is None or created is None:
        return None
    return Story(
        hn_item_id=int(item_id),
        url=url,
        title=item.get("title") or "",
        points=int(item.get("points") or 0),
        num_comments=_count_comments(item),
        created_at=datetime.fromtimestamp(int(created), tz=UTC),
    )


def _count_comments(node: dict) -> int:
    """text を持つノードを数える。

    /items/<id> は num_comments を返さないため自前で数える。Algolia の集計値
    （_story_from_hit 側）は削除済みも含むので、評価時のほうがやや小さく出る。
    閾値判定はどちらも同じ min_comments に当たるので、この差は「評価時のほうが
    厳しめに出る」方向に働く。
    """
    n = 0
    for child in node.get("children") or []:
        if child.get("text"):
            n += 1
        n += _count_comments(child)
    return n


MAX_COMMENT_DEPTH = 40


def _walk_comments(node: dict, depth: int = 0) -> list[Reaction]:
    """コメント木を深さ優先で平坦化する。削除済み（text が null）はスキップする。

    深さに上限を置くのは、壊れた応答や極端に深いスレッドで RecursionError に
    しないため。40 段より深い枝は議論の本筋から外れている。
    """
    if depth > MAX_COMMENT_DEPTH:
        return []
    out: list[Reaction] = []
    for child in node.get("children") or []:
        text = child.get("text")
        if text:
            out.append(
                Reaction(
                    comment_id=int(child.get("id") or 0),
                    author=child.get("author"),
                    text=text,
                    depth=depth,
                    reply_count=len(child.get("children") or []),
                )
            )
        out.extend(_walk_comments(child, depth + 1))
    return out

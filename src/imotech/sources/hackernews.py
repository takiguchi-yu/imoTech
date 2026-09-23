"""Hacker News からの収集と反応取得。

コメント木は Algolia の /api/v1/items/<id> で 1 リクエストで取る。Firebase API で
kids を再帰的に辿ると 1 記事で数百リクエストになるため使わない（docs/DESIGN.md 5.3）。
"""

from __future__ import annotations

import re
import time
from datetime import UTC, datetime, timedelta

import httpx

from ..models import Engagement, Reaction, SourceRef, Story

ALGOLIA_BASE = "https://hn.algolia.com/api/v1"
NAME = "hackernews"

#: 投稿者のプロフィールページ。匿名化で伏せ字にする（`anonymize.scrub` が使う）。
#: **URL の形はソースごとに違う**ので、パターンはソース側が持つ。
PROFILE_URL_RE = re.compile(
    r"https?://(?:www\.)?news\.ycombinator\.com/user\?id=[A-Za-z0-9_-]+", re.IGNORECASE
)


class HackerNews:
    """StoryFeed と ReactionSource の両方を満たす。"""

    name = NAME
    profile_url_re = PROFILE_URL_RE

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

    def fetch_reactions(self, ref: SourceRef) -> tuple[Story | None, list[Reaction]]:
        # 別のソースで拾った候補が回ってくることがある（設定を変えた後など）。
        # MultiFeed は name で振り分けるが、単一で使うときは誰も見ないので
        # ここで確かめる。**ID が数値のソースが増えると別記事を掴む**
        if ref.source != self.name:
            return None, []
        data = self._get(f"/items/{ref.id}")
        if not data:
            return None, []
        story = _story_from_item(data)
        return story, _walk_comments(data)


def discussion_url(item_id: str | int) -> str:
    """スレッドの URL。**Hacker News では元記事とは別の場所**にある。"""
    return f"https://news.ycombinator.com/item?id={item_id}"


def _ref(item_id: str | int) -> SourceRef:
    return SourceRef(source=NAME, id=str(item_id))


# --- Adapter: Algolia の返す形を models の型に変える -----------------------
# API の項目名（objectID / created_at_i / num_comments）を知っているのはここだけ。
# 別のソースを足すときは、そのソース用の同じ役割の関数をそのモジュールに書く。


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
        ref=_ref(object_id),
        url=url,
        title=hit.get("title") or "",
        engagement=Engagement(
            score=int(hit.get("points") or 0),
            comments=int(hit.get("num_comments") or 0),
        ),
        created_at=datetime.fromtimestamp(int(created), tz=UTC),
        discussion_url=discussion_url(object_id),
        author=hit.get("author") or None,
    )


def _story_from_item(item: dict) -> Story | None:
    url = item.get("url")
    item_id = item.get("id")
    created = item.get("created_at_i")
    if not url or item_id is None or created is None:
        return None
    return Story(
        ref=_ref(item_id),
        url=url,
        title=item.get("title") or "",
        engagement=Engagement(
            score=int(item.get("points") or 0),
            comments=_count_comments(item),
        ),
        created_at=datetime.fromtimestamp(int(created), tz=UTC),
        discussion_url=discussion_url(item_id),
        author=item.get("author") or None,
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
                    comment_id=str(child.get("id") or ""),
                    author=child.get("author"),
                    text=text,
                    depth=depth,
                    reply_count=len(child.get("children") or []),
                )
            )
        out.extend(_walk_comments(child, depth + 1))
    return out

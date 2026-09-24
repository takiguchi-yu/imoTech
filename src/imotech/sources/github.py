"""GitHub からの収集（急上昇中の新しいリポジトリ）。

| | Hacker News | GitHub |
|---|---|---|
| Story の実体 | 外部記事への投稿 | **リポジトリそのもの** |
| 注目度 | points | **stars** |
| 反応 | コメント | **無い**（Issue は議論ではなく不具合報告なので使わない） |
| 記事の本文 | 元記事のページ | **README**（API で取る。`fetch_article`） |
| URL に個人のハンドル | 入らない | **入る**（`github.com/<owner>/<repo>`） |

**取得は REST API だけ。** Trending のページや HTML を取りに行かない — GitHub の
Acceptable Use Policies はスクレイピングの用途を研究とアーカイブに限っており、
"Scraping does not refer to the collection of information through our API" と API を
対象外にしている
（https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies ）。

API: https://docs.github.com/en/rest/search/search#search-repositories
レート: 認証なし 60 req/h（検索は 10 req/min）、トークンありで 5,000 req/h
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

import httpx

from ..models import Engagement, Reaction, SourceRef, Story, Thresholds

API_BASE = "https://api.github.com"
NAME = "github"

#: README の上限。これを超える README は本文にしない
MAX_README_BYTES = 2 * 1024 * 1024

#: 検索する範囲。**作成からこの日数以内**のリポジトリ（ユーザーの判断: 急上昇中の新しいもの）
CREATED_WITHIN_DAYS = 30

#: 所有者のプロフィールページ。**リポジトリの URL には当てない**（出典が消える）。
#: リポジトリの URL に入るハンドルは `Story.author` で伏せる
PROFILE_URL_RE = re.compile(
    r"https?://(?:www\.)?github\.com/"
    # ユーザー名ではないトップレベルのパス
    r"(?!orgs/|topics/|features/|about\b|pricing\b|marketplace\b|search\b|trending\b)"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})"
    r"/?"
    r"(?![A-Za-z0-9_./-])",
    re.IGNORECASE,
)


class GitHub:
    """StoryFeed / ReactionSource / ArticleProvider を満たす。反応は常に 0 件。"""

    name = NAME
    profile_url_re = PROFILE_URL_RE
    #: 実測（2026-09-24）: 作成 30 日以内の stars 上位 30 件は 2,500〜21,000 stars。
    #: 1,000 を下限にすると 1 日数件が通る見込み（運用で `stats` を見て動かす）
    default_thresholds = Thresholds(min_score=1000, min_comments=0)
    #: **stars は Hacker News の points と桁が違う**（数千〜数万 対 数百）。注目度順に並べると
    #: 枠を独占するので、1 回の実行で記事にする本数と、収集する件数に上限を置く
    #: （`sources.per_run_caps` / `collect_quotas`）。2 本は自分で決めた値（運用で動かす）
    max_per_run = 2
    collect_quota = 10

    def __init__(
        self,
        *,
        timeout: float = 15.0,
        user_agent: str = "imoTechBot/1.0",
        token: str = "",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(
            timeout=timeout, headers=headers, follow_redirects=True, transport=transport
        )
        #: レート上限に当たったら、同じ実行の中では以降を叩かない
        self._rate_exhausted = False

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> GitHub:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _get(self, path: str, params: dict | None = None, **kw) -> httpx.Response | None:
        if self._rate_exhausted:
            return None
        try:
            r = self._client.get(f"{API_BASE}{path}", params=params, **kw)
        except httpx.HTTPError as e:
            print(f"  [warn] GitHub に到達できません（{path}）: {type(e).__name__}", flush=True)
            return None
        # 一次の上限は remaining=0、二次の上限（短時間の叩きすぎ）は retry-after で返る
        if r.status_code in (403, 429) and (
            r.headers.get("x-ratelimit-remaining") == "0" or "retry-after" in r.headers
        ):
            print("  [warn] GitHub の API のレート上限に達しました。次回に回します", flush=True)
            self._rate_exhausted = True
            return None
        if r.status_code >= 400:
            return None
        return r

    # --- StoryFeed --------------------------------------------------------

    def fetch_stories(
        self,
        *,
        window_hours: int = 24,  # noqa: ARG002 — 作成日の範囲は CREATED_WITHIN_DAYS で決める
        min_points: int = 10,  # noqa: ARG002 — 閾値は熟成後に stars で判定する
        limit: int = 50,
    ) -> list[Story]:
        """作成から CREATED_WITHIN_DAYS 日以内の、stars の多いリポジトリ。"""
        since = (datetime.now(UTC) - timedelta(days=CREATED_WITHIN_DAYS)).strftime("%Y-%m-%d")
        r = self._get(
            "/search/repositories",
            {
                "q": f"created:>={since} fork:false archived:false",
                "sort": "stars",
                "order": "desc",
                "per_page": min(max(limit, 1), 100),
            },
        )
        if r is None:
            raise RuntimeError("GitHub の検索に失敗しました")
        try:
            items = r.json().get("items") or []
        except ValueError as e:
            raise RuntimeError("GitHub の検索の応答を読めませんでした") from e
        return [s for s in map(_story_from_repo, items) if s is not None][:limit]

    # --- ReactionSource ---------------------------------------------------

    def fetch_reactions(self, ref: SourceRef) -> tuple[Story | None, list[Reaction]]:
        """現在の stars と、空の反応。"""
        if ref.source != self.name:
            return None, []
        r = self._get(f"/repositories/{ref.id}")
        if r is None:
            return None, []
        try:
            return _story_from_repo(r.json()), []
        except (ValueError, TypeError, AttributeError):
            # compose を止めない（問い合わせのループは例外を握らない）
            return None, []

    # --- ArticleProvider --------------------------------------------------

    def fetch_article(self, ref: SourceRef) -> str | None:
        """README の本文（Markdown のまま）。無ければ None。

        リポジトリのページ（HTML）は取りに行かない（モジュールの docstring 参照）。
        """
        if ref.source != self.name:
            return None
        r = self._get(
            f"/repositories/{ref.id}/readme",
            headers={"Accept": "application/vnd.github.raw+json"},
        )
        if r is None:
            return None
        text = r.text.strip()
        # 本文は後で max_chars で切るが、極端に大きい README は読み込みの段で捨てる
        if len(r.content) > MAX_README_BYTES:
            return None
        return text or None


def _story_from_repo(repo: dict) -> Story | None:
    """リポジトリ 1 件を Story にする。フォーク・アーカイブ・非公開は捨てる。"""
    if repo.get("private") or repo.get("fork") or repo.get("archived"):
        return None
    repo_id = repo.get("id")
    url = repo.get("html_url")
    name = repo.get("name")
    created = repo.get("created_at")
    if not repo_id or not url or not name or not created:
        return None
    description = (repo.get("description") or "").strip()
    owner = (repo.get("owner") or {}).get("login") or None
    return Story(
        ref=SourceRef(source=NAME, id=str(repo_id)),
        url=url,
        # **所有者のハンドルをタイトルに入れない**（owner/repo ではなく repo だけ）
        title=f"{name}: {description}" if description else name,
        engagement=Engagement(score=int(repo.get("stargazers_count") or 0), comments=0),
        created_at=datetime.fromisoformat(created.replace("Z", "+00:00")),
        discussion_url=url,
        # URL に入るので、伏せないと LLM と公開記事にハンドルが残る。組織でも個人でも伏せる
        author=owner,
    )

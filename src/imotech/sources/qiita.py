"""Qiita からの収集と反応取得。

Hacker News との違いが、このファイルのほとんどを説明する。

| | Hacker News | Qiita |
|---|---|---|
| Story の実体 | 外部記事への投稿 | **記事そのもの** |
| 議論の場所 | スレッド（記事とは別 URL） | **記事ページ自身**（`url == discussion_url`） |
| 注目度 | points | **LGTM**（`likes_count`） |
| 検索の絞り込み | points で絞れる | **ストック数でしか絞れない**（LGTM の条件は無い） |
| コメント | 議論が主体、数百付く | **ほぼ付かない**（実測で 82% が 0 件） |
| 記事 URL に著者名 | 入らない（第三者のブログ） | **入る**（`qiita.com/<user_id>/items/<id>`） |

最後の行が匿名化に効く。元記事の URL をそのまま LLM に渡すと著者のハンドルが載るため、
`Story.author` に入れて呼び出し側が伏せられるようにしてある。

API: https://qiita.com/api/v2/docs （非認証 60 req/h/IP、認証 1000 req/h）
検索の書式: https://help.qiita.com/ja/articles/qiita-search-options
"""

from __future__ import annotations

import re
import time
from datetime import UTC, datetime, timedelta, timezone

import httpx

from ..models import Engagement, Reaction, SourceRef, Story, Thresholds

#: 警告に出す回復時刻のタイムゾーン。運用者が日本にいる前提（README も JST 表記）
JST = timezone(timedelta(hours=9))

API_BASE = "https://qiita.com/api/v2"
NAME = "qiita"

#: 投稿者のプロフィールページ。**個別記事の URL には当てない**。
#:
#: `qiita.com/<user_id>` だけでなく、その配下のユーザーページ（`/likes` `/followers`
#: `/stocks` `/contributions` `/items` = 記事一覧）も伏せる。いずれも実在するページで、
#: **ハンドルがそのまま URL に出る**。ここを拾い漏らすと、スレッド参加者以外の
#: ハンドルが伏せ字から抜ける（`anonymize.py` がこのパターンを持つ理由そのもの）。
#:
#: 一方 `qiita.com/<user_id>/items/<id>` は**元記事そのもの**なので当てない。
#: 丸ごと伏せると出典のリンクが消える。この URL に含まれるハンドルは
#: `Story.author` を `anonymize` の `extra_handles` に渡して伏せる。
PROFILE_URL_RE = re.compile(
    r"https?://(?:www\.)?qiita\.com/"
    # ユーザー名ではないトップレベルのパス
    r"(?!api/|tags?/|organizations/|search\b|trend\b)"
    r"[A-Za-z0-9_-]+"
    # ユーザーページのサブパス。`/items/<id>` は個別記事なので、ここに `items` が
    # 当たっても末尾の否定先読みで落ちる
    r"(?:/(?:likes|followers|following|stocks|contributions|items|drafts))?"
    r"/?"
    r"(?![A-Za-z0-9_/-])",
    re.IGNORECASE,
)

#: 検索で母数を絞る下限（`stocks:>N`）。**LGTM では絞れない**ので、ストック数を使う。
#:
#: 実測（2026-09-23、直近 24 時間）: `stocks:>0` で 32 件、`stocks:>1` で 5 件。
#: **収集は投稿直後の記事を拾う**ので、この時点ではストックも LGTM もほとんど付いて
#: いない（直近 24h の記事は LGTM が最大 6 だった）。強く絞ると候補が枯れるため、
#: 「1 人でもストックした」を下限にする。絞り込みは熟成後の再評価に任せる。
SEARCH_MIN_STOCKS = 0

#: 1 ページあたりの件数。API の上限が 100（`per_page` は 1〜100）。
PER_PAGE = 100


class Qiita:
    """StoryFeed と ReactionSource の両方を満たす。

    `token` を渡すと認証ありになり、レート上限が 60 req/h から 1000 req/h に上がる。
    **無くても動く** — 1 回の実行で使うのは数リクエストなので、非認証で足りる。
    """

    name = NAME
    profile_url_re = PROFILE_URL_RE

    #: Qiita は記事にコメントがほぼ付かない（実測で 82% が 0 件、最多でも 9 件）。
    #: Hacker News 用の共通設定（コメント 30 件以上）を当てると 1 件も通らないので、
    #: **コメント数を見ない**。代わりに LGTM の下限を高めに取る。
    #: 実測（7 日間）: LGTM>=30 が 14 件 ≒ 1 日 2 件で、1 回の記事化上限に見合う。
    default_thresholds = Thresholds(min_score=30, min_comments=0)

    def __init__(
        self,
        *,
        timeout: float = 15.0,
        user_agent: str = "imoTechBot/1.0",
        token: str = "",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        headers = {"User-Agent": user_agent}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        # transport はテストからネットワークを差し替えるための口
        self._client = httpx.Client(
            timeout=timeout,
            headers=headers,
            follow_redirects=True,
            transport=transport,
        )
        #: 直近の応答の `Rate-Remaining`。分かるまでは None
        self.rate_remaining: int | None = None
        #: レートが回復する時刻（`Rate-Reset`、UNIX 秒）。分かるまでは None
        self.rate_reset: int | None = None
        self._rate_exhausted = False
        self._rate_warned = False

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Qiita:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # --- HTTP -------------------------------------------------------------

    def _request(self, path: str, params: dict | None = None, *, attempts: int = 3) -> object:
        """GET して JSON を返す。取れなければ None。

        **レート超過を検出したら、以降のリクエストを送らない。** Qiita は超過時に
        429 ではなく **403 + `{"type": "rate_limit_exceeded"}`** を返す（実測）。
        上限は時間単位でのリセットなので、数秒待っても回復しない。1 回の実行で
        60 件の候補を問い合わせると非認証の 60 req/h を使い切るため、
        気づかず撃ち続けると残り全部が無駄になる。
        """
        if self._rate_exhausted:
            return None
        last: Exception | None = None
        for i in range(attempts):
            try:
                r = self._client.get(f"{API_BASE}{path}", params=params)
                self._remember_rate(r)
                if self._is_rate_limited(r):
                    self._note_rate_exhausted(path)
                    return None
                if r.status_code >= 500:
                    raise httpx.HTTPStatusError(f"{r.status_code}", request=r.request, response=r)
                # **4xx はリトライしない。** 削除済み記事（404）や権限エラーは
                # 待っても変わらないのに、1 件で 3 リクエストを食う。
                # 非認証の 60 req/h が実運用の天井なので、無駄打ちが直接効く
                if r.status_code >= 400:
                    print(f"  [warn] Qiita {path} が {r.status_code} を返しました")
                    return None
                return r.json()
            except (httpx.HTTPError, ValueError) as e:
                last = e
                if i < attempts - 1:
                    time.sleep(2**i)
        if last is not None:
            print(f"  [warn] Qiita {path} の取得に失敗: {last}")
        return None

    def _remember_rate(self, response: httpx.Response) -> None:
        """レートのヘッダを覚える。残りが尽きたら次から撃たない。

        `Rate-Reset` も覚えるのは、**いつ回復するか**を警告に書くため。
        上限は時間単位でのリセットなので、運用者が「次の実行で直るのか、
        設定を下げるべきか」を判断できる。
        """
        self.rate_reset = _as_int(response.headers.get("Rate-Reset")) or self.rate_reset
        remaining = _as_int(response.headers.get("Rate-Remaining"))
        if remaining is None:
            return
        self.rate_remaining = remaining
        if remaining <= 0:
            self._rate_exhausted = True

    @staticmethod
    def _is_rate_limited(response: httpx.Response) -> bool:
        """レート超過か。403 は権限エラーでもあるので本文の type で見分ける。"""
        if response.status_code == 429:
            return True
        if response.status_code != 403:
            return False
        try:
            body = response.json()
        except ValueError:
            return False
        return isinstance(body, dict) and body.get("type") == "rate_limit_exceeded"

    def _note_rate_exhausted(self, path: str) -> None:
        """超過は 1 回だけ知らせる。候補の数だけ warn が並ぶとログが読めない。

        **次の一手が分かる文面にする。** 無人実行のログを後から読む人が、
        放っておけば直るのか設定を変えるべきかを判断できるようにする。
        """
        self._rate_exhausted = True
        if self._rate_warned:
            return
        self._rate_warned = True
        when = _reset_at(self.rate_reset)
        print(
            f"  [warn] Qiita のレート上限（非認証 60 req/h）に達しました（{path}）。"
            f"残りの候補はこの実行では問い合わせず、次回に回します。"
            f"{when}毎回ここで止まるなら IMOTECH_MAX_PROBES_PER_RUN を下げてください。"
        )

    def _get(self, path: str, params: dict | None = None) -> list | None:
        data = self._request(path, params)
        return data if isinstance(data, list) else None

    def _get_one(self, path: str) -> dict | None:
        data = self._request(path)
        return data if isinstance(data, dict) else None

    # --- StoryFeed --------------------------------------------------------

    def fetch_stories(
        self,
        *,
        window_hours: int = 24,
        min_points: int = 10,  # noqa: ARG002 — Protocol の形を満たすため受け取る（下記参照）
        limit: int = 50,
        max_pages: int = 3,
    ) -> list[Story]:
        """条件に合う記事を返す。

        **`min_points` は使わない。** 収集は投稿直後の記事を拾う段で、Qiita の記事は
        その時点でまだ LGTM が付いていない（実測: 直近 24 時間の記事は最大 6 LGTM）。
        収集時の値で切ると候補が 1 件も残らないため、ここでは母数だけを絞り、
        注目度の判定は 24 時間の熟成後に取り直した値で行う（`pipeline.select`）。
        Hacker News は投稿直後から points が伸びるので、あちらは収集時に切っている。

        `created:` は日付単位なので、`window_hours` を跨いだ古い記事も返ってくる。
        時刻での足切りは手元で行う。
        """
        since = datetime.now(UTC) - timedelta(hours=window_hours)
        # created は日付単位。境界の記事を取りこぼさないよう 1 日広く取り、時刻で絞る
        since_date = (since - timedelta(days=1)).strftime("%Y-%m-%d")
        query = f"created:>={since_date} stocks:>{SEARCH_MIN_STOCKS}"

        # **ページ間の重複を除く。** ページを追っている間に新着が入るとオフセットが
        # ずれ、同じ記事が 2 ページに現れる。dict にしておけば limit の枠も食わない
        found: dict[str, Story] = {}
        for page in range(1, max_pages + 1):
            items = self._get("/items", {"page": page, "per_page": PER_PAGE, "query": query})
            if not items:
                break
            for item in items:
                story = _story_from_item(item)
                if story is None or story.created_at < since:
                    continue
                found.setdefault(story.ref.id, story)
            if len(items) < PER_PAGE:
                break
        out = sorted(found.values(), key=lambda s: -s.engagement.score)
        return out[:limit]

    # --- ReactionSource ---------------------------------------------------

    def fetch_reactions(self, ref: SourceRef) -> tuple[Story | None, list[Reaction]]:
        """記事の現在値とコメントを返す。

        **コメントは 0 件が普通**（実測で 82%）。呼び出し側は 0 件でも記事化に進み、
        議論の論調を持たない記事になる。
        """
        # 別のソースで拾った候補が回ってくることがある（設定を変えた後など）。
        # ID の形が違うので取り違えはまず起きないが、無駄なリクエストを避ける
        if ref.source != self.name:
            return None, []
        item = self._get_one(f"/items/{ref.id}")
        if item is None:
            return None, []
        story = _story_from_item(item)
        if story is None:
            return None, []
        # **コメントが 0 件なら問い合わせない。** 実測で 82% がこれに当たる。
        # 非認証は 60 req/h しかないので、1 候補あたり 2 リクエストを 1 に減らす
        if story.engagement.comments == 0:
            return story, []
        comments = self._get(f"/items/{ref.id}/comments")
        if comments is None:
            # **「取れなかった」を「0 件だった」と混同しない。**
            # 記事本体は取れてもコメントの取得だけ失敗することがある（この 2 つの
            # リクエストの間にレートが尽きる、5xx が続く）。ここで `[]` を返すと、
            # 議論のある記事が「反応なし」の記事として確定的に書き出され、
            # 候補は drafted になって**二度と作り直されない**。
            # `(None, [])` は「今回は判定できなかった」の意味で、呼び出し側は
            # 候補を pending のまま次回に回す（`cli.cmd_compose`）。
            print(f"  [warn] Qiita のコメントを取得できませんでした（{ref.id}）。次回に回します")
            return None, []
        return story, [r for r in map(_reaction_from_comment, comments) if r is not None]


def _ref(item_id: str) -> SourceRef:
    return SourceRef(source=NAME, id=str(item_id))


# --- Adapter: Qiita API の返す形を models の型に変える ----------------------
# API の項目名（likes_count / stocks_count / rendered_body）を知っているのはここだけ。


def _story_from_item(item: dict) -> Story | None:
    """記事 1 件を Story にする。非公開記事と、必須項目を欠くものは捨てる。"""
    if item.get("private"):
        return None
    url = item.get("url")
    item_id = item.get("id")
    title = (item.get("title") or "").strip()
    created = _parse_dt(item.get("created_at"))
    # タイトルが無いと記事の見出しも slug も作れない。拾っても使えないので捨てる
    if not url or not item_id or not title or created is None:
        return None
    user = item.get("user") or {}
    return Story(
        ref=_ref(str(item_id)),
        url=url,
        title=title,
        engagement=Engagement(
            # 注目度は LGTM。ストック数は検索で絞るためだけに使い、表示には出さない
            score=int(item.get("likes_count") or 0),
            comments=int(item.get("comments_count") or 0),
        ),
        created_at=created,
        # **記事ページ自身が議論の場所。** Hacker News と違いスレッドは別に無い
        discussion_url=url,
        # 記事 URL に含まれるので、伏せないと LLM と公開記事にハンドルが残る
        author=user.get("id") or None,
    )


def _reaction_from_comment(comment: dict) -> Reaction | None:
    """コメント 1 件を Reaction にする。

    **Qiita のコメントはフラット**で、返信の親子関係を API が返さない。
    `depth` と `reply_count` は 0 で埋める（`anonymize` はこの 2 つで重み付けするが、
    全件同じ値なら元の並び順が保たれるだけで害はない）。

    本文は `rendered_body`（HTML）を使う。`anonymize.strip_html` が HTML を前提に
    しているので、Markdown の `body` を渡すと記法がそのまま残る。
    """
    comment_id = comment.get("id")
    text = comment.get("rendered_body") or ""
    if not comment_id or not text.strip():
        return None
    user = comment.get("user") or {}
    return Reaction(
        comment_id=str(comment_id),
        author=user.get("id") or None,
        text=text,
        depth=0,
        reply_count=0,
    )


def _as_int(raw: str | None) -> int | None:
    """ヘッダの値を整数にする。読めなければ None。"""
    if raw is None:
        return None
    try:
        return int(raw.strip())
    except ValueError:
        return None


def _reset_at(reset: int | None) -> str:
    """レートが回復する時刻の案内。分からなければ空文字。"""
    if reset is None:
        return ""
    try:
        when = datetime.fromtimestamp(reset, tz=UTC).astimezone(JST)
    except (OverflowError, OSError, ValueError):
        return ""
    return f"回復は {when:%H:%M}（JST）以降です。"


def _parse_dt(raw: object) -> datetime | None:
    """ISO 8601 の日時を UTC の datetime にする。Qiita は `+09:00` 付きで返す。"""
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return datetime.fromisoformat(raw).astimezone(UTC)
    except ValueError:
        return None

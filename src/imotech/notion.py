"""Notion API クライアント。

レビュー面としての Notion を扱う。**記事本文の正は Notion ではない** —
本文は compose が書いた Markdown が正で、Notion からは人が書いた imo だけを
取り出す。こうすると Notion のブロックから記事を再構成せずに済み、
「正となるデータは Git」という決定（docs/DESIGN.md Q2）も保てる。

公式 Python SDK は使わず httpx で直接叩く。REST が単純で、依存を増やす利点がない。
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from .models import ApprovedPage, ArticleDraft

# 記事本文と同じ但し書きを使う。**文言は 1 か所に閉じる** — レビュー面と公開記事で
# 違うことが書いてあると、どちらが正か分からなくなる。
# `llm.py` が `render` から imo のプレースホルダを取っているのと同じ向きの依存
from .render import USE_CASE_NOTE, usable_glossary, usable_use_cases

API = "https://api.notion.com/v1"

# 現行の最新版。古い版でも動くが、data_source を使う新しいデータモデルが使えない。
# 出典: https://developers.notion.com/reference/versioning
NOTION_VERSION = "2026-03-11"

# 1 リクエストのペイロード上限（1,000 ブロック / 500 KB）と、配列の 100 要素上限。
# 出典: https://developers.notion.com/reference/request-limits
MAX_CHILDREN_PER_REQUEST = 100
MAX_RICH_TEXT_CHARS = 2000

# Status プロパティの値。Select 型（Status 型ではない）。
# Status 型はオプションを API から作れず、環境の再現性が落ちるため
STATUS_DRAFT = "Draft"
STATUS_APPROVED = "Approved"
STATUS_PUBLISHED = "Published"
STATUS_REJECTED = "Rejected"

# プロパティ名。docs/DESIGN.md 3.1 と一致していなければならない
PROP_TITLE = "Title"
PROP_STATUS = "Status"
PROP_IMO = "imo"
PROP_URL_HASH = "URL Hash"
PROP_SLUG = "Slug"
PROP_SOURCE_URL = "Source URL"
PROP_HN_URL = "HN URL"
PROP_HATENA_URL = "Hatena URL"
PROP_HN_SCORE = "HN Score"
PROP_HN_COMMENTS = "HN Comments"
PROP_TAGS = "Tags"
PROP_COLLECTED_AT = "Collected At"
PROP_PUBLISHED_AT = "Published At"
PROP_MODEL = "Model"


class NotionError(RuntimeError):
    """Notion API の呼び出しに失敗した。"""


class NotionBlockLimitError(NotionError):
    """ワークスペースのブロック上限に達した。

    Free プランでメンバーが 2 人以上のワークスペースは生涯 1,000 ブロックが上限で、
    API も 403 restricted_resource を返す。1 人ワークスペースなら無制限。
    出典: https://developers.notion.com/reference/workspace-block-limits
    """


# --- rich_text の組み立て -------------------------------------------------


def _rich_text(content: str) -> list[dict]:
    """rich_text 配列にする。2,000 文字の上限で切る。"""
    return [{"type": "text", "text": {"content": content[:MAX_RICH_TEXT_CHARS]}}]


def _split_long(text: str) -> list[str]:
    """2,000 文字を超える文章を、段落として分けられる長さに切る。

    切るだけだと文が途中で切れるので、なるべく句点の後ろで切る。
    """
    if len(text) <= MAX_RICH_TEXT_CHARS:
        return [text]
    out: list[str] = []
    rest = text
    while len(rest) > MAX_RICH_TEXT_CHARS:
        window = rest[:MAX_RICH_TEXT_CHARS]
        cut = max(window.rfind("。"), window.rfind("\n"))
        cut = cut + 1 if cut > MAX_RICH_TEXT_CHARS // 2 else MAX_RICH_TEXT_CHARS
        out.append(rest[:cut])
        rest = rest[cut:]
    if rest:
        out.append(rest)
    return out


# --- ブロックの組み立て ---------------------------------------------------


def _paragraph(text: str) -> dict:
    return {"type": "paragraph", "paragraph": {"rich_text": _rich_text(text)}}


def _heading(level: int, text: str) -> dict:
    key = f"heading_{level}"
    return {"type": key, key: {"rich_text": _rich_text(text)}}


def _bullet(text: str) -> dict:
    return {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": _rich_text(text)}}


def _bullets(text: str) -> list[dict]:
    """2,000 文字を超える要旨は複数の項目に分ける。黙って切り捨てない。"""
    return [_bullet(chunk) for chunk in _split_long(text)]


def build_blocks(draft: ArticleDraft) -> list[dict]:
    """記事本文のブロックを組み立てる（docs/DESIGN.md 3.3）。

    imo の欄はここに作らない。imo は Notion のプロパティ側に置き、
    空かどうかをクエリで判定できるようにしている。
    """
    blocks: list[dict] = [
        {
            "type": "callout",
            "callout": {
                "rich_text": _rich_text(
                    "公開するには、右の imo プロパティに一言書いてから "
                    "Status を Approved にしてください。"
                    "imo が空のままでは公開されません。"
                ),
                "icon": {"emoji": "⚠️"},
            },
        },
        _heading(2, "元記事の要旨"),
    ]
    for line in draft.digest:
        blocks += _bullets(line)
    # 反応が無いソースの記事では論調が空になる。空の見出しを作らない
    if draft.discourse:
        blocks.append(_heading(2, "議論の論調"))
        for point in draft.discourse:
            blocks.append(_heading(3, point.point))
            blocks += [_paragraph(chunk) for chunk in _split_long(point.detail)]
    # 記事と同じ並び（論調 → 使いどころ → 用語）。imo は本文ではなくプロパティ側にある。
    # **但し書きを必ず添える。** ここは人が公開の可否を決める面なので、
    # 「元記事に書いてあること」と「生成 AI が考えた応用案」が混ざって見えてはいけない
    # **公開記事と同じフィルタを通す。** 片方だけ空項目を出すと、
    # 「レビュー面には節があるのに公開記事には無い」が起きる
    cases = usable_use_cases(draft.use_cases)
    if cases:
        blocks.append(_heading(2, "使いどころ"))
        # 但し書きは**項目より先**に置く。後ろだと、読んだあとに「推測でした」と
        # 知ることになり、レビューの判断が一度汚れる
        blocks.append(_paragraph(USE_CASE_NOTE))
        for case in cases:
            blocks += _bullets(f"{case.scene}: {case.detail}")
    entries = usable_glossary(draft.glossary)
    if entries:
        blocks.append(_heading(2, "用語"))
        for entry in entries:
            blocks += _bullets(f"{entry.term}: {entry.description}")
    blocks += [
        {"type": "divider", "divider": {}},
        _heading(2, "出典"),
        _bullet(f"元記事: {draft.source_url}"),
        _bullet(f"議論: {draft.discussion_url}"),
        _bullet(f"はてなブックマーク: {draft.hatena_url}"),
        _paragraph(
            f"生成モデル: {draft.model} / "
            f"生成日時: {(draft.generated_at or datetime.now(UTC)).isoformat(timespec='seconds')}"
        ),
    ]
    return blocks


def build_properties(draft: ArticleDraft, *, collected_at: datetime | None = None) -> dict:
    """ページのプロパティ。imo は**入れない**（人が書く欄なので空で作る）。"""
    generated = draft.generated_at or datetime.now(UTC)
    return {
        PROP_TITLE: {"title": _rich_text(draft.title)},
        PROP_STATUS: {"select": {"name": STATUS_DRAFT}},
        PROP_URL_HASH: {"rich_text": _rich_text(draft.url_hash)},
        PROP_SLUG: {"rich_text": _rich_text(draft.slug)},
        PROP_SOURCE_URL: {"url": draft.source_url},
        PROP_HN_URL: {"url": draft.discussion_url},
        PROP_HATENA_URL: {"url": draft.hatena_url},
        PROP_HN_SCORE: {"number": draft.engagement.score},
        PROP_HN_COMMENTS: {"number": draft.engagement.comments},
        PROP_TAGS: {"multi_select": [{"name": t} for t in draft.tags]},
        PROP_COLLECTED_AT: {
            "date": {"start": (collected_at or generated).isoformat(timespec="seconds")}
        },
        PROP_MODEL: {"rich_text": _rich_text(draft.model)},
    }


@dataclass
class NotionClient:
    """Notion REST API の薄いラッパ。

    スロットリングとリトライをここに閉じる。呼び出し側が毎回気にせずに済む。
    """

    token: str
    min_interval: float = 0.35
    max_attempts: int = 3
    timeout: float = 30.0
    transport: httpx.BaseTransport | None = None
    sleeper: object = time.sleep

    def __post_init__(self) -> None:
        self._client = httpx.Client(
            base_url=API,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
            transport=self.transport,
        )
        self._last_call = 0.0
        # 直前のクエリが 10,000 件の上限で打ち切られたか。呼び出し側が見る
        self.last_query_incomplete = False

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> NotionClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # --- HTTP -------------------------------------------------------------

    def _throttle(self) -> None:
        """Free / Plus は 180 req/min（平均 3 req/sec）。間隔を空けて超えないようにする。"""
        if self.min_interval <= 0:
            return
        wait = self.min_interval - (time.monotonic() - self._last_call)
        if wait > 0:
            self.sleeper(wait)
        self._last_call = time.monotonic()

    def request(self, method: str, path: str, **kw) -> dict:
        last: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            self._throttle()
            try:
                r = self._client.request(method, path, **kw)
            except httpx.HTTPError as e:
                last = NotionError(f"{method} {path} に到達できない: {type(e).__name__}")
                if attempt < self.max_attempts:
                    self.sleeper(float(2 ** (attempt - 1)))
                continue

            if r.status_code < 400:
                return r.json()

            body = _safe_json(r)
            code = body.get("code", "")

            # 403 はリトライしても回復しない。ただし原因は 1 つではない。
            # restricted_resource はインテグレーション未接続などの権限一般でも返る
            # 汎用コードなので、ブロック上限と決めつけると最もありがちな設定ミスに
            # 誤った案内（「2 人目のメンバーがいないか」）を出してしまう。
            # message に手がかりがあるときだけブロック上限として扱う。
            if r.status_code == 403:
                message = body.get("message", "")
                if _looks_like_block_limit(body):
                    raise NotionBlockLimitError(
                        "Notion がワークスペースのブロック上限を理由に 403 を返しました。"
                        "Free プランはメンバーが 2 人以上だと生涯 1,000 ブロックが上限です"
                        "（1 人なら無制限）。2 人目のメンバーがいないか確認してください。"
                        f" message={message}"
                    )
                raise NotionError(
                    f"{method} {path} が HTTP 403 ({code}) で拒否されました。"
                    "インテグレーションがこのデータベースに接続されているか"
                    "（Notion のページの ... → 接続）、トークンが正しいかを確認してください。"
                    f" message={message}"
                )

            retryable = r.status_code == 429 or r.status_code >= 500
            last = NotionError(
                f"{method} {path} が HTTP {r.status_code} ({code}): {body.get('message', '')}"
            )
            if not retryable or attempt >= self.max_attempts:
                raise last

            self.sleeper(_retry_after(r, body, attempt))
        raise last or NotionError(f"{method} {path} が失敗した")

    # --- データソース -----------------------------------------------------

    def data_source_id(self, database_id: str) -> str:
        """データベースから data_source の id を取る。

        2025-09-03 版でデータモデルが変わり、行とプロパティは database ではなく
        data source が持つようになった。クエリもページ作成もこの id を使う。
        出典: https://developers.notion.com/guides/get-started/upgrade-guide-2025-09-03
        """
        data = self.request("GET", f"/databases/{database_id}")
        sources = data.get("data_sources") or []
        if not sources:
            raise NotionError(
                f"データベース {database_id} に data_source がありません。"
                "インテグレーションがこのデータベースに接続されているか確認してください。"
            )
        return sources[0]["id"]

    def query(self, data_source_id: str, body: dict) -> list[dict]:
        """データソースを引く。ページネーションを辿って全件返す。

        POST /v1/databases/{id}/query は 2025-09-03 版で非推奨。
        出典: https://developers.notion.com/reference/query-a-data-source
        """
        out: list[dict] = []
        cursor: str | None = None
        self.last_query_incomplete = False
        while True:
            payload = dict(body)
            if cursor:
                payload["start_cursor"] = cursor
            data = self.request("POST", f"/data_sources/{data_source_id}/query", json=payload)
            out.extend(data.get("results") or [])
            if not data.get("has_more"):
                status = (data.get("request_status") or {}).get("type")
                if status == "incomplete":
                    # ライブラリ層は print しない。呼び出し側が判断できるよう記録する
                    self.last_query_incomplete = True
                return out
            cursor = data.get("next_cursor")
            if not cursor:
                return out

    # --- 投入 -------------------------------------------------------------

    def find_page_by_url_hash(self, data_source_id: str, url_hash: str) -> str | None:
        """URL Hash で既存ページを探す。冪等性の 2 段目（docs/DESIGN.md 2.2）。

        先頭 1 件で足りるので query のページネーションは通さない。重複ページが
        n 件あるとき 1 件ずつ n 回クエリすることになり、350ms × n の待ちが増える。
        """
        data = self.request(
            "POST",
            f"/data_sources/{data_source_id}/query",
            json={
                "filter": {"property": PROP_URL_HASH, "rich_text": {"equals": url_hash}},
                "page_size": 1,
            },
        )
        results = data.get("results") or []
        return results[0].get("id") if results else None

    def create_draft(
        self, data_source_id: str, draft: ArticleDraft, *, collected_at: datetime | None = None
    ) -> str:
        """下書きページを作る。既にあれば作らずその id を返す。"""
        existing = self.find_page_by_url_hash(data_source_id, draft.url_hash)
        if existing:
            return existing

        blocks = build_blocks(draft)
        page = self.request(
            "POST",
            "/pages",
            json={
                "parent": {"data_source_id": data_source_id},
                "properties": build_properties(draft, collected_at=collected_at),
                # 配列は 100 要素まで。残りは追記する
                "children": blocks[:MAX_CHILDREN_PER_REQUEST],
            },
        )
        page_id = page.get("id")
        if not page_id:
            raise NotionError(f"ページ作成の応答に id がありません: {page}")
        for i in range(MAX_CHILDREN_PER_REQUEST, len(blocks), MAX_CHILDREN_PER_REQUEST):
            self.request(
                "PATCH",
                f"/blocks/{page_id}/children",
                json={"children": blocks[i : i + MAX_CHILDREN_PER_REQUEST]},
            )
        return page_id

    # --- 承認の検知 -------------------------------------------------------

    def fetch_approved(self, data_source_id: str) -> list[ApprovedPage]:
        """Status が Approved かつ imo が空でないページを返す。

        last_edited_time は使わない。ページ単位でしか取れず「Status が変わった瞬間」を
        検知できないため、時刻ではなく状態そのものを引く。処理したら Published に
        変えるので、このクエリは常に「未処理の承認」だけを返す（docs/DESIGN.md 3.2）。

        imo の空チェックをクエリに含めることで、書き忘れたまま Approved にした記事が
        公開されるのを仕組みで防ぐ。
        """
        results = self.query(
            data_source_id,
            {
                "filter": {
                    "and": [
                        {"property": PROP_STATUS, "select": {"equals": STATUS_APPROVED}},
                        {"property": PROP_IMO, "rich_text": {"is_not_empty": True}},
                    ]
                }
            },
        )
        out: list[ApprovedPage] = []
        for page in results:
            props = page.get("properties") or {}
            # Notion の is_not_empty は空白だけの値を通す。strip して弾く
            imo = _plain_text(props.get(PROP_IMO, {}).get("rich_text")).strip()
            url_hash = _plain_text(props.get(PROP_URL_HASH, {}).get("rich_text"))
            slug = _plain_text(props.get(PROP_SLUG, {}).get("rich_text"))
            if not imo or not slug:
                # クエリで弾いたはずだが、念のため。空を通すと公開判定が壊れる
                continue
            out.append(ApprovedPage(page_id=page["id"], url_hash=url_hash, slug=slug, imo=imo))
        return out

    def mark_published(self, page_id: str, *, when: datetime | None = None) -> None:
        """Status を Published にし、Published At を入れる。"""
        ts = (when or datetime.now(UTC)).isoformat(timespec="seconds")
        self.request(
            "PATCH",
            f"/pages/{page_id}",
            json={
                "properties": {
                    PROP_STATUS: {"select": {"name": STATUS_PUBLISHED}},
                    PROP_PUBLISHED_AT: {"date": {"start": ts}},
                }
            },
        )


# ブロック上限の手がかり。Notion の message とエラーの additional_data に現れる。
# 出典: https://developers.notion.com/reference/workspace-block-limits
_BLOCK_LIMIT_HINTS = ("block_limit", "free blocks", "block limit", "upgrade its plan")


def _looks_like_block_limit(body: dict) -> bool:
    """403 の応答がワークスペースのブロック上限によるものか。

    additional_data に block_limit が入る形と、message に文言が出る形の両方を見る。
    どちらも確認できないときはブロック上限と決めつけない。
    """
    extra = body.get("additional_data") or {}
    if isinstance(extra, dict) and "block_limit" in extra:
        return True
    message = (body.get("message") or "").lower()
    return any(h in message for h in _BLOCK_LIMIT_HINTS)


def _safe_json(r: httpx.Response) -> dict:
    try:
        body = r.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


def _retry_after(r: httpx.Response, body: dict, attempt: int) -> float:
    """待つ秒数。Retry-After があれば尊重し、無ければ指数バックオフ。"""
    header = r.headers.get("Retry-After")
    if header:
        try:
            return float(header)
        except ValueError:
            pass
    from_body = (body.get("additional_data") or {}).get("retry_after")
    if from_body:
        try:
            return float(from_body)
        except (TypeError, ValueError):
            pass
    # 完了条件は 1s / 2s / 4s。attempt は 1 始まりなので 1 引く
    return float(2 ** (attempt - 1))


def _plain_text(rich_text: list[dict] | None) -> str:
    """rich_text 配列を素のテキストにする。2,000 文字で分割された分も繋ぐ。"""
    if not rich_text:
        return ""
    return "".join(
        rt.get("plain_text") or rt.get("text", {}).get("content", "") for rt in rich_text
    )


# --- データベースの作成 ---------------------------------------------------

# Select 型のオプション定義。Status 型ではなく Select 型にしているのは、
# Status 型のオプションが API から作れず環境の再現性が落ちるため
# （docs/DESIGN.md 3.1）。
#
# ⚠️ このスキーマの書式は公式ドキュメントの OpenAPI Explorer の折りたたみ内にあり、
# 調査では展開できなかった（未確認）。慣例の形で書いてある。
# notion-setup が失敗したら、応答の message を見て直すこと。
DATABASE_SCHEMA: dict = {
    PROP_TITLE: {"title": {}},
    PROP_STATUS: {
        "select": {
            "options": [
                {"name": STATUS_DRAFT, "color": "default"},
                {"name": STATUS_APPROVED, "color": "green"},
                {"name": STATUS_PUBLISHED, "color": "blue"},
                {"name": STATUS_REJECTED, "color": "red"},
            ]
        }
    },
    PROP_IMO: {"rich_text": {}},
    PROP_URL_HASH: {"rich_text": {}},
    PROP_SLUG: {"rich_text": {}},
    PROP_SOURCE_URL: {"url": {}},
    PROP_HN_URL: {"url": {}},
    PROP_HATENA_URL: {"url": {}},
    PROP_HN_SCORE: {"number": {}},
    PROP_HN_COMMENTS: {"number": {}},
    PROP_TAGS: {"multi_select": {}},
    PROP_COLLECTED_AT: {"date": {}},
    PROP_PUBLISHED_AT: {"date": {}},
    PROP_MODEL: {"rich_text": {}},
}


def create_database_payload(parent_page_id: str, title: str = "imoTech Drafts") -> dict:
    """POST /v1/databases に送るボディ。

    2025-09-03 版以降、プロパティのスキーマは initial_data_source.properties に
    ネストする。出典: https://developers.notion.com/reference/create-a-database
    """
    return {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": title}}],
        "initial_data_source": {"properties": DATABASE_SCHEMA},
    }


def _expected_type(spec: dict) -> str:
    """DATABASE_SCHEMA の 1 エントリから期待する type を取る。"""
    return next(iter(spec))


def schema_diff(existing: dict) -> tuple[dict, dict, dict]:
    """既存のプロパティと設計書のスキーマを比べる。

    返り値は (追加が必要なもの, タイトルの改名指示, 型が違うもの)。

    **型まで見る。** 名前だけを比べると、Notion の UI で作った DB の `Status` が
    Status 型（UI の既定）でも「揃っています」と判断してしまい、そのあと
    `build_properties` が送る `{"select": ...}` が毎回 400 になる。
    型の違いは API では直せないので、呼び出し側が「UI で作り直す必要がある」と
    案内できるように分けて返す。

    Notion のデータベースはタイトル型のプロパティを 1 つだけ持てる。既存 DB の
    タイトル列が別名（Notion が作る既定は「名前」）なら、Title を足すのではなく
    改名する必要がある。
    """
    missing = {k: v for k, v in DATABASE_SCHEMA.items() if k not in existing}

    mismatched: dict = {}
    for name, spec in DATABASE_SCHEMA.items():
        current = existing.get(name)
        if current is None:
            continue
        want = _expected_type(spec)
        got = current.get("type")
        if got != want:
            mismatched[name] = {"expected": want, "actual": got}

    rename: dict = {}
    if PROP_TITLE in missing:
        current_title = next(
            (name for name, spec in existing.items() if spec.get("type") == "title"), None
        )
        if current_title:
            # タイトル型は 1 つだけなので、追加ではなく改名する
            missing.pop(PROP_TITLE)
            rename = {current_title: {"name": PROP_TITLE}}
    return missing, rename, mismatched


def patch_properties_payload(existing: dict) -> dict:
    """既存のデータソースに足りないプロパティを追加するボディ。

    PATCH /v1/data_sources/{id} に送る。既存のプロパティは触らない。
    """
    missing, rename, _ = schema_diff(existing)
    props: dict = dict(rename)
    props.update(missing)
    return {"properties": props}

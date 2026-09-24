"""企業の公式ブログ（RSS / Atom）からの収集。

Hacker News や Qiita との違い:

| | Hacker News / Qiita | 公式ブログ |
|---|---|---|
| 注目度 | points / LGTM | **無い**（フィードに載らない） |
| 反応 | コメント | **無い** |
| 選び方 | 閾値を満たす上位 | **新着を 1 日 1 本まで枠で確保**（`reserved_per_run`） |

注目度が無いので、閾値の判定には乗せられない（0 と比べても意味が無い）。代わりに
**そのブログ自身が「この発信元の新着は読む価値がある」ことの保証**とみなし、1 日の
記事の枠のうち 1 本をブログに割り当てる。

使ってよいかは発信元ごとに確かめてある（docs/DESIGN.md 4.1d の表）。**robots.txt が AI への入力を
明示的に許しているブログだけ**を載せる（`Content-Signal: ai-input=yes`）。
"""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime

import httpx

from ..models import Engagement, Reaction, SourceRef, Story, Thresholds

_ATOM = "{http://www.w3.org/2005/Atom}"

#: フィード 1 本の上限。Vercel の Atom は 1,600 件を超える（2026-09-24 実測）ので、
#: 大きめに取る。読みながら数え、超えたら打ち切る（壊れた・巨大な応答で止まらないように）
MAX_FEED_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class BlogSpec:
    """ブログ 1 つの定義。"""

    name: str
    """ソースの名前（`registry` のキー、記事の `source`）"""
    feed_url: str
    path_prefix: str = ""
    """この接頭辞で始まる記事だけを使う（空なら全部）。Vercel の Atom は changelog を
    含み、数行の告知ばかりで記事にならないので `/blog/` に絞る"""


CLOUDFLARE = BlogSpec(name="cloudflare-blog", feed_url="https://blog.cloudflare.com/rss/")
VERCEL = BlogSpec(name="vercel-blog", feed_url="https://vercel.com/atom", path_prefix="/blog/")


class BlogFeed:
    """StoryFeed と ReactionSource を満たす。反応は常に 0 件。"""

    #: 注目度が無いので閾値は 0。**選ぶのは枠**（`reserved_per_run`）
    default_thresholds = Thresholds(min_score=0, min_comments=0)
    #: 1 回の実行で、注目度に関係なく記事にする本数の上限
    reserved_per_run = 1

    def __init__(
        self,
        spec: BlogSpec,
        *,
        timeout: float = 15.0,
        user_agent: str = "imoTechBot/1.0",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.spec = spec
        self.name = spec.name
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": user_agent},
            follow_redirects=True,
            transport=transport,
        )
        #: 1 回の実行のあいだ、フィードは 1 度だけ取る（候補ごとに取り直さない）
        self._cache: dict[str, Story] | None = None

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> BlogFeed:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _entries(self) -> dict[str, Story]:
        """フィードの記事。取れなければ例外（収集では MultiFeed が握る）。"""
        if self._cache is None:
            with self._client.stream("GET", self.spec.feed_url) as r:
                r.raise_for_status()
                buf = bytearray()
                for chunk in r.iter_bytes():
                    buf.extend(chunk)
                    if len(buf) > MAX_FEED_BYTES:
                        raise ValueError(
                            f"{self.name}: フィードが {MAX_FEED_BYTES} バイトを超えます"
                        )
            stories = [s for s in _parse(bytes(buf), self.spec) if s is not None]
            self._cache = {s.ref.id: s for s in stories}
        return self._cache

    def fetch_stories(
        self,
        *,
        window_hours: int = 24,
        min_points: int = 10,  # noqa: ARG002 — 注目度が無いので使わない
        limit: int = 50,
    ) -> list[Story]:
        since = datetime.now(UTC) - timedelta(hours=window_hours)
        out = [s for s in self._entries().values() if s.created_at >= since]
        out.sort(key=lambda s: s.created_at, reverse=True)
        return out[:limit]

    def fetch_reactions(self, ref: SourceRef) -> tuple[Story | None, list[Reaction]]:
        """現在の Story と、空の反応。

        **反応は無いが、「評価できた」ことにする必要がある**。問い合わせで Story が
        返らない候補は選別で選べない（`pipeline.select` の evaluated）。フィードから
        落ちた古い記事は None になり、期限切れで打ち切られる。
        """
        if ref.source != self.name:
            return None, []
        try:
            entries = self._entries()
        except (httpx.HTTPError, ET.ParseError, ValueError) as e:
            # **compose を止めない。** 問い合わせのループは例外を握らないので、ここで
            # 投げると HN も含めてその日の記事が 0 本になる。取れなかった候補は評価できず、
            # 次回に回る。同じ実行の中では取り直さない
            # 403（拒否）か 503（一時的な障害）かサイズ超過かを当番が見分けられるよう、中身も出す
            print(
                f"  [warn] {self.name} のフィード（{self.spec.feed_url}）を取得できません: "
                f"{type(e).__name__}: {str(e)[:120]}",
                flush=True,
            )
            self._cache = {}
            return None, []
        story = entries.get(ref.id)
        return (story, []) if story is not None else (None, [])


def _ref(spec: BlogSpec, key: str) -> SourceRef:
    # 記事の ID は URL から作る。フィードの guid / id はブログによって形が違う
    return SourceRef(source=spec.name, id=hashlib.sha256(key.encode()).hexdigest()[:16])


def _parse(content: bytes, spec: BlogSpec) -> list[Story | None]:
    """RSS 2.0 か Atom を読む。どちらかは要素で見分ける。

    **標準ライブラリの ElementTree で読む。** 相手は発信元が固定の公式ブログで、
    形は RSS 2.0 と Atom の 2 つだけ。feedparser を足すほどの形の揺れが無い。
    """
    root = ET.fromstring(content)
    if root.tag == f"{_ATOM}feed":
        return [_from_atom(e, spec) for e in root.findall(f"{_ATOM}entry")]
    return [_from_rss(i, spec) for i in root.findall("./channel/item")]


def _story(spec: BlogSpec, url: str, title: str, created: datetime | None) -> Story | None:
    if not url or not title or created is None:
        return None
    if spec.path_prefix and not httpx.URL(url).path.startswith(spec.path_prefix):
        return None
    return Story(
        ref=_ref(spec, url),
        url=url,
        title=title.strip(),
        engagement=Engagement(score=0, comments=0),
        created_at=created,
        discussion_url=url,
        # 著者は載せない。フィードに個人名は入るが、記事の出典はブログそのもの
        author=None,
    )


def _from_rss(item: ET.Element, spec: BlogSpec) -> Story | None:
    created = None
    raw = item.findtext("pubDate")
    if raw:
        try:
            parsed = parsedate_to_datetime(raw)
            # "-0000" は naive になる。ローカル時刻として解釈させない
            created = (parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)).astimezone(UTC)
        except (TypeError, ValueError):
            created = None
    return _story(
        spec, (item.findtext("link") or "").strip(), item.findtext("title") or "", created
    )


def _from_atom(entry: ET.Element, spec: BlogSpec) -> Story | None:
    link = entry.find(f"{_ATOM}link")
    url = (link.get("href") if link is not None else "") or ""
    # Vercel の Atom は published を持たず updated だけ（2026-09-24 実測）
    raw = entry.findtext(f"{_ATOM}published") or entry.findtext(f"{_ATOM}updated")
    created = None
    if raw:
        try:
            created = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            created = None
    return _story(spec, url.strip(), entry.findtext(f"{_ATOM}title") or "", created)

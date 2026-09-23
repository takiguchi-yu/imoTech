"""元記事の本文取得。

取得した本文は Gemini への入力にのみ使い、記事には転載しない（docs/DESIGN.md 5.4）。

本文も PII の経路である。元記事に著者の連絡先や引用が含まれることは普通にあり、
Gemini の無料枠は入力が学習に使われ人間のレビュアーが読む。よって
ArticleSource.text は **必ず scrub を通した状態** で作る。
"""

from __future__ import annotations

import html
import ipaddress
import re
import socket
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx
import trafilatura

from .anonymize import scrub
from .models import ArticleSource

_OG_DESCRIPTION = re.compile(
    r"""<meta\s[^>]*?(?:property|name)\s*=\s*["']og:description["'][^>]*?>""",
    re.IGNORECASE | re.DOTALL,
)
_CONTENT_ATTR = re.compile(r"""content\s*=\s*["'](.*?)["']""", re.IGNORECASE | re.DOTALL)

# robots.txt が肥大化しているサイトがある。読み込み量に天井を置く。
_MAX_ROBOTS_BYTES = 512 * 1024


def _host_is_public(url: str) -> bool:
    """名前解決した IP がすべてグローバルなら True。

    HN に投稿される URL は第三者が自由に決められる。リンクローカル
    （169.254.169.254 のメタデータサービス）や社内ネットワークへ誘導され、
    その内容が Gemini に送られて記事になる経路を塞ぐ。

    DNS rebinding までは防げない（解決と接続の間に応答が変わりうる）。
    ここでは、投稿された URL がそのまま内部を指しているケースを弾くのが目的。
    """
    host = urlsplit(url).hostname
    if not host:
        return False
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            return False
        if not ip.is_global:
            return False
    return bool(infos)


class ArticleFetcher:
    """robots.txt を尊重して元記事を取得する。

    robots.txt の判定は標準ライブラリの urllib.robotparser を使う（自作しない）。
    リダイレクトは httpx に任せず 1 ホップずつ追う。任せてしまうと、最終到達先の
    robots.txt を確認できず、内部ネットワークへの誘導も検査できない。
    """

    def __init__(
        self,
        *,
        user_agent: str,
        timeout: float = 10.0,
        max_bytes: int = 5 * 1024 * 1024,
        max_chars: int = 8000,
        max_redirects: int = 5,
        profile_url_re: re.Pattern[str] | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        # 投稿者のプロフィール URL は本文にも現れる。形はソースごとに違うので
        # 呼び出し側から受け取る（`sources.profile_url_pattern` が取り出す）
        self.profile_url_re = profile_url_re
        self.user_agent = user_agent
        self.max_bytes = max_bytes
        self.max_chars = max_chars
        self.max_redirects = max_redirects
        self._robots: dict[str, RobotFileParser | None] = {}
        # transport はテストからネットワークを差し替えるための口
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": user_agent},
            follow_redirects=False,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ArticleFetcher:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # --- robots.txt -------------------------------------------------------

    def can_fetch(self, url: str) -> bool:
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            return False
        origin = f"{parts.scheme}://{parts.netloc}"

        if origin not in self._robots:
            self._robots[origin] = self._load_robots(origin)
        rp = self._robots[origin]
        if rp is None:
            # robots.txt が無い・読めない → 許可（RFC 9309 の既定に沿う）
            return True
        return rp.can_fetch(self.user_agent, url)

    def _load_robots(self, origin: str) -> RobotFileParser | None:
        try:
            r = self._client.get(f"{origin}/robots.txt", follow_redirects=True)
        except httpx.HTTPError:
            return None
        if r.status_code >= 500:
            # サーバー側の障害。安全側に倒して不許可にする
            rp = RobotFileParser()
            rp.disallow_all = True
            return rp
        if r.status_code >= 400:
            return None
        rp = RobotFileParser()
        rp.parse(r.text[:_MAX_ROBOTS_BYTES].splitlines())
        return rp

    # --- 取得 -------------------------------------------------------------

    def fetch(self, url: str) -> ArticleSource | None:
        """本文を返す。取得できなければ None（呼び出し側が skipped にする）。

        返す text は必ず scrub 済み。元記事に含まれるメールアドレスや
        プロフィール URL を Gemini に送らないため。
        """
        fetched = self._get(url)
        if fetched is None:
            return None
        raw, final_url = fetched

        body = trafilatura.extract(
            raw,
            url=final_url,
            # 既定は True。元記事のコメント欄が要旨に混ざるのを防ぐ
            include_comments=False,
            include_tables=True,
            include_images=False,
            favor_precision=True,
            output_format="txt",
        )
        if body and body.strip():
            return self._as_source(body.strip(), "trafilatura")

        og = _og_description(_decode(raw))
        if og:
            return self._as_source(og, "og:description")
        print(f"  [info] 本文も og:description も取れませんでした: {final_url}", flush=True)
        return None

    def _as_source(self, text: str, via: str) -> ArticleSource:
        # 元記事側にも PII は載る。実データでメールアドレスが残っていた。
        cleaned = scrub(text, frozenset(), self.profile_url_re)
        return ArticleSource(text=cleaned[: self.max_chars], via=via)

    def _get(self, url: str) -> tuple[bytes, str] | None:
        """1 ホップずつリダイレクトを追い、各ホップで robots.txt と宛先 IP を検査する。"""
        current = url
        for _hop in range(self.max_redirects + 1):
            if not self.can_fetch(current):
                print(f"  [info] robots.txt により取得不可: {current}", flush=True)
                return None
            if not _host_is_public(current):
                print(f"  [info] 公開ネットワーク外を指すため中止: {current}", flush=True)
                return None
            try:
                with self._client.stream("GET", current) as r:
                    if r.is_redirect:
                        loc = r.headers.get("location")
                        if not loc:
                            print(f"  [info] Location の無いリダイレクト: {current}", flush=True)
                            return None
                        current = urljoin(current, loc)
                        continue
                    if r.status_code >= 400:
                        print(f"  [info] HTTP {r.status_code}: {current}", flush=True)
                        return None
                    ctype = r.headers.get("content-type", "")
                    if "html" not in ctype.lower():
                        print(f"  [info] HTML ではない ({ctype or '不明'}): {current}", flush=True)
                        return None
                    chunks: list[bytes] = []
                    total = 0
                    for chunk in r.iter_bytes():
                        total += len(chunk)
                        if total > self.max_bytes:
                            print(
                                f"  [info] {self.max_bytes} バイトを超えたため中断: {current}",
                                flush=True,
                            )
                            return None
                        chunks.append(chunk)
                    return b"".join(chunks), current
            except httpx.HTTPError as e:
                print(f"  [info] 取得に失敗: {current} ({type(e).__name__})", flush=True)
                return None
        print(f"  [info] リダイレクトが {self.max_redirects} 回を超えました: {url}", flush=True)
        return None


def _decode(raw: bytes) -> str:
    """OGP を読むためだけの復号。

    本文抽出は bytes のまま trafilatura に渡して自前で文字コードを判定させる。
    ここは meta タグを正規表現で拾うだけなので、化けても致命的ではない。
    """
    m = re.search(rb"""charset\s*=\s*["']?([A-Za-z0-9_.:-]+)""", raw[:4096], re.IGNORECASE)
    if m:
        try:
            return raw.decode(m.group(1).decode("ascii", "ignore"), errors="replace")
        except LookupError:
            # Content-Type に utf8mb4 のような未知の charset が入っていることがある
            pass
    return raw.decode("utf-8", errors="replace")


def _og_description(html_text: str) -> str | None:
    m = _OG_DESCRIPTION.search(html_text)
    if not m:
        return None
    c = _CONTENT_ATTR.search(m.group(0))
    if not c:
        return None
    return html.unescape(c.group(1)).strip() or None

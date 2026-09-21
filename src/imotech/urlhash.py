"""URL の正規化とハッシュ。

同じ記事が別表記で HN に複数回投稿されても 1 回しか書かないための冪等性キーを作る。
重複排除は 3 段構えの 1 段目にあたる（docs/DESIGN.md 2.2）。
"""

from __future__ import annotations

import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# 同じ記事に別の URL を与えてしまうパラメータ。除去してからハッシュを取る。
TRACKING_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "utm_id",
        "ref",
        "ref_src",
        "refsrc",
        "source",
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
        "igshid",
        "__twitter_impression",
        "spm",
        "at_medium",
        "at_campaign",
    }
)


def normalize(url: str) -> str:
    """比較用に URL を正規化する。表示には使わない（原文は Candidate.url に残す）。"""
    parts = urlsplit(url.strip())

    # scheme: http/https の差を吸収する。他のスキームはそのまま残す。
    scheme = "https" if parts.scheme in ("http", "https", "") else parts.scheme

    host = parts.hostname or ""
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]
    # 既定ポートは落とす
    netloc = host
    try:
        port = parts.port
    except ValueError:
        # 不正なポート表記（"https://e.com:8o/a" 等）。外部から投稿された URL なので起こりうる。
        # 1 件のために collect 全体を落とさず、ホスト部をそのまま使って決定的な値にする。
        port = None
        netloc = (parts.netloc or "").lower()
    if port and not ((scheme == "https" and port == 443) or (scheme == "http" and port == 80)):
        netloc = f"{host}:{port}"

    query = urlencode(
        sorted(
            (k, v)
            for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if k.lower() not in TRACKING_PARAMS
        )
    )

    path = parts.path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    # fragment は常に落とす
    return urlunsplit((scheme, netloc, path, query, ""))


def url_hash(url: str) -> str:
    """正規化 URL の SHA-256 先頭 16 桁。候補ストアと Notion の冪等性キー。"""
    return hashlib.sha256(normalize(url).encode("utf-8")).hexdigest()[:16]

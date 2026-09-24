"""記事にする候補を優先する「話題」の判定（docs/DESIGN.md 4.1c）。

話題の語は `topics.toml`（既定）に書く。判定するのは**タイトルと URL のホスト名**だけ —
本文を取りに行く前（候補の段階）に決める必要があるため。
"""

from __future__ import annotations

import re
import tomllib
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

#: 既定の話題の定義
DEFAULT_TOPICS_PATH = Path(__file__).with_name("topics.toml")

_ASCII_WORD = re.compile(r"[\x00-\x7f]+")


@dataclass(frozen=True)
class Topic:
    """話題 1 つ。名前はログに出す。"""

    name: str
    keywords: tuple[str, ...]

    def pattern(self) -> re.Pattern[str]:
        """この話題の語のどれかに当たる正規表現。

        英数字だけの語は**語の境界で**当てる（前が英数字でなく、後ろが英字でない）。"ai" が
        "said" に、"mac" が "machine" に当たらないようにするため。後ろに**数字**が続くのは許す
        （"GPT5" "Qwen3" "C++20"）。`\\b` は "next.js" や "c++" の記号の側で境界を誤るので使わない。
        英数字以外（日本語）を含む語は部分一致。
        """
        parts = []
        for kw in self.keywords:
            k = unicodedata.normalize("NFKC", kw).lower()
            esc = re.escape(k)
            parts.append(rf"(?<![a-z0-9]){esc}(?![a-z])" if _ASCII_WORD.fullmatch(k) else esc)
        return re.compile("|".join(parts))


def load_topics(path: Path = DEFAULT_TOPICS_PATH) -> list[Topic]:
    """`topics.toml` を読む。壊れていたら黙って空にせず落とす（優先が消えたことに気づけない）。"""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    topics = []
    for t in data.get("topic", []):
        name, keywords = t.get("name"), t.get("keywords")
        # 文字列 1 つ（keywords = "ai"）を通すと 1 文字ずつの語になり、ほぼ全件が当たる
        if (
            not name
            or not isinstance(keywords, list)
            or not keywords
            or not all(isinstance(k, str) and k for k in keywords)
        ):
            raise ValueError(f"{path}: 話題には name と空でない keywords が要ります: {t!r}")
        topics.append(Topic(name=name, keywords=tuple(keywords)))
    if not topics:
        # 空のファイルを黙って通すと、話題の優先が消えたことに気づけない
        raise ValueError(f"{path}: [[topic]] が 1 つもありません")
    return topics


def match_topics(title: str, url: str, topics: Sequence[Topic]) -> list[str]:
    """タイトルと URL のホスト名に当たった話題の名前（定義順）。当たらなければ空。"""
    try:
        host = urlparse(url).hostname or ""
    except ValueError:  # "http://[abc/" のような壊れた URL で compose 全体を落とさない
        host = ""
    # 全角英数（「生成ＡＩ」）を半角にそろえる
    text = unicodedata.normalize("NFKC", f"{title} {host}").lower()
    return [t.name for t in topics if t.pattern().search(text)]

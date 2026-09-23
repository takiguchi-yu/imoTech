"""外部サービスへのリンクを組み立てる。

API を呼ばずに URL の規則だけで作れるものだけを置く。`models` に置くと、
値の型が特定のサービスを知ることになり、依存の向きが崩れる。
"""

from __future__ import annotations


def hatena_bookmark_url(url: str) -> str:
    """はてなブックマークのコメントページ。**API は呼ばず URL を組み立てるだけ**。

    収益化を前提にしたため、はてなの API / oEmbed は利用規約上使えない
    （Developer Center 利用規約 第4条1項が「宣伝や商用を目的とした内容」を禁じている）。
    リンクの設置自体は規約上自由で、公式ヘルプが「そのリンクを公開することも自由である」と
    明文化している。
    """
    if url.startswith("https://"):
        return "https://b.hatena.ne.jp/entry/s/" + url[len("https://") :]
    if url.startswith("http://"):
        return "https://b.hatena.ne.jp/entry/" + url[len("http://") :]
    return "https://b.hatena.ne.jp/entry/" + url

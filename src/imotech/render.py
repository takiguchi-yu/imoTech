"""ArticleDraft を公開物の Markdown にする。

このモジュールは Notion の API 形式も HN のレスポンス形式も知らない。
models の型だけを受け取る（docs/DESIGN.md 1.3 の依存の向き）。
"""

from __future__ import annotations

import unicodedata
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from .models import ArticleDraft

JST = timezone(timedelta(hours=9))

# imo がまだ書かれていない印。
#
# この文字列が本文に残っているかぎり、サイト側はその記事を公開しない
# （site/src/lib/articles.ts の publishedArticles）。Notion 運用における
# 「imo プロパティが空なら公開しない」を、ファイルで果たす仕組み。
#
# site/src/content.config.ts の IMO_PLACEHOLDER と一致している必要がある。
# ずれると「imo 未記入の記事が公開される」という取り返しのつかない事故になるため、
# tests/test_render.py で両者を突合している。
IMO_PLACEHOLDER = "<!-- imo:"
# プレースホルダの一部だけを消して保存する事故が起きる（行選択のミスで普通に起きる）。
# そのとき `<!-- imo:` は消えても説明文は残り、運営の内部指示が記事本文として公開される。
# 判定はこの固定句でも行い、どちらかが残っていれば未記入とみなす。
IMO_SENTINEL = "このコメント行を消すまで"
IMO_PROMPT = (
    f"{IMO_PLACEHOLDER} ここに所感を 1 行以上書く。"
    "このコメント行を消すまで、この記事はサイトに公開されません -->"
)


# YAML 1.2 のダブルクォートスカラーが許すのは x09 と x20 以降だけ。
# それ以外の制御文字が生で入ると js-yaml が読めず、**サイトのビルド全体が落ちる**
# （1 ファイルが飛ぶのではなく content の同期段階で死ぬ）。
_YAML_SIMPLE_ESCAPES = {
    "\\": "\\\\",
    '"': '\\"',
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


def _yaml_str(s: str) -> str:
    """YAML のダブルクォート文字列にする。

    タイトルには `:` や `"` が普通に入る。素で書くと YAML が壊れるので、
    常にクォートしてエスケープする。

    加えて制御文字を落とす。LLM の出力に紛れた 1 文字でサイト全体がビルドできなく
    なるため、ここは通す側ではなく落とす側に倒す。改行とタブだけはエスケープして残す。
    """
    out = []
    for ch in s:
        if ch in _YAML_SIMPLE_ESCAPES:
            out.append(_YAML_SIMPLE_ESCAPES[ch])
        elif unicodedata.category(ch) in ("Cc", "Cf", "Cs"):
            # 制御文字・書式文字・サロゲート。
            # エスケープすると YAML が正しく読み戻して元の文字が復活し、
            # そのまま HTML の <title> に入る。意味を持たない文字なので落とす。
            continue
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _yaml_list(items: list[str]) -> str:
    return "[" + ", ".join(_yaml_str(i) for i in items) + "]"


def _iso(dt: datetime, tz: timezone = JST) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(tz).isoformat(timespec="seconds")


def _iso_z(dt: datetime) -> str:
    """UTC を Z 表記で。docs/DESIGN.md 2.5 の表記に揃える。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_markdown(draft: ArticleDraft, *, published_at: datetime | None = None) -> str:
    """下書きを Markdown にする。imo の欄は空のまま残す。

    published_at を渡さなければ生成時刻を使う。imo を書いたときに人が直してよい。
    出典と AI 利用の開示はサイトのテンプレート側がフロントマターから描くので、
    本文には入れない（二重に持つと片方だけ古くなる）。
    """
    generated = draft.generated_at or datetime.now(UTC)
    published = published_at or generated

    fm = [
        "---",
        f"title: {_yaml_str(draft.title)}",
        f"publishedAt: {_iso(published)}",
        f"sourceUrl: {_yaml_str(draft.source_url)}",
        f"sourceTitle: {_yaml_str(draft.source_title)}",
        f"hnUrl: {_yaml_str(draft.hn_url)}",
        f"hatenaUrl: {_yaml_str(draft.hatena_url)}",
        f"hnScore: {draft.hn_score}",
        f"hnComments: {draft.hn_comments}",
        f"tags: {_yaml_list(draft.tags)}",
        f"model: {_yaml_str(draft.model)}",
        f"generatedAt: {_iso_z(generated)}",
        "---",
        "",
    ]

    if not draft.digest or not draft.discourse:
        # 見出しだけの記事を作らない。呼び出し側が skipped にする
        raise ValueError(
            f"要旨 {len(draft.digest)} 件 / 論調 {len(draft.discourse)} 件では記事にならない"
        )

    body = ["## 元記事の要旨", ""]
    body += [f"- {line}" for line in draft.digest]
    body += ["", "## 議論の論調", ""]
    for point in draft.discourse:
        body += [f"### {point.point}", "", point.detail, ""]
    body += ["## imo", "", IMO_PROMPT, ""]

    return "\n".join(fm + body)


def has_imo(markdown: str) -> bool:
    """imo が書かれているか。

    プレースホルダか固定句のどちらかが残っていれば未記入とみなす。
    サイト側（site/src/lib/articles.ts）と同じ判定で、`imotech status` が使う。
    """
    return IMO_PLACEHOLDER not in markdown and IMO_SENTINEL not in markdown


def _source_url_of(path: Path) -> str | None:
    """既存ファイルのフロントマターから sourceUrl を読む。読めなければ None。"""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines()[1:40]:
        if line.startswith("sourceUrl: "):
            return line[len("sourceUrl: ") :].strip().strip('"')
        if line == "---":
            break
    return None


def write_article(draft: ArticleDraft, articles_dir: Path) -> tuple[Path, bool]:
    """Markdown を書き出す。(パス, 新規に書いたか) を返す。

    同じ記事のファイルが既にあれば上書きしない。人が imo を書き込んでいる
    可能性があり、上書きするとその手作業が消える（重複排除の 3 段目も兼ねる）。

    別の記事が同じ slug に当たったときは、捨てずに url_hash を足した名前で書く。
    slugify は日付 + 60 文字までなので、同じ日に似た見出しが出れば衝突する。
    そこで黙って捨てると、生成に使った API 呼び出しごと無駄になり、
    さらにその候補が pending のまま残って毎回作り直される。
    """
    articles_dir.mkdir(parents=True, exist_ok=True)
    path = articles_dir / f"{draft.slug}.md"

    if path.exists():
        existing = _source_url_of(path)
        if existing is None or existing == draft.source_url:
            # 同じ記事（または判別不能）。触らない
            return path, False
        # 別の記事が同じ slug に当たった
        path = articles_dir / f"{draft.slug}-{draft.url_hash[:6]}.md"
        if path.exists():
            return path, False

    path.write_text(to_markdown(draft), encoding="utf-8")
    return path, True

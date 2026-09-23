"""ArticleDraft を公開物の Markdown にする。

このモジュールは Notion の API 形式も HN のレスポンス形式も知らない。
models の型だけを受け取る（docs/DESIGN.md 1.3 の依存の向き）。
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from .models import ArticleDraft, DiscoursePoint, Engagement, GlossaryEntry

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


def _one_line(text: str) -> str:
    """連続する空白（改行を含む）を 1 つの空白に潰す。

    Markdown の 1 行に収める用。改行が残ると `- **語**: 説明` の形が崩れ、
    2 行目以降は from_markdown が読み戻せず黙って消える。
    """
    return _WHITESPACE_RUN_RE.sub(" ", text).strip()


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
        f"source: {_yaml_str(draft.source)}",
        f"discussionUrl: {_yaml_str(draft.discussion_url)}",
        f"hatenaUrl: {_yaml_str(draft.hatena_url)}",
        f"score: {draft.engagement.score}",
        f"comments: {draft.engagement.comments}",
        f"tags: {_yaml_list(draft.tags)}",
        f"model: {_yaml_str(draft.model)}",
        f"generatedAt: {_iso_z(generated)}",
        "---",
        "",
    ]

    if not draft.digest:
        # 見出しだけの記事を作らない。呼び出し側が skipped にする
        raise ValueError(f"要旨 {len(draft.digest)} 件では記事にならない")

    body = ["## 元記事の要旨", ""]
    body += [f"- {line}" for line in draft.digest]
    # **論調が無い記事を許す。** 記事プラットフォーム（Qiita など）の記事には
    # コメントがほぼ付かない（実測で 82% が 0 件）。無い議論を書かせるより、
    # 要旨と imo だけの記事にするほうが正しい。空の節は作らない
    if draft.discourse:
        body += ["", "## 議論の論調", ""]
        for point in draft.discourse:
            body += [f"### {point.point}", "", point.detail, ""]
    else:
        body += [""]
    body += ["## imo", "", IMO_PROMPT, ""]
    # imo の後ろに置く。記事の締めは運営者の所感で、用語は付録として最後に読む。
    # set_imo は次の見出しまでを imo 節として扱うので、ここに足しても壊れない。
    # 用語が無い記事では見出しごと出さない（空の節を作らない）
    # 空の語・説明は行にしない。`- **語**: ` の行は from_markdown が読み戻せず、
    # 往復で件数が合わなくなる（LLM 経由は llm.py が弾くが、直接作る経路もある）
    entries = [e for e in draft.glossary if e.term.strip() and e.description.strip()]
    if entries:
        body += [GLOSSARY_HEADING, ""]
        # 改行が入ると 1 行が割れて形が崩れるので、ここでも潰しておく
        body += [f"- **{_one_line(e.term)}**: {_one_line(e.description)}" for e in entries]
        body += [""]

    return "\n".join(fm + body)


def has_imo(markdown: str) -> bool:
    """imo が書かれているか。

    サイト側（site/src/lib/imo.ts の imoOf）と同じ判定で、`imotech status` が使う。

    **探す範囲は imo 節の中だけ。** 以前は Markdown 全文から探していたが、
    `## 用語` の説明にその文言が紛れると、imo を書いても「未記入」と報告し続けた
    （サイトは節だけを見るので公開はされる＝監視だけが嘘をつく）。

    `imo_of` とは意味が違う。こちらは「人がプレースホルダを消したか」で、
    `imo_of` は「公開できる中身があるか」。不可視文字だけを書いた節は
    has_imo が True・imo_of が None になり、その差で書き直しを促せる。
    """
    found = _imo_section(markdown)
    if found is None:
        return False
    _, _, section = found
    return IMO_PLACEHOLDER not in section and IMO_SENTINEL not in section


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


IMO_HEADING = "## imo"
# 用語の節。見出しと節名は 1 か所から導く（片方だけ直す事故を防ぐ）
GLOSSARY_HEADING = "## 用語"
GLOSSARY_SECTION = GLOSSARY_HEADING.removeprefix("## ")

# imo の見出し。**サイト側（site/src/lib/imo.ts の IMO_HEADING）と同じ規則**にする。
# 素朴な部分一致にしていたため、`##  imo`（空白 2 個）や `##\timo` を取りこぼし、
# 逆に `## imo について` では「について」を imo 本文として取り込んでいた。
# 判定がずれると「Notion では公開済みなのにサイトに出ない」が起きる。
_IMO_HEADING_RE = re.compile(r"^##[ \t]+imo[ \t]*$", re.MULTILINE)
# 用語の 1 行。`- **語**: 説明` の形で書き、from_markdown が同じ形で読み戻す。
# 語の途中に `**` があっても、コロンの直前の `**` までを語として取る
# （非貪欲だが、後続の `**` + コロンを満たすまでバックトラックするため）。
# 行頭は strip してから照合する＝入れ子の子項目も同列の用語として拾う
_WHITESPACE_RUN_RE = re.compile(r"\s+")
_GLOSSARY_LINE_RE = re.compile(r"^-\s+\*\*(?P<term>.+?)\*\*\s*[:：]\s*(?P<desc>.+)$")
_NEXT_HEADING_RE = re.compile(r"^## ", re.MULTILINE)
_HTML_COMMENT_RE = re.compile(r"<!--[\s\S]*?-->")

# 目に見えない文字。str.strip() では落ちない。
# Cf（書式文字。ゼロ幅スペース U+200B、ゼロ幅非結合子 U+200C、BOM U+FEFF など）、
# Cc（制御文字）、Zs（空白区切り。全角空白 U+3000 を含む）を対象にする。
#
# 貼り付け事故で不可視文字だけが imo に入ると、strip() を通り抜けて
# 「所感が実質空の記事」が公開される。実測で U+200B / U+200C / U+FEFF が
# Python 側・サイト側・CI の漏れ検査のすべてを通過した。
# サイト側（site/src/lib/imo.ts の MEANINGLESS）と同じ規則にしてある。
_MEANINGLESS_CATEGORIES = frozenset({"Cf", "Cc", "Zs", "Zl", "Zp"})


def meaningful_text(text: str) -> str:
    """目に見える文字だけを残す。imo が実質空かどうかの判定に使う。

    返り値が空文字なら「書かれていない」とみなす。整形のためではなく
    判定のための関数なので、この返り値を本文として使ってはいけない。
    """
    return "".join(
        ch
        for ch in text
        if not ch.isspace() and unicodedata.category(ch) not in _MEANINGLESS_CATEGORIES
    )


def _imo_section(markdown: str) -> tuple[int, int, str] | None:
    """imo 節の (見出しの開始位置, 本文の開始位置, 本文) を返す。無ければ None。"""
    m = _IMO_HEADING_RE.search(markdown)
    if m is None:
        return None
    body_start = m.end()
    rest = markdown[body_start:]
    nxt = _NEXT_HEADING_RE.search(rest)
    section = rest[: nxt.start()] if nxt else rest
    return m.start(), body_start, section


def imo_of(markdown: str) -> str | None:
    """Markdown から imo の中身を取り出す。書かれていなければ None。

    サイト側（site/src/lib/imo.ts の imoOf）と同じ規則。許可リスト方式で、
    プレースホルダでも HTML コメントでもない文字が 1 文字以上あるときだけ返す。
    """
    found = _imo_section(markdown)
    if found is None:
        return None
    _, _, section = found
    if IMO_PLACEHOLDER in section or IMO_SENTINEL in section:
        return None
    text = _HTML_COMMENT_RE.sub("", section).strip()
    # 不可視文字だけの imo を公開しない
    return text if meaningful_text(text) else None


def set_imo(markdown: str, imo: str) -> str:
    """Markdown の imo 節を、渡された文章で置き換える。

    Notion で書かれた imo をローカルの Markdown に差し込むために使う。
    記事の本文は compose が書いたものが正で、Notion からは imo だけを持ってくる。
    こうすると Notion のブロックから記事を再構成せずに済み、
    「正となるデータは Git」（docs/DESIGN.md の Q2）も保てる。
    """
    text = imo.strip()
    if not meaningful_text(text):
        raise ValueError("imo に目に見える文字がない（空白や不可視文字だけでは差し込めない）")
    if IMO_PLACEHOLDER in text or IMO_SENTINEL in text:
        raise ValueError("imo にプレースホルダの文言が含まれている")

    found = _imo_section(markdown)
    if found is None:
        raise ValueError(f"{IMO_HEADING} の節が見つからない")
    _, body_start, section = found

    head = markdown[:body_start]
    nxt = _NEXT_HEADING_RE.search(markdown[body_start:])
    tail = markdown[body_start:][nxt.start() :] if nxt else ""
    # 生成時の書式（見出しの次は空行）に揃える。差分が読みやすい
    return f"{head}\n\n{text}\n" + (f"\n{tail}" if tail else "")


def _unquote_yaml(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        inner = v[1:-1]
        out, i = [], 0
        while i < len(inner):
            if inner[i] == "\\" and i + 1 < len(inner):
                nxt = inner[i + 1]
                out.append({"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, nxt))
                i += 2
            else:
                out.append(inner[i])
                i += 1
        return "".join(out)
    return v


def from_markdown(text: str) -> ArticleDraft:
    """to_markdown の逆変換。既存の Markdown から下書きを復元する。

    Notion へ後から投入する（notion-sync）ために使う。**stance は Markdown に
    書いていないので復元できない**（Notion のページ本文も stance を使わないため
    実害はないが、往復で失われる情報として自覚しておく）。
    url_hash も持っていないので sourceUrl から計算し直す。
    """
    from .urlhash import url_hash

    if not text.startswith("---\n"):
        raise ValueError("フロントマターが無い")
    block, _, body = text[4:].partition("\n---\n")

    fm: dict[str, str] = {}
    for line in block.splitlines():
        if ": " in line:
            k, v = line.split(": ", 1)
            fm[k.strip()] = v.strip()

    required = ["title", "sourceUrl", "sourceTitle", "hatenaUrl", "model"]
    missing = [k for k in required if k not in fm]
    # 議論の URL は新旧どちらのキーでもよい（旧: hnUrl）
    if "discussionUrl" not in fm and "hnUrl" not in fm:
        missing.append("discussionUrl")
    if missing:
        raise ValueError(f"フロントマターに {missing} が無い")

    # _yaml_list の出力は JSON 互換（\\ \" \n \r \t のみエスケープ）なので JSON として読む。
    # カンマで split すると、タグ自体にカンマが入ったときに壊れる
    tags_raw = fm.get("tags", "[]").strip()
    try:
        parsed = json.loads(tags_raw)
        tags = [str(t) for t in parsed] if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        tags = []

    digest: list[str] = []
    discourse: list[DiscoursePoint] = []
    glossary: list[GlossaryEntry] = []
    section = None
    point: str | None = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal point, buf
        if point is not None:
            discourse.append(DiscoursePoint(point, "\n\n".join(buf).strip(), "mixed"))
        point, buf = None, []

    for line in body.splitlines():
        if line.startswith("## "):
            flush()
            section = line[3:].strip()
            continue
        if section == "元記事の要旨" and line.startswith("- "):
            digest.append(line[2:].strip())
        elif section == GLOSSARY_SECTION:
            m = _GLOSSARY_LINE_RE.match(line.strip())
            if m is not None:
                glossary.append(
                    GlossaryEntry(term=m["term"].strip(), description=m["desc"].strip())
                )
        elif section == "議論の論調":
            if line.startswith("### "):
                flush()
                point = line[4:].strip()
            elif line.strip() and point is not None:
                buf.append(line.strip())
    flush()

    source_url = _unquote_yaml(fm["sourceUrl"])
    generated = fm.get("generatedAt", "")
    return ArticleDraft(
        url_hash=url_hash(source_url),
        title=_unquote_yaml(fm["title"]),
        slug="",  # 呼び出し側がファイル名から埋める
        digest=digest,
        discourse=discourse,
        tags=tags,
        glossary=glossary,
        source_url=source_url,
        source_title=_unquote_yaml(fm["sourceTitle"]),
        # 旧キー（hnUrl / hnScore / hnComments）も読む。ソースが Hacker News だけ
        # だった頃に書いた記事が残っているため（書き戻すと新しいキーになる）
        # 旧記事は source を持たない。ソースが 1 つだった頃のものなので補う
        source=_unquote_yaml(fm.get("source", "")) or "hackernews",
        discussion_url=_unquote_yaml(fm.get("discussionUrl") or fm.get("hnUrl", "")),
        hatena_url=_unquote_yaml(fm["hatenaUrl"]),
        engagement=Engagement(
            score=int(fm.get("score") or fm.get("hnScore") or 0),
            comments=int(fm.get("comments") or fm.get("hnComments") or 0),
        ),
        model=_unquote_yaml(fm["model"]),
        generated_at=datetime.fromisoformat(generated.replace("Z", "+00:00"))
        if generated
        else None,
    )


def load_article(path: Path) -> ArticleDraft:
    """Markdown ファイルを読んで下書きにする。slug はファイル名から取る。"""
    draft = from_markdown(path.read_text(encoding="utf-8"))
    return replace(draft, slug=path.stem)


# slug として許す形。Notion の Slug は人が編集できる rich_text なので、
# そのままパスに連結すると articles_dir の外に書き込める
# （実測: articles_dir / "../../../../evil.md" はリポジトリ直下に解決した）。
_SAFE_SLUG_RE = re.compile(r"^[0-9a-z][0-9a-z.-]{0,119}$")


def is_safe_slug(slug: str) -> bool:
    """パスに連結してよい slug か。"""
    return bool(_SAFE_SLUG_RE.fullmatch(slug)) and ".." not in slug


def article_path(articles_dir: Path, slug: str) -> Path | None:
    """slug から記事のパスを作る。安全でなければ None。

    形を検査したうえで、解決後のパスが articles_dir の中にあることも確かめる。
    """
    if not is_safe_slug(slug):
        return None
    path = (articles_dir / f"{slug}.md").resolve()
    if not path.is_relative_to(articles_dir.resolve()):
        return None
    return path


def imo_section_text(markdown: str) -> str | None:
    """imo 節から、プレースホルダを除いた中身を返す。節が無ければ None。

    imo_of との違いは、プレースホルダが残っていても**それ以外の文章があれば
    それを返す**こと。人がコメント行を消し切れずに所感を書き足した状態を
    検出して、その文章を Notion の値で上書きしないために使う。
    """
    found = _imo_section(markdown)
    if found is None:
        return None
    _, _, section = found
    section = _HTML_COMMENT_RE.sub("", section)
    # 閉じていないコメントの残骸と、プレースホルダの説明文も落とす
    for marker in (IMO_PLACEHOLDER, IMO_SENTINEL):
        if marker in section:
            section = "".join(
                line
                for line in section.splitlines(keepends=True)
                if IMO_PLACEHOLDER not in line and IMO_SENTINEL not in line
            )
    text = section.strip()
    return text if meaningful_text(text) else ""

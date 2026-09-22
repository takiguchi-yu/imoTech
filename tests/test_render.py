"""Markdown 生成のテスト。

フロントマターが壊れると Astro のビルドが落ちる。imo のプレースホルダがずれると
「所感を書いていない記事が公開される」という取り返しのつかない事故になるので、
サイト側の定数との突合もここで行う。
"""

from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from imotech.config import REPO_ROOT
from imotech.models import ArticleDraft, DiscoursePoint
from imotech.render import (
    IMO_PLACEHOLDER,
    IMO_PROMPT,
    IMO_SENTINEL,
    article_path,
    has_imo,
    imo_of,
    imo_section_text,
    is_safe_slug,
    meaningful_text,
    set_imo,
    to_markdown,
    write_article,
)


def _draft(**kw) -> ArticleDraft:
    base = dict(
        url_hash="h1",
        title="タイトル",
        slug="2026-09-21-example",
        digest=["要旨1", "要旨2", "要旨3"],
        discourse=[DiscoursePoint("論点A", "詳細A", "critical")],
        tags=["rust", "async"],
        source_url="https://e.com/a",
        source_title="The Article",
        hn_url="https://news.ycombinator.com/item?id=1",
        hatena_url="https://b.hatena.ne.jp/entry/s/e.com/a",
        hn_score=342,
        hn_comments=187,
        model="gemini-3.8-flash",
        generated_at=datetime(2026, 9, 21, 6, 12, tzinfo=UTC),
    )
    base.update(kw)
    return ArticleDraft(**base)


def _frontmatter(md: str) -> dict[str, str]:
    assert md.startswith("---\n")
    block = md.split("---\n", 2)[1]
    out = {}
    for line in block.splitlines():
        if ": " in line:
            k, v = line.split(": ", 1)
            out[k] = v
    return out


# --- フロントマター -------------------------------------------------------


def test_必要なキーがすべて出る():
    fm = _frontmatter(to_markdown(_draft()))
    expected = {
        "title",
        "publishedAt",
        "sourceUrl",
        "sourceTitle",
        "hnUrl",
        "hatenaUrl",
        "hnScore",
        "hnComments",
        "tags",
        "model",
        "generatedAt",
    }
    assert expected <= set(fm)


def test_引用符とコロンを含むタイトルで壊れない():
    md = to_markdown(_draft(title='Rust の "async" 分裂: 1年後'))
    assert _frontmatter(md)["title"] == '"Rust の \\"async\\" 分裂: 1年後"'


def test_バックスラッシュもエスケープされる():
    md = to_markdown(_draft(title=r"path\to\file"))
    assert _frontmatter(md)["title"] == r'"path\\to\\file"'


def test_改行を含むタイトルでフロントマターが1行に収まる():
    md = to_markdown(_draft(title="前半\n後半"))
    assert _frontmatter(md)["title"] == '"前半\\n後半"'


def test_数値はクォートしない():
    fm = _frontmatter(to_markdown(_draft()))
    assert fm["hnScore"] == "342"
    assert fm["hnComments"] == "187"


def test_タグは配列で出る():
    assert _frontmatter(to_markdown(_draft()))["tags"] == '["rust", "async"]'


def test_タグが空でも配列になる():
    assert _frontmatter(to_markdown(_draft(tags=[])))["tags"] == "[]"


def test_publishedAtはJSTで出る():
    fm = _frontmatter(to_markdown(_draft()))
    assert fm["publishedAt"] == "2026-09-21T15:12:00+09:00"


def test_generatedAtはUTCのZ表記():
    # docs/DESIGN.md 2.5 の表記に揃える
    assert _frontmatter(to_markdown(_draft()))["generatedAt"] == "2026-09-21T06:12:00Z"


def test_publishedAtを明示できる():
    when = datetime(2026, 12, 1, 9, tzinfo=timezone(timedelta(hours=9)))
    fm = _frontmatter(to_markdown(_draft(), published_at=when))
    assert fm["publishedAt"] == "2026-12-01T09:00:00+09:00"


# --- 本文 -----------------------------------------------------------------


def test_要旨と論調が本文に出る():
    md = to_markdown(_draft())
    assert "## 元記事の要旨" in md and "- 要旨1" in md
    assert "## 議論の論調" in md and "### 論点A" in md and "詳細A" in md


def test_出典と開示は本文に入れない():
    # サイトのテンプレートがフロントマターから描く。二重に持つと片方が古くなる
    md = to_markdown(_draft())
    assert "## 出典" not in md
    assert "生成モデル" not in md


def test_imoの欄がプレースホルダつきで出る():
    md = to_markdown(_draft())
    assert "## imo" in md
    assert IMO_PROMPT in md
    assert has_imo(md) is False


def test_プレースホルダを消すとimo記入済みになる():
    md = to_markdown(_draft()).replace(IMO_PROMPT, "これは面白い。")
    assert has_imo(md) is True


# --- サイト側との突合（ここがずれると未記入の記事が公開される）----------------


def test_サイト側の定数と一致している():
    # 定義元は site/src/lib/imo.ts の 1 箇所。ずれると imo 未記入の記事が公開される
    ts = (REPO_ROOT / "site" / "src" / "lib" / "imo.ts").read_text(encoding="utf-8")
    for name, value in [("IMO_PLACEHOLDER", IMO_PLACEHOLDER), ("IMO_SENTINEL", IMO_SENTINEL)]:
        assert f'export const {name} = "{value}";' in ts, (
            f"site/src/lib/imo.ts の {name} と render.py の定数がずれている。"
            "ずれると imo 未記入の記事が公開される"
        )


def test_サイトが許可リスト方式で判定している():
    # 「未記入の証拠があれば隠す」ではなく「記入の証拠があれば出す」であること。
    # body が取れないときに公開側へ倒れると、内容不明の記事が世に出る
    ts = (REPO_ROOT / "site" / "src" / "lib" / "imo.ts").read_text(encoding="utf-8")
    assert 'if (typeof body !== "string") return null;' in ts
    assert "meaningfulText(text).length > 0 ? text : null" in ts


def test_サイトも不可視文字を弾く():
    # 貼り付け事故で不可視文字だけが入ると trim() を通り抜ける。
    # 実測で U+200B / U+200C / U+FEFF が Python 側・サイト側・CI をすべて通過した
    ts = (REPO_ROOT / "site" / "src" / "lib" / "imo.ts").read_text(encoding="utf-8")
    assert "const MEANINGLESS = /[\\p{Cf}\\p{Cc}\\p{Z}\\s]/gu;" in ts, (
        "site/src/lib/imo.ts の MEANINGLESS と render.py の _MEANINGLESS_CATEGORIES がずれている"
    )


def test_サイトの判定が全経路で使われている():
    lib = (REPO_ROOT / "site" / "src" / "lib" / "articles.ts").read_text(encoding="utf-8")
    assert "publishedArticles" in lib and "isPublished" in lib
    for page in ["index.astro", "rss.xml.ts", "articles/[...slug].astro", "tags/[tag].astro"]:
        src = (REPO_ROOT / "site" / "src" / "pages" / page).read_text(encoding="utf-8")
        assert "publishedArticles" in src, f"{page} がゲートを通っていない"


# --- 書き出し -------------------------------------------------------------


def test_slugの名前でファイルを作る(tmp_path: Path):
    path, created = write_article(_draft(), tmp_path)
    assert created is True
    assert path.name == "2026-09-21-example.md"
    assert path.read_text(encoding="utf-8").startswith("---\n")


def test_ディレクトリが無ければ作る(tmp_path: Path):
    target = tmp_path / "a" / "b"
    path, created = write_article(_draft(), target)
    assert created is True and path.exists()


def test_既存ファイルは上書きしない(tmp_path: Path):
    # 人が imo を書き込んでいるかもしれない。上書きするとその手作業が消える
    path, _ = write_article(_draft(), tmp_path)
    path.write_text("人が書いた内容", encoding="utf-8")
    path2, created = write_article(_draft(), tmp_path)
    assert created is False
    assert path2 == path
    assert path.read_text(encoding="utf-8") == "人が書いた内容"


@pytest.mark.parametrize("title", ["A: B", 'A "B"', "A\\B", "絵文字 🎉", "A # B"])
def test_厄介なタイトルでもYAMLが1行に収まる(title):
    md = to_markdown(_draft(title=title))
    line = [x for x in md.splitlines() if x.startswith("title: ")][0]
    assert line.count("\n") == 0
    assert line.endswith('"')


# --- 実 YAML パーサでの往復検証 -------------------------------------------
#
# 自前の文字列分割だけで検証していたため、制御文字を素通しして
# サイトのビルド全体が落ちる不具合を見逃していた。ここは実パーサを通す。


def _parse_frontmatter(md: str) -> dict:
    import yaml

    return yaml.safe_load(md.split("---\n", 2)[1])


@pytest.mark.parametrize(
    "title",
    [
        "A: B",
        'A "B" C',
        r"path\to\file",
        "前半\n後半",
        "前半\r\n後半",
        "A\x0bB\x07C",
        "タブ\tあり",
        "絵文字 🎉 と # と - と [x]",
        "  前後に空白  ",
        "*アスタリスク* と &アンパサンド;",
        "\u200b ゼロ幅スペース",
    ],
)
def test_厄介なタイトルでもYAMLとして読み戻せる(title):
    fm = _parse_frontmatter(to_markdown(_draft(title=title)))
    assert isinstance(fm["title"], str)
    assert fm["title"].strip() != ""


def test_制御文字は除去される():
    # 1 文字でも生で入ると js-yaml が読めず、サイトのビルド全体が死ぬ。
    # エスケープすると YAML が読み戻して復活し HTML に入るので、落とす
    fm = _parse_frontmatter(to_markdown(_draft(title="A\x00B\x1fC\x07D")))
    assert fm["title"] == "ABCD"


def test_改行とタブは残す():
    fm = _parse_frontmatter(to_markdown(_draft(title="A\tB\nC")))
    assert fm["title"] == "A\tB\nC"


def test_全フィールドが期待した型で読み戻せる():
    fm = _parse_frontmatter(to_markdown(_draft()))
    assert isinstance(fm["hnScore"], int)
    assert isinstance(fm["hnComments"], int)
    assert isinstance(fm["tags"], list)
    assert all(isinstance(t, str) for t in fm["tags"])
    assert isinstance(fm["title"], str)


def test_改行を含むタイトルでもフロントマターが1行に収まる():
    for title in ["前半\n後半", "前半\r\n後半", "前半\r後半"]:
        md = to_markdown(_draft(title=title))
        block = md.split("---\n", 2)[1]
        title_lines = [ln for ln in block.splitlines() if ln.startswith("title: ")]
        assert len(title_lines) == 1
        assert _parse_frontmatter(md)["title"] is not None


# --- slug 衝突 -------------------------------------------------------------


def test_別記事が同じslugなら別名で書く(tmp_path: Path):
    # 黙って捨てると生成に使った API 呼び出しが無駄になり、候補も pending に残り続ける
    a = _draft(source_url="https://a.com/1", url_hash="aaaaaa")
    b = _draft(source_url="https://b.com/2", url_hash="bbbbbb")
    p1, c1 = write_article(a, tmp_path)
    p2, c2 = write_article(b, tmp_path)
    assert c1 is True and c2 is True
    assert p1 != p2
    assert p2.name == "2026-09-21-example-bbbbbb.md"


def test_同じ記事の再実行では新しく書かない(tmp_path: Path):
    a = _draft(source_url="https://a.com/1")
    write_article(a, tmp_path)
    _, created = write_article(a, tmp_path)
    assert created is False
    assert len(list(tmp_path.glob("*.md"))) == 1


# --- 内容が空の記事を作らない ----------------------------------------------


@pytest.mark.parametrize("kw", [{"digest": []}, {"discourse": []}, {"digest": [], "discourse": []}])
def test_要旨や論調が空なら記事にしない(kw):
    with pytest.raises(ValueError):
        to_markdown(_draft(**kw))


# --- 固定句による判定 ------------------------------------------------------


def test_固定句が残っていれば未記入とみなす():
    md = to_markdown(_draft()).replace(IMO_PLACEHOLDER, "")
    assert IMO_SENTINEL in md
    assert has_imo(md) is False


def test_両方消せば記入済みになる():
    md = to_markdown(_draft())
    md = md.replace(IMO_PROMPT, "これは面白い。")
    assert has_imo(md) is True


# --- imo の取り出しと差し込み（Notion から持ってくるために使う）-------------


def test_生成直後はimoが取れない():
    assert imo_of(to_markdown(_draft())) is None


def test_差し込んだimoを取り出せる():
    md = set_imo(to_markdown(_draft()), "これは面白い。")
    assert imo_of(md) == "これは面白い。"
    assert has_imo(md) is True


def test_差し込みは前後の空白を落とす():
    md = set_imo(to_markdown(_draft()), "  所感。  \n")
    assert imo_of(md) == "所感。"


def test_複数段落のimoも差し込める():
    imo = "1 段落目。\n\n2 段落目。"
    assert imo_of(set_imo(to_markdown(_draft()), imo)) == imo


def test_差し込んでも要旨と論調が残る():
    md = set_imo(to_markdown(_draft()), "所感。")
    assert "## 元記事の要旨" in md and "- 要旨1" in md
    assert "### 論点A" in md and "詳細A" in md


def test_差し込みは冪等ではなく置き換えになる():
    md = set_imo(to_markdown(_draft()), "1 回目")
    md = set_imo(md, "2 回目")
    assert imo_of(md) == "2 回目"
    assert "1 回目" not in md


def test_imoの後ろに別の節があっても保たれる():
    md = to_markdown(_draft()) + "\n## おまけ\n\n別の話。\n"
    out = set_imo(md, "所感。")
    assert imo_of(out) == "所感。"
    assert "## おまけ" in out and "別の話。" in out


@pytest.mark.parametrize("bad", ["", "   ", "\n\n", IMO_PLACEHOLDER, IMO_SENTINEL])
def test_空やプレースホルダは差し込めない(bad):
    with pytest.raises(ValueError):
        set_imo(to_markdown(_draft()), bad)


def test_imo節が無ければ差し込めない():
    with pytest.raises(ValueError):
        set_imo("## 要旨\n\n- x\n", "所感。")


def test_サイト側と同じ判定になる():
    # Python 側（imo_of）とサイト側（imoOf）で結果が食い違うと、
    # 「Notion では公開済みなのにサイトに出ない」が起きる
    md = to_markdown(_draft())
    cases = [
        (md, None),
        (set_imo(md, "所感。"), "所感。"),
        (md.replace(IMO_PROMPT, ""), None),
        (md.replace(IMO_PLACEHOLDER, ""), None),
    ]
    for text, expected in cases:
        assert imo_of(text) == expected


# --- imo の見出しの表記ゆれ（サイト側との一致の回帰テスト）------------------
#
# 素朴な部分一致にしていたため `##  imo` を取りこぼし、`## imo について` では
# 「について」を imo 本文として取り込んでいた。判定がずれると
# 「Notion では公開済みなのにサイトに出ない」が起きる。


ARTICLE_HEAD = '---\ntitle: "T"\n---\n\n## 元記事の要旨\n\n- a\n\n'


@pytest.mark.parametrize("heading", ["## imo", "##  imo", "##\timo", "##   imo  "])
def test_imo見出しの表記ゆれを受け入れる(heading):
    assert imo_of(f"{ARTICLE_HEAD}{heading}\n\n所感。\n") == "所感。"


@pytest.mark.parametrize("heading", ["## imo について", "## imoは", "### imo", "## IMO"])
def test_imo見出しでないものは受け入れない(heading):
    assert imo_of(f"{ARTICLE_HEAD}{heading}\n\n所感。\n") is None


def test_表記ゆれの見出しにも差し込める():
    md = f"{ARTICLE_HEAD}##  imo\n\n{IMO_PROMPT}\n"
    assert imo_of(md) is None
    out = set_imo(md, "所感。")
    assert imo_of(out) == "所感。"
    assert "##  imo" in out  # 見出しは書き換えない


def test_サイト側の見出し正規表現と一致している():
    ts = (REPO_ROOT / "site" / "src" / "lib" / "imo.ts").read_text(encoding="utf-8")
    # サイト側: /^##\s+imo\s*$/m 相当。Python 側は [ \t] に限定している（\s は改行を含むため）
    assert "IMO_HEADING = /^##[ \\t]+imo[ \\t]*$/m" in ts, (
        "site/src/lib/imo.ts の見出し正規表現と render.py の _IMO_HEADING_RE がずれている"
    )


# --- 不可視文字（レビューで実測された Blocker の回帰テスト）----------------


@pytest.mark.parametrize(
    "ch",
    [
        "\u200b",  # ゼロ幅スペース
        "\u200c",  # ゼロ幅非結合子
        "\u200d",  # ゼロ幅結合子
        "\ufeff",  # BOM
        "\u00a0",  # ノーブレークスペース
        "\u3000",  # 全角空白
        "   ",
        "\n\t ",
        "\u200b \u3000\ufeff",
    ],
)
def test_不可視文字だけのimoは差し込めない(ch):
    with pytest.raises(ValueError, match="目に見える文字がない"):
        set_imo(to_markdown(_draft()), ch)


@pytest.mark.parametrize("text", ["あ", "a", "🎉", "。", "1", "\u200bあ\u200b"])
def test_見える文字が1つでもあれば差し込める(text):
    md = set_imo(to_markdown(_draft()), text)
    assert imo_of(md) is not None


def test_不可視文字だけの節は公開しない():
    md = to_markdown(_draft()).replace(IMO_PROMPT, "\u200b\u3000")
    assert imo_of(md) is None
    assert has_imo(md) is True  # プレースホルダは消えているが
    assert meaningful_text(imo_section_text(md) or "") == ""


# --- slug の検証（パス外書き込みの回帰テスト）------------------------------


@pytest.mark.parametrize(
    "slug", ["2026-09-22-example", "abc", "a1-b2.c3", "2026-09-22-a-very-long-slug-name"]
)
def test_安全なslug(slug):
    assert is_safe_slug(slug) is True


@pytest.mark.parametrize(
    "slug",
    [
        "../../../evil",
        "..",
        "a/b",
        "a\\b",
        "ABC",
        "2026_09",
        "-leading",
        ".leading",
        "",
        "x" * 130,
        "a b",
        "日本語",
    ],
)
def test_危険なslugを弾く(slug):
    assert is_safe_slug(slug) is False


def test_パス外を指すslugではパスを作らない(tmp_path: Path):
    # 実測で articles_dir / "../../../../evil.md" はリポジトリ直下に解決した
    target = tmp_path / "articles"
    target.mkdir()
    assert article_path(target, "../../../evil") is None
    assert article_path(target, "2026-09-22-ok") == (target / "2026-09-22-ok.md").resolve()


# --- 手書き imo の保護（データ喪失の回帰テスト）----------------------------


def test_プレースホルダを消し忘れた手書きimoを検出する():
    # imo_of は「未記入」と判定するが、上書きすると手書きが消える
    md = to_markdown(_draft())
    md = md.replace(IMO_PROMPT, f"{IMO_PROMPT}\n\n面白かった。")
    assert imo_of(md) is None
    assert imo_section_text(md) == "面白かった。"


def test_プレースホルダだけなら空を返す():
    assert imo_section_text(to_markdown(_draft())) == ""


def test_節が無ければNoneを返す():
    assert imo_section_text("## 要旨\n\n- a\n") is None

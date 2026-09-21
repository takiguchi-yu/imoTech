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
    has_imo,
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
    assert "text.length > 0 ? text : null" in ts


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

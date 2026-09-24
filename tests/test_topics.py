"""話題の判定（src/imotech/topics.py、docs/DESIGN.md 4.1c）。"""

import pytest

from imotech.topics import Topic, load_topics, match_topics

TOPICS = load_topics()


@pytest.mark.parametrize(
    ("title", "url", "want"),
    [
        ("OpenAI releases GPT-6", "https://example.com/a", "AI"),
        ("Show HN: A tiny LLM runtime", "https://example.com/a", "AI"),
        ("Some announcement", "https://openai.com/index/x", "AI"),
        ("Cloudflare outage postmortem", "https://example.com", "クラウド"),
        ("What's new", "https://aws.amazon.com/blogs/x", "クラウド"),
        ("Next.js 16 is out", "https://example.com", "言語・フレームワーク"),
        ("Writing a compiler in Rust", "https://example.com", "言語・フレームワーク"),
        ("Apple announces new iPhone", "https://example.com", "ガジェット・IT ニュース"),
        ("生成AIで議事録を自動化した", "https://qiita.com/x/items/1", "AI"),
        ("生成ＡＩの使い方", "https://qiita.com/x/items/1", "AI"),  # 全角
        ("Qwen3 is out", "https://example.com", "AI"),  # 語の後ろの数字は許す
        ("Cheap GPUs for everyone", "https://example.com", "ガジェット・IT ニュース"),
    ],
)
def test_話題に当たる(title, url, want):
    assert want in match_topics(title, url, TOPICS)


@pytest.mark.parametrize(
    ("title", "url"),
    [
        # 語の境界で当てる。"ai" は "said"、"mac" は "machine" に当たらない
        ("He said the machine was broken", "https://example.com"),
        ("Spain blocks Archive.today", "https://reclaimthenet.org/x"),
        ("English a vs an determiners", "https://www.redblobgames.com/x"),
        # "go" は入れていない（普通の英単語と重なる）
        ("Let's go outside", "https://example.com"),
        ("How to react to criticism", "https://example.com"),
        ("A distant galaxy", "https://example.com"),
        ("Meta-analysis of sleep", "https://example.com"),
        ("FBI agents raid office", "https://example.com"),
        ("Pixel art tutorial", "https://example.com"),
    ],
)
def test_話題に当たらない(title, url):
    assert match_topics(title, url, TOPICS) == []


def test_記号を含む語も前後の境界で当てる():
    t = [Topic("L", ("c++", "next.js"))]
    assert match_topics("Modern C++ tips", "", t) == ["L"]
    assert match_topics("Next.js caching", "", t) == ["L"]
    assert match_topics("nextjsx", "", t) == []


def test_壊れた定義は落とす(tmp_path):
    p = tmp_path / "t.toml"
    p.write_text('[[topic]]\nname = "X"\nkeywords = []\n', encoding="utf-8")
    with pytest.raises(ValueError):
        load_topics(p)


def test_壊れたURLでも落ちない():
    assert match_topics("Something", "http://[abc/", TOPICS) == []


@pytest.mark.parametrize(
    "body",
    [
        "x = 1\n",  # [[topic]] が無い
        '[[topic]]\nname = "X"\nkeywords = "ai"\n',  # 文字列 1 つ（1 文字ずつになる）
    ],
)
def test_優先が黙って消える定義は落とす(tmp_path, body):
    p = tmp_path / "t.toml"
    p.write_text(body, encoding="utf-8")
    with pytest.raises(ValueError):
        load_topics(p)

"""匿名化のテスト。

Gemini の無料枠は入力が学習に使われ人間のレビュアーが読むため、ここが漏れると
第三者の PII を外部に送ることになる。誤検出（英文の破壊）も同時に見る。
"""

from imotech.anonymize import EMAIL_PLACEHOLDER, PLACEHOLDER, anonymize, strip_html
from imotech.models import Engagement, Reaction, SourceRef
from imotech.sources.hackernews import PROFILE_URL_RE


def _r(cid, author, text, depth=0, replies=0):
    return Reaction(comment_id=cid, author=author, text=text, depth=depth, reply_count=replies)


def test_HTMLタグと実体参照が平文になる():
    out = strip_html('A &quot;quote&quot;<p>next<a href="https://x.test">link</a>')
    assert "<" not in out and "&quot;" not in out
    assert '"quote"' in out and "link" in out


def test_投稿者名が出力に残らない():
    rs = [_r(1, "prologic", "hello"), _r(2, "x", "As prologic noted, it works")]
    out = anonymize(rs, limit=10)
    joined = " ".join(a.text for a in out)
    assert "prologic" not in joined
    assert PLACEHOLDER in joined


def test_アットマーク付きメンションが消える():
    out = anonymize([_r(1, "a", "@someuser is wrong")], limit=10)
    assert "@someuser" not in out[0].text
    assert PLACEHOLDER in out[0].text


def test_メールアドレスが消える():
    out = anonymize([_r(1, "a", "reach me at foo.bar+x@example.co.uk please")], limit=10)
    assert "example.co.uk" not in out[0].text
    assert EMAIL_PLACEHOLDER in out[0].text


def test_英単語と同じハンドルは本文を壊さない():
    # 実データで what というハンドルがいて英文中の what が全滅した事故の回帰テスト
    rs = [_r(1, "what", "irrelevant"), _r(2, "b", "should know what you do here")]
    out = anonymize(rs, limit=10)
    assert "should know what you do here" in " ".join(a.text for a in out)


def test_AnonymizedReactionにauthorフィールドが無い():
    # 型の上で投稿者を運べないことを担保する。llm.py はこの型しか受け取らない
    a = anonymize([_r(1, "someone", "text")], limit=10)[0]
    assert not hasattr(a, "author")


def test_返信の多い順に選ばれ元の並びに戻る():
    rs = [
        _r(1, "a", "first", depth=0, replies=0),
        _r(2, "b", "second", depth=0, replies=9),
        _r(3, "c", "third", depth=0, replies=5),
    ]
    out = anonymize(rs, limit=2)
    # 返信数で second と third が選ばれ、出力は元の並び順（second → third）
    assert [a.text for a in out] == ["second", "third"]
    assert [a.label for a in out] == ["C1", "C2"]


def test_返信数と階層は残る():
    out = anonymize([_r(1, "a", "t", depth=3, replies=7)], limit=10)
    assert (out[0].depth, out[0].reply_count) == (3, 7)


def test_空文字になった反応は落とす():
    assert anonymize([_r(1, "a", "<p></p>")], limit=10) == []


# --- URL の扱い（レビューで見つかった漏れと誤検出の回帰テスト）--------------


def test_URLのパス区画に一致するハンドルは伏せる():
    # github.com/<handle>/repo の形で投稿者名が残っていた
    out = anonymize([_r(1, "DanMcInerney", "see https://github.com/DanMcInerney/tool")], limit=5)
    assert "DanMcInerney" not in out[0].text
    assert "github.com" in out[0].text


def test_URLの一部に偶然一致しても壊さない():
    # ?ref=newsletter.com が ?ref=[ユーザー名].com に化ける事故の回帰テスト
    out = anonymize([_r(1, "newsletter", "https://e.com/p?ref=newsletter.com is fine")], limit=5)
    assert "?ref=newsletter.com" in out[0].text


def test_通常のURLは温存する():
    out = anonymize([_r(1, "someone", "source: https://example.com/a/b?x=1")], limit=5)
    assert "https://example.com/a/b?x=1" in out[0].text


def test_プロフィールURLは伏せる():
    # スレッド参加者でないハンドルも載るので、handles 集合では捕まらない。
    # URL の形はソースごとに違うので、パターンはソース側（hackernews.PROFILE_URL_RE）が持つ
    out = anonymize(
        [_r(1, "a", "see https://news.ycombinator.com/user?id=patio11")],
        limit=5,
        profile_url_re=PROFILE_URL_RE,
    )
    assert "patio11" not in out[0].text
    assert PLACEHOLDER in out[0].text


def test_ユーザー名を含むURLはリンクごと伏せる():
    out = anonymize([_r(1, "a", "read https://medium.com/@someone/article")], limit=5)
    assert "@someone" not in out[0].text
    assert "[リンク]" in out[0].text


def test_文頭で大文字にしたハンドルも伏せる():
    out = anonymize([_r(1, "alice", "x"), _r(2, "b", "Alice makes a good point")], limit=5)
    assert "Alice" not in " ".join(a.text for a in out)


def test_4文字未満のハンドルは伏せない():
    # 既知の限界。短い語を消すと文章が壊れるため意図的にそうしている
    out = anonymize([_r(1, "ab", "x"), _r(2, "b", "ab initio means from the start")], limit=5)
    assert "ab initio" in " ".join(a.text for a in out)


def test_投稿者の個人ドメインは伏せる():
    # https://<handle>.ca/... のような本人のサイト。PII の信号が強い
    out = anonymize([_r(1, "srcreigh", "see https://srcreigh.ca/posts/kata/")], limit=5)
    assert "srcreigh" not in out[0].text
    assert "/posts/kata/" in out[0].text


def test_wwwつきの個人ドメインも伏せる():
    out = anonymize([_r(1, "srcreigh", "see https://www.srcreigh.ca/x")], limit=5)
    assert "srcreigh" not in out[0].text


# --- 元記事の URL・タイトル（検証役が見つけた漏れの回帰テスト）----------------


def test_元記事URLのドメインが投稿者名と一致したら伏せる():
    # ブログ主が自分の記事を HN に投稿してコメントもする、というのはよくある
    from imotech.anonymize import scrub_url

    rs = [_r(1, "buchodi", "There are specific details about how it works")]
    assert scrub_url("https://www.buchodi.com/chatgpt-ad-collector/", rs) == (
        "https://www.[ユーザー名].com/chatgpt-ad-collector/"
    )


def test_無関係なドメインの元記事URLは温存する():
    from imotech.anonymize import scrub_url

    rs = [_r(1, "someone", "text")]
    url = "https://example.com/posts/a?x=1"
    assert scrub_url(url, rs) == url


def test_タイトルのメールアドレスは伏せるがハンドル衝突では壊さない():
    from imotech.anonymize import scrub_title

    rs = [_r(1, "story", "text")]
    # 見出しを素のハンドル衝突で壊すと害が大きいので、そこは伏せない
    assert scrub_title("Rust's async story", rs) == "Rust's async story"
    assert "[メールアドレス]" in scrub_title("Contact a@b.com for details", rs)


def test_build_user_promptが匿名化済みのURLを使う():
    from datetime import UTC, datetime

    from imotech.llm import build_user_prompt
    from imotech.models import AnonymizedReaction, ArticleSource, Story

    story = Story(
        ref=SourceRef("hackernews", "1"),
        url="https://buchodi.com/a",
        title="T",
        engagement=Engagement(score=300, comments=90),
        created_at=datetime.now(UTC),
    )
    p = build_user_prompt(
        story,
        ArticleSource("本文", "trafilatura"),
        [AnonymizedReaction("C1", "反応", 0, 1)],
        display_url="https://[ユーザー名].com/a",
    )
    assert "buchodi" not in p
    assert "https://[ユーザー名].com/a" in p

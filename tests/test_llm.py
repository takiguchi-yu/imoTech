"""LLM 層のテスト。実 API は呼ばず、フォールバックの挙動をモックで確かめる。"""

from dataclasses import replace
from datetime import UTC, datetime

import pytest
from google.genai import errors

from imotech.llm import (
    RESPONSE_SCHEMA,
    DraftGenerator,
    LLMError,
    _to_glossary,
    build_response_schema,
    build_user_prompt,
    slugify,
)
from imotech.models import (
    AnonymizedReaction,
    ArticleSource,
    Engagement,
    SourceRef,
    Story,
    UseCase,
)
from imotech.render import IMO_PLACEHOLDER, IMO_SENTINEL

STORY = Story(
    ref=SourceRef("hackernews", "42"),
    url="https://e.com/a",
    title="Example Title",
    engagement=Engagement(score=342, comments=187),
    created_at=datetime(2026, 9, 20, tzinfo=UTC),
    discussion_url="https://news.ycombinator.com/item?id=42",
)
ARTICLE = ArticleSource(text="本文の中身", via="trafilatura")
REACTIONS = [AnonymizedReaction(label="C1", text="ある反応", depth=0, reply_count=4)]

VALID_JSON = (
    '{"title":"日本語のタイトル","slug_hint":"example-title",'
    '"digest":["A","B","C"],'
    '"discourse":[{"point":"論点","detail":"詳細","stance":"critical"}],'
    '"tags":["rust","async"]}'
)


class _Resp:
    def __init__(self, text):
        self.text = text


class _Models:
    def __init__(self, behaviors):
        self._behaviors = behaviors
        self.calls = []

    def generate_content(self, *, model, contents, config):
        self.calls.append(model)
        b = self._behaviors.get(model, VALID_JSON)
        if isinstance(b, Exception):
            raise b
        return _Resp(b)


class _Client:
    def __init__(self, behaviors=None):
        self.models = _Models(behaviors or {})


def _gen(behaviors=None, chain=("m1", "m2", "m3"), attempts=2):
    return DraftGenerator(
        api_key="dummy",
        model_chain=chain,
        max_attempts=attempts,
        sleep=0,
        client=_Client(behaviors),
        sleeper=lambda _: None,
    )


def _run(g):
    return g.generate(STORY, ARTICLE, REACTIONS, url_hash="abc123", hatena_url="https://b/x")


# --- プロンプト -----------------------------------------------------------


def test_プロンプトに本文と反応が含まれる():
    p = build_user_prompt(STORY, ARTICLE, REACTIONS)
    assert "本文の中身" in p and "ある反応" in p
    assert "返信 4 件" in p and "階層 0" in p


def test_プロンプトにスコアとコメント数が入る():
    assert "スコア 342 / コメント 187" in build_user_prompt(STORY, ARTICLE, REACTIONS)


# --- slug ----------------------------------------------------------------


@pytest.mark.parametrize(
    "hint,expected",
    [
        ("The Rust Async  Split!!", "2026-09-21-the-rust-async-split"),
        ("---", "2026-09-21-untitled"),
        ("Café Naïve", "2026-09-21-cafe-naive"),
        ("日本語だけ", "2026-09-21-untitled"),
    ],
)
def test_slugは日付つきの英小文字になる(hint, expected):
    assert slugify(hint, when=datetime(2026, 9, 21, tzinfo=UTC)) == expected


# --- フォールバック -------------------------------------------------------


def test_最初のモデルで成功すれば次を呼ばない():
    g = _gen()
    r = _run(g)
    assert r.model == "m1"
    assert g._client.models.calls == ["m1"]
    assert r.draft.title == "日本語のタイトル"
    assert r.draft.slug.endswith("-example-title")


def test_429は同じモデルで再試行してから次へ落ちる():
    g = _gen({"m1": errors.ClientError(429, {"error": {"message": "rate"}})}, attempts=2)
    r = _run(g)
    assert g._client.models.calls == ["m1", "m1", "m2"]
    assert r.model == "m2"


def test_5xxもリトライ対象():
    g = _gen({"m1": errors.ServerError(503, {"error": {"message": "down"}})}, attempts=2)
    assert _run(g).model == "m2"


def test_400はリトライせず即座に次のモデルへ():
    # 入力が悪いのでリトライしても同じ。無駄な待ちを作らない
    g = _gen({"m1": errors.ClientError(400, {"error": {"message": "bad"}})}, attempts=3)
    r = _run(g)
    assert g._client.models.calls == ["m1", "m2"]
    assert r.model == "m2"


def test_壊れたJSONは再試行して次のモデルへ():
    g = _gen({"m1": "これはJSONではない"}, attempts=2)
    assert _run(g).model == "m2"


def test_全モデルで失敗したらLLMErrorを投げる():
    err = errors.ClientError(429, {"error": {"message": "rate"}})
    g = _gen({"m1": err, "m2": err, "m3": err}, attempts=1)
    with pytest.raises(LLMError):
        _run(g)


def test_生成結果にStoryのメタ情報が載る():
    d = _run(_gen()).draft
    assert d.url_hash == "abc123"
    assert d.discussion_url == "https://news.ycombinator.com/item?id=42"
    assert d.hatena_url == "https://b/x"
    assert (d.engagement.score, d.engagement.comments) == (342, 187)
    assert d.model == "m1"


# --- 記事間のウェイト -----------------------------------------------------


def test_1件目は待たず2件目から間隔を空ける():
    # 呼び出し側に任せると呼び忘れる。レート制限を守る責務は LLM 層が持つ
    waited: list[float] = []
    g = DraftGenerator(
        api_key="dummy",
        model_chain=("m1",),
        max_attempts=1,
        sleep=6.0,
        client=_Client(),
        sleeper=waited.append,
    )
    _run(g)
    assert waited == []
    _run(g)
    assert waited == [6.0]
    _run(g)
    assert waited == [6.0, 6.0]


def test_ウェイト0なら待たない():
    waited: list[float] = []
    g = DraftGenerator(
        api_key="dummy",
        model_chain=("m1",),
        max_attempts=1,
        sleep=0,
        client=_Client(),
        sleeper=waited.append,
    )
    _run(g)
    _run(g)
    assert waited == []


# --- 用語 -----------------------------------------------------------------
#
# glossary は RESPONSE_SCHEMA の required に入れていない（技術的でない記事で
# 無理やり用語を作らせないため）。返らないことを前提にした受け方をする。


def test_glossaryが返らなくても落ちない():
    # VALID_JSON は glossary を持たない＝実際に返らないケース
    assert _run(_gen()).draft.glossary == []


def test_glossaryが返れば復元される():
    payload = VALID_JSON[:-1] + (
        ',"glossary":[{"term":"PE","description":"未公開株に投資するファンド。"},'
        '{"term":"FTC","description":"米連邦取引委員会。"}]}'
    )
    got = _run(_gen({"m1": payload})).draft.glossary
    assert [(g.term, g.description) for g in got] == [
        ("PE", "未公開株に投資するファンド。"),
        ("FTC", "米連邦取引委員会。"),
    ]


def test_空の用語は捨てる():
    # 語だけ・説明だけの要素をそのまま記事に出すと「**語**: 」の行が残る
    payload = VALID_JSON[:-1] + (
        ',"glossary":[{"term":"","description":"説明だけ"},'
        '{"term":"語だけ","description":"   "},'
        '{"term":" PE ","description":" 前後に空白 "}]}'
    )
    got = _run(_gen({"m1": payload})).draft.glossary
    assert [(g.term, g.description) for g in got] == [("PE", "前後に空白")]


def test_スキーマがglossaryを0件から5件で定義している():
    g = RESPONSE_SCHEMA["properties"]["glossary"]
    assert g["maxItems"] == 5
    # minItems を置くと、用語の無い記事でも無理に埋めさせることになる
    assert "minItems" not in g
    assert "glossary" not in RESPONSE_SCHEMA["required"]


@pytest.mark.parametrize(
    "raw",
    [
        "なし",  # 文字列
        {"term": "x", "description": "y"},  # 配列でなく単体
        ["PE", "FTC"],  # 要素が文字列
        [None],
        5,
        None,
    ],
)
def test_glossaryが配列以外で返っても落ちない(raw):
    # glossary は required に入れていない＝モデルが型を外しうる唯一のフィールド。
    # 例外が上がると、リトライ節（ValueError/KeyError/JSONDecodeError）を
    # すり抜けてバッチの残り候補ごと落ちる
    assert _to_glossary(raw) == []


def test_glossaryの改行は空白に潰される():
    # Markdown の 1 行に収める。改行が残ると `- **語**: 説明` の形が割れる
    got = _to_glossary([{"term": "X", "description": "1 行目\n2 行目"}])
    assert [(g.term, g.description) for g in got] == [("X", "1 行目 2 行目")]


def test_imoの判定に使う文言を含む用語は捨てる():
    # 記事が「imo 未記入」に見え続けるのを防ぐ。set_imo が同じ文言を弾くのと対称
    raw = [
        {"term": "A", "description": f"{IMO_SENTINEL}という話。"},
        {"term": "B", "description": f"{IMO_PLACEHOLDER} を含む話。"},
        {"term": "C", "description": "普通の説明。"},
    ]
    assert [g.term for g in _to_glossary(raw)] == ["C"]


# --- 反応が無いソース -------------------------------------------------------


def test_反応が無ければ論調を求めない():
    """記事プラットフォーム（Qiita など）の記事はコメントがほぼ無い（実測で 82% が 0 件）。

    無い議論を要求すると、モデルは元記事の内容を論点に見せかけて埋めてしまい、
    「反応で述べられたことだけを書く」という約束が壊れる。
    """
    schema = build_response_schema(with_discourse=False)
    assert "discourse" not in schema["properties"]
    assert "discourse" not in schema["required"]
    # 他の必須項目は落とさない
    assert set(schema["required"]) == {"title", "slug_hint", "digest", "tags"}


def test_反応があれば論調を求める():
    assert build_response_schema(with_discourse=True) is RESPONSE_SCHEMA
    assert "discourse" in RESPONSE_SCHEMA["required"]


def test_スキーマの切り替えは元を壊さない():
    # 辞書を共有して書き換えると、次の記事の生成に影響が残る
    before = list(RESPONSE_SCHEMA["required"])
    build_response_schema(with_discourse=False)
    assert RESPONSE_SCHEMA["required"] == before


def test_反応が0件ならプロンプトにその旨を書く():
    p = build_user_prompt(STORY, ARTICLE, [])
    assert "この記事には反応がありません" in p
    assert "discourse` は出力しないでください" in p


def test_プロンプトのソース名はStoryから取る():
    # 「Hacker News」を埋め込まない。何の場での反応かで読み方が変わるので名前は出す
    p = build_user_prompt(STORY, ARTICLE, REACTIONS)
    assert "## hackernews での反応" in p

    qiita_story = replace(STORY, ref=SourceRef("qiita", "x"))
    assert "## qiita での反応" in build_user_prompt(qiita_story, ARTICLE, REACTIONS)


def test_論調を含まない応答からも記事を作れる():
    payload = (
        '{"title":"日本語のタイトル","slug_hint":"example-title",'
        '"digest":["A","B","C"],"tags":["rust"]}'
    )
    g = _gen({"m1": payload})
    result = g.generate(STORY, ARTICLE, [], url_hash="abc123", hatena_url="https://b/x")
    assert result.draft.discourse == []
    assert result.draft.digest == ["A", "B", "C"]


# --- 使いどころ ------------------------------------------------------------
#
# **このフィールドだけは元記事に書かれていない応用案を含む**（prompts/compose.md の
# 「守ること」4・6 に例外を書いてある）。他のフィールドに同じ緩みが漏れていないかを
# スキーマで固定する。


def test_使いどころはスキーマにあるが必須ではない():
    # 主張・意見の記事には使いどころが無い。数を埋めさせると的外れな提案が並ぶ
    s = RESPONSE_SCHEMA["properties"]["use_cases"]
    assert s["maxItems"] == 3
    assert "minItems" not in s
    assert "use_cases" not in RESPONSE_SCHEMA["required"]


def test_使いどころの要素は場面と説明を必須にする():
    item = RESPONSE_SCHEMA["properties"]["use_cases"]["items"]
    assert sorted(item["properties"]) == ["detail", "scene"]
    assert sorted(item["required"]) == ["detail", "scene"]


def test_反応が無い記事でも使いどころは求める():
    # 論調（discourse）は反応が要るが、使いどころは元記事だけで書ける
    s = build_response_schema(with_discourse=False)
    assert "use_cases" in s["properties"]
    assert "discourse" not in s["properties"]


def test_使いどころが返らなくても記事を作れる():
    g = _gen({"m1": VALID_JSON})
    result = _run(g)
    assert result.draft.use_cases == []


def test_使いどころを含む応答を読める():
    payload = (
        '{"title":"日本語のタイトル","slug_hint":"example-title",'
        '"digest":["A","B","C"],'
        '"discourse":[{"point":"論点","detail":"詳細","stance":"critical"}],'
        '"tags":["rust"],'
        '"use_cases":[{"scene":"社内で試したいとき","detail":"手元で動きます"}]}'
    )
    result = _run(_gen({"m1": payload}))
    assert result.draft.use_cases == [UseCase("社内で試したいとき", "手元で動きます")]


@pytest.mark.parametrize(
    "raw",
    [
        '"use_cases":"文字列"',  # 配列でない
        '"use_cases":[["場面","説明"]]',  # 要素が dict でない
        '"use_cases":[{"scene":"","detail":"説明"}]',  # 場面が空
        '"use_cases":[{"scene":"場面","detail":"  "}]',  # 説明が空白だけ
        '"use_cases":[{"scene":"場面"}]',  # 説明が無い
    ],
)
def test_壊れた使いどころは捨てる(raw):
    # required に入れていないので、モデルが型を外しても弾かれずに届く
    payload = (
        '{"title":"T","slug_hint":"s","digest":["A","B","C"],'
        '"discourse":[{"point":"p","detail":"d","stance":"mixed"}],'
        f'"tags":["rust"],{raw}}}'
    )
    assert _run(_gen({"m1": payload})).draft.use_cases == []


def test_imoのプレースホルダを使いどころに持ち込まない():
    # 運営の内部指示が読者に出る事故を防ぐ（用語と同じ扱い）
    payload = (
        '{"title":"T","slug_hint":"s","digest":["A","B","C"],'
        '"discourse":[{"point":"p","detail":"d","stance":"mixed"}],'
        f'"tags":["rust"],"use_cases":[{{"scene":"場面","detail":"{IMO_PLACEHOLDER}"}}]}}'
    )
    assert _run(_gen({"m1": payload})).draft.use_cases == []


def test_件数の上限をコードでも守る():
    """**スキーマの maxItems はプロバイダ側の努力目標。** フォールバック先の
    モデルほど守らないので、後処理でも切る。"""
    from imotech.llm import MAX_GLOSSARY, MAX_USE_CASES, _to_glossary, _to_use_cases

    many = [{"scene": f"s{i}", "detail": f"d{i}"} for i in range(10)]
    assert len(_to_use_cases(many)) == MAX_USE_CASES
    terms = [{"term": f"t{i}", "description": f"d{i}"} for i in range(10)]
    assert len(_to_glossary(terms)) == MAX_GLOSSARY


def test_桁で外れた長さは捨てる():
    """Markdown の 1 行が数千字になると、Notion では 1 件が複数ブロックに割れて
    「別々の項目」に見える。"""
    from imotech.llm import _to_use_cases

    assert _to_use_cases([{"scene": "x", "detail": "あ" * 3000}]) == []
    assert _to_use_cases([{"scene": "あ" * 300, "detail": "d"}]) == []
    # 少しの超過は許す（指示は 60〜120 字）
    assert len(_to_use_cases([{"scene": "x", "detail": "あ" * 150}])) == 1


def test_ラベルのアスタリスクを落とす():
    """`- **ラベル**: 本文` の形で書き出すので、ラベルに `**` が入ると
    閉じ位置がずれ、往復で内容が変わる。"""
    from imotech.llm import _to_use_cases

    assert _to_use_cases([{"scene": "A**: B", "detail": "d"}]) == [UseCase("A: B", "d")]

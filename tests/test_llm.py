"""LLM 層のテスト。実 API は呼ばず、フォールバックの挙動をモックで確かめる。"""

from datetime import UTC, datetime

import pytest
from google.genai import errors

from imotech.llm import (
    RESPONSE_SCHEMA,
    DraftGenerator,
    LLMError,
    _to_glossary,
    build_user_prompt,
    slugify,
)
from imotech.models import AnonymizedReaction, ArticleSource, Story
from imotech.render import IMO_PLACEHOLDER, IMO_SENTINEL

STORY = Story(
    hn_item_id=42,
    url="https://e.com/a",
    title="Example Title",
    points=342,
    num_comments=187,
    created_at=datetime(2026, 9, 20, tzinfo=UTC),
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
    assert d.hn_url == "https://news.ycombinator.com/item?id=42"
    assert d.hatena_url == "https://b/x"
    assert (d.hn_score, d.hn_comments) == (342, 187)
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

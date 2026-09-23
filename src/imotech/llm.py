"""Gemini による記事生成。

無料枠は入力が学習に使われ人間のレビュアーが読むため、この層は AnonymizedReaction
しか受け取らない型にしてある。生の Reaction を渡せないことで PII の送信を実装で防ぐ。
"""

from __future__ import annotations

import json
import re
import time
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from .models import (
    AnonymizedReaction,
    ArticleDraft,
    ArticleSource,
    DiscoursePoint,
    GlossaryEntry,
    Story,
    UseCase,
)
from .render import IMO_PLACEHOLDER, IMO_SENTINEL

PROMPT_PATH = Path(__file__).with_name("prompts") / "compose.md"

# slug の日付は JST。render.py の publishedAt と揃える
JST = timezone(timedelta(hours=9))

#: 用語と使いどころの件数の上限。スキーマ（maxItems）と後処理の両方がここを見る
MAX_GLOSSARY = 5
MAX_USE_CASES = 3

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "slug_hint": {"type": "string"},
        "digest": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 5},
        "discourse": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "point": {"type": "string"},
                    "detail": {"type": "string"},
                    "stance": {
                        "type": "string",
                        "enum": ["supportive", "critical", "mixed"],
                    },
                },
                "required": ["point", "detail", "stance"],
            },
            "minItems": 2,
            "maxItems": 4,
        },
        "tags": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 5},
        # 読者が知らない語でつまずかないための補足。分野は問わない。
        # **minItems を置かない**のは、そういう語が無い記事で数を埋めさせないため
        # （required にも入れない）
        "glossary": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["term", "description"],
            },
            "maxItems": MAX_GLOSSARY,
        },
        # その話題が誰のどんな場面で効きそうか。**元記事に書かれていない応用案を含む**
        # 唯一のフィールド（prompts/compose.md の「守ること」に例外を書いてある）。
        # glossary と同じく minItems を置かず required にも入れない — 主張・意見の
        # 記事には使いどころが無く、数を埋めさせると的外れな提案が並ぶ
        "use_cases": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scene": {"type": "string"},
                    "detail": {"type": "string"},
                },
                "required": ["scene", "detail"],
            },
            "maxItems": MAX_USE_CASES,
        },
    },
    "required": ["title", "slug_hint", "digest", "discourse", "tags"],
}


def build_response_schema(*, with_discourse: bool) -> dict:
    """生成に使う JSON スキーマ。

    **反応が 1 件も無いときは `discourse` を求めない。** 記事プラットフォーム
    （Qiita など）の記事にはコメントがほぼ付かず、実測で 82% が 0 件だった。
    無い議論を要求すると、モデルは元記事の内容を論点に見せかけて埋めてしまい、
    「反応で述べられたことだけを書く」という約束（prompts/compose.md）が壊れる。
    """
    if with_discourse:
        return RESPONSE_SCHEMA
    schema = {
        **RESPONSE_SCHEMA,
        "properties": {k: v for k, v in RESPONSE_SCHEMA["properties"].items() if k != "discourse"},
        "required": [k for k in RESPONSE_SCHEMA["required"] if k != "discourse"],
    }
    return schema


class LLMError(RuntimeError):
    """全モデルで生成に失敗した。呼び出し側は候補を pending のまま残す。"""


def load_system_instruction() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_user_prompt(
    story: Story,
    article: ArticleSource,
    reactions: list[AnonymizedReaction],
    *,
    display_url: str | None = None,
    display_title: str | None = None,
) -> str:
    """Gemini に渡す本文。--dry-run はこれをそのまま標準出力に出す。

    display_url / display_title には、匿名化を通した値を呼び出し側が渡す。
    この層は投稿者ハンドルの一覧を知らない（知らせない）設計なので、
    URL とタイトルの伏せ字は anonymize.scrub_url / scrub_title が担う。
    """
    lines = [
        "## 元記事",
        f"タイトル: {display_title if display_title is not None else story.title}",
        f"URL: {display_url if display_url is not None else story.url}",
        f"本文（{article.via} から取得、{len(article.text)} 文字）:",
        article.text,
        "",
    ]
    # ソース名は出す（何の場での反応かで読み方が変わる）が、**表示名は持たない** —
    # ソースごとの呼び名を知るのは表示層の責務で、この層はソースを知らない
    if reactions:
        lines += [
            f"## {story.ref.source} での反応（{len(reactions)} 件、投稿者情報は削除済み）",
            f"スコア {story.engagement.score} / コメント {story.engagement.comments}",
            "",
        ]
        lines += [
            f"[{r.label}] (返信 {r.reply_count} 件, 階層 {r.depth}) {r.text}" for r in reactions
        ]
    else:
        # **無い議論を書かせない。** 反応が無いことを明示しないと、モデルは
        # 元記事の内容を論点に見せかけて discourse を埋めてしまう
        lines += [
            f"## {story.ref.source} での反応",
            f"スコア {story.engagement.score} / コメント {story.engagement.comments}",
            "",
            "**この記事には反応がありません。** `discourse` は出力しないでください。",
            "",
        ]
    return "\n".join(lines)


def normalize_tag(tag: str) -> str:
    """タグを URL に置ける形に正規化する。

    LLM は「英小文字の技術タグ」と指示しても `ci/cd` `tcp/ip` `a/b testing` を返す。
    これらは指示に反していない（どれも英小文字の技術タグである）が、`/` が入ると
    Astro のルートパラメータ分解に失敗し、**そのタグだけでなくビルド全体が落ちる**。
    空白入りは URL が未エンコードのまま出力され、大文字小文字違いは macOS の
    ファイルシステムで衝突する。ここで潰しておく。
    """
    s = unicodedata.normalize("NFKD", tag).encode("ascii", "ignore").decode("ascii")
    # c++ を c に潰すと C 言語のタグと混ざる。慣例どおり cpp にする
    s = s.replace("+", "p")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return re.sub(r"-{2,}", "-", s)


def normalize_tags(tags: list[str], *, limit: int = 5) -> list[str]:
    """正規化し、空と重複を落として順序を保ったまま limit 件までにする。"""
    out: list[str] = []
    for t in tags:
        n = normalize_tag(t)
        if n and n not in out:
            out.append(n)
    return out[:limit]


def slugify(hint: str, *, when: datetime) -> str:
    """YYYY-MM-DD-<hint> の形にする。英数字とハイフン以外は落とす。

    日付は JST。publishedAt も JST なので、URL の日付と表示日付を揃える。
    UTC で切ると日本時間の朝に作った記事が前日の URL になる。
    """
    s = unicodedata.normalize("NFKD", hint).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    s = re.sub(r"-{2,}", "-", s)[:60].strip("-") or "untitled"
    return f"{when.astimezone(JST):%Y-%m-%d}-{s}"


@dataclass
class GenerationResult:
    draft: ArticleDraft
    model: str
    attempts: int


class DraftGenerator:
    """モデルフォールバックつきの生成器。

    429 / 5xx を受けたら同じモデルで指数バックオフして再試行し、尽きたら次のモデルへ
    落とす。全モデルで失敗したら LLMError を投げる（docs/DESIGN.md 5.1）。
    """

    def __init__(
        self,
        *,
        api_key: str,
        model_chain: tuple[str, ...],
        max_attempts: int = 3,
        sleep: float = 6.0,
        client: object | None = None,
        sleeper=time.sleep,
    ) -> None:
        self.model_chain = model_chain
        self.max_attempts = max_attempts
        self.sleep_seconds = sleep
        self._sleeper = sleeper
        if client is not None:
            self._client = client
        else:
            from google import genai

            self._client = genai.Client(api_key=api_key)
        self._system = load_system_instruction()
        # 1 回目の生成前には待たない。2 回目以降だけ間隔を空ける
        self._called_once = False

    def generate(
        self,
        story: Story,
        article: ArticleSource,
        reactions: list[AnonymizedReaction],
        *,
        url_hash: str,
        hatena_url: str,
        display_url: str | None = None,
        display_title: str | None = None,
    ) -> GenerationResult:
        from google.genai import errors, types

        prompt = build_user_prompt(
            story, article, reactions, display_url=display_url, display_title=display_title
        )
        config = types.GenerateContentConfig(
            system_instruction=self._system,
            response_mime_type="application/json",
            response_schema=build_response_schema(with_discourse=bool(reactions)),
            temperature=0.4,
            # ツールは一切使わない。既定のままだと SDK が毎回
            # 「Direct use of automatic function calling ... is not recommended」を
            # 出力し、Actions のログが警告で埋まって障害調査の邪魔になる。
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )

        # 連続呼び出しのあいだに固定のウェイトを入れる（docs/DESIGN.md 5.1）。
        # 呼び出し側に任せると呼び忘れるので、レート制限を守る責務はこの層で持つ。
        if self._called_once and self.sleep_seconds > 0:
            self._sleeper(self.sleep_seconds)
        self._called_once = True

        total_attempts = 0
        last_error: Exception | None = None

        for model in self.model_chain:
            for attempt in range(1, self.max_attempts + 1):
                total_attempts += 1
                try:
                    resp = self._client.models.generate_content(
                        model=model, contents=prompt, config=config
                    )
                    payload = _parse(resp)
                    draft = _to_draft(
                        payload,
                        story=story,
                        url_hash=url_hash,
                        hatena_url=hatena_url,
                        model=model,
                    )
                    return GenerationResult(draft=draft, model=model, attempts=total_attempts)
                except (errors.ClientError, errors.ServerError) as e:
                    last_error = e
                    code = getattr(e, "code", None)
                    retryable = code == 429 or (isinstance(code, int) and code >= 500)
                    print(f"  [warn] {model}: HTTP {code}（試行 {attempt}/{self.max_attempts}）")
                    if not retryable:
                        break  # 400 などはリトライしても同じ。次のモデルへ
                    if attempt < self.max_attempts:
                        self._sleeper(2**attempt)
                except (ValueError, KeyError, json.JSONDecodeError) as e:
                    last_error = e
                    print(f"  [warn] {model}: 応答を解釈できない（試行 {attempt}）: {e}")
                    if attempt >= self.max_attempts:
                        break

        raise LLMError(f"全 {len(self.model_chain)} モデルで生成に失敗: {last_error}")


def _parse(resp: object) -> dict:
    text = getattr(resp, "text", None)
    if not text:
        raise ValueError("応答が空")
    return json.loads(text)


# 改行が入ると Markdown の 1 行が割れ、`- **ラベル**: 本文` の形が崩れる。
# 2 行目以降は from_markdown が読み戻せず黙って消え、`## ` で始まる行なら
# 以降の項目ごと別セクション扱いになる（render.py の _LABELED_LINE_RE を参照）。
# **用語と使いどころの両方に効く** — どちらも同じ形で書き出している
_WHITESPACE_RUN_RE = re.compile(r"\s+")


#: `- **ラベル**: 本文` の 1 行として成立する長さの上限。
#:
#: プロンプトは用語 30〜80 字・使いどころ 60〜120 字を指示しているが、
#: **構造化出力の制約はプロバイダ側の努力目標**で、フォールバック先のモデルほど
#: 守らないことがある。桁で外れたものを通すと、Markdown の 1 行が数千字になり、
#: Notion では 1 件が複数のブロックに割れて「別々の項目」に見える。
#: **少しの超過は許し、桁で外れたものだけ捨てる**（切り詰めると文が壊れるので捨てる）。
_ASTERISK_RE = re.compile(r"\*+")
_MAX_LABEL_CHARS = 100
_MAX_TEXT_CHARS = 300


def _labeled_pairs(raw: object, label_key: str, text_key: str, limit: int) -> list[tuple[str, str]]:
    """LLM が返した `[{label_key: ..., text_key: ...}, ...]` を 2 つ組の並びにする。

    **ここは LLM の出力をそのまま受ける唯一の経路なので、型も長さも件数も信用しない。**
    `glossary` も `use_cases` も RESPONSE_SCHEMA の required に入れていない
    （要らない記事で数を埋めさせないため）ので、モデルが制約を外しても弾かれずに届く。
    """
    if not isinstance(raw, list):
        return []
    out: list[tuple[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        # **ラベルから `*` を落とす。** `- **ラベル**: 本文` の形で書き出すので、
        # ラベルに `**` が入ると閉じ位置がずれ、往復で内容が変わる
        # （`scene="A**: B"` → 読み戻すと scene='A', detail='B**: …'）
        label = _ASTERISK_RE.sub(
            "", _WHITESPACE_RUN_RE.sub(" ", str(item.get(label_key, "")))
        ).strip()
        text = _WHITESPACE_RUN_RE.sub(" ", str(item.get(text_key, ""))).strip()
        if not label or not text:
            continue
        if len(label) > _MAX_LABEL_CHARS or len(text) > _MAX_TEXT_CHARS:
            continue
        # imo のプレースホルダの文言を記事に持ち込まない。`has_imo` は imo 節の中しか
        # 見ないので判定は汚れないが、「このコメント行を消すまで公開されません」という
        # 運営の内部指示が読者に出るのは記事として成立しない
        if IMO_PLACEHOLDER in label + text or IMO_SENTINEL in label + text:
            continue
        out.append((label, text))
        # **件数もここで守る。** スキーマの maxItems を超えて返るモデルがある
        if len(out) >= limit:
            break
    return out


def _to_glossary(raw: object) -> list[GlossaryEntry]:
    """LLM が返した glossary を GlossaryEntry のリストにする。"""
    return [
        GlossaryEntry(term=t, description=d)
        for t, d in _labeled_pairs(raw, "term", "description", MAX_GLOSSARY)
    ]


def _to_use_cases(raw: object) -> list[UseCase]:
    """LLM が返した use_cases を UseCase のリストにする。"""
    return [
        UseCase(scene=s, detail=d) for s, d in _labeled_pairs(raw, "scene", "detail", MAX_USE_CASES)
    ]


def _to_draft(
    payload: dict, *, story: Story, url_hash: str, hatena_url: str, model: str
) -> ArticleDraft:
    now = datetime.now(UTC)
    # 反応が無い記事では discourse を求めていない（build_response_schema）
    discourse = [
        DiscoursePoint(point=d["point"], detail=d["detail"], stance=d["stance"])
        for d in payload.get("discourse") or []
    ]
    glossary = _to_glossary(payload.get("glossary"))
    use_cases = _to_use_cases(payload.get("use_cases"))
    return ArticleDraft(
        url_hash=url_hash,
        title=payload["title"],
        slug=slugify(payload["slug_hint"], when=now),
        digest=list(payload["digest"]),
        discourse=discourse,
        tags=normalize_tags(list(payload.get("tags") or [])),
        glossary=glossary,
        use_cases=use_cases,
        source_url=story.url,
        source_title=story.title,
        source=story.ref.source,
        discussion_url=story.discussion_url,
        hatena_url=hatena_url,
        engagement=story.engagement,
        model=model,
        generated_at=now,
    )

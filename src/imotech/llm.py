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
)
from .render import IMO_PLACEHOLDER, IMO_SENTINEL

PROMPT_PATH = Path(__file__).with_name("prompts") / "compose.md"

# slug の日付は JST。render.py の publishedAt と揃える
JST = timezone(timedelta(hours=9))

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
            "maxItems": 5,
        },
    },
    "required": ["title", "slug_hint", "digest", "discourse", "tags"],
}


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
        f"## Hacker News の反応（{len(reactions)} 件、投稿者情報は削除済み）",
        f"スコア {story.points} / コメント {story.num_comments}",
        "",
    ]
    for r in reactions:
        lines.append(f"[{r.label}] (返信 {r.reply_count} 件, 階層 {r.depth}) {r.text}")
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
            response_schema=RESPONSE_SCHEMA,
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


# 改行が入ると Markdown の 1 行が割れ、`- **語**: 説明` の形が崩れる。
# 2 行目以降は from_markdown が読み戻せず黙って消え、`## ` で始まる行なら
# 以降の用語ごと別セクション扱いになる（render.py の _GLOSSARY_LINE_RE を参照）
_WHITESPACE_RUN_RE = re.compile(r"\s+")


def _to_glossary(raw: object) -> list[GlossaryEntry]:
    """LLM が返した glossary を GlossaryEntry のリストにする。

    **ここは LLM の出力をそのまま受ける唯一の経路なので、型を信用しない。**
    `glossary` は RESPONSE_SCHEMA の required に入れていない（用語が要らない記事で
    数を埋めさせないため）ので、モデルが型を外しても弾かれずに届く。
    配列でなければ空、要素が dict でなければ捨てる。
    """
    if not isinstance(raw, list):
        return []
    out: list[GlossaryEntry] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        term = _WHITESPACE_RUN_RE.sub(" ", str(item.get("term", ""))).strip()
        desc = _WHITESPACE_RUN_RE.sub(" ", str(item.get("description", ""))).strip()
        if not term or not desc:
            continue
        # imo のプレースホルダの文言を記事に持ち込まない。`has_imo` は imo 節の中しか
        # 見ないので判定は汚れないが、「このコメント行を消すまで公開されません」という
        # 運営の内部指示が用語の説明として読者に出るのは記事として成立しない
        if IMO_PLACEHOLDER in term + desc or IMO_SENTINEL in term + desc:
            continue
        out.append(GlossaryEntry(term=term, description=desc))
    return out


def _to_draft(
    payload: dict, *, story: Story, url_hash: str, hatena_url: str, model: str
) -> ArticleDraft:
    now = datetime.now(UTC)
    discourse = [
        DiscoursePoint(point=d["point"], detail=d["detail"], stance=d["stance"])
        for d in payload["discourse"]
    ]
    glossary = _to_glossary(payload.get("glossary"))
    return ArticleDraft(
        url_hash=url_hash,
        title=payload["title"],
        slug=slugify(payload["slug_hint"], when=now),
        digest=list(payload["digest"]),
        discourse=discourse,
        tags=normalize_tags(list(payload.get("tags") or [])),
        glossary=glossary,
        source_url=story.url,
        source_title=story.title,
        hn_url=story.hn_url,
        hatena_url=hatena_url,
        hn_score=story.points,
        hn_comments=story.num_comments,
        model=model,
        generated_at=now,
    )

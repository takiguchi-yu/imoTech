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
from datetime import UTC, datetime
from pathlib import Path

from .models import AnonymizedReaction, ArticleDraft, ArticleSource, DiscoursePoint, Story

PROMPT_PATH = Path(__file__).with_name("prompts") / "compose.md"

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


def slugify(hint: str, *, when: datetime) -> str:
    """YYYY-MM-DD-<hint> の形にする。英数字とハイフン以外は落とす。"""
    s = unicodedata.normalize("NFKD", hint).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    s = re.sub(r"-{2,}", "-", s)[:60].strip("-") or "untitled"
    return f"{when.astimezone(UTC):%Y-%m-%d}-{s}"


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


def _to_draft(
    payload: dict, *, story: Story, url_hash: str, hatena_url: str, model: str
) -> ArticleDraft:
    now = datetime.now(UTC)
    discourse = [
        DiscoursePoint(point=d["point"], detail=d["detail"], stance=d["stance"])
        for d in payload["discourse"]
    ]
    return ArticleDraft(
        url_hash=url_hash,
        title=payload["title"],
        slug=slugify(payload["slug_hint"], when=now),
        digest=list(payload["digest"]),
        discourse=discourse,
        tags=list(payload.get("tags") or []),
        source_url=story.url,
        source_title=story.title,
        hn_url=story.hn_url,
        hatena_url=hatena_url,
        hn_score=story.points,
        hn_comments=story.num_comments,
        model=model,
        generated_at=now,
    )

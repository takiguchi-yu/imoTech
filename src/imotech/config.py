"""環境変数から読む設定。

閾値は運用しながら調整する前提のため、すべて環境変数で上書きできるようにしてある
（根拠は docs/DESIGN.md 4.2）。
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .models import Thresholds

REPO_ROOT = Path(__file__).resolve().parents[2]

#: IMOTECH_SOURCE_THRESHOLDS の 1 ソースに書ける項目。`Thresholds` のフィールドと一致する
_THRESHOLD_FIELDS = frozenset({"min_score", "min_comments"})

# フォールバックの順序。先頭から試し、429/5xx が続いたら次へ落とす。
# gemini-1.5-flash は 2025-09-29、2.0 系は 2026-06-01 に shutdown 済みで存在しない。
DEFAULT_MODEL_CHAIN = (
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
)

# サイト管理者が問い合わせ先を辿れるようにする。ドメイン確定後に差し替える（M0 の残タスク）。
USER_AGENT = "imoTechBot/1.0 (+https://github.com/takiguchi-yu/imoTech)"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=(),
        # validation_alias を付けたフィールドを、環境変数だけでなく
        # フィールド名でも渡せるようにする（テストや埋め込み利用のため）
        populate_by_name=True,
    )

    # --- 秘密情報（プレフィックスなし） ---
    gemini_api_key: str = ""
    notion_token: str = ""
    notion_database_id: str = ""

    # --- 収集 ---
    # 使うソース。カンマ区切りで複数指定できる（例: "hackernews,qiita"）。
    # 2 つ以上なら sources.registry が MultiFeed で束ねるので、呼び出し側は
    # 1 つか複数かを意識しない
    sources: str = Field(default="hackernews", validation_alias="IMOTECH_SOURCES")
    collect_window_hours: int = Field(default=24, validation_alias="IMOTECH_COLLECT_WINDOW_HOURS")
    collect_min_score: int = Field(default=10, validation_alias="IMOTECH_COLLECT_MIN_SCORE")
    collect_hits_per_page: int = Field(default=50, validation_alias="IMOTECH_COLLECT_HITS")

    # --- 熟成と選別（docs/DESIGN.md 4.1） ---
    maturation_hours: int = Field(default=24, validation_alias="IMOTECH_MATURATION_HOURS")
    min_score: int = Field(default=100, validation_alias="IMOTECH_MIN_SCORE")
    min_comments: int = Field(default=30, validation_alias="IMOTECH_MIN_COMMENTS")
    max_drafts_per_run: int = Field(default=5, validation_alias="IMOTECH_MAX_DRAFTS_PER_RUN")
    # ソースごとの閾値の上書き。JSON で指定する
    # 例: '{"qiita": {"min_score": 50, "min_comments": 0}}'
    # 指定が無いソースは、そのソース自身の既定（`Qiita.default_thresholds` など）を使い、
    # それも無ければ上の min_score / min_comments に倒す
    source_thresholds: str = Field(default="", validation_alias="IMOTECH_SOURCE_THRESHOLDS")
    max_age_hours: int = Field(default=96, validation_alias="IMOTECH_MAX_AGE_HOURS")

    # 1 回の実行で HN に問い合わせる候補の上限。pending が数千件に育っても
    # Actions の timeout を食い潰さないための天井（1 件あたり実測 0.5 秒前後）。
    max_probes_per_run: int = Field(default=60, validation_alias="IMOTECH_MAX_PROBES_PER_RUN")
    # 問い合わせ全体の予算（秒）。HN が不調でリトライが積み上がっても打ち切る。
    probe_budget_seconds: float = Field(default=300.0, validation_alias="IMOTECH_PROBE_BUDGET")

    # --- LLM ---
    model_chain: tuple[str, ...] = DEFAULT_MODEL_CHAIN
    llm_sleep_seconds: float = Field(default=6.0, validation_alias="IMOTECH_LLM_SLEEP_SECONDS")
    llm_max_attempts: int = Field(default=3, validation_alias="IMOTECH_LLM_MAX_ATTEMPTS")

    # --- 反応と本文 ---
    max_reactions: int = Field(default=80, validation_alias="IMOTECH_MAX_REACTIONS")
    max_article_chars: int = Field(default=8000, validation_alias="IMOTECH_MAX_ARTICLE_CHARS")
    http_timeout_seconds: float = Field(default=10.0, validation_alias="IMOTECH_HTTP_TIMEOUT")
    max_response_bytes: int = Field(
        default=5 * 1024 * 1024, validation_alias="IMOTECH_MAX_RESPONSE_BYTES"
    )

    # --- Notion ---
    # Free / Plus は 180 req/min（平均 3 req/sec）。リクエスト間に置く最小間隔
    notion_min_interval_seconds: float = Field(
        default=0.35, validation_alias="IMOTECH_NOTION_MIN_INTERVAL"
    )
    notion_max_attempts: int = Field(default=3, validation_alias="IMOTECH_NOTION_MAX_ATTEMPTS")
    notion_timeout_seconds: float = Field(default=30.0, validation_alias="IMOTECH_NOTION_TIMEOUT")

    # --- パス ---
    candidates_path: Path = Field(
        default=REPO_ROOT / "data" / "candidates.jsonl",
        validation_alias="IMOTECH_CANDIDATES_PATH",
    )
    # 公開物の Markdown の置き場所。Astro の Content Collections がここを見る
    articles_dir: Path = Field(
        default=REPO_ROOT / "site" / "src" / "content" / "articles",
        validation_alias="IMOTECH_ARTICLES_DIR",
    )

    @property
    def default_thresholds(self) -> Thresholds:
        """ソース固有の既定も上書きも無いときに使う閾値。従来の挙動そのもの。"""
        return Thresholds(min_score=self.min_score, min_comments=self.min_comments)

    @property
    def threshold_overrides(self) -> dict[str, Thresholds]:
        """`IMOTECH_SOURCE_THRESHOLDS` で明示された、ソースごとの閾値。

        壊れた JSON は黙って無視せず落とす。閾値の設定ミスを黙って握り潰すと、
        意図した数より多い・少ない記事が出続けて無人実行では気づけない。
        """
        raw = self.source_thresholds.strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"IMOTECH_SOURCE_THRESHOLDS が JSON として読めません: {e}") from None
        if not isinstance(parsed, dict):
            raise ValueError(
                "IMOTECH_SOURCE_THRESHOLDS はソース名をキーにしたオブジェクトで指定してください"
                ' （例: \'{"qiita": {"min_score": 50, "min_comments": 0}}\'）'
            )
        out: dict[str, Thresholds] = {}
        for name, spec in parsed.items():
            if not isinstance(spec, dict):
                raise ValueError(
                    f"IMOTECH_SOURCE_THRESHOLDS の {name!r} がオブジェクトではありません"
                )
            # **キー名の打ち間違いを黙って通さない。** min_score を minscore と書くと
            # 共通設定で埋められ、「設定したのに効かない」を無言で食うことになる
            unknown = sorted(set(spec) - _THRESHOLD_FIELDS)
            if unknown:
                raise ValueError(
                    f"IMOTECH_SOURCE_THRESHOLDS の {name!r} に知らない項目 "
                    f"{', '.join(unknown)} があります。使えるのは "
                    f"{', '.join(sorted(_THRESHOLD_FIELDS))}"
                )
            try:
                out[str(name)] = Thresholds(
                    min_score=int(spec.get("min_score", self.min_score)),
                    min_comments=int(spec.get("min_comments", self.min_comments)),
                )
            except (TypeError, ValueError):
                raise ValueError(
                    f"IMOTECH_SOURCE_THRESHOLDS の {name!r} の "
                    "min_score / min_comments は整数で指定してください"
                ) from None
        return out

    @property
    def source_names(self) -> list[str]:
        """使うソースの名前。空白を落としてリストにする。"""
        return [n.strip() for n in self.sources.split(",") if n.strip()]

    @property
    def notion_enabled(self) -> bool:
        """Notion を使うかどうか。

        トークンと DB の両方が揃っているときだけ使う。片方だけだと
        中途半端に失敗するので、揃っていなければ黙って Markdown 直書きに倒す。
        """
        return bool(self.notion_token and self.notion_database_id)


def load_settings() -> Settings:
    return Settings()

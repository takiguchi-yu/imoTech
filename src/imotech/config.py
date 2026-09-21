"""環境変数から読む設定。

閾値は運用しながら調整する前提のため、すべて環境変数で上書きできるようにしてある
（根拠は docs/DESIGN.md 4.2）。
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]

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
    collect_window_hours: int = Field(default=24, validation_alias="IMOTECH_COLLECT_WINDOW_HOURS")
    collect_min_score: int = Field(default=10, validation_alias="IMOTECH_COLLECT_MIN_SCORE")
    collect_hits_per_page: int = Field(default=50, validation_alias="IMOTECH_COLLECT_HITS")

    # --- 熟成と選別（docs/DESIGN.md 4.1） ---
    maturation_hours: int = Field(default=24, validation_alias="IMOTECH_MATURATION_HOURS")
    min_score: int = Field(default=100, validation_alias="IMOTECH_MIN_SCORE")
    min_comments: int = Field(default=30, validation_alias="IMOTECH_MIN_COMMENTS")
    max_drafts_per_run: int = Field(default=5, validation_alias="IMOTECH_MAX_DRAFTS_PER_RUN")
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

    # --- パス ---
    candidates_path: Path = Field(
        default=REPO_ROOT / "data" / "candidates.jsonl",
        validation_alias="IMOTECH_CANDIDATES_PATH",
    )


def load_settings() -> Settings:
    return Settings()

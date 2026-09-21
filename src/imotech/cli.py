"""コマンドラインのエントリポイント。

書き込み（候補ストアの更新、外部への送信）はここだけが行う。各モジュールは
自分の関心に閉じ、呼び出し順はこの層が決める。
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from collections import Counter
from datetime import UTC, datetime

from .anonymize import anonymize, scrub_title, scrub_url
from .config import USER_AGENT, Settings, load_settings
from .extract import ArticleFetcher
from .llm import LLMError, build_user_prompt, load_system_instruction
from .models import Candidate, CandidateState, SkipReason
from .pipeline import mark_skipped, matured_candidates, select
from .sources.hackernews import HackerNews
from .store import CandidateStore
from .urlhash import url_hash


def _p(msg: str = "", *, err: bool = False) -> None:
    """常に flush して出す。

    flush しないと、パイプや GitHub Actions のログで stdout がブロックバッファされ、
    stderr だけが先に抜けて時系列が逆転する。障害調査で「どこまで進んだか」が読めなくなる。
    """
    print(msg, file=sys.stderr if err else sys.stdout, flush=True)


def _now() -> datetime:
    return datetime.now(UTC)


# --- collect --------------------------------------------------------------


def cmd_collect(settings: Settings, args: argparse.Namespace) -> int:
    store = CandidateStore(settings.candidates_path)
    before = len(store.load())

    with HackerNews(user_agent=USER_AGENT) as hn:
        stories = hn.fetch_stories(
            window_hours=settings.collect_window_hours,
            min_points=settings.collect_min_score,
            limit=settings.collect_hits_per_page,
        )

    now = _now()
    candidates: list[Candidate] = []
    skipped_urls = 0
    for s in stories:
        try:
            h = url_hash(s.url)
        except ValueError:
            # 壊れた URL の 1 件で collect 全体を落とさない
            skipped_urls += 1
            continue
        candidates.append(
            Candidate(
                url_hash=h,
                hn_item_id=s.hn_item_id,
                url=s.url,
                title=s.title,
                collected_at=now,
                score_at_collect=s.points,
                comments_at_collect=s.num_comments,
            )
        )

    added = store.append_new(candidates)
    after = len(store.load())

    _p(
        f"HN から {len(stories)} 件取得 / 新規 {added} 件を追加 "
        f"（{before} → {after} 行）: {settings.candidates_path}"
    )
    if skipped_urls:
        _p(f"  URL を解釈できなかった {skipped_urls} 件は捨てました")
    return 0


# --- compose --------------------------------------------------------------


def cmd_compose(settings: Settings, args: argparse.Namespace) -> int:
    store = CandidateStore(settings.candidates_path)
    _p(f"候補ストア: {settings.candidates_path}")
    all_rows = store.load()

    if not all_rows:
        _p("候補ストアが空です。先に `uv run imotech collect` を実行してください。")
        return 0

    pending = [c for c in all_rows if c.state is CandidateState.PENDING]
    if not pending:
        _p(f"pending の候補がありません（全 {len(all_rows)} 件は処理済み）。")
        _p("内訳は `uv run imotech stats` で見られます。")
        return 0

    now = _now()
    matured = matured_candidates(pending, now=now, maturation_hours=settings.maturation_hours)
    _p(
        f"pending {len(pending)} 件 / 熟成済み {len(matured)} 件"
        f"（収集から {settings.maturation_hours}h 以上）"
    )
    if not matured:
        newest_wait = settings.maturation_hours - (
            (now - max(c.collected_at for c in pending)).total_seconds() / 3600
        )
        oldest_wait = settings.maturation_hours - (
            (now - min(c.collected_at for c in pending)).total_seconds() / 3600
        )
        _p(
            f"熟成した候補がありません。最も古い候補があと約 {max(oldest_wait, 0):.1f} 時間で"
            f"対象になります（最も新しいものは約 {max(newest_wait, 0):.1f} 時間後）。"
        )
        _p("いま動作を確かめたいときは IMOTECH_MATURATION_HOURS=0 を付けてください。")
        return 0

    # 外部にリクエストを出す前に API キーを確かめる。あとで気づくと、
    # 数十秒かけて HN を叩いたあとに落ちることになる。
    generator = None
    if not args.dry_run:
        if not settings.gemini_api_key:
            _p(
                "GEMINI_API_KEY が未設定です。.env に設定するか、"
                "--dry-run を付けるとキー無しでプロンプトを確認できます。"
                "（候補ストアは変更していません）",
                err=True,
            )
            return 2
        from .llm import DraftGenerator

        generator = DraftGenerator(
            api_key=settings.gemini_api_key,
            model_chain=settings.model_chain,
            max_attempts=settings.llm_max_attempts,
            sleep=settings.llm_sleep_seconds,
        )

    # 現在値を取り直す。収集時の値では「まだ誰も反応していない」段階を見てしまう。
    # ただし全件に問い合わせると pending が育ったとき Actions の timeout を食い潰すので、
    # 件数と時間の両方に天井を置く。
    probe_targets = sorted(matured, key=lambda c: (-c.score_at_collect, c.collected_at))[
        : settings.max_probes_per_run
    ]
    if len(probe_targets) < len(matured):
        _p(
            f"問い合わせは収集時スコアの上位 {len(probe_targets)} 件に絞ります"
            f"（熟成済み {len(matured)} 件中、上限 IMOTECH_MAX_PROBES_PER_RUN）"
        )

    deadline = time.monotonic() + settings.probe_budget_seconds
    evaluated: set[str] = set()
    stories_by_hash: dict[str, object] = {}
    reactions_by_hash: dict[str, list] = {}
    with HackerNews(user_agent=USER_AGENT) as hn:
        for i, c in enumerate(probe_targets, 1):
            if time.monotonic() > deadline:
                _p(
                    f"問い合わせの予算 {settings.probe_budget_seconds:.0f} 秒を超えたため "
                    f"{i - 1}/{len(probe_targets)} 件で打ち切ります"
                )
                break
            if i % 20 == 0:
                _p(f"  現在値を取得中… {i}/{len(probe_targets)}")
            story, reactions = hn.fetch_reactions(c.hn_item_id)
            if story is None:
                continue
            c.evaluated_at = now
            c.score_at_evaluate = story.points
            c.comments_at_evaluate = story.num_comments
            evaluated.add(c.url_hash)
            stories_by_hash[c.url_hash] = story
            reactions_by_hash[c.url_hash] = reactions
    _p(f"現在値を取得できたもの: {len(evaluated)}/{len(probe_targets)} 件")

    # 評価値を保存する。これが残らないと stats の分布が打ち切り側に偏り、
    # 閾値調整の材料にならない。
    if not args.dry_run and evaluated:
        store.update([c for c in probe_targets if c.url_hash in evaluated])
        _p(f"評価値 {len(evaluated)} 件を候補ストアに保存しました")

    max_drafts = args.limit if args.limit is not None else settings.max_drafts_per_run
    sel = select(
        matured,
        now=now,
        min_score=settings.min_score,
        min_comments=settings.min_comments,
        max_drafts=max_drafts,
        max_age_hours=settings.max_age_hours,
        evaluated=evaluated,
    )
    _p(
        f"閾値 points>={settings.min_score} かつ comments>={settings.min_comments} → "
        f"選出 {len(sel.selected)} 件 / 打ち切り {len(sel.to_skip)} 件"
    )
    if not sel.selected:
        _p("閾値を満たす候補がありません。今回は記事を作りません。")
        _p("分布を見るには `uv run imotech stats`、閾値は IMOTECH_MIN_SCORE で変えられます。")
        _apply_skips(store, sel.to_skip, dry_run=args.dry_run)
        return 0

    no_content: list[Candidate] = []
    with ArticleFetcher(
        user_agent=USER_AGENT,
        timeout=settings.http_timeout_seconds,
        max_bytes=settings.max_response_bytes,
        max_chars=settings.max_article_chars,
    ) as fetcher:
        for i, c in enumerate(sel.selected, 1):
            story = stories_by_hash[c.url_hash]
            _p(f"\n=== [{i}/{len(sel.selected)}] {c.title[:70]}")
            _p(f"    {c.url}")
            _p(f"    points={c.score_at_evaluate} comments={c.comments_at_evaluate}")

            article = fetcher.fetch(c.url)
            if article is None:
                _p("    → 本文を取得できないため飛ばします")
                no_content.append(c)
                continue

            raw_reactions = reactions_by_hash[c.url_hash]
            reactions = anonymize(raw_reactions, limit=settings.max_reactions)
            # 元記事の URL とタイトルも匿名化を通す。ブログ主が自分の記事を投稿して
            # コメントもする場合、ドメイン名が投稿者ハンドルと一致する
            display_url = scrub_url(c.url, raw_reactions)
            display_title = scrub_title(c.title, raw_reactions)
            _p(f"    本文 {len(article.text)} 文字 ({article.via}) / 反応 {len(reactions)} 件")

            if args.dry_run:
                _p("\n" + "=" * 70)
                _p("## システム指示（prompts/compose.md）")
                _p("=" * 70)
                _p(load_system_instruction())
                _p("=" * 70)
                _p("## ユーザープロンプト")
                _p("=" * 70)
                _p(
                    build_user_prompt(
                        story,
                        article,
                        reactions,
                        display_url=display_url,
                        display_title=display_title,
                    )
                )
                _p("=" * 70)
                _p("## レスポンススキーマ（response_schema として渡す）")
                _p("=" * 70)
                from .llm import RESPONSE_SCHEMA

                _p(json.dumps(RESPONSE_SCHEMA, ensure_ascii=False, indent=2))
                _p("=" * 70)
                continue

            try:
                result = generator.generate(
                    story,
                    article,
                    reactions,
                    url_hash=c.url_hash,
                    hatena_url=c.hatena_url,
                    display_url=display_url,
                    display_title=display_title,
                )
            except LLMError as e:
                _p(f"    → 生成に失敗、pending のまま残します: {e}")
                continue
            _p(f"    生成成功: model={result.model} attempts={result.attempts}")
            _p(
                json.dumps(
                    dataclasses.asdict(result.draft), ensure_ascii=False, indent=2, default=str
                )
            )
            _p("    ※ Notion への投入と state の更新は M2 で実装します")

    to_skip = list(sel.to_skip) + [(c, SkipReason.NO_CONTENT) for c in no_content]
    _apply_skips(store, to_skip, dry_run=args.dry_run)
    return 0


def _apply_skips(
    store: CandidateStore, to_skip: list[tuple[Candidate, SkipReason]], *, dry_run: bool
) -> None:
    if not to_skip:
        return
    if dry_run:
        _p(f"\n（--dry-run のため、打ち切り {len(to_skip)} 件は書き込みません）")
        return
    updated = [mark_skipped(c, reason) for c, reason in to_skip]
    store.update(updated)
    reasons = Counter(r.value for _, r in to_skip)
    detail = ", ".join(f"{k}={v}" for k, v in sorted(reasons.items()))
    _p(f"\n打ち切り {len(updated)} 件を skipped に更新しました（{detail}）")


# --- stats ----------------------------------------------------------------


def cmd_stats(settings: Settings, args: argparse.Namespace) -> int:
    _p(f"候補ストア: {settings.candidates_path}")
    rows = CandidateStore(settings.candidates_path).load()
    if not rows:
        _p("候補ストアは空です。`uv run imotech collect` を実行してください。")
        return 0
    states = Counter(c.state.value for c in rows)
    reasons = Counter(c.skip_reason for c in rows if c.skip_reason)
    scores = sorted(
        (c.score_at_evaluate for c in rows if c.score_at_evaluate is not None), reverse=True
    )
    _p(f"候補 {len(rows)} 件: " + ", ".join(f"{k}={v}" for k, v in sorted(states.items())))
    if reasons:
        _p("打ち切り理由: " + ", ".join(f"{k}={v}" for k, v in sorted(reasons.items())))
    if scores:
        mid = scores[len(scores) // 2]
        over = sum(1 for s in scores if s >= settings.min_score)
        _p(f"評価済みスコア: 最大 {scores[0]} / 中央 {mid} / 件数 {len(scores)}")
        _p(f"  （閾値 {settings.min_score} 以上: {over} 件 = {over / len(scores):.0%}）")
        if over > settings.max_drafts_per_run * len(scores) / 10:
            _p("  → 閾値を満たす候補が多い。IMOTECH_MIN_SCORE を上げる余地があります")
    else:
        _p("評価済み（compose を通った）候補はまだありません")
    return 0


# --- entrypoint -----------------------------------------------------------


def build_parser(settings: Settings | None = None) -> argparse.ArgumentParser:
    default_limit = settings.max_drafts_per_run if settings else 5
    p = argparse.ArgumentParser(
        prog="imotech",
        description="Hacker News の議論を日本語でまとめる自動化パイプライン",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("collect", help="HN から候補を収集して候補ストアに追記する")

    c = sub.add_parser(
        "compose",
        help="熟成した候補から記事の下書きを作る",
        description=(
            "熟成済みの候補に現在値を問い合わせ、閾値を満たす上位 N 件を記事化する。"
            "問い合わせは熟成済み全件ではなく、収集時スコア上位 "
            "IMOTECH_MAX_PROBES_PER_RUN 件までに絞られる。"
        ),
    )
    c.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Gemini を呼ばず、渡すもの（システム指示・ユーザープロンプト・"
            "レスポンススキーマ）を全て出力する。API キー不要、状態も変えない"
        ),
    )
    c.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help=f"作る下書きの上限（既定 {default_limit} = IMOTECH_MAX_DRAFTS_PER_RUN）",
    )

    sub.add_parser("stats", help="候補ストアを集計する（閾値調整の材料）")
    return p


def main(argv: list[str] | None = None) -> int:
    settings = load_settings()
    args = build_parser(settings).parse_args(argv)
    handlers = {"collect": cmd_collect, "compose": cmd_compose, "stats": cmd_stats}
    return handlers[args.command](settings, args)


if __name__ == "__main__":
    raise SystemExit(main())

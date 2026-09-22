"""コマンドラインのエントリポイント。

書き込み（候補ストアの更新、外部への送信）はここだけが行う。各モジュールは
自分の関心に閉じ、呼び出し順はこの層が決める。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from datetime import UTC, datetime

from .anonymize import anonymize, scrub_title, scrub_url
from .config import REPO_ROOT, USER_AGENT, Settings, load_settings
from .extract import ArticleFetcher
from .llm import LLMError, build_user_prompt, load_system_instruction
from .models import Candidate, CandidateState, SkipReason
from .notion import (
    DATABASE_SCHEMA,
    NotionBlockLimitError,
    NotionClient,
    NotionError,
    create_database_payload,
    patch_properties_payload,
    schema_diff,
)
from .pipeline import mark_skipped, matured_candidates, select
from .render import (
    article_path,
    from_markdown,
    has_imo,
    imo_of,
    imo_section_text,
    load_article,
    set_imo,
    write_article,
)
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

    notion, notion_ds = _open_notion(settings, dry_run=args.dry_run)

    no_content: list[Candidate] = []
    drafted: list[Candidate] = []
    empty: list[Candidate] = []
    failed: list[Candidate] = []
    # Notion の成否は終了コードの判定に使う。無人実行では、投入が全滅したことを
    # 標準エラーの warn だけで知る術がない（docs/DESIGN.md 5.5 の失敗検知）
    notion_ok: list[Candidate] = []
    notion_failed: list[Candidate] = []
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
                failed.append(c)
                continue
            _p(f"    生成成功: model={result.model} attempts={result.attempts}")
            try:
                path, created = write_article(result.draft, settings.articles_dir)
            except ValueError as e:
                # 要旨や論調が空。見出しだけの記事にはしない
                _p(f"    → 記事にならないため飛ばします: {e}")
                empty.append(c)
                continue
            rel = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
            _p(f"    → {rel}" if created else f"    → {rel} は既にあるので上書きしません")
            if not created:
                _p("      （この記事の生成結果は破棄しました。次回は生成しません）")
            # Notion が設定されていればレビュー面としても投入する。
            # 記事本文の正はあくまで Markdown で、Notion からは imo だけを持ってくる
            if notion is not None and not args.dry_run:
                try:
                    c.notion_page_id = notion.create_draft(
                        notion_ds, result.draft, collected_at=c.collected_at
                    )
                    _p(f"      Notion: {c.notion_page_id}")
                    notion_ok.append(c)
                except NotionBlockLimitError as e:
                    _p(f"      [warn] {e}", err=True)
                    notion_failed.append(c)
                    # 以降の候補で繰り返し叩かない。参照を捨てる前に閉じる
                    notion.close()
                    notion = None
                except NotionError as e:
                    _p(f"      [warn] Notion への投入に失敗: {e}", err=True)
                    notion_failed.append(c)

            # 書けても既にあっても、この候補の記事はディスク上に存在する。
            # 状態を進めないと毎回選出され、そのたびに Gemini を呼んで課金される
            c.state = CandidateState.DRAFTED
            drafted.append(c)
            # 途中で落ちても進捗が失われないよう、1 件ごとに書き戻す
            if not args.dry_run:
                store.update([c])

    to_skip = (
        list(sel.to_skip)
        + [(c, SkipReason.NO_CONTENT) for c in no_content]
        + [(c, SkipReason.LLM_FAILED) for c in empty]
    )
    _apply_skips(store, to_skip, dry_run=args.dry_run)

    if notion is not None:
        notion.close()

    # 何も成功しなかった実行でも、何が起きたかと次の一手を必ず出す
    _p("")
    summary = (
        f"まとめ: 選出 {len(sel.selected)} / 記事化 {len(drafted)} / "
        f"本文取得できず {len(no_content)} / 生成失敗 {len(failed)} / 内容不足 {len(empty)}"
    )
    if notion_ok or notion_failed:
        summary += f" / Notion 投入 {len(notion_ok)} 成功 {len(notion_failed)} 失敗"
    _p(summary)
    if args.dry_run:
        _p(f"--dry-run のため何も書いていません。本実行なら最大 {len(sel.selected)} 件を")
        _p(f"{settings.articles_dir} に書き出します。")
        return 0
    if drafted:
        _p(f"{settings.articles_dir} の `## imo` に所感を書くと公開されます。")
        _p("未記入の一覧は `uv run imotech status`、表示の確認は `cd site && npm run dev`。")
    elif failed:
        _p("生成に失敗した候補は pending のまま残しました。次回の実行で再挑戦します。")
    else:
        _p("新しく記事化できたものはありませんでした。")

    # ここから終了コードの判定。無人実行（daily.yml）はこれだけを見て Issue を立てる。
    #
    # 部分的な失敗は 0 で返す — 失敗した候補は pending に残り、次回の実行が拾う。
    # 1 件ごとに Issue が立つと通知が意味を失う（docs/DESIGN.md 5.5）。
    # 非 0 にするのは、次回も同じ結果になる＝人が直すまで回復しない失敗だけ。
    if failed and not drafted:
        _p(
            f"生成が {len(failed)} 件すべて失敗し、記事化できたものがありません。"
            "Gemini 側の障害かキーの失効が疑われます。",
            err=True,
        )
        return 1
    if notion_failed and not notion_ok:
        _p(
            f"Notion への投入が {len(notion_failed)} 件すべて失敗しました。"
            "NOTION_TOKEN / NOTION_DATABASE_ID とインテグレーションの接続を確認してください。",
            err=True,
        )
        return 1
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


def cmd_status(settings: Settings, args: argparse.Namespace) -> int:
    """書き出した記事のうち、imo がまだ書かれていないものを挙げる。

    「imo を書いたのにサイトに出ない」を自力で切り分けられるようにするため。
    判定はサイト側（site/src/lib/imo.ts）と同じ規則。
    """
    d = settings.articles_dir
    _p(f"記事ディレクトリ: {d}")
    if not d.exists():
        _p("まだ 1 件も書き出されていません。`uv run imotech compose` を実行してください。")
        return 0

    files = sorted(d.glob("*.md"))
    if not files:
        _p("まだ 1 件も書き出されていません。`uv run imotech compose` を実行してください。")
        return 0

    pending, published = [], []
    for f in files:
        (published if has_imo(f.read_text(encoding="utf-8")) else pending).append(f)

    _p(f"全 {len(files)} 件: 公開中 {len(published)} / imo 未記入 {len(pending)}")
    if pending:
        _p("")
        _p("imo 未記入（サイトに出ていません）:")
        for f in pending:
            _p(f"  {f.name}")
        _p("")
        if settings.notion_enabled:
            _p("Notion で imo を書いて Status を Approved にし、")
            _p("`uv run imotech publish` を実行すると Markdown に反映されます。")
            _p("Markdown に直接書いてもよく、その場合はローカルの内容が優先されます。")
        else:
            _p("各ファイルの `## imo` にあるコメント行を消して、自分の言葉で所感を書いてください。")
    return 0


def _notion_client(settings: Settings) -> NotionClient:
    """設定を反映した Notion クライアント。既定値で作らないための共通化。"""
    return NotionClient(
        token=settings.notion_token,
        min_interval=settings.notion_min_interval_seconds,
        max_attempts=settings.notion_max_attempts,
        timeout=settings.notion_timeout_seconds,
    )


def _open_notion(settings: Settings, *, dry_run: bool) -> tuple[NotionClient | None, str]:
    """Notion クライアントを用意する。使えなければ (None, "")。

    トークンと DB ID が揃っていないときは黙って Markdown 直書きだけに倒す。
    Notion は「あれば使うレビュー面」で、無くてもパイプラインは完結する。
    """
    if dry_run or not settings.notion_enabled:
        return None, ""
    client = _notion_client(settings)
    try:
        ds = client.data_source_id(settings.notion_database_id)
    except NotionError as e:
        _p(f"[warn] Notion を使えません（Markdown の書き出しは続けます）: {e}", err=True)
        client.close()
        return None, ""
    return client, ds


def cmd_publish(settings: Settings, args: argparse.Namespace) -> int:
    """Notion で承認された記事の imo を、ローカルの Markdown に差し込む。

    記事本文は compose が書いたものが正で、Notion からは人が書いた imo だけを
    持ってくる。こうすると Notion のブロックから記事を再構成せずに済み、
    「正となるデータは Git」（Q2 の決定）も保てる。

    **書き込む前に 3 つ確かめる。** どれかが崩れたらその 1 件を飛ばし、
    Notion 側も更新しない（次回また拾えるようにする）。

    1. slug が安全か — Notion の Slug は人が編集できるので、そのままパスに
       連結すると articles_dir の外に書き込める
    2. その Markdown が同じ記事か — Slug だけで引くと、slug が衝突した別の記事に
       imo を書き込んでしまう。フロントマターの sourceUrl から url_hash を
       計算し直して突き合わせる
    3. 人が手で書いた imo が無いか — プレースホルダを消し切れずに書き足した
       状態は imo_of では「未記入」に見える。そのまま上書きすると手書きが消える
    """
    if not settings.notion_enabled:
        _p(
            "NOTION_TOKEN と NOTION_DATABASE_ID が未設定です。"
            "Notion を使わない運用では、生成された Markdown の `## imo` に直接書いてください"
            "（`uv run imotech status` で未記入の一覧が出ます）。",
            err=True,
        )
        return 2

    client = _notion_client(settings)
    applied, already, skipped = 0, 0, 0
    try:
        ds = client.data_source_id(settings.notion_database_id)
        approved = client.fetch_approved(ds)
        _p(f"Notion で承認済み（imo 記入済み）: {len(approved)} 件")
        if not approved:
            _p("処理するものはありません。")
            _p("Notion 側で Status が Approved になっているか、imo が空でないか確認してください。")
            return 0

        for page in approved:
            path = article_path(settings.articles_dir, page.slug)
            if path is None:
                skipped += 1
                _p(
                    f"  [warn] Slug {page.slug!r} は記事のファイル名として使えません。"
                    "Notion 側の Slug が書き換えられていないか確認してください。",
                    err=True,
                )
                continue
            if not path.exists():
                skipped += 1
                _p(f"  [warn] {path} が見つかりません", err=True)
                _p(
                    f"         Notion 側の Slug は {page.slug!r} です。"
                    "この記事をまだ compose していないか、Notion で Slug が"
                    "書き換えられている可能性があります。",
                    err=True,
                )
                continue

            md = path.read_text(encoding="utf-8")

            # 同じ記事か。slug が衝突した別記事に書き込むのを防ぐ
            try:
                local_hash = url_hash(from_markdown(md).source_url)
            except ValueError as e:
                skipped += 1
                _p(f"  [warn] {path.name} のフロントマターを読めません: {e}", err=True)
                continue
            if local_hash != page.url_hash:
                skipped += 1
                _p(
                    f"  [warn] {path.name} は別の記事です"
                    f"（ローカル {local_hash} / Notion {page.url_hash}）。"
                    "slug が衝突しています。書き込みません。",
                    err=True,
                )
                continue

            # 人が手で書いた imo を Notion の値で消さない
            handwritten = imo_section_text(md)
            if handwritten:
                already += 1
                _p(f"  {path.name} はローカルの imo を優先しました")
                _p("      （Notion の imo は取り込んでいません）")
                if not imo_of(md):
                    _p(
                        "      ※ プレースホルダのコメント行が残っているため、"
                        "サイトにはまだ出ません。その行を消してください。",
                        err=True,
                    )
                if not args.dry_run:
                    client.mark_published(page.page_id)
                continue

            try:
                updated = set_imo(md, page.imo)
            except ValueError as e:
                # 空白や不可視文字だけの imo、見出しが無い、など。
                # ここで落とすと以降の承認済みページが 1 件も処理されない
                skipped += 1
                _p(f"  [warn] {path.name} に差し込めません: {e}", err=True)
                continue

            if args.dry_run:
                applied += 1
                _p(f"  {path.name} に imo を差し込みます（--dry-run のため書きません）")
                _p(f"      imo: {page.imo[:60]}{'…' if len(page.imo) > 60 else ''}")
                continue

            path.write_text(updated, encoding="utf-8")
            applied += 1
            _p(f"  {path.name} に imo を差し込みました")
            # Markdown を書いたあとに Notion を進める。逆順にすると、
            # 書き込みに失敗したときに Notion だけ Published になって二度と拾えない
            client.mark_published(page.page_id)

        _p("")
        verb = "差し込む予定" if args.dry_run else "差し込み"
        _p(f"まとめ: {verb} {applied} / ローカル優先 {already} / 飛ばした {skipped}")
        if args.dry_run:
            _p("--dry-run のため、Markdown も Notion も変更していません。")
        if skipped:
            _p("飛ばした分は Notion の Status を Approved のままにしてあります。")
            _p("原因を直してもう一度実行すれば処理されます。")
        if applied or already:
            _p("`cd site && npm run dev` で表示を確認してください。")
            _p("公開物は Git が正なので、確認できたら commit してください。")
        return 0
    except NotionError as e:
        _p(f"Notion の呼び出しに失敗しました: {e}", err=True)
        _p(f"（ここまでの処理: 差し込み {applied} / ローカル優先 {already} / 飛ばした {skipped}）")
        return 1
    finally:
        client.close()


def cmd_notion_setup(settings: Settings, args: argparse.Namespace) -> int:
    """Notion のデータベースを docs/DESIGN.md 3.1 のスキーマに合わせる。

    既定は「既に NOTION_DATABASE_ID にある DB に足りないプロパティを追加する」。
    Notion の UI で作った空の DB を使う場合がこれにあたる。
    --create を渡したときだけ新しい DB を作る。
    """
    if not settings.notion_token:
        _p(
            "NOTION_TOKEN が未設定です。"
            "発行の手順は README の「Notion をレビュー面として使う」の"
            "「初期準備」節を参照してください。",
            err=True,
        )
        return 2

    if not args.create:
        return _notion_patch_existing(settings, args)

    payload = create_database_payload(args.create, args.title)
    if args.dry_run:
        _p("--dry-run のため作成しません。送るボディ:")
        _p(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    client = _notion_client(settings)
    try:
        data = client.request("POST", "/databases", json=payload)
    except NotionError as e:
        _p(f"作成に失敗しました: {e}", err=True)
        _p("", err=True)
        _p(
            "プロパティのスキーマの書式は公式ドキュメントで確認できていない箇所があります"
            "（notion.py の DATABASE_SCHEMA のコメント参照）。"
            "上の message を見て DATABASE_SCHEMA を直してください。",
            err=True,
        )
        return 1
    finally:
        client.close()

    db_id = data.get("id", "")
    _p(f"データベースを作成しました: {db_id}")
    _p(f"URL: {data.get('url', '')}")
    _p("")
    _p(".env に次を追記してください:")
    _p(f"  NOTION_DATABASE_ID={db_id}")
    return 0


def _notion_patch_existing(settings: Settings, args: argparse.Namespace) -> int:
    """既存の DB に足りないプロパティを追加する。"""
    if not settings.notion_database_id:
        _p(
            "NOTION_DATABASE_ID が未設定です。"
            "既存の DB を使うなら .env に設定してください。"
            "新しく作るなら `notion-setup --create <親ページ ID>` を使ってください。",
            err=True,
        )
        return 2

    client = _notion_client(settings)
    try:
        ds_id = client.data_source_id(settings.notion_database_id)
        ds = client.request("GET", f"/data_sources/{ds_id}")
        existing = ds.get("properties") or {}
        missing, rename, mismatched = schema_diff(existing)

        _p(f"データソース: {ds_id}")
        _p(f"既存のプロパティ: {len(existing)} 件 {sorted(existing)}")
        if rename:
            for old_name, spec in rename.items():
                _p(f"改名: {old_name!r} → {spec['name']!r}（タイトル型は 1 つだけ持てるため）")
        _p(f"追加するプロパティ: {len(missing)} 件 {sorted(missing)}")

        if mismatched:
            # 型は API では変えられない。名前だけ見て「揃っている」と言うと、
            # そのあと compose が送る値が毎回 400 になる
            _p("")
            _p("★ 型が設計書と違うプロパティがあります。API では直せません。", err=True)
            for name, d in sorted(mismatched.items()):
                _p(f"    {name}: 期待 {d['expected']} / 実際 {d['actual']}", err=True)
            _p("", err=True)
            _p(
                "Notion の UI でこれらのプロパティを削除し、"
                "もう一度 notion-setup を実行してください"
                "（Status は Status 型ではなく Select 型で作る必要があります）。",
                err=True,
            )
            return 1

        if not missing and not rename:
            _p("スキーマは既に揃っています。何もしません。")
            return 0

        payload = patch_properties_payload(existing)
        if args.dry_run:
            _p("")
            _p("--dry-run のため変更しません。送るボディ:")
            _p(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        client.request("PATCH", f"/data_sources/{ds_id}", json=payload)
        _p("")
        _p("スキーマを更新しました。")
        after = client.request("GET", f"/data_sources/{ds_id}").get("properties") or {}
        _, _, still_mismatched = schema_diff(after)
        still = sorted(set(DATABASE_SCHEMA) - set(after))
        if still or still_mismatched:
            if still:
                _p(f"★ まだ足りないもの: {still}", err=True)
            if still_mismatched:
                _p(f"★ 型が合わないもの: {sorted(still_mismatched)}", err=True)
            return 1
        _p(f"設計書の {len(DATABASE_SCHEMA)} 件すべてが揃いました（現在 {len(after)} 件）。")
        return 0
    except NotionError as e:
        _p(f"Notion の呼び出しに失敗しました: {e}", err=True)
        return 1
    finally:
        client.close()


def cmd_notion_sync(settings: Settings, args: argparse.Namespace) -> int:
    """既に書き出した Markdown を Notion に投入する。

    Gemini を呼ばない。生成済みの記事を後から Notion に載せる用途
    （Notion を後で用意した場合や、投入に失敗した分のやり直し）。
    URL Hash で既存を判定するので、何度実行しても増えない。
    """
    if not settings.notion_enabled:
        _p(
            "NOTION_TOKEN と NOTION_DATABASE_ID が必要です。"
            "設定の取り方は README の「Notion をレビュー面として使う」の"
            "「初期準備」節を参照してください。"
            "Notion を使わない運用では、生成された Markdown の `## imo` に直接書きます"
            "（`uv run imotech status` で未記入の一覧が出ます）。",
            err=True,
        )
        return 2

    files = sorted(settings.articles_dir.glob("*.md"))
    _p(f"記事ディレクトリ: {settings.articles_dir}（{len(files)} 件）")
    if not files:
        _p("投入するものがありません。")
        return 0

    # 投入した page id を候補ストアに書き戻す。ここを書かないと、あとから
    # 「この記事の Notion ページはどれか」を辿れなくなる
    store = CandidateStore(settings.candidates_path)
    by_hash = {c.url_hash: c for c in store.load()}
    touched: list[Candidate] = []

    client = _notion_client(settings)
    created, existed, failed = 0, 0, 0
    aborted: str | None = None
    try:
        ds = client.data_source_id(settings.notion_database_id)
        for f in files:
            try:
                draft = load_article(f)
            except ValueError as e:
                _p(f"  [warn] {f.name} を読めません: {e}", err=True)
                failed += 1
                continue
            candidate = by_hash.get(draft.url_hash)
            try:
                before = client.find_page_by_url_hash(ds, draft.url_hash)
                page_id = client.create_draft(
                    ds,
                    draft,
                    # 設計書 3.1 の Collected At は「候補として拾った時刻」。
                    # 渡さないと生成時刻にフォールバックして別の値になる
                    collected_at=candidate.collected_at if candidate else None,
                )
            except NotionError as e:
                _p(f"  [warn] {f.name} の投入に失敗: {e}", err=True)
                failed += 1
                continue
            if before:
                existed += 1
                _p(f"  {f.name} は既にあります（{page_id}）")
            else:
                created += 1
                _p(f"  {f.name} → {page_id}")

            if candidate is not None and candidate.notion_page_id != page_id:
                candidate.notion_page_id = page_id
                # skipped からは戻さない（models.py の CandidateState の不変条件）
                if candidate.state is CandidateState.PENDING:
                    candidate.state = CandidateState.DRAFTED
                touched.append(candidate)
    except NotionError as e:
        # ここで return せず、下の集計と書き戻しを通す。
        # 途中で落ちたときに「何件入ったか」「どこから再開すればよいか」が
        # 出力から辿れないと、利用者は全部やり直すしかなくなる
        aborted = str(e)
        _p(f"Notion の呼び出しに失敗したため中断しました: {e}", err=True)
    finally:
        client.close()

    if touched:
        store.update(touched)
        _p("")
        _p(f"候補ストアに notion_page_id を記録しました（{len(touched)} 件）")

    _p("")
    _p(f"まとめ: 新規 {created} / 既存 {existed} / 失敗 {failed}")
    if aborted:
        _p("残りは投入されていません。もう一度実行してください。")
        _p("既に入った分は URL Hash で判定され、重複して増えることはありません。")
        return 1
    if created:
        _p("Notion で imo を書いて Status を Approved にしてください。")
        _p("そのあと `uv run imotech publish` で Markdown に反映されます。")
    return 1 if failed else 0


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
            "NOTION_TOKEN と NOTION_DATABASE_ID が揃っていれば、Markdown の書き出しに加えて "
            "Notion にも下書きを投入する（--dry-run のときは Notion に触らない）。"
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
    sub.add_parser("status", help="書き出した記事のうち imo 未記入のものを挙げる")

    sub.add_parser(
        "notion-sync",
        help="既に書き出した Markdown を Notion に投入する（Gemini を呼ばない）",
        description=(
            "site/src/content/articles/*.md を読んで Notion に下書きページを作る。"
            "URL Hash で既存を判定するので何度実行しても増えない。"
        ),
    )

    pub = sub.add_parser(
        "publish",
        help="Notion で承認された記事の imo を Markdown に差し込む",
        description=(
            "Status が Approved かつ imo が空でないページを探し、その imo を "
            "site/src/content/articles/<slug>.md に差し込んで Notion 側を Published にする。"
            "記事本文は compose が書いたものが正で、Notion からは imo だけを持ってくる。"
            "ローカルに既に imo があればそちらを優先し、Notion の値は取り込まない。"
        ),
    )
    pub.add_argument(
        "--dry-run",
        action="store_true",
        help="Markdown も Notion も変更せず、何が起きるかだけを表示する",
    )

    ns = sub.add_parser(
        "notion-setup",
        help="Notion の DB を docs/DESIGN.md 3.1 のスキーマに合わせる",
        description=(
            "既定では NOTION_DATABASE_ID の DB に足りないプロパティを追加する"
            "（Notion の UI で作った空の DB を使う場合）。"
            "⚠️ 既存のタイトル列は Title に改名される"
            "（Notion はタイトル型のプロパティを 1 つしか持てないため）。"
            "既存のプロパティを削除することはない。"
            "何が変わるかは --dry-run で確認できる。"
            "--create を渡したときだけ新しい DB を作る。"
        ),
    )
    ns.add_argument(
        "--create",
        metavar="PARENT_PAGE_ID",
        default=None,
        help="新しい DB を作る。親ページの ID（Notion のページ URL の末尾 32 桁）",
    )
    ns.add_argument("--title", default="imoTech Drafts", help="新規作成時の DB 名")
    ns.add_argument(
        "--dry-run", action="store_true", help="変更せず、送るボディと差分を表示するだけ"
    )
    return p


def main(argv: list[str] | None = None) -> int:
    settings = load_settings()
    args = build_parser(settings).parse_args(argv)
    handlers = {
        "collect": cmd_collect,
        "compose": cmd_compose,
        "stats": cmd_stats,
        "status": cmd_status,
        "publish": cmd_publish,
        "notion-sync": cmd_notion_sync,
        "notion-setup": cmd_notion_setup,
    }
    return handlers[args.command](settings, args)


if __name__ == "__main__":
    raise SystemExit(main())

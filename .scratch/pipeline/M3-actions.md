# M3: GitHub Actions による定時自動実行

ローカルで通ったパイプラインを cron で毎日回す。シークレットを Actions に移し、失敗を検知できる状態にする。

**Status:** 完了（完了条件 24 件のうち 23 件を実測で充足。残り 1 件は 60 日待たないと実測できないもので、論拠は末尾に記録）
**Blocked by:** M2（Notion 投入が通ること）

## 完了条件

### CI
- [x] `.github/workflows/ci.yml` を作り、`push` / `pull_request` で `ruff check` と `pytest` を実行した
- [x] `astral-sh/setup-uv` を使い、`uv sync --frozen` でロックファイル通りに入れた
- [x] `timeout-minutes: 10` を設定した
- [x] CI が green になった

### シークレット
- [x] GitHub の Settings → Secrets and variables → Actions に `GEMINI_API_KEY` / `NOTION_TOKEN` / `NOTION_DATABASE_ID` を登録した
- [x] `.env.example` に 3 つのキー名だけ（値は空で）書き、commit した
- [x] `.env` が `.gitignore` に入っていることを再確認した（public リポジトリなので漏洩は即座に公開になる）

### daily.yml
- [x] `.github/workflows/daily.yml` を作り、`schedule: - cron: "17 21 * * *"`（= 06:17 JST）と `workflow_dispatch` を設定した
- [x] **毎正時を避けた**ことを確認した（公式に「High load times include the start of every hour」「some queued jobs may be dropped」と明記されている）
- [x] `permissions: { contents: write, issues: write }` を宣言した
      （`actions: read` も追加した。失敗したステップ名を `gh run view --json jobs` で読むため）
- [x] `concurrency: { group: daily, cancel-in-progress: false }` を設定した
- [x] `timeout-minutes: 20` を設定した
- [x] `collect` → `compose` の順に実行するステップを書いた
- [x] `data/candidates.jsonl` の変更を commit し、`git pull --rebase origin main` してから push するステップを書いた
      （**`site/src/content/articles/` も commit 対象にした。** `compose` が Markdown も書き出すので、
      残しておかないと次回実行の `git pull --rebase` が未コミット変更で止まる。imo 未記入の記事は
      サイト側のゲートが公開から除外するため、commit しても公開はされない）
      （`origin main` ではなく `origin "$GITHUB_REF_NAME"` にした。schedule / dispatch では既定ブランチに解決される。
      push が弾かれたときに 3 回まで取り込み直す）
- [x] commit メッセージを `chore: update candidates (YYYY-MM-DD)` の形にした
- [x] 変更が無いときに commit を試みて落ちないようにした
      （`git add` 後に `git diff --cached --quiet` で判定して `exit 0`。`git diff --quiet` だと
      新規ファイル（記事 Markdown）を取りこぼすため、条件の文言より `--cached` が正確）

### 失敗の検知
- [x] `if: failure()` のステップで `gh issue create --label pipeline-failure` を実行した
      （**`if: ${{ failure() || cancelled() }}` にした。** `failure()` は timeout（`timeout-minutes` 到達）や
      手動キャンセルでは真にならず、想定原因に timeout を挙げておきながらその timeout では
      通知されない状態だった。`cancelled()` は「ワークフローがキャンセルされたら true」
      — https://docs.github.com/en/actions/reference/workflows-and-actions/expressions）
      （起票処理は `.github/actions/notify-failure`（composite action）に切り出した。M4 の `publish.yml` からも使う）
- [x] **同じラベルの open issue が既にあればコメント追記**して乱立を防ぐ実装にした
      （`gh issue list --label pipeline-failure --state open --json number` で判定）
- [x] Issue 本文に、実行 URL・失敗したステップ・想定される原因を含めた
      （実測で、失敗したステップ名が正しく入ることも確認した。`gh run view --json jobs` は
      進行中の run でも完了済みステップの `conclusion` を返す。
      想定原因は**運用者がそのまま実行できる手順**に書き換えた — 元の案は
      「`IMOTECH_MAX_DRAFTS_PER_RUN` を下げる」とだけ書いており、その env が
      `daily.yml` に無いため指示どおり `.env` を直しても Actions には効かなかった。
      HN の 5xx は原因一覧から落とした（それ自体では失敗にならないため、
      README の「記事が出ない日」側に移した））
- [x] 意図的に失敗させて Issue が立つことを確認した
      （**手段を変えた。** Secrets を不正な値に書き換える方法は取らず、検証専用の一時ワークフロー
      `verify-failure-notice.yml` から `GEMINI_API_KEY` を空で渡して `compose` を非 0 で終わらせた。
      Secrets に触らないので本番の `daily.yml` に影響しない。確認後にワークフローは削除済み）
- [x] 2 回目の失敗でコメントが追記され、Issue が増えないことを確認した

### 通し
- [x] `workflow_dispatch` で手動実行し、Notion に下書きが入り `candidates.jsonl` が commit された
- [x] 翌日、cron で自動実行されたことを Actions の履歴で確認した
      （`schedule success 2026-09-22T23:35:50Z`。commit は `c90bc6d chore: update candidates (2026-09-23)`。
      **ただし予定は 21:17 UTC で、実行は 23:35 UTC＝約 2 時間 18 分遅れた。**
      公式の "The `schedule` event can be delayed during periods of high loads" の実例で、
      `publish.yml` で観測した drop と合わせて、**cron の時刻は当てにできない**ことが裏づけられた。
      この設計では実害が無い — 状態を時刻ではなく `state` で持ち、`MAX_AGE_HOURS=96` の猶予がある）
- [ ] 自動実行の commit があることで、**public repo の schedule が 60 日無活動で自動停止する条件に当たらない**ことを確認した
      **未達（60 日待たないと実測できない）。** 論拠は揃っている — 公式が停止条件を
      "no repository activity has occurred in 60 days" と定めており
      ([events-that-trigger-workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows))、
      `daily.yml` の自動 commit が実在する（`977d21e` / `72ad6dc`、いずれも `github-actions[bot]` 名義）。
      commit が activity に数えられるかの明文は見つからなかったため、**推測を含む**

## 見つけたときの状況

public リポジトリは標準ランナーが無料（"GitHub Actions usage is free for ... public repositories that use standard GitHub-hosted runners"）。
private だと GitHub Free で月 2,000 分の枠を消費するため、M0 で public を選んでいる。

**schedule は保証されない**。公式に "The `schedule` event can be delayed during periods of high loads... If the load is sufficiently high enough, some queued jobs may be dropped." とある。
これに対しては cron の時刻調整では対処できないので、状態を時刻ではなく `state` / `Status` で持ち、1 回飛んでも次回が拾う設計にしている。
`MAX_AGE_HOURS = 96` があるため 3 回連続で飛んでも取りこぼさない。

**失敗通知はメールに依存しない**。公式の通知は「自分がトリガーした実行」が対象で、schedule はワークフロー作成者に飛び、
cron を編集すると通知先が移る。Issue 起票を一次の通知手段にしている。

`CLOUDFLARE_API_TOKEN` は登録しない。M4 で Workers Builds の Git 連携を使うため、Actions からデプロイを叩かない。

## 着手できる条件

M2 が完了し、ローカルの `uv run imotech compose` で Notion に下書きが入っている。

---

## 実測の記録（2026-09-22）

### リポジトリと Secrets

```
$ gh repo create imoTech --public --source=. --remote=origin --push
https://github.com/takiguchi-yu/imoTech
$ gh secret list
GEMINI_API_KEY      2026-09-22T02:40:08Z
NOTION_DATABASE_ID  2026-09-22T02:40:10Z
NOTION_TOKEN        2026-09-22T02:40:09Z
```

Actions のログで `GEMINI_API_KEY: ***` とマスクされることを確認した。

### CI

`35681016578` で green（`パイプライン` / `サイト` の両ジョブ success）。

**2 回落ちてから green になった。** どちらも M3 の変更とは無関係の既存の不具合で、
初回 push まで露見していなかった。

1. `npm test` が `ERR_UNKNOWN_FILE_EXTENSION: Unknown file extension ".ts"` で失敗。
   `node --test src/**/*.test.ts` は型ストリッピングを必要とするが、これがデフォルト有効に
   なったのは **v22.18.0 / v23.6.0**（[nodejs.org/api/typescript.html](https://nodejs.org/api/typescript.html)）。
   `engines` が `>=22.12.0` を宣言していたのが実態と合っていなかったので、下限を 22.18.0 に上げ、
   `ci.yml` と README 2 つを追随させた。ローカルは v24.12.0 なので通っていた
2. `astro check` が `SITE_URL が未設定です` で失敗。`SITE_URL` をビルドステップの `env` にだけ
   渡していたが、`astro.config.mjs` を読むのは `check` と `build` の両方。ジョブレベルの `env` に移した

### 失敗通知（完了条件 20 / 21）

| 回 | run | 結果 |
|---|---|---|
| 1 | `35682805928` | Issue **#1** が `pipeline-failure` ラベルで起票された |
| 2 | `35682860008` | Issue は **1 本のまま**、コメントが 1 件追記された |

Issue #1 の本文に入っていたもの: 実行 URL / 失敗したステップ名（`下書きを生成する（キーを渡さないので非 0 で終わる）`）/
トリガーと試行回数 / 発生時刻 / 想定される原因 / `gh run view <run_id> --log-failed`。
確認後、Issue #1 は close し、検証用ワークフローは削除した（`ee69813`）。

### 通し（完了条件 22）

`35682922767` で success。

```
閾値 points>=100 かつ comments>=30 → 選出 5 件 / 打ち切り 0 件
まとめ: 選出 5 / 記事化 5 / 本文取得できず 0 / 生成失敗 0 / 内容不足 0 / Notion 投入 5 成功 0 失敗
```

commit は `72ad6dc chore: update candidates (2026-09-22)`（`github-actions[bot]` 名義、JST 日付）。
`data/candidates.jsonl` と記事 Markdown 5 件が入った。

**Markdown を commit しても公開されない**ことを成果物で確認した。

```
$ uv run imotech status
全 7 件: 公開中 0 / imo 未記入 7
$ cd site && SITE_URL=https://example.invalid npm run build && node scripts/check-unpublished.mjs
記事 7 件（うち imo 未記入 7 件）。出力への漏れはありません。
```

モデルフォールバックも実際に働いた（`gemini-3.5-flash attempts=10` / `gemini-3.6-flash attempts=9`
＝ 429 を受けて指数バックオフで粘った記録）。

### この チケットで決めたこと

- **`compose` の終了コードを実装した。** Gemini の全滅も Notion の 403 も捕まえて続行する
  実装だったため、**全滅しても exit 0** で終わり `if: failure()` が反応しなかった。
  完了条件が例示する「不正な `NOTION_DATABASE_ID` で Issue が立つ」がそのままでは成立しないので、
  完了条件を緩めるのではなく実装を直した。境目は「記事化が 0 件か」「Notion が使えたか」
- **記事 Markdown も commit 対象にした**（チケットは `candidates.jsonl` だけを書いていた）。
  `compose` が Markdown も書き出すので、残さないと次回の `git pull --rebase` が
  未コミット変更で止まる
- **失敗通知を composite action に切り出した。** M4 の `publish.yml` が同じものを使うため
- **`IMOTECH_*` を env で渡す口は開けなかった。** `${{ vars.X || '5' }}` で渡せるが、既定値を
  `config.py` と `daily.yml` の 2 箇所に持つことになる。代わりに Issue 本文の指示を
  「compose ステップの env に足す」という実行可能な形にした

### 申し送り

- **M4 に制約を追記した** — `publish.yml` から `data/candidates.jsonl` を書かないこと。
  `store.save` は JSONL を全行書き直すため、`daily.yml` と同時に走ると rebase が
  行単位で解決できず競合する
- **`daily.yml` と `publish.yml` がほぼ同時に失敗すると Issue が 2 本立つ。** GitHub API に
  「無ければ作る」の原子操作が無いため避けられない。実害は Issue 2 本なので許容した（`docs/DESIGN.md` 5.5 に記録）
- **`GITHUB_TOKEN` の push は CI を起動しない**ので、自動 commit に `ci.yml` が当たらない。
  公開の可否はサイト側のゲートが決めるため漏洩には至らない（同 5.5 に記録）
- `.serena/` が未追跡で残っている。`project.yml` は versioned 想定・秘密情報なしなので触っていない

# M3: GitHub Actions による定時自動実行

ローカルで通ったパイプラインを cron で毎日回す。シークレットを Actions に移し、失敗を検知できる状態にする。

**Status:** 未着手
**Blocked by:** M2（Notion 投入が通ること）

## 完了条件

### CI
- [ ] `.github/workflows/ci.yml` を作り、`push` / `pull_request` で `ruff check` と `pytest` を実行した
- [ ] `astral-sh/setup-uv` を使い、`uv sync --frozen` でロックファイル通りに入れた
- [ ] `timeout-minutes: 10` を設定した
- [ ] CI が green になった

### シークレット
- [ ] GitHub の Settings → Secrets and variables → Actions に `GEMINI_API_KEY` / `NOTION_TOKEN` / `NOTION_DATABASE_ID` を登録した
- [ ] `.env.example` に 3 つのキー名だけ（値は空で）書き、commit した
- [ ] `.env` が `.gitignore` に入っていることを再確認した（public リポジトリなので漏洩は即座に公開になる）

### daily.yml
- [ ] `.github/workflows/daily.yml` を作り、`schedule: - cron: "17 21 * * *"`（= 06:17 JST）と `workflow_dispatch` を設定した
- [ ] **毎正時を避けた**ことを確認した（公式に「High load times include the start of every hour」「some queued jobs may be dropped」と明記されている）
- [ ] `permissions: { contents: write, issues: write }` を宣言した
- [ ] `concurrency: { group: daily, cancel-in-progress: false }` を設定した
- [ ] `timeout-minutes: 20` を設定した
- [ ] `collect` → `compose` の順に実行するステップを書いた
- [ ] `data/candidates.jsonl` の変更を commit し、`git pull --rebase origin main` してから push するステップを書いた
- [ ] commit メッセージを `chore: update candidates (YYYY-MM-DD)` の形にした
- [ ] 変更が無いときに commit を試みて落ちないようにした（`git diff --quiet || git commit ...`）

### 失敗の検知
- [ ] `if: failure()` のステップで `gh issue create --label pipeline-failure` を実行した
- [ ] **同じラベルの open issue が既にあればコメント追記**して乱立を防ぐ実装にした
      （`gh issue list --label pipeline-failure --state open --json number` で判定）
- [ ] Issue 本文に、実行 URL・失敗したステップ・想定される原因（Gemini の 429 / Notion の 403 block_limit / HN の 5xx）を含めた
- [ ] 意図的に失敗させて（不正な `NOTION_DATABASE_ID` など）Issue が立つことを確認した
- [ ] 2 回目の失敗でコメントが追記され、Issue が増えないことを確認した

### 通し
- [ ] `workflow_dispatch` で手動実行し、Notion に下書きが入り `candidates.jsonl` が commit された
- [ ] 翌日、cron で自動実行されたことを Actions の履歴で確認した
- [ ] 自動実行の commit があることで、**public repo の schedule が 60 日無活動で自動停止する条件に当たらない**ことを確認した

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

# M4: 承認の検知 → Markdown コミット → サイト公開

Notion で `Approved` にした記事を検知して Markdown に変換し、リポジトリに commit する。
Workers Builds の Git 連携がそれを検知してサイトをビルド・公開する。

**Status:** 未着手
**Blocked by:** M3（Actions が動くこと）、M0（ドメインまたは `*.workers.dev` の決定）

## 完了条件

### Astro サイトの骨組み
- [ ] `site/` に `npm create astro@latest` でプロジェクトを作った（最小構成、TypeScript）
- [ ] `site/src/content.config.ts` に `articles` コレクションを定義し、[docs/DESIGN.md 2.5](../../docs/DESIGN.md) のフロントマターを zod スキーマで型付けした
- [ ] `site/src/content/articles/` に手書きのサンプル記事を 1 本置き、`npm run build` が通った
- [ ] `site/src/pages/index.astro`（記事一覧、公開日の降順）を作った
- [ ] `site/src/pages/articles/[...slug].astro`（記事詳細）を作った
- [ ] `site/src/pages/tags/[tag].astro`（タグ別一覧）を作った
- [ ] `@astrojs/rss` を入れ、`site/src/pages/rss.xml.ts` を作った
- [ ] `@astrojs/sitemap` を入れ、`sitemap-index.xml` が生成されることを確認した
- [ ] スタイリングは最小限に留めた（デザインは後回しと決めている。読める状態であればよい）

### 開示と法務ページ
- [ ] `site/src/pages/about.astro` を作り、制作プロセスを書いた
      （何を機械がやり、何を人間がやるか。Google の自己点検 "Is the use of automation, including AI-generation, self-evident to visitors through disclosures or in other ways?" に答える内容にする）
- [ ] 記事詳細のレイアウト末尾に、AI 生成の固定文を入れた
      （「本記事の要旨と論調の整理は Gemini による生成で、imo は運営者が執筆しています」+ /about へのリンク）
- [ ] `site/src/pages/privacy.astro` を作った（AdSense 申請時に見られる）
- [ ] 運営者情報を `/about` に含めた

### Markdown 生成
- [ ] `src/imotech/render.py` に `to_markdown(draft) -> str` を実装した
- [ ] `render.py` が Notion の API 形式を知らず、`models` の型だけを受け取ることを確認した（依存の向き）
- [ ] フロントマターに `title` / `publishedAt` / `sourceUrl` / `sourceTitle` / `hnUrl` / `hatenaUrl` / `hnScore` / `hnComments` / `tags` / `model` / `generatedAt` を出した
- [ ] YAML のエスケープを確認した（タイトルに `"` や `:` が入っても壊れない）
- [ ] `tests/test_render.py` で、引用符とコロンを含むタイトルでフロントマターが壊れないことを確認した

### 承認の検知
- [ ] `src/imotech/notion.py` に `fetch_approved()` を実装し、フィルタを `Status == Approved` **かつ** `imo is_not_empty` にした
- [ ] `last_edited_time` を使っていないことを確認した（ページ単位でしか取れず、ワークフローが飛ぶと取りこぼすため）
- [ ] ページ本文のブロックを取得して要旨・論調を復元する実装にした（ページネーションに対応する）
- [ ] commit 後に `Status` を `Published` に、`Published At` を現在時刻に更新する実装にした
- [ ] **`imo` が空のまま Approved にされたページは公開されない**ことを、実際に空で Approved にして確認した

### publish.yml
- [ ] `.github/workflows/publish.yml` を作り、`schedule: - cron: "23 * * * *"` と `workflow_dispatch` を設定した
- [ ] `permissions: { contents: write, issues: write }` / `concurrency: { group: publish }` / `timeout-minutes: 10` を設定した
- [ ] `site/src/content/articles/<slug>.md` を書き、`git pull --rebase` してから push するステップを書いた
- [ ] 同じ slug のファイルが既にあるとき、上書きせずスキップして Notion の Status だけ更新する実装にした
- [ ] 承認が 0 件のとき、commit を試みずに正常終了することを確認した
- [ ] 失敗時の Issue 起票を `daily.yml` と同じ形で入れた

### Cloudflare Workers + Static Assets
- [ ] `site/wrangler.jsonc` に `assets` の設定を書いた
- [ ] Cloudflare ダッシュボードで Workers プロジェクトを作り、**GitHub リポジトリと連携**した
- [ ] ビルドコマンドを `npm run build`、出力ディレクトリを `dist` に設定した
- [ ] ルートディレクトリを `site/` に設定した（モノレポ構成のため）
- [ ] `main` への push で自動ビルドが走ることを確認した
- [ ] **Deploy Hook が不要であることを確認した**（Git 連携で自動ビルドされるなら、Actions から叩く必要はない。走らない場合のみ Deploy Hook を追加し、URL を Secrets に置く）
- [ ] 独自ドメインを設定した（M0 で取得済みの場合）

### 通し
- [ ] Notion で下書き 1 件に `imo` を書き、`Status` を `Approved` にした
- [ ] `publish.yml` を手動実行し、`site/src/content/articles/` に Markdown が commit された
- [ ] Notion の該当ページが `Published` になり、`Published At` が入った
- [ ] Workers のビルドが走り、**公開 URL で記事が読めた**
- [ ] `/rss.xml` と `/sitemap-index.xml` に新しい記事が含まれている
- [ ] 記事末尾に AI 生成の開示が表示されている
- [ ] cron（毎時 23 分）で自動実行されたことを Actions の履歴で確認した

## 見つけたときの状況

Cloudflare 公式が Pages のドキュメントトップに「Workers supports most Pages use cases and offers a broader feature set...
**Start new projects with Workers.**」と明記しているため、Pages ではなく Workers + Static Assets を選んでいる（Pages の非推奨・EOL 宣言は出ていない）。
Astro のドキュメント・事例は Pages 前提のものが多いので、詰まったら Pages への切り替えも選択肢に残す。

Cloudflare の Free プランは**月 500 ビルド・同時 1 ビルド**。毎時ポーリングしても、実際にビルドが走るのは commit したときだけなので、
1 日 5 記事公開でも月 150 ビルド程度に収まる。ただし `daily.yml` の `candidates.jsonl` commit でもビルドが走る点に注意
（`site/` 配下しか見ないようビルド設定でパスフィルタをかけられるなら、かける）。

静的アセットへのリクエストは Free でも無制限（"requests to static assets are free and unlimited"）。
ただし Pages Functions / Workers のサーバーサイドコードを足すと日次 100,000 リクエストの枠が出現するため、**完全な SSG を維持する**。

## 着手できる条件

M3 が完了し、`daily.yml` が cron で動いて Notion に下書きが溜まっている。

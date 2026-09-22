# M4: 承認の検知 → Markdown コミット → サイト公開

Notion で `Approved` にした記事を検知して Markdown に変換し、リポジトリに commit する。
Workers Builds の Git 連携がそれを検知してサイトをビルド・公開する。

**Status:** コードは完成（`publish.yml` / `site/wrangler.jsonc` / 承認検知）。**Cloudflare のプロジェクト作成と通し確認が残り**（いずれも人間のダッシュボード操作か Notion 操作が必要）
**Blocked by:** M3（Actions が動くこと）、M0（ドメインまたは `*.workers.dev` の決定）

## 完了条件

### Astro サイトの骨組み
- [x] `site/` に `npm create astro@latest` でプロジェクトを作った（最小構成、TypeScript）
- [x] `site/src/content.config.ts` に `articles` コレクションを定義し、[docs/DESIGN.md 2.5](../../docs/DESIGN.md) のフロントマターを zod スキーマで型付けした
- [x] `site/src/content/articles/` に手書きのサンプル記事を 1 本置き、`npm run build` が通った
- [x] `site/src/pages/index.astro`（記事一覧、公開日の降順）を作った
- [x] `site/src/pages/articles/[...slug].astro`（記事詳細）を作った
- [x] `site/src/pages/tags/[tag].astro`（タグ別一覧）を作った
- [x] `@astrojs/rss` を入れ、`site/src/pages/rss.xml.ts` を作った
- [x] `@astrojs/sitemap` を入れ、`sitemap-index.xml` が生成されることを確認した
- [x] スタイリングは最小限に留めた（デザインは後回しと決めている。読める状態であればよい）

### 開示と法務ページ
- [x] `site/src/pages/about.astro` を作り、制作プロセスを書いた
      （何を機械がやり、何を人間がやるか。Google の自己点検 "Is the use of automation, including AI-generation, self-evident to visitors through disclosures or in other ways?" に答える内容にする）
- [x] 記事詳細のレイアウト末尾に、AI 生成の固定文を入れた
      （「本記事の要旨と論調の整理は Gemini による生成で、imo は運営者が執筆しています」+ /about へのリンク）
- [x] `site/src/pages/privacy.astro` を作った（AdSense 申請時に見られる）
- [x] 運営者情報を `/about` に含めた

### Markdown 生成
- [x] `src/imotech/render.py` に `to_markdown(draft) -> str` を実装した
- [x] `render.py` が Notion の API 形式を知らず、`models` の型だけを受け取ることを確認した（依存の向き）
- [x] フロントマターに `title` / `publishedAt` / `sourceUrl` / `sourceTitle` / `hnUrl` / `hatenaUrl` / `hnScore` / `hnComments` / `tags` / `model` / `generatedAt` を出した
- [x] YAML のエスケープを確認した（タイトルに `"` や `:` が入っても壊れない）
- [x] `tests/test_render.py` で、引用符とコロンを含むタイトルでフロントマターが壊れないことを確認した

### 承認の検知
- [x] `src/imotech/notion.py` に `fetch_approved()` を実装し、フィルタを `Status == Approved` **かつ** `imo is_not_empty` にした
- [x] `last_edited_time` を使っていないことを確認した（ページ単位でしか取れず、ワークフローが飛ぶと取りこぼすため）
- [x] ~~ページ本文のブロックを取得して要旨・論調を復元する実装にした（ページネーションに対応する）~~
      → **不要。M2 で「Notion は記事本文の正ではない」と決めた**（`.scratch/pipeline/M2-notion.md`
      の「決めたこと」、`docs/DESIGN.md` 3.0b）。本文は `compose` が書いた Markdown が正で、
      Notion からは人が書いた `imo` だけを取り出す。Notion のブロックを読む実装は存在せず、
      設計上も作らない（`grep -rn "/blocks/" src/imotech/notion.py` は書き込み 1 件だけ）
- [x] commit 後に `Status` を `Published` に、`Published At` を現在時刻に更新する実装にした
      （**2 段構成にした。** 1 回目の実行で Markdown に `imo` を差し込むだけにして Notion は
      触らず、commit と push が成功してから 2 回目を実行し、その回が `mark_published` を呼ぶ。
      1 回目で進めると、push が失敗したときに「Notion は Published なのに Markdown は未コミット」
      が残り、`fetch_approved` は Approved しか引かないのでその記事は自動では永久に公開されない）
- [ ] **`imo` が空のまま Approved にされたページは公開されない**ことを、実際に空で Approved にして確認した

### publish.yml
- [x] `.github/workflows/publish.yml` を作り、`schedule: - cron: "23 * * * *"` と `workflow_dispatch` を設定した
- [x] `permissions: { contents: write, issues: write }` / `concurrency: { group: publish }` / `timeout-minutes: 10` を設定した
- [x] `git pull --rebase` してから push するステップを書いた
      （**`<slug>.md` を「書く」のは `compose` の仕事**で、`publish` は既存ファイルの `## imo` を
      書き換えるだけ。M2 の決定どおり。push が弾かれたときに 3 回まで取り込み直す）
- [x] 同じ slug のファイルが既にあるとき、上書きせずスキップして Notion の Status だけ更新する実装にした
      （実装の対応物は「**ローカルに手書きの `imo` があれば Notion の値で上書きせず、Status だけ進める**」。
      publish は新規ファイルを作らない設計なので、条件が想定していた「上書き」は起きない）
- [x] **プレースホルダのコメント行が残っているページは Published に進めない**
      （レビューで見つけた穴。消し忘れたまま所感を書き足した状態ではサイト側のゲートが記事を
      公開から外すのに、`already` として成功に数えて Published にしていた。`fetch_approved` は
      Approved しか引かないので、公開もされないまま二度と拾われない。Approved のまま残す）
- [x] 承認が 0 件のとき、commit を試みずに正常終了することを確認した
- [x] 失敗時の Issue 起票を `.github/actions/notify-failure` で入れた（`daily.yml` と同じ composite action。`causes` だけ publish 用に差し替える）
- [x] `if: ${{ failure() || cancelled() }}` にした（timeout とキャンセルでは `failure()` が真にならない）
- [x] **`publish.yml` から `data/candidates.jsonl` を書かない**ことを確認した
      （`store.save` は JSONL を全行書き直すため、`daily.yml` と同時に走ると rebase が
      行単位で解決できず競合する。publish が触るのは記事 Markdown と Notion だけに留める）

### Cloudflare Workers + Static Assets
- [x] `site/wrangler.jsonc` に `assets` の設定を書いた
- [ ] Cloudflare ダッシュボードで Workers プロジェクトを作り、**GitHub リポジトリと連携**した
- [ ] ビルドコマンドを `npm run build` に設定した
      （**出力ディレクトリの設定項目は Workers Builds に無い。** `site/wrangler.jsonc` の
      `assets.directory: "./dist"` が担う。設定できるのは Git アカウント・リポジトリ・ブランチ・
      ビルドコマンド・デプロイコマンド・ルートディレクトリ・ビルド変数だけ —
      [configuration](https://developers.cloudflare.com/workers/ci-cd/builds/configuration/)）
      **Worker 名は `imotech` にする必要がある**（公式が "The Worker name in the Cloudflare
      dashboard must match the `name` in the Wrangler configuration file in the specified
      root directory, or the build will fail." と明記）
- [ ] ルートディレクトリを `site/` に設定した（モノレポ構成のため）
- [ ] `main` への push で自動ビルドが走ることを確認した
- [ ] **Deploy Hook が不要であることを確認した**（Git 連携で自動ビルドされるなら、Actions から叩く必要はない。走らない場合のみ Deploy Hook を追加し、URL を Secrets に置く）
- [ ] ~~独自ドメインを設定した（M0 で取得済みの場合）~~
      → **該当しない。`*.workers.dev` で進めると決めた**（M0 の「ドメインを後回しにする場合は
      `*.workers.dev` で進める判断を README に 1 行残す」に従い、README の「公開」節に記載）。
      収益化（ads.txt はルートドメイン起点でクロールされる）に必要になるのは M5

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

---

## ローカル通しまで完了（2026-09-22）

Notion を飛ばし、`compose` が Markdown を直接書く経路で、収集からサイト表示までを通した。
M2 が入ったら「Notion の Approved を検知して書く」に差し替える。公開判定の考え方は同じ。

### 実測

```
npm run build（記事 2 件、うち imo 記入済み 1 件）
  → 9 ページ生成。imo 未記入の記事はページも RSS も sitemap も出ない
  → 未記入記事のタグ（google/ai/agents/kubernetes/infrastructure）も dist に一切出ない
rss.xml     → item 1 件、language ja
sitemap-0.xml → 9 URL、すべて公開済みのもの
localhost:4321 → 一覧・記事詳細とも描画を目視確認
uv run pytest → 147 passed（test_render.py 24 件を追加）
```

### 決めたこと

- **公開の引き金はプレースホルダの消去**。`draft: true` のフラグ方式だと立て忘れで
  未完成の記事が出るが、この方式なら「書かないかぎり出ない」。
- **`IMO_PLACEHOLDER` は Python とサイトの両方に定義がある**。ずれると事故になるので
  `tests/test_render.py::test_サイト側の定数と一致している` で突合している。
- **`write_article` は既存ファイルを上書きしない。** 人が imo を書き込んでいる可能性があり、
  上書きするとその手作業が消える。重複排除の 3 段目も兼ねる。
- **`site` の URL は `SITE_URL` 環境変数で上書きでき、未設定なら localhost。**
  ドメインが未確定でも RSS と sitemap が壊れないようにするため。

### 残り（外部アカウントが要る分）

- Notion の Approved 検知（M2 が入ってから）
- `publish.yml`
- Cloudflare Workers のプロジェクト作成と Git 連携、`wrangler.jsonc`
- 独自ドメインの設定

## レビューと修正（2026-09-22）

3 視点を並列で回し、**Blocker 4 件 / Major 13 件 / Minor 15 件**。Blocker と Major はすべて修正。

### Blocker

| 指摘 | 修正 |
|---|---|
| **公開ゲートが fail-open だった** — 本文が空・`<!--imo:`（空白なし）・`## imo` の中身なし・`body` が undefined、のいずれでも公開された（実測） | 許可リスト方式に反転。`## imo` の節を切り出し、プレースホルダでも HTML コメントでもない文字が 1 文字以上あるときだけ公開する。`body` が取れなければ非公開 |
| **タグに `/` が入るとビルド全体が TypeError で落ちる**（実測）。`ci/cd` `tcp/ip` は「英小文字の技術タグ」の条件を満たすので必ず踏む | `llm.py` の `normalize_tags()` で `[a-z0-9-]` に正規化し、重複と空を落とす。`c++` は慣例どおり `cpp` |
| **機械が書いた imo の記事が公開状態でステージされていた** | プレースホルダに戻した。`/about` に「機械だけで記事が世に出ることはありません」と書いている以上、自分で反例を作ってはいけない |
| **README のリード文が「Notion で imo を書く」のままで実装と逆を向いていた** | 現行フロー（Markdown の `## imo` に書くと公開される、Notion は M2 の将来計画）に書き替え |

### Major（抜粋）

- **`_yaml_str` が制御文字を素通しし、1 文字でサイトのビルド全体が死ぬ**（実測）。テストが自前の文字列分割で、実 YAML パーサを一度も通していなかったので見逃していた → 制御文字を除去し、`pyyaml` での往復検証テストを 15 件追加
- **プレースホルダを部分的に消すと運営の内部指示が記事本文として公開される**（実測）→ 消しにくい固定句 `このコメント行を消すまで` でも判定する
- **`created=False` のとき候補が pending のまま残り、毎回 Gemini を呼んで結果を捨てる** → 状態を進める。さらに `write_article` が slug 衝突時に別記事を捨てず `<slug>-<hash>.md` で保存する。書き戻しも 1 件ごとにしてクラッシュ窓を閉じた
- **CI がサイトを一切ビルドせず、ゲートの回帰を検知できない** → `site` ジョブを追加（`npm ci` / `npm test` / `astro check` / `npm run build` / **未記入記事が dist に漏れていないことを成果物で検査**）
- **`SITE_URL` 未設定でもビルドが成功し、localhost の URL が RSS と sitemap に焼き込まれる** → CI では落とす。判定に `NODE_ENV` は使わない（`astro build` が自ら production を立てるためローカルまで落ちる）
- **サイト側にテストが 1 件も無い** → `node --test` で 17 件。Node 24 は `.ts` をそのまま実行できるので依存の追加ゼロ
- **「imo を書いたのに出ない」を切り分ける手段が無い** → `uv run imotech status` を追加し、`has_imo`（それまで未使用だった）を実際に使う
- **`/about` の連絡先リンクが 404**（リポジトリ未作成）→「準備中」と明記
- **`compose` が何も成功しなかった実行で無言に終わる** → 必ずサマリを出す。既存スキップ時は「生成結果を破棄した」ことも明示
- **README のコピペで git 管理下の候補ストアが汚れる** → 「まず試す」用のブロックを `IMOTECH_CANDIDATES_PATH` 付きにし、運用用と分けた
- **前提に Node.js が無い / 読者向けページに内部手順が出る / 記事から一覧へ戻れない** → いずれも修正

### 見送ったもの

| 指摘 | 理由 |
|---|---|
| カスタム 404 ページ | デザインは後回しの方針。Astro 既定で機能上の支障はない |
| `publishedAt` を imo 記入日にする | 記入日を機械が知る手段が無い。docstring の「人が直してよい」を README にも書くに留めた |
| 末尾スラッシュの統一 | Astro の既定（`trailingSlash: "ignore"`）でどちらも解決する。設定を触ると既存 URL に影響する |

### 検証（修正後）

```
uv run ruff check . / format --check     → All checks passed / 39 files formatted
uv run pytest -q                          → 170 passed（+23）
cd site && npm test                       → 17 passed（公開ゲート）
cd site && npm run check                  → 0 errors / 0 warnings
cd site && npm run build                  → 3 ページ（記事 2 件とも imo 未記入のため）
cd site && CI=1 npm run build             → SITE_URL 未設定で非ゼロ終了
スクラッチで imo を 1 件記入してビルド        → 9 ページ / RSS 1 件 / sitemap 9 URL / タグ 5 件
                                             未記入の記事は dist に一切出ない
```

---

## 実測の記録（2026-09-22）

### コード側（完了したもの）

```
$ uv run ruff format --check . && uv run ruff check . && uv run pytest -q
307 passed
$ cd site && npm test && SITE_URL=https://example.invalid npm run build
17 pass / 3 page(s) built
$ node scripts/check-unpublished.mjs
記事 7 件（うち imo 未記入 7 件）。出力への漏れはありません。
$ WRANGLER_SEND_METRICS=false npx wrangler deploy --dry-run
✨ Read 10 files from the assets directory .../site/dist
$ uv run imotech publish --dry-run          # SSL_CERT_FILE を付けて実行
Notion で承認済み（imo 記入済み）: 0 件 → exit 0
```

CI は `35684...`（`d8d6874`）で green。

### レビューで見つけて直したもの

| 深刻度 | 内容 |
|---|---|
| Blocker | **完了条件は「commit 後に Status を Published に」と書いていたが、実装は commit 前に進めていた。** push が失敗すると「Notion は Published なのに Markdown は未コミット」が残り、`fetch_approved` は Approved しか引かないのでその記事は自動では永久に公開されない。2 段構成にした |
| Major | **プレースホルダのコメント行を消し忘れたまま所感を書き足した状態**で、公開されないのに Notion を Published に進めていた。Approved のまま残すようにした |
| Blocker | Notion を使わない運用に切り替えると `publish.yml` が毎時 終了コード 2 で落ち、失敗 Issue に毎時コメントが積む。`gh workflow disable publish.yml` を案内した |
| Major | **dist が空でも `wrangler deploy` は警告なく成功**し、公開サイトの全 URL が 404 になる（実測: 空の dist で `--dry-run` が終了コード 0）。CI で HTML の数と wrangler の設定を検証するようにした |
| Major | Cloudflare の手順に、アカウント作成と GitHub App の許可（手順 0）が無く、上から実行すると手順 1 で止まった |
| Major | 「サイトが更新されない」ときの切り分けが無かった（止まりうる 3 か所を順に切る節を追加） |
| Major | TLS の疎通確認の例が `publish` で、Notion 未設定だとネットワークに触る前に終わっていた。`collect` に変えた |

### 条件を改訂した 4 件

| 元の条件 | どうしたか | 理由 |
|---|---|---|
| ページ本文のブロックを取得して要旨・論調を復元する | **取り消し** | M2 で「Notion は記事本文の正ではない」と決めた。Notion のブロックを読む実装は無く、設計上も作らない |
| `<slug>.md` を書き、`git pull --rebase` してから push | 「書く」を落とした | `<slug>.md` を書くのは `compose` の仕事。`publish` は既存ファイルの `## imo` を書き換えるだけ |
| 同じ slug のファイルが既にあるとき上書きせずスキップして Status だけ更新 | 実装の対応物に読み替え | publish は新規ファイルを作らないので「上書き」は起きない。対応物は「ローカルに手書きの imo があれば Notion の値で上書きせず Status だけ進める」 |
| 出力ディレクトリを `dist` に設定した | 「設定項目が無い」と註記 | Workers Builds に出力ディレクトリの項目は無く、`wrangler.jsonc` の `assets.directory` が担う |

### 決めたこと

- **Notion を進めるのは commit/push の後**（2 段構成）。`publish.yml` は
  「publish → commit/push → publish」の順にステップを並べる。1 回目は Markdown に
  差し込むだけ、2 回目が `mark_published` を呼ぶ
- **`*.workers.dev` で進める。** 独自ドメインは M5（ads.txt がルートドメインを要求する）
- **`not_found_handling` は指定しない。** 404.html を持っていないため指定しても効かない。
  カスタム 404 を作るときに合わせて入れる
- **Workers Builds にパスフィルタは無い。** `candidates.jsonl` だけの commit でもビルドが走る。
  1 日 3 回の承認なら月 120 回で Free の 500 枠に収まる（毎時 1 件ずつ承認すると 750 回で超過）

### 申し送り

- **Cloudflare 側の失敗は Issue 経路に乗らない。** Actions が成功して commit も push された
  あとに Cloudflare のビルドが落ちると、`publish.yml` は正常終了し Issue も立たず、
  サイトが何日も古いままになる。気づく手段はダッシュボードだけ。
  中期的には Cloudflare の Build notification か、公開 URL の `/rss.xml` の最終更新を
  定期チェックするステップを足す
- **`SITE_URL` のガードが Workers Builds で効くかは未確認。** `site/astro.config.mjs` の判定は
  `!process.env.SITE_URL && process.env.CI` で、Cloudflare のビルド環境に `CI` があるかを
  確認できていない。無い場合は**ビルドが成功して localhost の URL が sitemap と RSS に
  焼き込まれる**。初回ビルドで `SITE_URL` を空にして落ちるかを 1 回見れば分かる
- **`not_found_handling` の既定挙動は未確認。** 公開後に `curl -i https://<url>/no-such-page` を
  1 回確認する
- **`compatibility_date` が当日（2026-09-22）で、サーバ側が受理するかは未確認。**
  `wrangler deploy --dry-run` は日付を検証しない（未来日付でも警告なく成功する — 実測）
- **`data_source_id` は Actions のログに素で出る。** secret 登録しているのは
  `NOTION_DATABASE_ID` で、そこから導出した `data_source_id` はマスク対象外。
  トークンが無ければ悪用できないので情報開示のみ。気にするなら
  `src/imotech/notion.py` の `request()` のエラー文からパスの ID をマスクする
- **「1 件は手書き imo でローカル優先、残り全部が skip」のとき終了コードは 0** になる。
  1 件は Notion が進むので完全な失敗ではないと判断した

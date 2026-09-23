# imoTech — サイト

[imoTech](../README.md) の静的サイト。Astro で `src/content/articles/` の Markdown から生成する。

記事の Markdown は `uv run imotech compose`（リポジトリのルートで実行）が生成する。
**手で書くのは `## imo` の節だけ。** それ以外は再生成で上書きされうるものとして扱う。

**前提**: Node.js 22.18 以上（`package.json` の `engines`）。`npm test` が `.ts` を直接 `node --test` に渡すので、型ストリッピングがデフォルト有効な版（v22.18.0 / v23.6.0 以降）が必要。

## 使い方

```bash
npm install
npm run dev      # http://localhost:4321
npm test         # 公開ゲートのテスト（Node 標準のテストランナー）
npm run check    # astro check（型）
npm run build    # dist/ に出力
npm run preview  # build 結果を確認
```

開発サーバーはバックグラウンドでも起動できる（`site/AGENTS.md` 参照）。

```bash
npx astro dev --background
npx astro dev status
npx astro dev stop
```

## imo を書かないと公開されない

`compose` が生成した Markdown の末尾には、こういうプレースホルダが入っている。

```markdown
## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->
```

このコメント行が残っているかぎり、その記事は**ページも RSS も sitemap も生成されない**。
判定は `src/lib/imo.ts` の `imoOf()` が行い、`npm test` で 17 件のケースを固定している。

判定は**許可リスト方式**にしてある。「未記入の証拠があれば隠す」ではなく
「記入の証拠があれば出す」。本文が読めない・見出しが無い・表記が違う、といったケースは
すべて非公開に倒れる。所感を書いていない記事が世に出るほうが取り返しがつかないため。

> **sitemap は `npm run build` でしか生成されない。** `npm run dev` では `/sitemap-index.xml` は 404 になる。

置き換えの目印は `src/content.config.ts` の `IMO_PLACEHOLDER` で、
Python 側（`src/imotech/render.py`）の同名定数と一致していなければならない。
ずれると「imo 未記入の記事が公開される」ので、`tests/test_render.py` で突合している。

## 構成

| パス | 役割 |
|---|---|
| `src/content.config.ts` | 記事コレクションのスキーマ |
| `src/lib/imo.ts` | **公開判定と定数の唯一の定義元**。`npm test` の対象 |
| `src/lib/articles.ts` | コレクションの取得・タグ集計・日付整形 |
| `src/lib/sources.ts` | ソースの表示名と注目度の呼び名（points / LGTM） |
| `src/lib/og.ts` | アイキャッチ（OG 画像）の**レイアウト**。描画はしない |
| `src/lib/og-render.ts` | アイキャッチの**描画**（Satori + Resvg、フォントの読み込み） |
| `src/layouts/Base.astro` | 共通レイアウトとスタイル。OGP と X のカードのタグもここ |
| `src/pages/index.astro` | 記事一覧 |
| `src/pages/articles/[...slug].astro` | 記事詳細。アイキャッチ・出典・AI 利用の開示を描く |
| `src/pages/og/[slug].png.ts` | 記事ごとのアイキャッチ（OG 画像）をビルド時に PNG で書き出す |
| `fonts/` | アイキャッチ用の日本語フォント（Noto Sans CJK JP Bold、OFL）。**ビルド時だけ使い、配らない**。出典は `fonts/README.md` |
| `scripts/check-unpublished.mjs` | imo 未記入の記事が出力（ページ・RSS・sitemap・**OG 画像**）に漏れていないか |
| `scripts/check-og.mjs` | 公開記事の OG 画像が 1200×630 で出ていて、og:image が絶対 URL で指しているか |
| `src/pages/tags/[tag].astro` | タグ別一覧 |
| `src/pages/rss.xml.ts` | RSS |
| `src/pages/about.astro` | 制作プロセスと AI 利用の開示 |
| `src/pages/privacy.astro` | プライバシーポリシー |

## ドメイン

未確定（リポジトリルートの `.scratch/pipeline/M0-setup.md` を参照）。
`astro.config.mjs` の `site` は `SITE_URL` 環境変数で上書きでき、未設定なら
`http://localhost:4321` になる。RSS と sitemap が絶対 URL を必要とするため。

```bash
SITE_URL=https://example.com npm run build
```

## アイキャッチ（OG 画像）

記事ごとに、**タイトルカードをビルド時に自動で描く**（サイト名 + 記事タイトル + ソース名と注目度）。
記事ページの見出しの直下に出し、同じ画像を `og:image` にも使う。

- **生成 AI の画像は使わない。** Gemini の画像生成は無料枠で使えない（https://ai.google.dev/gemini-api/docs/pricing ）
- **元記事の画像も使わない。** 他人の画像の無断転載になる
- 描くのは**公開済み（imo 記入済み）の記事だけ**。未公開記事の画像を作ると、画像のタイトルから中身が漏れる
- 1 枚あたり約 0.3 秒（1 枚目だけフォントの読み込みで約 0.6〜0.75 秒）。**公開記事の全件を毎回描き直す**ので、公開記事が 100 本なら約 30 秒、約 1,500 本で公開ワークフローの 10 分の制限に近づく（手当ては `../.scratch/pipeline/M12-og-cache.md`）

見た目を変えるときは `src/lib/og.ts`、フォントを差し替えるときは `fonts/README.md` を読む。

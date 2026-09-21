# imoTech — サイト

[imoTech](../README.md) の静的サイト。Astro で `src/content/articles/` の Markdown から生成する。

記事の Markdown は `uv run imotech compose`（リポジトリのルートで実行）が生成する。
**手で書くのは `## imo` の節だけ。** それ以外は再生成で上書きされうるものとして扱う。

**前提**: Node.js 22.12 以上（`package.json` の `engines`）。

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
| `src/layouts/Base.astro` | 共通レイアウトとスタイル |
| `src/pages/index.astro` | 記事一覧 |
| `src/pages/articles/[...slug].astro` | 記事詳細。出典と AI 利用の開示を描く |
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

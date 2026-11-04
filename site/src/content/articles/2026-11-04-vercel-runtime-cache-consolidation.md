---
title: "Vercel、Data CacheをRuntime Cacheに統合　容量を最大10倍に拡大"
publishedAt: 2026-11-04T10:24:42+09:00
sourceUrl: "https://vercel.com/blog/simplifying-runtime-caching-on-vercel"
sourceTitle: "Simplifying runtime caching on Vercel"
source: "vercel-blog"
discussionUrl: "https://vercel.com/blog/simplifying-runtime-caching-on-vercel"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/vercel.com/blog/simplifying-runtime-caching-on-vercel"
score: 0
comments: 0
tags: ["vercel", "caching", "nextjs", "redis"]
model: "gemini-3.6-flash"
generatedAt: 2026-11-04T01:24:42Z
---

## 元記事の要旨

- Vercelは、Next.jsのApp Routerなどで使われていたData CacheをRuntime Cacheに統合し、フレームワークを問わず一貫して利用できるデータキャッシュ基盤へ一本化しました。
- Runtime Cacheは分散型インフラで構築されており、各リージョンのRedisとタグによる無効化機構によって、毎時4億4000万回以上の読み取りリクエストを処理します。
- 回路遮断器の導入によりトラフィック急増時のレイテンシを従来比で約5分の1に削減したほか、ストレージ容量枠をProで8倍、Enterpriseで10倍に拡大しました。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **Next.js以外のフレームワークでデータキャッシュを使いたいとき**: Runtime CacheのAPIを直接呼び出すことで、SvelteKitやNuxtなどのアプリからでもVercelのリージョン別キャッシュ基盤を利用できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **p99（99パーセンタイル）**: 全体のリクエストのうち99%が収まる応答時間を指し、最悪に近い条件下での遅延状況を評価する指標です。
- **サーキットブレーカー（回路遮断器）**: 依存先システムの遅延や障害を検知した際に接続を一時遮断し、システム全体の崩壊や処理待ちを防ぐ仕組みです。

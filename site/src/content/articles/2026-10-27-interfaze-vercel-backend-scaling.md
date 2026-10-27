---
title: "Interfaze、Vercelで月5000万件のモデルAPIを運用　サーバーレスで完結"
publishedAt: 2026-10-27T09:32:28+09:00
sourceUrl: "https://vercel.com/blog/how-interfaze-serves-50-million-requests-a-month-on-vercel"
sourceTitle: "How Interfaze serves 50 million requests a month on Vercel"
source: "vercel-blog"
discussionUrl: "https://vercel.com/blog/how-interfaze-serves-50-million-requests-a-month-on-vercel"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/vercel.com/blog/how-interfaze-serves-50-million-requests-a-month-on-vercel"
score: 0
comments: 0
tags: ["vercel", "serverless", "ai", "puppeteer"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-27T00:32:28Z
---

## 元記事の要旨

- InterfazeはOCRや文書処理、分類など、汎用LLMが苦手とする決定論的なタスクに特化したモデルを開発・提供しており、根拠箇所を示すバウンディングボックスや信頼度スコアを付与して検証可能な出力を返すのが特徴です。
- 同社のAPIは月間5000万リクエストに達していますが、フロントエンドと同一のリポジトリからVercel上にサーバーレス関数としてバックエンドをデプロイしており、インフラ管理の手間なく運用されています。
- 高負荷な処理にはFluid computeを採用し、Puppeteerによるウェブスクレイピングやコード実行を安定して処理しているほか、AI Gatewayによって複数プロバイダー間の自動フォールバックと性能比較を実現しています。
- また、長期のメール配信シーケンスを管理するWorkflow SDKや、モデルのバージョンごとに独立したログとURLを提供するプレビュー機能を活用し、迅速な検証と障害原因の特定を可能にしています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **請求書や契約書の記載内容を高精度かつ検証可能に抽出したいとき**: 入力プロンプトを解釈しつつ、抽出値とともに文書内の該当座標と信頼度スコアを返すため、医療や金融、法務などの厳密さが求められる業務で誤抽出を即座に確認できます。
- **外部AIモデルの障害やAPI制限によるシステム停止を防ぎたいとき**: AI Gatewayの自動フォールバック機能により、特定プロバイダーが停止しても別の提供元へトラフィックを自動迂回できるため、データ前処理などのパイプラインを停止させずに運用できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **bounding box（バウンディングボックス、境界枠）**: 画像や文書内で特定の情報が存在する位置を四角形の座標で囲んで示す枠のことです。
- **deterministic（決定論的、再現性のある処理）**: 同じ入力に対して常に一貫した同一の結果を返す特性のことです。
- **fallback（フォールバック、代替処理）**: 接続先の障害や制限時に、自動で予備の別システムへ切り替えて処理を継続する仕組みのことです。

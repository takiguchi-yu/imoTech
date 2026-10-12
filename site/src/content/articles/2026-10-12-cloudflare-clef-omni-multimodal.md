---
title: "Cloudflare、音声動画対応「Clef-omni」公開　flashを約58%値下げ"
publishedAt: 2026-10-12T09:32:16+09:00
sourceUrl: "https://blog.cloudflare.com/clef-faster-cheaper-multimodal/"
sourceTitle: "Introducing Clef-omni with full multimodality, plus a faster Clef and a cheaper Clef-flash"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/clef-faster-cheaper-multimodal/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/clef-faster-cheaper-multimodal/"
score: 0
comments: 0
tags: ["cloudflare", "multimodal", "ai-agents", "machine-learning"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-12T00:32:16Z
---

## 元記事の要旨

- Cloudflareは、テキストや画像に加え音声・動画入力を直接扱えるオープンウェイト意思決定モデル「Clef-omni」を公開しました。外部の音声認識や動画分解パイプラインを挟まず、単一のAPI呼び出しで判定処理を完結できます。
- Clef-omniはQwen3-OmniのMoE構造を基盤としており、テキスト生成を省いて入力の全モダリティを同時にスコアリングします。応答速度はテキストで中央値約130ミリ秒、音声付き動画でも約1.5秒で判定を返します。
- あわせて小型版「Clef-flash」のホスト版価格を100万トークンあたり0.09ドルから0.038ドルへ値下げしました。これに伴いホスト版のコンテキスト長は24kに縮小されましたが、公開されている重み自体は256k対応のまま維持されます。
- ホスト版の通常モデル「Clef」についても Workers AI 上での最適化により実行速度が向上しました。ベンチマークでは各種API呼び出しやツール選択タスクにおいて高い精度を維持していることが示されています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **機器の設置状態や異音を一度に点検したいとき**: 写真と稼働音、動画をClef-omniにまとめて送信することで、音声文字起こしや画像切り出しの処理系を組むことなく、部品の視認性や異音の有無を単一APIで即座に自動判定できます。
- **低遅延かつ低コストに大量の分岐処理を行いたいとき**: 大幅に値下げされたClef-flashや高速化されたClefを活用することで、トークン費用を抑えながらミリ秒単位でワークフロー内のツール選択や分岐判断を実行できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **MoE（Mixture of Experts、専門家混合）**: 複数の専門ネットワークを入力に応じて切り替え、計算量を抑えつつモデル規模を拡大する設計手法です。
- **コンテキスト長（context window、文脈幅）**: モデルが一度に入力として受け取って処理できるトークン（単語や文字の単位）の最大量のことです。
- **Brier score（ブライエスコア、予測確率の評価指標）**: 予測確率と実際の結果の二乗誤差を測る指標で、モデルが出力する信頼度スコアの正確さを評価・補正する際に用いられます。

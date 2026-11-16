---
title: "Vercel、AI統計発表　判断特化型が要求の26%に急伸"
publishedAt: 2026-11-16T10:05:40+09:00
sourceUrl: "https://vercel.com/blog/ai-gateway-production-index-november-2026"
sourceTitle: "Decision models take 26% of requests; Anthropic now wins new teams 2:1"
source: "vercel-blog"
discussionUrl: "https://vercel.com/blog/ai-gateway-production-index-november-2026"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/vercel.com/blog/ai-gateway-production-index-november-2026"
score: 0
comments: 0
tags: ["ai", "llm", "vercel", "cloud"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-16T01:05:40Z
---

## 元記事の要旨

- VercelがAI Gatewayの本番トラフィック分析レポート（2026年11月版）を公表しました。テキスト生成を行わず分類や選択に特化した「決定モデル（decision model）」が、わずか6週間で全リクエストの26%を占めるまでに急成長しています。
- 決定モデルはリクエストあたりのコストが言語モデルの約70分の1と安価なため、リクエスト数の4分の1を占めながら利用金額全体の0.53%にとどまっています。月間100億トークン以上を処理する大規模チームでは7割が導入しています。
- モデル提供元のシェアでは新規チームの獲得比率でAnthropicがOpenAIを約2対1でリードした一方、支出シェアではOpenAIが前年12月比で約66%増加しました。上位1%の大規模チームの9割以上は両社を併用しています。
- 言語モデルのリクエストの半数以上が公開後2か月未満のモデルに送られており、モデルの利用ピークから1か月後には75%のチームが別モデルへ移行するなど、最新モデルへの乗り換えサイクルの短縮化が顕著になっています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **大規模なWebサービスでユーザー入力のトリアージや分類を低コストに行いたいとき**: 生成を行わない決定モデルを活用することで、従来の言語モデルと比べて約70分の1のAPIコストで高速に分類や選択の判定処理を実行できます。
- **既存のチャットアプリやエージェント機能に音声対話インターフェースを追加したいとき**: 既存の言語モデル処理の前後に音声認識・音声合成モデルを個別に追加する構成が主流となっており、コアロジックを維持したまま音声対応を導入できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **AI Gateway（AIゲートウェイ）**: アプリと複数AIサービスの間に入り、認証やルーティング、利用計測を一括管理する仲介基盤です。
- **決定モデル（decision model）**: 文章生成ではなく、短文の分類・スコアリング・選択に特化し、低コストかつ高速に動くAIモデルです。

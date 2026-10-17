---
title: "Vercel、AI利用動向を発表　オープン重みモデルがトークンの71%占める"
publishedAt: 2026-10-18T08:08:56+09:00
sourceUrl: "https://vercel.com/blog/ai-gateway-production-index-october-2026"
sourceTitle: "Open weight takes 71.5% of tokens and 23% of spend"
source: "vercel-blog"
discussionUrl: "https://vercel.com/blog/ai-gateway-production-index-october-2026"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/vercel.com/blog/ai-gateway-production-index-october-2026"
score: 0
comments: 0
tags: ["ai", "vercel", "llm", "open-weight", "cloud"]
model: "gemini-3.6-flash"
generatedAt: 2026-10-17T23:08:56Z
---

## 元記事の要旨

- Vercelは2026年10月の「AI Gateway Production Index」を公開した。オープンウェイトモデルがトークン処理量の71.5%を占め、全体支出における割合も6月の5%未満から23%へと4倍以上に急増している。
- 全体のAI支出は前年12月比で13倍に拡大した一方、トークンあたりの平均単価は47%下落した。また、利用チームの約3割が1ヶ月で最も利用する開発元（ラボ）を変更するなど、マルチモデル化が進んでいる。
- 中国発のAIモデルに対する支出の68%超が米国プロバイダー経由で行われている。DeepSeekやKimiなどのモデルが活発に利用される中、推論インフラを提供する米国企業を経由した利用が定着している。
- 9月の新モデルでは、決定モデルのJevが開始2週間で有料チームの35%に達する最速の導入率を記録した。一方で、支出額のシェアではOpus 5.5が10%以上を獲得し最大となった。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **自社プロダクトで複数のAIモデルを使い分けたいとき**: トークン単価の下落とモデルの多様化が進む中、AI Gateway等を挟んで用途別に最適なモデルへルーティングすることで、コストを抑えつつシステムの応答性能を高められます。
- **海外発の高性能モデルを安全に導入したいとき**: オープンソースや中国発のモデルを自社で運用せず、実績のある米国クラウドプロバイダーが展開するAPIを経由することで、運用の安定性やセキュリティ要件を満たしながら活用できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **オープンウェイトモデル（open-weight model）**: 学習済みの重み（パラメーター）が公開され、自前のインフラや各種クラウド上で自由に動かすことができるAIモデル。
- **決定モデル（decision model）**: 長文生成ではなく、高速かつ低コストで特定の条件判定やルーティングなどの意思決定を行うことに特化したモデル。

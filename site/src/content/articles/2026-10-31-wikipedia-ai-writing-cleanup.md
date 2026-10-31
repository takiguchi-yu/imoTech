---
title: "Wikipedia、AI生成記事を排除へ　有志が検知ツール開発し新規の最大2割対象"
publishedAt: 2026-10-31T10:19:10+09:00
sourceUrl: "https://spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup"
sourceTitle: "Wikipedia's Cleanup of AI-Generated Content"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50257326"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/spectrum.ieee.org/wikipedia-wikiproject-ai-writing-cleanup"
score: 518
comments: 189
tags: ["wikipedia", "ai", "llm", "crowdsourcing"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-31T01:19:10Z
---

## 元記事の要旨

- Wikipediaの有志プロジェクト「WikiProject AI Cleanup」は、ガイドラインに反して投稿されるAI生成テキストを検知し、削除する取り組みを続けています。
- 初期のAI特有の決まり文句から構造的な特徴へと検知手法を進化させており、本物の出典を用いながら内容を誤解釈する幻覚への対策や、検証用AIツールの導入が進められています。
- 検出企業との検証では新規記事や下書きの最大20％がAI生成と判定されており、英語版WikipediaではLLMを用いた記事生成を禁止する規則が導入されました。
- 人間が執筆した信頼性の高い知識基盤という価値を守る一方で、AI検索による直接流入の減少（Google Zero）を見据えたAIとの新たな協調関係も模索されています。

## 議論の論調

### 大量生成される低品質記事と検証負荷の増大

8割程度それらしい文章が容易に作れるようになった結果、残り2割の誤りや不正確な出典を検証する人間の負担が急増しているという指摘がなされました。質の低い投稿が大量に押し寄せることで、コミュニティのリソースが限界を迎える懸念が共有されています。

### AI生成の是非ではなく記述内容の正確性が本質

問題視すべきはAIが生成したこと自体ではなく内容の正確さや品質であり、人間が書いた文章でも誤りや偏向は存在するという意見が出ました。人間対AIという二項対立ではなく、誤りを発見・修正するための補助ツールとしてAIを前向きに活用すべきだという見解もあります。

### AIモデルの再学習によるデータ汚染への危惧

Wikipediaのような主要な情報源にAI生成テキストが混入すると、将来のモデルが自身の出力を学習して劣化する循環的な崩壊を招くという懸念が語られました。特に少数言語では学習元となる自然なテキストが損なわれ、不可逆的な影響が出ることが指摘されています。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **RAG（retrieval-augmented generation、検索拡張生成）**: 外部資料を検索・参照した上でLLMに回答を生成させ、誤情報の発生を抑える技術。
- **Google Zero（グーグル・ゼロ）**: 検索エンジンのAI回答により、参照元Webサイトへの訪問者が激減する現象。

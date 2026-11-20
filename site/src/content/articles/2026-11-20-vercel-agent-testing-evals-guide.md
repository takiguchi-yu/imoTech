---
title: "米Vercel、AIエージェント向け評価手法の設計指針を公開"
publishedAt: 2026-11-20T11:19:56+09:00
sourceUrl: "https://vercel.com/blog/agent-evals"
sourceTitle: "Agents are users, so your software needs evals"
source: "vercel-blog"
discussionUrl: "https://vercel.com/blog/agent-evals"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/vercel.com/blog/agent-evals"
score: 0
comments: 0
tags: ["ai", "llm", "testing", "evaluation"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-20T02:19:56Z
---

## 元記事の要旨

- AIエージェントがソフトウェアの利用者となる中、APIやCLIの正常応答だけでなく、ユーザーの意図した結果を達成できたかを評価する「eval」の重要性を論じています。
- テストをLLMの呼び出し回数に応じて「決定論的テスト」「1ターン評価」「E2E評価」の3層に分類し、低コストなテストを優先するテストピラミッドの活用を提唱しています。
- E2E評価では、複数回試行して1回でも成功する確率「pass@k」と、連続して成功する確率「pass^k」を区別し、失敗のコストに応じた指標管理を求めています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **AIエージェント対応のAPIやCLIを開発・保守するとき**: LLM呼び出し回数に基づくテストピラミッドを適用することで、コストと実行時間を抑えつつ、エージェントが正しく目的を達成できるかを段階的に検証できます。
- **業務自動化エージェントの運用信頼性を評価したいとき**: 単発の成功率だけでなく「pass^k」を算出することで、失敗が許されない業務タスクに対してエージェントが実用的な水準に達しているかを客観的に判断できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **eval（評価）**: LLMやAIエージェントに同一タスクを複数回実行させ、成功率や効率を採点するテスト手法です。
- **pass@k**: k回試行したうち、少なくとも1回タスクを達成できる確率を示す評価指標です。
- **pass^k**: k回試行したとき、そのすべてで連続してタスクに成功する確率を示す評価指標です。

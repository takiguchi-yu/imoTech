---
title: "Rogo、AI生成コードのデプロイ時間を5分に短縮　月7万3千回超をVercelで実行"
publishedAt: 2026-10-06T10:48:28+09:00
sourceUrl: "https://vercel.com/blog/how-rogo-ships-agent-written-code-to-production-in-5-minutes-on-vercel"
sourceTitle: "How Rogo ships agent-written code to production in 5 minutes on Vercel"
source: "vercel-blog"
discussionUrl: "https://vercel.com/blog/how-rogo-ships-agent-written-code-to-production-in-5-minutes-on-vercel"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/vercel.com/blog/how-rogo-ships-agent-written-code-to-production-in-5-minutes-on-vercel"
score: 0
comments: 0
tags: ["vercel", "ai-agent", "devops", "deployment"]
model: "gemini-3.6-flash"
generatedAt: 2026-10-06T01:48:28Z
---

## 元記事の要旨

- 金融機関向けAIエージェント「Felix」を開発するRogoは、社内アプリケーション基盤をVercel上に再構築し、AIエージェントが作成したコードをわずか5分で本番環境へデプロイする体制を整えました。
- 同社は解約分析から取引支援までの業務を自動化する6つの本番用AIエージェントを運用しており、Vercelの導入によって月間7万3,000回を超えるデプロイを実行しています。
- 本番環境で障害が発生した際には、AI SDK上で動作するエージェント群が自動で原因調査と修復を行うため、手動による介入なしでトラブル対応が完了します。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **AIによるコード生成から本番公開までを高速化したいとき**: Vercelのプレビュー環境と自動デプロイ基盤を連携させることで、エージェントが作成したコードの検証から本番反映までを5分に短縮できます。
- **本番環境の障害一次対応や復旧作業を自動化したいとき**: AI SDKで構築したエージェント群を連携させることで、人間の介入なしに障害原因の調査から修正プログラムの適用までを自律的に行えます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **AI SDK（AI開発用ソフトウェア開発キット）**: Vercelが提供する、WebアプリケーションにAIエージェントやLLMを組み込むための開発ライブラリ群です。

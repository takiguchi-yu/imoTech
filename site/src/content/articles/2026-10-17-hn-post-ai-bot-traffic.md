---
title: "開発者、HN投稿後にAIボット殺到で障害　アクセスの約半分が特定業者"
publishedAt: 2026-10-17T08:38:15+09:00
sourceUrl: "https://www.sammystraus.com/#i-posted-to-hn-and-then-my-website-was-flooded-with-ai-bot-traffic"
sourceTitle: "I posted to HN, and then my website was flooded with AI bot traffic"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50073221"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/www.sammystraus.com/#i-posted-to-hn-and-then-my-website-was-flooded-with-ai-bot-traffic"
score: 350
comments: 176
tags: ["bots", "web-scraping", "infrastructure", "nginx"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-16T23:38:15Z
---

## 元記事の要旨

- フィードリーダーを開発した個人がHacker Newsでサービスを紹介したところ、直後からサーバーの負荷が跳ね上がり、動作が極端に遅くなる事態に見舞われました。
- アクセスログを調査した結果、全トラフィックの約半分がサイトの変更を監視してAI要約を作成する単一の業者による過剰なリクエストだと判明しました。
- 大手AI企業のクローラーや脆弱性スキャナーも多数押し寄せていたため、著者は該当業者の遮断、robots.txtの整備、レート制限の導入とインフラ改善で対応しました。

## 議論の論調

### 悪質なクローラーに対する遮断手法の限界

大手クラウドのIP帯をまとめて遮断しているという報告に対し、住宅用プロキシの普及によりIP単位の拒否は難しくなっているとの指摘が上がりました。対抗策として、応答を極端に遅らせて相手のリソースを奪うターピットや難解な計算パズルの活用も提案されています。

### サーバー側の設計とキャッシュ配置の重要性

毎分数十回程度のリクエストでサーバーが耐えられないのは構成に課題があり、静的コンテンツのCDN配信やエッジキャッシュを挟むべきだとの指摘が寄せられました。一方で、APIエンドポイントを直接狙う高度なbotにはキャッシュだけでは対処できないという意見も出ています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **個人開発のWebサービスを公開・告知するとき**: 公開直後にAIボットやスキャナーが殺到する前提で、事前にレートリミットやrobots.txt、CDNキャッシュを組み込んでおく設計指針として役立ちます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **ASN（Autonomous System Number、自律システム番号）**: インターネット上で独立して経路制御を行うネットワーク組織（クラウド事業者など）を識別する番号です。
- **住宅用プロキシ（レジデンシャルプロキシ）**: 一般家庭のプロバイダ回線を経由させる接続中継手段で、クラウド遮断を回避するbotに悪用されます。
- **tarpit（ターピット、遅延接続）**: 不正なアクセスに対して意図的に極端に遅くデータを送信し、攻撃側の接続枠を拘束して嫌がらせを防ぐ手法です。

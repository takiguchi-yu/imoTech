---
title: "Cloudflare、個人向けAIエージェントの可視化とアクセス制御を提供"
publishedAt: 2026-11-06T10:33:54+09:00
sourceUrl: "https://blog.cloudflare.com/personal-agents-visibility-control/"
sourceTitle: "See the agents, set the terms: new visibility and control for personal agents"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/personal-agents-visibility-control/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/personal-agents-visibility-control/"
score: 0
comments: 0
tags: ["cloudflare", "bot-management", "ai-agent", "security", "waf"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-06T01:33:54Z
---

## 元記事の要旨

- 人間の指示を受けてサイトの比較や購入を代行する個人向けAIエージェントを自動トラフィックから識別するため、分析ダッシュボードに専用カテゴリが新設されました。
- サイト管理者は訪問元のエージェントごとにリクエスト数や閲覧パス、HTTPステータスコードを確認でき、顧客による有用な通信かリスクかを判断できます。
- セキュリティ設定の拡張により、エージェントごとに許可、全体ブロック、または広告掲載ページのみのブロックといった細かなアクセス制御ポリシーを適用可能です。
- アカウント保護機能と併用することで、不審なエージェント利用のみを特定アカウント単位のWAFルールで遮断し、他の正規ユーザーに影響を与えずに対処できます。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **広告収入を守りつつAI経由の訪問客を受け入れたいとき**: 広告掲載ページのみエージェントを遮断し、商品詳細ページではアクセスを許可する制御ポリシーを選ぶことで、広告の閲覧機会を損なわずに購入支援エージェントの流入を維持できます。
- **特定アカウントへの不正な自動アクセスを個別に遮断したいとき**: アカウント保護機能で各顧客に紐づくエージェント履歴を追跡し、不審な動きを見せたアカウントのみにWAFルールを適用することで、他の利用者を巻き込まずに安全を確保できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **WAF（web application firewall、ウェブアプリ防御壁）**: 悪意ある通信や不正アクセスを検知・遮断するセキュリティシステムです。この記事では特定ユーザー単位の制御手段として言及されています。

---
title: "Cloudflare、AIでボット対策を自動設定する「Turnstile Spin」公開"
publishedAt: 2026-09-28T08:48:28+09:00
sourceUrl: "https://blog.cloudflare.com/turnstile-spin/"
sourceTitle: "Agents can now set up your website’s security with Turnstile Spin"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/turnstile-spin/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/turnstile-spin/"
score: 0
comments: 0
tags: ["cloudflare", "security", "bot-protection", "generative-ai"]
model: "gemini-3.8-flash"
generatedAt: 2026-09-27T23:48:28Z
---

## 元記事の要旨

- Cloudflareは、AIコーディングエージェントを介してボット対策機能「Turnstile」の導入や修正を自動化する新ツール「Turnstile Spin」を公開しました。
- Turnstileの導入にはフロントエンドの配置とバックエンドの検証API連携の2工程が必要ですが、エージェントがコードベースを調べて双方の実装を自動で行います。
- 新規導入に加えて、サーバー側検証が抜けている既存設定の修復や他社CAPTCHAからの移行にも対応しており、ソースコードを同社へ送信せずに手元で変更を適用できます。
- ダッシュボードやCLIツールのWrangler、各種AIエージェントから呼び出し可能で、先行提供開始からすでに6万5000件以上のウィジェット作成に利用されています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **AIエージェントで素早く作成したWebアプリにボット対策を追加したいとき**: エージェントに指示を渡すだけで、フロントエンドのウィジェット配置とバックエンドの認証API呼び出しを同時に抜け漏れなくコードへ組み込めます。
- **過去にTurnstileを導入したもののサーバー側検証が抜けていたとき**: 管理画面の警告から起動でき、既存のウィジェットやキーを維持したまま、不足しているバックエンドの検証ロジックを自動で追加してくれます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **Turnstile**: Cloudflareが提供する、画像パズルなどを解かせずに訪問者が人間かを判定するボット対策機能。
- **Siteverify API**: 訪問者が認証を通過したかを確認するために、自社サーバー側からCloudflareへ問い合わせるAPI。

---
title: "Rillet、AIエージェントで開発速度を3倍に　改修を2時間で本番反映"
publishedAt: 2026-10-12T09:34:03+09:00
sourceUrl: "https://vercel.com/blog/how-rillet-ships-3-faster-with-ai-agents-on-vercel"
sourceTitle: "How Rillet ships 3× faster with AI agents on Vercel"
source: "vercel-blog"
discussionUrl: "https://vercel.com/blog/how-rillet-ships-3-faster-with-ai-agents-on-vercel"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/vercel.com/blog/how-rillet-ships-3-faster-with-ai-agents-on-vercel"
score: 0
comments: 0
tags: ["vercel", "ai-agent", "llm", "automation"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-12T00:34:03Z
---

## 元記事の要旨

- 会計ERPプラットフォームを提供する米Rilletは、Vercelとフレームワーク「eve」を活用して社内業務にAIエージェントを組み込み、リリース速度を3か月で3倍に向上させました。
- 顧客対応チームが取得した要望から、エージェントが仕様策定、コード修正、サンドボックス上でのテスト、プルリクエスト作成までを自動で行い、最短2時間で本番環境へ反映しています。
- エージェントは指示やツールを1つのディレクトリにまとめるeveの構成を採用しており、TypeScriptを書かない非エンジニアでもMarkdownを通じて振る舞いの調整に参加可能です。
- モデルへの接続にはVercelのAI Gatewayを用いて複数プロバイダを一元管理し、外部連携にはVercel Connectの短寿命トークンを利用して安全性を確保しています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **顧客からの改善要望やバグ修正を少人数で迅速に反映したいとき**: 文脈収集からコード生成、テスト、PR作成までをエージェントに任せることで、エンジニアのレビュー負荷を抑えつつ修正を短時間で本番投入できます。
- **非エンジニアも含めて社内業務用のエージェントを内製したいとき**: 指示やナレッジをMarkdownで管理できる構成を採用することで、コードを書けない担当者でもエージェントの挙動定義や改善に直接関われます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **ERP（Enterprise Resource Planning、統合基幹業務システム）**: 会計、人事、購買などの基幹業務データを一元的に管理し、業務を効率化するためのシステムです。
- **SSO（Single Sign-On、シングルサインオン）**: 一度のユーザー認証を行うだけで、連携する複数のクラウドサービスや社内システムを利用できる仕組みです。
- **PRD（Product Requirements Document、製品要求仕様書）**: 開発する機能の背景、目的、満たすべき要件などを整理して関係者間で共有するための文書です。

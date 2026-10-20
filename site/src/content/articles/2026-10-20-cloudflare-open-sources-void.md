---
title: "Cloudflare、「Void」3製品をOSS公開　Viteでフルスタック開発"
publishedAt: 2026-10-20T09:20:46+09:00
sourceUrl: "https://blog.cloudflare.com/deploy-with-void/"
sourceTitle: "Deploy with Void"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/deploy-with-void/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/deploy-with-void/"
score: 0
comments: 0
tags: ["cloudflare", "vite", "javascript", "fullstack"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-20T00:20:46Z
---

## 元記事の要旨

- VoidZeroのCloudflare合流に伴い、ViteとCloudflareを活用したフルスタック開発を実現する「Void Platform」「Void SDK」「Void CLI」の3製品がオープンソースとして公開されました。
- Void SDKはViteプラグインとして機能し、ReactやVueなどに対応しつつ、データベースやAI GatewayなどのCloudflareリソースをコードから自動でプロビジョニングします。
- Void Platformにより企業は独自の共通デプロイ基盤を構築でき、アクセス制御やリソース制限を維持したまま、非エンジニアやコーディングエージェントによる迅速な社内アプリ公開を支援します。
- Void CLIを用いることで単一コマンドでのデプロイが可能となり、AIエージェントと連携したログ確認やデバッグ、プラットフォーム運用のライフサイクル管理まで一括して行えます。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **社内向けツールを安全かつ迅速に開発したいとき**: 自社環境にVoid Platformを構築することで、社員にクラウドアカウントを直接渡さずに制限付きの共有基盤を提供し、安全なプロトタイプ開発を可能にします。
- **Vite製フロントエンドにAPIやDBを追加したいとき**: Void SDKをプラグインとして追加するだけで、ローカルDBやCloudflare D1のプロビジョニングが自動化され、型安全なフルスタック構成へ即座に拡張できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **Workers for Platforms**: 自社基盤上で外部ユーザーや従業員が作成したコードを安全に分離・実行できるCloudflareの基盤機能です。
- **AI Gateway**: AIモデルへのAPI呼び出しを集約し、分析やキャッシュ、レート制限などを一括管理できる機能です。

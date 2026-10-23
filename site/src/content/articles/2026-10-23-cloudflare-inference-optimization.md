---
title: "Cloudflare、AIコードレビューの推論コストを68%削減した手法を公開"
publishedAt: 2026-10-23T09:00:24+09:00
sourceUrl: "https://blog.cloudflare.com/obsessive-inference-optimization/"
sourceTitle: "Cutting our inference bill by 68% by being obsessive about optimization"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/obsessive-inference-optimization/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/obsessive-inference-optimization/"
score: 0
comments: 0
tags: ["ai", "llm", "optimization", "cloudflare"]
model: "gemini-3.5-flash-lite"
generatedAt: 2026-10-23T00:00:24Z
---

## 元記事の要旨

- AIコードレビューの平均コストが1回あたり2.46ドルから0.77ドルへと68%減少した。
- コスト増大の主な原因は、Anthropicモデルへの移行や、エンジニアがより複雑な変更を行うようになったことによるトークン数の増加だった。
- プロンプトのキャッシュ機構を活用し、リポジトリ間で共通するプレフィックスを共有できるようにプロンプトの構造を改修した。
- 不要なツールの削除やファイルの一括読み込み、再レビュー時の不要なレビュアーのスキップなどを実施し、LLMの呼び出し回数を減らした。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **OpenCode**: Cloudflareが開発・運用しているAIコードレビューを行うための内部システムおよびフレームワーク。
- **Durable Objects**: Cloudflare Workers上で状態を保持しながら実行できるサーバーレスのストレージおよびコンピュート機能。

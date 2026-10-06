---
title: "Cloudflare、AI Gateway経由のWeb検索APIを3社と提携し提供開始"
publishedAt: 2026-10-06T10:46:15+09:00
sourceUrl: "https://blog.cloudflare.com/introducing-web-search-api/"
sourceTitle: "Introducing Web Search API via AI Gateway"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/introducing-web-search-api/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/introducing-web-search-api/"
score: 0
comments: 0
tags: ["cloudflare", "ai-gateway", "llm", "search-api"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-06T01:46:15Z
---

## 元記事の要旨

- Cloudflareは、AI Gateway経由で利用できる「Web Search API」を発表しました。Ceramic.ai、Exa、Linkupの3社と提携し、AIエージェントへの最新情報の供給を支援します。
- 従来のURL推測によるWeb取得の失敗を防ぎ、検索エンジンを用いて最新ニュースや変更されたAPIドキュメントなどの構造化されたスニペットを推論コンテキストに直接注入できます。
- 提携検索プロバイダーはクローラーの身元明示やrobots.txtの遵守といったCloudflareの認証ボット基準を満たすことが義務付けられ、検索結果には情報元のリンクが含まれます。
- AI Gatewayを通じて統合ログや利用量課金、BYOKに対応し、標準REST APIやCloudflare Workersバインディングから追加の手数料なしで呼び出し可能です。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **最新ドキュメントを参照する開発支援エージェントを作るとき**: AI GatewayのWeb Search APIを通じて最新のAPI仕様やリリース情報を取得できるため、モデルの知識カットオフ以降のツール情報にも正確に追従できます。
- **社内エージェントのWeb検索コストとログを一元管理したいとき**: AI Gatewayの管理画面に検索APIの利用ログや課金が集約され、既存のクレジットやBYOKを用いて統一的にアクセス制御や監査を行えます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **BYOK（Bring Your Own Key、独自キー持ち込み）**: ユーザー自身が外部サービスで契約・取得したAPIキーを、プラットフォームに持ち込んでそのまま利用する仕組みです。
- **ZDR（Zero Data Retention、データ非保持）**: プロバイダーが送信されたプロンプトや検索クエリなどの利用データをサーバー側に保存しない運用方針のことです。

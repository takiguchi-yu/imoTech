---
title: "Cloudflare、監視機能を統合する8つのメジャーアップデートを公開"
publishedAt: 2026-10-07T09:43:39+09:00
sourceUrl: "https://blog.cloudflare.com/one-observability-platform/"
sourceTitle: "8 major updates to Cloudflare Observability"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/one-observability-platform/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/one-observability-platform/"
score: 0
comments: 0
tags: ["cloudflare", "observability", "logging", "tracing"]
model: "gemini-3.5-flash"
generatedAt: 2026-10-07T00:43:39Z
---

## 元記事の要旨

- Cloudflareは、ログ、トレース、分析、アラート、ダッシュボード、エクスポートを1つに統合した、新しいオブザーバビリティプラットフォームを発表しました。製品をまたいだ一貫性のある監視体験を提供します。
- 主な更新として、すべてのログを1箇所で調査できる「Logs home」や、リクエストの動きを可視化する「Cloudflare Traces」のオープンベータ版、統一されたSQL APIの提供などが含まれます。
- 料金体系も刷新され、イベント数ではなく、取り込み・保存されたデータ量に基づいたシンプルな従量課金制に移行します。また、これまでエンタープライズ向けだった「Logpush」が全プランで利用可能になります。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **Cloudflare上の複数サービスで発生したエラーの原因を特定したいとき**: Logs homeでHTTPイベントやWorkersなどの異なるログを横断検索できます。SQLや自然言語での可視化に対応しているため、データセンターやパスごとの遅延を迅速に絞り込めます。
- **リクエストがCloudflare内でどのように処理されたか詳細に追跡したいとき**: オープンベータ版のCloudflare Tracesを利用することで、キャッシュの決定やセキュリティルール、Workersの処理時間などをリクエスト単位で可視化し、ボトルネックを特定できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **オブザーバビリティ（observability、可観測性）**: システムの内部状態を、出力されるログやメトリクスなどのデータからどれだけ詳細に把握・理解できるかを示す度合いのことです。
- **トレース（trace、実行経路の追跡）**: システム内でリクエストがどのように処理され、どのコンポーネントを通過したかを時系列で記録し、パフォーマンスのボトルネックを特定する仕組みです。
- **MCP（Model Context Protocol、モデルコンテキストプロトコル）**: AIアシスタントやエージェントが、外部のデータソースや開発ツールと安全に連携して情報を取得・操作するための標準的な接続規格です。

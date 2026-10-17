---
title: "Cloudflare、GatewayとDLPにCloudflare Workersを統合したプログラマブルなSASEプラットフォームを発表"
publishedAt: 2026-10-18T08:08:17+09:00
sourceUrl: "https://blog.cloudflare.com/programmable-gateway-dlp/"
sourceTitle: "A fully programmable secure web gateway"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/programmable-gateway-dlp/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/programmable-gateway-dlp/"
score: 0
comments: 0
tags: ["cloudflare", "security", "edge-computing", "networking"]
model: "gemini-3.5-flash-lite"
generatedAt: 2026-10-17T23:08:17Z
---

## 元記事の要旨

- Cloudflareは、セキュアウェブゲートウェイ（Gateway）およびDLPにおいて、エッジコンピューティングプラットフォームを用いた完全なプログラマビリティの提供を発表しました。
- 従来の許可やブロックといった固定的なアクションに加え、HTTPリクエストの改変やプロキシ処理を行う新しい「Forward」アクションがパブリックベータとして公開されています。
- トラフィックの検証や判定処理をカスタムコードでインライン実行できるカスタム関数機能により、外部インフラを別途運用することなく柔軟な制御が可能になります。
- Cloudflare WorkersとGatewayが同一のエッジインフラ上で動作するため、ネットワーク境界を越えることによるレイテンシの増加や複雑なルーティングを回避できます。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **社内アプリケーションへのアクセス時にJWTのクレーム情報を元にしてHTTPヘッダーを動的に付与したいとき**: Cloudflare Workersを用いたカスタムロジックをインラインで実行できるため、これまで必要だったNginxプロキシのプールなどの追加インフラを自前で運用・維持管理するコストを削減できます。
- **従業員が新しいSaaSサービスへの登録を行った瞬間にSlackへ通知を送りたいとき**: Gatewayの「Forward」アクションにより、マッチしたトラフィックのコンテキストを非同期でWorkerへ渡し、外部サービスへの通知やログ記録といった処理をインフラの追加なしで実装できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **SASE（Secure Access Service Edge、ネットワークセキュリティとWAN機能を統合したアーキテクチャ）**: ネットワーク接続機能とセキュリティ機能をクラウド上で統合して提供するセキュリティモデルの概念。
- **DLP（Data Loss Prevention、情報漏洩対策）**: 機密データや個人情報の外部への流出を検出し、自動的にブロックまたは制御するためのセキュリティ技術。

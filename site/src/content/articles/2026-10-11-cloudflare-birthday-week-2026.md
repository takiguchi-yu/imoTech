---
title: "Cloudflare、設立記念週に46件を発表　AI対応や耐量子暗号を推進"
publishedAt: 2026-10-11T09:14:55+09:00
sourceUrl: "https://blog.cloudflare.com/birthday-week-2026-wrap-up/"
sourceTitle: "Everything we launched during Birthday Week 2026"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/birthday-week-2026-wrap-up/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/birthday-week-2026-wrap-up/"
score: 0
comments: 0
tags: ["cloudflare", "security", "ai", "cryptography"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-11T00:14:55Z
---

## 元記事の要旨

- Cloudflareは設立16周年を記念したイベントにて、自動トラフィックの増加やAIエージェントの普及に対応する全46件の新機能・構想を発表しました。
- オープンソース分野では、API操作用のCLI「cf」や分離実行CMS「EmDash」、ViteとNext.jsの統合ツールなどを公開し、開発環境を強化しました。
- セキュリティ面では、独自のパブリック認証局設立計画をはじめ、マークルツリー証明書による耐量子暗号対応やAIを活用したWAF検査などを打ち出しました。
- エージェント経済への対応として、AIによるWebアクセスに対してHTTP 402経由で対価を徴収できる課金ゲートウェイ機能のベータ版などを提供開始しました。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **自社WebコンテンツをAIエージェントに有料提供したいとき**: Monetization GatewayとHTTP 402を活用することで、AIによるサイト巡回やデータ取得に対して自動で利用料を請求し、対価を回収できます。
- **自社サービスの耐量子暗号への対応状況を把握・監査したいとき**: LogpushやHTTP Analyticsの可視化機能により、ユーザーとの通信で耐量子鍵交換が正常に成立しているかをリアルタイムに検証できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **耐量子暗号（ポスト量子暗号、PQC）**: 量子コンピュータでも解読が困難な次世代の暗号化方式。
- **HTTP 402（Payment Required、支払いが必要）**: Webコンテンツの利用に対価の支払いが必要であることを示す状態コード。
- **CA（Certificate Authority、認証局）**: Web通信の暗号化に使われる電子証明書を発行・管理する公的な機関。

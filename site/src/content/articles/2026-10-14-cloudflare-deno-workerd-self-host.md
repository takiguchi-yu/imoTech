---
title: "米Cloudflare、Deno開発陣と合流　Workersの自前運用を正式推進へ"
publishedAt: 2026-10-14T09:18:38+09:00
sourceUrl: "https://blog.cloudflare.com/deno-joins-cloudflare/"
sourceTitle: "Deno is joining Cloudflare"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/deno-joins-cloudflare/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/deno-joins-cloudflare/"
score: 0
comments: 0
tags: ["cloudflare", "deno", "workerd", "javascript"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-14T00:18:38Z
---

## 元記事の要旨

- Cloudflareは、Denoチームが開発したCloudflare Workers互換のセルフホスト実装「celld」を歓迎し、Deno創業者らと協力して公式ランタイム「workerd」のセルフホスト機能拡充を進めると発表しました。
- Workersは独自アーキテクチャによる低価格と高い分散性能を目指して設計されており、ベンダーロックインへの懸念を払拭するため実行基盤「workerd」のコード自体は本番と同じものをOSSとして公開していました。
- しかし、ステートフル処理を担う「Durable Objects」の自社運用向け実装が不足していたため、セルフホストとスケーラビリティに注力したcelldの設計思想やコードをworkerdへ統合することを決定しました。
- Node.jsやDenoの開発者であるライアン・ダール氏らが主導し、Workersのプログラミングモデルを外部サーバーでも本番稼働できる第一級の選択肢として整備していく計画です。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **自社インフラ環境でエッジ向け分散アプリを自前運用したいとき**: workerdにcelldの成果が統合されることで、Durable Objectsを含むWorkersのプログラミングモデルを自社サーバー群へ互換性を保ったまま展開できるようになります。
- **クラウドロックインを回避してエッジ関数基盤を選定したいとき**: Workers向けに書いたコードをOSSのworkerdで外部環境へ移行できる退路が保証されるため、特定プラットフォームに縛られるリスクを減らして導入を進められます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **Durable Objects**: Cloudflare Workers上で状態を永続化し、世界各地のエッジ間でデータの整合性を保ちながら協調動作させる仕組み。
- **workerd**: Cloudflare Workersの本番環境で実際に動作している、オープンソースのJavaScriptやWebAssembly実行基盤。

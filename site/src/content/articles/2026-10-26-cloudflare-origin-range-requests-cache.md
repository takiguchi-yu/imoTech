---
title: "Cloudflare、範囲要求キャッシュを刷新　R2のp99遅延を約半減"
publishedAt: 2026-10-26T08:17:27+09:00
sourceUrl: "https://blog.cloudflare.com/origin-range-requests/"
sourceTitle: "Origin Range Requests: Serving large files without range-request tuning"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/origin-range-requests/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/origin-range-requests/"
score: 0
comments: 0
tags: ["cdn", "cloudflare", "cache", "http", "networking"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-25T23:17:27Z
---

## 元記事の要旨

- 動画シークや中断再開などに使われるHTTP範囲リクエストについて、Cloudflareは旧来のキャッシュ機構を刷新し、全プランで利用可能な新機能「Origin Range Requests」を公開しました。
- 従来のNginxベースの実装では設定値によって過剰なオリジン転送やリクエストのブロックが生じていましたが、Pingoraの固定長チャンク保存を活用することで手動調整が不要になりました。
- エッジ側がキャッシュ済みデータや取得中の通信、オリジンからの差分取得を協調させて応答を結合するため、無駄なデータ転送を抑制しながら標準のHTTP応答を正確に返せます。
- 同社のオブジェクトストレージR2では、新実装によりp99での最初の1バイト受信時間（TTFB）が約半分に短縮され、キャッシュ階層間のトラフィックも約6%削減されたと報告されています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **動画配信サービスでシーク操作時の遅延を減らしたいとき**: クライアントが指定した範囲のみを固定長チャンクから切り出して返せるため、不要な大容量転送の待ち時間を発生させずにシーク時の応答速度を向上できます。
- **大容量パッケージ配布でオリジンの転送負荷を抑えたいとき**: 同じファイルへの範囲リクエストを進行中のダウンロードに相乗りさせ、未取得分のみを境界に合わせて取得するため、アクセス急増時でもオリジンへの負荷を抑制できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **TTFB（Time to First Byte、最初の1バイトを受信するまでの時間）**: リクエスト送信から最初のデータが届くまでの所要時間で、サーバーの応答速度の指標です。
- **HTTP範囲リクエスト（HTTP range request）**: ファイル全体ではなく、Rangeヘッダーを用いて指定した一部のバイト区間だけを取得する要求仕様です。
- **Pingora（ピンゴラ）**: CloudflareがNginxの代替としてRust言語で開発した、高速なプロキシサーバー基盤です。

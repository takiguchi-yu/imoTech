---
title: "Cloudflare、動画処理基盤「Streamline」公開　独自加工に対応"
publishedAt: 2026-10-05T08:57:49+09:00
sourceUrl: "https://blog.cloudflare.com/streamline/"
sourceTitle: "Streamline: custom video pipelines with Cloudflare Stream and Workers"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/streamline/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/streamline/"
score: 0
comments: 0
tags: ["cloudflare", "video", "workers", "containers", "ffmpeg"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-04T23:57:49Z
---

## 元記事の要旨

- Cloudflareは、ライブ配信への動的な注釈追加や字幕の焼き込みなど、独自の動画処理パイプラインを同社の開発者プラットフォーム上で構築できる環境「Streamline」を公開しました。
- Streamlineは、Go言語による制御部とFFmpegベースの処理部からなるMedia Engineをコンテナ上で常時実行し、動画の入出力やリアルタイム加工を担当します。
- セッション管理やライフサイクル制御にはWorkersとDurable Objectsを活用し、クライアントが切断しても処理を継続させつつ、タイムアウトによる自動停止も担保します。
- RTMPSやHLSといった動画プロトコルを扱い、Webカメラからの映像取り込みやリアルタイムプレビュー、配信結果をCloudflare Streamへ送出する連携が可能です。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **ライブ配信に動的な字幕や注釈を重ねたいとき**: Containers上でFFmpegが常時稼働し、API経由で注釈画像などの更新を受け付けるため、配信を切断することなくリアルタイムでテロップや図をオーバーレイできます。
- **配信動画のアーカイブに字幕を焼き込みたいとき**: Cloudflare Streamに保存された動画のHLSマニフェストを入力として読み込み、コンテナ内のパイプラインで字幕を合成して新たな動画として再出力できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **RTMPS（Real-Time Messaging Protocol over SSL/TLS、暗号化リアルタイム動画転送プロトコル）**: ライブ配信の映像や音声を安全に配信サーバーへ送信するための通信プロトコルです。
- **HLS（HTTP Live Streaming、HTTPベースの動画配信プロトコル）**: Appleが策定した、動画を短いセグメントに分割してHTTP経由で配信するストリーミング技術です。
- **FFmpeg（動画や音声の記録・変換・再生を行うオープンソースのマルチメディアフレームワーク）**: 多様な形式の動画や音声をデコード、エンコード、加工するための標準的なツールです。
- **Durable Objects（Cloudflare Workersで強い整合性と永続化状態を提供する分散実行環境）**: 複数の接続やリクエスト間で単一の状態を保持し、セッション調整や中継を行う仕組みです。

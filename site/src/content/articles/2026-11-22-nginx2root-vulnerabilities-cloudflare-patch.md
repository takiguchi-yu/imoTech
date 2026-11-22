---
title: "F5、nginxの脆弱性「nginx2root」5件を公表　遠隔実行の恐れ"
publishedAt: 2026-11-22T10:20:16+09:00
sourceUrl: "https://blog.cloudflare.com/nginx2root/"
sourceTitle: "nginx2root: Five new nginx vulnerabilities, and how Cloudflare protects origins from the worst of them"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/nginx2root/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/nginx2root/"
score: 0
comments: 0
tags: ["nginx", "security", "vulnerability", "cloudflare", "http2"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-22T01:20:16Z
---

## 元記事の要旨

- F5とnginx.orgは、nginxの脆弱性10件を公表しました。そのうちXintリサーチチームが「nginx2root」と名付けた5件は、未認証の攻撃者がworkerのクラッシュや任意のコマンド実行を行えるメモリ破壊の欠陥です。
- 5件の中で最も影響が大きいCVE-2026-123007は、HTTP/2有効時にヒープの境界外読み書きを引き起こす整数オーバーフローで、バージョン1.9.5以降のほぼすべてのリリースが影響を受けます。
- Xintはさらに、LinuxカーネルのSCTP実装にある解放後メモリ利用の欠陥を組み合わせることで、Dockerコンテナ内からホストのroot権限を奪取できる実証に成功したと報告しています。
- Cloudflareは、プロキシ背後にあるサーバーはHTTP/2やHTTP/3をエッジで終端するため主要な攻撃フレームから保護されるとしつつ、nginx 1.30.7や1.31.9への速やかな更新を呼びかけています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **管理下のnginxサーバーで緊急パッチを適用したいとき**: HTTP/2やHTTP/3を有効にした露出サーバーを特定し、最新の1.30.7や1.31.9への更新やSCTPモジュールの無効化を即座に実施する優先度判断に役立ちます。
- **CDN等のリバースプロキシによる防御効果を検証したいとき**: エッジで接続を終端して制御フレームを破棄するプロキシの仕組みが、オリジンへの直接攻撃をどこまで緩和できるかを把握する設計指針になります。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **ASLR（Address Space Layout Randomization、アドレス空間配置のランダム化）**: プログラム実行時にメモリ配置を毎回変え、悪意あるコード実行を妨げるOSの安全機能です。
- **UAF（use-after-free、解放後メモリ利用）**: 一度解放したメモリ領域を誤って参照・操作してしまうことで生じるメモリ破壊の脆弱性です。
- **SCTP（Stream Control Transmission Protocol）**: 複数の通信の流れを束ねて送受信できる、TCPやUDPと並ぶトランスポート層の通信規格です。

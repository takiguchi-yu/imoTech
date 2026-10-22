---
title: "Cloudflare、eMudhra証明書8件の鍵流出に対処　WARPなど更新"
publishedAt: 2026-10-22T09:03:48+09:00
sourceUrl: "https://blog.cloudflare.com/emudhra-certificate-compromise/"
sourceTitle: "8 eMudhra certificates are compromised. Here's what you need to know"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/emudhra-certificate-compromise/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/emudhra-certificate-compromise/"
score: 0
comments: 0
tags: ["security", "cloudflare", "tls", "pki"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-22T00:03:48Z
---

## 元記事の要旨

- Cloudflareは2026年10月19日、広く信頼されていた認証局eMudhraの中間証明書8件の秘密鍵が侵害されたことを把握し、悪用される前に主要サービスの改修を開始しました。
- 侵害された秘密鍵を用いると任意のドメインの偽造証明書を作成できるため、WARPクライアントやCloudflare Tunnelのセキュリティ更新版を速やかに提供しました。
- CDNやZero Trust基盤への対策を適用する一方、独自の証明書ストアやオリジンサーバーを運用する利用者に対し、該当する信頼設定の点検と更新を呼びかけています。
- 開発者に対しては、SDKの更新にとどまらず依存関係にあるHTTPライブラリやOSの信頼ストアを確認し、証明書エラーを検証無効化で回避しないよう求めています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **自社サーバーと外部APIの連携通信を保護したいとき**: 侵害された中間証明書を排除するため、ランタイムやOSの証明書ストアを更新した上で、検証エラーが出ても検証処理を無効化せず証明書を再確認することで安全な接続を維持できます。
- **コンテナ環境からの外部HTTPS通信の安全性を確保したいとき**: Cloudflare ContainersでHTTPS送信の傍受機能を有効化すると、証明書検証の処理が基盤側に委任され、管理インフラの更新による保護を自動的に享受できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **中間証明書（Intermediate Certificate）**: ルート認証局から信頼を引き継ぎ、末端のサーバー証明書を発行するために使われるデジタル証明書です。
- **WebPKI（Web Public Key Infrastructure、公開鍵暗号基盤）**: ウェブブラウザやサーバーが互いの正当性を確認し、暗号化通信を行うための認証局を中心とした信頼モデルです。
- **mTLS（mutual TLS、相互TLS認証）**: クライアントとサーバーの双方が証明書を提示し合い、互いの身元を確認した上で通信を確立する方式です。

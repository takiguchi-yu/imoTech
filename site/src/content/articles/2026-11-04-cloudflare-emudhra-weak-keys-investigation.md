---
title: "Cloudflare、eMudhraの脆弱鍵問題に対するシステム対応と被害状況を公表"
publishedAt: 2026-11-04T10:22:30+09:00
sourceUrl: "https://blog.cloudflare.com/emudhra-patching/"
sourceTitle: "4 real? Tracking exploitation and patching of eMudhra’s weak keys"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/emudhra-patching/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/emudhra-patching/"
score: 0
comments: 0
tags: ["cloudflare", "security", "tls", "pki", "cryptography"]
model: "gemini-3.6-flash"
generatedAt: 2026-11-04T01:22:30Z
---

## 元記事の要旨

- 認証局eMudhraが生成した8つの秘密鍵が極めて単純かつ脆弱であり、公衆証明書から秘密鍵を即座に復元して偽造証明書を発行できる深刻な脆弱性が発覚した。
- Cloudflareは発覚直後にPingoraを含む主要システムへパッチを適用し、脆弱な鍵を用いた接続を拒否する措置を数時間で完了させた。
- 通信ログの解析では、悪用やテスト目的とみられる約2万2,000件の接続試行を検知し、脆弱性の公表から1時間以内に偽造証明書が作られた形跡があったが、中間攻撃の被害は確認されていない。
- チャレンジページを活用した5,000万件のプローブ調査の結果、最新ブラウザでは修正が進む一方、ボットやAndroid WebViewなどの埋め込みブラウザでは30〜40％が依然として脆弱な鍵を信頼していることが判明した。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **自社サービスでTLS証明書の検証処理を実装・運用するとき**: 認証局の秘密鍵漏洩や脆弱性発生時に備え、証明書透明性（CT）の強制やカスタムログによる不正ハンドシェイクの拒否・検知ロジックをプロキシ層へ組み込む判断に役立ちます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **CA（certificate authority、認証局）**: 通信の暗号化に使うデジタル証明書を発行し、サイトやサービスの身元を証明する第三者機関。
- **SNI（Server Name Indication）**: TLS通信のハンドシェイク時に、クライアントが接続したいホスト名をサーバーに伝える仕組み。
- **Android WebView**: Androidアプリ内でWebページを表示するために使われる、OS提供の組み込みブラウザコンポーネント。

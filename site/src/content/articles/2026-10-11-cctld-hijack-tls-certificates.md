---
title: "Googleなど、3つのccTLD乗っ取りで偽TLS証明書を発行される被害"
publishedAt: 2026-10-11T09:18:22+09:00
sourceUrl: "https://arstechnica.com/security/2026/10/hackers-obtain-counterfeit-tls-certificates-for-google-and-other-large-services/"
sourceTitle: "Hackers obtain counterfeit TLS certificates for Google and other large services"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=49988230"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/arstechnica.com/security/2026/10/hackers-obtain-counterfeit-tls-certificates-for-google-and-other-large-services/"
score: 140
comments: 51
tags: ["security", "dns", "tls", "pki"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-11T00:18:22Z
---

## 元記事の要旨

- 攻撃者が「.gh」「.sl」「.as」の3つのccTLDを侵害し、特定ドメインの権威DNSレコードを改ざんして不正なTLS証明書を取得したとGoogleが発表しました。
- DNSレコードの制御権を奪われたことで自動ドメイン所有確認が突破され、Googleや複数の世界的大手ブランドのドメインを対象に不正な証明書が発行されました。
- 不正な証明書の所持は通信のなりすましを可能にするため、GoogleはChromeを更新して該当証明書をブロックし、認証局と連携して失効手続きを進めました。
- Googleはドメイン所有者に対し、証明書の透明性（CT）ログの継続的な監視や、キャッシュ悪用を防ぐ厳格なCAAレコードの設定を呼びかけています。

## 議論の論調

### DNS乗っ取り時にCAAレコードで防御できるか

攻撃者が権威DNSを掌握した場合、認証局を制限するCAAレコード自体を削除または改ざんできるため、CAAだけでは不正発行を阻止できないという指摘がなされました。これに対し、長いキャッシュ期間の設定やACMEアカウントのバインディングを行っていれば一定の抑止効果が期待できるという反論も交わされています。

### ログによる早期検知とWeb PKIの脆弱性

今回の不正発行はCertificate Transparency（CT）ログのおかげで早期に検知・対処されたとして現行エコシステムを評価する声があります。一方で、DNSに過度に依存するWeb PKIの構造的な弱点を懸念する意見や、数時間から数日の悪用であっても巨大サービスでは膨大な利用者に被害が及ぶという指摘も上がっています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **自社サービスのドメインセキュリティ対策を見直すとき**: 記事で推奨されたCTログの常時監視と厳格なCAAレコード設定を導入することで、万一の不正なTLS証明書発行を早期に検知し、未承認の認証局による発行リスクを下げられます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **ccTLD（country code top-level domain、国別コードトップレベルドメイン）**: 国や地域ごとに割り当てられる最高位のドメイン名です（「.jp」や「.gh」など）。
- **CAA（Certification Authority Authorization、認証局認証）**: そのドメインのTLS証明書を発行できる認証局（CA）をDNSレコードで指定する仕組みです。
- **CT（Certificate Transparency、証明書の透明性）**: 不正なTLS証明書の発行を誰でも迅速に監視・検知できるように公開される監査ログの仕組みです。

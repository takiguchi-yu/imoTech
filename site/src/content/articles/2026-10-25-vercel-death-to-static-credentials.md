---
title: "Vercel、OIDC推進ツールを公開　SaaSの対応率8.4%からの脱却へ"
publishedAt: 2026-10-25T08:16:33+09:00
sourceUrl: "https://vercel.com/blog/death-to-long-lived-static-credentials"
sourceTitle: "Death to long-lived static credentials"
source: "vercel-blog"
discussionUrl: "https://vercel.com/blog/death-to-long-lived-static-credentials"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/vercel.com/blog/death-to-long-lived-static-credentials"
score: 0
comments: 0
tags: ["vercel", "security", "oidc", "authentication"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-24T23:16:33Z
---

## 元記事の要旨

- APIキーやDBパスワードなどの長寿命な静的認証情報は、漏洩時のリスクが高く鍵のローテーションにも莫大な工数がかかるため、セキュリティ上の深刻な課題となっています。
- Vercelが1,000社超のSaaSベンダーを調査したところ、OIDCなどの安全な認証方式に対応している企業は8.4%にとどまり、普及の遅れが浮き彫りになりました。
- Vercelは静的キーの廃止を掲げ、プロバイダ向けに信頼ポリシーとトークン検証を支援する「OIDC UI」の提供や、環境変数を介さず安全に認証する連携基盤の拡充を進めています。
- トークン取得に伴うレイテンシ増加を抑えるため、関数実行時のヘッダー配布やキャッシュ機構を導入し、開発者が性能を落とさずに短命トークンへ移行できる環境を整備しています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **Vercel上のアプリからクラウドDBへ安全に接続したいとき**: Vercelが発行する短命なOIDCトークンをクラウドの一時クレデンシャルへ交換できるため、静的な接続キーを環境変数に保持するリスクを排除できます。
- **自社SaaSのAPIに短命トークン認証を導入したいとき**: shadcn/uiレジストリとして提供される「OIDC UI」を利用することで、信頼ポリシー設定画面やサーバー側のトークン検証コードを一から開発せずに組み込めます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **OIDC（OpenID Connect、認証のための標準規格）**: 短命なIDトークンを用いてシステムの身元を証明し、安全に認証を行うための標準規格です。
- **静的認証情報（static credentials）**: 有効期限が設定されていないか長期にわたり使い回される、APIキーやパスワードなどの秘密情報です。
- **キーローテーション（key rotation）**: 漏洩リスクを抑えるため、システムで利用しているAPIキーなどを定期的に新しい値へ更新する作業です。

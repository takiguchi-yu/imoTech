---
title: "Mercor社、AIバッチ処理を12時間から2時間に短縮　Vercel活用で"
publishedAt: 2026-11-06T10:34:20+09:00
sourceUrl: "https://vercel.com/blog/how-mercor-ships-internal-apps-and-billions-of-production-tokens-on-one-platform"
sourceTitle: "How Mercor ships internal apps and billions of production tokens on one platform"
source: "vercel-blog"
discussionUrl: "https://vercel.com/blog/how-mercor-ships-internal-apps-and-billions-of-production-tokens-on-one-platform"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/vercel.com/blog/how-mercor-ships-internal-apps-and-billions-of-production-tokens-on-one-platform"
score: 0
comments: 0
tags: ["vercel", "ai", "cloud", "infrastructure"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-06T01:34:20Z
---

## 元記事の要旨

- AIモデル評価を手がけるMercorは、需要急増時のレート制限によってバッチ処理が12時間を超え、顧客に対する24時間以内の納期を圧迫する課題を抱えていました。
- 同社はVercel AI Gatewayを導入し、プロバイダ間のフェイルオーバーを活用することで、レート制限を回避してバッチ処理時間を2〜3時間へと大幅に短縮しました。
- 導入後わずか10日間で1800万件のリクエストと630億トークンを処理し、有効期限や予算上限を設定した個別キーによりエンジニアの安全な実験環境を確立しました。
- さらにVercel Passportを活用し、ビジネス部門が構築した約2000件の案件用アプリに対して、外部専門家へのアクセス権限を即座に付与・解除できる仕組みを整えました。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **外部AIモデルのレート制限でバッチ処理が遅延しているとき**: AI Gatewayのフェイルオーバー機能により、特定プロバイダの上限超過時に別プロバイダへ自動で振り替えることで、長時間の待機列を防ぎ納期遅延を回避できます。
- **案件ごとに社外専門家向けツールの環境を素早く配備したいとき**: Vercel PassportとIdPグループを連携させることで、プロジェクトごとに個別の認証基盤を組むことなく、一時的な個別アプリへの権限管理を即座に完了できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **IdP（identity provider、IDプロバイダ）**: ユーザーの認証情報を一元管理し、各種サービスへの安全なシングルサインオン連携を提供する基盤です。
- **トークン（token、モデルの処理単位）**: 大規模言語モデルがテキストを解釈・生成する際に扱う最小の文字単位で、課金や利用制限の基準となります。

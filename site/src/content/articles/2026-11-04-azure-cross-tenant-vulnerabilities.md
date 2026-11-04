---
title: "Azure の Logic Apps、テナント間の不正アクセスを許す複数の脆弱性が発見される"
publishedAt: 2026-11-04T10:30:39+09:00
sourceUrl: "https://www.binarysecurity.no/posts/2026/10/one-root-case"
sourceTitle: "Azure's Weakest Link – Five Full Cross-Tenant Compromises"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50301854"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/www.binarysecurity.no/posts/2026/10/one-root-case"
score: 339
comments: 64
tags: ["azure", "security", "cloud", "vulnerability"]
model: "gemini-3.5-flash-lite"
generatedAt: 2026-11-04T01:30:39Z
---

## 元記事の要旨

- Azure Logic Apps の API Connections において、テナントの境界を越えて任意のバックエンドにアクセスできる深刻な脆弱性が発見された。
- ARM REST API のエンドポイントを悪用し、不正なパス構築によって他テナントの Key Vault や Azure SQL データベースにアクセスが可能になる。
- 最初の修正に対する不十分なブラックリスト方式の対策をバイパスしたうえ、さらに文書化されていない複数の未知のエンドポイントが同様に脆弱であることを確認している。

## 議論の論調

### 相次ぐセキュリティ上の不備に対する強い懸念

Azure におけるテナント分離の不備や、不十分な修正が繰り返されている現状について、クラウドの信頼性に関わる深刻な問題であるとして批判的な意見が多く寄せられている。

### 脆弱性が多発する背景と企業の採用動向

Microsoft 製品全般における品質管理やサポート体制への不満が示される一方で、大規模な企業調達や既存の契約関係、国内データセンターの存在といった実務上の理由から、依然として多くの企業が Azure を選ばざるを得ない現実が指摘されている。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **Azure の API Connections を用いて外部サービスやデータベースと連携する環境を構築したいとき**: API Connections のアーキテクチャや認証トークンの扱いに不備があるとクロステナントの不正アクセスの温床になるため、依存するマネージドサービスのアクセス権限が適切にスコープされているか確認するために本件の検証手法を参照できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **ARM（Azure Resource Manager）**: Azure のリソース管理とデプロイを行うための管理レイヤー。API を通じてインフラストラクチャの操作や構成管理を行う。
- **APIM（API Management）**: API の公開やルーティング、認証を管理するための Azure のマネージドサービス。
- **Key Vault**: クラウド上のアプリケーションで使用される暗号化キーやシークレット情報を安全に保管するための Azure のサービス。

---
title: "Cloudflare、耐量子匿名認証プロトコル「MOLE」の概念を公開"
publishedAt: 2026-11-09T09:53:55+09:00
sourceUrl: "https://blog.cloudflare.com/vole-mole/"
sourceTitle: "The post-quantum future of web privacy"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/vole-mole/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/vole-mole/"
score: 0
comments: 0
tags: ["cryptography", "privacy", "post-quantum", "cloudflare"]
model: "gemini-3.6-flash"
generatedAt: 2026-11-09T00:53:55Z
---

## 元記事の要旨

- Privacy Passなどの匿名トークン技術は、Webサイトのアクセス制限においてプライバシー保護とスパム防止を両立してきましたが、従来のRSAや楕円曲線暗号は将来の量子コンピュータにより無効化される脅威に晒されています。
- 量子コンピュータが登場してもトークンの発行と利用の非リンク性自体は保たれますが、暗号の解読によってトークンの偽造が可能になり、レート制限などのセキュリティ機能が回避される恐れがあるため移行が必要です。
- この課題に対しCloudflareは、発行者の識別子を隠蔽しつつ複数クライアントの公平な評価を可能にする次世代技術「MOLE（Moderation Of unLinkable Endorsements）」の構想を発表しました。
- 耐量子暗号への移行では署名サイズの大幅な増大が主な課題であり、既存の代替ではなくシステム全体を再構築してプロトコルに柔軟性を持たせるアプローチが求められています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **耐量子暗号化を見据えて匿名認証基盤を設計するとき**: MOLEの概念を取り入れることで、将来の量子計算の脅威に備えつつ、クライアントの属性や発行者を特定させないプライバシーに配慮したアクセス制限システムを検討できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **Privacy Pass（プライバシー・パス）**: ユーザーのプライバシーを保護しながら、Webサイトがスパムや過剰アクセスを防ぐために利用する匿名認証プロトコル。
- **ブラインド署名（blind signature）**: 署名者がメッセージの内容を知ることなく署名を発行し、後から検証可能にする暗号技術。
- **Q-day（キュー・デイ）**: 現在使われている主要な公開鍵暗号を解読できる実用的な量子コンピュータが実現すると予測される未来の日のこと。

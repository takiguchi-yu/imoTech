---
title: "OpenAI のアドトラッキング機構と、AI チャットサービスにおけるプライバシーの是非"
publishedAt: 2026-09-22T00:03:51+09:00
sourceUrl: "https://www.buchodi.com/chatgpt-now-knows-what-you-do-on-other-websites-via-ad-collector/"
sourceTitle: "ChatGPT now knows what you do on other websites via ad collector"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=49776729"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/www.buchodi.com/chatgpt-now-knows-what-you-do-on-other-websites-via-ad-collector/"
score: 735
comments: 365
tags: ["openai", "privacy", "tracking", "chatgpt", "adtech"]
model: "gemini-3.5-flash-lite"
generatedAt: 2026-09-21T15:03:51+00:00
---

## 元記事の要旨

- OpenAI は広告収集用のカスタムクッキー「__obi」を使用し、ユーザーの外部ウェブサイトでの行動履歴を ChatGPT アカウントに結びつけている。
- 広告主がサイトに設置したトラッキング用ピクセルや SDK を介して、__obi クッキーが OpenAI のサーバーへ送信される仕組みになっている。
- データ送信時には、フォームに入力されたメールアドレスや電話番号などがハッシュ化され、位置情報や閲覧パスなども収集対象となっている。
- このトラッキングは、有料プランの利用者や、マーケティングを拒否してアナリティクスのみを許可しているユーザーに対しても適用される。

## 議論の論調

### 既存の広告技術との比較と、AI製品への導入に対する違和感

GoogleやFacebookなどのプラットフォームが長年行ってきた手法と本質的には同じであるという指摘がある一方で、SNSとは異なり有料で利用しているサービスや、機微な情報を打ち明けることの多いAIチャット製品にこの仕組みが組み込まれていることに対して強い不快感や懸念を示す意見が多く見られる。

### ビジネスモデルの持続可能性と広告収入の必要性

多額の資金を投じられているAIサービスを維持するためには広告収入やデータ活用が避けられないという意見や、広告なしの無料プランが存在しない以上、何らかの形でユーザーがコストを支払うのは当然であるという見解が示されている。

### ブラウザによる保護機能とユーザー側の自衛手段

Firefox、Brave、Safariなどのようにサードパーティクッキーやストレージを分離・ブロックするブラウザを利用することや、DNSブロッカーを活用してトラッキングドメインへの通信を防ぐことが有効な対抗策として議論されている。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

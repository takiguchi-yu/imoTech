---
title: "Mozilla、iOSで代替エンジン導入が3年間ゼロの実態を公表"
publishedAt: 2026-11-28T12:28:30+09:00
sourceUrl: "https://blog.mozilla.org/en/mozilla/internet-policy/apple-ios-browser-engine-rules/"
sourceTitle: "Why there are still no non-WebKit browsers on iOS"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50575644"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.mozilla.org/en/mozilla/internet-policy/apple-ios-browser-engine-rules/"
score: 604
comments: 334
tags: ["apple", "mozilla", "webkit", "ios", "gecko"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-28T03:28:30Z
---

## 元記事の要旨

- EUのデジタル市場法（DMA）施行以降、欧州でFirefoxの利用は倍増したものの、iOS上では依然としてWebKit以外のブラウザエンジンの採用が阻まれています。
- AppleはEUや日本で代替エンジンの利用条件を定めましたが、条件が極めて厳しく、規制導入から最長3年近くが経過しても非WebKitブラウザは1つも公開されていません。
- Mozillaによると、Geckoエンジンを採用するには既存アプリの更新ではなく別アプリの配信が必要となり、利用者に手動移行を強いる仕様などが参入の障害になっています。

## 議論の論調

### Appleが課す移行の摩擦や開発制約への批判

既存アプリの更新を認めず別アプリとしての公開を強制する仕様や、EU域外からの開発・検証を著しく困難にしているAppleの条件設計に対して、独禁法遵守を形式的なものにとどめていると批判する意見が多く寄せられました。ユーザー自身がブックマークや設定の移行作業を強いられることによる離脱を狙った、意図的な摩擦ではないかとの指摘もなされています。

### WebKit強制がもたらす独占阻止と標準化への懸念

AppleによるWebKitの強制が、結果的にGoogleのChromiumによるWeb標準の独占を防ぎ、ウェブの多様性を守る防波堤になっていると評価する声がありました。一方で、Safariによる実装遅延や機能制限がPWAの普及や技術標準の進展を阻んでおり、かつてのInternet Explorerのような停滞を生んでいると反論する意見もあり、賛否が分かれました。

### セキュリティ確保と事業収益をめぐる動機への見解

Appleが独自エンジンの参入を阻む理由として、JITコンパイルに伴う脆弱性やセキュリティリスクを最小化するためだとする説明がある一方で、Googleから得ている年間約200億ドルの検索エンジン契約料や、App Storeが徴収する手数料ビジネスを守るための囲い込み策に過ぎないのではないかとの疑念も多く語られました。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **WebKit**: Appleが開発するブラウザエンジン。iOS上のブラウザに長年採用が義務付けられていました。
- **DMA（Digital Markets Act、デジタル市場法）**: 巨大IT企業の市場支配を抑制し、公正な競争環境を確保するためにEUが定めた包括的な規制です。
- **Gecko**: Mozillaがオープンソースで開発する、Firefoxの描画や処理を担うブラウザエンジンです。

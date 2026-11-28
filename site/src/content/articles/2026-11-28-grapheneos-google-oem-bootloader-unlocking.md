---
title: "GrapheneOS、Googleが端末各社に解除制限を要求と主張"
publishedAt: 2026-11-28T12:33:19+09:00
sourceUrl: "https://grapheneos.social/@GrapheneOS/117645038299496084"
sourceTitle: "Google is pushing OEMs against GrapheneOS and bootloader unlocking"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50570479"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/grapheneos.social/@GrapheneOS/117645038299496084"
score: 512
comments: 212
tags: ["android", "grapheneos", "google", "security", "smartphones"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-28T03:33:19Z
---

## 元記事の要旨

- オープンソースのモバイルOS「GrapheneOS」の開発陣は、Googleがスマートフォン製造企業（OEM）に対してブートローダーのアンロック防止を働きかけていると主張しました。
- GrapheneOS側の説明によると、Googleは端末各社に対して代替OSプロジェクトと協力していないかを繰り返し確認し、アンロック機能の提供をやめるよう圧力をかけているとされています。
- ブートローダーの制限が厳格化された場合、ユーザーが端末を購入してもサードパーティ製OSの導入や独自ファームウェアの書き換えが難しくなり、所有権の行使が狭まる懸念が浮上しています。

## 議論の論調

### 独占的地位の濫用として司法当局や規制機関へ通報すべきとの意見

Googleによる端末制御の強化は市場の寡占を利用した反競争的行為であるとし、米国の州司法長官や欧州の競争当局（DMA担当チームなど）に通報して調査を求めるべきだという声が上がっています。以前の独占禁止法違反事例を挙げ、ハードウェアの囲い込みを阻止するためには法的介入が不可欠だと主張されています。

### 告発の根拠となる証拠の提示を求める慎重な受け止め

GrapheneOS側の主張に共感しつつも、相手企業からの働きかけや脅迫を示す具体的な証拠が提示されていない点を懸念する意見があります。根拠を示さなければ感情的な注目集めと受け取られかねず、大企業側が本当に特定のカスタムOSを脅威と見なして狙い撃ちにしているのか疑問視する見方も出ています。

### 独自OSへの移行や脱Googleの難しさを指摘する声

端末の支配から逃れるためにGrapheneOSなどの代替OSを使いたいと望む声がある一方、対応端末が高価なモデルに限られる点や、Google Play Integrityなどの認証機構によって銀行や公的アプリが動かなくなる実用上の壁が挙げられています。セキュリティと利便性のトレードオフが依然として大きいと議論されています。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **ブートローダー（bootloader）**: 端末起動時にOS本体をメモリに読み込む基礎プログラム。これを解除（アンロック）することで別のOSを導入できます。
- **OEM（original equipment manufacturer、相手先商標製品製造企業）**: 自社ブランドまたは他社委託でハードウェア製品を製造する企業。本稿ではスマートフォン端末メーカーを指します。
- **Play Integrity（旧SafetyNet、端末完全性検証API）**: 端末が改変されていない正規環境かをGoogleが遠隔検証する機能。銀行などのアプリで起動制限に使われます。

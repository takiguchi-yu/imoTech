---
title: "OOSEX GANG、Android機でiOS 16.5を動かす「HackiOS」公開"
publishedAt: 2026-10-25T08:20:42+09:00
sourceUrl: "https://github.com/oosexgang/hackios-xnu-kernel"
sourceTitle: "Run full iOS 16.5 firmware on Android Devices"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50196718"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/oosexgang/hackios-xnu-kernel"
score: 528
comments: 194
tags: ["ios", "android", "xnu", "reverse-engineering", "kernel"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-24T23:20:42Z
---

## 元記事の要旨

- 開発者グループ「OOSEX GANG」は、AndroidスマートフォンやQEMU上で、AppleのオープンソースXNUカーネルおよびiOS 16.5のユーザー空間環境を動作させる研究プロジェクト「HackiOS」を公開しました。
- システムは内蔵ストレージを書き換えずRAM上で稼働し、独自のEFIローダーやオープンソースのUEFI、代替ドライバを組み合わせて実現されており、端末を再起動すれば通常のAndroid環境へ復帰します。
- POCO X5 Pro 5G上ではタッチ操作、画面描画、Wi-Fi通信、標準アプリの動作などが確認されていますが、セルラー通信やBluetooth、充電、Secure Enclaveを要する認証などは未対応です。

## 議論の論調

### 技術的快挙を称賛しつつ実用上の制限を指摘する意見

独自ハードウェアへのiOS移植という高度なリバースエンジニアリング技術を純粋に楽しむ声が多く寄せられました。一方で、セルラー機能や充電が動作しない点、Secure Enclaveの欠如によりApp StoreやApple ID関連の機能が使えず実用的な日常利用には程遠い現状を冷静に指摘する意見も見られます。

### 偽造端末の増加やAppleによる法的対応への懸念

Android端末上で本物のiOSが動作することで、精巧な偽造iPhoneが出回るのではないかと警戒する意見が上がりました。また、Appleが著作権保護や商標などの観点からDMCA通知などの強力な法的措置をとってプロジェクトを差し止めるのではないかと予想する声も多く見られます。

### 求められている移植の方向性や利用価値を巡る議論

Android端末でiOSを動かすことへの驚きがある一方で、安価な端末でiOSの音楽制作アプリなどを動かしたい層からの関心も集まりました。しかし同時に、ハードウェア性能が高いiPhone上でオープンなAndroidやLinuxを動かすことこそが真に求められているのではないかという反論も交わされています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **iOS内部構造やセキュリティの検証を行いたいとき**: 実機に書き込まずRAM上やQEMUでiOS 16.5環境を一時起動できるため、専用の脱獄端末を用意せずにカーネルログの採取やユーザー空間の挙動調査が手軽に行えます。
- **非Mac環境のCIでiOS動作確認を試みたいとき**: QEMU上でiOSユーザー空間を動かせる仕組みを活用することで、macOSランナーを用いずにLinuxサーバー上でiOSアプリの簡易なテスト自動化を模索できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **XNU**: Appleが開発するDarwin OSの中核を担うカーネル。MachやBSDなどをベースに構成されています。
- **UEFI（Unified Extensible Firmware Interface）**: OSを起動するための標準的なファームウェア仕様。PCや一部のスマートフォンで利用されます。
- **Secure Enclave**: Apple製品に搭載されている、生体認証や暗号化鍵などの機密情報を安全に管理する専用セキュリティチップ。
- **fastboot**: Android端末のブートローダーと直接通信し、パーティションの書き換えや一時起動を行うプロトコルおよびツール。

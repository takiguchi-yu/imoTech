---
title: "DiPlay、BYD車向けCarPlay受信アプリを公開　ドングル不要で動作"
publishedAt: 2026-10-12T09:35:51+09:00
sourceUrl: "https://github.com/shihabal3amri/DiPlay"
sourceTitle: "DiPlay: Independent CarPlay receiver for compatible Android head units. Wired and wireless public preview."
source: "github"
discussionUrl: "https://github.com/shihabal3amri/DiPlay"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/shihabal3amri/DiPlay"
score: 9351
comments: 0
tags: ["android", "carplay", "byd", "reverse-engineering"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-12T00:35:51Z
---

## 元記事の要旨

- DiPlayは、BYDなどのAndroid車載機で動作する独立したCarPlayレシーバーアプリです。追加のドングルやiPhoneの脱獄、Macや外部の認証サーバーを必要とせず、有線USB接続および無線接続の両方で利用できます。
- 車載機がAPKの直接インストールに対応している必要があり、Android 7.1以降をサポートします。無線接続ではWi-Fi Directや車載ホットスポット、同一ローカルネットワーク経由での通信に対応しています。
- 本アプリはAppleの公式認定製品ではなく、公開ファームウェアから抽出された実験的なアクセサリ識別情報を内包しています。そのため、将来のiOS更新による影響や車載機ごとの完全な互換性は保証されていません。
- バージョン0.2.18では、USB接続切断問題の解消、ステアリングスイッチによる曲送り対応、QRコードを用いた設定のバックアップと復元、MediaTek向け低遅延デコードなどの機能追加が行われました。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **BYD車の車載機でCarPlayを有線や無線で利用したいとき**: 市販の変換ドングルを買い足すことなく、車載機に直接APKを導入するだけで有線USBや車内Wi-Fiを通じたCarPlay接続が可能になります。
- **車載機のステアリングボタンで音楽再生を操作したいとき**: 0.2.18でステアリングの次へ・前へボタンの直接制御が強化されたため、CarPlay画面上でハンドルから曲の切り替えが行えます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **HUD（head-up display、ヘッドアップディスプレイ）**: フロントガラスなどに速度やナビゲーションの案内矢印を投影して表示する車載機器です。
- **APK（Android application package、Androidアプリパッケージ）**: Android OSにアプリを直接配布・インストールするためのファイル形式です。
- **MFi（Made for iPhone/iPad/iPod）**: Appleが外部機器向けに提供する、同社製品との互換性や安全性を保証する公式の認定プログラムです。

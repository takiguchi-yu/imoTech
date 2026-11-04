---
title: "開発者、SwitchゲームをiOSやMacでネイティブ実行する「nxnative」公開"
publishedAt: 2026-11-04T10:27:10+09:00
sourceUrl: "https://github.com/seedds/nxnative"
sourceTitle: "nxnative: Switch games running natively on iPhone, iPad and Mac: an NSP folder becomes an unsigned IPA (NSO rewriter, Horizon HLE host, NVN→Metal)"
source: "github"
discussionUrl: "https://github.com/seedds/nxnative"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/seedds/nxnative"
score: 11884
comments: 0
tags: ["ios", "macos", "switch", "metal", "graphics"]
model: "gemini-3.6-flash"
generatedAt: 2026-11-04T01:27:10Z
---

## 元記事の要旨

- 「nxnative」は、Nintendo SwitchのゲームファイルをiPhoneやiPad、Mac上で動作する形式へ変換するツールです。エミュレータではなく、ゲームのプログラムコードをAppleのチップ上でネイティブに直接実行します。
- 描画処理にはSwitch独自のAPIからMetalへの変換レイヤーやSPIRV-Crossなどが活用されており、グラフィックスはMetal上で再構築されます。これにより高い描画パフォーマンスを実現しています。
- 変換作業にはMac環境やprod.keysが必要であり、スクリプトを実行してIPAファイルやMac用アプリを生成します。iOS端末への導入にはAltStoreなどのサイドロード用ツールを利用します。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **所有するSwitchゲームをiPhoneやMacで遊びたいとき**: nxnativeはゲームコードをAppleのチップ上で直接実行し、グラフィックスをMetalへ変換するため、エミュレータを使わずに手持ちのiOSデバイスやMacでネイティブ動作させることができます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **IPA（iOS App Store Package、iOSアプリの配布用パッケージ）**: iOSやiPadOS上で動作するアプリケーションを格納するための標準ファイル形式で、特定のツールを用いて端末へ直接インストール可能です。
- **Metal（Apple独自のローレベルグラフィックスAPI）**: Apple製デバイスのGPUを高速かつ効率的に制御するためのAPIです。本ツールではSwitchのGPU命令をMetal向けに変換して描画します。

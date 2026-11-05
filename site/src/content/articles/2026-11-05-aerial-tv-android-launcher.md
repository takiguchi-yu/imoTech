---
title: "Aerialを公開　Android TV向けの広告なしtvOS風ランチャー"
publishedAt: 2026-11-05T10:45:58+09:00
sourceUrl: "https://github.com/pengchujin/aerial-tv"
sourceTitle: "aerial-tv: 给国产电视的一块干净桌面：参照 tvOS 设计的开源 Android TV 桌面，没有广告，开机自动接管。A tvOS-style launcher for Xiaomi, TCL and other China-market TVs."
source: "github"
discussionUrl: "https://github.com/pengchujin/aerial-tv"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/pengchujin/aerial-tv"
score: 9633
comments: 0
tags: ["android", "android-tv", "open-source", "launcher"]
model: "gemini-3.6-flash"
generatedAt: 2026-11-05T01:45:58Z
---

## 元記事の要旨

- 「Aerial」は、Apple TV（tvOS）風のデザインを採用したオープンソースのAndroid TV向けホーム画面アプリです。広告やおすすめ配信を排除し、ユーザーが使用するアプリや壁紙、スクリーンセーバーのみのシンプルな画面構成を提供します。
- Xiaomi、TCL、Sonyなどの中国市場向けテレビやテレビボックス、プロジェクターに対応しています。root化は不要で、ADBコマンドを利用した設定により、テレビの起動時やスリープ解除時に自動で本画面を起動させる運用が可能です。
- スマートフォンでテレビ画面のQRコードを読み取ることでアプリの並べ替えや名称変更が行える機能や、4K Dolby Visionに対応した空撮スクリーンセーバー機能、入力切替や音量調整を行えるコントロールセンターを備えています。
- Android 5.0以上に対応した標準版に加えて、旧型の端末向けに機能を絞ったAndroid 4.0〜4.4対応の「Aerial Lite」テスト版も用意されており、幅広い世代の端末で導入が考慮されています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **スマートテレビの広告表示や複雑な画面を改善したいとき**: root化を行わずにADB経由でデフォルトのホームアプリとして設定できるため、メーカー固有の広告や推奨動画を完全に除去し、シンプルな操作環境を実現できます。
- **テレビのアプリ配置や入力源の設定を直感的に整理したいとき**: テレビ画面に表示されるQRコードをスマートフォンで読み取ることで、アプリの並べ替えや名前変更、接続した各種ゲーム機などのアイコン設定をスマホ側から容易に行えます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **ADB（Android Debug Bridge、Androidデバッグ橋）**: パソコンやスマホからAndroid端末へコマンドを送信し、アプリの設置やシステム設定の書き換えなどを行うための開発用通信ツールです。
- **tvOS（Apple TV用オペレーティングシステム）**: Appleが提供するメディアプレーヤー向けのOSで、シンプルでグリッド感のある洗練されたUIや空撮スクリーンセーバーなどが特徴です。
- **Dolby Vision（ドルビービジョン、ハイダイナミックレンジ映像規格）**: 映像の明暗差や色彩の表現力を飛躍的に向上させるHDR規格の一つで、対応テレビにおいて豊かな質感と鮮明な映像表現を可能にします。

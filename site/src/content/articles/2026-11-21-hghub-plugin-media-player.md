---
title: "開発者が「HGhub」公開　Tauri 2製プラグイン式動画再生ソフト"
publishedAt: 2026-11-21T11:14:14+09:00
sourceUrl: "https://github.com/Minireel/HGhub"
sourceTitle: "HGhub: Plug-in media player"
source: "github"
discussionUrl: "https://github.com/Minireel/HGhub"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/Minireel/HGhub"
score: 10459
comments: 0
tags: ["tauri", "rust", "react", "media-player"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-21T02:14:14Z
---

## 元記事の要旨

- HGhubは、JavaScriptプラグインを導入して多様なコンテンツ配信元を統合し、同一の操作画面で検索・視聴・管理を行えるようにするオープンソースの動画プレーヤーです。
- アプリ本体にはコンテンツ配信元やプラグイン一覧を内蔵せず、ユーザー自身がURLやファイルからプラグインを追加して利用する設計となっており、HGhubへのアカウント登録も不要です。
- クライアントはRust、Tauri 2、React、TypeScriptで構築されており、現在はWindowsとAndroidへの対応に注力しながら早期開発が進められています。
- ライセンスにはPolyForm Noncommercial 1.0.0が採用されており、広告収入や有料機能を含む一切の商業利用が明確に禁止されています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **複数サービスの動画配信を一つの再生環境で整理したいとき**: 外部プラグインにより各配信元の検索や再生をまとめられ、視聴履歴やローカルのお気に入りリストも同一の画面から一括管理できます。
- **自前の動画配信サーバー用クライアントを用意したいとき**: HPPプラグイン仕様に従って独自のJavaScriptプラグインを作成することで、HGhubの再生・UI機能を活かした専用ビューアとして利用できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **Tauri（タウリ）**: RustとWebフロントエンド技術を組み合わせ、軽量なデスクトップやモバイル向けアプリを構築するためのフレームワークです。
- **HLS（HTTP Live Streaming、動画配信プロトコル）**: 動画を小さなファイルに分割し、HTTP経由で効率的に順次配信・再生を行うために広く使われているストリーミング技術規格です。

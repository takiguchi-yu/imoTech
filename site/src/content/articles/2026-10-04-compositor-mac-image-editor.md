---
title: "開発者が画像編集ソフト「Compositor」公開　PSD対応のMac専用OSS"
publishedAt: 2026-10-04T08:49:21+09:00
sourceUrl: "https://github.com/robbietilton/Compositor"
sourceTitle: "Compositor: The Photoshop alternative for Mac"
source: "github"
discussionUrl: "https://github.com/robbietilton/Compositor"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/robbietilton/Compositor"
score: 7307
comments: 0
tags: ["macos", "opensource", "image-editor", "photoshop"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-03T23:49:21Z
---

## 元記事の要旨

- Photoshopの高額さや既存ツールの操作感への不満から、同等の合成・現像ワークフローを再現する完全無料のオープンソース画像編集ツール「Compositor」が開発されました。
- レイヤー構造やマスク、Photoshop互換のブレンドモード、Camera Rawフィルター、コンテンツに応じた塗りつぶしなど、画像合成に必要な主要機能を幅広く網羅しています。
- 8ビットRGBのPSDおよびPSBファイルのインポートに対応しており、フォルダーやマスク、一部テキストの編集性を維持したまま読み込んで作業を継続できます。
- プロジェクトファイルはPNGレイヤーとマニフェストで構成され、AIエージェントやスクリプトから直接変更を加え、開いているプロジェクトへリアルタイムに反映させることが可能です。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **Mac環境でPSDファイルを手軽に編集・確認したいとき**: 8ビットRGBのPSDやPSBの読み込みに対応し、レイヤーやマスクの構造を維持できるため、PhotoshopのライセンスがないMac環境でも手軽に修正や書き出しが行えます。
- **AIや自動化スクリプトで画像合成を自動化したいとき**: プロジェクトがPNGとマニフェストで構成され外部から直接操作できるため、生成AIエージェントによるレイヤー配置や画像編集処理のパイプラインを容易に構築できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **Camera Raw（カメラRAW現像フィルター）**: 写真の色調や露出、カラーグレーディング、光学補正などを非破壊で精密に調整する機能です。
- **コンテンツに応じた塗りつぶし（Content-Aware Fill）**: 画像内の不要物を消去したり背景を拡張したりする際、周囲の絵柄を解析して自然に補完する機能です。

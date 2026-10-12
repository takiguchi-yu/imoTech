---
title: "開発者、Rust製現像アプリ「LightCraft」公開　Lightroomを再実装"
publishedAt: 2026-10-12T09:35:04+09:00
sourceUrl: "https://github.com/storytold/lightcraft"
sourceTitle: "lightcraft: LightCraft: An open-source non-destructive photo editor written by scratch in pure Rust"
source: "github"
discussionUrl: "https://github.com/storytold/lightcraft"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/storytold/lightcraft"
score: 10193
comments: 0
tags: ["rust", "photo-editing", "raw", "mcp", "wasm"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-12T00:35:04Z
---

## 元記事の要旨

- LightCraftは、Adobe LightroomをPure Rustでクリーンルーム再実装したオープンソースの写真ライブラリ兼RAW現像ツールです。MITおよびApache-2.0のデュアルライセンスで提供されています。
- macOS、Windows、Linuxのネイティブ環境に対応するほか、WebAssemblyによりブラウザでも動作します。さらにMCP（Model Context Protocol）経由でAIエージェントからの自動操作も可能です。
- 編集は原画を改変しない非破壊方式で、32ビット浮動小数点パイプラインを採用しています。ハイライトの復元やOkLCh色空間でのカラーグレーディング、階調の反転が起きない単調トーンカーブなどを備えます。
- ブラシやグラデーションに加え、輝度や色域、空や被写体の自動選択によるマスキングに対応しています。マスクごとに露光量やコントラストなど15項目の局所調整が可能です。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **AIエージェントに大量のRAW現像を一括処理させたいとき**: MCPサーバーが組み込まれており外部エージェントから全機能を操作できるため、露出調整やプリセット適用の自動化ワークフローを自前のスクリプトやAIで構築できます。
- **クラウドや独自形式に縛られず手元で写真編集を行いたいとき**: Pure Rustによる軽量ネイティブ動作と非破壊編集パイプラインを備えているため、元データを保護しながらローカル完結で32ビット浮動小数点精度の現像が行えます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **クリーンルーム再実装（clean-room design）**: 既存製品のソースコードを直接見ず、仕様や挙動のみを分析して著作権侵害を防ぎながら独自に再実装する手法です。
- **MCP（Model Context Protocol）**: AIエージェントが外部ツールやアプリケーションを操作・連携するための標準プロトコルです。
- **OkLCh**: 人間の視覚知覚に合わせて設計された、明度や彩度を直感的に破綻なく扱える新しい色空間です。

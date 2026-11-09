---
title: "開発者、AI作成UIをデザインし直す「unslop」をオープンソースで公開"
publishedAt: 2026-11-09T09:54:40+09:00
sourceUrl: "https://github.com/heydamir/unslop"
sourceTitle: "unslop: A Claude skill that turns vibecoded, AI-looking UI into a designed interface"
source: "github"
discussionUrl: "https://github.com/heydamir/unslop"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/heydamir/unslop"
score: 11999
comments: 0
tags: ["ai", "ui-design", "claude", "frontend", "open-source"]
model: "gemini-3.6-flash"
generatedAt: 2026-11-09T00:54:40Z
---

## 元記事の要旨

- Claude CodeやCodex、Google Antigravity向けスキル「unslop」が公開されました。AIが生成した特有のUIデザイン（紫のグラデーションや不揃いな余白など）を検出し、洗練されたデザインへ一括で修正します。
- 対応する技術スタックはNext.js、React、Vue、Svelte、Tailwind、プレーンなHTML/CSSなど多岐にわたり、既存のダッシュボードやアプリ、ランディングページ、公開中のWebサイトに対しても適用可能です。
- 処理の流れとして、画面上の問題点を洗い出す監査から始まり、プロダクトに合ったデザイン方針を設定した上で、余白、カラー、アイコン、文言などの順に段階的な修正を実施します。変更前には方向性の確認も行われます。
- オプションとしてPlaywrightとffmpegを利用し、UIが段階的に改善されていく様子を10秒未満のショート動画として生成する機能や、falなどの画像生成サービスと連携したビジュアル生成機能も備えています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **AIでプロトタイプ作成した画面の見た目を整えたいとき**: Claude Codeなどで自動生成された不揃いな余白や装飾を自動監査し、自社プロダクトのトーンに合わせたカラーやレイアウトの修正を段階的に適用して完成度を高められます。
- **SNS投稿用にUIのビフォーアフター動画を作成したいとき**: Playwrightとffmpegを連携させることで、AIが画面デザインを修正していくプロセスを10秒未満のショート動画として自動生成し、製品の改善アピールに活用できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **slop（AIが生成した低品質なデータやUI）**: AIによって出力された、質の低いコンテンツや過剰に装飾された不自然なデザイン要素を指す表現です。
- **MCP（Model Context Protocol、モデルコンテキストプロトコル）**: AIモデルが外部ツールや各種データソースと安全に通信・連携するための標準化された接続規格です。

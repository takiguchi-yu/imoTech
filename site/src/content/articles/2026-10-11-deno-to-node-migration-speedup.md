---
title: "開発者、静的サイトをDenoからNodeへ移行　ビルドが15％高速化"
publishedAt: 2026-10-11T09:15:24+09:00
sourceUrl: "https://dbushell.com/2026/10/03/deno-to-node/"
sourceTitle: "Friendship ended with Deno, now Node is my best friend"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=49971719"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/dbushell.com/2026/10/03/deno-to-node/"
score: 322
comments: 240
tags: ["nodejs", "deno", "typescript", "pnpm"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-11T00:15:24Z
---

## 元記事の要旨

- 長年Denoを愛用していた開発者がクライアント案件を機にNode.jsを再評価し、最新仕様への追従やレガシーAPIの刷新により扱いやすさが大幅に向上していると評価しました。
- パッケージ管理にはNPMではなくPNPMとFNMを採用し、リリースの遅延設定を行うことでサプライチェーン攻撃などのセキュリティリスクを抑えつつ運用しています。
- TypeScriptの直接実行機能である型ストリッピングに対応した一方、node_modules配下の制限を回避するため、パッケージ作成にはtsdownでのバンドルを導入しました。
- 自作の静的サイト生成ツールをDenoからNode.js v26.10.0へ最小限のAPI変更で移行したところ、ビルド時間が15％短縮されたと報告しています。

## 議論の論調

### NodeやDenoの代替としてBunを推す声と互換性の懸念

依存関係を最小限に抑えられ軽量で高機能な選択肢としてBunを好む意見が多く寄せられました。一方で、GETリクエストでのボディ送信の可否など標準仕様やNode.jsとの細かな挙動の違いにより、既存システムとの完全な互換性に疑問を持つ声も挙がっています。

### テストやリントを内包するDenoの利便性を再評価する意見

Denoにはテストランナー、リンター、型チェッカーが標準で組み込まれており、外部パッケージ選定や設定の手間が不要な点を高く評価するユーザーからは、Node.jsへ戻る理由はないという反論が出ました。またJSRの提供するドキュメント生成などの使い勝手も支持されています。

### Nodeの型ストリッピング制限に対する技術的見解

元記事が主張した特定企業による囲い込みという見方に対し、node_modules配下で型情報除去を制限しているのは依存関係ごとのtsconfig設定の不一致を防ぐための技術的判断であると指摘されました。型定義ファイル配布の利点を挙げて元記事の解釈を正すコメントも見られます。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **Denoで書いたスクリプトをNode.js環境へ戻したいとき**: Nodeの標準APIがモダン化されnode:fsやnode:pathへの差し替えが容易なため、コードの大幅な書き換えを避けつつ既存資産を移行できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **型ストリッピング（type stripping）**: TypeScriptのコードから構文木解析のみで型注釈を取り除き、高速にJavaScriptとして実行する機能です。
- **JSR（JavaScript Registry）**: TypeScriptのソースコードを直接公開でき、ドキュメント自動生成などを備えたモダンなパッケージ管理基盤です。

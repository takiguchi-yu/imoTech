---
title: "Cloudflare、Workersの本番プロファイラ公開　CPU・メモリ解析"
publishedAt: 2026-10-13T11:34:43+09:00
sourceUrl: "https://blog.cloudflare.com/workers-on-demand-profiling/"
sourceTitle: "Introducing on-demand CPU and memory profiling with flamegraphs for Workers and Durable Objects"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/workers-on-demand-profiling/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/workers-on-demand-profiling/"
score: 0
comments: 0
tags: ["cloudflare", "workers", "profiling", "flamegraph", "performance"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-13T02:34:43Z
---

## 元記事の要旨

- Cloudflareは、Cloudflare WorkersおよびDurable Objectsを対象とした、CPUとメモリのオンデマンドプロファイリング機能の提供を開始しました。
- ダッシュボードのObservabilityタブまたはCLI経由で本番環境のプロファイルを取得でき、関数ごとのリソース消費量をインタラクティブなフレームグラフとして可視化できます。
- TypeScript利用時はソースマップを有効化することで関数名の難読化を回避でき、取得したプロファイルファイル（pprof形式）を外部ツールで分析することも可能です。
- 社内事例では、R2バインディングの重複再帰処理を修正して関数を2.7倍高速化した例や、無効化し損ねたPrometheusコードによる128MBメモリ制限超過を解消した例が示されました。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **Workersで原因不明のメモリ制限超過エラーに対処したいとき**: 本番環境でメモリプロファイルを取得することで、不要なライブラリや処理がメモリを過剰に確保している箇所を関数単位で特定し、上限値未満へ削減できます。
- **高トラフィックなWorkerのCPU実行時間を削りたいとき**: CPUプロファイルのフレームグラフから実行時間の幅が大きい関数を特定し、重複呼び出しや冗長な走査処理を取り除くことで処理速度の改善につなげられます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **flamegraph（フレームグラフ、コールスタック可視化図）**: 関数の呼び出し関係と各処理のリソース消費割合を横幅のブロックで視覚的に表す図です。
- **pprof（プロファイル解析ツール・データ形式）**: Go言語等で広く使われる、CPUやメモリの割り当てプロファイルデータを可視化・分析する形式です。
- **Durable Objects（永続オブジェクト）**: Cloudflare Workersでデータの一貫性と状態管理を提供するサーバーレスな分散実行基盤です。

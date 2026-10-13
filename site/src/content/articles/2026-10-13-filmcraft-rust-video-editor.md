---
title: "ArtCraft、Rust製動画編集ソフト「FilmCraft」をオープンソース公開"
publishedAt: 2026-10-13T11:35:09+09:00
sourceUrl: "https://github.com/storytold/filmcraft"
sourceTitle: "filmcraft: FilmCraft: An open-source, nonlinear video editor written by scratch in pure Rust"
source: "github"
discussionUrl: "https://github.com/storytold/filmcraft"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/storytold/filmcraft"
score: 11583
comments: 0
tags: ["rust", "video-editing", "open-source", "webassembly"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-13T02:35:09Z
---

## 元記事の要旨

- ArtCraftチームは、Premiere ProのUIや操作感を再現したオープンソースの非線形動画編集ソフト「FilmCraft」を公開しました。Rustで一から実装され、macOS、Windows、Linux、WebAssemblyに対応します。
- H.264、HEVC、ProRes、AACなどの主要コーデックを仕様書からRustで独自実装し、GPUコンポジタはリニアライトで処理します。時間計算には厳密な整数値を用いており、タイムライン上のズレを完全に防ぎます。
- 3点編集や各種トリム、Lumetriスタイルの色補正パネルなどプロ向けの編集機能を網羅しています。さらにすべての操作がコマンドとして構成されており、AIエージェントによる直接の自動制御も想定した設計です。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **Premiereの操作感を維持したままオープンソース環境へ移行したいとき**: パネル配置やショートカットキーがPremiere Proに準拠しているため、操作の学習コストをかけずにRust製の高速なローカル編集環境へ移行できます。
- **AIエージェントによる動画編集の自動化ワークフローを構築したいとき**: アプリ内のすべての編集操作がコマンドとして設計されている性質を活かし、AIエージェントからプログラム経由で正確なタイムライン操作やカット割りを指示できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **非線形編集（ノンリニア編集、NLE）**: テープのように順番に繋ぐのではなく、デジタルデータをタイムライン上で自由に並べ替えて編集できる方式のことです。
- **クリーンルーム再実装**: 元のソースコードを見ずに公開仕様や外部の挙動のみを参考に、著作権を侵害しない形で一から同等機能を作り直す手法です。

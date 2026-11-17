---
title: "開発者が動画をカット別に解析し再現手順を示す「rea-video」公開"
publishedAt: 2026-11-17T12:52:13+09:00
sourceUrl: "https://github.com/JuneYaooo/rea-video"
sourceTitle: "rea-video: Reverse-engineer any video, shot by shot: filmed, AI-generated or coded, and how to remake it. Breakdowns in the open VIDEO.md format. 逆向一切视频，逐个镜头看是拍的、AI 生成的还是代码做的，再告诉你怎么复刻；拆解结果按 VIDEO.md 格式输出。"
source: "github"
discussionUrl: "https://github.com/JuneYaooo/rea-video"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/JuneYaooo/rea-video"
score: 9765
comments: 0
tags: ["video", "ai", "reverse-engineering", "agent"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-17T03:52:13Z
---

## 元記事の要旨

- rea-video は、入力された動画をカット単位でリバースエンジニアリングし、実写、AI 生成、3D アニメーション、コードによる動的表現のどれで作られたかを自動判定する CLI ツールです。
- Claude Code や Codex などの AI エージェント上で動作するよう設計されており、エージェント向けに最適化された独自仕様「VIDEO.md」と、人間が読むための HTML や PDF レポートの 2 種類を出力します。
- 画像認識モデルと連携することで各カットを再生成するためのプロンプトを逆算できるほか、実写の場合はカメラワークや 12 種類の一覧から照明機材の構成まで特定して再現手順を提示します。
- 映像の判定にとどまらず、字幕の出現タイミングやフォント装飾、音声が AI 音声か人間の声か、BGM のテンポ（BPM）や効果音の位置といった編集データも細かく抽出可能です。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **競合のショート動画広告の制作手法を自社で真似したいとき**: 実写か AI かコードかをショットごとに判別し、実写の照明配置や AI 生成プロンプトを抽出できるため、同様のクオリティの動画を再現・制作する足がかりにできます。
- **既存動画のテロップや構成を別言語向けに再編集したいとき**: 字幕の開始・終了タイミングや文字装飾、BGM のテンポなどを自動抽出し SRT などに出力できるため、元の構成を保ったまま編集作業を進められます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **VIDEO.md**: AI エージェントが必要な層だけを読み取れるよう設計された、動画の解析構造を記述する独自仕様の形式。
- **Remotion**: React のコードを使ってプログラムで動画やアニメーションを作成・編集できるオープンソースのフレームワーク。

---
title: "Z.ai、AIコーディング環境「ZCode」を公開　デスクトップやCLIに対応"
publishedAt: 2026-09-29T10:01:57+09:00
sourceUrl: "https://github.com/zai-org/ZCode"
sourceTitle: "ZCode: Z.ai's coding agent harness. Powerful, intelligent, extensible."
source: "github"
discussionUrl: "https://github.com/zai-org/ZCode"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/zai-org/ZCode"
score: 7043
comments: 0
tags: ["electron", "cli", "typescript", "ai-agent"]
model: "gemini-3.7-flash"
generatedAt: 2026-09-29T01:01:57Z
---

## 元記事の要旨

- Z.aiがAIコーディング作業環境「ZCode」のリポジトリを公開しました。デスクトップアプリ、Webインターフェース、ターミナル向けAgent CLIおよびランタイムのソースコードで構成されています。
- CLI版は1つのコマンドでターミナルUI（TUI）とWeb UIの両方に対応し、Electronを使わずにローカル環境で軽量に動作させることが可能です。
- リモート開発機能も備えており、SSHやWSL経由で接続した環境に対してローカルでビルドしたアセットをSFTP経由で転送して利用できます。
- リポジトリ内にはElectron製デスクトップアプリ、ReactとZustandを用いた共有UI、HTTP/WebSocketサーバー、Agent SDKなどがモノレポ形式で整理されています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **ターミナル上で対話的にAIコーディングを実行したいとき**: CLI版のzcodeコマンドを実行するだけでTUIやローカルWebサーバーが立ち上がるため、GUIアプリを開かずに端末内で完結して作業を進められます。
- **SSH接続先のサーバーでAIエージェントを動かしたいとき**: リモート開発向けの準備コマンドとSFTP転送の仕組みが用意されているため、外部CDNを使わずにローカル資産をリモート環境へ展開して利用できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **TUI（text user interface、テキスト利用者境界面）**: 文字や記号を用いて端末画面上で対話的に操作を行う表示方式です。

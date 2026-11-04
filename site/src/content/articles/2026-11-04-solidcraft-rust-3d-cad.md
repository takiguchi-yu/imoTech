---
title: "開発者、純Rust製の3D CAD「SolidCraft」公開　ブラウザやMCP対応"
publishedAt: 2026-11-04T10:25:57+09:00
sourceUrl: "https://github.com/tangency-labs/solidcraft"
sourceTitle: "solidcraft: SolidCraft: an open-source parametric 3D CAD application built in pure Rust. Desktop, web, and automation through MCP."
source: "github"
discussionUrl: "https://github.com/tangency-labs/solidcraft"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/tangency-labs/solidcraft"
score: 13415
comments: 0
tags: ["rust", "cad", "3d", "mcp", "open-source"]
model: "gemini-3.5-flash"
generatedAt: 2026-11-04T01:25:57Z
---

## 元記事の要旨

- 「SolidCraft」は、純Rustで構築されたオープンソースのパラメトリック3D CADアプリケーションです。寸法や拘束条件の変更に応じてモデルが自動再構築される機能を備え、デスクトップ環境（Windows、macOS、Linux）だけでなくWebブラウザ上でも動作します。
- 独自開発の拘束ソルバーを搭載しており、押出、回転、フィレットなどの立体形状編集、アセンブリ設計、板金機能に対応しています。また、STEP、IGES、3MF、STLなど多様な3Dファイル形式の入出力が可能です。
- ヘッドレスで実行可能なCLI機能に加え、AIエージェントによるモデル操作を可能にするModel Context Protocol（MCP）サーバーを内蔵しています。Claude Codeなどの外部AIツールと連携し、自動化された設計処理を実行できます。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **AIを活用して3Dモデルの作成やパラメーター変更を自動化したいとき**: 内蔵されたMCPサーバーを通じてClaudeなどのAIツールを接続することで、プロンプト指示に応じたコマンド実行や形状の自動更新が可能になります。
- **環境構築なしでブラウザ上で3Dモデルの閲覧や簡易編集を行いたいとき**: RustからコンパイルされたWeb版が提供されているため、専用ソフトのインストール不要でデスクトップ版同等の機能やファイル読み書きを試すことができます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **パラメトリックCAD**: 形状の寸法や位置関係を数値や変数として定義し、パラメーターを変更することでモデル全体を自動的に再計算・更新できる3D CADの設計手法。
- **MCP（Model Context Protocol）**: AIモデルが外部のツールやアプリケーションと標準化された仕様で安全に連携し、自動操作やデータ取得を行うためのプロトコル。

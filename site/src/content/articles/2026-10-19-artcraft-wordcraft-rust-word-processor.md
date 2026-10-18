---
title: "ArtCraft、WordをRustで再実装したワープロ「WordCraft」を公開"
publishedAt: 2026-10-19T08:12:04+09:00
sourceUrl: "https://github.com/storytold/wordcraft"
sourceTitle: "wordcraft: An open-source, clean-room reimplementation of Microsoft Word in pure Rust"
source: "github"
discussionUrl: "https://github.com/storytold/wordcraft"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/storytold/wordcraft"
score: 14375
comments: 0
tags: ["rust", "wordprocessor", "gui", "mcp"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-18T23:12:04Z
---

## 元記事の要旨

- ArtCraftチームは、Microsoft Wordを純粋なRustでクリーンルーム再実装したオープンソースのワープロ「WordCraft」を公開しました。リボンUIやスタイル、変更履歴、表、差し込み印刷など、Word特有の操作体系を再現しています。
- docxやodt、LaTeX、Markdownなどの読み書きに対応し、PDF出力も可能です。ElectronやTauriを使わずネイティブGUIライブラリeguiを採用しており、macOSやWindows、Linux、WebAssemblyで動作します。
- 段落レイアウトのキャッシュ機能により、188ページの文書でもタイピング時の再レイアウトを約1.4ミリ秒で処理する高い性能を備えています。スペルチェックや文法チェックを含め、完全にオフラインで動作する設計です。
- 全機能が422個のコマンドIDとして定義されており、UI操作だけでなくCLIやJSONチャンネル、MCPサーバー経由でAIエージェントから操作できるよう設計されています。ライセンスはMITまたはApache-2.0です。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **AIエージェントにWord文書の編集を自動化させたいとき**: 422個の機能がコマンド化されMCPサーバー経由で直接操作できるため、外部のLLMエージェントからWord互換の構造化文書をプログラムで正確に作成・編集できます。
- **軽量かつ完全オフラインでdocx文書を扱いたいとき**: Electronを使わず純RustとGPUネイティブ描画で構築され、通信を行わずオフラインで高速に動作するため、機密性の高い文書でも安全に閲覧・編集できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **クリーンルーム再実装（Clean-room design、権利侵害を防ぐ再開発手法）**: 元のソースコードを見ずに、公開仕様や外部挙動の観察のみから独立して同等品を開発する手法です。
- **MCP（Model Context Protocol、モデルコンテキストプロトコル）**: AIアシスタントなどの外部モデルが、アプリケーションの機能やツールと連携するための共通規格です。

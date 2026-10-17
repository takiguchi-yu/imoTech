---
title: "magpie、各種 AI エージェントのモデルを統合管理するローカルゲートウェイ"
publishedAt: 2026-10-18T08:09:36+09:00
sourceUrl: "https://github.com/yetone/magpie"
sourceTitle: "magpie: Every agent's model. One place. Codex on DeepSeek, Claude Code on Kimi, from the menu bar."
source: "github"
discussionUrl: "https://github.com/yetone/magpie"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/yetone/magpie"
score: 15025
comments: 0
tags: ["ai", "cli", "gateway", "macos", "developer-tools"]
model: "gemini-3.5-flash-lite"
generatedAt: 2026-10-17T23:09:36Z
---

## 元記事の要旨

- Claude CodeやCodexなど多様なAIエージェントの利用モデルを、メニューバーやCLIから一元的に切り替えることができるローカルゲートウェイです。
- APIキーやローカルモデル、各種サブスクリプションをプロバイダとして登録し、異なるエージェント間で共通して利用可能です。
- クォータの上限に達した際には、ルーティンググループ機能により自動的に次のアカウントやモデルへ切り替えを行い、エラーを防ぎます。
- macOS、Windows、Linux、Docker、Termuxに対応しており、各種設定ファイルや認証情報を自動で検出・管理します。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **複数の AI エージェントで利用するモデルを一括で切り替えたいとき**: ローカルゲートウェイ経由でモデルやプロバイダの設定を統合管理できるため、エージェントごとに異なる設定ファイルやキーを手動で書き換える手間を省き、メニューバーから一括して切り替えられます。
- **API の利用制限やクォータを気にせず作業を続けたいとき**: ルーティンググループ機能により、あるアカウントのクォータが枯渇した際に自動的別のアカウントやモデルへシームレスにフェイルオーバーするため、作業を中断せずに済みます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

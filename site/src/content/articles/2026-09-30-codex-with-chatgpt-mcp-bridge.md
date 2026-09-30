---
title: "開発者がWeb版ChatGPTとCodexを繋ぎAPI消費を抑えるツール公開"
publishedAt: 2026-09-30T09:26:42+09:00
sourceUrl: "https://github.com/XiaoDuoYa/codex-with-chatgpt"
sourceTitle: "codex-with-chatgpt: ChatGPT thinks. Codex works. Use ChatGPT as the planning brain while keeping the Codex harness."
source: "github"
discussionUrl: "https://github.com/XiaoDuoYa/codex-with-chatgpt"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/XiaoDuoYa/codex-with-chatgpt"
score: 6889
comments: 0
tags: ["chatgpt", "codex", "mcp", "automation", "developer-tools"]
model: "gemini-3.8-flash"
generatedAt: 2026-09-30T00:26:42Z
---

## 元記事の要旨

- ChatGPT有料プランのWeb枠を活用し、CodexのAPIトークン消費を抑えながら、ChatGPTに設計やレビューを担当させCodexにコード実行を委ねるツール「codex-with-chatgpt」が公開されました。
- CodexとWeb版ChatGPTは軽量な制御メッセージのみをやり取りし、ChatGPTは読み取り専用のMCPブリッジ経由で必要なコード行のみを取得するため、リポジトリ全体をアップロードしません。
- セキュリティ設計として、ファイル書き込みやシェル実行のツールを排除した読み取り専用の構成となっており、Cloudflare TunnelとOAuth 2.1による認証、秘密鍵や環境変数ファイルの除外機能を備えています。
- インストールと初期設定は専用の指示文をCodexに貼り付けるだけで環境確認からビルドまで自動実行され、日常のアップデートもGitHub経由で自動チェックされる仕組みとなっています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **CodexのAPI利用コストを抑えたいとき**: 思考やレビューの負荷をサブスクリプション契約済みのWeb版ChatGPTに肩代わりさせ、Codexをコード編集と実行のみに専念させることができます。
- **機密コードを外部に漏らさずAIレビューを受けたいとき**: 読み取り専用MCPを介して必要な行のみを都度参照し、秘密鍵や環境変数ファイルをブロックするため、コードベース全体のアップロードを回避できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **MCP（Model Context Protocol、モデル・コンテキスト・プロトコル）**: AIモデルが外部のデータソースや開発ツールと安全に連携するためのオープンな共通規格。
- **Cloudflare Tunnel（クラウドフレア・トンネル）**: ローカル環境で稼働するサーバーを、ルーターのポート開放をせずに安全に外部へ公開する通信技術。

---
title: "開発者、Claude Codeの履歴要約を間引きに置換するプラグイン公開"
publishedAt: 2026-09-28T08:49:48+09:00
sourceUrl: "https://github.com/tamaratran/fast-jev-compaction"
sourceTitle: "fast-jev-compaction: Claude Code plugin that replaces the compaction summary with Jev decisions: every tool call and result is scored in one fast request, stale ones are dropped or truncated, everything kept stays verbatim."
source: "github"
discussionUrl: "https://github.com/tamaratran/fast-jev-compaction"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/tamaratran/fast-jev-compaction"
score: 7021
comments: 0
tags: ["claude", "llm", "npm", "typescript"]
model: "gemini-3.8-flash"
generatedAt: 2026-09-27T23:49:48Z
---

## 元記事の要旨

- LLMによる会話履歴の要約はファイルパスや制約が欠落する問題があるため、文章の要約を行わずに不要なツール実行履歴のみを削除する手法を提案しています。
- 判定モデルのJevを用いて会話全体の文脈を評価し、各ツール呼び出しの記録とその実行結果を残すべきか個別に判定して間引きます。
- ユーザーとアシスタントのやり取り本文は一切改変せず元の状態を保ち、最新のやり取りや最初の指示は保護対象として維持されます。
- Claude Codeの関数フック向けプラグインとして機能するほか、単体のnpmパッケージとしても利用可能です。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **Claude Codeで長時間の修正作業を行うとき**: 文脈要約によるファイルパスやエラー詳細の消失を防ぎ、ツール実行の不要ログだけを間引くことで指示や制約を元の文面のまま保持できます。
- **独自のAIコーディングエージェントを構築するとき**: npmライブラリとして提供されているため、ツール呼び出しの判定と会話ログの選別ロジックを自作のエージェントへ手軽に組み込めます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **コンテキスト圧縮（context compaction）**: LLMの入力上限を超えないよう、過去の会話履歴を要約や削除によって削減する処理です。
- **フック（function hooks）**: ソフトウェアの特定処理の実行前後に割り込み、処理内容を差し替える拡張機能です。

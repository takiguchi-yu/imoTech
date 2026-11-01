---
title: "Anthropic、商用ClaudeのFB送信データを最長5年保存し学習利用"
publishedAt: 2026-11-01T09:21:46+09:00
sourceUrl: "https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training"
sourceTitle: "Is my data used for model training?"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50259406"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training"
score: 225
comments: 121
tags: ["anthropic", "claude", "privacy", "llm"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-01T00:21:46Z
---

## 元記事の要旨

- Anthropicは商用製品（Claude for Work、API、Claude Govなど）において、初期状態では入力や出力をAIモデルの学習に使用しない方針を規定しています。
- Good/Badボタンなどからフィードバックや不具合報告を送信した場合は、関連するチャットやコーディングセッションがモデル学習に利用される可能性があります。
- フィードバック送信時は会話全体やモデル設定が最大5年間安全なバックエンドに保存されますが、利用前にユーザーIDや顧客IDとの紐付けは解除されます。
- TeamプランやEnterpriseプランの管理者は、組織設定の「Data and Privacy」項目からメンバーによるフィードバック送信機能を無効化できます。

## 議論の論調

### フィードバック送信時の学習利用に対する当然視と反発

問題の原因究明やモデル改善を行うには報告された対話データが必要であり、送信画面にも明記されているため当然の仕様だとする意見が多く見られました。一方で、商用契約で学習対象外を期待しているユーザーに対し、評価ボタンを押しただけで会話全体を最長5年保持して学習に回す仕組みはプライバシー保護の観点で不親切であり、誤送信を誘発しやすいとの批判もあります。

### Claude Code等の簡易調査における収集範囲への疑念

CLIツールのClaude Codeなどで作業中に表示される満足度アンケートについても、回答するとセッション内容が収集・学習されるのではないかとの懸念が寄せられました。これに対しては、該当のポップアップは単なる満足度評価のみを記録するものであり、対話ログやコードなどのセッションデータは保存されないと公式仕様を引用して説明する声が上がっています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **機密性の高い業務でClaudeの商用プランを組織導入するとき**: 従業員が日常の対話で安易に評価ボタンを押して対話内容が最長5年間保存されるのを防ぐため、組織設定の「Data and Privacy」からフィードバック送信機能を事前に一括無効化する運用が役立ちます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **MCP（Model Context Protocol、AIモデルと外部データを接続する標準規格）**: ローカル環境や各種サービス上のデータ、ツールをAIモデルへ安全に連携するためのオープンなプロトコルです。

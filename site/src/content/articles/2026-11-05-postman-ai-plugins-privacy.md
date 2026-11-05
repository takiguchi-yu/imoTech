---
title: "Postman、AI プラグインの自動インストールと API データの共有機能に懸念の声"
publishedAt: 2026-11-05T10:47:05+09:00
sourceUrl: "https://github.com/postmanlabs/postman-app-support/issues/14370"
sourceTitle: "Postman silently auto-installs AI plugins and attempts to share all API data"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50354960"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/postmanlabs/postman-app-support/issues/14370"
score: 1485
comments: 470
tags: ["postman", "api", "security", "privacy"]
model: "gemini-3.5-flash-lite"
generatedAt: 2026-11-05T01:47:05Z
---

## 元記事の要旨

- Postman がデスクトップアプリで Codex や Claude 向けプラグインを事前の明示的な同意なしに自動インストールし、スタートアップフックを設定しようとする挙動が報告された。
- クエリパラメータやテンプレート構文に含まれる機密情報やシークレットの値までもが外部サーバーへ送信されているとの指摘がなされている。
- ネットワーク通信を遮断するとアプリケーション自体が正常に動作しなくなる仕様になっており、プライバシーやセキュリティ面での懸念が強まっている。

## 議論の論調

### 多額の資金調達と過度なマネタイズへの批判

多額のベンチャーキャピタルからの資金調達や大規模な人員拡大の結果として、強制的なログイン、データ収集、不要な AI 機能の追加といった、いわゆる「Enshittification（質の低下）」が進んだと強く批判されている。

### オフラインファーストで Git 管理可能な代替ツールへの移行

肥大化した Postman から離れ、ローカル完結型で Git によるリクエスト定義の管理が可能な Bruno や Insomnia などの代替ツールへ移行した、あるいは移行を検討しているという体験談が多く共有されている。

### AI ツールを用いた自作や従来のシンプルな手法への回帰

AI コーディング支援を活用すれば同等のクライアントツールを短時間で自作できるという意見や、そもそも curl やスクリプト、エディタ内蔵の機能で十分であるという意見が述べられている。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **社外秘の API エンドポイントや機密トークンを含むリクエストを安全にテストしたいとき**: Postman のように入力されたシークレットやクエリパラメータが外部サーバーへ送信される懸念を避け、ローカル環境のみでリクエストの送受信と検証を完結させることができます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **cURL（カール、URL 転送用コマンドラインツール）**: コマンドラインから HTTP リクエストを送信して API の動作確認などを行うための標準的なツール。
- **HIPAA（Health Insurance Portability and Accountability Act、医療保険の相互運用性と責任に関する法律）**: 患者の医療情報やプライバシーの保護を義務付けるアメリカの法律。

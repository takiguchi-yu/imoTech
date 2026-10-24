---
title: "Cloudflare、WAFにレスポンス遮断機能を追加　全プラン提供"
publishedAt: 2026-10-24T08:52:48+09:00
sourceUrl: "https://blog.cloudflare.com/full-transaction-waf/"
sourceTitle: "Introducing full transaction detection for Cloudflare WAF"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/full-transaction-waf/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/full-transaction-waf/"
score: 0
comments: 0
tags: ["cloudflare", "waf", "security", "http"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-23T23:52:48Z
---

## 元記事の要旨

- CloudflareはWebアプリケーションファイアウォール（WAF）を拡張し、HTTPリクエストとオリジンのレスポンス双方を評価する「フル・トランザクション検出」と「レスポンス・ルール」を導入しました。
- これまでのリクエスト単体の検査では誤検知のリスクから見逃していた攻撃も、レスポンスに含まれる機密データやエラー状況と突合することで、悪用が成立したかを正確に判定できます。
- 攻撃の兆候が確認された場合、レスポンス・ルールによってオリジンからの応答を検疫し、クライアントへ届く前にHTTP 403のエラー画面へ差し替えて情報漏洩を防ぎます。
- 本機能は無料プランを含むすべての顧客向けに一般提供が開始されており、最近公開されたphp2shell脆弱性への対策マネージドルールなどが初期提供されます。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **アプリの意図しない機密情報漏洩を防ぎたいとき**: パストラバーサル等で設定ファイルが参照された際、レスポンス内容をWAFが検知して403に差し替えるため、脆弱性が修正される前でも情報流出を阻止できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **WAF（Web Application Firewall、Webアプリ向けファイアウォール）**: Web通信の内容を検査し、外部からの攻撃や不正なアクセスを検知・遮断してWebサービスを守る仕組みです。
- **パストラバーサル（path traversal、相対パスの不正横断）**: パラメータを不正に操作して意図しないディレクトリをたどり、サーバー内の機密ファイルを外部から取得する攻撃手法です。

---
title: "Cloudflare、Ruby脆弱性「ruby2shell」の遮断ルールを全プランに追加"
publishedAt: 2026-11-28T12:19:08+09:00
sourceUrl: "https://blog.cloudflare.com/ruby2shell-waf-protection/"
sourceTitle: "How Cloudflare WAF protects against ruby2shell (CVE-2026-132825)"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/ruby2shell-waf-protection/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/ruby2shell-waf-protection/"
score: 0
comments: 0
tags: ["cloudflare", "waf", "ruby", "vulnerability"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-28T03:19:08Z
---

## 元記事の要旨

- Ruby開発チームは、文字列の大文字変換処理に起因する深刻なヒープバッファオーバーフロー脆弱性「ruby2shell」（CVE-2026-132825）を公表しました。RailsやSinatraの初期構成にも影響し、遠隔コード実行の危険があります。
- Cloudflareは無料プランを含む全利用者を対象に、本脆弱性および関連する整数オーバーフローをブロックする2つのWAFマネージドルールを追加しました。攻撃通信の自動遮断を既定で有効にしています。
- WAFはパッチ適用までの緩和策であり代替ではありません。Cloudflareを経由しない直接通信やHTTP以外の入力経路は防御できないため、根本的な解決にはRuby 3.3.14や3.4.13、4.0.10への更新が必要です。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **RailsアプリのRuby本体を直ちに更新できないとき**: Cloudflare WAFを挟むことで、細工されたHTTPリクエストによる悪用通信をネットワーク境界で遮断し、ランタイム更新までの防壁として利用できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **WAF（Web Application Firewall、Webアプリケーション向け防御機能）**: HTTP通信の内容を検査し、Webアプリケーション特有の悪意あるアクセスを検知して遮断するセキュリティ機構です。
- **ヒープバッファオーバーフロー**: プログラム実行時に動的確保されるメモリ領域の許容量を超えてデータを書き込み、隣接データを破壊してしまう脆弱性です。

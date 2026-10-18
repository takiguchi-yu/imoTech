---
title: "Cloudflare、認証ボットの振る舞いを継続評価　信用度を数値化"
publishedAt: 2026-10-19T08:11:10+09:00
sourceUrl: "https://blog.cloudflare.com/verified-bots-accountability/"
sourceTitle: "Continuous accountability for Verified bots"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/verified-bots-accountability/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/verified-bots-accountability/"
score: 0
comments: 0
tags: ["cloudflare", "bot", "crawler", "security"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-18T23:11:10Z
---

## 元記事の要旨

- Cloudflareは、認証済みボットがサイト側の設定やルールを継続して遵守しているかを評価・記録する新システムを発表しました。
- 身元証明だけでなく、robots.txtの指定遵守やHTTP 429への応答といった振る舞いを追跡し、継続的な信頼度を算出します。
- 過去にはスクレイピング拒否の回避を試みたPerplexityのボットを除外した例があり、身元の確認にとどまらない継続監査を重視しています。
- 収集したスコアは今後Radarで公開される予定で、サイト管理者は信頼度の基準値に基づいてトラフィックの制御が可能になります。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **クローラーによる過度な負荷を抑制したいとき**: 正規ボットであってもHTTP 429の減速指示を無視してアクセスを続ける挙動を検知できるため、マナーを守らないトラフィックを的確に遮断できます。
- **自社開発クローラーの信頼性を証明したいとき**: サイト側の指示やrobots.txtを遵守している履歴が継続的に評価されるため、悪質ボットと誤認されずに巡回できる環境を整えられます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **HTTP 429（Too Many Requests、リクエスト過多）**: サーバー側が許容量を超えるアクセスを受けた際、送信側へリクエスト頻度を落とすよう要求するHTTPステータスコードです。
- **robots.txt（クローラー巡回規約ファイル）**: サイト管理者がクローラーに対し、巡回を許可または拒否するパスやルールを提示するために配置するテキストファイルです。

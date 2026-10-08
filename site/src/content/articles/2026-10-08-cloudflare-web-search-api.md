---
title: "Cloudflare、AI向け「Web Search API」公開　3社から選択可能"
publishedAt: 2026-10-08T10:02:45+09:00
sourceUrl: "https://developers.cloudflare.com/changelog/post/2026-10-02-introducing-web-search-api/"
sourceTitle: "Web Search API"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=49963171"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/developers.cloudflare.com/changelog/post/2026-10-02-introducing-web-search-api/"
score: 588
comments: 281
tags: ["cloudflare", "api", "ai", "web-search"]
model: "gemini-3.6-flash"
generatedAt: 2026-10-08T01:02:45Z
---

## 元記事の要旨

- Cloudflareは、AIエージェントやアプリがWebを検索して最新情報にアクセスできるようにする「Web Search API」のベータ版の提供を開始しました。
- 開始時点ではCeramic.ai、Exa、Linkupの3プロバイダーに対応し、いずれもデータ保持なし（Zero Data Retention）やCloudflareのクローリング規格に準拠しています。
- 本機能はAI Gateway経由で実行され、検索要求の統合ログ記録や各社の定価による課金に対応し、独自APIキーの持ち込みにも対応します。

## 議論の論調

### Cloudflareの仲介による利便性とプラットフォーム依存の懸念

複数プロバイダーを統合し、請求の取りまとめやフェイルオーバーを容易にできる点を評価する意見がある一方、直接利用すれば済むとして中間に入り込むCloudflareへの依存やロックイン、インターネットの仲介者としての影響力拡大を懸念する声が出されています。

### 選択できる検索プロバイダーの価格帯と検索品質のばらつき

1,000リクエストあたり0.25ドルから7ドルまでプロバイダー間で大きな価格差が存在することが議論されました。安価なサービスでは意図しない検索結果が出ると指摘される一方、特定の用途に強みを持つサービスも評価されています。また利用規約による結果の保存や再配布制限を問題視する意見もあります。

### ボット保護サービスとクローラー仲介ビジネスの自己矛盾への批判

自社でWebサイトをボットやスクレイピングから保護するサービスを提供しながら、AI向けの検索やクローリング基盤を販売する姿勢に対して矛盾や利益の二重取りであるとの批判が上がりました。これに対し、検証済みボットによる管理されたアクセス提供であれば全体の負担軽減につながるとの擁護も見られます。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **AIエージェントにWeb検索機能を組み込み評価したいとき**: AI Gateway経由で複数プロバイダーを共通のインターフェースで試せるため、自前で各社と個別に契約やAPI接続を行わずにコストや検索精度の比較・検証が容易に行えます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **Zero Data Retention（データ保持ゼロ）**: ユーザーが送信したリクエストや検索データを、サービス事業者がサーバー上に保存や学習用途で蓄積しない運用方針のことです。
- **AI Gateway（エーアイ・ゲートウェイ）**: AIモデルや各種APIへのリクエストを中継し、ログ収集やキャッシュ、課金の一元管理を行うCloudflareのプラットフォーム機能です。

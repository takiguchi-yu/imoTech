---
title: "Cloudflare、欧州のオープンAIモデル2種をWorkers AIに追加"
publishedAt: 2026-10-04T08:48:59+09:00
sourceUrl: "https://blog.cloudflare.com/sovereign-ai-choice-one-year-later/"
sourceTitle: "One year later: Sovereign AI and the fight for choice"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/sovereign-ai-choice-one-year-later/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/sovereign-ai-choice-one-year-later/"
score: 0
comments: 0
tags: ["ai", "cloudflare", "llm", "security"]
model: "gemini-3.6-flash"
generatedAt: 2026-10-03T23:48:59Z
---

## 元記事の要旨

- CloudflareはBirthday Weekの取り組みとして、EU全24言語を網羅するEuroLLMと、1,500以上の言語に対応したスイスのApertusの2つの欧州オープンAIモデルをWorkers AIに追加しました。
- これらのモデルは公的研究機関によって開発され、透明性やEUのGDPRおよびAI Actなどの法規制に配慮された設計となっており、希少言語や地域言語での高い性能を発揮します。
- また、特定モデルのアクセス遮断に左右されないAIセキュリティ防御用のハーネスをオープンソース公開し、政府機関や重要インフラ事業者向けの体験型ワークショップを10月に開始します。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **特定のAIモデルの制限に左右されず防御を行いたいとき**: オープンソース化されたセキュリティハーネスを利用することで、複数のAIモデルを並列稼働させて脆弱性を検出でき、特定のアクセスが停止しても防御機能を継続できます。
- **多言語やマイナー言語に対応したサービスを開発したいとき**: Workers AI上のEuroLLMやApertusを活用することで、EU全24言語や地域の主要言語に対応した音声対話や行政案内サービスを低遅延で構築できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **Workers AI（Cloudflareが提供するGPU推論プラットフォーム）**: Cloudflareのエッジネットワーク上で機械学習モデルの推論を高速かつ低遅延で実行できるサーバーレスサービスです。
- **GDPR（General Data Protection Regulation、EU一般データ保護規則）**: EUにおける個人のデータプライバシーを保護するための法規制で、学習データの削除や透明性の確保が義務付けられています。

---
title: "DeepSeek、Web検索と取得のAPIを公開　1000件0.75ドルで提供"
publishedAt: 2026-10-20T09:22:31+09:00
sourceUrl: "https://api-docs.deepseek.com/guides/search/"
sourceTitle: "DeepSeek search and fetch – $0.75 per 1000 successful requests"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50138531"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/api-docs.deepseek.com/guides/search/"
score: 597
comments: 248
tags: ["deepseek", "api", "search", "web-scraping", "rag"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-20T00:22:31Z
---

## 元記事の要旨

- DeepSeekは、AIエージェントやRAG用途向けにWeb検索を行うSearch APIと、単一ページをMarkdownで取得するFetch APIを公開しました。価格は1000件の成功リクエストあたり0.75ドルです。
- Search APIは同社独自開発の検索エンジンを基盤とし、site:やlang:、after:などの検索演算子に対応しています。結果には関連性スコアや要約、権威度（authority）が含まれます。
- Fetch APIは最大8192文字のURLからWebページを取得し、タイトルとMarkdown形式の本文を返します。対象サイトの公開状況やアクセス制御ポリシーに準拠します。
- 両APIはREST形式のJSON APIで、既存のDeepSeek APIキーによるBearer認証を共用します。エラー応答はOpenAI互換の形式を採用しています。

## 議論の論調

### 競合サービスと比べた圧倒的な低価格

Brave Search（1000件あたり5ドル）やKagi（12ドル）、Exa（4ドル）などの主要な検索APIと比較して、0.75ドルという設定は極めて安価だと評価されています。効率的なキャッシュ機構や巡回アルゴリズムによる低コスト化と見る声がある一方、持続可能性や将来的な値上げを懸念する意見もあります。

### Webサイトのボット対策を巡る実効性と倫理

Cloudflareなどの保護を回避できるのかという疑問に対し、プロキシや指紋偽装を用いたスクレイピング対策の難しさが語られています。また、AIクローラーの過剰なアクセスによってWeb全体の閲覧障壁が高まっていることへの批判や、robots.txtなどの規約をどこまで尊重しているのかを懸念する声も上がっています。

### 自前クローラー運用と専用APIの利便性比較

SearXNGなどを利用した自前環境ではIP制限やCAPTCHAによる遮断が頻発するため、数ドル払ってマネージドなAPIを使う方が現実的だという意見が多く見られます。一方で、Exaのような高度なセマンティック検索や学術論文インデックスを持つ特化型サービスと比べると、検索品質自体はまだ粗削りだとする報告もあります。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **RAGシステムで最新のWeb情報を低コストで参照したいとき**: 1000件あたり0.75ドルという低価格設定と、要約やMarkdown本文を直接返せる仕様により、外部APIの従量課金を抑えながら最新ニュースやドキュメントを組み込めます。
- **AIエージェントにWeb調査ツールを組み込みたいとき**: 独自エンジンの検索結果にドメイン絞り込みや言語指定演算子、サイトの信頼性スコアが含まれるため、エージェントが自律的に信憑性の高い情報源を探索・取得できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **RAG（retrieval-augmented generation、検索拡張生成）**: 外部の情報源から関連文書を検索・取得し、LLMの入力プロンプトに補足情報として与えることで回答精度を高める手法です。
- **MCP（Model Context Protocol）**: AIモデルやエージェントが、外部のツールやデータソースと標準化された形式で通信・連携するための接続プロトコルです。

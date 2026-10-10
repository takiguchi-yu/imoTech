---
title: "Cloudflare、警報を自動検証する4種の専門AIエージェント基盤を構築"
publishedAt: 2026-10-10T09:51:12+09:00
sourceUrl: "https://blog.cloudflare.com/agentic-security-operations/"
sourceTitle: "Building an evidence-grounded agentic security operations harness on Cloudflare"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/agentic-security-operations/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/agentic-security-operations/"
score: 0
comments: 0
tags: ["cloudflare", "security", "ai-agents", "llm"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-10T00:51:12Z
---

## 元記事の要旨

- 大量のセキュリティ警報が同時に発生した際の分析負荷を減らすため、Cloudflareは決定論的処理と複数の専門AIエージェントを組み合わせた運用基盤を構築しました。
- 単一の汎用エージェントでは証拠に基づかない誤出力や探索範囲の逸脱が発生したため、モデルの推論前にコード側で確定的な証拠収集と事前調査を完了させる構成へと刷新しました。
- 取得した証拠をもとに、通信解析、顧客コンテキスト、グローバル遠隔測定、脅威情報の4つの専門エージェントが並行して分析を行い、合成エージェントが1つの助言に集約します。
- 各専門エージェントには事前調査パッケージ内の証拠引用が義務付けられており、無効な主張の混入を防ぐとともに、過去の対応履歴を統合して誤検知判定の精度を高めています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **大量のセキュリティ警報への一次対応を効率化したいとき**: 決定論的なログ収集と軽量モデルによるノイズ除去を組み合わせることで、アナリストが詳細調査すべき高リスクな警報だけに集中できるようになります。
- **調査エージェントのハルシネーションを抑制したいとき**: 推論前の証拠収集をコード側で固定し、AIには確定した証拠パッケージからの引用のみを義務付けることで、根拠のない推測混入を防ぐ設計が参考になります。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **SIEM（Security Information and Event Management、セキュリティ情報イベント管理）**: 多様な機器のログを一元管理し、異常の相関分析や脅威検知を行う監視システムです。
- **トリアージ（triage、優先度選別）**: 大量に届く警報の中から、即時対処すべき重大事象を優先順位付けして振り分ける作業です。

---
title: "開発チーム、推論基盤「Strata」を公開　125BのAIを市販PCで実行"
publishedAt: 2026-10-05T08:58:50+09:00
sourceUrl: "https://github.com/Niko1221/Strata"
sourceTitle: "Strata: Qwen3.8-Flash-Next on any consumer hardware: one-click install for Windows / Linux. Strata inference engine, OpenAI/Anthropic API on localhost, optional image input."
source: "github"
discussionUrl: "https://github.com/Niko1221/Strata"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/Niko1221/Strata"
score: 10957
comments: 0
tags: ["llm", "ai", "inference", "gpu", "opensource"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-04T23:58:50Z
---

## 元記事の要旨

- オープンソースの推論エンジン「Strata」が公開され、通常はサーバー環境を要する1250億パラメータの大規模モデル「Qwen3.8-Flash-Next」を市販のPC上で動かせるようになりました。
- 動作要件としてVRAM 12GB以上のNVIDIAまたはAMD製GPUと32GB以上のシステムRAMが必要で、WindowsとLinuxに対応した自動セットアップ用スクリプトが提供されています。
- チャットやコード生成、画像入力に対応し、すべての処理をローカルで完結させながら、RTX 5070などの環境で毎秒50〜90トークン以上の生成速度を達成しています。
- 搭載メモリ量に応じて複数の量子化モデルが用意されており、32GB環境向けのコーディング特化版「Coder」から高精度な版まで選択が可能です。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **機密コードや非公開文書を外部クラウドに出さずAI解析したいとき**: 125B規模の高度なモデルがPCローカル上で完全に動作するため、機密データを外部のAPIに送信することなく安全にコード生成や要約を行えます。
- **手元のゲーミングPCでローカルなコーディング支援環境を構築したいとき**: 12GBのVRAMと32GBのRAMがあれば動作し、ローカルAPIを介してエディタと連携させることで、毎秒50トークン以上の実用的な速度でコード補完を利用できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **VRAM（ビデオRAM、グラフィックスメモリ）**: GPUに搭載された専用メモリで、大規模なAIモデルの読み込みや高速な推論処理に用いられます。
- **トークン（token、AI処理の最小テキスト単位）**: 言語モデルが文章を扱う際の基本単位で、英単語の約4分の3程度に相当します。
- **量子化（quantization、モデルの軽量化処理）**: モデルの重みデータの数値精度を落とすことで、性能を保ちつつメモリ消費を抑えて高速化する手法です。

---
title: "開発者が意思決定モデル群「Kev」を公開　4サイズ展開でローカル実行に対応"
publishedAt: 2026-09-28T08:49:32+09:00
sourceUrl: "https://github.com/jaredpalmer/kev"
sourceTitle: "kev: Jev-like family of decision models built on top of Qwen3.5/3.8 you can train and run on your own"
source: "github"
discussionUrl: "https://github.com/jaredpalmer/kev"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/jaredpalmer/kev"
score: 7413
comments: 0
tags: ["machine-learning", "llm", "python", "open-source"]
model: "gemini-3.8-flash"
generatedAt: 2026-09-27T23:49:32Z
---

## 元記事の要旨

- KevはQwen3.5およびQwen3.8を基盤に構築された、ローカルで訓練や推論を実行できるオープンソースの意思決定モデル群です。TypeSafeのJevのアーキテクチャに着想を得て設計されています。
- 1つのリクエストでYes/No判定、多肢選択、スコアリングの質問をまとめて処理できる点が特徴で、質問間で入力文を共有しつつ相互の干渉を防ぎ、調整済みの確率スコアを出力します。
- サイズは0.8Bから27Bまでの4種類が用意されており、軽量版はApple SiliconのMacで動作し、最大モデルはデータセンター向けGPU1基で稼働します。
- TypeSafeのSystem One APIと互換性があり、既存のPython SDKをそのままローカルサーバーに向けるだけで利用できるほか、独自データセットでのファインチューニングにも対応します。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **問い合わせチケットの一次振り分けを自動化したいとき**: 4Bや9B版を自社サーバーで動かし、問い合わせ文から担当部署や緊急度、感情スコアの確率分布を同時に取得して、確信度が高い案件のみ自動分類できます。
- **機密データを外部APIに送信せず分類したいとき**: 0.8BモデルならローカルのMac環境で軽量に動作するため、社外秘の情報や個人情報を含むテキストの判定処理を自社内だけで安全に完結させられます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **Brierスコア（予測確率の正確性を測る評価指標）**: 予測確率と実際の結果との二乗誤差を平均した指標で、値が0に近いほど確率予測の精度が高いことを示します。
- **System One（TypeSafe社の高速判定API）**: TypeSafe社が提供する、テキストに対する確率や分類結果を高速に返す意思決定向けAPI仕様のことです。

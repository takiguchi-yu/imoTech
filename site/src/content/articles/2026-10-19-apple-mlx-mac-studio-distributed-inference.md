---
title: "Apple、Mac StudioでLLMを分散推論　1兆規模で毎秒36トークン"
publishedAt: 2026-10-19T08:18:43+09:00
sourceUrl: "https://machinelearning.apple.com/research/mlx-distributed-inference"
sourceTitle: "Apple ML Research: Muse Spark Open with MLX on Mac Studio"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50118320"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/machinelearning.apple.com/research/mlx-distributed-inference"
score: 365
comments: 205
tags: ["apple", "mlx", "macstudio", "llm", "distributed-computing"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-18T23:18:43Z
---

## 元記事の要旨

- Appleの研究チームは、自社開発の機械学習フレームワーク「MLX」の最新版を用い、Mac Studioクラスタ上で大規模言語モデルを分散推論する手法を発表しました。
- Thunderbolt 5経由のRDMAドライバーと新しい通信ライブラリを活用し、M5 Ultra搭載Mac Studio 4台のクラスタで約8160億パラメータの「Muse Spark Open」を毎秒36トークン以上で動作させました。
- M5 UltraはGPU Neural Acceleratorを搭載しており、M3 Ultraと比較して最初のトークン生成までの時間（TTFT）が最大4.6倍高速化し、メモリ帯域幅の拡大により生成速度も1.6倍に向上しています。
- 単一マシンに収まらない巨大モデルに対してパイプライン並列化やテンソル並列化をサポートし、デスクサイドのハードウェアで大規模モデルを実行可能にする道筋を示しています。

## 議論の論調

### ハードウェア導入費用とクラウドAPIの利用コストの比較

大容量メモリを搭載したMac Studioを4台揃える構成は数万ドル規模の投資になるため、クラウドAPIやホスティングサービスの従量課金と比べて費用対効果が見合わないという指摘が多くなされました。一方で、データセンターのGPUと異なりプライベートな手元環境を長期間維持できる価値を評価する声もあり、稼働率や用途によって意見が分かれています。

### モデル開発ではなく実行環境を売るAppleの事業戦略

多額の費用をかけてフロンティアモデルを独自訓練するのではなく、Metaなどのオープンウェイトモデルを動かすための高性能ハードウェアを販売する「ツルハシ売り」の立ち位置を巧みだと評する意見が見られました。その一方で、データセンター向けGPUやCUDAエコシステムと比較すると依然として本格的な機械学習インフラとしては限定的だとする見方も出ています。

### ベンチマーク比較における量子化精度の不公平さ

Metaの巨大モデルには4ビット量子化（NVFP4）を適用しているのに対し、比較対象として挙げられたQwenなどはネイティブの浮動小数点精度（BF16）のまま測定されている点について、比較の前提条件が揃っておらず恣意的ではないかという疑問が投げかけられました。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **機密データを社外に出さずに超大規模LLMを運用したいとき**: Thunderbolt接続のRDMAによる分散推論を活用することで、外部のクラウドAPIにデータを送信することなく、8000億規模のモデルをオフィス内のMac Studioクラスタで安全に実行できます。
- **大規模な文脈を読み込む自律型コーディング支援を行いたいとき**: M5 UltraのGPU Neural Acceleratorが入力処理を最大4.6倍高速化するため、6万トークンを超える巨大なリポジトリ全体の文脈を与えたプロンプトでも初回応答の待ち時間を短縮できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **RDMA（Remote Direct Memory Access、遠隔直接メモリアクセス）**: CPUを介さずにネットワーク経由で他のマシンのメモリ領域へ直接アクセスし、低遅延で高速な通信を行う技術です。
- **TTFT（Time to First Token、初トークン生成時間）**: モデルに入力テキストを渡してから、最初の1単語目（トークン）が出力されるまでにかかる応答時間を指します。
- **MoE（Mixture of Experts、専門家混合）**: 複数の小規模なネットワークを持ち、入力に応じて必要な一部のみを動作させることで計算量を抑えるモデル構造です。
- **NVFP4（4-bit Floating Point、4ビット浮動小数点数）**: モデルの重みパラメータを4ビットの浮動小数点形式に圧縮し、メモリ消費量と計算負荷を低減する量子化規格です。

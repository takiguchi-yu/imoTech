---
title: "Cloudflareら、TypeScriptのRust移植「tsrs」公開　最大8倍高速化"
publishedAt: 2026-10-22T09:12:08+09:00
sourceUrl: "https://blog.cloudflare.com/typescript-rust-port/"
sourceTitle: "Tsrs: A Port of TypeScript to Rust"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50165953"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/typescript-rust-port/"
score: 428
comments: 209
tags: ["typescript", "rust", "compiler", "webassembly", "cloudflare"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-22T00:12:08Z
---

## 元記事の要旨

- CloudflareとVoidZeroは、TypeScriptコンパイラのRust移植版「tsrs」の開発を発表しました。フォークではなく、本家TypeScriptチームと緊密に連携しながらOxcツールチェーンの一部として育成されています。
- 早期ベンチマークでは、TypeScript 7.0と比較して最大8倍高速化され、メモリ使用量が約70％削減されました。この移植版で見つかった最適化の一部は本家TypeScript 7.1にも還元されています。
- Rustを採用した背景にはWebAssemblyとの親和性があります。Go言語と異なりランタイムのGCが不要なため、Cloudflare Workersやブラウザなどの制約のある環境で軽量に動作させることが可能です。
- アップストリームとの互換性を保つため、日次で差分を追跡し自動テストや修正案生成を行うエージェントを活用し、動作の乖離を最小限に抑えながら維持管理する体制を整えています。

## 議論の論調

### AIを活用したコード移植の保守性や設計への懸念

人手による緻密な設計ではなくフロンティアAIによる短期間での移植が主流になることに対し、コードレビューの形骸化やアーキテクチャの妥協を懸念する声が上がっています。一方で、十分な統合テストがあれば問題ないとする意見や、今後の開発の不可逆な潮流と捉える見解もあります。

### 公式Go版がある中でのRust版の必要性

TypeScript公式が開発を進めているGo移植版で十分高速化されているため、さらなる高速化は過剰ではないかという疑問が出ました。これに対し、WebAssembly環境でGCを抱えずに極小のメモリで動かせる点や、巨大リポジトリでの実行速度の差には実利があるとの反論がなされています。

### 本家TypeScriptへの最適化還元への評価

TypeScriptチーム関係者が議論に参加し、tsrsで見つかった最適化手法が公式のTS 7.1の高速化に貢献していることを歓迎しました。競合や分裂ではなく、エコシステム全体に知見を還元し合う協調姿勢が高く評価されています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **ブラウザやエッジ上で型検査を実行したいとき**: Wasm上でGCなしで軽量に動作するため、Cloudflare Workersやブラウザ内IDEなど、リソース制約の厳しい環境でも高速な開発環境を構築できます。
- **大規模コードベースのCIの検査時間を短縮したいとき**: TypeScript 7.0比で最大8倍の処理速度と70％のメモリ削減を実現しているため、CIパイプラインにおける型検査の待ち時間を大幅に削減できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **LSP（Language Server Protocol、言語サーバープロトコル）**: エディタとコンパイラ間で補完や定義ジャンプなどの言語機能を提供する標準規約です。
- **Wasm（WebAssembly、ウェブアセンブリ）**: ブラウザやエッジ環境などで高速かつ安全に動作する低レベルなバイナリ命令形式です。

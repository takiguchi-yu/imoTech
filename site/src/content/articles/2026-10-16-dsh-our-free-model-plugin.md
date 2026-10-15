---
title: "開発者、「dsh-our-free-model」公開　DeepSeekなど先端AIを登録不要で提供"
publishedAt: 2026-10-16T08:42:37+09:00
sourceUrl: "https://github.com/Ebony-Vinyl/dsh-our-free-model"
sourceTitle: "dsh-our-free-model: 在 dsh 里装上这个插件即可，无需登录、注册或填 API Key，就能使用包括 DeepSeek V4.1 Flash、Kimi K3 在内的前沿模型——完全免费，不限量。 All you do is install this plugin in dsh: no login, no sign-up, no API key — the frontier models are just there, DeepSeek V4.1 Flash and Kimi K3 among them. Completely free, with no usage cap."
source: "github"
discussionUrl: "https://github.com/Ebony-Vinyl/dsh-our-free-model"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/Ebony-Vinyl/dsh-our-free-model"
score: 17816
comments: 0
tags: ["ai", "llm", "proxy", "deepseek", "opensource"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-15T23:42:37Z
---

## 元記事の要旨

- dsh向けプラグイン「dsh-our-free-model」が公開されました。アカウント登録やAPIキーの入力を行わずに、DeepSeek V4.1 FlashやKimi K3などの先端大規模言語モデルを無料で利用できます。
- OpenCodeやKilo AIなどの公開ゲートウェイに直接接続する仕組みを採用しており、モデル一覧や利用可否は手元の環境から上流へリアルタイムに問い合わせて動的に更新されます。
- OpenAI互換およびAnthropic互換のローカル転送ポートを備えており、Claude Codeなどの外部ツールからローカルプロキシ経由で各モデルを呼び出すことが可能です。
- 76社のプロバイダーAPIキーを集約する機能や、ツールの出力を圧縮してトークン消費を抑える機能、応答失敗時に別モデルへ自動切り替えするフォールバック機能も搭載されています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **外部ツールから先端モデルを手軽に検証したいとき**: OpenAI互換のローカル転送ポートが提供されるため、自作スクリプトやコーディング支援ツールからAPIキー不要で即座にDeepSeek等の推論を試せます。
- **多数のLLMプロバイダーを一括管理したいとき**: 76社のプロバイダー登録に対応し、自前キーの管理や自動フォールバック経路を同一画面で構築できるため、障害時の迂回設定を容易に整備できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **SSE（Server-Sent Events、サーバー送出イベント）**: サーバーからクライアントへリアルタイムにテキストデータを単方向ストリーミング配信する技術です。
- **フォールバック（fallback、代替への切り替え）**: 主系のモデル呼び出しが制限や障害で失敗した際に、自動的に後続のモデルへ切り替えて処理を継続する仕組みです。

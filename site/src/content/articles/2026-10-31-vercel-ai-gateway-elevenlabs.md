---
title: "Vercel、ElevenLabsの音声AIモデル14種をAI Gatewayに統合"
publishedAt: 2026-10-31T09:53:59+09:00
sourceUrl: "https://vercel.com/blog/elevenlabs-on-ai-gateway"
sourceTitle: "ElevenLabs on AI Gateway"
source: "vercel-blog"
discussionUrl: "https://vercel.com/blog/elevenlabs-on-ai-gateway"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/vercel.com/blog/elevenlabs-on-ai-gateway"
score: 0
comments: 0
tags: ["vercel", "elevenlabs", "ai", "audio", "tts"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-31T00:53:59Z
---

## 元記事の要旨

- VercelはAI GatewayにおいてElevenLabsとの提携を発表し、音声認識や音声合成、リアルタイム会話、音楽・効果音生成を含む14種の音声モデルの提供を開始しました。
- 開発者は単一のゲートウェイAPIキーを通じて各音声モデルを利用でき、既存の言語モデルと接続してストリーミング再生を行ったり、複数話者の対話を1リクエストで生成したりできます。
- クライアント側から接続するリアルタイム対話機能向けには短時間有効なトークンを発行する仕組みが用意され、APIキーを公開せずにWebSocket経由で双方向音声会話を実装できます。
- AI Gatewayの標準機能として、モデル呼び出しの使用量や費用の可視化、リトライやフェイルオーバーの管理、ゼロデータ保持（ZDR）などのガバナンス機能がそのまま適用されます。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **リアルタイムで音声対話ができるWebアプリを作りたいとき**: 単一のWebSocket接続で完結するEleven Realtimeモデルを活用することで、一時トークンを用いてブラウザにAPIキーを露出させずに低遅延な音声エージェントを導入できます。
- **LLMの回答を待たせず自然な音声で即座に読み上げたいとき**: ストリーミング対応のEleven Flash v2.5を組み合わせることで、言語モデルが文章を出力している最中から音声を並行再生し、ユーザーの待ち時間を最小限に抑えられます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **VAD（voice activity detection、音声活動検知）**: 音声入力の中から人が話している区間を判別する技術です。モデルが発話終了を自動検知するために利用されます。
- **ZDR（zero data retention、データ非保持）**: リクエストに含まれるプロンプトや生成データを外部プロバイダーのサーバー上に永続保存させないプライバシー保護方針です。

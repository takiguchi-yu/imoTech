---
title: "Windows 11、開発ツールやAIの利用を収集　診断データとして米社へ送信"
publishedAt: 2026-11-20T11:22:17+09:00
sourceUrl: "https://xusheng.dev/posts/windows-coding-agent-telemetry/"
sourceTitle: "Windows 11 is collecting data on which coding agents and developer tools you use"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50524736"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/xusheng.dev/posts/windows-coding-agent-telemetry/"
score: 732
comments: 621
tags: ["windows", "telemetry", "privacy", "ai-tools"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-20T02:22:17Z
---

## 元記事の要旨

- Windows 11のシステムDLL「MissionControlAggregator.dll」内に、ClaudeやCodex、Cursorなどのコーディングエージェントや各種開発ツールの実行ファイル名が直接組み込まれていることが判明しました。
- このコンポーネントはプロセスの状態変化やWSLの実行イベントを購読し、対象ツールの実行を検知するとビットマップ形式でローカルに状態を保持します。
- 保持された情報はETW経由で診断イベントとして記録され、デフォルトで有効になっているオプションの診断データを無効化していない場合、マイクロソフトへ送信されます。
- ソースコードやプロンプトの内容そのものは含まれないものの、特定分野の開発ツールやAIエージェントの起動有無を追跡する仕組みが標準で動作していたことが示されています。

## 議論の論調

### OSや他社サービスでも同様の収集は行われているとする見方

一部の参加者は、大半の商用OSやGPUドライバ、ブラウザでも同等以上の利用状況テレメトリが日常的に収集されていると指摘しました。マイクロソフトに限った話ではなく以前から想定されていた挙動であり、大騒ぎするほど新規性のある情報ではないという冷静な受け止めが見られます。

### プライバシー侵害への懸念と設定無効化の推奨

デフォルトで有効なオプション診断データ経由で特定のAIツール利用が追跡される点に対し、強い嫌悪感やプライバシー上の懸念を示す声が上がりました。設定画面からオプション診断データをオフにすれば送信を防げると周知され、OSが独自に特定アプリを追跡する設計そのものが批判されています。

### WindowsからLinuxへの移行の現実味と障壁

このような追跡を機にLinuxへの移行を勧める意見が多く出た一方、カーネルレベルのアンチチートを要するオンライン対戦ゲームや一部の業務アプリが動かない現実が議論されました。Protonの進歩でシングルプレイゲームの互換性は向上したものの、完全な移行には依然としてハードルが残るという意見が交わされています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **Windows環境での開発ツール利用情報の送信を防ぎたいとき**: Windows 11が標準でツール利用を記録しているため、「設定」の「プライバシーとセキュリティ」からオプションの診断データを無効化することで、利用エージェント情報のマイクロソフトへの自動送信を停止できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **ETW（Event Tracing for Windows）**: Windowsのカーネルやアプリの動作イベントを効率的にログ記録・追跡するための標準トレース機能。
- **WSL（Windows Subsystem for Linux）**: Windows上でLinux環境のバイナリを直接実行できるようにする仕組み。

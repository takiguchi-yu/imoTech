---
title: "OpenAIのCodex Desktop、1日5GB以上のクラッシュダンプを無制限に生成"
publishedAt: 2026-10-21T08:56:36+09:00
sourceUrl: "https://github.com/openai/codex/issues/25921"
sourceTitle: "Codex Desktop continuously generates Crashpad pending dumps"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50133231"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/openai/codex/issues/25921"
score: 175
comments: 88
tags: ["openai", "codex", "debugging", "storage"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-20T23:56:36Z
---

## 元記事の要旨

- GitHub上のOpenAI公式リポジトリにて、デスクトップ版クライアント「Codex Desktop」に関する不具合が報告されました。
- 報告によると、Codex DesktopはCrashpadによる保留中のクラッシュダンプファイルを上限なく継続的に生成し続ける挙動を示しています。
- この不具合によってディスク容量が少なくとも1日あたり5GB以上のペースで消費され続け、ストレージを圧迫する問題が生じています。

## 議論の論調

### 開発環境における急激なストレージ圧迫の実態

実際に300GB以上もの容量を消費された事例や、テスト成果物やスクリーンショットが大量に残置される現象が報告されました。Codexに限らず自律型コーディングエージェント全般が中間生成物を適切に掃除しない設計になっている点が指摘されています。

### エージェント実行時のシステム保護と回避策

大規模な容量消費やメモリ枯渇に対処するため、コンテナや仮想マシンへの隔離、ZFSなどのファイルシステムによる圧縮、プロセスの強制終了設定、不要ファイルを巡回削除する定期スクリプトの導入など、各自が実践している防衛策が共有されました。

### 高度なAI技術と基本ソフト品質の乖離への指摘

高度な推論モデルを標榜する一方で、数か月間にわたり初歩的とも思えるリソース解放の不具合を放置している開発姿勢に呆れの声が上がりました。一方で、AI以前から同種の不具合は日常茶飯事であり過度な失望は不要とする冷静な見方も示されています。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **Crashpad（クラッシュパッド、障害情報収集機構）**: Googleが開発した、プロセスが異常終了した際にメモリ状態などのダンプを取得・保存するためのオープンソース仕組みです。
- **worktree（ワークツリー、Gitの作業ディレクトリ機能）**: Gitで同一リポジトリから複数のブランチを異なるディレクトリに同時に展開して並行作業を行える仕組みです。

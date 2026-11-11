---
title: "PwnAI、FirecrackerのVM脱出手法を公開　KVM復帰時のレジスタ改変で"
publishedAt: 2026-11-11T10:18:03+09:00
sourceUrl: "https://pwn.ai/blog/firecracker-escape"
sourceTitle: "Firecracker VM Escape: PwnEscape Part 2"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50397219"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/pwn.ai/blog/firecracker-escape"
score: 288
comments: 140
tags: ["security", "virtualization", "linux", "kernel", "exploit"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-11T01:18:03Z
---

## 元記事の要旨

- セキュリティ企業のPwnAIが、マイクロVM「Firecracker」の隔離を突破し、ホスト上でroot権限コード実行を達成するエクスプロイトの詳細を公開しました。先行研究で得たホストメモリアクセス権限を起点としています。
- 実証ではゲスト側メモリに配置した特定のバイト列を手がかりに、拡張ページテーブルを探索してホスト物理アドレスを特定します。さらにホストのページテーブルを逆引き走査することで、Firecrackerプロセスの特定と検証を行いました。
- 特定したプロセスの情報から、KVM_RUNの復帰待ちにある仮想CPUスレッドのpt_regs構造体を特定し、保存されたレジスタ値を書き換えることで、Firecrackerへ制御が戻る瞬間に任意の処理を実行させることに成功しました。

## 議論の論調

### 実証環境の前提条件と脆弱性の責任所在をめぐる議論

コメントでは、今回の実証がFirecrackerの保護機構であるJailerを無効化した環境で行われている点や、根本原因がLinuxカーネルのvirtio-netにある点が指摘されました。Firecracker固有の欠陥というよりカーネル側の問題であり、本番環境で直ちにホスト完全掌握に至るわけではないと冷静に見る意見があります。一方で、KVMの隔離境界が破られた事実そのものは極めて重大であり、後続の権限昇格攻撃と組み合わせれば深刻な脅威になると警鐘を鳴らす声も上がっています。

### LinuxとKVMの構造的リスクと代替設計への関心

巨大で複雑なLinuxカーネルに仮想化の制御層を任せるアプローチの限界を懸念する意見が集まりました。形式検証された極小のマイクロカーネルを用いるNovaやseL4などのマイクロハイパーバイザ設計こそが、この種の脆弱性を排除する正しい道だとする支持意見が投稿されています。これに対し、形式検証済みカーネルであっても周辺機能やその上で動くコンポーネントの実装不備までは防げず、性能や実用性とのトレードオフを無視できないという反論も交わされました。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **EPT（Extended Page Tables、拡張ページテーブル）**: 仮想マシンが認識する物理アドレスを、ホストの物理アドレスへ変換するハードウェア仮想化機能です。
- **pt_regs（Linuxカーネルのレジスタ退避構造体）**: システムコールなどでカーネルへ移行する際、ユーザ空間のレジスタ状態を一時退避しておくためのデータ構造です。

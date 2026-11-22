---
title: "開発者がコンテナ環境「kiri」公開　Docker比80倍高速に起動"
publishedAt: 2026-11-22T10:24:38+09:00
sourceUrl: "https://github.com/libracoder/kiri"
sourceTitle: "kiri: A small, fast container runtime for macOS, Windows and Linux with free Ngrok alternative"
source: "github"
discussionUrl: "https://github.com/libracoder/kiri"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/libracoder/kiri"
score: 12055
comments: 0
tags: ["docker", "containers", "rust", "kubernetes"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-22T01:24:38Z
---

## 元記事の要旨

- Rustで開発された軽量コンテナランタイム「kiri」が公開されました。macOS、WSL2上のWindows、Linuxに対応し、Docker Engine APIと互換性を持つため既存のdocker CLIやComposeがそのまま動作します。
- Docker API経由でのコンテナ起動・終了が約2.5ミリ秒と、Docker Desktopと比較して約80倍の高速化を実現しています。アイドル状態が60秒続くと仮想マシンが自動休止し、デーモンのメモリ使用量は約15MBにとどまります。
- コンテナごとにローカルドメインと自動生成の証明書によるHTTPS環境が提供されるほか、コマンド1つでk3sによるKubernetes環境やLinux環境を起動できます。
- ローカルポートをインターネット経由で公開する共有機能やUSBデバイスのパススルー機能も備え、Docker DesktopやOrbStackからの移行コマンドも提供されています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **ローカルでのDockerコンテナ起動やCIテストを高速化したいとき**: コンテナが約2.5ミリ秒で起動・終了し、既存のdockerコマンドやCompose設定をそのまま使えるため、ローカル開発環境の待ち時間を大幅に削減できます。
- **開発用ノートPCのメモリ消費やバッテリー消費を抑えたいとき**: 常駐デーモンの消費メモリが約15MBと小さく、未使用時は60秒で仮想マシンが自動休止するため、マシンへの負荷や発熱を抑えながら作業できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **k3s（軽量版Kubernetes）**: リソース消費を抑えて単一ノードなどで手軽に動作するように設計された、軽量なKubernetes実装です。
- **IPAM（IP address management、IPアドレス管理）**: コンテナネットワーク内で使用されるIPアドレスの割り当てや解放を管理する仕組みです。

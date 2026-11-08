---
title: "開発者が「dsh-Go」公開、Android単体でDeepSeek Harnessを動作"
publishedAt: 2026-11-08T09:43:43+09:00
sourceUrl: "https://github.com/ccch1mneyyy/dsh-Go"
sourceTitle: "dsh-Go: dsh-go — DeepSeek Harness 装进口袋：手机本机运行，也能遥控你的电脑。"
source: "github"
discussionUrl: "https://github.com/ccch1mneyyy/dsh-Go"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/ccch1mneyyy/dsh-Go"
score: 14364
comments: 0
tags: ["android", "deepseek", "open-source", "ai-agent"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-08T00:43:43Z
---

## 元記事の要旨

- 「dsh-Go」は、AIエージェントフレームワーク「DeepSeek Harness」をAndroid端末上で動作させるためのオープンソース（AGPL-3.0）クライアントです。Android 8.0以上に対応しています。
- 端末内にUbuntuとNode.jsを含むLinux環境を内包しており、root権限の取得やTermuxなどの追加アプリなしで、スマートフォン単体でDSHエンジンを実行できます。
- 単体動作だけでなく、SSHや「DSHarness Remote」を介してPCや外部サーバー上で稼働するDSHのリモート制御にも対応しており、環境をシームレスに切り替えて利用可能です。
- 画面の読み取りやタップ・入力を自動化する端末操作機能、AI生成中の割り込み指示機能、さらに作業状況をアニメーションで伝えるデスクトップペット機能などを備えています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **出先でスマートフォンからAIエージェントに作業を任せたいとき**: アプリ内に独立したLinux環境を備えているため、PCを開けない環境でも端末単体でエージェントを動かし、画面の自動操作やタスク実行を完結できます。
- **自宅PCのAIエージェント環境を遠隔から操作したいとき**: SSHやリモート接続機能を通じて手元のスマホからPC側のDSHセッションを引き継げるため、外出先から継続して作業の指示や進捗確認が行えます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **Termux**: Android端末上でLinux環境とターミナル機能を提供するアプリケーションです。
- **Root権限（ルートけんげん）**: AndroidなどのUnix系OSにおいて、システムの全操作が許可された最高管理者権限です。

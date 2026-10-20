---
title: "開発者、Macの個別ウィンドウをiOSで遠隔操作する「Sill」を無料公開"
publishedAt: 2026-10-20T09:24:39+09:00
sourceUrl: "https://github.com/Saffsanity/sill"
sourceTitle: "Any window from your Mac, on your iPhone and iPad"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50112739"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/Saffsanity/sill"
score: 270
comments: 76
tags: ["macos", "ios", "swift", "screencapture", "remotedesktop"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-20T00:24:39Z
---

## 元記事の要旨

- Sillは、Mac上の個別ウィンドウやデスクトップ全体をiPhoneやiPadへHEVC動画として配信し、タッチやキーボードで遠隔操作できるオープンソースツールです。
- 画面転送にはScreenCaptureKitとハードウェア動画エンコードを用い、遅延時にはフレームを破棄して最新表示を維持します。端末間の通信はTLS 1.3で暗号化されます。
- 同一ネットワークだけでなく、USB有線接続、AirDrop類似の直接Wi-Fi通信、Tailscale等のVPNを経由した遠隔アクセスに対応し、仲介サーバーを必要としません。
- クリップボード共有やフォントサイズ調整、仮想ディスプレイ機能による他ウィンドウ重複時の描画継続など、手元での操作性を高める補助機能を備えています。

## 議論の論調

### Apple標準のSidecarとの違いや利便性の比較

iPadをサブディスプレイ化するSidecarとは異なり、手元のiOS端末側から操作を開始して特定ウィンドウだけを複製・操作できる点が評価されています。また、Sidecarが同一Apple IDや同一ネットワークを要求するのに対し、VPN経由でも動く柔軟性を支持する声が上がりました。

### 既存のVNCアプリに対する優位性と手軽さ

RealVNCなどの既存ツールは全画面共有が中心で設定やサブスクリプション料金の負担が大きい中、Sillは無料かつ軽量でウィンドウ単位の操作が快適だと歓迎されています。一方で、画面全体のズーム表示や詳細なショートカット操作を求める意見も寄せられました。

### WindowsやLinuxなど他OSへの対応要望

MacとiOSに限定されていることに対し、LinuxノートPCからMacのウィンドウを操作したいという要望や、Windows版・Intel Mac対応を望む声が上がりました。Appleのエコシステム内での完成度の高さを認めつつも、マルチプラットフォーム化への期待が見られます。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **離れた場所からMacの作業状況を確認・操作したいとき**: 自宅内で席を離れた際、iPhoneやiPadからMacで開いた特定ウィンドウだけを呼び出せます。ハードウェアHEVCエンコードにより低遅延で映像が届くため、ダイアログの確認や軽い設定変更が手元で素早く完結します。
- **外出先からTailscale等のVPN経由でMacを遠隔管理したいとき**: 仲介サーバーを経由せずVPN通信に対応しており、回線帯域が落ちた場合も自動でフレームを間引いて遅延を防ぐため、不安定なモバイル回線からでもMac上の特定アプリを安定して監視・操作できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **ScreenCaptureKit**: macOSに標準搭載されている高パフォーマンスな画面収録用APIフレームワークです。
- **HEVC（High Efficiency Video Coding、高効率動画圧縮規格）**: 従来のH.264より高い圧縮率を実現する映像符号化規格で、H.265とも呼ばれます。
- **Tailscale**: WireGuardプロトコルを基盤にしたゼロコンフィグの仮想プライベートネットワークサービスです。

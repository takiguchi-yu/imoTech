---
title: "Discord、デスクトップ版をRustで再構築　起動即時化・メモリ70%削減"
publishedAt: 2026-11-09T10:10:43+09:00
sourceUrl: "https://www.windowslatest.com/2026/11/06/every-windows-11-app-should-kill-electron-and-discord-just-showed-why-no-starting-screen-and-70-less-ram-even-with-two-accounts-signed-in/"
sourceTitle: "Every Windows 11 app should kill Electron, and Discord just showed why"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50403507"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/www.windowslatest.com/2026/11/06/every-windows-11-app-should-kill-electron-and-discord-just-showed-why-no-starting-screen-and-70-less-ram-even-with-two-accounts-signed-in/"
score: 450
comments: 469
tags: ["discord", "rust", "electron", "gpui", "performance"]
model: "gemini-3.6-flash"
generatedAt: 2026-11-09T01:10:43Z
---

## 元記事の要旨

- Discordは、従来採用していたElectronを廃止し、Rustおよび描画フレームワーク「GPUI」を用いて開発された新しいデスクトップクライアントのデモ動画を公開しました。
- 新クライアントは起動時のアップデート画面をスキップして即座に立ち上がり、2つのアカウントを同時実行した状態でもメモリ消費量を従来の約70%減となる290.2MBに抑えています。
- 新UIの描画にはGPUアクセラレーションを行うGPUIを採用しており、モバイルアプリのReact Native廃止やWeb版のWebAssembly導入により、主要ロジックをRustで共通化します。
- 新しいクライアントはWindowsだけでなくmacOSやLinuxにも対応しており、安定性とセキュリティの確保に向けたプライベートテストが近日中に開始される予定です。

## 議論の論調

### Electron脱却とパフォーマンス向上の徹底を歓迎する声

従来のElectronアプリが多大なリソースを消費していた背景から、今回のRustおよびGPUIへの移行による起動速度向上やメモリ消費量の削減を高く評価する意見が多くみられます。一方で、複数プラットフォーム向けの開発を少人数で実現してきたElectronの功績を認める声も残っています。

### アクセシビリティや独自フレームワークの保守性に対する懸念

Web技術をベースとするElectronが提供してきた画面読み上げ機能や多言語入力（IME）などのサポートが、Rust製のUIフレームワークでも同等に維持できるかを心配する声が上がっています。また、採用されたGPUIが特定エディタの開発向けに特化している点から、汎用性や長期的なメンテナンス性を疑問視する意見もあります。

### 開発効率とユーザー体験のバランスを巡る議論

単一のコードベースで全OSに対応できるWeb技術の利便性が開発コスト削減に寄与してきた反面、ユーザーのシステムリソースを過剰に消費してきた現状が議論されました。ネイティブに近い性能とマルチプラットフォーム対応を両立する開発ツールの成熟が、今後のアプリ開発の標準を変えるかに注目が集まっています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **メモリ容量が限られたPCで他の重い作業と並行してチャットを使うとき**: GPUによる画面描画とRustによる軽量設計により、2アカウント起動時でもメモリ使用量が約290MBに抑えられるため、開発ツールや動画編集アプリと同居させても動作を圧迫しにくくなります。
- **個人用と業務用のアカウントを同一PCで切り替えずに運用したいとき**: 新クライアントはアプリを再起動・リセットすることなく2つのアカウントの同時実行をネイティブにサポートしているため、アカウント切り替えの手間なく複数アカウントを管理できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **Electron（ChromiumとNode.jsを統合したアプリ基盤）**: Web技術を使ってクロスプラットフォームのデスクトップアプリを作成するための開発フレームワークです。
- **GPUI（GPUアクセラレーションを利用したRust向けUIフレームワーク）**: コードエディタZedの開発元が作成した、GPUを用いてUIを高速描画するRust用のライブラリです。
- **WebAssembly（WASM、Webブラウザ上で高速動作するバイナリ形式）**: Rustなどの言語で書かれたコードをコンパイルし、Webブラウザ内で高速に実行させるための技術です。

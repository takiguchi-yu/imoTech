---
title: "macOS 27、CoreStorageの対応を事実上終了　通常マウントや消去が不能に"
publishedAt: 2026-11-08T09:52:12+09:00
sourceUrl: "https://wadetregaskis.com/macos-27-golden-gate-does-not-actually-support-corestorage-or-hfs-volumes/"
sourceTitle: "macOS 27 does not support CoreStorage volumes"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50356944"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/wadetregaskis.com/macos-27-golden-gate-does-not-actually-support-corestorage-or-hfs-volumes/"
score: 141
comments: 117
tags: ["macos", "storage", "apfs", "filesystem"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-08T00:52:12Z
---

## 元記事の要旨

- macOS 27ではCoreStorageおよび暗号化HFS+ボリュームがサポートされず、ディスクユーティリティなどの標準ツールで通常のマウントやAPFSへの変換、ディスク消去が行えなくなりました。
- 起動時には「macOS 28で非対応になる」という案内ダイアログが表示されるものの、実際にはmacOS 27の時点で既に正常な操作が受け付けられない状態に陥っています。
- 下位ツールのmount_hfsコマンドを読み取り専用オプション付きで直接実行すれば手動マウントは可能ですが、書き込みモードでのマウントや通常の手順による消去はエラーとなり失敗します。
- 論理ボリュームグループをコマンドラインから削除した後にマシンを再起動することで、リソースが解放されて物理ドライブの再フォーマットが可能になる回避策が確認されています。

## 議論の論調

### 古い規格の性急な打ち切りと品質への批判

警告画面では次期バージョンでの廃止と案内されているにもかかわらず、現行バージョンで実質的に壊れていることへ厳しい批判が集まりました。Microsoftが後方互換性を長期間維持するのに対し、Appleは自社が使わなくなった技術を性急に切り捨てる傾向があるという指摘や、近年のOSアップデートによる安定性の低下を嘆く声が上がっています。

### HDD向け暗号化バックアップ手段の不足

APFSはSSD向けに最適化されておりHDDでの動作が非常に遅いため、従来の暗号化HFS+を外部バックアップ用途に残していたユーザーから困惑の声が上がりました。代替案としてNASやZFS、サードパーティ製ツールの利用が挙げられたものの、OSの標準機能だけで手軽に大容量HDDへ暗号化保存する手段が狭まったことが懸念されています。

### CoreStorageの歴史的役割と世代交代の必然性

CoreStorageはLinuxのLVMに似た論理ボリューム管理であり、かつてSSDとHDDを組み合わせたFusion DriveやHFS+の暗号化を実現するための過渡期の技術であったと整理されました。現在のmacOSではAPFSがサブボリュームやスナップショットを直接処理できるため、使われなくなった古い機構が削除されるのは自然な流れだとする意見もあります。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **暗号化HFS+の外付けHDDからデータを救出したいとき**: 標準のディスクユーティリティを介さず、ターミナルからmount_hfsコマンドに読み取り専用オプションを添えて直接指定することで、データを退避させられます。
- **CoreStorage形式だったストレージを再フォーマットしたいとき**: diskutilコマンドで論理ボリュームを削除した後にOSを再起動すると、リソース使用中エラーが解消されて物理ドライブの初期化が可能になります。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **CoreStorage**: macOSで論理ボリューム管理やディスク全体の暗号化、Fusion Driveを実現していたストレージ基盤技術です。
- **HFS+（Mac OS Extended、Mac OS 拡張フォーマット）**: APFSが登場するまで、長年にわたりMacの標準ファイルシステムとして使われていたファイル体系です。
- **APFS（Apple File System、アップルファイルシステム）**: フラッシュストレージ向けに最適化され、スナップショット機能などを備える現在のApple標準ファイルシステムです。

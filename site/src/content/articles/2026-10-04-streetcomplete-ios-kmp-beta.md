---
title: "OSM編集アプリ「StreetComplete」、iOS版をベータ公開　KMP採用で移行50％に"
publishedAt: 2026-10-04T08:51:48+09:00
sourceUrl: "https://github.com/streetcomplete/StreetComplete/issues/5421"
sourceTitle: "StreetComplete on iOS is now in public beta"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=49920160"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/streetcomplete/StreetComplete/issues/5421"
score: 627
comments: 175
tags: ["streetcomplete", "ios", "kotlin-multiplatform", "openstreetmap"]
model: "gemini-3.6-flash"
generatedAt: 2026-10-03T23:51:48Z
---

## 元記事の要旨

- OpenStreetMapのデータ収集アプリ「StreetComplete」の開発チームが、iOS版のパブリックベータテストを開始したと発表しました。これまでAndroid向けに提供されていた機能をiOS環境にも広げる取り組みです。
- 本プロジェクトではKotlin MultiplatformとCompose Multiplatformを採用しており、アプリ全体のロジックとUIを単一のコードベースで維持することで、移植に伴う保守コストの増加を低減させています。
- iOS移植には全体で1人年程度の工数が見込まれていますが、2024年前半の集中開発により作業の約50％が完了しました。開発者はタスクボードでの協力やスポンサー支援をコミュニティに呼びかけています。

## 議論の論調

### Kotlin Multiplatformの採用に対する評価と疑問

Kotlin Multiplatformを採用した開発体験について、共有コードを多く維持できる点を評価する声がある一方、ビルドプロセスの複雑化やiOS開発者の学習コスト、フレームワーク固有の不具合対応にかかる保守負担を懸念する意見も上がっています。

### ベータ版におけるUI操作や画面遷移への要望

質問画面から元の地図に戻る際、標準的なボタンではなく画面縁からのスワイプジェスチャーが必須となっている点に戸惑う利用者が多く見られます。多くのユーザーが強制終了に頼っている状況が指摘され、より直感的なUIへの改善が求められています。

### 初心者支援とデータ正確性のバランスを巡る議論

アプリの手軽さでOSMへの貢献のハードルが下がったと絶賛される一方で、道路の歩行可否などの定義を巡りベテラン編集者と初心者の間で編集の撤回トラブルが発生している事例が報告されています。これに対し、質問の文言改善や機能の見直しが進められています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **iPhoneでOpenStreetMapの地図データ作成に参加したいとき**: 簡単な質問に答えるだけで属性情報を更新できるUIを備えているため、専門的な知識がなくても散歩や移動のついでに現地調査を行い、地図の精度向上に直接寄与できます。
- **Kotlinの既存資産を活かしてiOSアプリを構築したいとき**: Kotlin MultiplatformとCompose Multiplatformにより単一コードベースでUIとロジックを共有できるため、Androidアプリの資産を活用し保守コストを抑えてiOS展開を試せます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **KMP（Kotlin Multiplatform、Kotlinによる複数OS対応技術）**: KotlinコードをiOSやWebなど複数プラットフォーム向けにコンパイルし、共通のロジックとして共有・再利用する技術です。
- **OSM（OpenStreetMap、自由に参加・編集できる世界地図）**: 有志のコミュニティによって作られるオープンデータの地理情報サービスで、誰でも地図の表示や編集に参加できます。
- **Compose Multiplatform（UI構成用のマルチプラットフォームフレームワーク）**: Jetpack Composeの描画仕組みを応用し、AndroidとiOSで共通の宣言的UIコードを動作させるための開発ツールです。

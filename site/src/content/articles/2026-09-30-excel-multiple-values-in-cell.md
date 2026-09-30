---
title: "Microsoft、Excelで1セルへの複数値格納に対応　40年の歴史で初"
publishedAt: 2026-09-30T09:27:31+09:00
sourceUrl: "https://techcommunity.microsoft.com/blog/microsoft365insiderblog/put-multiple-values-in-one-cell-with-lists-and-arrays-in-excel/4559395"
sourceTitle: "Excel now supports multiple values in a single cell"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=49849832"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/techcommunity.microsoft.com/blog/microsoft365insiderblog/put-multiple-values-in-one-cell-with-lists-and-arrays-in-excel/4559395"
score: 276
comments: 191
tags: ["excel", "microsoft", "spreadsheet", "data-structures"]
model: "gemini-3.8-flash"
generatedAt: 2026-09-30T00:27:31Z
---

## 元記事の要旨

- 米Microsoftは、表計算ソフト「Excel」において、1つのセルの中にリストや配列、ネストされた配列といった複数の値を保持できるようにする機能変更を発表しました。
- Excelの40年の歴史において、セルは基本的に1つの値のみを保持する設計でしたが、この根本的な制約が撤廃されることになります。
- 本機能は、まずWindowsおよびMac向けのMicrosoft Excel Beta Channelを対象に先行提供が開始されます。

## 議論の論調

### シート構造の整理や計算モデルの簡素化に役立つ

これまでの動的配列では中間計算の結果が別セルに展開（スピル）され、シートが乱雑になったりエラーが生じたりしていました。1つのセル内に配列を閉じ込められることで、余計なヘルパー領域を排除して計算モデルを格段にすっきりと構築できるようになると、実際に試したユーザーから高く評価されています。

### 柔軟性の過剰な追求が保守性低下を招くという懸念

データベース設計における第一正規形（各セルは単一の値を持つ）の原則から逸脱し、データ構造が複雑化・スパゲッティ化することで、第三者による理解や保守が困難になるという懸念があります。特に企業内に数多く存在する既存のマクロ（VBA）や古い業務フローを破壊するリスクを指摘する声も上がっています。

### 表計算ソフトの本質的な改善点に対する議論

型システムの根本的な刷新として革命的だと受け止める意見がある一方で、確率分布のセル表現や使い勝手の良いショートカットなど、他に優先すべき機能改善があるのではないかという指摘もあります。また、そもそも表計算ソフトの2次元モデルに収まらない処理なら専用スクリプトやDBを使うべきだという見方も示されています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **大規模な財務モデルや集計シートのレイアウトを整理したいとき**: 中間計算用の動的配列を1つのセルに収められるため、展開用の余分なセル領域を確保する必要がなくなり、計算エラーを防ぎつつシートをコンパクトに保てます。
- **LET関数やLAMBDA関数を駆使して複雑なカスタム数式を組むとき**: セル内に配列やリストを直接保持できるため、ワークシート全体に展開結果を露出させることなく、高度なデータ処理を単一セル内で完結させやすくなります。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **スピル（spill、数式結果の自動展開）**: 数式が複数の値を返した際、隣接する空セルへ自動的に結果が流れ出して展開されるExcelの挙動です。
- **第一正規形（1NF、First Normal Form）**: リレーショナルデータベース設計で、すべての属性値が分割できない単一の値（スカラー）を持つ状態を指します。

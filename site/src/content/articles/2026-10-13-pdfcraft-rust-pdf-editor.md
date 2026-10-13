---
title: "ArtCraft、Rust製PDFツール「PdfCraft」を公開　破損修復にも対応"
publishedAt: 2026-10-13T11:35:48+09:00
sourceUrl: "https://github.com/storytold/pdfcraft"
sourceTitle: "pdfcraft: PdfCraft: An open-source PDF reader and editor written by scratch in pure Rust"
source: "github"
discussionUrl: "https://github.com/storytold/pdfcraft"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/storytold/pdfcraft"
score: 11459
comments: 0
tags: ["rust", "pdf", "opensource", "desktop-app"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-13T02:35:48Z
---

## 元記事の要旨

- ArtCraftは、Rustでゼロから実装されたオープンソースのPDF閲覧・編集ソフト「PdfCraft」を公開しました。Adobe Acrobatのクリーンルーム再実装を目指しています。
- アカウント作成やテレメトリ収集、クラウドへの依存が一切なく、完全にオフラインで動作します。保存時は追記型で行われるため、元のデータを壊さずに安全に編集できます。
- 縦書き日本語やカラー絵文字を含む多言語の精密な描画に対応し、タイル単位での描画方式を採用しているため、高倍率に拡大しても鮮明な表示を維持します。
- 破損したPDFドキュメントの修復機能を備え、pdf.jsの983件のテストデータにおいてクラッシュ数ゼロを記録したほか、ページの結合や分割、並べ替えも可能です。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **社外秘のPDF書類をネットワークに接続せず安全に編集・整理したいとき**: テレメトリや外部通信が一切ない完全オフライン設計のため、情報漏洩を防ぎながら追記保存で元ファイルを保護しつつ結合やページの整理を行えます。
- **縦書きの日本語など複雑な書式を含むPDFを拡大して精査したいとき**: 縦書きCJKや特殊なグリフ描画に対応し、タイルレンダリングにより高倍率ズームでもぼやけずに表示できるため、細かい文字の確認に役立ちます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **クリーンルーム再実装（clean-room reimplementation）**: 既存ソフトのソースコードを見ずに仕様や振る舞いだけを調べ、権利侵害を避けて独自にゼロから同じ機能を作り直す手法です。
- **テレメトリ（telemetry、利用状況の自動収集）**: ソフトウェアの利用状況やエラー情報などを、利用者の端末から開発元へ自動的に送信して集計する仕組みのことです。

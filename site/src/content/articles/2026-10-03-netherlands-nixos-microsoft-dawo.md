---
title: "オランダ政府、Microsoft離れへ「NixOS」基盤を構築　2027年末公開へ"
publishedAt: 2026-10-03T09:32:40+09:00
sourceUrl: "https://www.tomshardware.com/software/the-netherlands-is-rolling-alternative-nixos-based-software-ecosystem-after-u-s-sanctions-on-icc-took-microsoft-off-the-table-trial-programs-running-now-first-release-expected-at-end-of-2027"
sourceTitle: "US sanctions force The Netherlands off Microsoft and toward alternative NixOS"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=49891550"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/www.tomshardware.com/software/the-netherlands-is-rolling-alternative-nixos-based-software-ecosystem-after-u-s-sanctions-on-icc-took-microsoft-off-the-table-trial-programs-running-now-first-release-expected-at-end-of-2027"
score: 387
comments: 394
tags: ["nixos", "linux", "microsoft", "open-source"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-03T00:32:40Z
---

## 元記事の要旨

- 米国政府がオランダ・ハーグの国際刑事裁判所（ICC）に制裁を科し、主任検察官がメールなどのMicrosoftサービスを遮断されたことを契機に、オランダ政府は米国製ソフトウェアへの依存低減を決定しました。
- オランダ内務・王国関係省の監督のもと、3つのICTサービス事業者が「DAWO（政府向けデジタル自立型職場環境）」と呼ばれるNixOSベースの新システム開発を進めています。
- NixOSは宣言的な構成管理と不変性により設定の最大90％を他環境へ流用可能で、行政機関への一括展開が容易なほか、Windows 11の要件を満たさない旧型PCでも動作する利点があります。
- 現在は8つの自治体で試験運用が行われており、2027年末までに最初の安定版が用意される予定です。ドイツやフランス、デンマークなど欧州他国でも同様の米国製技術離れが進められています。

## 議論の論調

### デスクトップOSとしてのNixOS採用の実現性

宣言的設定や再現性の高さを評価し、大規模配布に最適とする意見がある一方で、汎用Linux向けバイナリの動作に制約がある点や、低レイヤーのライブラリ更新による大規模な再ダウンロード・再ビルドの発生、ユーザー環境を含めたロールバックの難しさなどを挙げ、行政の一般事務端末としての実用性に疑問を呈する技術的な反論が多く寄せられました。

### 欧州全体での標準化と独自開発による分断

欧州域内にはSUSEなど実績ある企業製ディストリビューションがあるにもかかわらず、各国が個別に独自環境を開発することは重複コストと分断を生むとの懸念が示されました。これに対し、NixOS財団の本拠がオランダにあることや、特定企業に買収されるリスクを避けて真の技術的主権を確保するための合理的な選択だとする反論もありました。

### OS刷新だけでは防げないクラウドや決済の依存

今回の制裁で問題となったメールや金融サービスの遮断はデスクトップOSの変更だけでは防げず、OSを変えても本質的な解決にならないという冷ややかな見方が出ました。それに対し、インフラ全体を一度に置き換えることは不可能なため、まずはOSから段階的に依存度を下げていくアプローチとして妥当だとする擁護意見も交わされました。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **旧型PCを活用しつつ全社の端末環境を刷新したいとき**: NixOSはWindows 11の要件を満たさない旧型機でも動作するため、既存資産を延命しながらOSの移行と管理の標準化を進めることが可能です。
- **多数の部署で構成の揃った業務端末を展開したいとき**: Nixの宣言的構成管理により、構成の大部分を他環境へ容易に流用できるため、拠点ごとの個別キッティング工数を削減し再現性の高い環境を配布できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **DAWO（Digitaal Autonome Werkomgeving Overheid、政府向けデジタル自立型職場環境）**: オランダ政府が進める、特定外国企業への依存を排したデジタル自立型職場環境構想。
- **ICC（International Criminal Court、国際刑事裁判所）**: オランダ・ハーグに常設され、戦争犯罪や人道に対する罪などを裁く国際司法機関。

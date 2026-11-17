---
title: "Apple、MacBook Pro にタンデム OLED 採用　240Hz の PWM 調光で体調不良の報告"
publishedAt: 2026-11-17T12:54:25+09:00
sourceUrl: "https://macanorak.com/the-macbook-pros-oled-pwm-problem-when-a-better-display-becomes-worse-to-use/"
sourceTitle: "The MacBook Pro's OLED PWM problem"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50506719"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/macanorak.com/the-macbook-pros-oled-pwm-problem-when-a-better-display-becomes-worse-to-use/"
score: 505
comments: 279
tags: ["apple", "macbook", "oled", "hardware", "display"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-17T03:54:25Z
---

## 元記事の要旨

- Apple が新型 MacBook Pro にタンデム OLED を採用した「PROLED XDR Display」を導入したものの、一部のユーザーから目の疲れや頭痛、めまい、吐き気などの不快感を訴える声が上がっています。
- Notebookcheck の測定によると、新ディスプレイの輝度制御には 240Hz の PWM（パルス幅変調）が用いられており、従来の Mini-LED モデルが記録した 14,880Hz と比べて周波数が約 62 分の 1 に低下しています。
- 輝度 99% 以下で明滅が確認されており、DC 調光と PWM が併用されていますが、これまで他の OLED 端末で問題がなかったユーザーでも症状を自覚して返品に至る事例がコミュニティで報告されています。

## 議論の論調

### 240Hz という低周波 PWM の採用に対する失望と懸念

アクセシビリティを重視してきた Apple の旗艦機が、業界基準である IEEE 1789 の低リスク基準すら満たさない 240Hz で明滅することへの驚きが示されました。kHz 帯での駆動に比べると、健康被害を受けるユーザーが無視できない規模で存在するのではないかという懸念が寄せられています。

### 測定結果の解釈やハードウェア設計の技術的制約への着目

公開されたオシロスコープ波形を分析し、タンデム OLED が位相をずらして駆動しているなら実質的な周波数は 480Hz や 960Hz に近いのではないかという指摘や、有機 EL の応答速度や発色精度との兼ね合いで高周波化が難しかった可能性など、技術的側面から冷静に原因を探る議論が行われました。

### フリッカー感受性の個人差と認知拡大の必要性

本人が意識して画面のチラつきを視認できなくても、脳や視神経への負荷で片頭痛などが引き起こされる現象について実体験が共有されました。ディスプレイだけでなく室内 LED 照明やテールランプでも同様の不快感が生じるとして、フリッカー耐性への配慮が設計に求められるという意見が出ています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **目の疲れやすさに不安があり購入を検討しているとき**: 輝度 99% 以下で 240Hz の PWM 明滅が生じる仕様のため、実機を店頭で確認するか、返品可能な保証期間内に長時間のテキスト作業を行って体調に異常が出ないか確かめる用途に向きます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **PWM（pulse width modulation、パルス幅変調）**: 電源のオンとオフを高速に切り替え、その時間比率を変えることで見かけの明るさを調整する手法です。
- **DC 調光（direct current 調光、直流調光）**: 素子に流す電流の強さ自体を増減させて明るさを制御し、画面の明滅を抑える調光方式です。
- **タンデム OLED（tandem organic light-emitting diode、積層型有機 EL）**: 発光層を多層に重ねることで、高輝度と長寿命を両立させた有機 EL パネルの構造です。

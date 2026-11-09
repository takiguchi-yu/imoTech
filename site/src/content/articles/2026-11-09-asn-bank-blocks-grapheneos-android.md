---
title: "オランダASN銀行が非公認Androidを遮断、GrapheneOSも対象"
publishedAt: 2026-11-09T10:08:24+09:00
sourceUrl: "https://github.com/PrivSec-dev/banking-apps-compat-report/issues/105"
sourceTitle: "Dutch 'idealist' bank ASN blocks non-Google Android, including GrapheneOS"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50390124"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/PrivSec-dev/banking-apps-compat-report/issues/105"
score: 655
comments: 426
tags: ["grapheneos", "android", "security", "privacy"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-09T01:08:24Z
---

## 元記事の要旨

- オランダのASN銀行が、GrapheneOSをはじめとするGoogleサービス非搭載のAndroid端末からのアクセスを遮断したことがGitHub上で報告されました。
- この事象はモバイルバンキングアプリの互換性を追跡・検証するリポジトリのIssueとして報告され、同行のアプリが非公式なAndroid環境で動作しなくなった状況が記録されています。
- 社会的責任や倫理的な方針を掲げるASN銀行による制限措置として取り上げられ、カスタムROMやプライバシー重視のOSを利用するユーザー環境への影響が示されています。

## 議論の論調

### Play Integrityによる画一的な端末制限への批判

銀行がGoogleのPlay Integrity APIを利用してカスタムROMやルート権限を持つ端末を一律に排除していることに対し、ユーザーの主権を奪う過度な統制だとする批判が集まりました。何年もセキュリティ更新が途絶えた正規端末は通る一方で、強固な保護機能を備えたGrapheneOSが弾かれる実態は不合理だと指摘されています。

### 銀行側のサポート費用や管理責任を重視する視点

金融機関が非公式OSをサポート対象外とする背景には、不正利用時の賠償責任や動作検証コストの抑制があるとの意見も出されました。大多数の顧客に対してGoogleの標準的な認証基準で安全性を担保するほうが合理的であり、利用者がごく一部に限られる独自環境への対応を見送るのは企業として妥当な判断だとする声も見られます。

### Web取引の廃止と欧州決済網への移行に伴う懸念

欧州の銀行でWebブラウザ経由の取引機能が廃止され、専用アプリが強制される傾向が進んでいる点に懸念が示されています。さらに欧州独自の決済基盤であるWeroへの移行に際してGoogleの認証基盤への依存が強まれば、巨大IT企業から距離を置きたいユーザーの選択肢が完全に塞がれてしまうのではないかと議論されました。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **プライバシー重視の端末でネット銀行口座を管理したいとき**: GrapheneOS環境ではアプリ起動が遮断される事例があるため、ブラウザ単体で送金や認証が完結する銀行や、物理トークンを提供している金融機関を事前に見極める判断基準になります。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **GrapheneOS（グラフェンオーエス、セキュリティ重視のAndroid派生OS）**: Googleサービスを排し、端末の堅牢性と利用者のプライバシー保護を目的に開発されているOSです。
- **Play Integrity API（端末完全性検証機能）**: アプリが改変されていない正規のAndroid環境で動作しているかをGoogleが判定する仕組みです。
- **Wero（欧州共通デジタル決済基盤）**: 米系決済サービスへの依存軽減を目指し欧州の大手銀行連合が推進する共通決済システムです。

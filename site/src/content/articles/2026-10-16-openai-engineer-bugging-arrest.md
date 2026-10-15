---
title: "OpenAIのエンジニア、役員室への盗聴器設置で逮捕　最高で禁錮5年"
publishedAt: 2026-10-16T08:52:21+09:00
sourceUrl: "https://sfstandard.com/2026/10/13/openai-engineer-arrested-alleged-bugging-executive-conference-room/"
sourceTitle: "OpenAI engineer arrested in bugging of executive conference room"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50078141"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/sfstandard.com/2026/10/13/openai-engineer-arrested-alleged-bugging-executive-conference-room/"
score: 652
comments: 540
tags: ["openai", "security", "espionage", "hardware"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-15T23:52:21Z
---

## 元記事の要旨

- 米連邦検察は、OpenAI本社の役員会議室に盗聴器を仕掛けた通信傍受容疑で、同社のエンジニアを逮捕したと発表しました。有罪判決を受けた場合、最高5年の禁錮刑と25万ドルの罰金が科される可能性があります。
- 盗聴器はテレビ背面のUSB端子に接続されトイレットペーパーで偽装されており、市販のマイコンボード「Seeed XIAO ESP32-S3 Sense」が使用されていました。端末内のデータは暗号化されていました。
- 容疑者は配偶者と共有するチャットボットアカウントで盗聴器の作成やSDカードの暗号化、対象機器のMACアドレスについて問い合わせていたほか、社内ツールで役員会議の場所などを調査していました。
- OpenAIは社内調査チームが機器を発見後、自社のAIモデルを使って解析した上でFBIに通報し、容疑者を解雇しました。モデルの重みや顧客データへの不正アクセスは確認されていないとしています。

## 議論の論調

### チャットボットの利用履歴が証拠になる点への警戒

容疑者がチャットボットに盗聴器の作成やMACアドレスを尋ねた履歴が捜査で特定されたことに対し、LLMに入力した内容はすべて記録され捜査機関に利用されるリスクを再認識したという意見が多く集まりました。検索エンジンの履歴と同様にプライバシー意識の甘さを指摘する声も上がっています。

### 盗聴手口の稚拙さと国家関与を巡る議論

24ドル程度の市販マイコンを用い、トイレットペーパーで隠した手口があまりに杜撰であることから、高度な産業スパイや国家主導の工作とは考えにくいという見方が出ています。一方で、国家主導の工作員であっても現場の実行犯は素人同然の行動を取ることがあると反論する意見も見られます。

### 事件発表に自社AIの宣伝を交えた姿勢への違和感

OpenAIが盗聴器の特定に自社モデルを活用したと発表したことについて、深刻な情報セキュリティ事件の公表に自社製品の宣伝を織り交ぜているように見え不適切だとする批判が寄せられました。一方で、自社技術でインシデント調査を完遂した証拠だと評価する向きもあります。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **Seeed XIAO ESP32-S3 Sense**: Wi-Fiやマイク、カメラを搭載した、約24ドルで購入できる親指サイズの超小型開発ボードです。
- **MACアドレス（Media Access Control address、機器固有の識別番号）**: ネットワーク機器ごとにハードウェアレベルで一意に割り振られている物理識別子です。

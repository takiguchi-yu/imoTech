---
title: "Goldman Sachs、トレーダーのClaude Code利用を禁止　対象をエンジニアに限定"
publishedAt: 2026-11-10T12:35:14+09:00
sourceUrl: "https://www.thestateofai.com/news/goldman-sachs-claude-code-traders-bankers"
sourceTitle: "Goldman Sachs is pulling Claude Code from its bankers and traders"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50415628"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/www.thestateofai.com/news/goldman-sachs-claude-code-traders-bankers"
score: 884
comments: 452
tags: ["ai-agent", "claude", "security", "fintech"]
model: "gemini-3.6-flash"
generatedAt: 2026-11-10T03:35:14Z
---

## 元記事の要旨

- Goldman Sachsは、これまでトレーダーやバンカーが顧客動向の把握や市場モデルの構築に使っていたAnthropicのClaude CodeやGitHub Copilotの利用をエンジニアのみに制限しました。
- 同行は7月時点で非技術職によるAIツール構築を評価していましたが、十分な検証を経ないコード運用によるセキュリティリスクやデータ保護上の懸念、コスト増を踏まえて社内方針を改定しました。
- 自律的にコードを実行するエージェント型AIは、金融機関に義務付けられている厳格な情報障壁（チャイニーズウォール）やレビュープロセスに抵触する恐れがある点が問題視されています。
- 同行はAnthropicの新規株式公開（IPO）の主幹事を務めていますが、香港での利用制限に続き、職種に応じた厳格な利用権限の管理へと舵を切った形です。

## 議論の論調

### 非技術職のコード生成が招くセキュリティ上のリスク

未検証のコードやローカル端末で動作する自律エージェントが、顧客データへの不正アクセスや規制違反、データ漏洩を引き起こす懸念があるとして、利用制限を合理的とみなす意見が多く見られました。特に金融機関では厳格な情報管理が不可欠であると強調されています。

### 非技術職が作成したプロトタイプの保守に対する不満

業務部門がAIで作成したコードをエンジニアに引き渡す運用について、実際の開発現場では設計の甘さから使い物にならず、修正や再構築の負荷が大きいと批判されました。コードの挙動を正しく理解せずに運用することの危険性も指摘されています。

### AIエージェントの利用によるトークン課金の急増

全社的にエージェント型AIを開放した結果、想定以上のトークン消費が発生し費用が急増している点が取り上げられました。定額制プランと異なり従量課金の管理が難しいため、アクセス制限やモデルの利用抑制が必要になっている実態が語られています。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **バイブコーディング（vibe coding、感覚的にAIにコードを書かせる手法）**: プログラミングの知識がなくても、自然言語による大まかな指示でAIにコードを生成・実行させる開発手法。
- **チャイニーズウォール（Chinese wall、企業内の情報遮断壁）**: 金融機関で利益相反やインサイダー取引を防ぐため、部門間での未公開情報の共有をシステム的・組織的に制限する仕組み。

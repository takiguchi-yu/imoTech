---
title: "Cloudflare、AIエージェント拡大に伴うWebの認証と責任保護の必要性を提示"
publishedAt: 2026-11-08T09:35:12+09:00
sourceUrl: "https://blog.cloudflare.com/trusted-agent-delegation/"
sourceTitle: "Agents aren’t humans (but they kinda are)"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/trusted-agent-delegation/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/trusted-agent-delegation/"
score: 0
comments: 0
tags: ["ai", "security", "authentication", "cloudflare"]
model: "gemini-3.6-flash"
generatedAt: 2026-11-08T00:35:12Z
---

## 元記事の要旨

- 個人向けAIエージェントはユーザーに代わりクラウド等で自動操作を行うツールであり、利用トラフィックが急増しています。従来の人間による閲覧を超える勢いで拡大しており、Webサイト運営者に大きな影響を与えつつあります。
- エージェントが仲介者となることで、サイト側は実際のユーザーを識別して認証したり、不正行為に対する責任を追及したりすることが困難になります。複数人によるアカウント共有や不正購入といったトラブル発生時の追跡が阻害されます。
- エージェント遮断という従来の対策は主流化に伴い困難になります。サイトとユーザーのビジネス関係やセキュリティ責任を仲介経由でも維持するため、身元証明や評判管理を含めた新たな認証メカニズムの確立が必要とされています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **AIエージェントに対応したWebサービスの認証設計を行いたいとき**: 元ユーザーの身元情報や行動責任を仲介経由でも維持する認証モデルを取り入れることで、エージェント経由のアクセスを受け入れつつ不正利用や課金トラブルのリスクを軽減できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **KYC（know your customer、顧客身元確認）**: 法令順守などのためユーザーの本人確認を行う手続きのこと。AIエージェントの仲介により従来の確認手法が機能しにくくなる課題が提示されています。

---
title: "米Vercel、AWSでのBYOC提供開始や社内AI向け統制機能を拡充"
publishedAt: 2026-10-20T09:21:16+09:00
sourceUrl: "https://vercel.com/blog/vercel-for-enterprise"
sourceTitle: "Vercel for Enterprise"
source: "vercel-blog"
discussionUrl: "https://vercel.com/blog/vercel-for-enterprise"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/vercel.com/blog/vercel-for-enterprise"
score: 0
comments: 0
tags: ["vercel", "aws", "cloud", "generative-ai", "security"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-20T00:21:16Z
---

## 元記事の要旨

- Vercelはエンタープライズ向けに「Enterprise Apps and Agents」を拡張し、自社のAWSアカウント内で関数を実行できるBYOC（Bring Your Own Cloud）の一般提供を開始しました。
- IdPと連携した認可機能のパブリックベータを開始し、AIエージェントが従業員の権限スコープに基づいて安全に外部サービスや社内データへアクセスできる仕組みを導入しました。
- AI Gatewayにより複数モデルを単一APIで集約し、個別キーの発行やプロジェクトごとの予算設定、ゼロデータ保持（Zero Data Retention）によるデータ保護を実現します。
- Klaviyoでは2週間で512名の社員が356のアプリを公開し、Vercel自身のサポートエージェントは問い合わせの91%を自律解決するなど、社内外の実績も報告されています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **非エンジニアが社内向け業務ツールを安全に開発したいとき**: IdP連携でアプリをデフォルト非公開にし、外部接続もユーザー権限に基づく一時トークンに制限できるため、情報漏洩を防ぎながら自由な開発を促進できます。
- **社内規定でデータや計算資源を自社クラウド外に出せないとき**: AWS対応のBYOCにより、関数の実行環境を自社AWSアカウント内に維持したままVercelのデプロイ環境や管理画面を利用できるため、コンプライアンス要件を満たせます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **BYOC（Bring Your Own Cloud、自社クラウド持ち込み）**: サービスの実行基盤を自社のクラウド環境内に配置し、データや計算資源を自社の権限管理下に置く運用形態です。
- **IdP（Identity Provider、認証プロバイダー）**: ユーザーの認証情報を一元管理し、複数の外部サービスに対してシングルサインオンなどの認証機能を提供する基盤です。
- **市民開発者（citizen developer）**: 専業のエンジニアではないものの、AIやノーコードツールを使って自身の業務に必要なアプリを自作する従業員を指します。

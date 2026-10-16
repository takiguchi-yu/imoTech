---
title: "Cloudflare、データ基盤の最適化でハードウェア増強を2年半延命"
publishedAt: 2026-10-17T08:35:30+09:00
sourceUrl: "https://blog.cloudflare.com/rewinding-the-exponential/"
sourceTitle: "Rewinding the exponential: How we keep hardware usage down"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/rewinding-the-exponential/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/rewinding-the-exponential/"
score: 0
comments: 0
tags: ["cloudflare", "architecture", "clickhouse", "compression"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-16T23:35:30Z
---

## 元記事の要旨

- Cloudflareは毎秒約20億イベントを処理する自社データ基盤において、指数関数的なトラフィック増加に対し、過去5年間の改善を通じてハードウェア増強を2年半先送りすることに成功しました。
- 2022年には全プロダクトのフィールドを統合していた巨大スキーマをプロダクト別に分割し、バックボーン帯域を35〜40%削減しました。2024年には圧縮アルゴリズムをLZ4からzstdへ移行してスループットを約40%圧縮しました。
- 2026年には災害対策のための二重書き込み構成を見直し、エッジからの送信を1回に集約して中央でサンプリング後に複製する構成へと移行することで、WAN経由のトラフィックを大幅に削減しました。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **大規模分散システムで拠点間転送コストを削減したいとき**: エッジ側での二重送信をやめて中央集約先でサンプリング後に複製する遅延レプリケーション設計を採用することで、WANの帯域消費を大きく削減できます。
- **既存ログ基盤のネットワーク帯域が逼迫しているとき**: 全量ログを流す単一スキーマを消費側ごとに分割し、LZ4からzstdへの変更を段階検証することで、CPU負荷を抑えつつ転送量を圧縮できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **zstd（Zstandard）**: 高い圧縮率と高速な伸張速度を両立させた可逆圧縮アルゴリズムです。
- **サンプリング（抽出処理）**: 高トラフィック下でデータ総量を抑えるため、統計的代表性を保ちながら一部のログを間引く手法です。

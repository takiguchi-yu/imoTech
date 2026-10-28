---
title: "Cloudflare、Workers AIのデータ漏洩バグを修正　155件の応答に他者データ混入"
publishedAt: 2026-10-28T09:33:15+09:00
sourceUrl: "https://blog.cloudflare.com/kv-cache-exposure-remediation/"
sourceTitle: "Cross-request KV cache exposure in the GLM-5.3 Workers AI model, and our remediation with SGLang"
source: "cloudflare-blog"
discussionUrl: "https://blog.cloudflare.com/kv-cache-exposure-remediation/"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.cloudflare.com/kv-cache-exposure-remediation/"
score: 0
comments: 0
tags: ["cloudflare", "sglang", "llm", "security"]
model: "gemini-3.6-flash"
generatedAt: 2026-10-28T00:33:15Z
---

## 元記事の要旨

- Cloudflareは、Workers AIで提供するモデル「GLM-5.3」において、別ユーザーのリクエストデータが混入するKVキャッシュ漏洩問題を修正したと発表しました。影響を受けたのは長文プロンプトに対する155件の応答です。
- 原因は設定不備と推論エンジンSGLangのバグの重複です。設定上のKVキャッシュ容量を超える長文リクエストに対し、SGLangが処理を途中で正しく破棄せず、古いキャッシュを残したまま応答を生成していました。
- CloudflareはKVキャッシュプールを拡張してフルコンテキストに対応させるとともに、SGLangに修正パッチを提供して本流に取り込ませることで、エラー処理時の安全性を確保し再発を防止しました。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **LLM推論エンジンを自作環境で運用するとき**: SGLangなどの推論エンジンで大容量コンテキストを扱う際、コンテキスト長とKVキャッシュ容量の不一致やエラー時の挙動を確認することで、データ漏洩事故を防げます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **KVキャッシュ（Key-Value cache、LLMの計算結果を保持する記憶領域）**: LLMがテキストを生成する際、過去トークンの計算結果を再利用するためにGPUメモリ上に保持しておく記憶領域のことです。
- **SGLang（LLMの推論を高速化するオープンソースエンジン）**: LLMの高速な推論やコンテキスト管理を行うためのオープンソース推論エンジンであり、Workers AIの基盤にも採用されています。

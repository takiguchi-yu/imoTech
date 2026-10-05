---
title: "Vercel、Python向けAI SDKで分類AI「Jev」の実験的APIを提供"
publishedAt: 2026-10-05T08:58:18+09:00
sourceUrl: "https://vercel.com/blog/jev-for-python-engineers"
sourceTitle: "Jev for Python engineers"
source: "vercel-blog"
discussionUrl: "https://vercel.com/blog/jev-for-python-engineers"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/vercel.com/blog/jev-for-python-engineers"
score: 0
comments: 0
tags: ["python", "vercel", "ai-sdk", "classification"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-04T23:58:18Z
---

## 元記事の要旨

- VercelはPython向け「AI SDK」の最新版を公開し、限定的な判断に特化したAIモデル「Jev」を直接呼び出せる実験的API「evaluate()」を追加しました。
- JevはLLMの重みを活用した汎用分類器であり、自由形式のテキスト生成ではなく、多肢選択やスコア評価といった質問に対して構造化JSON形式で高速かつ安価に回答を返します。
- 元記事では、REPLにおける英語とPythonコードの入力自動判別や、抽象構文木（AST）の選択によるコード生成といった実験を通じて、Jevの特性と課題を検証しています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **対話画面でコード入力と自然言語入力を自動判別したいとき**: Jevはテキストを生成せず選択肢に対する確率や判定を高速に返すため、ユーザーの入力内容がプログラミング言語か自然文かを低遅延で識別し、シンタックスハイライトなどを動的に切り替えられます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **AST（abstract syntax tree、抽象構文木）**: プログラムのソースコードの構文を木構造で表現したもの。コードの生成や解析の基盤として使われます。
- **REPL（read-eval-print loop、対話型評価環境）**: 入力されたコードを対話形式で1行ずつ即座に実行し、結果を返すプログラミングの実行環境です。

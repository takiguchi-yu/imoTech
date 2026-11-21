---
title: "Jane Street、指示集「agent_skills」を公開　対話指導を実装"
publishedAt: 2026-11-21T11:15:35+09:00
sourceUrl: "https://github.com/janestreet/agent_skills"
sourceTitle: "agent_skills: Agent skills"
source: "github"
discussionUrl: "https://github.com/janestreet/agent_skills"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/github.com/janestreet/agent_skills"
score: 10434
comments: 0
tags: ["ai-agent", "prompt-engineering", "llm", "education"]
model: "gemini-3.8-flash"
generatedAt: 2026-11-21T02:15:35Z
---

## 元記事の要旨

- 米金融機関のJane Streetは、AIエージェントやチャットボット向けに自社で運用している指示定義の集約リポジトリを公開しました。各スキルはSKILL.mdファイルを持つディレクトリ単位で管理されます。
- 収録されている「socratic-tutor」は、診断テストやレベル0から5の段階別スキルマップ、間隔を空けた復習や最終テストを取り入れ、ソクラテス式問答法でユーザーを指導する対話型チューターを提供します。
- SKILL.md形式に対応したコーディングエージェントのスキル用フォルダに配置して呼び出すか、一般的なチャットボットのシステムプロンプトやチャット欄に内容を貼り付けて利用します。
- 社内業務で日常的に使われ有用性が確認された知見を共有することが目的であり、新規スキルの追加や既存スキルの改変を伴う外部からのプルリクエストは受け付けない方針を示しています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **技術や専門知識をAIとの対話形式で自習したいとき**: socratic-tutorの指示をLLMに読み込ませることで、単なる質問応答にとどまらず、前提知識の診断からレベル別の演習問題まで段階的な個人指導を受けられます。
- **開発支援エージェントに教育機能を組み込みたいとき**: SKILL.md形式に対応したコーディングツールに配置するだけで、Jane Streetが社内で実証した学習進行の枠組みを自前の開発環境へ導入できます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **ソクラテス式問答法（Socratic method、対話により思考を深める教育手法）**: 一方的に答えを教えるのではなく、質問を投げかけて対話を重ねることで学習者自身の思考と理解を促す手法です。
- **間隔反復（spaced review / spaced repetition、間隔を広げた復習法）**: 学習した内容の忘却を防ぐため、一定の期間を空けて段階的に復習を促す記憶定着のための学習設計です。

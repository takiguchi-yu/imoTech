# M7: データソースを増やせる形に再設計する

Hacker News だけに結合している収集層・モデル・表示層を、**ソースを足すだけで増やせる形**に作り替える。

**Status:** 着手
**Blocked by:** なし（M1〜M6 が完了していれば動く）

## なぜやるか

`sources/__init__.py` に `StoryFeed` / `ReactionSource` の Protocol は**最初から切ってある**
（`docs/DESIGN.md` 1.3 の「Strategy（薄く）」）。しかし **`cli.py` がその Protocol を一度も使わず、
`HackerNews` を直接 import してインスタンス化している**（`cli.py:41,66,182`）。
つまり「抽象が無い」のではなく「**抽象を通していない**」。

さらにモデルが HN に結合している。`Story.hn_item_id` / `hn_url`、`Candidate.hn_item_id` /
`hatena_url`、`ArticleDraft.hn_url` / `hn_score` / `hn_comments`。これらは
`candidates.jsonl`（298 行）・記事 12 件のフロントマター・サイトの zod スキーマまで貫いている。

## 想定するソース

Hacker News に加えて **dev.to / Zenn / Qiita**（記事プラットフォーム）を想定する。
HN との違いが設計に効く。

| | Hacker News | Zenn / Qiita / dev.to |
|---|---|---|
| Story の実体 | **外部記事への投稿**（url は他所） | **記事そのもの**（url は自サイト） |
| 議論の場所 | スレッド URL（記事とは別） | 記事ページのコメント欄（記事 URL と同じ） |
| 注目度 | points / comments | LGTM / いいね / reactions |
| 反応 | 議論が主体 | コメントは少なめ |
| API | Algolia（公開） | Qiita: あり / dev.to: あり / **Zenn: 公式 API 無し（RSS）** |

### 規約の確認（2026-09-23 に一次情報を確認）

| ソース | 確認した内容 |
|---|---|
| Qiita | [API v2 docs](https://qiita.com/api/v2/docs): 認証 1000 req/h、非認証 60 req/h/IP。[利用規約](https://qiita.com/terms): 自動アクセスの禁止条項なし。外部サイトによる記事要約の直接的な制限条項もなし |
| Zenn | **公式 API が無い**（RSS のみ）。[利用規約](https://zenn.dev/terms) 第 6 条 3 項「利用者コンテンツについて、権利者の許可を得ることなく、**無断で転載または二次配布等を行うことはできません**」 |
| dev.to | [利用規約](https://dev.to/terms): 「use the materials for any **commercial purpose**, or for any public display」を禁止。ただし "materials" の範囲が曖昧。API 条項は無い |

**dev.to は、はてブ・Reddit と同じ懸念がある**（収益化を前提にしている限り）。
**どのソースを実際に足すかは、この設計とは別に決める。** M7 は「足せる形」を作るところまで。

## 完了条件

### 概念（models）
- [ ] `SourceRef`（`source` + `id`）を導入し、どのソースのどの投稿かを 1 つの値で表すようにした
- [ ] `Engagement`（`score` + `comments`）を導入し、注目度の指標をソース非依存にした
- [ ] `Story` / `Candidate` / `ArticleDraft` から `hn_` 接頭辞のフィールドを無くした
- [ ] `models.py` が **どのソースも知らない**ことを確認した（`hn` / `hatena` / `ycombinator` の grep が 0 件）
- [ ] `hatena_url` の組み立てを `models` から出した（はてブは「元記事 URL から組み立てるリンク」であって Story の属性ではない）

### 抽象（sources）
- [ ] `StoryFeed` Protocol に `permalink(ref) -> str`（議論の URL）を足した
- [ ] **反応を持たないソースを許す**設計にした（`ReactionSource` を実装しないソースがあってよい）
- [ ] `sources/registry.py` に名前 → 具象の Registry を置いた（**Factory Method** を Python の辞書 + 関数に翻訳）
- [ ] 複数ソースを 1 つの `StoryFeed` として扱える **Composite** を置いた
- [ ] 各ソースの生データ → `Story` / `Reaction` の変換を **Adapter** として明示的に位置づけた
- [ ] `HackerNews` を新しい Protocol に適合させた

### 依存の向き（cli）
- [ ] `cli.py` が具象（`HackerNews`）を import しなくなった
- [ ] ソースを設定で切り替えられる（`IMOTECH_SOURCES`）
- [ ] 反応を持たないソースの候補を `compose` がどう扱うか決めて実装した

### 互換性
- [ ] 既存の `data/candidates.jsonl`（298 行）が**そのまま読める**（旧キーからのフォールバック）
- [ ] 既存記事 12 件のフロントマターを移行した（または旧キーを読めるようにした）
- [ ] `site/src/content.config.ts` の zod スキーマを新しい形に合わせた
- [ ] 既存記事が**サイトのビルドを壊さない**ことを確認した

### 表示と匿名化
- [ ] `anonymize.py` の `news.ycombinator.com/user?id=` のハードコードをソース側に移した
- [ ] サイトの「Hacker News」固定の文言をソース非依存にした（`[...slug].astro` / `about.astro` / `index.astro` / `Base.astro`）
- [ ] Notion のプロパティ名を新しい形に合わせた

### パターンの記録
- [ ] `docs/DESIGN.md` に**採用したパターン**と**見送ったパターン**を理由つきで書いた
- [ ] GoF の検討表（`oo-design`）を 1 行ずつ当て、当てた結果を記録した

### 検証
- [ ] `uv run ruff format --check . && uv run ruff check . && uv run pytest -q` が通る
- [ ] `cd site && npm test && npm run build && node scripts/check-unpublished.mjs` が通る
- [ ] **2 つ目のソースを足すのに必要な変更が `sources/` の中だけで済む**ことを、実際にダミーのソースを 1 つ書いて確かめた
- [ ] `docs/DESIGN.md` 1.3 の依存図と 6 節のディレクトリ構成を更新した（現状 `sources/` が 6 節から抜けている）
- [ ] `CONTEXT.md` の `Story` の定義から「Hacker News に投稿された」を外した

## 見つけたときの状況

`sources/` の Protocol は M1 の時点で切られていたが、`cli.py` が一度も使っていなかった。
`docs/DESIGN.md` 5.6 には「将来 RSS ソースを足す場合に備え、`sources/rss.py` に閉じ
`feedparser` で形式差を吸収する」と**実装先まで指定済み**で、設計の意図は一貫している。

M5 に「はてブ・Reddit は収益化の間は不採用。ReactionSource を抽象化してあるので、
方針が変わったときは実装を足すだけで戻せる」とあり、この設計はその前提とも噛み合う。

## 着手できる条件

なし。

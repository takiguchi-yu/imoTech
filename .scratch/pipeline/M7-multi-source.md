# M7: データソースを増やせる形に再設計する

Hacker News だけに結合している収集層・モデル・表示層を、**ソースを足すだけで増やせる形**に作り替える。

**Status:** 完了（`ct-verifier` で 28 件を機械検証し ✅ 27 / ❌ 1。❌ の 1 件は Notion のプロパティ名で、別チケットに切った — 末尾参照）
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
- [x] `SourceRef`（`source` + `id`）を導入し、どのソースのどの投稿かを 1 つの値で表すようにした
- [x] `Engagement`（`score` + `comments`）を導入し、注目度の指標をソース非依存にした
- [x] `Story` / `Candidate` / `ArticleDraft` から `hn_` 接頭辞のフィールドを無くした
- [x] `models.py` から**ソース固有の URL 組み立てロジック**が消えたことを確認した
      （**条件を改訂した。** 元の文言は「`hatena` の grep が 0 件」だったが、`ArticleDraft.hatena_url`
      は**値**として残る — はてブへのリンクは記事に出す情報であって、話題の発見元とは別概念。
      消したのは `Story.hn_url` / `Candidate.hn_url` / `Candidate.hatena_url` の**プロパティ**＝
      組み立てロジックで、それは `links.py` と各ソースへ移した）
- [x] `hatena_url` の組み立てを `models` から出した（はてブは「元記事 URL から組み立てるリンク」であって Story の属性ではない）

### 抽象（sources）
- [x] ~~`StoryFeed` Protocol に `permalink(ref) -> str`（議論の URL）を足した~~
      → **足さなかった。`Story.discussion_url` に値として持たせた。** ソースが組み立てて入れるので、
      `Story` を受け取った側（render / notion / llm）は**ソースを知らずに URL を使える**。
      `permalink` を Protocol に置くと、URL が要るたびにソースを引き回すことになり依存の向きが崩れる
- [x] **反応を持たないソースを許す**設計にした（`ReactionSource` を実装しないソースがあってよい）
- [x] `sources/registry.py` に名前 → 具象の Registry を置いた（**Factory Method** を Python の辞書 + 関数に翻訳）
- [x] 複数ソースを 1 つの `StoryFeed` として扱える **Composite** を置いた
- [x] 各ソースの生データ → `Story` / `Reaction` の変換を **Adapter** として明示的に位置づけた
- [x] `HackerNews` を新しい Protocol に適合させた

### 依存の向き（cli）
- [x] `cli.py` が具象（`HackerNews`）を import しなくなった
- [x] ソースを設定で切り替えられる（`IMOTECH_SOURCES`）
- [x] 反応を持たないソースの候補を `compose` がどう扱うか決めて実装した

### 互換性
- [x] 既存の `data/candidates.jsonl`（298 行）が**そのまま読める**（旧キーからのフォールバック）
- [x] 既存記事 12 件のフロントマターを移行した（または旧キーを読めるようにした）
- [x] `site/src/content.config.ts` の zod スキーマを新しい形に合わせた
- [x] 既存記事が**サイトのビルドを壊さない**ことを確認した

### 表示と匿名化
- [x] `anonymize.py` の `news.ycombinator.com/user?id=` のハードコードをソース側に移した
- [x] サイトの「Hacker News」固定の文言をソース非依存にした（`[...slug].astro` / `about.astro` / `index.astro` / `Base.astro`）
      **検証で取り残しが 1 件見つかり、直した。** `about.astro:13` だけ「Hacker News で議論を呼んだ
      英語圏のテック記事」のままだった（チェックは入っていたが実態が伴っていなかった）。
      ついでに `README.md:3` と `CONTEXT.md:3` も同じ取り残しだったので統一し、
      自己定義を**「Hacker News をはじめとする英語圏のテックコミュニティ」の 1 通りに揃えた**
      （`Base.astro:32` / `index.astro:12,15` / `rss.xml.ts:11` / `about.astro:13` / `README.md:3` / `CONTEXT.md:3`）
- [ ] Notion のプロパティ名を新しい形に合わせた
      **未達。** `PROP_HN_URL = "HN URL"` などの**表示名は据え置いた**。既存 DB の 14 ページと
      整合させるほうを優先している（`notion-setup --dry-run` で差分 0 を実測）。
      入る値は `draft.discussion_url` / `draft.engagement.score` に変えてあるので、
      HN 以外のソースを足すとラベルが実態とずれる。**リネームは既存ページの移行を伴うので別チケット**

### パターンの記録
- [x] `docs/DESIGN.md` に**採用したパターン**と**見送ったパターン**を理由つきで書いた
- [x] GoF の検討表（`oo-design`）を 1 行ずつ当て、当てた結果を記録した

### 検証
- [x] `uv run ruff format --check . && uv run ruff check . && uv run pytest -q` が通る
- [x] `cd site && npm test && npm run build && node scripts/check-unpublished.mjs` が通る
- [x] **2 つ目のソースを足すのに必要な変更が `sources/` の中だけで済む**ことを、実際にダミーのソースを 1 つ書いて確かめた
- [x] `docs/DESIGN.md` 1.3 の依存図と 6 節のディレクトリ構成を更新した（現状 `sources/` が 6 節から抜けている）
- [x] `CONTEXT.md` の `Story` の定義から「Hacker News に投稿された」を外した

## 見つけたときの状況

`sources/` の Protocol は M1 の時点で切られていたが、`cli.py` が一度も使っていなかった。
`docs/DESIGN.md` 5.6 には「将来 RSS ソースを足す場合に備え、`sources/rss.py` に閉じ
`feedparser` で形式差を吸収する」と**実装先まで指定済み**で、設計の意図は一貫している。

M5 に「はてブ・Reddit は収益化の間は不採用。ReactionSource を抽象化してあるので、
方針が変わったときは実装を足すだけで戻せる」とあり、この設計はその前提とも噛み合う。

## 着手できる条件

なし。

---

## レビューで直したもの（2026-09-23）

3 視点のレビューで **Blocker 2 件 / Major 14 件 / Minor 10 件**。採用した分は以下。

### Blocker 1: 束ねたソースで PII の伏せ字が丸ごと効かなくなっていた

**視点 A と C が独立に実証した、この差分が入れた回帰。** `profile_url_pattern(feed)` は
`feed.profile_url_re` を `getattr` で取るだけで、`MultiFeed` はその属性を持たないので**必ず None**。
`anonymize.scrub` は `None` なら伏せ字を飛ばすため、**投稿者のプロフィール URL（ハンドル名を含む）が
そのまま Gemini に渡り、記事にも残る**。M7 以前は `anonymize.py` にハードコードされていて常に効いていた。

- `profile_url_patterns()` に変え、**束ねたソースでは子のぶんをすべて集める**（複数返す）
- `scrub` / `scrub_title` / `anonymize` の**既定値を無くした**。渡し忘れが `TypeError` で落ちる
  （既定 `None` は「安全側の既定」から「危険側の既定」への変更になっていた）
- `tests/test_sources.py` に回帰テストを足した

```
単一 HackerNews  : ハンドル残存 = False
MultiFeed([...]) : ハンドル残存 = False   （直す前は True）
```

### Blocker 2: `.env.example` が存在しないソース名を指していた

`例: hackernews,qiita` と書いていたが `_FACTORIES` には `hackernews` しか無く、
**コピーしてコメントを外すと `collect` が落ちる**。ドキュメントが誤った操作に誘導していた。

### Major（採用）

| 指摘 | 直した内容 |
|---|---|
| `StoryFeed` Protocol にコンテキストマネージャの契約が無いのに `cli` が `with` で使う。ダミーソースは `__enter__` を持たないので**実際に cli を通すと落ちる** | `opened()` を置き、`close()` を持つソースだけ閉じる。どちらの形のソースでも足せる |
| 単一ソース経路で `ref.source` を検証していない（Composite と非対称）。**ID が数値のソースを足すと別記事を掴む** | 各ソースの `fetch_reactions` 先頭で確かめる |
| `MultiFeed` の `except Exception` で、**全ソースが落ちても exit 0**。無人実行では Issue が立たない | 全部落ちたら再送出する |
| 反応を取れないソースだけの構成で、compose が**無言で成功**し永久に記事が出ない | 設定ミスとして終了コード 2 で落とす |
| `supports_reactions(MultiFeed)` が、子が全部非対応でも True | 子を再帰的に見る |
| 旧形式の記事が 1 件混ざると **zod の必須チェックでサイトのビルド全体が落ちる**（Python 側は旧キーを読めるのに非対称） | CI に「記事のフロントマターが新形式であること」の検査を足した |
| 旧形式 `candidates.jsonl` のフォールバックに**テストが 1 件も無い**（本番 298 行が依存） | `tests/test_store.py` に 3 件足した |
| 設定ミスがトレースバックで出る | `main()` で捕まえて 1 行にし、メッセージに `IMOTECH_SOURCES` を入れた |
| 複数ソース時のログが `ソース: multi` だけで内訳が分からない | `multi(hackernews,qiita)` の形にした |
| DESIGN の「触る範囲」にサイト側（`site/src/lib/sources.ts`）が抜けていた | 手順を 3 段に分けて明記 |
| 注目度の単位「points」がハードコードで、Qiita では嘘になる | `sources.ts` に `scoreUnit` を持たせた（Qiita は LGTM、Zenn はいいね） |
| RSS の説明文だけ「Hacker News」のまま取り残し。サイト・README・CONTEXT で自己定義が 3 通り | 「Hacker News をはじめとする英語圏のテックコミュニティ」に統一 |
| ソース非依存化で「何のサイトか」が薄まった | 具体（Hacker News）を残しつつ拡張余地を作る表現にした |
| `CONTEXT.md` の `_Avoid_: スコア` が自分の定義文でも違反 | `score` は正式な構成要素なので `_Avoid_` から外した |
| 同名のソースを 2 つ束ねられた | `dict.fromkeys` で重複を除く |

### Minor（見送り、申し送りへ）

`MultiFeed.close()` が 1 つ目の例外で残りを閉じ損ねる / `runtime_checkable` が非 callable を
素通しする / `Candidate.discussion_url` が書き込み専用 / `limit` の意味が単一と Composite で違う。

## 申し送り

- **ロールバックは candidates.jsonl とセット。** この差分をデプロイして `daily.yml` が 1 回走ると、
  `hn_item_id` がファイルから消える（前進移行）。**commit だけ revert すると全 298 行で `KeyError` に
  なりパイプラインが止まる。** 戻すときは `data/candidates.jsonl` も同じコミットまで戻すこと
- **Notion のプロパティ名（`HN URL` など）は据え置き。** HN 以外のソースを足すとラベルが実態と
  ずれる。リネームは既存 14 ページの移行を伴うので `M8-notion-props.md` に切った
- **`limit` の意味が経路で違う。** `HackerNews` は `max_pages=5` まで追うので最大 5×limit 件返すが、
  `MultiFeed` は結合後に `limit` で切る。ソースを 1 つ足すと HN の収集件数が減る
- **`Candidate.discussion_url` は書き込み専用**。記事に出る議論 URL は `story.discussion_url` から
  取るので、候補側の値は誰も読んでいない。記録として残している
- **dev.to は規約に「commercial purpose」の禁止がある**（はてブ・Reddit と同じ懸念）。
  Zenn は公式 API が無く第 6 条 3 項に無断転載の禁止がある。Qiita が最も素直。
  **どれを実際に足すかは、この設計とは別に決める**

## 検証（2026-09-23）

`ct-verifier` に完了条件 28 件を 1 件ずつ渡し、**チェック済みかどうかを根拠にせず**実行で判定させた。

| | 件数 |
|---|---|
| ✅ 充足 | 27 |
| ❌ 未充足 | 1（Notion のプロパティ名 — 別チケット） |
| ⚠️ 機械検証不能 | 0 |

**検証で見つかって直したもの**

- `about.astro:13` の説明文が旧文言のまま取り残されていた。**チェックが入っているのに実態が
  伴っていなかった 1 件**。同じ取り残しが `README.md:3` / `CONTEXT.md:3` にもあったので合わせて直した

**PII の回帰確認（レビューで直した最重要の指摘）**

束ねたソースで投稿者ハンドルの伏せ字がスキップされる不具合が直っていることを、実行で確かめた。

```
単一 ハンドル残存 = False
束ね ハンドル残存 = False
```

`scrub` / `scrub_title` / `anonymize` は `profile_url_res` を省くと `TypeError` になる
（渡し忘れが静かに PII を残さない）。`anonymize.py` に `news.ycombinator.com` のハードコードは無い。

**実測（すべて再実行可能）**

| 検査 | 結果 |
|---|---|
| `uv run ruff format --check . && uv run ruff check .` | 57 files already formatted / 指摘なし |
| `uv run pytest -q` | 355 passed |
| `cd site && npm test` | tests 17 / pass 17 |
| `npm run build` | 8 page(s) built |
| `node scripts/check-unpublished.mjs` | 記事 12 件（imo 未記入 11 件）／出力への漏れなし |
| `data/candidates.jsonl` 298 行の load→save→load | 298 行一致、本番ファイルは無変更 |
| `IMOTECH_SOURCES=nosuchsource uv run imotech collect` | 1 行のメッセージ + exit 2（トレースバックなし） |
| `grep -n "hackernews\|HackerNews" src/imotech/cli.py` | 0 件 |
| `grep -l "hnUrl:\|hnScore:\|hnComments:" site/src/content/articles/*.md` | 0 件 |
| GitHub Actions CI（`4e8d781`） | サイト・パイプラインとも success |

Composite の挙動も実行で確かめた — 全ソース失敗で `RuntimeError`、同名ソースは `dict.fromkeys` で
重複排除、`supports_reactions` は子を再帰的に見る、`opened()` は `close()` を持たないソースでも動く。

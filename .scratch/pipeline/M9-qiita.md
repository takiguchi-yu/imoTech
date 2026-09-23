# M9: 2 つ目のデータソースとして Qiita を足す

M7 で「ソースを足すのに `sources/` の中だけで済む」形に再設計した。**その主張を実地で
検証すること**が、このチケットの裏の目的。

**Status:** 完了（`ct-verifier` で完了条件 30 件を機械検証し ✅ 30 / ❌ 0 / ⚠️ 0）
**Blocked by:** なし（M7 が完了していれば動く）

## 調べて分かったこと（2026-09-23 に一次情報で確認）

### Qiita API v2

| 項目 | 実測・出典 |
|---|---|
| 記事一覧 | `GET /api/v2/items`（`page` 1〜100、`per_page` 1〜100、`query`） |
| 検索の書式 | `stocks:>N` / `created:>=YYYY-MM-DD` / `tag:` / `user:`（[検索オプション](https://help.qiita.com/ja/articles/qiita-search-options)） |
| **LGTM では絞れない** | `likes:` にあたる条件が無い。ストック数で母数を絞って手元で見るしかない |
| コメント | `GET /api/v2/items/:item_id/comments`。`id` は**20 桁の 16 進**、`rendered_body` が HTML |
| レート | 非認証 60 req/h/IP、認証 1000 req/h。`Rate-Limit` / `Rate-Remaining` / `Rate-Reset` ヘッダ |
| **超過時の応答** | **429 ではなく 403** + `{"message":"Rate limit exceeded","type":"rate_limit_exceeded"}`（実測） |
| robots.txt | `Disallow: /api/*` かつ `Allow: /api/*/docs$` |

**`robots.txt` の解釈**: 検索エンジンのクローラに API レスポンスをインデックスさせない
ための指定であって、公式 API の利用を禁じたものではないと読む。Qiita はトークン認証と
レート制限を備えた API をドキュメント付きで公開しており、API の利用自体は想定内である。
利用規約（[qiita.com/terms](https://qiita.com/terms)）にも自動アクセスの禁止条項は無い。
**この判断はユーザーの承認を得ている。**

### Qiita が Hacker News と決定的に違うところ

実測（2026-09-23）で分かったことが、そのまま設計を決めた。

| 観測 | 実測値 | 設計への影響 |
|---|---|---|
| コメントがほぼ付かない | `created:>=2026-09-16 stocks:>3` の **56 件中、0 件が 46 件（82%）**、最多 9 | 論調ゼロを許す形にした |
| そのコメントも議論ではない | 最多 9 件の記事で、**3 件が著者自身の作業メモ**、他は質問と謝辞 | 同上。Qiita で「議論の論調」は期待しない |
| 投稿直後は LGTM が付かない | 直近 24h の記事で**最大 6 LGTM** | 収集時に LGTM で切らない |
| 記事 URL に著者名が入る | `qiita.com/<user_id>/items/<id>` | **PII**。`Story.author` を足して伏せる |
| 熟成後は伸びる | 同じ 56 件（`stocks:>1` の上位 100 件）で LGTM>=30 が 14 件 ≒ **1 日 2 件** | `Qiita.default_thresholds = Thresholds(30, 0)` |

### 論調を外部から補えないか（ユーザーからの問い）

Qiita のコメントで論調が作れないなら、同じ技術の議論を別の場所から取れないかを調べた。

| 候補 | 一次情報 | 判定 |
|---|---|---|
| はてなブックマーク | Developer Center 利用規約 第4条1項が商用目的を禁止 | ✕（収益化前提のため） |
| Reddit | 同上の判断で除外済み（M0 の記録） | ✕ |
| **Lobsters** | JSON API は動く（`/hottest.json` が HTTP 200）が、`robots.txt` が `User-agent: * / Disallow: /` かつ **`Content-Signal: ai-input=no, ai-train=no`** | ✕ **AI への入力を明示的に拒否している** |
| Bluesky | `app.bsky.actor.getProfile` は 200 だが `app.bsky.feed.searchPosts` は **403**（未認証不可）。利用規約に商用禁止・スクレイピング禁止の条項は見当たらず | △ app password が要る。実効性は未測定 |
| Mastodon | `GET /api/v2/search` の投稿検索は認証 + ElasticSearch バックエンドが必要。そのインスタンスが知る範囲のみ | ✕ 網羅性が無い |
| X | pay-per-usage・クレジット制。`docs.x.com/x-api/pricing` は 404 で単価不明 | △ 未確認 |

**結論: 今回は補わない。** 反応が無ければ論調節を省く形にした。

## 完了条件

### ソース
- [x] `src/imotech/sources/qiita.py` を書いた（`StoryFeed` + `ReactionSource`）
- [x] `registry.py` の `_FACTORIES` に 1 行足した（`IMOTECH_SOURCES=qiita` で切り替わる）
- [x] `Story.url == Story.discussion_url`（記事プラットフォームでは議論の場所が記事ページ自身）
- [x] 注目度は LGTM（`likes_count`）、ストック数は検索で絞るためだけに使う
- [x] 非公開記事・必須項目を欠く記事・期間外の記事を落とす

### PII（最優先）
- [x] `PROFILE_URL_RE` が `qiita.com/<user_id>` に当たり、**記事 URL には当たらない**（出典が消えないため）
- [x] **記事の著者を伏せ字の対象に入れた** — `Story.author` を足し、`anonymize.scrub_url` /
      `anonymize.anonymize` が `extra_handles` で受け取る。**既定値を置いていない**ので渡し忘れは `TypeError`
- [x] 束ねたソース（`MultiFeed`）でも Qiita のプロフィールパターンを集める（M7 の回帰テストを拡張）

### 閾値
- [x] `models.Thresholds` を足し、`pipeline.select` がソースごとに引く
- [x] `Qiita.default_thresholds = Thresholds(30, 0)`（コメント数を見ない）
- [x] `IMOTECH_SOURCE_THRESHOLDS`（JSON）で上書きできる。壊れた JSON は落とす
- [x] **Hacker News は既定を持たず共通設定に倒れる**（`IMOTECH_MIN_SCORE` が従来どおり効く）

### 反応が無い記事
- [x] `build_response_schema(with_discourse=False)` が `discourse` をスキーマから外す
- [x] プロンプトが「この記事には反応がありません」と明示する
- [x] `render.to_markdown` / `notion.build_blocks` が空の見出しを作らない
- [x] 論調が空の Markdown を `from_markdown` が読み戻せる（往復で壊れない）

### レート制限
- [x] **403 + `type: rate_limit_exceeded`** をレート超過として扱い、リトライしない
- [x] `Rate-Remaining` を覚え、尽きたら以降のリクエストを送らない
- [x] 警告は 1 回だけ出す（候補の数だけ並ぶとログが読めない）
- [x] コメント数が 0 なら `/comments` を呼ばない（1 候補あたり 2 → 1 リクエスト）

### ソース非依存化（今回見つかった書き残し）
- [x] `Reaction.comment_id` を `int` → `str`（Qiita は 20 桁の 16 進）
- [x] `prompts/compose.md` から「Hacker News」を外した
- [x] `llm.build_user_prompt` の「## Hacker News の反応」を `story.ref.source` から作る
- [x] `cli` の「HN から N 件取得」を `feed.name` にした

### 検証
- [x] `uv run ruff format --check . && uv run ruff check . && uv run pytest -q` が通る
- [x] `cd site && npm test && npm run build && node scripts/check-unpublished.mjs` が通る
- [x] **実際に Qiita から収集できる**（本番の候補ストアを汚さずに確認）
- [x] **束ねた形（`hackernews,qiita`）で compose が動く**（`--dry-run`、LLM も Notion も呼ばない）
- [x] `docs/DESIGN.md` に「2 つ目のソースで実際に何が起きたか」を記録した
- [x] README / `.env.example` / CONTEXT を更新した

## 着手できる条件

（完了済み）

## 申し送り

- **本番ではまだ有効にしていない。** `IMOTECH_SOURCES` の既定は `hackernews` のまま。
  切り替えるときは `IMOTECH_SOURCES=hackernews,qiita` を Actions の env に足す
- **非認証の 60 req/h が実運用の天井。** `IMOTECH_MAX_PROBES_PER_RUN=60` と合わせると
  ちょうど使い切る。実際に検証中に使い切って 403 が多発した（そのための打ち切りを実装済み）。
  **GitHub Actions の IP は共有**なので、他の利用者と競合する可能性もある。
  常用するなら Qiita のアクセストークンを発行して 1000 req/h にするのが素直
  （`Qiita(token=...)` は実装済みだが、**トークンを設定から渡す配線はまだ無い**）
- **Qiita 記事の「質」は未検証。** dry-run でプロンプトまでは確認したが、実際に Gemini に
  投げて記事を作ってはいない。論調の無い記事が読み物として成立するかは、1 本作ってみないと分からない
- **Bluesky は測っていない。** 論調を補える可能性は残っているが、app password の発行が要る。
  やるなら別チケット
- **`min_points` を Qiita が使っていない。** Protocol の形を満たすために受け取るだけ。
  3 つ目のソースで同じことが起きるなら、`fetch_stories` の引数の設計を見直す余地がある

## レビューで直したもの（2026-09-23）

3 視点（正確性 / 利用者目線 / リスク）で並列にレビューし、Blocker 6 件・Major 9 件を直した。

### Blocker

| 指摘 | 直したこと |
|---|---|
| **`PROFILE_URL_RE` が実在するユーザーページを取りこぼす** — `qiita.com/<id>/likes` `/followers` `/stocks` `/contributions` がいずれも HTTP 200 で実在するのに伏せられない | サブパスを含む形に直し、`/items/<id>`（元記事）だけを除外するようにした |
| **3 文字以下・英単語と同じ綴りの著者 ID が URL から伏せられない** — `qiita.com/ken` `qiita.com/abc` は実在する。`_MIN_HANDLE_LEN` と `_COMMON_WORDS` が `extra_handles` にも効いていた | `_scrub_in_url` の**パス区画**には除外を当てないようにした（区切り文字に挟まれていて曖昧さが無い）。ホスト名側は誤爆しうるので従来どおり |
| **テストのフィクスチャに実在する Qiita アカウント ID が入っていた** | 架空の ID に置換（**組織規定「PII を含めない」に抵触**していた） |
| **反応の取得失敗を「反応ゼロ」と誤認** — `/items/:id` は成功したが `/comments` が失敗すると、議論のある記事が「反応なし」で確定的に書き出され、drafted になって二度と作り直されない | `(None, [])` を返して判定不能にし、候補を pending のまま次回へ回す |
| **README に「本番で Qiita を有効にする」導線が無い** — `daily.yml` の collect と compose の両方に env が要り、片方だけだとエラーも出ず毎日 0 本になる | `daily.yml` の **job レベル**に `IMOTECH_SOURCES` を置き、**1 箇所で切り替わる**ようにした。README に「ソースを増やすとき」の節を追加 |
| **レート見積もりの誤り** — README は「60 を超えないこと」だったが、collect の検索（最大 3 ページ）と compose の問い合わせ（最大 60）が同じ枠を食うので既定値のままで超える | 「Qiita を使うときは 40 以下に下げる」に訂正し、`daily.yml` にも注記 |

### Major

| 指摘 | 直したこと |
|---|---|
| 元記事本文（= 著者本人のページ）に著者ハンドルが残る経路 | `ArticleFetcher.fetch` が `extra_handles` を受け取るようにした |
| `scrub_title` だけ `extra_handles` を受け取らない | 必須引数で追加 |
| **cli の PII 配線に自動テストが無い**（戻しても全テストが通る） | `cmd_compose` を dry-run で通し、プロンプトに著者ハンドルが出ないことを見る回帰テストを 6 本追加。**わざと配線を壊して 5 件落ちることを確認済み** |
| ソース名・項目名の打ち間違いが黙殺される | 未知のソース名（`cli`）と未知の項目名（`config`）を `ValueError` にした |
| 設定ミスが 60 リクエスト使い切った後に落ちる | `_dispatch` の冒頭で検証し、`_resolve_thresholds` も問い合わせの前に移した |
| `imotech stats` がソースを混ぜて 1 本の閾値と比べ、誤った助言を出す | ソース別に集計し、各ソースの実効閾値と比べるようにした |
| レート枯渇の警告に「次に何をすればいいか」が無い | `Rate-Reset` を覚えて回復時刻（JST）を出し、`IMOTECH_MAX_PROBES_PER_RUN` を下げる案内を入れた。README の「記事が出ない日」にも項目を追加 |
| プロンプトの `title` 指示（「議論の争点を含めよ」）が反応ゼロのルールと矛盾 | `title` にも反応ゼロの例外を書いた |
| **CONTEXT.md に「論調 (Discourse)」が既にあるのに重複して定義していた** | 既存の定義に 1 文足して統合し、重複を削除 |
| `docs/DESIGN.md` の新設節が 1 章にあり「1 節 1 目的」に反する | 閾値を **4.1b** へ、論調ゼロを **2.3 / 2.4 / 2.5** へ、レート制限を **5.3b** へ移し、1.3 には依存の向きの説明だけ残した |

### Minor（直したもの）

4xx を 3 回リトライしてレート予算を浪費 / ページ間で重複した記事を二重に数える /
タイトルが空の記事を拾う / `--dry-run` が実際と違うスキーマを出す /
送信パラメータ（`query` `per_page`）を検証するテストが無い。

### Minor（見送り、申し送りへ）

- **未評価のまま期限切れになった候補が `BELOW_THRESHOLD` として打ち切られる。**
  レート枯渇が数日続くと、一度も測れていない候補が「閾値未満」として記録される。
  別の `SkipReason` を足すのが筋だが、本番で Qiita を有効にするまでは起きない
- **`fetch_stories` が全滅しても例外を投げず `collect` が exit 0 になる。**
  Qiita 固有ではなく Hacker News も同じ（既存の性質）。ソースが増えた今は
  「片方だけ死んでいる」が見えにくいので、別チケットで扱う

## 検証（2026-09-23、コミット `21be133`）

`ct-verifier` に完了条件 30 件を 1 件ずつ渡し、**チェック済みかどうかを根拠にせず**実行で判定させた。

| | 件数 |
|---|---|
| ✅ 充足 | 30 |
| ❌ 未充足 | 0 |
| ⚠️ 機械検証不能 | 0 |

**PII の回帰確認（最優先）**

| 検査 | 結果 |
|---|---|
| `PROFILE_URL_RE` が `/likes` `/followers` `/stocks` `/contributions` `/items` に当たる | ✅ |
| 同パターンが `/items/<20桁hex>`（元記事）・`tags/` `api/` に当たらない | ✅ |
| 3 文字以下・英単語と同じ綴りの著者 ID が URL から伏せられる（`abc` `ken` `what` `code`） | ✅ 全て伏せられる |
| 束ねたソースで両方のパターンを集める | ✅ 2 件 |
| `scrub` / `scrub_title` / `scrub_url` / `anonymize` / `handles_of` の引数省略 | ✅ 5 つとも `TypeError` |
| **cli の配線をわざと壊すと回帰テストが落ちる** | ✅ **5 failed / 45 passed**（壊した後 `git checkout` で復元、`git status` クリーン） |
| 今回の差分に実在アカウント ID が無い | ✅ フィクスチャは `alice` / `bob` / `carol123` / `someuser` / `someone` のみ |

**設定ミスの検出（すべて 1 行のメッセージ + exit 2、トレースバックなし）**

| 入力 | 出力 |
|---|---|
| `IMOTECH_SOURCE_THRESHOLDS='{壊れた'` | `... JSON として読めません` |
| `{"qiita":{"minscore":50}}` | `... 'qiita' に知らない項目 minscore があります。使えるのは min_comments, min_score` |
| `IMOTECH_SOURCES=nosuchsource` | `... 知らないソース 'nosuchsource' があります。使えるのは hackernews, qiita` |
| `{"hackernwes":{"min_score":1}}` | `ValueError: ... 知らないソース hackernwes` |

**後方互換**

- 本番 `data/candidates.jsonl` 298 行がそのまま読める（本番ファイルは無変更）
- 既存記事 12 件が `load_article` を通る
- `IMOTECH_MIN_SCORE=77 IMOTECH_MIN_COMMENTS=5` が Hacker News に従来どおり効く

**実データでの end-to-end**

```
qiita から 33 件取得 / 新規 33 件を追加
閾値 hackernews: score>=100 かつ comments>=30 / qiita: score>=3 かつ comments>=0 → 選出 1 件
    本文 8000 文字 (trafilatura) / 反応 0 件
URL: https://qiita.com/[ユーザー名]/items/7306e0b1a9207e08d86e   ← 著者ハンドルが伏せられている
**この記事には反応がありません。** `discourse` は出力しないでください。
スキーマの properties: ['digest', 'glossary', 'slug_hint', 'tags', 'title']   ← discourse が外れている
```

**その他**

| 検査 | 結果 |
|---|---|
| `uv run ruff format --check . && uv run ruff check .` | 61 files already formatted / 指摘なし |
| `uv run pytest -q` | 439 passed |
| `cd site && npm test` | tests 17 / pass 17 |
| `npm run build` / `check-unpublished.mjs` | 8 page(s) built / 漏れなし |
| GitHub Actions CI（`21be133`） | サイト・パイプラインとも success |
| `cli.py` が具象を import / インスタンス化しない | ✅ 0 件（コメント内の固有名詞 2 件のみ） |

### 検証で新たに分かった申し送り

- **`tests/test_anonymize.py` に実在ハンドルが 12 箇所ある**（`tests/test_sources.py` にも 4 箇所）。
  いずれも**今回より前**から入っている（`git log -S` で M1 の `5e6d077` と M7 まで遡れる）。
  実データで起きた匿名化の事故を再現するために入れたもので、コメントに経緯が書いてある。
  組織規定「PII を含めない」に照らすと精査の価値があるが、**今回の差分の範囲外**なので手を付けていない

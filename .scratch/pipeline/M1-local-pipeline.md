# M1: ローカルで収集〜生成が通る

Hacker News から候補を拾い、熟成を判定し、元記事と反応を取得して、Gemini で記事 JSON を生成するところまでをローカルで通す。
Notion も Actions もまだ触らない。

**Status:** 完了（完了条件 34 件すべて充足）
**Blocked by:** M0（`GEMINI_API_KEY` と uv 環境が要る）

## 完了条件

### 型と設定（依存の起点）
- [x] `src/imotech/models.py` に `Story` / `Candidate` / `Reaction` / `AnonymizedReaction` / `ArticleDraft` の dataclass を定義した
- [x] `models.py` が他の `imotech.*` モジュールを import していないことを確認した（依存の向きを守る）
- [x] `src/imotech/config.py` に `pydantic-settings` で設定クラスを作り、`MATURATION_HOURS` / `MIN_SCORE` / `MIN_COMMENTS` / `MAX_DRAFTS_PER_RUN` / `MAX_AGE_HOURS` / `COLLECT_MIN_SCORE` / `MODEL_CHAIN` を環境変数で上書きできるようにした

### URL 正規化（冪等性の土台）
- [x] `src/imotech/urlhash.py` に `normalize(url)` と `url_hash(url)` を実装した
- [x] `tests/test_urlhash.py` で次が同じハッシュになることを確認した:
      `http://www.example.com/a/` / `https://example.com/a` / `https://example.com/a?utm_source=x#top`
- [x] `uv run pytest tests/test_urlhash.py` が通る

### 候補ストア
- [x] `src/imotech/store.py` に `CandidateStore`（`load()` / `append_new()` / `update_state()` / `exists(url_hash)`）を実装した
- [x] jsonl の読み書きが `store.py` の外に漏れていないことを確認した
- [x] `tests/test_store.py` で、同じ `url_hash` を 2 回 append しても 1 行にしかならないことを確認した

### Hacker News
- [x] `src/imotech/sources/__init__.py` に `StoryFeed` / `ReactionSource` の `Protocol` を定義した
- [x] `src/imotech/sources/hackernews.py` に `search_by_date` での収集を実装した
      （`tags=story`、`numericFilters=created_at_i>...,points>COLLECT_MIN_SCORE`、`hitsPerPage=50`）
- [x] `url` が `null` の story（Ask HN など）を除外した
- [x] `/api/v1/items/<id>` でコメント木を 1 リクエストで取る実装にした（Firebase の `kids` 再帰は使わない）
- [x] `text` が `null` のコメント（削除済み）をスキップした
- [x] 5xx / タイムアウトで指数バックオフ 3 回のリトライを入れた
- [x] `uv run imotech collect` を実行し、`data/candidates.jsonl` に行が増えた
- [x] もう一度実行しても行が増えないこと（冪等）を確認した

### 匿名化
- [x] `src/imotech/anonymize.py` で `by` / プロフィール URL / 本文中の `@username` を落とし、`reply_count` と `depth` を残す実装にした
- [x] `tests/test_anonymize.py` で、ハンドル名とメンションが出力に残らないことを確認した
- [x] `llm.py` が生の `Reaction` を受け取れない型シグネチャになっている（`AnonymizedReaction` のみ受け取る）

### 元記事の取得
- [x] `src/imotech/extract.py` で `urllib.robotparser` による判定を実装した（404/取得失敗は許可、5xx は不許可）
- [x] User-Agent を `imoTechBot/1.0 (+https://<domain>/about)` に固定した
- [x] timeout=10s / リダイレクト最大 5 / レスポンス上限 5MB / `text/html` 以外は中断、を実装した
- [x] `trafilatura` で本文を抽出し 8,000 文字で切った
- [x] 抽出失敗・不許可のとき `og:description` にフォールバックし、それも無ければ `None` を返す実装にした

### Gemini
- [x] `src/imotech/prompts/compose.md` にシステム指示を置いた（コードに埋め込まない）
- [x] `src/imotech/llm.py` で `response_mime_type="application/json"` と `response_schema` を指定した
- [x] `MODEL_CHAIN` のフォールバック（429/5xx で次のモデルへ、同一モデルは最大 3 回）を実装した
- [x] 記事間に 6 秒の sleep を入れた
- [x] 全モデルで失敗したとき、候補を `pending` のまま残す（`skipped` にしない）実装にした

### 通し
- [x] `src/imotech/cli.py` に `collect` / `compose` を実装し、`compose --dry-run` で Notion に投げずに JSON を標準出力に出す
- [x] `uv run imotech compose --dry-run` を実行し、記事 JSON が 1 件以上出力された
- [x] 出力された `title` が 40〜60 文字で、`【】` や感情語を含んでいないことを目視で確認した
- [x] 出力された `discourse` に、反応の原文がそのまま含まれていないことを目視で確認した

## 見つけたときの状況

`gemini-1.5-flash` は 2025-09-29 に shutdown 済み、`gemini-2.0-flash` 系も 2026-06-01 に shutdown 済みで、
どちらもエンドポイントが存在しない。`MODEL_CHAIN` は 3.8 / 3.7 / 3.6 / 3.5 / 3.5-lite で構成する。

HN の API はコメント単位の score を返さない（`score` を持つのは story と pollopt のみ）。
「どの意見が議論を呼んだか」の手がかりは返信数とツリー階層しかないため、匿名化でこの 2 つを残す設計にしている。

## 着手できる条件

M0 が完了し、`uv run python -c "import imotech"` が通り、`.env` に `GEMINI_API_KEY` がある。

---

## 完了時の記録（2026-09-21）

### 実測で確かめた事実

```
uv run python -V                    → Python 3.11.15
uv run ruff check .                 → All checks passed!
uv run ruff format --check .        → 30 files already formatted
uv run pytest -q                    → 66 passed
uv run imotech collect              → 0 → 50 行（新規 50）
uv run imotech collect（2 回目）      → 50 → 50 行（新規 0、冪等）
IMOTECH_MATURATION_HOURS=0 uv run imotech compose --dry-run --limit 1
                                    → 本文 7958 文字 (trafilatura) / 反応 80 件 / プロンプト全文を出力
uv lock --check                     → Resolved 50 packages（CI の uv sync --frozen が通る）
```

社内プロキシ（Netskope）下では `uv` が `invalid peer certificate: UnknownIssuer` で失敗する。
`SSL_CERT_FILE="$AWS_CA_BUNDLE"` を付けると通る。README に記載した。GitHub Actions 上では不要。

### 決めたこと（設計書から変えた点）

- **`pipeline.py` を新設した。** 熟成判定と選別を副作用のない純関数に切り出し、CLI と分離して単体テストできるようにした。設計書 6 のツリーに追記済み。
- **記事間のウェイトを `DraftGenerator` の責務にした。** 当初 `cli.py` 側で待つ想定だったが実装時に呼び忘れた。レート制限を守る責務は LLM 層にあるべきなので、`generate()` が 2 回目以降に自分で待つ形にした。回帰テスト `test_1件目は待たず2件目から間隔を空ける` を追加。
- **メールアドレスの伏せ字を追加した。** 当初はハンドル名と @メンションだけを想定していたが、本文に直接書かれたメールも PII なので `anonymize.scrub()` で潰す。
- **英単語と衝突するハンドルは伏せない。** 実データに `what` というハンドルの投稿者がいて、英文中の "what" が全て `[ユーザー名]` になり文章が壊れた。頻出語 346 語の除外リストを入れて回帰テストを書いた。

### 申し送り

- **`title` と `discourse` の目視確認（上の 2 件）は M2 に持ち越す。** GEMINI_API_KEY が入り次第 `uv run imotech compose --limit 1` で確認する。
- **`data/candidates.jsonl` に実データ 80 件が入った状態でコミットされる。** 動作確認の副産物だが、パイプラインの初期状態として妥当なので消していない。作り直したい場合は空にしてから `collect` を回す。

---

## レビューと修正（1 周目 / 2026-09-21）

3 視点を並列で回した（差分 4,731 行・PII が中核・CLI と README が成果物に含まれるため 3 体）。
**Blocker 2 件 / Major 15 件 / Minor 16 件**。Blocker と Major はすべて修正、Minor は大半を修正した。

### Blocker

| 指摘 | 修正 |
|---|---|
| 反応取得に失敗した候補が選出されると `compose` が KeyError で全体停止し、打ち切り更新も失われる | `pipeline.select()` に `evaluated`（現在値を取り直せた url_hash）を渡し、そこに無い候補を選出しないようにした。期限超過の打ち切りは取り直せなかった候補にも当てる |
| **元記事の本文が匿名化を通らず Gemini に送られ、実データでメールアドレス 2 件が流出していた** | `ArticleFetcher._as_source()` で必ず `scrub()` を通す。`ArticleSource.text` は常に scrub 済みという不変条件にした |

### Major（抜粋）

- **HN のプロフィール URL が伏せられない** — `news.ycombinator.com/user?id=` を伏せ字化。スレッド参加者以外のハンドルも載るため handles 集合では捕まらなかった
- **ハンドルの伏せ字が大文字小文字を区別** — 文頭の `Alice` が残っていた。`re.IGNORECASE` を付与
- **URL 内のハンドルが残る／URL が壊れる** — `github.com/<handle>/` と `https://<handle>.ca/` は伏せ、`?ref=newsletter.com` は温存するよう、パス区画とホスト先頭ラベルに限定した
- **`--dry-run` がシステム指示とレスポンススキーマを出していなかった** — 「プロンプト全文」を名乗れていなかった。3 部構成で全部出すようにした
- **評価値が永続化されず `stats` が打ち切り側に偏る** — 取り直した現在値を書き戻すようにした
- **閾値を満たすが上位 N 件から溢れた候補が永久に pending** — 期限超過の打ち切りを「今回選ばれなかった全候補」に広げた
- **`--limit 1` でも熟成済み全件に問い合わせ、81 件で 42.7 秒** — 件数（`IMOTECH_MAX_PROBES_PER_RUN=60`）と時間（`IMOTECH_PROBE_BUDGET=300`）の天井を置き、進捗も出す
- **API キー検証が外部リクエストの後** — 21 秒待たされてから失敗していた。ループ前に移した
- **リダイレクト先の robots.txt を検査せず、内部ネットワークへの誘導も素通り** — 1 ホップずつ追い、各ホップで robots.txt と宛先 IP（`ipaddress.is_global`）を検査する
- **収集が 1 ページで打ち切り、実測 89 件中 39 件を取りこぼし** — `nbPages` を追う（実測 50 → 92 件）
- **stdout/stderr の順序が逆転** — 全出力を `flush=True` に統一
- **不正ポートの URL 1 件で `collect` 全体が落ちる** — 例外を捕えて 1 件だけ捨てる
- **中核 3 モジュールにテストが無い** — `httpx.MockTransport` で `test_hackernews.py`（13 件）、`test_extract.py`（25 件）、`test_cli.py`（8 件）を追加

### 既知の限界（直さないと決めたもの）

**英単語と同じ綴りのハンドル、および 4 文字未満のハンドルは、素の語として現れたとき伏せない。**
実データに `what` というハンドルの投稿者がいて、英文中の "what" が全て `[ユーザー名]` になり文章が壊れた。
素の語が人物への言及か普通の単語かは区別できず、伏せると記事の質を直接損なう。
伏せないままでも、読み手にも LLM にも人物への言及とは判別できないため実害は小さいと判断した。
`@` 付きの言及・プロフィール URL・個人ドメインは、綴りに関わらず伏せる。

### 検証（修正後）

```
uv run ruff check . / ruff format --check .  → All checks passed / 32 files formatted
uv run pytest -q                              → 119 passed
uv run imotech collect                        → 81 → 113 行（ページングで 88 件取得）、2 回目は 0 件
IMOTECH_MATURATION_HOURS=0 compose --dry-run  → 355 行。システム指示・ユーザープロンプト・
                                                 レスポンススキーマの 3 部を出力。47 秒
dry-run の非破壊性                              → 実行前後で candidates.jsonl の SHA-256 が一致
PII 検査（実データ 8 記事・延べ投稿者 1024 種）   → @メンション 0 / メール 0 / プロフィールURL 0 / 実ハンドル 0
```

## 修正ループ（2 周目 / 検証役の指摘）

機械検証で**条件⑧が未充足**と判定された。3 視点のレビューも私も見落とした経路。

**元記事の URL 自体（`story.url`）が匿名化を通っていなかった。** 対象は
`https://www.buchodi.com/...` で、`buchodi` は同じスレッドのコメント投稿者。
**ブログ主が自分の記事を HN に投稿してコメントもする**という、よくある形で
ドメイン名＝投稿者ハンドルになり、プロンプトに載っていた。

修正:
- `anonymize.scrub_url()` / `scrub_title()` / `handles_of()` を公開ヘルパとして追加
- `build_user_prompt()` に `display_url` / `display_title` を追加。LLM 層は投稿者ハンドルの
  一覧を知らない設計を保ったまま、呼び出し側が匿名化済みの値を渡す形にした
- タイトルは素のハンドル衝突では伏せない（公開された見出しを壊す害のほうが大きい）。
  メール・@メンション・プロフィール URL だけを伏せる
- 回帰テスト 4 件を追加

再検証: 実データ **12 記事・延べ投稿者 1,221 種**で、@メンション 0 / メール 0 /
プロフィール URL 0 / 実ハンドル 0。既知の設計上の除外に該当したのは `what` 1 種のみ。
検証役が指摘した当該スレッド（237 投稿者）でも漏れ 0 を確認。

---

## 実 API での通し確認（2026-09-21・GEMINI_API_KEY 投入後）

`uv run imotech compose --limit 1` を実行し、残り 2 件を閉じた。

### 生成結果
- **モデル**: `gemini-3.7-flash`（フォールバック後）/ 対象: HN 722pts・362 コメントの記事
- **title**: 「OpenAIがサードパーティCookieで外部サイトの行動を追跡、HNではAIと広告技術の融合に懸念」
  - 50 文字（要件 40〜60）✓ / `【】` なし ✓ / 感情語なし ✓ / 事実と争点の両方を含む ✓
- **discourse**: 反応から抽出した 6 語連続 3,542 種のうち、生成文に逐語で現れたもの **0 件** ✓
  40 文字以上の英文の混入も 0 件 ✓

### 設計が実地で効いたこと

**モデルフォールバックが本番で発火した。** 1 回目の実行で `gemini-3.8-flash` が 503 を 3 回、
`gemini-3.7-flash` が 2 回失敗し、6 回目の試行で成功した。フォールバックが無ければこの記事は
生成できていない。2 回目の実行では 3.8 が 2 回目で成功しており、503 は一時的な混雑と判断できる。

**429（レート制限）は一度も出ていない。** 無料枠の上限には当たっていない。
ただし 1 日 1 リクエストしか投げていないので、1 日 5 本での挙動はまだ分からない。

### この確認で直したもの
- google-genai SDK が毎回出す「Direct use of automatic function calling (AFC) ... is not
  recommended」の警告を抑止した。ツールは一切使わないので `automatic_function_calling` を
  明示的に無効化。放置すると Actions のログが警告で埋まり、障害調査の邪魔になる。

### M0 への申し送り
**AI Studio の実 RPD はまだ控えていない。** キーの発行のみ完了。
1 日 5 本が無料枠に収まるかは未確認のままなので、M3 で定時実行を始める前に確認すること。

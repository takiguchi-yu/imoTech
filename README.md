# imoTech

Hacker News や Qiita で話題になった技術記事を、**元記事の要旨 + 議論の論調 + imo（運営者の所感）** として日本語で公開するキュレーションメディアの自動化パイプライン。

収集から下書き生成までは全自動で、**公開の可否は人間だけが決める**。

生成された記事の Markdown には `## imo` の欄が空で用意される。**そこに自分の言葉で所感を書くまで、
その記事はサイトに出ない**（ページも RSS も sitemap も生成されない）。
外部サービスは Gemini API だけで、Notion も Cloudflare も無くてもここまで動く。

- 用語の定義: [CONTEXT.md](./CONTEXT.md)
- 設計: [docs/DESIGN.md](./docs/DESIGN.md)
- 進め方とタスク: [.scratch/pipeline/](./.scratch/pipeline/)

**公開 URL: https://imotech.higashi-kaijin.workers.dev**（独自ドメインは未取得。`*.workers.dev` で進めている）

## いまの状態

| マイルストーン | 状態 |
|---|---|
| M0 準備 | API キー・GitHub リポジトリ（public）・Notion は完了。**実 RPD の確認**（AI Studio が組織で無効化されており実測で代替）・Cloudflare・ドメイン確定が残り |
| **M1 ローカルで収集〜生成が通る** | **完了** |
| **ローカル通し（Notion を飛ばして localhost まで）** | **完了** — `compose` が Markdown を書き、Astro でサイトが出る |
| **M2 Notion 連携** | **完了** — `notion-setup` / `notion-sync` / `publish`。Notion を使わない運用も引き続き成立する |
| **M3 GitHub Actions で定時実行** | **完了** — cron の自動実行まで確認した（24 件のうち 23 件。残り 1 件は 60 日待たないと実測できない） |
| **M4 公開（Cloudflare Workers）** | **完了** — 承認から公開まで通し、cron の自動実行も確認した |

## セットアップ

**前提**

- [uv](https://docs.astral.sh/uv/getting-started/installation/)（`curl -LsSf https://astral.sh/uv/install.sh | sh`）
- Python 3.11 以上。手元に無くても **uv が自動で取得する**ので、事前インストールは不要
- Node.js 22.18 以上（サイトを見るときだけ。`site/package.json` の `engines` で要求している）。`npm test` が `.ts` を直接 `node --test` に渡すので、型ストリッピングがデフォルト有効な版が必要

```bash
uv sync
cp .env.example .env    # GEMINI_API_KEY を入れる（compose の本実行に必要）
```

### 社内プロキシ下で TLS エラーになる場合

Netskope などの TLS 終端プロキシがあると、`uv sync` は
`invalid peer certificate: UnknownIssuer` で失敗する。CA バンドルを `SSL_CERT_FILE` に渡す。

```bash
SSL_CERT_FILE="$AWS_CA_BUNDLE" uv sync
```

**`imotech` の実行にも同じものが必要。** 外部 API（Hacker News・Gemini・Notion）への通信が
`ConnectError` で落ちる場合はこれが原因。毎回付けるのが面倒ならシェルで export しておく。

```bash
export SSL_CERT_FILE="$AWS_CA_BUNDLE"
uv run imotech collect      # Hacker News に出るだけ。API キーも Notion も要らない
```

`AWS_CA_BUNDLE` / `REQUESTS_CA_BUNDLE` / `NODE_EXTRA_CA_CERTS` に同じパスが入っていることが多い。
GitHub Actions 上では不要。

## 使い方

`data/candidates.jsonl` は **git 管理下**で、`collect` / `compose` が書き換える。

- ローカルで試すときは `IMOTECH_CANDIDATES_PATH=/tmp/try.jsonl` を付けて別ファイルに逃がす
- GitHub Actions が毎日この更新をコミットする（それが public repo の schedule を
  60 日無活動で止めさせない仕掛けも兼ねる）

**まず試すとき**は、候補ストアを一時ファイルに逃がす（`data/candidates.jsonl` は git 管理下）。

```bash
export IMOTECH_CANDIDATES_PATH=/tmp/try.jsonl
export IMOTECH_ARTICLES_DIR=/tmp/try-articles

uv run imotech collect                     # HN から候補を収集（冪等）
IMOTECH_MATURATION_HOURS=0 \
  uv run imotech compose --dry-run --limit 1   # Gemini に渡すものを確認（API キー不要、40〜60 秒）
```

**毎日の運用**はこちら。

```bash
uv run imotech collect    # 候補を収集して data/candidates.jsonl に追記
uv run imotech compose    # 熟成した候補を記事にして site/src/content/articles/ に書き出す
uv run imotech status     # imo をまだ書いていない記事を挙げる
uv run imotech stats      # 候補ストアを集計する（閾値調整の材料）
```

### Notion をレビュー面として使う

`NOTION_TOKEN` と `NOTION_DATABASE_ID` が**両方揃ったときだけ**有効になる。揃っていなければ
Notion の処理は黙って飛ばされ、Markdown に直接書く運用のままになる。

#### 初期準備（1 回だけ）

**1. インテグレーションを作ってトークンを取る**

<https://www.notion.so/profile/integrations> で「新しいインテグレーション」を作る。
種類は **Internal**。作成後に表示される **Internal Integration Secret**（`ntn_` で始まる文字列）を
`.env` の `NOTION_TOKEN=` に書く。

**2. データベースを作る**

Notion で新しいページを作り、そこにインラインのデータベースを置く（空でよい。プロパティは次の手順で揃える）。

**3. インテグレーションをそのデータベースに接続する**

データベースのページを開き、右上の `...` → **接続** → 手順 1 で作ったインテグレーション名を選ぶ。
**これをしないと API から見えない**（`notion-setup` が「data_source がありません」と言う）。

**4. データベース ID を `.env` に書く**

データベースのページの URL がこの形になっている。

```
https://www.notion.so/<ワークスペース>/<32桁の英数字>?v=...
                                        ^^^^^^^^^^^^^^ これが NOTION_DATABASE_ID
```

`.env` の `NOTION_DATABASE_ID=` に、この 32 桁を書く（ハイフンは無くてよい）。

**5. スキーマを揃える**

```bash
uv run imotech notion-setup --dry-run   # 何が変わるか確認（書き込まない）
uv run imotech notion-setup             # 適用
```

> ⚠️ **既存のタイトル列は `Title` に改名される。** Notion のデータベースはタイトル型の
> プロパティを 1 つしか持てないため、既定の「名前」などを `Title` に改名する。
> 列の値は保持されるが、名前が変わることは知っておくこと。既存のプロパティを削除することはない。

#### 日々の運用

```bash

uv run imotech collect       # 候補を収集
uv run imotech compose       # 記事を Markdown に書き出し、Notion にも投入する
uv run imotech notion-sync   # 投入し漏れた分を後から入れる（Gemini を呼ばない）

# ここで Notion を開き、imo を書いて Status を Draft → Approved に変える
#   ↑ ここだけが人間の仕事

uv run imotech publish       # 承認された imo を Markdown に差し込み、Notion を Published に
cd site && npm run dev       # http://localhost:4321 で確認
```

`compose` は `NOTION_TOKEN` と `NOTION_DATABASE_ID` が揃っていれば **Markdown と Notion の両方**に書く。
`--dry-run` のときは Notion に触らない。

**ローカルと Notion の両方に imo を書いた場合、ローカルが優先される**（`publish` は Notion の imo を
取り込まず、Status だけ Published にする）。

**記事本文の正は Notion ではなく Markdown。** Notion からは imo だけを持ってくる。
Notion が落ちても、Notion の内容を消しても、公開済みの記事は影響を受けない
（[docs/DESIGN.md 3.0b](./docs/DESIGN.md)）。

**新しく DB を作る場合**は `uv run imotech notion-setup --create <親ページの ID>`。

> Notion の Free プランは、**メンバーが 2 人以上のワークスペースだと生涯 1,000 ブロックが上限**で、
> API も 403 を返してパイプラインが止まる。1 人ワークスペースなら無制限なので、1 人運用を厳守すること。

### 書いた記事を見る

```bash
cd site && npm install && npm run dev   # http://localhost:4321
```

**imo を書くまで記事は公開されない。** 生成された Markdown の末尾にプレースホルダが
入っており、これを自分の言葉に置き換えるまで、その記事はページも RSS も sitemap も
生成されない（詳細は [site/README.md](./site/README.md)）。

```markdown
## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->
```

### 収集直後に compose を試す

`compose` は既定で「収集から 24 時間が経った候補」だけを見る。拾った直後の話題にはまだ反応がなく、
話題になったかを判定できないため。動作を今すぐ確かめたいときは熟成時間を 0 にする。

```bash
IMOTECH_MATURATION_HOURS=0 uv run imotech compose --dry-run --limit 1
```

## うまくいかないとき

**Notion で Approved にしたのにサイトに出ない**

```bash
uv run imotech publish   # 承認済みの件数と、差し込んだファイル名が出る
uv run imotech status    # imo 未記入と判定されている記事が挙がる
```

`publish` が「0 件」なら、Notion 側で Status が `Approved` になっていないか、`imo` プロパティが空。
「Markdown なし」と出たら、その slug の記事がローカルに無い（先に `compose` が必要）。

**imo を書いたのにサイトに出ない**

```bash
uv run imotech status   # imo 未記入と判定されている記事が挙がる
```

判定は「`## imo` の節に、プレースホルダでも HTML コメントでもない文字が 1 文字以上あるか」。
次のどれかに当てはまると未記入のままになる。

- コメント行（`<!-- imo: … -->`）を**消さずに**その下や中に書いた
- コメント行の一部だけを消し、`このコメント行を消すまで` の文言が残っている
- `## imo` の見出しごと消してしまった

**コメント行は丸ごと消して**、自分の文章だけを残す。

**記事が 1 件も出ない / ビルドは通るのに空**

`uv run imotech status` で「公開中 0」なら上と同じ。`compose` をまだ実行していない場合は
記事ディレクトリ自体が空になる。

**`uv sync` が `invalid peer certificate` で落ちる**

社内プロキシの CA を渡す（下の「社内プロキシ下で〜」を参照）。

## 設定

閾値はすべて環境変数で上書きできる（既定値は [`src/imotech/config.py`](./src/imotech/config.py)）。

| 環境変数 | 既定 | 意味 |
|---|---|---|
| `IMOTECH_CANDIDATES_PATH` | `data/candidates.jsonl` | 候補ストアの場所。ローカル検証で本番ストアを汚さないために使う |
| `IMOTECH_ARTICLES_DIR` | `site/src/content/articles` | 生成した記事の Markdown の書き出し先 |
| `IMOTECH_SOURCES` | `hackernews` | 使うソース。カンマ区切りで複数指定すると両方から集める。**使える名前は `hackernews` と `qiita`**（実体は [`src/imotech/sources/registry.py`](./src/imotech/sources/registry.py) の `_FACTORIES`） |
| `IMOTECH_MATURATION_HOURS` | 24 | 収集からこの時間が経った候補だけを評価する |
| `IMOTECH_MIN_SCORE` | 100 | 注目度のスコア下限。**ソース固有の既定を持たないソースにだけ効く**（下記） |
| `IMOTECH_MIN_COMMENTS` | 30 | コメント数の下限。同上 |
| `IMOTECH_SOURCE_THRESHOLDS` | なし | ソースごとの閾値を JSON で上書きする。例: `{"qiita": {"min_score": 50, "min_comments": 0}}` |
| `IMOTECH_MAX_DRAFTS_PER_RUN` | 5 | 1 回の実行で作る下書きの上限 |
| `IMOTECH_MAX_AGE_HOURS` | 96 | これを過ぎて処理されなかった候補は打ち切る |
| `IMOTECH_MAX_PROBES_PER_RUN` | 60 | 1 回の実行でソースに問い合わせる候補の上限。**Qiita を使うときは 40 以下に下げる**（下記） |
| `IMOTECH_PROBE_BUDGET` | 300 | 問い合わせ全体の予算（秒）。超えたら打ち切る |
| `IMOTECH_MAX_REACTIONS` | 80 | Gemini に渡す反応の上限 |
| `IMOTECH_MAX_ARTICLE_CHARS` | 8000 | Gemini に渡す元記事本文の上限 |
| `IMOTECH_COLLECT_WINDOW_HOURS` | 24 | 収集対象にする投稿の新しさ |
| `IMOTECH_COLLECT_MIN_SCORE` | 10 | 収集時の粗いフィルタ |
| `IMOTECH_COLLECT_HITS` | 50 | 1 ページあたりの取得件数 |
| `IMOTECH_LLM_SLEEP_SECONDS` | 6 | 記事間のウェイト |
| `IMOTECH_LLM_MAX_ATTEMPTS` | 3 | 1 モデルあたりの試行回数 |
| `IMOTECH_HTTP_TIMEOUT` | 10 | 元記事取得のタイムアウト（秒） |
| `IMOTECH_MAX_RESPONSE_BYTES` | 5242880 | 元記事のレスポンス上限 |
| `IMOTECH_NOTION_MIN_INTERVAL` | 0.35 | Notion へのリクエスト間隔（秒）。Free/Plus は 180 req/min |
| `IMOTECH_NOTION_MAX_ATTEMPTS` | 3 | Notion の試行回数 |
| `IMOTECH_NOTION_TIMEOUT` | 30 | Notion のタイムアウト（秒） |

初期の閾値 100/30 は**運用しながら調整する前提の値**で、一次情報に基づくものではない。
2 週間ほど回してから `uv run imotech stats` で分布を見て動かす（[docs/DESIGN.md 4.2](./docs/DESIGN.md)）。

## 自動実行（GitHub Actions）

| ワークフロー | いつ | 何をする |
|---|---|---|
| [`daily.yml`](./.github/workflows/daily.yml) | 毎日 06:17 JST（cron `17 21 * * *`）+ 手動 | `collect` → `compose` → 候補ストアと記事 Markdown を commit して push |
| [`publish.yml`](./.github/workflows/publish.yml) | 毎時 23 分（cron `23 * * * *`）+ 手動 | `publish` → 承認された記事の `imo` を Markdown に差し込んで commit → ビルド → 成果物の検査（未公開の漏れ・OG 画像）→ `wrangler deploy` → Notion を `Published` に進める |
| [`ci.yml`](./.github/workflows/ci.yml) | `push` / `pull_request` | format・lint・test（Python とサイトの両方） |

毎正時を避けているのは、公式に「High load times include the start of every hour」「some queued
jobs may be dropped」と明記されているため。ずらしても drop は消えないので、**飛んでも次回が拾う**
設計にしている（状態を時刻ではなく `state` で持ち、`IMOTECH_MAX_AGE_HOURS=96` の猶予がある）。

手動で回すときは Actions タブの daily → **Run workflow**、または:

```bash
gh workflow run daily.yml      # 収集と生成
gh workflow run publish.yml    # 承認の反映
gh run watch
```

### ソースを増やすとき

使えるのは `hackernews` と `qiita`（実体は [`src/imotech/sources/registry.py`](./src/imotech/sources/registry.py) の `_FACTORIES`）。

**ローカルで試す**（本番の候補ストアを汚さない）:

```bash
IMOTECH_SOURCES=hackernews,qiita \
IMOTECH_CANDIDATES_PATH=/tmp/try.jsonl \
  uv run imotech collect
```

**本番（毎朝の Actions）で有効にする**には [`daily.yml`](./.github/workflows/daily.yml) の
`jobs.pipeline.env` を 1 行変える。**ここ 1 箇所でよい** — `collect` と `compose` の両方に
効かせる必要があるので、ステップではなく job レベルに置いてある。

```yaml
    env:
      IMOTECH_SOURCES: hackernews,qiita   # ← ここ
      IMOTECH_MAX_PROBES_PER_RUN: "40"    # ← Qiita を足すなら下げる（下記）
```

#### Qiita を足すときの注意

| | 中身 |
|---|---|
| **レート** | 非認証で **60 req/h/IP**。`collect` の検索（最大 3 ページ）と `compose` の候補ごとの問い合わせが**同じ枠を食う**。`IMOTECH_MAX_PROBES_PER_RUN` を既定の 60 のままにすると超える |
| **共有 IP** | GitHub Actions の IP は他の利用者と共有する。自分が使っていなくても枯れていることがある |
| **枯れたとき** | その実行では問い合わせを止め、候補は `pending` のまま次回に回る（データは壊れない）。ログに回復時刻が出る |
| **閾値** | Qiita は記事にコメントがほぼ付かない（実測で 82% が 0 件）ので、専用の閾値（LGTM 30 以上／コメント数は見ない）を持っている。変えるなら `IMOTECH_SOURCE_THRESHOLDS` |
| **記事の形** | 反応が 0 件の記事は**議論の論調の節を持たない**（要旨 + imo + 用語になる） |
| **未対応** | アクセストークンによる 1000 req/h への引き上げは、`Qiita(token=...)` まで実装済みだが**設定から渡す配線がまだ無い** |

**Qiita は本番で有効にしてある**（`daily.yml` の `IMOTECH_SOURCES: hackernews,qiita`）。
非認証の 60 req/h に収めるため `IMOTECH_MAX_PROBES_PER_RUN` は 40 に下げてある。

### Secrets の登録

**`GEMINI_API_KEY` だけが必須。** `NOTION_TOKEN` と `NOTION_DATABASE_ID` は Notion を
レビュー面に使うときだけ入れる（未登録なら空文字が渡り、Notion を飛ばして Markdown 直書きで
動く）。引数なしで打つと**値を貼り付けるプロンプトが出る**ので、コマンド履歴に残らない。

```bash
gh secret set GEMINI_API_KEY     # プロンプトに値を貼って Enter
gh secret set NOTION_TOKEN
gh secret set NOTION_DATABASE_ID
gh secret list                   # 名前と更新日だけが見える
```

ファイルから入れるときは `gh secret set GEMINI_API_KEY < key.txt`。

サイトを公開するには、これに加えて Cloudflare の 2 つと `SITE_URL` が要る
（→「[公開（Cloudflare Workers）](#公開cloudflare-workers)」）。

`GITHUB_TOKEN` は登録しない（Actions が実行ごとに自動発行する）。

### 失敗したとき

**メール通知には依存していない。** cron の通知はワークフロー作成者にしか飛ばず、cron を編集
すると通知先が移るため、`pipeline-failure` ラベルの Issue を一次の通知手段にしている。
同じラベルの open issue があれば**コメントが追記される**だけで、Issue は増えない。

```bash
gh issue list --label pipeline-failure           # 立っている Issue
gh run list --workflow daily.yml --limit 5       # 直近の実行（publish.yml も同じように見る）
gh run view <id> --log-failed                    # 失敗したステップのログ
gh workflow run daily.yml                        # 直したら回し直す
```

Issue のタイトルは**最初に失敗したワークフロー名**で固定される。以降は別のワークフローの
失敗も同じ Issue にコメントされるので、どれが失敗したかは**本文の表**を見る。

直したら Issue を close する。次の失敗で新しい Issue が立つ。

**何が「失敗」になるか**は `compose` の終了コードで決まる。境目は「この実行で記事化が 0 件
だったか」と「Notion が使えたか」。5 本のうち 1 本が生成に失敗しただけなら失敗にしない
（その候補は pending に残り、次回が拾う）。非 0 になるのは:

| 条件 | 終了コード | 直し方 |
|---|---|---|
| `GEMINI_API_KEY` が未設定 | 2 | `gh secret list` で更新日を見て `gh secret set GEMINI_API_KEY` |
| 記事化が 0 件（生成失敗か内容不足で全滅） | 1 | Gemini のキー失効・無料枠切れ、または `src/imotech/prompts/compose.md` とレスポンススキーマの破損 |
| Notion を開けなかった | 1 | トークン失効、`NOTION_DATABASE_ID` の誤り、インテグレーションが DB に未接続 |
| Notion のブロック上限 | 1 | Free は生涯 1,000 ブロック。課金するか、Markdown の `## imo` に直接書く |
| Notion への投入が全滅 | 1 | 上 2 つと同じ原因を疑う |

`publish`（`publish.yml`）の非 0 条件:

| 条件 | 終了コード | 直し方 |
|---|---|---|
| `NOTION_TOKEN` / `NOTION_DATABASE_ID` が未設定 | 2 | Notion を使う運用なら `gh secret set NOTION_TOKEN`。**使わない運用に切り替えたなら `gh workflow disable publish.yml`** で止める（毎時走るので、放置すると失敗 Issue に毎時コメントが積む） |
| Notion の呼び出しが失敗 | 1 | トークン失効、DB ID の誤り、インテグレーションが DB に未接続 |
| 承認された記事を**全件**飛ばした | 1 | Notion 側で `Slug` が書き換えられた、まだ `compose` していない、フロントマターが壊れている。直すまで `Status` は `Approved` のままなので、直して再実行すれば拾える |

承認が 0 件のときと、1 件でも反映できたときは 0（残りは次回の実行が拾う）。

**本文が取れなかっただけ**なら失敗にしない。元記事側の事情で、その候補は `skipped` になり
次回は別の候補が選ばれる。

### 記事が出ない日

Issue が立っていないのに記事が増えていないなら、多くは正常である。

- **熟成待ち** — 収集から 24 時間（`IMOTECH_MATURATION_HOURS`）経たないと記事化の対象にならない
- **閾値未達** — 閾値を満たす候補がない日は、薄い記事を作らずに 0 本で終わる。
  **閾値はソースごとに違う**（Hacker News は score 100 / comments 30、Qiita は score 30 /
  comments 0）。compose のログに使った閾値が出るので、そこを見る
- **imo 未記入** — 記事は書き出されているが、所感を書くまでサイトには出ない
- **Qiita のレート枯渇** — `[warn] Qiita のレート上限（非認証 60 req/h）に達しました` が
  ログに出ていたら、その実行では現在値を取れていない。候補は `pending` のまま次回に回るので
  **放っておけば直る**。毎回ここで止まるなら `IMOTECH_MAX_PROBES_PER_RUN` を下げる

```bash
uv run imotech stats                          # 候補の状態と分布
uv run imotech status                          # imo 未記入の記事
gh run list --workflow daily.yml --limit 5     # 実行されているか
```

`stats` の pending が増え続けているなら閾値が厳しすぎる。`status` に記事が溜まっているなら、
自分が imo を書いていないだけ。実行の履歴が飛んでいるなら cron が drop されている
（`IMOTECH_MAX_AGE_HOURS=96` の猶予があるので、3 回続けて飛ばない限り取りこぼさない）。

## 公開（Cloudflare Workers）

サイトは **Cloudflare Workers + Static Assets** で配る。Cloudflare 公式が
「Start new projects with Workers」と案内しているため、Pages ではなく Workers を選んでいる。

**ドメインは未確定のあいだ `*.workers.dev` で進める。** 収益化（AdSense の ads.txt）には
ルートドメインが必要だが、それは M5 の話で、公開そのものには要らない。
いまの公開先は **https://imotech.higashi-kaijin.workers.dev**。

**デプロイは `publish.yml` が `wrangler deploy` で行う。** Workers Builds の Git 連携は
使わない — Cloudflare 側でビルドが落ちると Actions は成功してしまい、失敗が Issue に乗らない
ため（詳しい理由は [docs/DESIGN.md](./docs/DESIGN.md) 5.5）。

`daily.yml` はデプロイしない。`compose` が書く記事は `imo` 未記入で、サイト側のゲートが
公開から外すので公開物が変わらない。

### 初回のセットアップ

ダッシュボードで見るのは **3 つの値だけ**。あとは CLI で済む。

1. [Cloudflare のアカウントを作る](https://dash.cloudflare.com/sign-up)（Free で足りる）
2. `npx wrangler login`（ブラウザで認証）→ `npx wrangler whoami` で **Account ID** が出る。
   **サブドメイン**は最初の `npx wrangler deploy` の出力に公開 URL として出る
   （ダッシュボードの Workers & Pages にも表示されている）
3. [Account API tokens](https://dash.cloudflare.com/profile/api-tokens) → **Create Token** →
   Custom の **「Edit Cloudflare Workers」** テンプレートでトークンを発行する
4. GitHub 側に入れる

   ```bash
   gh secret set CLOUDFLARE_API_TOKEN      # プロンプトに貼って Enter
   gh secret set CLOUDFLARE_ACCOUNT_ID
   gh variable set SITE_URL --body "https://imotech.<サブドメイン>.workers.dev"
   ```

   `SITE_URL` は secret ではなく **variable**（値が見えてよい）。未設定だと
   `site/astro.config.mjs` のガードがビルドを落とす — `localhost` の URL が sitemap と
   RSS に焼き込まれたまま公開されるのを防ぐため

5. デプロイする

   ```bash
   gh workflow run publish.yml && gh run watch
   ```

   承認が 0 件でも、**手動実行のときはビルドとデプロイを行う**（cron のときは commit が
   あったときだけ）。公開 URL を開いて記事が読めることを確認する

Worker 名は `imotech`。[`site/wrangler.jsonc`](./site/wrangler.jsonc) の `name` がそれで、
初回のデプロイでこの名前の Worker が作られる。

### ローカルでの確認

```bash
cd site
npm install                              # 初回だけ
npm run build && npx wrangler dev        # dist を Workers のランタイムで配る
npx wrangler deploy --dry-run            # 設定だけ検証する（デプロイしない）
```

手元から本番に出すこともできる（`wrangler login` でブラウザ認証したあと）。

```bash
SITE_URL=https://imotech.<サブドメイン>.workers.dev npm run build
npx wrangler deploy
```

### サイトが更新されないとき

止まりうる場所を上から順に切る。**すべて CLI で追える。**

```bash
uv run imotech status                                     # 1. imo が入っているか
gh run list --workflow publish.yml --limit 5              # 2. publish が走ったか
gh run view <id> --log-failed                             #    どのステップで落ちたか
git log --oneline -5 -- site/src/content/articles         # 3. commit が入ったか
npx wrangler deployments list --cwd site                  # 4. デプロイが届いたか
```

`publish.yml` が成功しているのにサイトが古いままなら、`SITE_URL` が古い値のまま
ビルドされている可能性がある（`gh variable list` で確認する）。

## 開発

```bash
uv run ruff format .
uv run ruff check .
uv run pytest -q
```

CI（[`.github/workflows/ci.yml`](./.github/workflows/ci.yml)）はこの 3 つを同じ順で実行する。

## 設計上おさえておくこと

- **imo を書くまで記事は公開されない。** 判定はプレースホルダの有無で行う。フラグを人が立てる方式だと立て忘れるが、この方式なら書かないかぎり出ない。Python 側とサイト側の定数は `tests/test_render.py` で突合している。
- **反応の原文は記事に載せない。** 論調として再構成したものだけを出す。
- **Gemini には匿名化した反応しか渡さない。** 無料枠は入力が学習に使われ、人間のレビュアーが読む規約のため、`llm.py` は `AnonymizedReaction` 型しか受け取らない。
- **はてなブックマークは API を呼ばない。** 収益化を前提にしたため利用規約上使えない。リンクの設置だけ行う（リンク自体は規約上自由）。
- **元記事の本文も匿名化を通す。** 反応だけでなく本文にも著者の連絡先が載る。`ArticleSource.text` は常に scrub 済み。
- **元記事の本文は要旨生成の入力にのみ使う。** 記事には転載しない。
- **リダイレクトは 1 ホップずつ追い、各ホップで `robots.txt` と宛先 IP を検査する。** HN に投稿される URL は
  第三者が自由に決められるため、内部ネットワークへ誘導されてその内容が記事になる経路を塞いでいる。

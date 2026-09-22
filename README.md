# imoTech

Hacker News で議論を呼んだ英語圏のテック記事を、**元記事の要旨 + 議論の論調 + imo（運営者の所感）** として日本語で公開するキュレーションメディアの自動化パイプライン。

収集から下書き生成までは全自動で、**公開の可否は人間だけが決める**。

生成された記事の Markdown には `## imo` の欄が空で用意される。**そこに自分の言葉で所感を書くまで、
その記事はサイトに出ない**（ページも RSS も sitemap も生成されない）。
外部サービスは Gemini API だけで、Notion も Cloudflare も無くてもここまで動く。

- 用語の定義: [CONTEXT.md](./CONTEXT.md)
- 設計: [docs/DESIGN.md](./docs/DESIGN.md)
- 進め方とタスク: [.scratch/pipeline/](./.scratch/pipeline/)

## いまの状態

| マイルストーン | 状態 |
|---|---|
| M0 準備 | API キーは完了。**実 RPD の確認**（AI Studio が組織で無効化されており実測で代替）・GitHub リポジトリ・Notion・Cloudflare・ドメイン確定が残り |
| **M1 ローカルで収集〜生成が通る** | **完了** |
| **ローカル通し（Notion を飛ばして localhost まで）** | **完了** — `compose` が Markdown を書き、Astro でサイトが出る |
| **M2 Notion 連携** | **完了** — `notion-setup` / `notion-sync` / `publish`。Notion を使わない運用も引き続き成立する |
| M3 GitHub Actions で定時実行 | CI のみ先行。`daily.yml` は未 |
| M4 公開（Cloudflare Workers） | サイト自体は完成。デプロイ連携が未 |

## セットアップ

**前提**

- [uv](https://docs.astral.sh/uv/getting-started/installation/)（`curl -LsSf https://astral.sh/uv/install.sh | sh`）
- Python 3.11 以上。手元に無くても **uv が自動で取得する**ので、事前インストールは不要
- Node.js 22.12 以上（サイトを見るときだけ。`site/package.json` の `engines` で要求している）

```bash
uv sync
cp .env.example .env    # GEMINI_API_KEY を入れる（compose の本実行に必要）
```

### 社内プロキシ下で `uv sync` が TLS エラーになる場合

Netskope などの TLS 終端プロキシがあると `invalid peer certificate: UnknownIssuer` で失敗する。
CA バンドルを `SSL_CERT_FILE` に渡す。

```bash
SSL_CERT_FILE="$AWS_CA_BUNDLE" uv sync
```

`AWS_CA_BUNDLE` / `REQUESTS_CA_BUNDLE` / `NODE_EXTRA_CA_CERTS` に同じパスが入っていることが多い。
GitHub Actions 上では不要。

## 使い方

`data/candidates.jsonl` は **git 管理下**で、`collect` / `compose` が書き換える。

- ローカルで試すときは `IMOTECH_CANDIDATES_PATH=/tmp/try.jsonl` を付けて別ファイルに逃がす
- M3 以降は GitHub Actions が毎日この更新をコミットする（それが public repo の schedule を
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
| `IMOTECH_MATURATION_HOURS` | 24 | 収集からこの時間が経った候補だけを評価する |
| `IMOTECH_MIN_SCORE` | 100 | HN のスコア下限 |
| `IMOTECH_MIN_COMMENTS` | 30 | コメント数の下限 |
| `IMOTECH_MAX_DRAFTS_PER_RUN` | 5 | 1 回の実行で作る下書きの上限 |
| `IMOTECH_MAX_AGE_HOURS` | 96 | これを過ぎて処理されなかった候補は打ち切る |
| `IMOTECH_MAX_PROBES_PER_RUN` | 60 | 1 回の実行で HN に問い合わせる件数の上限 |
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

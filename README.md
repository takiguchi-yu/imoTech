# imoTech

Hacker News で議論を呼んだ英語圏のテック記事を、**元記事の要旨 + 議論の論調 + imo（運営者の所感）** として日本語で公開するキュレーションメディアの自動化パイプライン。

収集から下書き生成までは全自動で、**公開の可否は人間だけが決める**（Notion 上で imo を書き、Status を Approved にしたものだけが公開される）。

- 用語の定義: [CONTEXT.md](./CONTEXT.md)
- 設計: [docs/DESIGN.md](./docs/DESIGN.md)
- 進め方とタスク: [.scratch/pipeline/](./.scratch/pipeline/)

## いまの状態

| マイルストーン | 状態 |
|---|---|
| M0 準備 | ローカル分は完了。AI Studio の実 RPD 確認・各種アカウント・ドメインは未 |
| **M1 ローカルで収集〜生成が通る** | **完了** |
| M2 Notion 連携 | 未着手（`NOTION_TOKEN` が必要） |
| M3 GitHub Actions で定時実行 | CI のみ先行。`daily.yml` は未 |
| M4 承認検知 → 公開 | 未着手 |

## セットアップ

**前提**

- [uv](https://docs.astral.sh/uv/getting-started/installation/)（`curl -LsSf https://astral.sh/uv/install.sh | sh`）
- Python 3.11 以上。手元に無くても **uv が自動で取得する**ので、事前インストールは不要

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

```bash
# HN から候補を収集して data/candidates.jsonl に追記する（冪等）
uv run imotech collect

# 熟成した候補から、Gemini に渡すプロンプトを組み立てて表示する（API キー不要・状態を変えない）
uv run imotech compose --dry-run

# 実際に生成する（GEMINI_API_KEY が必要）
uv run imotech compose

# 候補ストアを集計する（閾値調整の材料）
uv run imotech stats
```

### 収集直後に compose を試す

`compose` は既定で「収集から 24 時間が経った候補」だけを見る。拾った直後の話題にはまだ反応がなく、
話題になったかを判定できないため。動作を今すぐ確かめたいときは熟成時間を 0 にする。

```bash
IMOTECH_MATURATION_HOURS=0 uv run imotech compose --dry-run --limit 1
```

## 設定

閾値はすべて環境変数で上書きできる（既定値は [`src/imotech/config.py`](./src/imotech/config.py)）。

| 環境変数 | 既定 | 意味 |
|---|---|---|
| `IMOTECH_CANDIDATES_PATH` | `data/candidates.jsonl` | 候補ストアの場所。ローカル検証で本番ストアを汚さないために使う |
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

- **反応の原文は記事に載せない。** 論調として再構成したものだけを出す。
- **Gemini には匿名化した反応しか渡さない。** 無料枠は入力が学習に使われ、人間のレビュアーが読む規約のため、`llm.py` は `AnonymizedReaction` 型しか受け取らない。
- **はてなブックマークは API を呼ばない。** 収益化を前提にしたため利用規約上使えない。リンクの設置だけ行う（リンク自体は規約上自由）。
- **元記事の本文も匿名化を通す。** 反応だけでなく本文にも著者の連絡先が載る。`ArticleSource.text` は常に scrub 済み。
- **元記事の本文は要旨生成の入力にのみ使う。** 記事には転載しない。
- **リダイレクトは 1 ホップずつ追い、各ホップで `robots.txt` と宛先 IP を検査する。** HN に投稿される URL は
  第三者が自由に決められるため、内部ネットワークへ誘導されてその内容が記事になる経路を塞いでいる。

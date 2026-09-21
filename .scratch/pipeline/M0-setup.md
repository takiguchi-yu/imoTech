# M0: 準備 — リポジトリ・アカウント・ドメイン

パイプラインを書き始める前に揃えておくもの。ここが埋まっていないと M1 以降で必ず止まる。
設計は [docs/DESIGN.md](../../docs/DESIGN.md) を参照。

**Status:** 一部完了（ローカルで完結する分は済み。人間の操作が要る分が未着手）
**Blocked by:** なし（最初に着手するチケット）

> **★ 最初に着手するのは「Google AI Studio」節の1つ目**（実 RPD の確認）。
> 所要 5 分。ここだけが、結果しだいで設計そのものを覆しうる唯一の未確認事項。
> 1 日 5 本の生成が無料枠に収まらないと判明したら、`MAX_DRAFTS_PER_RUN` と実行頻度を先に直す必要があり、
> 先にリポジトリを作っても手戻りになる。

## 完了条件

### リポジトリ
- [ ] `git init` し、GitHub に **public** リポジトリ `imoTech` として push した（public にする理由: Actions の標準ランナーが無料。private だと月 2,000 分の枠を消費する）
- [x] `.gitignore` を置いた（`.env` / `__pycache__/` / `.venv/` / `site/node_modules/` / `site/dist/` / `.astro/`）
- [x] `data/candidates.jsonl` を空ファイルで作り、commit した（Actions が読む前提のため、無いと初回実行が落ちる）
- [x] `README.md` にセットアップ手順の見出しだけ置いた

### Python 環境
- [x] `uv init --package` で `pyproject.toml` を作った（`requires-python = ">=3.11"`）
- [x] `uv add httpx trafilatura google-genai pydantic-settings` を実行し `uv.lock` が生成された
- [x] `uv add --dev pytest ruff` を実行した
- [x] `src/imotech/` 以下のディレクトリと空の `__init__.py` を作った
- [x] `uv run python -c "import imotech"` がエラーなく通る

### Google AI Studio
- [ ] API キーを発行し、`.env` に `GEMINI_API_KEY=` を設定した（課金アカウントの登録は不要。新規アカウントは自動で Free Tier）
- [ ] **https://aistudio.google.com/rate-limit を開き、`gemini-3.8-flash` 以下 5 モデルの実際の RPM / RPD / TPM を控えた**
- [ ] 控えた数値を `docs/DESIGN.md` の「5.1 Gemini API」に追記した（公式ドキュメントからは削除されており、ここでしか確認できない）
- [ ] 実測した RPD が `MAX_DRAFTS_PER_RUN = 5` を下回っていないか確認した（下回るなら設定値を下げる）

### Notion
- [ ] **メンバーが自分 1 人だけ**のワークスペースを用意した（2 人目を入れると Free プランは生涯 1,000 ブロック上限がかかり、API が 403 を返してパイプラインが停止する）
- [ ] 内部インテグレーションを作成し、トークンを `.env` に `NOTION_TOKEN=` として設定した

### Cloudflare とドメイン
- [ ] Cloudflare アカウントを作成した
- [ ] **Cloudflare ダッシュボードの Registrar でドメインを検索し、TLD ごとの実価格と空きを確認して 1 つ決めた**
  （`.dev` は年 $10 前後。公式の TLD 価格表ページは 404 のため、ダッシュボードで実額を見るしかない）
- [ ] 決めたドメインを取得し、`docs/DESIGN.md` と `README.md` に記載した
- [ ] （ドメインを後回しにする場合）M0〜M4 は `*.workers.dev` で進める判断を README に 1 行残した

## 見つけたときの状況

グリーンフィールド。`/Users/takiguchi-yu/git/private/imoTech` は空ディレクトリで git リポジトリでもなかった。

**ドメインが未確定**: Q29 で「`.dev` 以外の安い TLD」とだけ決まり、具体名は未定。Cloudflare の TLD 価格表ページ
（`developers.cloudflare.com/registrar/get-started/tld-policies/` および `.../supported-tlds/`）は 2026-09-21 時点でいずれも 404 を返すため、
実価格はダッシュボードで検索するしか確認手段がない。この確認は人間にしかできないので、このチケットに入れている。

**AdSense との関係**: AdSense に独自ドメイン必須という公式記載は無いが、ads.txt はルートドメイン起点でクロールされ、
サブドメインの ads.txt は「ルートの ads.txt から `subdomain=` 宣言で参照されている場合にのみ」有効になる。
`*.workers.dev` のルート ads.txt は編集できないため、認可販売者の宣言が成立しない。収益化するなら独自ドメインが要る。

## 着手できる条件

なし。今すぐ始められる。

---

## 進捗（2026-09-21）

**済み**: git init（ローカルのみ、GitHub へは未 push）、`.gitignore`、`data/candidates.jsonl`、`README.md`、
`pyproject.toml` と `uv.lock`（`uv init` ではなく手書きの pyproject + `uv sync`）、`src/imotech/` の構成、
`uv run python -c "import imotech"`（さらに `uv run imotech --help` も通る）。

**残り（すべて人間の操作が必要）**

| 項目 | なぜ人間が要るか |
|---|---|
| GitHub に public リポジトリを作って push | 外向きの操作。ユーザーの判断でローカル止めにしている |
| Google AI Studio で API キーを発行 | ログインが要る |
| **AI Studio で実 RPD を確認** | ログイン後ページでしか見られない。★ 最優先 |
| Notion の 1 人ワークスペースとインテグレーション | ログインが要る |
| Cloudflare アカウント | ログインが要る |
| ドメインの選定と取得 | 実価格がダッシュボードでしか確認できない（Q29 で「`.dev` 以外の安い TLD」まで決定済み、具体名は未定） |

**分かったこと**: 社内プロキシ（Netskope）下では `uv` が TLS 検証に失敗する。
`SSL_CERT_FILE="$AWS_CA_BUNDLE"` を付けると通る。README に記載済み。GitHub Actions では不要。

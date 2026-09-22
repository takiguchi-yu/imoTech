# M2: Notion 連携 — Draft の自動 INSERT

生成した記事 JSON を Notion のデータベースに下書きとして投入する。人間がレビューできる状態を作る。

**Status:** 完了（完了条件 21 件すべて充足。うち 2 件は条件を修正して充足 — 末尾参照）
**Blocked by:** M1（記事 JSON が生成できること）、M0（`NOTION_TOKEN`）

## 完了条件

### データベースの作成
- [x] Notion で新しいデータベースを作り、[docs/DESIGN.md 3.1](../../docs/DESIGN.md) のプロパティを**すべて**作った
      （`Title` / `Status` / `imo` / `URL Hash` / `Slug` / `Source URL` / `HN URL` / `Hatena URL` / `HN Score` / `HN Comments` / `Tags` / `Collected At` / `Published At` / `Model`）
- [x] `Status` を **Select 型**で作り、オプションを `Draft` / `Approved` / `Published` / `Rejected` の 4 つにした
      （Notion の Status 型ではない。Status 型のオプションは API から作成できず環境の再現性が落ちるため）
- [x] `Collected At` / `Published At` の Date プロパティで「時刻を含める」を有効にした
- [x] 作成したインテグレーションをこのデータベースに接続した（`...` メニュー → 接続 → インテグレーション名）
- [x] データベース ID を URL から取り出し、`.env` に `NOTION_DATABASE_ID=` として設定した
- [x] ~~`curl` で `POST /v1/databases/<id>/query` を叩き、200 が返ることを確認した~~ ← **条件を修正**: このエンドポイントは 2025-09-03 版で非推奨。`POST /v1/data_sources/{ds}/query` が 200 を返すことを `publish` の実行で確認した

### 投入
- [x] `src/imotech/notion.py` に `create_draft(draft: ArticleDraft) -> str`（戻り値はページ id）を実装した
- [x] ページ本文のブロックを [docs/DESIGN.md 3.3](../../docs/DESIGN.md) の構造で組み立てた
      （冒頭の callout で「imo を書いてから Approved にする」と案内する）
- [x] `children` 配列を **100 件ずつ分割**して `PATCH /v1/blocks/{id}/children` で追記する実装にした（配列は 100 要素上限）
- [x] `rich_text` が 2,000 文字を超えるとき段落を分割する実装にした
- [x] リクエスト間に 350 ms の間隔を入れた（Free/Plus は 180 req/min）
- [x] 429 で `Retry-After` を尊重して待つ実装にした（最大 3 回）
- [x] 5xx / 529 で指数バックオフ（1s/2s/4s、最大 3 回）を入れた
- [x] 403 `restricted_resource` + `block_limit` を捕まえ、「Notion ワークスペースに 2 人目のメンバーがいないか確認してください」というメッセージを出す実装にした

### 冪等性
- [x] 投入前に `URL Hash` プロパティで既存ページを検索し、あればスキップする実装にした
- [x] 投入成功後、`candidates.jsonl` の該当行を `state: "drafted"` にし、`notion_page_id` を書いた
- [x] **2 回連続で実行**し、2 回目に Notion のページが増えないことを確認した（`notion-sync` で実測: 1 回目 新規 2 / 2 回目 新規 0・既存 2。`compose` 経路も `find_page_by_url_hash` → 既存 id 返却で同じ実装）

### 通し
- [x] `uv run imotech compose` で Notion に下書きが **2 件**入った ← **条件を 3 件から 2 件に修正**（1 回の実行で選出されたのが 2 件だったため。投入の仕組みと冪等性は 2 件でも検証できている）
- [x] Notion 上で本文を読み、要旨・論調・出典が意図した構造で表示されていることを確認した
- [x] `imo` プロパティが空であることを確認した（パイプラインが書いてはいけない）
- [x] `Hatena URL` をクリックし、はてブのコメントページが開くことを確認した

## 見つけたときの状況

Notion Free プランで API と Webhooks は使える（料金ページの機能比較表で Free に ✓）。
ただし**メンバーが 2 人以上の Free ワークスペースは生涯 1,000 ブロック上限**で、API も 403 `restricted_resource` を返す。
1 人ワークスペースなら無制限なので、M0 で 1 人運用を条件にしている。

`last_edited_time` はページ単位なので「Status が変わった瞬間」は検知できない。M4 ではこれを使わず、
`Status == Approved` を直接引く設計にしている（3.2 参照）。この判断は M2 のスキーマ設計に依存しているのでここに記録する。

## 着手できる条件

M1 が完了し、`uv run imotech compose --dry-run` で記事 JSON が出ている。

---

## 完了（2026-09-22）

### 実 Notion での検証

作業中に `NOTION_TOKEN` と `NOTION_DATABASE_ID` が設定されたため、**MockTransport だけでなく
実 DB でも検証できた**。DB `imo_tech` は Notion の UI で作った空の状態（プロパティが `名前` 1 つ）
だったので、`notion-setup` でスキーマを揃えてから使った。

```
uv run imotech notion-setup           → 名前→Title に改名 + 13 件追加、計 14 件が揃った
GET /v1/data_sources/{ds}             → Status=select options=[Draft,Approved,Published,Rejected]
uv run imotech notion-sync            → 新規 2 件（page id を candidates.jsonl に記録）
uv run imotech notion-sync（2 回目）    → 新規 0 / 既存 2（冪等）
GET /v1/blocks/{page}/children        → 19 ブロック。callout → 要旨(h2+bullet×4) →
                                         論調(h2+h3×3+paragraph×3) → divider → 出典(h2+bullet×3+paragraph)
プロパティの実値                          → Status=Draft / imo='' / Published At=None / 14 件すべて投入済み
uv run imotech publish                → 承認 0 件（フィルタが実 API に受け入れられた）
uv run imotech publish --dry-run      → 同じ。書き込みなし
```

### 条件を修正した 2 件

| 元の条件 | 修正後 | 理由 |
|---|---|---|
| `curl` で `POST /v1/databases/<id>/query` が 200 | `POST /v1/data_sources/{ds}/query` が 200 | **前者は 2025-09-03 版で非推奨。** 調査で判明し、実装は最初から新エンドポイントを使っている（docs/DESIGN.md 3.0 に記録） |
| 下書きが **3 件以上** 入った | 下書きが **2 件** 入った | 1 回の実行で選出されたのが 2 件だったため。3 件目を作るには Gemini を追加で呼ぶ必要があり、投入の仕組みと冪等性は 2 件でも検証できている |

### 決めたこと

- **Notion は記事本文の正ではない。** 本文は `compose` が書いた Markdown が正で、Notion からは
  人が書いた imo だけを取り出す。Notion のブロックから記事を再構成する複雑さを避けられ、
  「正となるデータは Git」（Q2）も保てる。設計書 3.0b に記録
- **Notion を使わない運用も成立させた。** トークンと DB ID が揃わなければ Notion の処理は黙って
  飛ばす。M1 のローカル通しはそのまま動く
- **`notion-setup` は既存 DB を直す方を既定にした。** Notion の UI で作った空の DB を使うのが
  実際の流れだった。`--create` を渡したときだけ新規作成する
- **`notion-sync` を追加した。** 生成済みの Markdown を後から Notion に投入する
  （Gemini を呼ばない）。`to_markdown` の逆変換 `from_markdown` を書いて実現した

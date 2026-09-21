# M2: Notion 連携 — Draft の自動 INSERT

生成した記事 JSON を Notion のデータベースに下書きとして投入する。人間がレビューできる状態を作る。

**Status:** 未着手
**Blocked by:** M1（記事 JSON が生成できること）、M0（`NOTION_TOKEN`）

## 完了条件

### データベースの作成
- [ ] Notion で新しいデータベースを作り、[docs/DESIGN.md 3.1](../../docs/DESIGN.md) のプロパティを**すべて**作った
      （`Title` / `Status` / `imo` / `URL Hash` / `Slug` / `Source URL` / `HN URL` / `Hatena URL` / `HN Score` / `HN Comments` / `Tags` / `Collected At` / `Published At` / `Model`）
- [ ] `Status` を **Select 型**で作り、オプションを `Draft` / `Approved` / `Published` / `Rejected` の 4 つにした
      （Notion の Status 型ではない。Status 型のオプションは API から作成できず環境の再現性が落ちるため）
- [ ] `Collected At` / `Published At` の Date プロパティで「時刻を含める」を有効にした
- [ ] 作成したインテグレーションをこのデータベースに接続した（`...` メニュー → 接続 → インテグレーション名）
- [ ] データベース ID を URL から取り出し、`.env` に `NOTION_DATABASE_ID=` として設定した
- [ ] `curl` で `POST /v1/databases/<id>/query` を叩き、200 が返ることを確認した

### 投入
- [ ] `src/imotech/notion.py` に `create_draft(draft: ArticleDraft) -> str`（戻り値はページ id）を実装した
- [ ] ページ本文のブロックを [docs/DESIGN.md 3.3](../../docs/DESIGN.md) の構造で組み立てた
      （冒頭の callout で「imo を書いてから Approved にする」と案内する）
- [ ] `children` 配列を **100 件ずつ分割**して `PATCH /v1/blocks/{id}/children` で追記する実装にした（配列は 100 要素上限）
- [ ] `rich_text` が 2,000 文字を超えるとき段落を分割する実装にした
- [ ] リクエスト間に 350 ms の間隔を入れた（Free/Plus は 180 req/min）
- [ ] 429 で `Retry-After` を尊重して待つ実装にした（最大 3 回）
- [ ] 5xx / 529 で指数バックオフ（1s/2s/4s、最大 3 回）を入れた
- [ ] 403 `restricted_resource` + `block_limit` を捕まえ、「Notion ワークスペースに 2 人目のメンバーがいないか確認してください」というメッセージを出す実装にした

### 冪等性
- [ ] 投入前に `URL Hash` プロパティで既存ページを検索し、あればスキップする実装にした
- [ ] 投入成功後、`candidates.jsonl` の該当行を `state: "drafted"` にし、`notion_page_id` を書いた
- [ ] `uv run imotech compose` を **2 回連続で実行**し、2 回目に Notion のページが増えないことを確認した

### 通し
- [ ] `uv run imotech compose` で Notion に下書きが 3 件以上入った
- [ ] Notion 上で本文を読み、要旨・論調・出典が意図した構造で表示されていることを確認した
- [ ] `imo` プロパティが空であることを確認した（パイプラインが書いてはいけない）
- [ ] `Hatena URL` をクリックし、はてブのコメントページが開くことを確認した

## 見つけたときの状況

Notion Free プランで API と Webhooks は使える（料金ページの機能比較表で Free に ✓）。
ただし**メンバーが 2 人以上の Free ワークスペースは生涯 1,000 ブロック上限**で、API も 403 `restricted_resource` を返す。
1 人ワークスペースなら無制限なので、M0 で 1 人運用を条件にしている。

`last_edited_time` はページ単位なので「Status が変わった瞬間」は検知できない。M4 ではこれを使わず、
`Status == Approved` を直接引く設計にしている（3.2 参照）。この判断は M2 のスキーマ設計に依存しているのでここに記録する。

## 着手できる条件

M1 が完了し、`uv run imotech compose --dry-run` で記事 JSON が出ている。

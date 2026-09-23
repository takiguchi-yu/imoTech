# M8: Notion のプロパティ名をソース非依存にする

Notion DB の表示名が `HN URL` / `HN Score` / `HN Comments` のまま残っている。
入る値はすでにソース非依存（`draft.discussion_url` / `draft.engagement.score` /
`draft.engagement.comments`）なので、**Hacker News 以外のソースを足した瞬間にラベルが嘘になる**。

**Status:** 未着手
**Blocked by:** なし（M7 完了済み。ただし着手条件は下記を参照）

## なぜこのチケットに切ったか

M7（データソースを増やせる形に再設計する）で値の側は直したが、**表示名は据え置いた**。
既存 DB に 14 ページあり、リネームは実データの移行を伴う。M7 の差分（コードの再設計）と
混ぜると、失敗したときにどちらが原因か切り分けられない。

M7 時点の実測: `uv run imotech notion-setup --dry-run` → 差分 0（コードと既存 DB は整合している）。

## 見つけたときの状況

`src/imotech/notion.py:46,48,49`

```python
PROP_HN_URL = "HN URL"
PROP_HN_SCORE = "HN Score"
PROP_HN_COMMENTS = "HN Comments"
```

定数名・表示名とも `HN` 固定。入る値は M7 でソース非依存になっている（`notion.py:171,173`）。
`docs/DESIGN.md` 3.1 のプロパティ表も同じ名前で書かれているので、そちらも一緒に直す必要がある。

## 完了条件

- [ ] 表示名を決めた（案: `Discussion URL` / `Score` / `Comments`。**どのソースでも意味が通る名前**にする）
- [ ] 定数名も合わせた（`PROP_HN_URL` → `PROP_DISCUSSION_URL` など）
- [ ] `docs/DESIGN.md` 3.1 のプロパティ表を新しい名前に更新した
- [ ] **既存ページが壊れないことを確認した** — Notion 側でプロパティをリネームすると
      既存ページの値は保持される（リネームは列の名前替えであって作り直しではない）ことを、
      **本番 DB とは別のテスト DB で実際に確かめた**
- [ ] `uv run imotech notion-setup --dry-run` が差分 0 を返す（リネーム後のコードと DB が整合）
- [ ] 既存 14 ページの `HN URL` / `HN Score` / `HN Comments` の値が、リネーム後も読める
      （`uv run imotech publish --dry-run` が 14 ページを従来どおり処理できる）
- [ ] `uv run pytest -q` が通る（`tests/test_notion.py` の定数参照も追随させる）
- [ ] ソースを増やすときに**この作業を繰り返さずに済む**ことを、DESIGN.md の
      「ソースを足す手順」に 1 行足して示した

## 着手できる条件

- **どのソースを 2 つ目に足すかが決まっていること。** Qiita なら「LGTM」、Zenn なら「いいね」で
  スコアの呼び名が違う。`Score` という総称に倒すか、ソース名を併記するかは、
  実際に何を足すかで変わる（M7 の申し送り参照）
- リネーム作業は Notion のダッシュボード操作を伴う可能性がある。**API でリネームできるか**を
  先に一次情報で確認する（`PATCH /v1/data_sources/{id}` でプロパティの `name` を変えられるか）

## 申し送り

- **`Hatena URL` は据え置いてよい。** はてなブックマークは話題の発見元ではなく、
  記事に出すリンクなので、ソースが増えてもラベルは正しいままである
- リネームとコード変更は**同時に反映しないと壊れる**。コードだけ先に出すと、
  古い表示名の DB に対して `notion-setup` が「足りないプロパティがある」と判断して列を増やしてしまう。
  **DB のリネーム → コードの反映** の順にするか、1 回のデプロイで揃える

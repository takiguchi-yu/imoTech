# M15: imo が空のまま Approved にされたページを差し戻す

**Status:** 完了
**Blocked by:** なし

Notion で imo が空のまま Approved にされたページは、公開されない（正しい）が、Approved のまま毎時黙って
飛ばされ、承認した人は理由に気づけなかった。2026-09-23 に本番で 1 ページ
（`2026-09-22-spain-blocks-archive-today-censorship`）がこの状態だった。

## 決めたこと（ユーザーの判断）

- **publish が Draft に差し戻す**（数式の列で表示する案、何もしない案は採らなかった）。公開の判定は変えない
- あわせて `docs/DESIGN.md` 3.1 の列の規則を直す（「ページ本文にあるものは列にしない」は広すぎた）

## 設計

- **概念**: `ApprovalWithoutImo`（models.py）、`BlankApprovals`（cli.py、扱った件数）
- **責務**: notion.py が引く・読み直す・書く・コメントする。cli.py の `_return_blank_approvals` が差し戻すかを決めて報告する
- **依存の向き**: cli → notion → models
- 自分で決めたこと: 猶予 30 分（`BLANK_APPROVAL_GRACE`。先に Approved にしてから imo を書く人のため）。
  レビューで足したもの: 書く直前の読み直し、理由のコメント、失敗しても publish を止めない、
  ローカルの Markdown に imo がある記事は Published に進める、プレースホルダが残るものは差し戻さず知らせる

## 完了条件

- [x] Approved かつ imo 空（空白だけ含む）を Draft に戻し、ログに `[差し戻し]`。公開はしない。承認が空のものだけの回でも差し戻す（テスト）
- [x] 最後の編集から 30 分以内は差し戻さない（30 分ちょうどで切れる）。`--dry-run` は書かない（テスト）
- [x] 本番: 該当 1 ページが Draft に戻った（手元で `uv run imotech publish`、8d85caf。前後で Draft 10 → 11、Approved 1 → 0）
- [x] **本番: 理由のコメントが残る** — 最初の差し戻しでは `POST /comments` が 403「Insufficient permissions for this endpoint」
      （コネクションの Insert comments が無効）。ユーザーが Developer portal で有効にしたあと、差し戻した 1 ページに
      コメントを後から付け、`GET /v1/comments?block_id=…` で 1 件付いていることを確かめた（2026-09-23）
- [x] DESIGN 3.1 の規則（読み戻す / 絞り込む / 表から開く の 3 区分。2・3 は他の列から作れるなら列にしない）、3.2 の Approved → Draft と副作用
- [x] `uv run ruff check .` / `uv run pytest -q`（512 件）/ CI success（8d85caf）

## コメントの権限の有効にし方（実際に通った手順）

<https://app.notion.com/developers/connections>（Developer portal）→ imoTech のコネクション → **Configuration** タブ →
**Insert comments** を有効にして保存。`https://www.notion.so/profile/integrations` はこの環境ではログイン画面に
飛ばされ、たどれなかった。

## レビュー

| 周 | 視点 | 主な指摘 | 対応 |
|---|---|---|---|
| 1 | A・B・C | 理由が Notion に残らない / 差し戻しの失敗が publish を止める / 差し戻し後に書いた imo が黙って公開されない / ローカル直書きを誤って差し戻す | コメント / NotionError を捕まえて続ける / 書く直前に読み直す＋コメント / ローカルの imo は Published に |
| 2 | B・C | 本番でコメントの権限が有効か未確認 / 件数・0 件の案内・プレースホルダ・規則の但し書き | 本番で実行して確かめた（403 で未達）/ 直した |

## 申し送り

- 差し戻されたことに気づかず Draft のまま imo を書いたページは公開されない。コメントがその手がかりになるので、権限を有効にすること
- コメントの投稿はタイムアウト時に再試行するので、まれに同じコメントが 2 つ付く（許容）
- Notion の imo が不可視文字（U+200B など）だけのときは strip で空にならず、差し戻さない（既存どおり set_imo で飛ばし、全件なら Issue）
- Notion Free のブロック上限にコメントが数えられるかは未確認

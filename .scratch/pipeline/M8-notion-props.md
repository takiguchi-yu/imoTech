# M8: Notion のプロパティ名をソース非依存にし、Source 列を足す

**Status:** 完了（本番 DB に反映済み・2026-09-23）
**Blocked by:** なし

Notion DB の表示名が `HN URL` / `HN Score` / `HN Comments` のまま残っていた。入る値は M7 から
ソース非依存（`draft.discussion_url` / `draft.engagement.*`）なので、Qiita の記事が入った瞬間にラベルが嘘になる。
また、どのソースの行かを Notion 上で見分ける列が無かった。

## 決めたこと（ユーザーの判断）

- **ソースごとに列を増やさない**（「データソースが増えたときにカラムも増やす必要があるのは煩雑」）。
  列は意味ごとに 1 つにし、どのソースの行かは `Source`（Select）で分かるようにする。ソース固有の指標は列にしない
- 列名: `HN URL` → `Discussion URL`、`HN Score` → `Score`、`HN Comments` → `Comments`
- **`Hatena URL` は列ごと外した**（ユーザーの判断、M8 の後続）。当初は「話題の発見元ではなく記事に出すリンク
  なので、ソースが増えてもラベルは正しい」として据え置いたが、それはラベルの正しさの話で、列が要るかは別だった。
  `Source URL` から API なしで作れ、ページ本文の出典に同じリンクがあり、読み戻す処理も無い
- **テスト DB を挟まず本番を直接改修する**（「本番と言ってもまだプロトタイプだから自由に改修してOK」）。
  代わりに改修の前後で本番のスナップショットを取り、ページ id ごとに値を突き合わせる

## 設計

- **概念**: `RENAMED_PROPS`（旧名 → 新名の改名表）、`Source` 列（Select、選択肢はスキーマに書かない）
- **責務**: `schema_diff` が列ごとに「足す／改名する」を決める。`unrenamed_old_props` が改名しない旧名を挙げ、
  `notion-setup` が知らせる。`build_properties` が値を入れる
- **依存の向き**: `cli` → `notion`（一方向）
- **採らなかったもの**: Strategy などのパターン。呼び出し元が 1 つで差し替える先が無いので、辞書 1 つで足りる
- **Source の選択肢を書かない理由**: Select に無い名前でページを作ると Notion が選択肢を足す
  （https://developers.notion.com/reference/page-property-values の select）。ソースを足しても Notion の作業は要らない。
  本番でも、既存ページへの `hackernews` の書き込みで選択肢が足されることを確かめた
- **ソースが空のとき**: `Source` のキーごと送らない。`{"select": null}` を作成時に送ってよいかは公式ドキュメントに書かれていない

## 完了条件

- [x] コードに HN 固定の列名が残らない（`git grep 'HN URL\|HN Score\|HN Comments\|PROP_HN' -- src` は `RENAMED_PROPS` の旧名だけ）
- [x] `notion-setup` が旧名の列を足し直さず改名する。型が違う旧名は改名しない（`tests/test_notion.py`）
- [x] 改名しない旧名の列（型が違う・新名が既にある）を `notion-setup` が名指しで知らせる
- [x] 新しいページに Source が入る。知らないソース名もそのまま送る。空なら送らない（テスト）
- [x] 本番: 改名の前後で 12 ページ × 12 列の値が一致（ページ id で突き合わせ、Status / Published At / Source は比較から外した）
- [x] 本番: Source が 12 ページすべて `hackernews`（議論の URL のホストから判定。判定できないページは 0 件）
- [x] 本番: 改名後の `notion-setup --dry-run` が「追加 0 件・何もしません」
- [x] `uv run ruff check .` / `uv run pytest -q`（487 件）
- [x] `docs/DESIGN.md` 3.1（列の表・列をソースごとに作らない方針・改名・Source が空のページ・戻し方）、3.3、「ソースを足すときに触る範囲」
- [x] `README.md`（以前の版の DB の改名、コードを更新したら `notion-setup` を 1 回）

## 本番での作業の記録（2026-09-23 20:0x JST）

| 手順 | 結果 |
|---|---|
| 改名前のスナップショット | 列 14、ページ 12（Draft 10 / Approved 1 / Published 1）、議論の URL はすべて news.ycombinator.com |
| `notion-setup` | 改名 3 件 + Source の追加を 1 回の PATCH で。「設計書の 15 件すべてが揃いました」 |
| 改名直後の比較 | 12 ページ × 12 列、不一致 0 |
| Source の埋め込み | 12 件（scratchpad の一度きりのスクリプト。コードには入れない） |
| 埋め込み後の比較 | 不一致 0。Source は `hackernews` 12 |
| 2 回目の `notion-setup --dry-run` | 追加 0 件 |

改名と push のあいだに `daily.yml`（06:17 JST）は走っていない（作業は 20 時台）。`publish.yml` は
Status / imo / URL Hash / Slug しか読まないので、改名の影響を受けない。

## 申し送り

- **戻すとき**は、コードを戻す前に Notion の UI で列名を旧名に戻す（逆だと旧コードの `notion-setup` が空の列を足す）
- **列の名前が変わる版を push したら、次の `daily.yml`（06:17 JST）より前に `notion-setup`**（README の「コードを更新したら」）。
  間に合わず全件失敗したら、Actions は何も commit しないので `notion-setup` のあと `gh workflow run daily.yml`。
  一部だけ失敗したら `git pull` → `notion-setup` → `notion-sync`。`daily.yml` の失敗通知の原因一覧にも足した
- `notion-setup` は旧名の列が残っていても終了コード 0（★ で知らせるだけ）。旧名の列を消すかは人が決めるので、失敗にはしない
- テストの「ソース固有の名前の列を作らない」は "HN" / "Qiita" の部分一致しか見ていない。3 つ目のソース名が入った列は検出しない

## レビュー

| 周 | 視点 | 主な指摘 | 対応 |
|---|---|---|---|
| 1 | A・B・C | 本番確認の前に「確認した」と書いている / 移行手順が無い / 改名しない旧名が黙って残る / 前後比較が順序依存 / 改名と push のあいだの compose | 本番で確認してから commit / README に節 / ★ で名指し / ページ id で比較し直し / 作業時刻で回避 |
| 2 | B・C | 移行手順が Actions の compose を想定していない | 「push したら次の daily より前に」に書き直し |
| 3 | B | 間に合わなかったときの手順が、全件失敗（何も commit されない）で通らない | 全件失敗と一部失敗で手順を分け、`daily.yml` の失敗通知と compose の失敗文言に案内を足した |

3 周目の修正は上限に達したので、レビューに回さず自分で確かめた（`compose` が全件失敗で `return 1` し、
`daily.yml` の commit ステップに `if:` が無く失敗時は走らないことをコードで確認。actionlint 通過）。

## 後続: Hatena URL 列の廃止（2026-09-23、f0fc62d）

ユーザーの問い「notion db のテーブルに hatena url があるけど合ってる？」を受けて、列ごと外した。
**列にするのは、絞り込み・並べ替えに使うか、パイプラインが読み戻す値だけ**（`docs/DESIGN.md` 3.1）。

- [x] スキーマと新しいページの投入から外した。ページ本文の出典のはてブのリンク、Markdown の `hatenaUrl`、サイトのリンクは残る（テスト）
- [x] 廃止した列は `notion-setup` が消さず、`RETIRED_PROPS` で名指しして知らせる（テスト、本番 dry-run で ★ が出ることを削除前に確認）
- [x] 本番の列を削除: 反映の順序は **push → CI 緑（f0fc62d）→ 実行中・待機中の daily.yml が 0 件 → 削除**（20:47 JST）。
      先に消すと main の古いコードの compose がその列に書こうとして全件失敗するので、レビューで順序を逆にした
- [x] 削除前の控え: 12 ページすべての `Hatena URL` が `hatena_bookmark_url(Source URL)` と一致（作り直せる。失う情報なし）
- [x] 削除後: 15 列 → 14 列。`Hatena URL` 以外の 12 列の値は 12 ページとも前後で一致。`notion-setup --dry-run` は「何もしません」
- [x] `uv run ruff check .` / `uv run pytest -q`（491 件）/ CI success

レビューで直したもの（2 周）: 反映の順序（push してから消す）、★ の文言（残しても影響なし、消してよい条件）、
compose の全件失敗の案内（Actions なら daily を回し直す、手元なら notion-sync — 前回の文言は手元の実行と食い違っていた）、
廃止を戻すときの手順。

申し送り:
- `notion-setup` の ★ の出力と終了コードを確かめる CLI のテストは無い（旧名の ★ と同じく既存の慣習どおり）
- compose が `hatena_bookmark_url` で組み立てる経路（`cli.py`）をテストが通っていない。空になっても気づけない

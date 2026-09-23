# M11: 記事にアイキャッチを付け、og:image にも使う

**Status:** 実装済み・CI での確認待ち（レビューで直したものは末尾）
**Blocked by:** なし

## なぜやるか

記事に見出しの画像が無く、**OGP のタグも 1 つも無かった**（`Base.astro` は `<title>` と
`description` だけ）。SNS で共有してもタイトルも画像も出ない状態だった。

## 決めたこと（ユーザーの判断）

| 項目 | 決定 |
|---|---|
| 作り方 | **タイトルカードをビルド時に自動生成**する |
| 表示位置 | **記事ページの冒頭（見出しの直下）+ og:image**。一覧には出さない |
| カードの中身 | **サイト名 + 記事タイトル + ソース名と注目度** |

**採らなかった案**: 生成 AI の画像（Gemini の画像生成は無料枠で使えない —
[料金表](https://ai.google.dev/gemini-api/docs/pricing)で全モデル "Not available"）、
元記事の og:image の流用（無断転載になる。はてブの OGP プレビューを避けた判断と同じ）。

## 調べて決めたこと（一次情報）

| 論点 | 決定 | 根拠 |
|---|---|---|
| 大きさ | 1200×630 PNG | [Meta](https://developers.facebook.com/docs/sharing/webmasters/images): 1.91:1 に近いほど切り抜かれない、8 MB 以下、`og:image:width/height` で初回から描ける |
| 描き方 | **Satori + Resvg** | [Vercel](https://vercel.com/docs/og-image-generation): `@vercel/og` は Satori と Resvg で PNG を作る。satori の作者側の参照実装 |
| PNG 化 | `@resvg/resvg-js` | `sharp` は Astro の**任意依存**（`optionalDependencies`）で、暗黙に頼ると環境によって入らない |
| フォント | **Noto Sans CJK JP Bold の公式 OTF を同梱**（4.6 MB） | 下表 |
| 生成の場所 | 静的エンドポイント `pages/og/[slug].png.ts` | [Astro](https://docs.astro.build/en/guides/endpoints/): `getStaticPaths` + `GET` でバイナリを返せる。サイトは完全な静的出力なので実行時には作れない |
| `<img>` の alt | `alt=""` | [WAI](https://www.w3.org/WAI/tutorials/images/decorative/): 隣のテキストで説明済みの画像は alt を空に。画像の文字は直上の見出しと同じ |
| X のカード | `twitter:*` を明示的に出す | 公式の仕様ページが消えていて（`docs.x.com` のトップへ転送）、og: へのフォールバックを**一次情報で確かめられなかった** |

**フォントの比較（実測、既存 12 記事のタイトル + 負荷用の文字列）**

| 候補 | 欠けた字 | 速度 |
|---|---|---|
| `@fontsource/noto-sans-jp` の japanese + latin（WOFF） | `𠮷髙﨑鷗 ①②③` | 1 枚目 744 ms / 以降 314 ms |
| 同 + 分割ファイル 122 個すべて | `𠮷髙﨑鷗 ①②③`（Google Fonts 版が収録していない） | 1 枚目 892 ms / 以降 約 300 ms |

（速度はスクリプト単体で測ったもの。ビルドの中では 1 枚目が約 0.6〜0.75 秒になる）
| **公式 OTF（採用）** | **なし** | 1 枚目 338 ms / 以降 330 ms |

公式 OTF はタグ `Sans2.004` の版と git blob sha が一致することを確認した（`site/fonts/README.md`）。

## 完了条件

### 生成
- [x] `site/src/pages/og/[slug].png.ts` が公開記事ごとに `dist/og/<slug>.png` を書き出す
- [x] 画像は 1200×630 の PNG、8 MB 以下（実測 45 KB）
- [x] カードにサイト名・記事タイトル・ソース名と注目度が載る
- [x] 注目度の書き方は記事ページの見出し下と同じ（`Hacker News ・ 1098 points / 452 コメント`、Qiita は `LGTM`）
- [x] 長いタイトルは字を小さくし、それでも収まらなければ 4 行で省略記号
- [x] **字の大きさは実際にレイアウトして行数を数えて選ぶ**（見積もりは既存記事 1 本で外れた。レビューで直した）
- [x] 折り返せない長い英単語や URL が右端からはみ出さない（画素で確かめるテストあり）
- [x] 既存記事のタイトルはすべて字が欠けずに描ける（テストで固定）
- [x] フォントに無い字は検出して警告する（ビルドは止めない）

### 未公開記事を漏らさない
- [x] **imo 未記入の記事の画像は生成しない**（記事ページと同じ `publishedArticles()` で絞る）
- [x] `site/scripts/check-unpublished.mjs` が OG 画像の漏れも検出する。**許可リスト方式**（`dist/og/` の下を全部数える）。サブディレクトリに置く・無関係な名前で置く、の 2 通りで検出を確認

### OGP
- [x] `og:title` / `og:description` / `og:url` / `og:type` / `og:site_name` / `og:locale` を全ページに出す
- [x] 記事ページに `og:image`（**絶対 URL**）/ `og:image:width` / `og:image:height` / `og:image:type` / `og:image:alt`
- [x] `twitter:card` は画像のあるページで `summary_large_image`、無いページで `summary`
- [x] `canonical` を出す

### 記事ページ
- [x] 見出しの直下にアイキャッチを出す（並びは h1 → 画像 → 日付・注目度）
- [x] `alt=""`、`width` / `height` を明記（読み込み中のレイアウトのずれを防ぐ）
- [x] 暗い背景でも境目が見える（枠線）

### 配信物
- [x] **フォントを配らない**（`site/fonts/` は `public/` の外。`dist/` にフォントが無いことを確認）
- [x] `dist/` の大きさ 120 KB

### 検査
- [x] `site/scripts/check-og.mjs` が、公開記事の画像の有無・寸法・8 MB 以下・og:image の絶対 URL・アイキャッチの参照を確かめる（3 通りの壊し方で検出を確認）
- [x] `.github/workflows/ci.yml` に `check-og.mjs` を足した
- [x] `cd site && npm test` が通る（22 → 51 件）
- [x] `npm run check` がエラー・警告 0（hint 3 件は変更前から）
- [x] `npm run build` が通る
- [x] `uv run pytest -q` / `uv run ruff check .` が通る（Python 側は無変更）
- [x] 追加した依存に既知の脆弱性が無い（`npm audit` 0 件）
- [ ] **GitHub Actions（ubuntu）で動く** — **未達: CI 未実行。** ロックファイルに `@resvg/resvg-js-linux-x64-gnu` は記録済み。ブランチに push して CI が通ってから main に入れる

### ドキュメント
- [x] `docs/DESIGN.md` 2.6 と 6 節のディレクトリ構成
- [x] `site/README.md` の構成表とアイキャッチの節
- [x] `site/fonts/README.md`（出典・ハッシュ・ライセンス・選んだ理由）
- [x] `CONTEXT.md` に「アイキャッチ (Eyecatch)」

## 見つけて直したもの（作業中）

- **`satori` 経由で `fflate` に中程度の脆弱性**（GHSA-px8p-9vwx-vf98、`unzipSync` の無限ループ）。
  satori が使うのは `inflateSync` だけで到達しないが、修正版 0.7.5 が同じ 0.7 系にあるので
  `overrides` で上げた。npm の提案（satori を 0.32.0 に下げる）は採らなかった

## 申し送り

- **公開ワークフロー（`publish.yml`）はビルド後の検査を回さずにデプロイしている。**
  未公開漏れの検査（`check-unpublished.mjs`）も OG 画像の検査も CI（push 時）だけで走る。
  今回より前からの隙間で、**OG 画像は `getStaticPaths` の段階で未公開記事を除いているので
  漏れない構造**になっているが、多重の守りとして `publish.yml` にも足すかは別に決める
- **ビルド時間**: 1 枚あたり約 0.3 秒で、公開記事の全件を毎回描き直す。**公開記事が約 1,500 本で
  公開ワークフローの 10 分の制限に近づく**。差分だけ描く手当ては `M12-og-cache.md` に起票した
  （着手の条件: ビルドのステップが 5 分を超える、または公開記事が 700 本を超える）。
  公開ワークフローの失敗時の案内にも、この原因と見分け方を足した
- **リポジトリが 4.6 MB 増える**（フォント）。npm で配る公式の静的 OTF が無いため
- **X のカードの挙動は一次情報で未確認**（公式ページが消えている）。`twitter:*` を明示的に出して
  フォールバックに頼らない形にした。実際の表示は、公開後に X のカードの検証で確かめるしかない
- **トップ・タグ・about などのページには og:image が無い**（`twitter:card` は `summary`）。
  サイト全体の既定の画像を作るかは別に決める

## レビューで直したもの（2026-09-23）

2 視点（正確性 / リスク）で並列にレビューした。**Blocker 0 / Major 4 / Minor 8**。

### Major

| 指摘 | 直したこと |
|---|---|
| **字の大きさの見積もりが実際の行数とずれる。** 字数から `ceil(幅 × 字の大きさ / 1056)` で見積もっていたが、1 行に入る字数の端数と「英単語は途中で折り返さない」ことで外れる。**既存記事 `2026-09-21-google-ax-agent-orchestrator`（52 字）が 64px で 3 行の見込みで、実際は 4 行**になっていた | **見積もりをやめ、実際にレイアウトして行数を数える**（`measureTitleLines`）。高さを渡さずに組むと satori は中身の高さの SVG を返すので、1 行の高さで割る。カードと実測は同じ要素（`titleNode`）を使うので見た目がずれない。1 回 1〜2 ms |
| **折り返せない長い英単語や URL がカードの右端で切れる** | `wordBreak: "break-word"`（収まらないときだけ折る）。画素で右の余白を調べるテストを足した |
| **記事が増えるとビルドが公開ワークフローの 10 分の制限に当たる**（全件を毎回描き直すため） | 閾値（公開記事 約 1,500 本）を記録し、`M12-og-cache.md` に起票。失敗時の案内に原因と見分け方を足した |
| **「GitHub Actions（ubuntu）で動く」を未検証のまま完了扱いにしていた** | 未達に戻した。ブランチで CI を通してから main に入れる |

### Minor

| 指摘 | 扱い |
|---|---|
| 未公開漏れの検査が「未公開記事の名前のファイルがあるか」しか見ておらず、サブディレクトリに置くとすり抜けた（レビュー役が実際にすり抜けさせた） | **許可リスト方式**に変えた |
| フォントに無い字の警告がログに埋もれる | GitHub Actions の注釈（`::warning file=...::`）の形で出す |
| アイキャッチが LCP の候補なのに `fetchpriority` が無い | `fetchpriority="high"` を足した |
| 行数のテストが実装の式を写していた | 実際に描いて数えるテストに置き換えた（外れていた記事の実物のタイトルで固定） |
| 1 枚目の描画時間の記述が文書どうしで食い違う（0.7 秒と 338 ms） | 測った条件（スクリプト単体 / ビルドの中）を書き分けた |
| `check-og.mjs` が `src` をエスケープせずに正規表現へ埋め込んでいた | エスケープした |
| `og.ts` のコメントが「エンドポイントもこの関数を使う」と書いていたが、実際はファイルの置き場所で出力先が決まる | コメントを実態に合わせ、置き場所をテストで固定した（横断チェックで自分で見つけた） |
| **却下**: 「`OFL.txt` から上流 LICENSE の著作権表示の行が落ちている」 | **誤検知。** レビュー役自身が「上流の内容は記憶による推測」と書いていた。同梱の `OFL.txt` は上流 `Sans2.004` の `LICENSE` と git blob sha（`d952d62c…`）が一致し、**バイト単位で同じ**。著作権表示はフォント本体の name テーブルにある（`Copyright 2014-2021 Adobe`） |

### 範囲外として直さなかったもの

- ヘッダーのリンクが `/about`（末尾スラッシュ無し）で、canonical の `/about/` とずれる — 変更前から
- `SITE_URL` にパスを含めると canonical / og:url から消える — `base` を設定していないので実際の配信先はルートで、
  sitemap の挙動とも揃っている
- 記事ページは `[...slug]`、OG は `[slug]` で形が違う — 記事は Python が平らに書き出すので id に `/` は入らない

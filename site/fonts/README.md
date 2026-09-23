# fonts

OG 画像（アイキャッチ）を描くための日本語フォント。**ビルド時にだけ使い、サイトには配らない**
（`public/` に置かないのはそのため。4.6 MB を読者に配る理由が無い）。

| ファイル | 中身 |
|---|---|
| `NotoSansJP-Bold.otf` | Noto Sans CJK JP の Bold（静的ウェイト、JP サブセット OTF） |
| `OFL.txt` | SIL Open Font License 1.1 の全文。同梱・再配布の条件として一緒に置く |

## 出典

- リポジトリ: https://github.com/notofonts/noto-cjk
- タグ: **`Sans2.004`**（`Sans/SubsetOTF/JP/NotoSansJP-Bold.otf`）
- git blob sha: `40262777db707145a08795e0e62ab5956eafe4b6`（タグの版と一致を確認済み）
- sha256: `1b0edfb500b73a4fa8a4fcaae1bbbd403994e08e73e3e0da37e70d3853f42c5f`
- ライセンス: SIL Open Font License 1.1（同タグのリポジトリ直下 `LICENSE`）

## なぜこのファイルか

| 候補 | 結果 |
|---|---|
| `@fontsource/noto-sans-jp` の `japanese` + `latin`（WOFF） | 既存記事のタイトルは描けるが、`𠮷髙﨑鷗`（異体字）と `①②③`（丸数字）が**欠ける**。分割ファイル 122 個を全部足しても欠けたまま（Google Fonts 版がそもそも収録していない） |
| **公式 OTF（このファイル）** | **欠けなし**。速度も同等（スクリプト単体で測って 1 枚目 338 ms、2 枚目以降 約 330 ms/枚。大半は描画側。ビルドの中では 1 枚目が約 0.6〜0.75 秒になる） |

satori は WOFF2 を読めず（https://github.com/vercel/satori ）、Vercel は「解析速度のため TTF / OTF を WOFF より推奨」と
明記している（https://vercel.com/docs/og-image-generation ）。

**npm で配る公式の静的 OTF が無い**ので、リポジトリに同梱した。ビルド時に取りに行く案は、
公開ワークフロー（`.github/workflows/publish.yml`）が外部サイトの可用性に依存するので採らなかった。

## 差し替えるとき

同じタグ系列の新しいリリースから取り、上の sha を更新する。**可変フォント（`NotoSansJP[wght].ttf`）は使わない** —
satori の README に可変フォントの記載が無く、動作が保証されていない。

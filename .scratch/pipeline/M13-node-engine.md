# M13: CI の Node（22.18）が依存の要求（22.19 以上）を満たしていない

**Status:** 未着手
**Blocked by:** なし

## 見つけたときの状況

M11 のリスクレビュー（2 周目）で、CI の `npm ci` のログに次の警告が出ていると指摘された。

```
npm warn EBADENGINE Unsupported engine {
npm warn EBADENGINE   package: 'undici@8.10.2',
  required: { node: '>=22.19.0' }, current: { node: 'v22.18.0' }
```

- 出どころ: `astro@7.3.3` → `unifont@0.7.5` → `undici@8.10.2`（`npm ls undici`）
- **M11 より前からある。** 変更前のコミット `896861f` のロックファイルにも `undici@8.10.2`（`engines: node >=22.19.0`）が入っている
- CI と公開ワークフローは Node を `22.18` に固定している（`.github/workflows/ci.yml` / `publish.yml` の
  `actions/setup-node`、`site/package.json` の `engines: >=22.18.0`）。22.18 を下限にしたのは、
  `.ts` を直接 `node --test` に渡すための型ストリッピングが既定で有効になった版だから（M3 で決めた）
- 今は**警告だけでビルドもテストも通っている**（CI run `35847114925` は success）。`undici` の中で
  22.19 の機能を使う経路を踏んでいないだけで、踏めば落ちうる

M11 では直さない。M11 の差分（アイキャッチ）と関係が無く、Node の版はサイト全体に効くため。

## 完了条件

- [ ] CI・公開ワークフロー・`site/package.json` の `engines` の Node の版を、依存が要求する版以上に揃えた
      （一次情報: https://nodejs.org/ の 22 系の最新、と各ワークフローの `node-version`）
- [ ] `npm ci` のログに `EBADENGINE` が出ない
- [ ] `cd site && npm test && npm run check && npm run build` が新しい版で通る
- [ ] `site/package.json` の `engines` と README の Node の記述（ルートと `site/`）を合わせた

## 着手できる条件

いつでも。Node 22 系の中での更新なので、型ストリッピングの前提（22.18 以上）は崩れない。

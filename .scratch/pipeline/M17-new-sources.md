# M17: GitHub と公式ブログ（Cloudflare・Vercel）をソースに足す

**Status:** 完了（本番の daily.yml に反映。次の実行から効く）
**Blocked by:** なし

「AI・クラウド・言語・ガジェット/IT ニュースをもっと収集してほしい」の 3 つ目の手（1・2 は話題の優先と 1 日 10 本）。

## 決めたこと

- ユーザーの判断: 3 つとも足す / ブログは各 1 日 1 本まで枠を確保（10 本の内数）/ GitHub は作成 30 日以内の stars 上位、本文は README、所有者のハンドルは伏せる
- 自分で決めた: GitHub は stars 1,000 以上・**1 日 2 本まで・収集 10 件まで**（stars と HN の points の桁が違い、収集の実測で 53 件中 48 件が GitHub になった）。Vercel は `/blog/` だけ（Atom の 6 割は changelog）
- ハンドルを伏せる範囲は Qiita と同じ: LLM 入力から伏せ、出典の `sourceUrl` には残す（DESIGN 4.1d）
- 調査と判定（使えないソースを含む）は `docs/DESIGN.md` 4.1d

## 完了条件

- [x] 3 ソースが StoryFeed / ReactionSource を満たし registry から作れる（`tests/test_new_sources.py`）
- [x] ブログは各 1 日 1 本まで（穴埋めでも 2 本目を取らない）、収集・問い合わせで落ちない（テスト）
- [x] GitHub は README を API で取り HTML を取りに行かない。タイトルにハンドルを入れない（テスト）
- [x] GitHub が枠を独占しない（収集 10 件・1 日 2 本・問い合わせは 6 件まで）（テスト、実測）
- [x] フィードや GitHub の失敗（5xx・壊れた応答・レート上限）で compose を止めない（テスト）
- [x] 本番ストアの複製で collect（新規 14 件 = GitHub 10 / HN 2 / Cloudflare 2）と compose --dry-run（選出 10 件 = Cloudflare 1 / GitHub 1（本文は api）/ HN 8）
- [x] サイトの注目度の表示を `engagementText` に 1 本化（ブログは表示名だけ、GitHub は stars）
- [x] `ruff format --check .` / `ruff check .` / pytest 579 / site npm test・check・build・check-unpublished・check-og

## 申し送り

- GitHub の README が一時的な失敗（レート上限・5xx）で取れないと、候補は本文取得できず（no_content）で打ち切られ戻らない。一時的な失敗と「README が無い」を分けるとよい
- README は全体を読んでから大きさを見ている（読みながら打ち切ってはいない）
- 30 日以内・stars 上位 10 件は毎日ほぼ同じ顔ぶれになりうる。`stats` で source=github の新規件数を数日見る
- HN と GitHub で同じリポジトリの URL は url_hash が同じで、先に収集した側だけが残る（GitHub が先だと HN の論調が失われうる）
- 各サイトの説明文は公式ブログも「話題になった」とひとまとめに書いている（ブログは枠で新着を選んでいる）
- stars 1,000・1 日 2 本・ブログ 1 日 1 本が妥当かは運用で見る

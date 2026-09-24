import assert from "node:assert/strict";
import { test } from "node:test";

import { engagementText, hasSeparateDiscussion, scoreUnit, sourceLabel } from "./sources.ts";

test("Hacker News は議論が別 URL にある", () => {
  assert.equal(
    hasSeparateDiscussion({
      sourceUrl: "https://example.com/a",
      discussionUrl: "https://news.ycombinator.com/item?id=1",
    }),
    true,
  );
});

test("記事プラットフォームでは議論の場所が記事ページ自身", () => {
  // 同じ URL へのリンクを 2 本出さない。反応が 0 件のときに
  // 「議論」へのリンクが出ると、議論があるかのように読める
  const url = "https://qiita.com/someone/items/aaaaaaaaaaaaaaaaaaaa";
  assert.equal(hasSeparateDiscussion({ sourceUrl: url, discussionUrl: url }), false);
});

test("議論の URL が空なら出さない", () => {
  assert.equal(
    hasSeparateDiscussion({ sourceUrl: "https://example.com/a", discussionUrl: "" }),
    false,
  );
});

test("注目度の呼び名はソースごとに違う", () => {
  assert.equal(scoreUnit("hackernews"), "points");
  assert.equal(scoreUnit("qiita"), "LGTM");
  // 知らないソースでも壊れない
  assert.equal(scoreUnit("nosuch"), "points");
});

test("表示名を知らないソースは生の名前を出す", () => {
  assert.equal(sourceLabel("qiita"), "Qiita");
  assert.equal(sourceLabel("nosuch"), "nosuch");
});

test("注目度の 1 行はソースの性質で変わる", () => {
  assert.equal(engagementText("hackernews", 342, 187), "Hacker News 342 points / 187 コメント");
  // GitHub はコメントを持たない
  assert.equal(engagementText("github", 5000, 0), "GitHub 5000 stars");
  // 公式ブログは注目度を持たない。「0 points」と出すと話題にならなかったように読める
  assert.equal(engagementText("cloudflare-blog", 0, 0), "Cloudflare Blog");
  assert.equal(engagementText("hackernews", 1, 2, " ・ "), "Hacker News ・ 1 points / 2 コメント");
});

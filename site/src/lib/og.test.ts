/**
 * OG 画像（アイキャッチ）のレイアウトのテスト。描画はしない（それは og-render.test.ts）。
 */
import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { test } from "node:test";

import {
  OG_HEIGHT,
  OG_WIDTH,
  type OgNode,
  TITLE_MAX_LINES,
  TITLE_SIZES,
  TITLE_WIDTH,
  chooseTitleFontSize,
  metaLine,
  ogCardTree,
  ogImagePath,
  titleNode,
} from "./og.ts";

const CARD = { title: "タイトル", source: "hackernews", score: 1098, comments: 452 };

/** 木の中の文字列をすべて集める。 */
function texts(node: OgNode): string[] {
  const c = node.props.children;
  if (typeof c === "string") return [c];
  if (Array.isArray(c)) return c.flatMap(texts);
  return c ? texts(c) : [];
}

test("推奨サイズは 1200×630", () => {
  // 1.91:1 に近いほどフィードで切り抜かれない（Meta の公式）
  assert.equal(OG_WIDTH, 1200);
  assert.equal(OG_HEIGHT, 630);
});

test("画像のパスはエンドポイントの置き場所と一致する", () => {
  // 出力先は pages/og/[slug].png.ts というファイルの置き場所で決まる。
  // ずれると og:image が 404 を指す（ビルド後は check-og.mjs も検出する）
  assert.equal(ogImagePath("2026-09-22-example"), "/og/2026-09-22-example.png");
  assert.ok(existsSync("src/pages/og/[slug].png.ts"), "エンドポイントの置き場所が変わった");
});

test("注目度の行は記事ページの見出し下と同じ書き方", () => {
  assert.equal(metaLine(CARD), "Hacker News ・ 1098 points / 452 コメント");
});

test("注目度の呼び名はソースで変わる", () => {
  assert.equal(metaLine({ source: "qiita", score: 9, comments: 0 }), "Qiita ・ 9 LGTM / 0 コメント");
});

// --- 字の大きさの選び方 ---------------------------------------------------
// 行数は描画側が実測して渡す（og-render.test.ts が本物で確かめる）。ここでは選び方だけを見る

/** 字の大きさ → 行数 の表から、測る関数を作る。どの大きさを測ったかも記録する。 */
function fakeMeasure(lines: Record<number, number>) {
  const asked: number[] = [];
  const measure = async (size: number) => {
    asked.push(size);
    return lines[size] ?? 99;
  };
  return { measure, asked };
}

test("収まるいちばん大きい字を選ぶ", async () => {
  const { measure } = fakeMeasure({ 64: 4, 56: 3, 48: 3, 42: 2 });
  assert.equal(await chooseTitleFontSize(measure), 56);
});

test("短いタイトルは最大の字で描く", async () => {
  const { measure } = fakeMeasure({ 64: 2 });
  assert.equal(await chooseTitleFontSize(measure), 64);
});

test("収まった時点でそれより小さい字は測らない", async () => {
  const { measure, asked } = fakeMeasure({ 64: 5, 56: 3 });
  await chooseTitleFontSize(measure);
  assert.deepEqual(asked, [64, 56]);
});

test("どの大きさでも収まらなければ最小の字にする", async () => {
  // 小さすぎる字は SNS の縮小表示で読めない。溢れた分は省略記号に任せる
  const { measure } = fakeMeasure({});
  assert.equal(await chooseTitleFontSize(measure), TITLE_SIZES[TITLE_SIZES.length - 1]);
});

test("収めたい行数は 3 行", () => {
  assert.equal(TITLE_MAX_LINES, 3);
});

test("カードのタイトルと実測のタイトルは同じ見た目で組む", () => {
  // 見た目（幅・字の大きさ・行間・折り返し）がずれると、実測が意味を失う
  const card = titleNode("タイトル", 56, { clamp: true }).props.style ?? {};
  const measured = titleNode("タイトル", 56, { clamp: false }).props.style ?? {};
  for (const key of ["width", "fontSize", "lineHeight", "fontFamily", "wordBreak"]) {
    assert.equal(card[key], measured[key], key);
  }
  assert.equal(card.width, TITLE_WIDTH);
});

test("実測のときは省略せずに組む", () => {
  // 省略すると本当の行数が分からない
  assert.equal(titleNode("タイトル", 56, { clamp: false }).props.style?.lineClamp, undefined);
});

test("折り返せない長い英単語は途中で折る", () => {
  // 指定が無いと 1 行より長い単語が右端で切れる。break-all だと普通の英単語も崩れる
  assert.equal(titleNode("タイトル", 56, { clamp: true }).props.style?.wordBreak, "break-word");
});

test("カードにはサイト名・タイトル・注目度の 3 つが載る", () => {
  const all = texts(ogCardTree({ ...CARD, title: "記事のタイトル" }, 64));
  assert.ok(all.includes("imoTech"));
  assert.ok(all.includes("記事のタイトル"));
  assert.ok(all.includes("Hacker News ・ 1098 points / 452 コメント"));
});

test("カードの大きさは OG 画像と同じ", () => {
  const style = ogCardTree(CARD, 64).props.style ?? {};
  assert.equal(style.width, OG_WIDTH);
  assert.equal(style.height, OG_HEIGHT);
});

test("日本語の禁則を効かせる", () => {
  assert.equal(ogCardTree(CARD, 64).props.lang, "ja-JP");
});

test("タイトルは選んだ大きさで、行数を制限して描く", () => {
  const children = ogCardTree(CARD, 48).props.children as OgNode[];
  const title = children.find((c) => c.props.children === CARD.title);
  assert.ok(title, "タイトルの要素が無い");
  assert.equal(title.props.style?.fontSize, 48);
  assert.equal(title.props.style?.lineClamp, 4);
});

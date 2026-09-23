/**
 * OG 画像の描画のテスト。同梱のフォント（site/fonts/）で実際に描く。
 *
 * **一番守りたいのは「タイトルの字が抜けたまま公開される」こと。** satori はフォントに
 * 無い字を黙って空白で描くので、ここで既存記事のタイトルと、落としやすい字を当てる。
 */
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { test } from "node:test";

import { Resvg } from "@resvg/resvg-js";

import { OG_HEIGHT, OG_WIDTH, TITLE_MAX_LINES, TITLE_SIZES, TITLE_WIDTH } from "./og.ts";
import {
  measureTitleLines,
  ogCardTreeFor,
  renderOgPng,
  renderOgSvg,
  renderTreeSvg,
} from "./og-render.ts";
import type { OgNode } from "./og.ts";

const card = (title: string) => ({ title, source: "hackernews", score: 100, comments: 30 });

function existingTitles(): string[] {
  const dir = "src/content/articles";
  return readdirSync(dir)
    .filter((f) => f.endsWith(".md"))
    .map((f) => readFileSync(`${dir}/${f}`, "utf8").match(/^title: "(.*)"$/m)?.[1] ?? "");
}

/** カードのタイトルに選ばれた字の大きさ。 */
async function chosenSize(title: string): Promise<number> {
  const tree = await ogCardTreeFor(card(title));
  const children = tree.props.children as { props: { children?: unknown; style?: Record<string, unknown> } }[];
  return Number(children.find((c) => c.props.children === title)?.props.style?.fontSize);
}

async function missingIn(title: string): Promise<string[]> {
  const missing = new Set<string>();
  await renderOgSvg(card(title), missing);
  return [...missing];
}

test("PNG として 1200×630 で描ける", async () => {
  const png = await renderOgPng(card("タイトル"));
  assert.deepEqual([...png.subarray(0, 8)], [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  // IHDR の幅と高さ（署名 8 バイト + 長さ 4 + 種別 4 の直後）
  assert.equal(png.readUInt32BE(16), OG_WIDTH);
  assert.equal(png.readUInt32BE(20), OG_HEIGHT);
});

test("SNS の上限（8 MB）よりずっと小さい", async () => {
  const png = await renderOgPng(card("あ".repeat(80)));
  assert.ok(png.length < 1024 * 1024, `${png.length} bytes`);
});

test("既存記事のタイトルはすべて字が欠けずに描ける", async () => {
  const titles = existingTitles();
  assert.ok(titles.length > 0);
  for (const t of titles) assert.deepEqual(await missingIn(t), [], t);
});

// --- 字の大きさと行数（実測） ---------------------------------------------

test("行数を実際のレイアウトで数える", async () => {
  assert.equal(await measureTitleLines("短い", 64), 1);
  // 1 行に 16 字（1056 / 64）しか入らない。17 字なら 2 行
  assert.equal(await measureTitleLines("あ".repeat(16), 64), 1);
  assert.equal(await measureTitleLines("あ".repeat(17), 64), 2);
});

test("既存記事のタイトルはすべて選んだ字の大きさで 3 行以内に収まる", async () => {
  // **回帰テスト。** 字数からの見積もりで選んでいたころ、52 字の記事が
  // 「64 px で 3 行」の見込みで実際は 4 行になり、最後が省略されていた
  for (const t of existingTitles()) {
    const size = await chosenSize(t);
    assert.ok((await measureTitleLines(t, size)) <= TITLE_MAX_LINES, `${size}px: ${t}`);
  }
});

/** カードのタイトルが**省略されずに全文描かれているか**を、行数の実測とは独立に確かめる。
 *
 * 同じカードを「行数の制限あり」と「実質無制限」で描き比べる。全文が入っていれば省略記号は
 * 出ず、2 つの SVG は同じになる。**`measureTitleLines` を使わない**ので、
 * 実測の関数そのものが誤っていても（あるいは実測とカードで組み方がずれても）ここで分かる。 */
async function titleFullyShown(title: string): Promise<boolean> {
  const tree = await ogCardTreeFor(card(title));
  const unclamped = structuredClone(tree) as OgNode;
  for (const child of unclamped.props.children as OgNode[]) {
    if (child.props.children === title && child.props.style) child.props.style.lineClamp = 99;
  }
  return (await renderTreeSvg(tree)) === (await renderTreeSvg(unclamped));
}

test("既存記事のタイトルはカードで省略されずに全文が出る", async () => {
  for (const t of existingTitles()) assert.ok(await titleFullyShown(t), t);
});

test("省略されたかの判定は、本当に長いタイトルでは省略を検出する", async () => {
  // 上のテストが素通りでないこと（描き比べで違いが出ること）の確認
  assert.equal(await titleFullyShown("あ".repeat(120)), false);
});

test("見積もりで外れていた記事は 64px ではなく 56px を選ぶ", async () => {
  // レビューで見つかった実在の記事。字数（52 字）からは 64px で 3 行と見積もっていた
  const t = readFileSync("src/content/articles/2026-09-21-google-ax-agent-orchestrator.md", "utf8")
    .match(/^title: "(.*)"$/m)?.[1];
  assert.ok(t);
  assert.equal(await measureTitleLines(t, 64), 4);
  assert.equal(await chosenSize(t), 56);
});

test("3 行に収まらない長さなら最小の字にする", async () => {
  assert.equal(await chosenSize("あ".repeat(120)), TITLE_SIZES[TITLE_SIZES.length - 1]);
});

/** カードを画素に描き、タイトルの右の余白に濃い画素があるか（字がはみ出したか）を見る。 */
async function overflowsRight(title: string): Promise<boolean> {
  const img = new Resvg(await renderOgSvg(card(title))).render();
  // `pixels` は読むたびに画素全体（1200×630×4 バイト）を複製する。1 回だけ取る
  const px = img.pixels;
  const width = img.width;
  const right = (OG_WIDTH + TITLE_WIDTH) / 2; // タイトルの右端（左右の余白は等しい）
  for (let y = 100; y < 560; y++) {
    for (let x = Math.ceil(right) + 4; x < width; x++) {
      const i = (y * width + x) * 4;
      if (px[i] < 128 && px[i + 3] > 0) return true;
    }
  }
  return false;
}

test("折り返せない長い英単語も右端からはみ出さない", async () => {
  // **回帰テスト。** 折り返しの指定が無かったころ、1 行より長い単語が画像の右端で切れていた
  assert.equal(
    await overflowsRight("Supercalifragilisticexpialidocious_and_antidisestablishmentarianism_x の話"),
    false,
  );
});

test("長い URL も右端からはみ出さない", async () => {
  assert.equal(await overflowsRight("https://example.com/a/very/long/path/that/never/breaks/naturally/index.html を読む"), false);
});

test("はみ出しの判定は普通のタイトルで誤検出しない", async () => {
  assert.equal(await overflowsRight(existingTitles()[0]), false);
});

test("落としやすい字も描ける", async () => {
  // Google Fonts 版の Noto Sans JP には無く、fontsource では欠けた字。
  // 同梱の公式 OTF（Noto Sans CJK JP）なら入っている（site/fonts/README.md）
  assert.deepEqual(await missingIn("𠮷髙﨑鷗 ①②③ 齟齬 贔屓 鬱 —「」『』〜…"), []);
});

test("英数字と記号も描ける", async () => {
  assert.deepEqual(await missingIn("GPT-2 / C++ & Rust: 100% (v1.0) #tag @user"), []);
});

test("フォントに無い字は検出できる", async () => {
  // 絵文字は同梱のフォントに無い。**黙って空白にされず、呼び出し側に知らされる**こと
  assert.notDeepEqual(await missingIn("絵文字 🦀"), []);
});

/**
 * 公開ゲートのテスト。
 *
 * ここが破れると「所感を書いていない記事が公開される」という、書き手にとって
 * 取り返しのつかない事故になる。レビューで fail-open だったものを許可リスト方式に
 * 直した経緯があるので、素通りしたケースを 1 件ずつ固定しておく。
 *
 * 実行: cd site && npm test
 */
import assert from "node:assert/strict";
import { test } from "node:test";
import { IMO_PLACEHOLDER, IMO_SENTINEL, imoOf } from "./imo.ts";

const PLACEHOLDER_LINE = `${IMO_PLACEHOLDER} ここに所感を 1 行以上書く。${IMO_SENTINEL}、この記事はサイトに公開されません -->`;

function article(imoSection: string): string {
  return [
    "## 元記事の要旨",
    "",
    "- 要旨",
    "",
    "## 議論の論調",
    "",
    "### 論点",
    "",
    "詳細",
    "",
    "## imo",
    "",
    imoSection,
    "",
  ].join("\n");
}

// --- 公開しないケース（fail-closed であること）---------------------------

test("body が undefined なら公開しない", () => {
  assert.equal(imoOf(undefined), null);
});

test("body が null なら公開しない", () => {
  assert.equal(imoOf(null), null);
});

test("body が空文字なら公開しない", () => {
  assert.equal(imoOf(""), null);
});

test("imo 見出しが無ければ公開しない", () => {
  assert.equal(imoOf("## 元記事の要旨\n\n- x\n"), null);
});

test("プレースホルダが丸ごと残っていれば公開しない", () => {
  assert.equal(imoOf(article(PLACEHOLDER_LINE)), null);
});

test("空白の無い <!--imo: でも公開しない", () => {
  // 表記ゆれ。固定句で拾う
  assert.equal(imoOf(article(`<!--imo: ここに所感を書く。${IMO_SENTINEL}、公開されません -->`)), null);
});

test("プレースホルダを部分的に消しただけでは公開しない", () => {
  // 行選択のミスで開始タグだけ消えるのは普通に起きる。
  // ここを通すと運営の内部指示が記事本文として公開される
  assert.equal(imoOf(article(`ここに所感を 1 行以上書く。${IMO_SENTINEL}、公開されません -->`)), null);
});

test("imo 見出しだけで中身が無ければ公開しない", () => {
  assert.equal(imoOf(article("")), null);
});

test("空白と改行だけなら公開しない", () => {
  assert.equal(imoOf(article("   \n\n\t  ")), null);
});

test("別の HTML コメントだけなら公開しない", () => {
  assert.equal(imoOf(article("<!-- あとで書く -->")), null);
});

test("プレースホルダの下に書いても公開しない", () => {
  // コメント行を消さずに書き足すのはよくある誤操作
  assert.equal(imoOf(article(`${PLACEHOLDER_LINE}\n\n面白かった。`)), null);
});

test("コメントの内側に書いても公開しない", () => {
  assert.equal(imoOf(article(`<!-- imo: 面白かった -->`)), null);
});

// --- 公開するケース -------------------------------------------------------

test("所感が書かれていれば公開する", () => {
  assert.equal(imoOf(article("これは面白い。")), "これは面白い。");
});

test("複数行の所感も公開する", () => {
  const imo = "1 行目。\n\n2 行目。";
  assert.equal(imoOf(article(imo)), imo);
});

test("所感のあとに別の HTML コメントがあっても公開する", () => {
  assert.equal(imoOf(article("面白い。<!-- メモ -->")), "面白い。");
});

test("imo が最後のセクションでなくても切り出せる", () => {
  const body = ["## imo", "", "所感。", "", "## おまけ", "", "別の話。"].join("\n");
  assert.equal(imoOf(body), "所感。");
});

test("次の見出しの内容を imo に含めない", () => {
  const body = ["## imo", "", "所感。", "", "## 出典", "", "リンク"].join("\n");
  assert.equal(imoOf(body), "所感。");
});

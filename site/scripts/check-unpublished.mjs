/**
 * imo 未記入の記事がビルド出力に混ざっていないかを、成果物そのもので検査する。
 *
 * 判定はゲート本体（src/lib/imo.ts の imoOf）を呼ぶ。固定句の grep だけで判定すると、
 * プレースホルダを消して不可視文字だけを書いた記事を取りこぼす
 * （U+200B / U+FEFF などは trim() を通り抜ける）。
 *
 * 実行: cd site && npm run build && node scripts/check-unpublished.mjs
 */
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { imoOf } from "../src/lib/imo.ts";

const ARTICLES = "src/content/articles";
const DIST = "dist";

if (!existsSync(DIST)) {
  console.error(`${DIST}/ がありません。先に npm run build を実行してください。`);
  process.exit(1);
}

const rss = existsSync(join(DIST, "rss.xml")) ? readFileSync(join(DIST, "rss.xml"), "utf8") : "";
const sitemap = existsSync(join(DIST, "sitemap-0.xml"))
  ? readFileSync(join(DIST, "sitemap-0.xml"), "utf8")
  : "";

const files = existsSync(ARTICLES)
  ? readdirSync(ARTICLES).filter((f) => f.endsWith(".md"))
  : [];

let leaked = 0;
let unpublished = 0;

for (const file of files) {
  const slug = file.replace(/\.md$/, "");
  const raw = readFileSync(join(ARTICLES, file), "utf8");
  // フロントマターを落として本文だけを渡す（Astro の entry.body と同じ形）
  const body = raw.startsWith("---\n") ? raw.slice(4).split("\n---\n").slice(1).join("\n---\n") : raw;

  if (imoOf(body) !== null) continue; // 公開されてよい記事
  unpublished += 1;

  if (existsSync(join(DIST, "articles", slug, "index.html"))) {
    console.error(`::error file=${ARTICLES}/${file}::imo 未記入なのに dist/articles/${slug}/ が生成されている`);
    leaked += 1;
  }
  if (rss.includes(slug)) {
    console.error(`::error file=${ARTICLES}/${file}::imo 未記入なのに RSS に載っている`);
    leaked += 1;
  }
  if (sitemap.includes(slug)) {
    console.error(`::error file=${ARTICLES}/${file}::imo 未記入なのに sitemap に載っている`);
    leaked += 1;
  }
}

if (leaked > 0) {
  console.error(`\n${leaked} 件の漏れを検出しました。`);
  process.exit(1);
}
console.log(`記事 ${files.length} 件（うち imo 未記入 ${unpublished} 件）。出力への漏れはありません。`);

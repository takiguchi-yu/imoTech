/**
 * imo 未記入の記事がビルド出力に混ざっていないかを、成果物そのもので検査する。
 *
 * 判定はゲート本体（src/lib/imo.ts の imoOf）を呼ぶ。固定句の grep だけで判定すると、
 * プレースホルダを消して不可視文字だけを書いた記事を取りこぼす
 * （U+200B / U+FEFF などは trim() を通り抜ける）。
 *
 * 実行: cd site && npm run build && node scripts/check-unpublished.mjs
 */
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
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

// OG 画像（pages/og/[slug].png.ts）。ページが作られなくても画像だけ出ていれば、
// 画像に描かれたタイトルから未公開記事の中身が漏れる。
//
// **許可リスト方式で数える。** 「未公開記事の名前のファイルがあるか」を見るだけだと、
// 出力の場所が少しずれた（サブディレクトリ、ルートの形の変更、フロントマターの slug）だけで
// 漏れていても通ってしまう。dist/og/ の下を全部数え、公開記事の画像でないものが 1 つでもあれば落とす
const OG_DIR = join(DIST, "og");
const published = new Set(
  files
    .filter((f) => {
      const raw = readFileSync(join(ARTICLES, f), "utf8");
      const body = raw.startsWith("---\n") ? raw.slice(4).split("\n---\n").slice(1).join("\n---\n") : raw;
      return imoOf(body) !== null;
    })
    .map((f) => `${f.replace(/\.md$/, "")}.png`),
);
const ogFiles = existsSync(OG_DIR) ? readdirSync(OG_DIR, { recursive: true }).map(String) : [];
for (const rel of ogFiles) {
  if (statSync(join(OG_DIR, rel)).isDirectory()) continue;
  if (!published.has(rel)) {
    console.error(`::error file=${join(OG_DIR, rel)}::公開記事のものではない OG 画像が出力に含まれている（未公開記事のタイトルが画像から漏れうる）`);
    leaked += 1;
  }
}

// ページの HTML 全体（トップ・タグ別一覧・記事・about など）。**許可リスト方式で見る。**
// 一覧が公開判定（publishedArticles）を通らなくなった場合、未公開記事のタイトルとリンクが
// トップに出る。個々のページを名指しで見るだけだと、ページが増えたり形が変わったりしたときに漏れる。
// 未公開記事の slug（ファイル名）が、どこかの HTML に 1 つでも出たら落とす
const unpublishedSlugs = files
  .filter((f) => {
    const raw = readFileSync(join(ARTICLES, f), "utf8");
    const body = raw.startsWith("---\n") ? raw.slice(4).split("\n---\n").slice(1).join("\n---\n") : raw;
    return imoOf(body) === null;
  })
  .map((f) => f.replace(/\.md$/, ""));
const htmlFiles = readdirSync(DIST, { recursive: true })
  .map(String)
  .filter((rel) => rel.endsWith(".html"));
for (const rel of htmlFiles) {
  const html = readFileSync(join(DIST, rel), "utf8");
  for (const slug of unpublishedSlugs) {
    // slug の前後が区切りであることまで見る。部分一致だと、公開記事 `X-part2` へのリンクを
    // 未公開の `X` の漏れと誤判定し、正しい状態でデプロイが止まる
    const esc = slug.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    if (new RegExp(`(?<![\\w-])${esc}(?![\\w-])`).test(html)) {
      console.error(`::error file=${join(DIST, rel)}::imo 未記入の記事 ${slug} がこのページに出ている（タイトルやリンクが漏れうる）`);
      leaked += 1;
    }
  }
}

if (leaked > 0) {
  console.error(`\n${leaked} 件の漏れを検出しました。`);
  process.exit(1);
}
console.log(`記事 ${files.length} 件（うち imo 未記入 ${unpublished} 件）。出力への漏れはありません。`);

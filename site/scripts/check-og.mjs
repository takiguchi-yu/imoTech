/**
 * 公開記事の OG 画像（アイキャッチ）が、成果物として正しく出ているかを検査する。
 *
 * **未公開記事の画像が漏れていないか**は check-unpublished.mjs の仕事で、ここは見ない。
 * ここが見るのは、公開記事について「共有したのに画像が出ない」を起こす壊れ方だけ。
 *
 * - dist/og/<slug>.png があり、PNG で、1200×630、8 MB 以下
 *   （https://developers.facebook.com/docs/sharing/webmasters/images ）
 * - 記事ページの og:image が**絶対 URL**でその画像を指し、寸法のタグが画像と一致する
 * - 記事ページのアイキャッチ（<img class="eyecatch">）が同じ画像を指す
 * - 一覧（トップとタグ別）のサムネイルが、公開記事の実在する画像だけを指し、
 *   寸法を書き、画像のリンクが読み上げとキーボードから外れている
 *
 * 実行: cd site && npm run build && node scripts/check-og.mjs
 */
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { imoOf } from "../src/lib/imo.ts";
import { OG_HEIGHT, OG_WIDTH, ogImagePath } from "../src/lib/og.ts";

const ARTICLES = "src/content/articles";
const DIST = "dist";
const MAX_BYTES = 8 * 1024 * 1024;
const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

if (!existsSync(DIST)) {
  console.error(`${DIST}/ がありません。先に npm run build を実行してください。`);
  process.exit(1);
}

/** PNG の IHDR から幅と高さを読む（先頭 8 バイトの署名の直後が IHDR）。 */
function pngSize(buf) {
  if (buf.length < 24 || !buf.subarray(0, 8).equals(PNG_SIGNATURE)) return null;
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
}

/** `<meta property="og:image" content="...">` の content を取る。属性の順は問わない。 */
function meta(html, key) {
  const tag = html.match(new RegExp(`<meta[^>]*(?:property|name)="${key}"[^>]*>`));
  return tag?.[0].match(/content="([^"]*)"/)?.[1];
}

const files = existsSync(ARTICLES) ? readdirSync(ARTICLES).filter((f) => f.endsWith(".md")) : [];

let problems = 0;
let checked = 0;
const fail = (file, msg) => {
  console.error(`::error file=${ARTICLES}/${file}::${msg}`);
  problems += 1;
};

for (const file of files) {
  const slug = file.replace(/\.md$/, "");
  const raw = readFileSync(join(ARTICLES, file), "utf8");
  const body = raw.startsWith("---\n") ? raw.slice(4).split("\n---\n").slice(1).join("\n---\n") : raw;
  if (imoOf(body) === null) continue; // 未公開。check-unpublished.mjs の担当
  checked += 1;

  const src = ogImagePath(slug);
  const png = join(DIST, src);
  if (!existsSync(png)) {
    fail(file, `OG 画像 ${png} が無い（共有しても画像が出ない）`);
    continue;
  }
  const buf = readFileSync(png);
  const size = pngSize(buf);
  if (!size) fail(file, `${png} が PNG ではない`);
  else if (size.width !== OG_WIDTH || size.height !== OG_HEIGHT)
    fail(file, `${png} が ${size.width}×${size.height}（${OG_WIDTH}×${OG_HEIGHT} のはず）`);
  if (statSync(png).size > MAX_BYTES) fail(file, `${png} が 8 MB を超えている`);

  const page = join(DIST, "articles", slug, "index.html");
  if (!existsSync(page)) {
    fail(file, `記事ページ ${page} が無い`);
    continue;
  }
  const html = readFileSync(page, "utf8");
  const ogImage = meta(html, "og:image");
  if (!ogImage) fail(file, "og:image が無い");
  // SNS のクローラーは相対 URL を解決しない。絶対 URL でなければ画像は出ない
  else if (!/^https?:\/\//.test(ogImage) || !ogImage.endsWith(src))
    fail(file, `og:image が絶対 URL で ${src} を指していない: ${ogImage}`);
  if (meta(html, "og:image:width") !== String(OG_WIDTH) || meta(html, "og:image:height") !== String(OG_HEIGHT))
    fail(file, "og:image:width / og:image:height が画像の寸法と一致しない");
  if (meta(html, "twitter:card") !== "summary_large_image") fail(file, "twitter:card が summary_large_image でない");
  // src をそのまま正規表現に埋め込むと `.` が任意の 1 字に当たり、緩く一致してしまう
  const esc = src.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  if (!new RegExp(`<img[^>]*class="eyecatch"[^>]*src="${esc}"|<img[^>]*src="${esc}"[^>]*class="eyecatch"`).test(html))
    fail(file, `記事ページのアイキャッチが ${src} を指していない`);
}

// --- 一覧のサムネイル（components/ArticleEntry.astro） ---------------------
const failPage = (page, msg) => {
  console.error(`::error file=${page}::${msg}`);
  problems += 1;
};
/** 公開記事の slug とタグ。一覧に**いくつ並ぶはずか**を数えるのに使う。 */
const publishedArticles = files
  .map((f) => ({ f, raw: readFileSync(join(ARTICLES, f), "utf8") }))
  .filter(({ raw }) => {
    const body = raw.startsWith("---\n") ? raw.slice(4).split("\n---\n").slice(1).join("\n---\n") : raw;
    return imoOf(body) !== null;
  })
  .map(({ f, raw }) => {
    // 生成元（src/imotech/render.py）は tags を JSON の配列で 1 行に書く。読めなければ、件数が
    // ずれた理由が分からない失敗になるので、ここで原因を名指しして落とす
    const tagsLine = raw.match(/^tags: (.*)$/m)?.[1] ?? "[]";
    let tags = [];
    try {
      tags = JSON.parse(tagsLine);
    } catch {
      fail(f, `frontmatter の tags を JSON の配列として読めない（検査の件数が合わなくなる）: ${tagsLine}`);
    }
    return { slug: f.replace(/\.md$/, ""), tags };
  });
const publishedSrcs = new Set(publishedArticles.map((a) => ogImagePath(a.slug)));
/** 一覧のページと、そこに並ぶはずの項目の数。
 *
 * **タグ別のページは公開記事のタグから数える。** dist にあるディレクトリから数えると、
 * タグ別のページがまるごと（または 1 タグ分）出なくなったときに、検査するページが減るだけで
 * 成功で終わる（M14 のレビュー 2 周目で実際に起きた）。 */
const listPages = [{ page: join(DIST, "index.html"), expected: publishedArticles.length }];
const tagsDir = join(DIST, "tags");
const publishedTags = [...new Set(publishedArticles.flatMap((a) => a.tags))];
for (const t of publishedTags) {
  const page = join(tagsDir, t, "index.html");
  if (!existsSync(page)) {
    failPage(page, `タグ「${t}」の一覧ページが無い（公開記事にこのタグがある）`);
    continue;
  }
  listPages.push({ page, expected: publishedArticles.filter((a) => a.tags.includes(t)).length });
}
// 逆向き。公開記事に無いタグのページがあれば、タグの読み取りか公開判定がずれている
if (existsSync(tagsDir)) {
  for (const t of readdirSync(tagsDir)) {
    if (!publishedTags.includes(t)) failPage(join(tagsDir, t), `公開記事に無いタグ「${t}」の一覧ページがある`);
  }
}
let thumbs = 0;
for (const { page, expected } of listPages) {
  const html = readFileSync(page, "utf8");
  // class を足しても当たるよう、空白区切りの 1 語として探す（`\b` だと entry-foo にも当たる）
  const entries = html.match(/<li class="(?:[^"]*\s)?entry(?:\s[^"]*)?"[\s\S]*?<\/li>/g) ?? [];
  // **項目の数を突き合わせる。** 部品の形が変わって 1 件も当たらなくなると、下の検査が
  // すべて空振りしたまま成功で終わる（M14 のレビューで実際に起きた）
  if (entries.length !== expected) {
    failPage(page, `一覧の項目が ${entries.length} 件（公開記事から数えると ${expected} 件のはず）`);
  }
  entries.forEach((entry, i) => {
    const link = entry.match(/<a class="[^"]*\bentry-thumb\b[^"]*"[^>]*>/)?.[0];
    const img = entry.match(/<a class="[^"]*\bentry-thumb\b[^"]*"[^>]*>\s*(<img[^>]*>)/)?.[1];
    if (!link || !img) return failPage(page, `一覧の ${i + 1} 件目にサムネイルが無い`);
    thumbs += 1;
    const src = img.match(/src="([^"]*)"/)?.[1] ?? "";
    // 公開記事の画像以外を指していれば、未公開記事の画像への参照か、壊れた参照
    if (!publishedSrcs.has(src)) failPage(page, `一覧のサムネイルが公開記事の画像でないものを指している: ${src}`);
    else if (!existsSync(join(DIST, src))) failPage(page, `一覧のサムネイルの画像が無い: ${src}`);
    if (!/width="\d+"/.test(img) || !/height="\d+"/.test(img))
      failPage(page, `一覧のサムネイルに width / height が無い（読み込み中にレイアウトがずれる）: ${src}`);
    // alt="" の画像だけのリンクは読み上げでリンク名が無くなる。タイトルのリンクがあるので外す
    if (!/aria-hidden="true"/.test(link) || !/tabindex="-1"/.test(link))
      failPage(page, `一覧の画像のリンクが読み上げ・キーボードから外れていない: ${src}`);
    const expected = i === 0 ? "eager" : "lazy";
    if (!new RegExp(`loading="${expected}"`).test(img))
      failPage(page, `一覧の ${i + 1} 件目の画像の loading が ${expected} でない: ${src}`);
    // 先頭は狭い画面で LCP になりやすいので優先して取りに行かせる。2 件目以降は優先しない
    const priority = i === 0 ? "high" : "auto";
    if (!new RegExp(`fetchpriority="${priority}"`).test(img))
      failPage(page, `一覧の ${i + 1} 件目の画像の fetchpriority が ${priority} でない: ${src}`);
  });
}

if (problems > 0) {
  console.error(`\n${problems} 件の問題を検出しました。`);
  process.exit(1);
}
console.log(`公開記事 ${checked} 件の OG 画像を確認しました（${OG_WIDTH}×${OG_HEIGHT}、og:image は絶対 URL）。`);
console.log(`一覧 ${listPages.length} ページのサムネイル ${thumbs} 件を確認しました（公開記事の画像だけを指している）。`);

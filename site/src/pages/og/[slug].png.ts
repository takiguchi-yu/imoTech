/** 記事ごとの OG 画像（アイキャッチ）。ビルド時に `dist/og/<slug>.png` として書き出される。
 *
 * 静的エンドポイント（https://docs.astro.build/en/guides/endpoints/ ）。
 * サイトは完全な静的出力なので、実行時に画像を作る場所は無い。
 */
import type { APIRoute, GetStaticPaths, InferGetStaticPropsType } from "astro";
import { publishedArticles } from "../../lib/articles";
import { renderOgPng } from "../../lib/og-render";

export const getStaticPaths = (async () => {
  // **記事ページ（articles/[...slug].astro）と同じ関数で絞る。** imo 未記入の記事の画像を
  // 作ると、ページは生成されないのに画像だけが公開され、未公開記事のタイトルが漏れる
  const articles = await publishedArticles();
  return articles.map((article) => ({ params: { slug: article.id }, props: { article } }));
}) satisfies GetStaticPaths;

type Props = InferGetStaticPropsType<typeof getStaticPaths>;

export const GET: APIRoute<Props> = async ({ props }) => {
  const d = props.article.data;
  const missing = new Set<string>();
  const png = await renderOgPng(
    { title: d.title, source: d.source, score: d.score, comments: d.comments },
    missing,
  );
  // フォントに無い字は空白で描かれる。**ビルドは止めない**（1 記事のために全記事の
  // 公開が止まるほうが害が大きい）が、どの記事の何の字が抜けたかは知らせる。
  // `::warning file=...::` は GitHub Actions の注釈の書式で、実行の概要ページに出る
  // （ログに埋もれない）。ローカルでもそのまま読める
  if (missing.size > 0) {
    console.warn(
      `::warning file=src/content/articles/${props.article.id}.md::` +
        `アイキャッチでフォントに無い字が空白になります: ${[...missing].join("")}`,
    );
  }
  return new Response(new Uint8Array(png), { headers: { "Content-Type": "image/png" } });
};

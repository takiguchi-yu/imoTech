import rss from "@astrojs/rss";
import type { APIContext } from "astro";
import { publishedArticles } from "../lib/articles";
import { scoreUnit, sourceLabel } from "../lib/sources";

export async function GET(context: APIContext) {
  const articles = await publishedArticles();
  return rss({
    title: "imoTech",
    description:
      "Hacker News や Qiita で話題になった技術記事を、元記事の要旨と議論の論調、そして運営者の imo とともに日本語で紹介します。",
    // astro.config.mjs の site。未設定なら localhost
    site: context.site ?? "http://localhost:4321",
    items: articles.map((a) => ({
      title: a.data.title,
      pubDate: a.data.publishedAt,
      link: `/articles/${a.id}/`,
      categories: a.data.tags,
      description: `${sourceLabel(a.data.source)} ${a.data.score} ${scoreUnit(a.data.source)} / ${a.data.comments} コメント — ${a.data.sourceTitle}`,
    })),
    customData: "<language>ja</language>",
  });
}

import rss from "@astrojs/rss";
import type { APIContext } from "astro";
import { publishedArticles } from "../lib/articles";
import { engagementText } from "../lib/sources";

export async function GET(context: APIContext) {
  const articles = await publishedArticles();
  return rss({
    title: "imoTech",
    description:
      "Hacker News や Qiita、GitHub、各社の公式ブログで話題になった技術記事を、元記事の要旨、議論の論調（反応がある記事）、使いどころ、そして運営者の imo とともに日本語で紹介します。",
    // astro.config.mjs の site。未設定なら localhost
    site: context.site ?? "http://localhost:4321",
    items: articles.map((a) => ({
      title: a.data.title,
      pubDate: a.data.publishedAt,
      link: `/articles/${a.id}/`,
      categories: a.data.tags,
      description: `${engagementText(a.data.source, a.data.score, a.data.comments)} — ${a.data.sourceTitle}`,
    })),
    customData: "<language>ja</language>",
  });
}

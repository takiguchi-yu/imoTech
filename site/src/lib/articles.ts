import { type CollectionEntry, getCollection } from "astro:content";
import { imoOf } from "./imo";

export { imoOf } from "./imo";

export type Article = CollectionEntry<"articles">;

export function isPublished(article: Article): boolean {
  return imoOf(article.body) !== null;
}

/** imo が書かれた記事だけを、新しい順に返す。 */
export async function publishedArticles(): Promise<Article[]> {
  const all = await getCollection("articles");
  return all
    .filter(isPublished)
    .sort((a, b) => b.data.publishedAt.valueOf() - a.data.publishedAt.valueOf());
}

export function allTags(articles: Article[]): string[] {
  return [...new Set(articles.flatMap((a) => a.data.tags))].sort();
}

export function formatDate(d: Date): string {
  return d.toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone: "Asia/Tokyo",
  });
}

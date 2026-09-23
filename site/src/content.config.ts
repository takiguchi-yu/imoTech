import { glob } from "astro/loaders";
import { defineCollection } from "astro:content";
// astro:content の z は非推奨。Astro が同梱する zod を直接使う
import { z } from "astro/zod";

// imo の公開判定と定数は lib/imo.ts が唯一の定義元。ここからも参照できるようにする
export { IMO_PLACEHOLDER, IMO_SENTINEL, imoOf } from "./lib/imo";

const articles = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/articles" }),
  schema: z.object({
    title: z.string(),
    publishedAt: z.coerce.date(),
    sourceUrl: z.string().url(),
    sourceTitle: z.string(),
    // 話題を拾ったソース。表示の出し分けに使う（lib/sources.ts の SOURCE_LABELS）
    source: z.string().default("hackernews"),
    // 議論が付いている場所。Hacker News はスレッド、Zenn や Qiita は記事ページ自身
    discussionUrl: z.string().url(),
    hatenaUrl: z.string().url(),
    score: z.number().int(),
    comments: z.number().int(),
    tags: z.array(z.string()).default([]),
    model: z.string(),
    generatedAt: z.coerce.date(),
  }),
});

export const collections = { articles };

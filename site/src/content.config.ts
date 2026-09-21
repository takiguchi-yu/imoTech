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
    hnUrl: z.string().url(),
    hatenaUrl: z.string().url(),
    hnScore: z.number().int(),
    hnComments: z.number().int(),
    tags: z.array(z.string()).default([]),
    model: z.string(),
    generatedAt: z.coerce.date(),
  }),
});

export const collections = { articles };

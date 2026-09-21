// @ts-check
import sitemap from "@astrojs/sitemap";
import { defineConfig } from "astro/config";

// ドメインは未確定（M0 の残タスク）。確定するまでは localhost で通す。
// sitemap と RSS が絶対 URL を必要とするため、必ず何かを入れる必要がある。
const LOCAL = "http://localhost:4321";
const site = process.env.SITE_URL || LOCAL;

// CI や本番ビルドで SITE_URL を入れ忘れると、localhost の URL が sitemap と RSS に
// 焼き込まれたまま公開される。ビルドは成功してしまうので気づけない。ここで落とす。
//
// 判定に NODE_ENV は使わない。astro build が自ら NODE_ENV=production を立てるため、
// ローカルの `npm run build` まで落ちてしまう。CI 環境変数だけを見る。
if (!process.env.SITE_URL && process.env.CI) {
  throw new Error(
    "SITE_URL が未設定です。CI や本番ビルドでは必ず指定してください" +
      "（未指定だと sitemap と RSS に localhost の URL が入ります）。" +
      "例: SITE_URL=https://example.com npm run build",
  );
}

export default defineConfig({
  site,
  integrations: [sitemap()],
});

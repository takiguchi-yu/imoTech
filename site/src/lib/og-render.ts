/** OG 画像（アイキャッチ）を PNG に描く。
 *
 * **Satori（要素 → SVG）+ Resvg（SVG → PNG）**の組み合わせ。satori の作者側の
 * 参照実装 `@vercel/og` と同じ構成（https://vercel.com/docs/og-image-generation ）。
 *
 * ビルド時にだけ動く（サイトは完全な静的出力で、実行時に画像を作る場所が無い）。
 * レイアウトは `og.ts` が持ち、ここはフォントの読み込みと描画だけを持つ。
 */
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { Resvg } from "@resvg/resvg-js";
import satori from "satori";
import {
  OG_HEIGHT,
  OG_WIDTH,
  type OgCard,
  type OgNode,
  TITLE_LINE_HEIGHT,
  TITLE_WIDTH,
  chooseTitleFontSize,
  ogCardTree,
  titleNode,
} from "./og.ts";

/** 同梱の日本語フォント（出典とライセンスは `site/fonts/README.md`）。
 *
 * **`import.meta.url` からは辿らない。** Astro はビルド時にこのファイルを別の場所へ
 * まとめ直すので、相対パスが `dist/` の中を指してしまう。ビルドもテストも `site/` で
 * 実行する（`.github/workflows/ci.yml` の `working-directory: site`）ので、そこを基準にする。 */
const FONT_PATH = resolve(process.cwd(), "fonts/NotoSansJP-Bold.otf");

let fontData: Buffer | undefined;

function loadFont(): Buffer {
  if (fontData) return fontData;
  if (!existsSync(FONT_PATH)) {
    throw new Error(
      `OG 画像用のフォントが見つかりません: ${FONT_PATH}` +
        "（site/ で実行しているか、site/fonts/ にフォントがあるかを確認してください）",
    );
  }
  // 1 回だけ読む。記事の数だけ 4.6 MB を読み直さない
  fontData = readFileSync(FONT_PATH);
  return fontData;
}

/** 描画に失敗した文字（フォントに無い字）を集める先。テストが見る。 */
export type MissingGlyphs = Set<string>;

type SatoriElement = Parameters<typeof satori>[0];

function fonts() {
  return [{ name: "Noto Sans JP", data: loadFont(), weight: 700 as const, style: "normal" as const }];
}

/** タイトルを実際にレイアウトして、何行になるかを数える。
 *
 * **高さを渡さずに組むと、satori は中身の高さの SVG を返す。** それを 1 行の高さで割る。
 * カードと同じ要素（`titleNode`）を省略なしで組むので、カードでの行数と一致する。
 * 1 回 1〜2 ms で、カードの描画（約 300 ms）に比べて無視できる。 */
export async function measureTitleLines(title: string, size: number): Promise<number> {
  const svg = await satori(titleNode(title, size, { clamp: false }) as unknown as SatoriElement, {
    width: TITLE_WIDTH,
    fonts: fonts(),
    // 字の欠けは本番の描画で拾う。ここで拾うと同じ字を何度も数える
    loadAdditionalAsset: async () => [],
  });
  const height = Number(svg.match(/height="([\d.]+)"/)?.[1]);
  if (!Number.isFinite(height) || height <= 0) {
    throw new Error(`タイトルの行数を測れませんでした（SVG の高さが読めない）: ${title}`);
  }
  return Math.round(height / (size * TITLE_LINE_HEIGHT));
}

/** カードの要素の木を組む。字の大きさは実測で選ぶ。 */
export async function ogCardTreeFor(card: OgCard): Promise<OgNode> {
  const size = await chooseTitleFontSize((s) => measureTitleLines(card.title, s));
  return ogCardTree(card, size);
}

/** カードを SVG に描く。**フォントに無い字の検出はここで起きる**ので、
 * 字の欠けだけを見たいテストは PNG 化（時間の大半）を飛ばしてこちらを呼ぶ。 */
export async function renderOgSvg(card: OgCard, missing?: MissingGlyphs): Promise<string> {
  return satori((await ogCardTreeFor(card)) as unknown as SatoriElement, {
    width: OG_WIDTH,
    height: OG_HEIGHT,
    fonts: fonts(),
    // フォントに無い字があると satori はここを呼ぶ。**黙って空白にされると
    // タイトルの字が抜けたまま公開される**ので、呼び出し側が検知できるよう記録する
    loadAdditionalAsset: async (_code, segment) => {
      // satori は空文字の区切りで呼ぶことがある。字ではないので数えない
      if (segment) missing?.add(segment);
      return [];
    },
  });
}

/** カードを PNG に描く。 */
export async function renderOgPng(card: OgCard, missing?: MissingGlyphs): Promise<Buffer> {
  const svg = await renderOgSvg(card, missing);
  return new Resvg(svg, { fitTo: { mode: "width", value: OG_WIDTH } }).render().asPng();
}

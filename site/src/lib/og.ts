/** OG 画像（アイキャッチ）のレイアウト。
 *
 * **ここは値からカードの形を組むだけで、描画はしない**（フォントの読み込みと PNG 化は
 * `og-render.ts`）。描画には native 依存と 4.6 MB のフォントが要るので、
 * レイアウトの判断（タイトルの大きさ、注目度の書き方）はそれ抜きでテストできるようにしてある。
 *
 * 載せるのは サイト名 + 記事タイトル + ソース名と注目度 の 3 つ。
 * 元記事の画像は使わない — 他人の画像の無断転載になる（はてブの OGP プレビューを
 * 「転載になる」として避けた判断と同じ理由）。
 */
import { engagementText } from "./sources.ts";

/** 推奨サイズ。1.91:1 に近いほど、フィードで切り抜かれずに全体が出る
 * （https://developers.facebook.com/docs/sharing/webmasters/images ）。 */
export const OG_WIDTH = 1200;
export const OG_HEIGHT = 630;

/** サイトのアクセント色（`layouts/Base.astro` の `--accent` のライト側）。
 * satori は 3 桁の略記を保証していないので 6 桁で書く。 */
const ACCENT = "#00aa55";
const FG = "#1a1a1a";
const MUTED = "#666666";

/** カードの左右の余白。タイトルが使える幅はここから決まる。 */
const PADDING_X = 72;
/** タイトルが使える幅。行数を実測するときもこの幅で組む。 */
export const TITLE_WIDTH = OG_WIDTH - PADDING_X * 2;
/** タイトルの行間（字の大きさに対する倍率）。行数の実測はこれで高さを割る。 */
export const TITLE_LINE_HEIGHT = 1.4;

/** タイトルの字の大きさの候補（大きい順）。 */
export const TITLE_SIZES = [64, 56, 48, 42] as const;
/** 大きい字で収めたい行数。これを超えるなら字を小さくする。 */
export const TITLE_MAX_LINES = 3;
/** どの大きさでも収まらないときの行数の上限。超えた分は省略記号になる。 */
const TITLE_CLAMP_LINES = 4;

/** カードに載せる値。記事のフロントマターから作る。 */
export type OgCard = {
  title: string;
  /** ソースの名前（`hackernews` / `qiita`）。表示名への変換は `sources.ts` */
  source: string;
  score: number;
  comments: number;
};

/** satori に渡す要素。React に依存しないよう、素のオブジェクトで組む。 */
export type OgNode = {
  type: string;
  props: { style?: Record<string, string | number>; children?: string | OgNode | OgNode[]; lang?: string };
};

/** 記事の OG 画像の公開パス。記事ページ（og:image とアイキャッチ）と検査
 * （`scripts/check-og.mjs`）がここを使う。
 *
 * **画像を書き出す側はこの関数を使えない** — 静的エンドポイントの出力先はファイルの
 * 置き場所（`pages/og/[slug].png.ts`）で決まるため。両者がずれると og:image が 404 を
 * 指すが、その場合は `check-og.mjs` が「画像が無い」として落とす。 */
export function ogImagePath(slug: string): string {
  return `/og/${slug}.png`;
}

/** 注目度の 1 行。記事ページの見出し下（`[...slug].astro`）と同じ書き方に揃える。 */
export function metaLine(card: Pick<OgCard, "source" | "score" | "comments">): string {
  return engagementText(card.source, card.score, card.comments, " ・ ");
}

/** タイトルの字の大きさを選ぶ。**収まる範囲でいちばん大きい字**にする。
 *
 * 行数は**見積もらず、実際にレイアウトして数える**（`measureLines` は描画側が渡す —
 * フォントとレイアウトの仕組みはここに持ち込まない）。以前は字数から見積もっていたが、
 * 1 行に入る字数の端数や「英単語は途中で折り返さない」ことで実際の行数とずれ、
 * 既存記事の 1 本（52 字）が 3 行の見込みで 4 行になっていた。
 *
 * 記事タイトルは幅 40 まで（全角 1・半角 0.5）の指示だが（`src/imotech/prompts/compose.md`）、超えることがあり、
 * 2026-09-23 より前の記事は 40〜60 字の旧形式。
 * 小さい字で押し込むより、読める大きさで 3 行に収めるほうを優先し、
 * 収まらなければ最小の字で 4 行まで出して残りは省略する。 */
export async function chooseTitleFontSize(
  measureLines: (size: number) => Promise<number>,
): Promise<number> {
  for (const size of TITLE_SIZES) {
    if ((await measureLines(size)) <= TITLE_MAX_LINES) return size;
  }
  return TITLE_SIZES[TITLE_SIZES.length - 1];
}

/** タイトルの要素。**カードも行数の実測もこれを使う**（見た目がずれると実測が意味を失う）。
 *
 * `clamp` はカードのときだけ付ける。実測では省略せずに組み、本当の行数を得る。 */
export function titleNode(title: string, size: number, { clamp }: { clamp: boolean }): OgNode {
  const style: Record<string, string | number> = {
    width: TITLE_WIDTH,
    fontSize: size,
    lineHeight: TITLE_LINE_HEIGHT,
    fontFamily: "Noto Sans JP",
    // 折り返せない長い英単語や URL を、はみ出さずに途中で折る。**収まらないときだけ**折るので、
    // 普通の英単語は崩れない（`break-all` だとどの英単語も字の途中で切れる）
    wordBreak: "break-word",
    display: clamp ? "block" : "flex",
  };
  if (clamp) style.lineClamp = TITLE_CLAMP_LINES;
  return { type: "div", props: { lang: "ja-JP", style, children: title } };
}

/** カードの要素の木を組む。字の大きさは `chooseTitleFontSize` で選んだものを渡す。 */
export function ogCardTree(card: OgCard, titleSize: number): OgNode {
  return {
    type: "div",
    props: {
      // 日本語の禁則（行頭の句読点など）を効かせる
      lang: "ja-JP",
      style: {
        width: OG_WIDTH,
        height: OG_HEIGHT,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        padding: `56px ${PADDING_X}px 72px`,
        background: "#ffffff",
        color: FG,
        fontFamily: "Noto Sans JP",
        position: "relative",
      },
      children: [
        { type: "div", props: { style: { fontSize: 34, color: ACCENT }, children: "imoTech" } },
        titleNode(card.title, titleSize, { clamp: true }),
        { type: "div", props: { style: { fontSize: 30, color: MUTED }, children: metaLine(card) } },
        // 下端の帯。サイトのアクセント色で、タイムラインでも imoTech の記事だと分かるようにする
        {
          type: "div",
          props: {
            style: {
              position: "absolute",
              left: 0,
              bottom: 0,
              width: OG_WIDTH,
              height: 16,
              background: ACCENT,
            },
          },
        },
      ],
    },
  };
}

/**
 * imo の公開判定。astro:content に依存しないので単体テストできる。
 *
 * 定数は site/src/content.config.ts と src/imotech/render.py の 3 箇所にあり、
 * ずれると「imo 未記入の記事が公開される」。tests/test_render.py で突合している。
 */
export const IMO_PLACEHOLDER = "<!-- imo:";
export const IMO_SENTINEL = "このコメント行を消すまで";

// \s は改行も含むので [ \t] に限定する。Python 側（render.py の _IMO_HEADING_RE）と揃える
export const IMO_HEADING = /^##[ \t]+imo[ \t]*$/m;
const NEXT_HEADING = /^##\s/m;
const HTML_COMMENT = /<!--[\s\S]*?-->/g;

/**
 * 目に見えない文字。`trim()` では落ちない。
 *
 * Cf（書式文字。ゼロ幅スペース U+200B、ゼロ幅非結合子 U+200C、BOM U+FEFF など）、
 * Cc（制御文字）、Z*（空白区切り。全角空白 U+3000 を含む）が対象。
 *
 * 貼り付け事故で不可視文字だけが imo に入ると、`trim()` を通り抜けて
 * 「所感が実質空の記事」が公開される。Python 側（render.py の meaningful_text）と
 * 同じ規則にしてある。
 */
const MEANINGLESS = /[\p{Cf}\p{Cc}\p{Z}\s]/gu;

/** 目に見える文字だけを残す。imo が実質空かどうかの判定に使う。 */
export function meaningfulText(text: string): string {
  return text.replace(MEANINGLESS, "");
}

/**
 * 本文から imo の中身を取り出す。書かれていなければ null。
 *
 * **許可リスト方式。** 「未記入の証拠があれば隠す」ではなく「記入の証拠があれば出す」。
 * 前者だと、本文が取れない・見出しが無い・プレースホルダの表記が違う、といった
 * ケースがすべて公開側に倒れる。所感を書いていない記事の公開は取り返しがつかない。
 */
export function imoOf(body: string | undefined | null): string | null {
  if (typeof body !== "string") return null;

  const heading = IMO_HEADING.exec(body);
  if (!heading) return null;

  const after = body.slice(heading.index + heading[0].length);
  const next = NEXT_HEADING.exec(after);
  const section = next ? after.slice(0, next.index) : after;

  if (section.includes(IMO_PLACEHOLDER) || section.includes(IMO_SENTINEL)) return null;

  const text = section.replace(HTML_COMMENT, "").trim();
  // 不可視文字だけの imo を公開しない
  return meaningfulText(text).length > 0 ? text : null;
}

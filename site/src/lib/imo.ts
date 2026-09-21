/**
 * imo の公開判定。astro:content に依存しないので単体テストできる。
 *
 * 定数は site/src/content.config.ts と src/imotech/render.py の 3 箇所にあり、
 * ずれると「imo 未記入の記事が公開される」。tests/test_render.py で突合している。
 */
export const IMO_PLACEHOLDER = "<!-- imo:";
export const IMO_SENTINEL = "このコメント行を消すまで";

const IMO_HEADING = /^##\s+imo\s*$/m;
const NEXT_HEADING = /^##\s/m;
const HTML_COMMENT = /<!--[\s\S]*?-->/g;

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
  return text.length > 0 ? text : null;
}

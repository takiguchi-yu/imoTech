/** 話題を拾ったソースの表示名。
 *
 * Python 側（`src/imotech/sources/registry.py`）の名前と対応する。
 * 知らない名前が来たらそのまま出す（新しいソースを足しても表示が壊れない）。
 */
const SOURCE_LABELS: Record<string, string> = {
  hackernews: "Hacker News",
  qiita: "Qiita",
  zenn: "Zenn",
  devto: "dev.to",
};

export function sourceLabel(source: string): string {
  return SOURCE_LABELS[source] ?? source;
}

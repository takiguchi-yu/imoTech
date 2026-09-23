/** 話題を拾ったソースの表示名と、注目度の単位。
 *
 * Python 側（`src/imotech/sources/registry.py`）の名前と対応する。
 * **ソースを足したらここにも 1 行足す**（無くても壊れないが、生の名前と
 * "points" が出るので体裁が崩れる）。
 */
type SourceMeta = {
  /** 表示名 */
  label: string;
  /** 注目度の呼び名。Hacker News は points、Qiita は LGTM、Zenn はいいね */
  scoreUnit: string;
};

const SOURCES: Record<string, SourceMeta> = {
  hackernews: { label: "Hacker News", scoreUnit: "points" },
  qiita: { label: "Qiita", scoreUnit: "LGTM" },
  zenn: { label: "Zenn", scoreUnit: "いいね" },
  devto: { label: "dev.to", scoreUnit: "reactions" },
};

export function sourceLabel(source: string): string {
  return SOURCES[source]?.label ?? source;
}

export function scoreUnit(source: string): string {
  return SOURCES[source]?.scoreUnit ?? "points";
}

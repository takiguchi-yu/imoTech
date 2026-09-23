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

/** 議論の場所が元記事とは別にあるか。
 *
 * Hacker News はスレッドが別 URL なので真。Qiita や Zenn のような
 * **記事プラットフォームでは議論の場所が記事ページ自身**なので偽になり、
 * 同じ URL へのリンクを 2 本出さずに済む。
 *
 * URL の比較で決めるのは、ソース名で分岐すると新しいソースを足すたびに
 * ここを直す必要が出るため。値を見れば判断できる。
 */
export function hasSeparateDiscussion(article: {
  sourceUrl: string;
  discussionUrl: string;
}): boolean {
  return Boolean(article.discussionUrl) && article.discussionUrl !== article.sourceUrl;
}

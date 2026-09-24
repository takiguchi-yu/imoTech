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
  /** 注目度を持たないソース（公式ブログ）。表示名だけを出す */
  noEngagement?: boolean;
  /** コメント数を持たないソース（GitHub）。注目度だけを出す */
  noComments?: boolean;
};

const SOURCES: Record<string, SourceMeta> = {
  hackernews: { label: "Hacker News", scoreUnit: "points" },
  qiita: { label: "Qiita", scoreUnit: "LGTM" },
  zenn: { label: "Zenn", scoreUnit: "いいね" },
  devto: { label: "dev.to", scoreUnit: "reactions" },
  github: { label: "GitHub", scoreUnit: "stars", noComments: true },
  "cloudflare-blog": { label: "Cloudflare Blog", scoreUnit: "", noEngagement: true },
  "vercel-blog": { label: "Vercel Blog", scoreUnit: "", noEngagement: true },
};

export function sourceLabel(source: string): string {
  return SOURCES[source]?.label ?? source;
}

export function scoreUnit(source: string): string {
  return SOURCES[source]?.scoreUnit ?? "points";
}

/** 「ソース名 注目度 / コメント数」の 1 行。記事ページ・一覧・RSS・アイキャッチで同じ書き方にする。
 *
 * 注目度を持たないソース（公式ブログ）は「0 points / 0 コメント」と出すと、話題にならなかった
 * ように読めるので、表示名だけにする。GitHub はコメントを持たないので stars だけ。 */
export function engagementText(
  source: string,
  score: number,
  comments: number,
  /** 表示名と注目度のあいだ。アイキャッチは「 ・ 」で区切る */
  separator = " ",
): string {
  const meta = SOURCES[source];
  const label = sourceLabel(source);
  if (meta?.noEngagement) return label;
  if (meta?.noComments) return `${label}${separator}${score} ${scoreUnit(source)}`;
  return `${label}${separator}${score} ${scoreUnit(source)} / ${comments} コメント`;
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

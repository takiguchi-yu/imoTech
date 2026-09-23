"""反応から投稿者を特定しうる情報を落とす。

Gemini の無料枠は入力が学習に使われ、人間のレビュアーが読む
（"Do not submit sensitive, confidential, or personal information to the Unpaid Services."）。
そのため LLM に渡す前に必ずここを通す。llm.py は AnonymizedReaction しか受け取らない。
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from html.parser import HTMLParser

from .models import AnonymizedReaction, Reaction

PLACEHOLDER = "[ユーザー名]"
EMAIL_PLACEHOLDER = "[メールアドレス]"

# 行頭や空白のあとの @handle。foo@bar.com のようなメールには当たらないよう先読みで除く。
# CSS の @media や Python のデコレータに誤爆しうるが、PII を残すより誤爆を取る。
_MENTION = re.compile(r"(?<![\w.])@([A-Za-z][A-Za-z0-9_-]{1,29})\b")

# 投稿者のプロフィールページ。リンクテキストとして本文に現れ、ハンドル名がそのまま残る。
# スレッド参加者以外のハンドルも載るため、handles 集合による伏せ字では捕まらない。
#
# **URL の形はソースごとに違う**ので、パターンはソース側が持つ
# （`sources/hackernews.py` の `PROFILE_URL_RE`）。ここは受け取って適用するだけ。

# URL 全般。ハンドル名の伏せ字が URL の一部に誤爆して壊すのを防ぐため、
# 伏せ字をかける前に退避しておく。実データで ?ref=newsletter.com が
# ?ref=[ユーザー名].com に化ける事故が観測された。
_URL = re.compile(r"https?://\S+", re.IGNORECASE)

# ユーザー名を含む URL は、リンクごと伏せる。URL を温存すると PII が残るため。
_URL_WITH_HANDLE = re.compile(r"https?://\S*@\S*", re.IGNORECASE)
LINK_PLACEHOLDER = "[リンク]"

# 本文に直接書かれたメールアドレス。ハンドル名と並ぶ典型的な PII。
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# 実在ハンドルを本文から消すときの最小長。短すぎる語を消すと文章が壊れるため。
_MIN_HANDLE_LEN = 4

# 【既知の限界】英単語と同じ綴りのハンドル、および 4 文字未満のハンドルは伏せない。
# 文章中に素の語として現れたとき、それが人物への言及なのか普通の単語なのかは
# 区別できず、伏せると文章が壊れる（下記の what の事故）。伏せないままでも、
# 読み手にも LLM にも人物への言及とは判別できないため、実害は小さいと判断した。
# @ 付きの言及とプロフィール URL は綴りに関わらず伏せる。
# 英単語と同じ綴りのハンドルは伏せない。
# 実データで、what というハンドルの投稿者がいたために英文中の "what" が全て伏せ字になり、
# 文章が読めなくなる事故が起きた。誤検出は記事の質を直接壊すので、頻出語は除外する。
# ここに無い語と衝突したハンドルは伏せられるが、その場合の劣化は 1 語にとどまる。
_COMMON_WORDS = frozenset(
    """
    about above actually after again against all also always another answer anyone
    around away back bad because been before being belief best better between both
    call came case change check clear code come coming common could data days
    dead deal detail different does doing done down draw each early else even ever
    every exactly example fact fair fast feel felt file find first form free from
    full function game general give given goes going gone good great group guess hand
    hard have head help here high hold home hope house however human idea instead
    into issue itself just keep kind knew know known large last late later learn
    least leave left less life like line list little live long look lost love made
    main make many mark match matter mean might mind mine miss more most move much
    must name near need never news next nice night none noone note nothing
    number often once only open order other over page part past people perhaps
    place plain play please point post power pretty probably problem process
    public quite rather read real really reason right room rule said same save
    school seem seen sense server service several shall short should show side
    similar simple since site size slow small some soon sort sound space speak
    stand start state still stop story such sure take talk team tell test than
    that them then there these they thing think this those though three through
    time today together told took top true turn type under until upon used
    user using very view want watch water well went were what when where which
    while white whole will wish with within without word work world would wrong
    year your
    agent async await base build cache class client cloud core count debug
    default delete deploy error event false field float index input java json
    linux local login logic loop main model module mount node null object output
    parse patch print proxy query queue reset root route rust scale schema scope
    script shell stack stream string style table token trace tree unix update
    value vector write
    """.split()
)


class _TextExtractor(HTMLParser):
    """HN のコメント HTML からテキストだけを取り出す。

    HN は <p>（閉じタグなし）、<a href>、<i>、<code>、<pre> を使う。
    <a> はリンクテキストを残す（URL が二重に出るのを避ける）。
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in ("p", "br", "pre"):
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("p", "pre"):
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def text(self) -> str:
        return "".join(self._parts)


def strip_html(raw: str) -> str:
    """HN のコメント HTML を平文にする。"""
    p = _TextExtractor()
    p.feed(raw)
    p.close()
    # HTMLParser(convert_charrefs=True) が既に実体参照を解決しているので、
    # ここで html.unescape を重ねない。重ねると利用者が書いた &lt;script&gt; が
    # <script> に化け、コード片の引用が別物になる。
    text = p.text()
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def scrub(text: str, handles: frozenset[str], profile_url_res: Sequence[re.Pattern[str]]) -> str:
    """本文から PII を伏せる。

    順序に意味がある。
    1. 投稿者のプロフィール URL — スレッド外のハンドルも載るので最初に潰す
       （URL の形はソースごとに違うので、パターンは呼び出し側が渡す）
    2. ユーザー名を含む URL — リンクごと伏せる（温存すると PII が残る）
    3. 残った URL を退避 — ハンドル名の伏せ字が URL を壊すのを防ぐ
    4. メールアドレス — @メンションの正規表現より先に当てる
    5. @メンション
    6. スレッドに実在するハンドル名
    7. URL を戻す
    """
    for pattern in profile_url_res:
        text = pattern.sub(PLACEHOLDER, text)
    text = _URL_WITH_HANDLE.sub(LINK_PLACEHOLDER, text)

    stash: list[str] = []

    def _park(m: re.Match[str]) -> str:
        stash.append(m.group(0))
        return f"\x00U{len(stash) - 1}\x00"

    text = _URL.sub(_park, text)

    text = _EMAIL.sub(EMAIL_PLACEHOLDER, text)
    text = _MENTION.sub(PLACEHOLDER, text)
    for h in sorted(handles, key=len, reverse=True):
        if len(h) < _MIN_HANDLE_LEN or h.lower() in _COMMON_WORDS:
            continue
        # 文頭で先頭大文字にして言及するのは普通に起きるので大小を無視する
        text = re.sub(rf"\b{re.escape(h)}\b", PLACEHOLDER, text, flags=re.IGNORECASE)

    for i, u in enumerate(stash):
        text = text.replace(f"\x00U{i}\x00", _scrub_in_url(u, handles))
    return text


def _scrub_in_url(url: str, handles: frozenset[str]) -> str:
    """URL の中のハンドル名を伏せる。

    URL 全体を伏せ字の対象から外すと github.com/<handle>/repo のような形で
    投稿者名が残る。かといって素朴に部分一致で置換すると ?ref=newsletter.com が
    ?ref=[ユーザー名].com に化ける。

    そこで「パス区切り・クエリ区切りで完全に 1 区画を成している」ときだけ伏せる。
    ホスト名の先頭ラベルが投稿者名と一致する場合も伏せる。本人の個人ドメイン
    （https://<handle>.ca/... など）であることがほとんどで、PII の信号が強い。

    - https://github.com/DanMcInerney/repo → パス区画なので伏せる
    - https://srcreigh.ca/posts/x          → 先頭ホストラベルなので伏せる
    - https://e.com/p?ref=newsletter.com   → クエリ値の一部なので伏せない

    **パス区画には短さ・頻出語の除外を当てない。** `_MIN_HANDLE_LEN` と `_COMMON_WORDS` は
    「本文に素の語として現れたとき、人物への言及か普通の単語か区別できない」ための規則で、
    URL のパス区画にはその曖昧さが無い。当ててしまうと、記事プラットフォームで
    `qiita.com/abc/items/<id>` のように **URL 自体が著者を指す形**のときに伏せ字が抜ける
    （Qiita には 3 文字の user_id も、英単語と同じ綴りの user_id も実在する）。
    ホスト名側は誤爆しうる（`what.com` が人物とは限らない）ので、従来どおり除外を当てる。
    """
    for h in sorted(handles, key=len, reverse=True):
        esc = re.escape(h)
        # パス・クエリの 1 区画。区切り文字に挟まれていて曖昧さが無いので、
        # 短いハンドル・英単語と同じ綴りのハンドルもここでは伏せる
        url = re.sub(rf"(?<=[/=?&]){esc}(?=[/?&#]|$)", PLACEHOLDER, url, flags=re.IGNORECASE)
        if len(h) < _MIN_HANDLE_LEN or h.lower() in _COMMON_WORDS:
            continue
        # ホスト名の先頭ラベル（www. の有無を許す）。ここは普通のドメインに誤爆しうる
        url = re.sub(rf"(?<=://){esc}(?=\.)", PLACEHOLDER, url, flags=re.IGNORECASE)
        url = re.sub(rf"(?<=://www\.){esc}(?=\.)", PLACEHOLDER, url, flags=re.IGNORECASE)
    return url


def handles_of(reactions: list[Reaction], extra_handles: frozenset[str]) -> frozenset[str]:
    """伏せ字の対象になる投稿者ハンドルの集合。

    スレッドの投稿者に加えて `extra_handles` を混ぜる。**記事の著者は反応に
    現れないことがある**（Qiita で著者がコメントしていない場合など）ので、
    呼び出し側が `Story.author` を渡す。
    """
    return frozenset(r.author for r in reactions if r.author) | {h for h in extra_handles if h}


def scrub_url(url: str, reactions: list[Reaction], extra_handles: frozenset[str]) -> str:
    """元記事の URL を匿名化する。

    ブログ主が自分の記事を HN に投稿してコメントもする、というのはよくある。
    その場合ドメイン名が投稿者ハンドルと一致し、URL をそのまま渡すと
    プロンプトに投稿者名が載る（実データで buchodi.com / buchodi を検出した）。

    **記事プラットフォームでは URL そのものに著者名が入る**（Qiita の
    `qiita.com/<user_id>/items/<id>`）。この場合、著者が 1 度もコメントして
    いなくても伏せる必要があるため、`extra_handles` に `Story.author` を渡す。
    **既定値を置いていない**のは、渡し忘れが静かに PII を残すため。
    """
    return _scrub_in_url(url, handles_of(reactions, extra_handles))


def scrub_title(
    title: str,
    reactions: list[Reaction],
    profile_url_res: Sequence[re.Pattern[str]],
    extra_handles: frozenset[str],
) -> str:
    """元記事のタイトルを匿名化する。

    タイトルは公開された見出しなので、**スレッド参加者のハンドル**との衝突で文章を
    壊すほうが害が大きい。そちらは伏せず、メールアドレス・@メンション・
    プロフィール URL だけを伏せる。

    一方 `extra_handles`（記事の著者）は伏せる。記事プラットフォームでは著者が
    自分の ID をタイトルに書くことがあり、そこは衝突ではなく本人への言及である。
    """
    return scrub(title, frozenset(h for h in extra_handles if h), profile_url_res)


def anonymize(
    reactions: list[Reaction],
    *,
    limit: int,
    profile_url_res: Sequence[re.Pattern[str]],
    extra_handles: frozenset[str],
) -> list[AnonymizedReaction]:
    """反応を匿名化し、議論を呼んだ順に limit 件まで絞る。

    HN の API はコメント単位の score を返さないため、重みの手がかりは reply_count と
    depth しかない。返信の多いもの・浅いものを優先し、選んだあとは元の並び順に戻して
    議論の流れが読める形で渡す。

    整形で空になった反応は limit を数える前に落とす。あとから落とすとラベルが
    C1, C3, ... と飛び、limit 件に満たない件数しか返らない。
    """
    handles = handles_of(reactions, extra_handles)

    cleaned: list[tuple[int, Reaction, str]] = []
    for i, r in enumerate(reactions):
        text = scrub(strip_html(r.text), handles, profile_url_res)
        if text:
            cleaned.append((i, r, text))

    picked = sorted(cleaned, key=lambda t: (-t[1].reply_count, t[1].depth, t[0]))[:limit]
    picked.sort(key=lambda t: t[0])

    return [
        AnonymizedReaction(
            label=f"C{n}",
            text=text,
            depth=r.depth,
            reply_count=r.reply_count,
        )
        for n, (_, r, text) in enumerate(picked, 1)
    ]

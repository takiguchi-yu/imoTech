"""Hacker News クライアントのテスト。

ネットワークは httpx.MockTransport で差し替える。チケットに明記された
「url が null の story を除外」「text が null をスキップ」「5xx で 3 回リトライ」
はここで担保する。
"""

import httpx
import pytest

from imotech.models import SourceRef
from imotech.sources import ReactionSource, StoryFeed
from imotech.sources.hackernews import MAX_COMMENT_DEPTH, HackerNews

NOW_I = 1789900000


def _hit(oid, url="https://e.com/a", points=120, comments=40):
    return {
        "objectID": str(oid),
        "url": url,
        "title": f"title {oid}",
        "points": points,
        "num_comments": comments,
        "created_at_i": NOW_I,
    }


def _client(handler):
    return HackerNews(transport=httpx.MockTransport(handler))


def test_Protocolを満たす():
    hn = _client(lambda r: httpx.Response(200, json={"hits": [], "nbPages": 1}))
    assert isinstance(hn, StoryFeed)
    assert isinstance(hn, ReactionSource)
    hn.close()


def test_urlがnullのstoryは除外される():
    # Ask HN などは元記事が無いので記事化できない
    payload = {"hits": [_hit(1), {**_hit(2), "url": None}, {**_hit(3), "url": ""}], "nbPages": 1}
    with _client(lambda r: httpx.Response(200, json=payload)) as hn:
        got = hn.fetch_stories()
    assert [s.ref.id for s in got] == ["1"]


def test_created_atが欠けたstoryは除外される():
    payload = {"hits": [{**_hit(1), "created_at_i": None}], "nbPages": 1}
    with _client(lambda r: httpx.Response(200, json=payload)) as hn:
        assert hn.fetch_stories() == []


def test_複数ページを追う():
    # 1 ページで打ち切ると条件に合う話題を取りこぼす（実測で 89 件中 39 件を落としていた）
    seen = []

    def handler(request):
        page = int(dict(request.url.params).get("page", 0))
        seen.append(page)
        return httpx.Response(200, json={"hits": [_hit(page * 10)], "nbPages": 3})

    with _client(handler) as hn:
        got = hn.fetch_stories(limit=1)
    assert seen == [0, 1, 2]
    assert len(got) == 3


def test_max_pagesで打ち切る():
    def handler(request):
        return httpx.Response(200, json={"hits": [_hit(1)], "nbPages": 999})

    with _client(handler) as hn:
        got = hn.fetch_stories(max_pages=2)
    assert len(got) == 2


def test_5xxは3回リトライして諦める(monkeypatch):
    monkeypatch.setattr("imotech.sources.hackernews.time.sleep", lambda _: None)
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(503)

    with _client(handler) as hn:
        assert hn.fetch_stories() == []
    assert len(calls) == 3


def test_5xxのあと成功すれば結果を返す(monkeypatch):
    monkeypatch.setattr("imotech.sources.hackernews.time.sleep", lambda _: None)
    state = {"n": 0}

    def handler(request):
        state["n"] += 1
        if state["n"] == 1:
            return httpx.Response(500)
        return httpx.Response(200, json={"hits": [_hit(7)], "nbPages": 1})

    with _client(handler) as hn:
        got = hn.fetch_stories()
    assert [s.ref.id for s in got] == ["7"]


# --- コメント木 -----------------------------------------------------------


def _item(children, points=300):
    return {
        "id": 1,
        "url": "https://e.com/a",
        "title": "t",
        "points": points,
        "created_at_i": NOW_I,
        "children": children,
    }


def _c(cid, text="hello", children=None):
    return {"id": cid, "author": f"u{cid}", "text": text, "children": children or []}


def test_削除済みコメントはスキップする():
    payload = _item([_c(1), {**_c(2), "text": None}, _c(3)])
    with _client(lambda r: httpx.Response(200, json=payload)) as hn:
        story, reactions = hn.fetch_reactions(SourceRef("hackernews", "1"))
    assert [r.comment_id for r in reactions] == [1, 3]
    # 削除済みは num_comments にも数えない
    assert story.engagement.comments == 2


def test_階層と返信数が取れる():
    payload = _item([_c(1, children=[_c(2), _c(3)])])
    with _client(lambda r: httpx.Response(200, json=payload)) as hn:
        _, reactions = hn.fetch_reactions(SourceRef("hackernews", "1"))
    by_id = {r.comment_id: r for r in reactions}
    assert (by_id[1].depth, by_id[1].reply_count) == (0, 2)
    assert (by_id[2].depth, by_id[2].reply_count) == (1, 0)


def test_深すぎる枝は打ち切る():
    node = _c(999)
    for i in range(MAX_COMMENT_DEPTH + 10):
        node = _c(i, children=[node])
    with _client(lambda r: httpx.Response(200, json=_item([node]))) as hn:
        _, reactions = hn.fetch_reactions(SourceRef("hackernews", "1"))
    assert len(reactions) <= MAX_COMMENT_DEPTH + 1


def test_取得に失敗したらNoneと空リストを返す(monkeypatch):
    # 呼び出し側はこれを見て「今回は判定不能」として pending のまま残す
    monkeypatch.setattr("imotech.sources.hackernews.time.sleep", lambda _: None)
    with _client(lambda r: httpx.Response(500)) as hn:
        assert hn.fetch_reactions(SourceRef("hackernews", "1")) == (None, [])


@pytest.mark.parametrize("bad", [b"not json", b"{"])
def test_壊れた応答でも例外を投げない(monkeypatch, bad):
    monkeypatch.setattr("imotech.sources.hackernews.time.sleep", lambda _: None)
    with _client(lambda r: httpx.Response(200, content=bad)) as hn:
        assert hn.fetch_stories() == []

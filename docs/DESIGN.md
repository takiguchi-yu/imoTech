# imoTech 実装設計書

Hacker News で議論を呼んだ英語圏のテック記事を、日本語の「要旨 + 議論の論調 + imo」として公開する自動化パイプラインの設計。
用語は [CONTEXT.md](../CONTEXT.md) に従う。この文書は実装の設計だけを扱い、用語の定義はしない。

**前提の確定日**: 2026-09-21 / **調査した一次情報の確認日**: 同日

---

## 1. 全体像

### 1.1 データフロー

```mermaid
flowchart TB
    HN["Hacker News<br/>Algolia API"]
    SRC["元記事サイト<br/>robots.txt を確認してから取得"]
    GEM["Gemini API<br/>Free tier"]
    NOTION[("Notion DB")]
    STORE[("data/candidates.jsonl<br/>候補ストア")]
    HUMAN(["★ 人間<br/>imo を書き Status を Approved にする"])
    MD[("site/src/content/articles/&lt;slug&gt;.md<br/>公開物")]
    CFB["Cloudflare Workers<br/>publish.yml が wrangler deploy で配る"]
    SITE["Workers + Static Assets<br/>imoTech 公開"]

    subgraph DAILY["daily.yml — 毎日 06:17 JST"]
        COLLECT["collect"]
        COMPOSE["compose"]
    end

    subgraph PUB["publish.yml — 毎時 23 分"]
        DETECT["Approved を検知"]
        RENDER["Markdown を生成"]
    end

    HN -->|"1 story を検索"| COLLECT
    COLLECT -->|"2 新規のみ追記 state=pending"| STORE
    STORE -->|"3 24h 経過かつ閾値を満たす上位 N 件"| COMPOSE
    COMPOSE -->|"4 本文を取得"| SRC
    SRC -.->|"拒否・失敗なら og:description"| COMPOSE
    HN -->|"5 コメント木を 1 リクエストで取得"| COMPOSE
    COMPOSE -->|"6 匿名化した反応 + 要旨"| GEM
    GEM -.->|"429 ならモデルを落とす<br/>3.8 → 3.7 → 3.6 → 3.5 → 3.5-lite"| GEM
    GEM -->|"7 記事 JSON"| COMPOSE
    COMPOSE -->|"8 Draft を作成"| NOTION
    COMPOSE -->|"state=drafted"| STORE

    NOTION --> HUMAN
    HUMAN -->|"9 ここだけが公開の引き金"| NOTION

    NOTION -->|"10 Status=Approved かつ imo が空でない"| DETECT
    DETECT --> RENDER
    RENDER -->|"11 commit"| MD
    RENDER -->|"13 Status=Published に書き戻す"| NOTION
    MD -->|"12 git push"| CFB
    CFB --> SITE

    classDef human fill:#fff3cd,stroke:#b8860b,stroke-width:2px,color:#333
    classDef store fill:#e8f4f8,stroke:#31708f,color:#333
    classDef ext fill:#f5f5f5,stroke:#888,color:#333
    class HUMAN human
    class STORE,NOTION,MD store
    class HN,SRC,GEM,CFB,SITE ext
```

矢印の番号は処理の順序を表す。**9 番だけが人間の操作**で、他はすべて自動。
デプロイは `publish.yml` が `wrangler deploy` で行う（Workers Builds の Git 連携を使わない理由は 5.5 参照）。

### 1.2 ワークフローの分割

| ワークフロー | トリガー | 責務 | timeout |
|---|---|---|---|
| `daily.yml` | cron `17 21 * * *` (UTC) = 毎日 06:17 JST + `workflow_dispatch` | collect → compose | 20 分 |
| `publish.yml` | cron `23 * * * *` = 毎時 23 分 + `workflow_dispatch` | Approved 検知 → commit → ビルド → `wrangler deploy` → Notion を Published に | 10 分 |
| `ci.yml` | `push` / `pull_request` | lint + test | 10 分 |

**毎正時を避ける理由**: 公式ドキュメントに「The `schedule` event can be delayed during periods of high loads of GitHub Actions workflow runs. High load times include the start of every hour. If the load is sufficiently high enough, some queued jobs may be dropped.」と明記されている（[events-that-trigger-workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)）。分をずらしても drop の可能性は消えないため、**遅延・欠落を前提にした設計**（下記 5.5）にしている。

### 1.2b ローカル通し（Notion を使わない経路）

M2 の前に、外部アカウントを使わずに通しで動かす経路を用意した。M1 の完成後、
「生成物の行き先が無い」状態を解消するために入れたもので、**M2 を置き換えるものではない**。

```
collect → compose → site/src/content/articles/<slug>.md → Astro → localhost:4321
                         ↑ ここで止まり、人が imo を書くまで公開されない
```

Notion 運用との対応:

| Notion 経由（M2 以降） | ローカル通し（いま） |
|---|---|
| Draft を Notion に投入 | Markdown を `site/src/content/articles/` に書き出す |
| `imo` プロパティが空なら公開しない | 本文の `IMO_PLACEHOLDER` が残っていれば公開しない |
| 人が Status を Approved にする | 人がプレースホルダを自分の言葉に置き換える |
| `publish` が Markdown を commit | `compose` が直接書く。M3 以降は `daily.yml` が候補ストアと一緒に commit する |
| state を `drafted` にする | 同じ（Markdown を書けた時点で `drafted`） |

**公開の引き金を「人が何かを書くこと」に置いている点は同じ**。フラグを立てる方式にすると
立て忘れが起きるが、この方式なら書かないかぎり出ない。

`IMO_PLACEHOLDER` は `src/imotech/render.py` と `site/src/content.config.ts` の
両方に定義があり、ずれると「imo 未記入の記事が公開される」ため `tests/test_render.py` で突合している。

### 1.3 コンポーネントの責務と依存の向き

```
  cli.py  (collect / compose / publish のエントリポイント)
    │
    ├──▶ store.py        候補の永続化。jsonl の読み書きをここだけに閉じる
    ├──▶ sources/        StoryFeed / ReactionSource の Protocol と HN 実装
    ├──▶ extract.py      元記事本文の取得。robots.txt の判定を含む
    ├──▶ anonymize.py    反応から投稿者情報を落とす
    ├──▶ llm.py          Gemini 呼び出しとモデルフォールバック
    ├──▶ notion.py       Notion の投入・検知・更新
    └──▶ render.py       Draft → Markdown（フロントマター込み）
         │
         └──▶ models.py  すべてが依存する dataclass 群。他の何にも依存しない
```

**逆向きの参照を作らない**。`models.py` は他モジュールを import しない。`notion.py` は `store.py` を知らない（呼び出し順は `cli.py` が決める）。`render.py` は Notion の API 形式を知らず、`models.Draft` だけを受け取る。

**採用したパターン**
- **Repository** (`store.py`): 候補の永続化形式（jsonl）を 1 箇所に閉じる。将来 SQLite に替えても呼び出し側は変わらない。
- **Strategy（薄く）** (`sources/`): `StoryFeed` / `ReactionSource` の Protocol を切り、実装は Hacker News のみ。Bluesky / Mastodon を後から足す前提があるため。

**見送ったパターン**
- **Chain of Responsibility**: ステージ連鎖に分岐が無く、関数の直列呼び出しで読めるため入れない。
- **State**: Status の遷移は「人間が 1 回 Approved にする」だけで、状態ごとの振る舞いの差が無い。Enum + 遷移関数で足りる。

---

## 2. インターフェース仕様

### 2.1 候補ストア `data/candidates.jsonl`

1 行 1 候補の JSON Lines。**追記のみ**ではなく、状態更新時は全行を読み直して書き戻す（件数が数千行の規模では問題にならない）。

```json
{
  "url_hash": "3f9a1c7e2b8d4506",
  "hn_item_id": 41234567,
  "url": "https://example.com/posts/rust-async-split",
  "title": "The Rust async runtime split, one year later",
  "collected_at": "2026-09-21T21:17:04Z",
  "score_at_collect": 12,
  "comments_at_collect": 3,
  "state": "pending",
  "evaluated_at": null,
  "score_at_evaluate": null,
  "comments_at_evaluate": null,
  "notion_page_id": null,
  "skip_reason": null
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `url_hash` | string(16) | **冪等性キー**。正規化 URL の SHA-256 先頭 16 桁（2.2 参照） |
| `hn_item_id` | int | HN の item id。同じ URL が再投稿された場合の区別に使う |
| `url` | string | 元記事の URL（正規化**前**の原文。表示と取得に使う） |
| `title` | string | HN 上のタイトル（英語） |
| `collected_at` | RFC3339 | 収集時刻（UTC） |
| `score_at_collect` / `comments_at_collect` | int | 収集時点の値。熟成の伸び幅を見るために残す |
| `state` | enum | `pending` \| `drafted` \| `skipped` |
| `evaluated_at` | RFC3339 \| null | 熟成判定を行った時刻 |
| `score_at_evaluate` / `comments_at_evaluate` | int \| null | 判定時点の値。Notion に載せるのはこちら |
| `notion_page_id` | string \| null | 投入した Notion ページの id |
| `skip_reason` | string \| null | `below_threshold` \| `no_content` \| `llm_failed` \| `over_daily_limit` |

**state の遷移**: `pending` → `drafted`（Notion 投入成功）または `pending` → `skipped`（閾値未達・本文取得失敗・生成失敗）。`skipped` からは戻らない。

### 2.2 URL 正規化とハッシュ（冪等性の担保）

同じ記事が別の URL 表記で HN に複数回投稿されても 1 回しか書かないための仕組み。

```python
# src/imotech/urlhash.py の方針
TRACKING_PARAMS = {"utm_source","utm_medium","utm_campaign","utm_term","utm_content",
                   "ref","ref_src","fbclid","gclid","mc_cid","mc_eid","s","__twitter_impression"}

def normalize(url: str) -> str:
    # 1. scheme を https に固定（http/https の差を吸収）
    # 2. host を小文字化し、先頭の "www." を除去
    # 3. TRACKING_PARAMS を query から除去し、残りを key でソート
    # 4. fragment (#...) を除去
    # 5. path 末尾の "/" を除去（ただし path が "/" だけの場合は残す）

def url_hash(url: str) -> str:
    return hashlib.sha256(normalize(url).encode()).hexdigest()[:16]
```

**重複排除は 3 段構え**にする。1 つでも漏れると同じ記事を 2 回書くため。

1. `collect` 時: `candidates.jsonl` に同じ `url_hash` があればスキップ
2. `compose` 時: Notion を `URL Hash` プロパティで検索し、既存ページがあればスキップ
3. `publish` 時: `site/src/content/articles/` に同じ `slug` のファイルがあれば上書きせずスキップ（Notion 側の Status 更新だけ行う）

### 2.3 Gemini への入力（匿名化済み反応）

```
# システム指示（プロンプトの固定部分。src/imotech/prompts/ に置く）
あなたは日本語のテックメディアの編集者です。以下を読み、指定の JSON 形式で出力してください。
- 反応の原文をそのまま引用してはいけません。論点ごとに再構成してください。
- 反応の投稿者を特定しうる表現（ハンドル名、所属の推測）を書いてはいけません。
- 事実と意見を混ぜず、です・ます調で書いてください。

# ユーザー入力（動的部分）
## 元記事
タイトル: {title}
URL: {url}
本文（抜粋、最大 8000 文字）:
{article_text}

## Hacker News の反応（{n} 件、投稿者情報は削除済み）
[C1] (返信 7 件, 階層 0) {body}
[C2] (返信 0 件, 階層 1) {body}
...
```

**匿名化で落とすもの**: `by`（ハンドル名）、ユーザープロフィール URL、コメント本文中の `@username` 形式のメンション。
**残すもの**: 本文、`len(kids)`（直接の返信数）、ツリーの階層。
**残す理由**: HN の API はコメント単位の score を返さない（[HackerNews/API](https://github.com/HackerNews/API) の item に `score` があるのは story と pollopt のみ）ため、「どの意見が議論を呼んだか」を測れる唯一の手がかりが返信構造になる。

### 2.4 Gemini からの出力（構造化 JSON）

`response_mime_type: "application/json"` と `response_schema` を指定して、パース失敗を構造的に防ぐ。

```json
{
  "title": "Rust の非同期ランタイム分裂から1年、HN の争点は「互換性の約束」",
  "slug_hint": "rust-async-runtime-split-one-year",
  "digest": [
    "2025年に分裂した Rust の非同期ランタイム勢力図が、1年でどう変わったかを追った記事。",
    "筆者は tokio 以外の選択肢が実用段階に入ったとする一方、エコシステムの分断コストを指摘している。",
    "具体的には、ライブラリ側が複数ランタイムに対応するための抽象化レイヤの現状を比較している。"
  ],
  "discourse": [
    {
      "point": "互換レイヤは問題を先送りしているだけではないか",
      "detail": "最も返信を集めたのは、抽象化レイヤ自体が新たな依存になるという指摘でした。...",
      "stance": "critical"
    },
    {
      "point": "実運用ではランタイムを混ぜる場面がそもそも少ない",
      "detail": "...",
      "stance": "supportive"
    }
  ],
  "tags": ["rust", "async", "ecosystem"]
}
```

| フィールド | 制約 |
|---|---|
| `title` | 日本語、40〜60 文字。事実 + 争点を含める。`【】` と感情語を使わない |
| `slug_hint` | 英小文字・数字・ハイフンのみ。最終 slug は `YYYY-MM-DD-<slug_hint>` |
| `digest` | 3〜5 要素、各 60〜120 文字 |
| `discourse` | 2〜4 要素。`stance` は `supportive` \| `critical` \| `mixed` |
| `tags` | 2〜5 要素、英小文字 |

### 2.5 公開物の Markdown（`site/src/content/articles/<slug>.md`）

```markdown
---
title: "Rust の非同期ランタイム分裂から1年、HN の争点は「互換性の約束」"
publishedAt: 2026-09-22T09:00:00+09:00
sourceUrl: "https://example.com/posts/rust-async-split"
sourceTitle: "The Rust async runtime split, one year later"
hnUrl: "https://news.ycombinator.com/item?id=41234567"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/example.com/posts/rust-async-split"
hnScore: 342
hnComments: 187
tags: ["rust", "async", "ecosystem"]
model: "gemini-3.8-flash"
generatedAt: 2026-09-22T06:12:31Z
---

## 元記事の要旨

- ...

## 議論の論調

### 互換レイヤは問題を先送りしているだけではないか

...

## imo

（人間が書いた 1 行以上。空のあいだはプレースホルダが入り、公開されない）

```

出典と AI 利用の開示は**本文に入れない**。サイトのテンプレート（`site/src/pages/articles/[...slug].astro`）がフロントマターから描く。本文にも持たせると片方だけ古くなる。

`hatenaUrl` は `https://b.hatena.ne.jp/entry/s/` + 元記事 URL から scheme を除いたもの（https の場合）。**API は呼ばず、文字列として組み立てるだけ**。

---

## 3. Notion データベーススキーマ

### 3.0 API のバージョンとデータモデル（実装の前提）

| 事実 | 出典 |
|---|---|
| `Notion-Version` の現行値は **`2026-03-11`**。必須ヘッダで、欠けると 400 `missing_version` | [versioning](https://developers.notion.com/reference/versioning) |
| **`POST /v1/databases/{id}/query` は 2025-09-03 版で非推奨。** 代わりに `POST /v1/data_sources/{data_source_id}/query` を使う | [query-a-data-source](https://developers.notion.com/reference/query-a-data-source) |
| データモデルが変わり、**行とプロパティは database ではなく data source が持つ**。`data_source_id` は `GET /v1/databases/{database_id}` の `data_sources[0].id` から取る | [upgrade-guide-2025-09-03](https://developers.notion.com/guides/get-started/upgrade-guide-2025-09-03) |
| ページ作成の親は `{"data_source_id": ...}` | [post-page](https://developers.notion.com/reference/post-page) |
| DB 作成時のプロパティスキーマは `initial_data_source.properties` にネストする | [create-a-database](https://developers.notion.com/reference/create-a-database) |
| 1 クエリの上限は 10,000 件。到達すると `has_more: false` かつ `request_status.type == "incomplete"` | [query-a-data-source](https://developers.notion.com/reference/query-a-data-source) |

**古いバージョンを指定してはならない。** 動くが非推奨仕様のままになり、`data_source` を使う
新しい設計（ページ作成時の `data_source_id` など）が使えない。

### 3.0b Notion と Markdown の関係

**Notion は記事本文の正ではない。** 本文は `compose` が書いた Markdown が正で、
Notion からは**人が書いた imo だけ**を取り出す（`publish`）。

```
compose → Markdown を書く（## imo は空）
        → 同じ内容を Notion にも投入（imo プロパティは空）
人      → Notion で imo を書き、Status を Approved にする
publish → Notion から imo を読み、ローカルの Markdown に差し込む
        → Notion 側を Published にする
```

こうする理由は 2 つ。Notion のブロックから記事を再構成する複雑さを避けられること。
そして「正となるデータは Git」（Q2 の決定）を保てること。Notion が落ちても、
Notion の内容を消しても、公開済みの記事は影響を受けない。

**Notion を使わない運用も成立する。** `NOTION_TOKEN` と `NOTION_DATABASE_ID` が
揃っていなければ Notion の処理は黙って飛ばし、Markdown の `## imo` に直接書く運用になる。


### 3.1 プロパティ一覧

| プロパティ名 | 型 | 設定値 | 誰が書くか | 用途 |
|---|---|---|---|---|
| `Title` | Title | — | パイプライン | 記事タイトル（日本語） |
| `Status` | **Select** | `Draft` / `Approved` / `Published` / `Rejected` | 両方 | 状態。Approved だけが人間の操作 |
| `imo` | Rich text | — | **人間のみ** | 所感。空のまま Approved にされたら公開を拒否する |
| `URL Hash` | Rich text | — | パイプライン | 冪等性キー。投入前の存在チェックに使う |
| `Slug` | Rich text | — | パイプライン | `YYYY-MM-DD-<slug_hint>` |
| `Source URL` | URL | — | パイプライン | 元記事 |
| `HN URL` | URL | — | パイプライン | HN スレッド |
| `Hatena URL` | URL | — | パイプライン | はてブのコメントページ（リンクのみ） |
| `HN Score` | Number | 整数 | パイプライン | 熟成判定時のスコア |
| `HN Comments` | Number | 整数 | パイプライン | 熟成判定時のコメント数 |
| `Tags` | Multi-select | — | パイプライン | タグ |
| `Collected At` | Date | 時刻を含む | パイプライン | 候補として拾った時刻 |
| `Published At` | Date | 時刻を含む | パイプライン | commit した時刻 |
| `Model` | Rich text | — | パイプライン | 実際に使われたモデル ID（フォールバックの記録） |

**`Status` を Notion の Status 型ではなく Select 型にする理由**: Status 型のオプションは API から作成できず、Notion の UI で手作業になる。Select 型なら DB 作成スクリプトで完結し、環境の再現性が取れる。グループ機能（To-do / In progress / Complete）は今回の 4 状態には不要。

**`imo` をページ本文のブロックではなくプロパティにする理由**: API で確実に取得でき（本文ブロックの走査が不要）、「空のまま Approved」のバリデーションが 1 行で書ける。Notion のテーブルビューでも一覧できる。

### 3.2 ステータス遷移

```
                  ┌──────────────────────────────┐
                  │                              │ (人間が却下)
   [compose]      ▼                              │
  ─────────▶  ┌───────┐   人間が imo を書いて   ┌──────────┐
              │ Draft │──────────────────────▶ │ Approved │
              └───────┘        Approved に      └────┬─────┘
                  │                                  │
                  │ (人間が却下)                       │ [publish] が検知
                  ▼                                  │ Markdown を commit
             ┌──────────┐                            ▼
             │ Rejected │                      ┌───────────┐
             └──────────┘                      │ Published │
                                               └───────────┘
```

- `Draft` → `Approved`: **人間のみ**。これが公開の唯一の引き金
- `Approved` → `Published`: `publish` ワークフローが commit 成功後に書き戻す
- `Draft` / `Approved` → `Rejected`: 人間が却下。パイプラインは二度と触らない
- `Published` から先に遷移はない。記事を直したいときは Markdown を直接編集する（Git が正）

**`Approved` の検知クエリ**（Notion API の制約への対処）:

```json
{
  "filter": {
    "and": [
      { "property": "Status", "select": { "equals": "Approved" } },
      { "property": "imo", "rich_text": { "is_not_empty": true } }
    ]
  }
}
```

`last_edited_time` はページ単位でしか取れず「Status が変わった瞬間」を検知できない（[filter リファレンス](https://developers.notion.com/reference/post-database-query-filter)）。そこで**時刻ではなく状態そのものを引く**。`Approved` は publish が処理したら即 `Published` に変わるため、このクエリは常に「未処理の承認」だけを返す。時刻比較が不要になり、ワークフローが遅延・欠落しても取りこぼさない。

`imo` の空チェックをクエリに含めることで、書き忘れたまま Approved にした記事が公開されるのを仕組みで防ぐ。

### 3.3 ページ本文のブロック構造

```
callout   ⚠️ 公開するには、右の imo プロパティに一言書いてから Status を Approved にしてください
heading_2 元記事の要旨
bulleted_list_item × 3〜5
heading_2 議論の論調
  heading_3 <論点1>
  paragraph <detail>
  heading_3 <論点2>
  paragraph <detail>
divider
heading_2 出典
bulleted_list_item 元記事: <Source URL>
bulleted_list_item Hacker News: <HN URL>
bulleted_list_item はてなブックマーク: <Hatena URL>
paragraph 生成モデル: <model> / 生成日時: <generatedAt>
```

**ブロックの分割投入**: Notion API は 1 リクエストあたり **1,000 ブロック / 500 KB / 配列 100 要素**が上限（[request-limits](https://developers.notion.com/reference/request-limits)）。記事 1 本は 20 ブロック前後で収まるが、`children` 配列は 100 要素上限があるため、**100 件ずつに分割して `PATCH /v1/blocks/{id}/children` で追記する**実装にする。

**rich_text の 2,000 文字上限**: `detail` が長い場合に備え、2,000 文字を超えたら段落を分割する。

---

## 4. 熟成と選別

### 4.1 判定ロジック

```python
# src/imotech/config.py（すべて環境変数で上書き可能にする）
MATURATION_HOURS = 24  # 収集からこの時間が経った候補だけを評価する
MIN_SCORE = 100  # HN の points 下限
MIN_COMMENTS = 30  # コメント数の下限
MAX_DRAFTS_PER_RUN = 5  # 1 回の実行で作る下書きの上限
MAX_AGE_HOURS = 96  # これを過ぎた pending は skipped(below_threshold) にする
```

```
compose の処理順:
  1. candidates.jsonl から state == "pending" を読む
  2. collected_at + MATURATION_HOURS <= now のものだけ残す
  3. Algolia で現在の points / comments を取り直す（収集時の値ではなく現在値で判定）
  4. points >= MIN_SCORE かつ comments >= MIN_COMMENTS を満たすものを残す
  5. points の降順に並べ、上位 MAX_DRAFTS_PER_RUN 件だけ処理する
  6. 残った候補のうち collected_at + MAX_AGE_HOURS を過ぎたものは skipped にする
     （それ以外は pending のまま翌日に持ち越す）
```

**閾値を満たす候補が 0 件の日は、記事を 1 本も作らない**。これは意図した挙動で、AdSense の Publisher Policies が広告を許さないとしている "low-value content" / "embedded or copied content from others without additional commentary, curation, or otherwise adding value"（[Publisher Policies](https://support.google.com/adsense/answer/9335564)）を避けるための設計判断。更新頻度より 1 本あたりの密度を取る。

**現在値で判定する理由**: 収集時点のスコアは「まだ誰も反応していない」段階の値で、熟成の判定に使えない。Algolia の `/api/v1/items/<id>` は 1 リクエストでコメント木ごと取れるため、判定と反応取得を同じレスポンスで済ませられる。

### 4.2 閾値の初期値の根拠と調整

`MIN_SCORE = 100` / `MIN_COMMENTS = 30` は**運用しながら調整する前提の初期値**であり、一次情報に基づく値ではない。HN の front page 到達ラインは時間帯とその日の投稿量で変動するため、固定値の正解は存在しない。

**調整の手順**: 運用 2 週間後に `candidates.jsonl` を集計し、`MAX_DRAFTS_PER_RUN` に対して候補が常に余る（＝閾値が緩い）か、0 件の日が続く（＝厳しい）かを見て動かす。この集計は `uv run imotech stats` で出せる（M1 で実装済み）。

---

## 5. エラーハンドリングとレート制限

### 5.1 Gemini API

**モデルフォールバック**（Q8 の決定）:

```python
MODEL_CHAIN = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
]
```

```
1 記事の生成:
  for model in MODEL_CHAIN:
      for attempt in 1..3:
          try: return generate(model, prompt)
          except RateLimited (429):
              if attempt < 3: sleep(2 ** attempt)  # 2s, 4s
              else: break  # 次のモデルへ
          except ServerError (5xx):
              if attempt < 3: sleep(2 ** attempt)
              else: break
          except InvalidResponse:  # JSON schema 不一致
              if attempt < 3: continue  # 同じモデルで再試行
              else: break
  # 全モデルで失敗 → その候補を pending のまま残し、失敗を記録して次の候補へ
```

**スロットリング**: 記事間に固定 6 秒の sleep を入れる。5 本でも合計 30 秒で、20 分の timeout に対して十分な余裕がある。

**RPD/RPM の公称値は確認できない**: Google は[レート制限の数値を公式ドキュメントから削除](https://ai.google.dev/gemini-api/docs/rate-limits)し（"Rate limits ... can be viewed in Google AI Studio"）、AI Studio のログイン後ページでしか公開していない。さらに**この環境では組織の管理者が AI Studio を無効化**しており、そのページも開けない。

**代わりに実ワークロードで実測した（2026-09-21）**。1 日分（5 本）を流した結果:

| 指標 | 実測 |
|---|---|
| 429（レート制限） | **0 件** |
| 503（一時的な不可用） | **20 件**（3.8=8 / 3.7=6 / 3.6=6） |
| 生成成功 | 3 件（うち 2 件は 10 回目の試行で成功） |

**無料枠は「枠」ではなく「空き」で律速されている。** よって `MAX_DRAFTS_PER_RUN = 5` を下げる理由は無い。一方で**モデルフォールバックが無いと成立しない**（2 件は 3.8 → 3.7 → 3.6 → 3.5 と落ちてようやく通った）。鎖を短くしてはならない。

**匿名化の強制**: `llm.py` は `anonymize.py` を通していない生の反応を受け取れない型にする（`AnonymizedReaction` 型を引数に取る）。無料枠は[規約](https://ai.google.dev/gemini-api/terms)に "human reviewers may read, annotate, and process your API input and output... Do not submit sensitive, confidential, or personal information to the Unpaid Services." とあるため、PII の送信を実装レベルで防ぐ。

**Amazon 関連情報を Gemini に渡さない**: Amazon アソシエイトのポリシーに「プログラム・コンテンツから作成したAI生成コンテンツを...大規模言語モデル...を開発または改善するために使用しない」とあり、無料枠は入力が学習に使われる。アフィリエイトの商品情報は Gemini のプロンプトに一切含めない。

### 5.2 Notion API

| 事象 | 対処 |
|---|---|
| 429 | レスポンスの `Retry-After` ヘッダ（および body の `additional_data.retry_after`）を尊重して待つ。最大 3 回 |
| 5xx / 529 | 指数バックオフで**最大 3 回試行**。待ちは 1 回目の失敗後 1 秒、2 回目の失敗後 2 秒（3 回目が失敗した時点で諦めるので 4 秒待ちには到達しない）。`IMOTECH_NOTION_MAX_ATTEMPTS=4` にすれば 4 秒待ちも入る |
| 通常時 | リクエスト間に **350 ms** の間隔を入れる（Free/Plus は 180 req/min = 平均 3 req/sec、[request-limits](https://developers.notion.com/reference/request-limits)） |
| 403 `restricted_resource` + `block_limit` | ワークスペースのブロック上限。**1 人ワークスペースなら無制限**なので、これが出たら「2 人目を招待した」のサイン。Issue のメッセージにこの注意書きを含める |

**Notion ワークスペースは 1 人で運用すること。** Free プランは 2 人目のメンバーを入れた瞬間に生涯 1,000 ブロック上限がかかり、API も 403 を返してパイプラインが停止する（[workspace-block-limits](https://developers.notion.com/reference/workspace-block-limits)）。共同編集が必要になったらゲスト招待（10 人まで）で回避する。

### 5.3 Hacker News

| 事象 | 対処 |
|---|---|
| 取得方法 | **Algolia の `/api/v1/items/<id>`** を使い、コメント木を 1 リクエストで取る。Firebase API で `kids` を再帰的に辿ると 1 記事で数百リクエストになるため使わない |
| レート制限 | Algolia は 10,000 req/h（[hn.algolia.com/api](https://hn.algolia.com/api)）。1 日 5〜30 リクエスト程度なので余裕 |
| 5xx / タイムアウト | 指数バックオフ 3 回。全滅したらその候補を pending のまま翌日へ |
| 欠損フィールド | `points` / `num_comments` / `url` が `null` のことがある（Ask HN など URL を持たない投稿）。**`url` が null の story は collect の段階で除外する**（元記事が存在しないため） |
| 削除されたコメント | `text` が null の要素はスキップする |

**収集クエリ**:
```
GET https://hn.algolia.com/api/v1/search_by_date
      ?tags=story
      &numericFilters=created_at_i>{24時間前のunixtime},points>{COLLECT_MIN_SCORE}
      &hitsPerPage=50
```
`COLLECT_MIN_SCORE` は熟成前の粗いフィルタ（初期値 10）。ここを 0 にすると 1 日数千件が候補に入り jsonl が肥大化する。

### 5.4 元記事の本文取得

```
1. urllib.robotparser で {origin}/robots.txt を取得し、can_fetch(USER_AGENT, url) を判定
   - robots.txt が 404 / 取得失敗 → 「許可」として扱う（RFC 9309 の既定に沿う）
   - robots.txt が 5xx → 「不許可」として扱い、OGP にフォールバック
2. 許可された場合のみ GET
   - User-Agent: "imoTechBot/1.0 (+https://<domain>/about)"
   - timeout=10s, リダイレクト最大 5 回, レスポンス上限 5 MB, Content-Type が text/html 以外は中断
3. trafilatura で本文抽出 → 8,000 文字で切る
4. 抽出失敗 or 不許可 → <meta property="og:description"> にフォールバック
5. それも取れない → その候補を skipped(no_content) にする
```

**本文は Gemini への入力にのみ使い、記事には転載しない。** 公開物に載るのは Gemini が生成した日本語の要旨だけ。

`robots.txt` の判定は標準ライブラリの `urllib.robotparser` を使う（自作しない）。

### 5.5 GitHub Actions

| 事象 | 対処 |
|---|---|
| ジョブ失敗 | `if: failure()` で `.github/actions/notify-failure`（composite action）を呼ぶ。**同じラベル `pipeline-failure` の open issue があればコメント追記**して乱立を防ぐ。`publish.yml` からも同じ action を使う |
| 失敗しても exit 0 で終わる | `if: failure()` はステップの終了コードしか見ない。`compose` は Gemini の失敗も Notion の 403 も捕まえて続行するため、**そのままでは全滅しても 0 で終わる**。そこで「人が直すまで回復しない失敗」＝ **生成が全滅して記事化 0 件**／**Notion 投入が全滅**のときだけ非 0 を返す（`src/imotech/cli.py` の `cmd_compose` 末尾）。部分的な失敗は 0 のまま — pending に残り次回が拾うので、1 件ごとに Issue が立つと通知が意味を失う |
| schedule の遅延・drop | 状態を時刻ではなく `state` / `Status` で持っているため、1 回飛んでも次回が拾う。`MAX_AGE_HOURS=96` があるので、3 回連続で飛んでも取りこぼさない |
| 60 日無活動での自動停止 | **`daily.yml` が毎日 `candidates.jsonl` を commit するため、無活動状態にならない**（public repo の schedule は「no repository activity in 60 days」で停止する。[docs](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)） |
| ワークフローの多重実行 | `concurrency: { group: <workflow>, cancel-in-progress: false }` |
| commit の競合 | push 前に `git pull --rebase origin main`。`daily.yml` は `data/candidates.jsonl` と **`site/src/content/articles/` の新規ファイル**、`publish.yml` は既存記事の `## imo` を書き換える。同じ記事ファイルに同時に当たらない限り rebase で解決でき、当たった場合はジョブが失敗して Issue が立つ |
| timeout / キャンセルで通知が出ない | `if: failure()` は timeout（`timeout-minutes` 到達）や手動キャンセルでは真にならない。`if: ${{ failure() \|\| cancelled() }}` で両方を拾う（[expressions](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions) の `cancelled()` は「ワークフローがキャンセルされたら true」） |
| 通知が 2 本立つ | `daily.yml` と `publish.yml` がほぼ同時に失敗すると、双方が open issue を見つけられず Issue が 2 本立つ。GitHub API に「無ければ作る」の原子操作が無いので避けられない。**実害は Issue 2 本なので許容する** |
| 自動 commit に CI が当たらない | `GITHUB_TOKEN` による push は新しいワークフロー実行を作らない（[公式](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)。再帰実行の防止）。`ci.yml` の公開ゲート検証は自動 commit をすり抜けるが、公開の可否を決めるのはサイト側のゲート（`site/src/lib/imo.ts`）なので、未記入記事の漏洩には至らない |
| 失敗通知が届かない | 公式の通知は「自分がトリガーした実行」が対象で、schedule はワークフロー作成者に飛ぶ。cron を編集すると通知先が移る（[notifications](https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs)）。**Issue 起票を一次の通知手段とし、メール通知には依存しない** |

**Secrets**（すべて GitHub Secrets に登録。public repo でもログには出ない）:

| 名前 | 用途 | 取得元 |
|---|---|---|
| `GEMINI_API_KEY` | Gemini API | Google AI Studio |
| `NOTION_TOKEN` | Notion 内部インテグレーション | Notion の Integrations 画面 |
| `NOTION_DATABASE_ID` | 対象 DB | Notion の DB URL |
| `GITHUB_TOKEN` | commit / issue 起票 / 失敗ステップの特定 | Actions が自動発行（`permissions: {contents: write, issues: write, actions: read}` を宣言。`actions: read` は `gh run view --json jobs` が実行の記録を読むために必要） |
| `CLOUDFLARE_API_TOKEN` | `wrangler deploy` | Cloudflare の Account API tokens で「Edit Cloudflare Workers」テンプレートから発行 |
| `CLOUDFLARE_ACCOUNT_ID` | 同上 | Cloudflare ダッシュボード |

**Variables**（secret ではない。値が見えてよいもの）:

| 名前 | 用途 |
|---|---|
| `SITE_URL` | `astro build` が sitemap と RSS に焼き込む絶対 URL。`https://imotech.<サブドメイン>.workers.dev` |

**デプロイは Actions から `wrangler deploy` を叩く。** Workers Builds の Git 連携ではなく、
`publish.yml` の中でビルドしてデプロイする。理由は 3 つ。

1. **失敗を検知できる。** Git 連携だと Cloudflare 側でビルドが落ちても Actions は成功するので
   Issue が立たず、サイトが何日も古いままになる（気づく手段はダッシュボードだけ）
2. **Cloudflare のビルド枠を使わない。** Free は月 500 ビルド・同時 1 ビルドで、
   **Workers Builds にパスフィルタは無い**（[configuration](https://developers.cloudflare.com/workers/ci-cd/builds/configuration/)
   の設定項目は Git アカウント・リポジトリ・ブランチ・ビルドコマンド・デプロイコマンド・
   ルートディレクトリ・ビルド変数だけ）。`candidates.jsonl` だけの commit でもビルドが走る
3. **`SITE_URL` の設定漏れが起きない。** Actions の `env` で渡せる

使うのは公式アクション `cloudflare/wrangler-action@v4`
（[github-actions](https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/)）。
`GITHUB_TOKEN` による push は他のワークフローを起動しないため、デプロイは
**`publish.yml` と同じジョブの中**に置く（別ワークフローに切り出すと走らない）。

`daily.yml` はデプロイしない。`compose` が書く記事は `imo` 未記入で、サイト側のゲートが
公開から外すため、公開物は変わらない。

### 5.6 「RSS のフォーマット差異」について（元の要件からの変更点）

当初の要件には「取得元 RSS のフォーマット差異や取得失敗時のフォールバック処理」が含まれていたが、**設計の結果 RSS を使わない**ことになった（情報源が Hacker News の API 単独）。RSS 特有の差異（RSS 2.0 / Atom / 日付フォーマットの揺れ / CDATA）への対処は不要になる。

将来 RSS ソースを足す場合に備え、`sources/` の `StoryFeed` Protocol は「フィードの形式を知らない」インターフェース（`fetch_stories() -> list[Story]`）にしてある。RSS 実装を足すときは `sources/rss.py` に閉じ、`feedparser` で形式差を吸収する。

---

## 6. ディレクトリ構成

```
imoTech/
├── CONTEXT.md                     用語集（実装の詳細は書かない）
├── README.md                      セットアップと運用手順
├── .gitignore
├── .env.example                   必要な環境変数の一覧（値は空）
├── pyproject.toml                 uv
├── uv.lock
├── docs/
│   └── DESIGN.md                  この文書
├── .scratch/
│   └── pipeline/                  マイルストーンのチケット
├── data/
│   └── candidates.jsonl           候補ストア（Git 管理。空ファイルで初期化）
├── src/
│   └── imotech/
│       ├── __init__.py
│       ├── cli.py                 collect / compose / publish / stats
│       ├── config.py              閾値・モデル一覧・環境変数の読み込み
│       ├── models.py              Story / Candidate / Reaction / Draft の dataclass
│       ├── urlhash.py             URL 正規化とハッシュ
│       ├── store.py               candidates.jsonl の読み書き（Repository）
│       ├── pipeline.py            熟成判定と選別（副作用を持たない純関数）
│       ├── anonymize.py           反応から投稿者情報を落とす
│       ├── extract.py             元記事本文の取得（robots.txt 判定込み）
│       ├── llm.py                 Gemini 呼び出しとモデルフォールバック
│       ├── notion.py              Notion の投入・検知・更新
│       ├── render.py              Draft → Markdown
│       └── prompts/
│           └── compose.md         システム指示（コードと分離する）
├── tests/
│   ├── test_urlhash.py            正規化のケース（トラッキング除去、www、末尾スラッシュ）
│   ├── test_store.py              追記・更新・重複検出
│   ├── test_pipeline.py           熟成と選別の境界条件
│   ├── test_anonymize.py          ハンドル名とメンションが残らないこと
│   └── test_render.py             フロントマターの生成
├── site/                          Astro
│   ├── package.json
│   ├── astro.config.mjs
│   ├── wrangler.jsonc             Workers + Static Assets
│   ├── public/
│   └── src/
│       ├── content.config.ts      Content Collections のスキーマと IMO_PLACEHOLDER
│       ├── lib/
│       │   ├── imo.ts             ★ 公開判定と定数の唯一の定義元（npm test の対象）
│       │   └── articles.ts        コレクションの取得・タグ集計・日付整形
│       ├── content/
│       │   └── articles/          ★ 公開物の Markdown（compose が書く。M2 以降は publish が commit）
│       ├── layouts/
│       │   └── Base.astro
│       ├── components/
│       └── pages/
│           ├── index.astro        記事一覧
│           ├── about.astro        制作プロセスと AI 利用の開示
│           ├── privacy.astro      プライバシーポリシー（AdSense 申請時に要る）
│           ├── articles/[...slug].astro
│           ├── tags/[tag].astro
│           └── rss.xml.ts
└── .github/
    └── workflows/
        ├── daily.yml
        ├── publish.yml
        └── ci.yml
```

---

## 7. 主要ライブラリ

| 用途 | ライブラリ | 備考 |
|---|---|---|
| パッケージ管理 | `uv` | `astral-sh/setup-uv` の Action を使う |
| HTTP | `httpx` | タイムアウト・リトライの制御がしやすい |
| 本文抽出 | `trafilatura` | 主要な本文抽出ライブラリ。失敗時は OGP にフォールバック |
| robots.txt | `urllib.robotparser`（標準） | 自作しない |
| Gemini | `google-genai` | 公式 SDK。`response_schema` で構造化出力 |
| Notion | `httpx` で直接叩く | 公式 Python SDK は無い。REST が単純なので依存を増やさない |
| 設定 | `pydantic-settings` | 環境変数の型付き読み込みとバリデーション |
| テスト | `pytest` | |
| lint / format | `ruff` | |

---

## 8. マイルストーン

| # | ゴール | 完了の判定 |
|---|---|---|
| **M0** | 準備 | リポジトリ・アカウント・ドメインが揃い、`uv run imotech --help` が動く |
| **M1** | ローカルで収集〜生成が通る | `uv run imotech compose --dry-run` で記事 JSON が標準出力に出る |
| **M2** | Notion 連携 | `uv run imotech compose` で Notion に Draft が 3 件入る |
| **M3** | 定時自動実行 | `daily.yml` が cron で動き、失敗時に Issue が立つ |
| **M4** | 承認 → 公開 | Notion で Approved にすると、1 時間以内にサイトに記事が出る |

タスクの詳細は `.scratch/pipeline/` の各チケットを参照。

---
title: "Cloudflare、Denoを買収　ランタイム開発は1年後に終了へ"
publishedAt: 2026-10-12T09:36:48+09:00
sourceUrl: "https://deno.com/blog/cloudflare"
sourceTitle: "Cloudflare acquires Deno"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50019911"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/deno.com/blog/cloudflare"
score: 1367
comments: 696
tags: ["deno", "cloudflare", "javascript", "typescript", "serverless"]
model: "gemini-3.8-flash"
generatedAt: 2026-10-12T00:36:48Z
---

## 元記事の要旨

- Denoチーム全体がCloudflareに合流することを発表しました。今後は分散アプリケーション向けの基盤構築に注力し、個別のランタイムやホスティングの独立した開発からは退きます。
- Denoランタイムは月次のバグ修正とセキュリティ更新を1年間継続した後に開発終了となります。コードはMITライセンスのオープンソースとして残り、コミュニティによる継続開発は歓迎されます。
- ホスティングサービスのDeno Deployは6か月後に終了し有料顧客にはCloudflare Workersへの移行支援を行います。パッケージレジストリのJSRはCloudflareに移管されて運用を継続します。
- Denoチームが開発してきたcelldとCloudflareのWorkersやDurable Objectsを統合し、クラウドやオンプレミスを問わず動作するサーバー構築の標準基盤を目指します。

## 議論の論調

### 突然の開発終了告知に対する投資の梯子外しへの反発

多くの企業がNode.jsからの移行を進めていた中で、買収に伴いランタイム自体の開発終了が発表されたことへの驚きや落胆が広がっています。新興ツールを早期に採用するリスクを指摘する声や、企業に買収されてオープンソースプロジェクトが終了するパターンに対する不信感が示されています。

### Node.js互換性の追従による独自性の喪失という指摘

当初のクリーンな設計からnpm互換性を重視する方針へ舵を切ったことで、Node.jsを再実装する状態に陥り差別化が難しくなったとの見解が寄せられています。一方で、スタンドアロンスクリプトでの手軽な実行環境や標準ツールの完成度など、優れた開発体験を評価し終了を惜しむ声もあります。

### workerdとcelldの統合による新基盤への期待

分散ステート管理やDurable Objectsを中心としたプログラミングモデルをオープンソースかつセルフホスト可能な形で発展させる方針に対しては、AIエージェントなどの新しいユースケースに適した抽象化として前向きに評価する開発者もいます。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **Durable Objects**: サーバーレス環境で永続化されたストレージと単一の実行状態を保持できるCloudflareの仕組みです。
- **workerd**: Cloudflare Workersを駆動しているオープンソースのJavaScript/Wasm実行基盤です。
- **JSR（JavaScript Registry）**: TypeScriptとECMAScriptモジュールに特化したDeno発のパッケージ公開・配布基盤です。

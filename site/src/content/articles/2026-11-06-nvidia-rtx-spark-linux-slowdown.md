---
title: "Nvidia RTX Sparkノート、Linux給電時に推論速度が約8割低下"
publishedAt: 2026-11-06T10:44:21+09:00
sourceUrl: "https://www.mindstudio.ai/blog/linux-nvidia-rtx-spark-laptop"
sourceTitle: "Nvidia RTX Spark encrypted firmware slows inference speed to 35% on Linux"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50362905"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/www.mindstudio.ai/blog/linux-nvidia-rtx-spark-laptop"
score: 610
comments: 283
tags: ["nvidia", "linux", "cuda", "hardware", "gpu"]
model: "gemini-3.7-flash"
generatedAt: 2026-11-06T01:44:21Z
---

## 元記事の要旨

- NvidiaのRTX Sparkを搭載したノートPCにおいて、Linuxを導入すると電源接続時にGPUクロックが約780MHzに固定され、推論性能が大きく低下することが判明しました。
- 120Bモデルでの検証では、WindowsやWSLで毎秒約65トークンを記録したのに対し、電源接続時のネイティブLinuxでは毎秒約14トークンとおよそ5分の1に落ち込みました。
- 原因はCPUとGPUの電力配分を司るコントローラーにあり、電力制御テーブルが暗号化されているため、復号キーを持たないLinuxでは正常な電力供給が行えません。
- バッテリー駆動時であれば制限を受けずに通常速度が出るほか、Windowsのドライバスタック上で動くWSLを利用すれば、クロック低下を回避しつつLinux用AIツールを実行できます。

## 議論の論調

### クラウド依存への誘導や差別化戦略を疑う声

電力設定テーブルが暗号化されている点に対し、安価なノートPCでLinux環境を構築してデータセンター的に運用されるのを防ぐための意図的な制限ではないかと疑う意見が上がりました。過去の仕様制限の前例を引き合いに出し、ハードウェアに対するベンダーの過度な囲い込みを危惧する声が目立ちます。

### 設計優先順位に起因する初期の未対応とみる見解

今回のノートPCはWindows on ARMを前提に作られた初世代のプラットフォームであり、Linux向け電力制御の実装が単に遅れているだけだとする冷静な指摘も多くなされました。過去にも同様の電力共有機能がLinuxドライバへ提供されるまで数年かかった経緯があり、悪意による機能制限とは断定できないという意見です。

### 有志の解析や将来の公式更新による解決への期待

Windows側のドライバ挙動をリバースエンジニアリングしてLinux向け互換機能をコミュニティで作成できるのではないかという議論や、公式ドライバのアップデートによる将来的な解決を期待する声が交わされました。ただし、現状では安定動作までのデバッグ負担が重すぎると躊躇する見方も出ています。

## 使いどころ

※ 元記事の内容をもとに生成 AI が考えた応用案です。元記事に書かれているとは限りません。

- **ノートPC上で100B級の大規模モデルを検証したいとき**: RTX Sparkノートは最大128GBの統合メモリを持ち巨大モデルを配置可能ですが、現状のLinuxネイティブでは給電時のGPU性能が約5分の1に激減するため、性能を維持するにはWSL環境上で実行するのが有効です。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **WSL（Windows Subsystem for Linux）**: Windows上でLinux環境を直接実行する仕組み。Windows側のGPUドライバを共有して動作します。
- **unified memory（統合メモリ）**: CPUとGPUが同一のメモリ領域を共有する構造。大容量モデルをGPUメモリに直接載せやすくなります。
- **vLLM**: 大規模言語モデルの高速な推論と効率的なメモリ管理を実現する、Linux環境向けの代表的なライブラリです。

---
title: "開発者、1992年製のCDPLAYERがWin 11で無改造動作することを確認"
publishedAt: 2026-10-28T09:35:37+09:00
sourceUrl: "https://blog.enlyth.com/posts/oldest-windows-gui-app-win-11/"
sourceTitle: "Oldest GUI application that still runs on Windows 11"
source: "hackernews"
discussionUrl: "https://news.ycombinator.com/item?id=50248055"
hatenaUrl: "https://b.hatena.ne.jp/entry/s/blog.enlyth.com/posts/oldest-windows-gui-app-win-11/"
score: 525
comments: 307
tags: ["windows", "win32", "gui", "retrocomputing", "compatibility"]
model: "gemini-3.5-flash"
generatedAt: 2026-10-28T00:35:37Z
---

## 元記事の要旨

- 64ビット版のWindows 11はNTVDMを欠くため16ビットアプリを直接実行できないことから、著者は変更やエミュレーションなしで動作する最も古い32ビットGUIアプリを探索した。
- 初期のWin32sに含まれていた1993年2月22日更新の「FREECELL.EXE」が、現行のWindows 11上で何ら変更を加えることなく正常にプレイ可能であることを確認した。
- さらに古いソフトを探した結果、1992年11月16日にビルドされた初期NT 3.1の「CDPLAYER.EXE」も、既存の互換ライブラリを通じて正常に起動することを発見した。
- 呼び出し規約やCランタイム依存の互換性問題を乗り越えたこのプログラムは、実に約34年前のバイナリでありながら、最新OSで動作する高い後方互換性を証明している。

## 議論の論調

### Win32 APIの軽量性と現代フレームワークの資源消費比較

昔のWin32 APIで作られたアプリの軽量さや高速な応答性を評価する声がある一方、現代のWeb技術やクロスプラットフォーム開発による資源消費の増大やUI不整合を懸念する意見が交わされました。また、最新の.NET環境の最適化を評価する見解も挙げられています。

### Windowsの後方互換性の高さに対する感嘆と他OSとの比較

数十年前に作成されたバイナリが最新のWindowsでそのまま動作する互換性の維持能力に感心するコメントが集まりました。同時に、動的ライブラリやABIの変更により過去のバイナリ実行が難しいLinuxやUnix環境の難しさとの対比も議論されています。

### 過去のGUIデザインに対する評価と現代UIへの不満

Windows 95や7時代のメニューバーや明確なボタン表示を中心としたGUIが使いやすかったと懐かしむ意見が多く見られます。モバイルファーストな設計やフラットデザインへの移行によって、操作性や画面領域の活用効率が低下したと指摘されています。

## imo

<!-- imo: ここに所感を 1 行以上書く。このコメント行を消すまで、この記事はサイトに公開されません -->

## 用語

- **NTVDM（NT Virtual DOS Machine、NT仮想DOSマシン）**: 32ビット版Windowsで16ビットのDOSやWindowsアプリを動かすための互換レイヤー。
- **cdecl（シーデクル、C言語呼び出し規約）**: 関数の呼び出し時に、スタックに積まれた引数の解除を呼び出し側が行うプログラム上の規約。
- **stdcall（スタンダードコール、標準呼び出し規約）**: 関数の呼び出し時に、引数の解除を呼び出された関数自身が行うWindows APIの標準規約。
- **PEフォーマット（Portable Executable、実行ファイル形式）**: Windows OSで実行ファイルやDLLなどに採用されている標準のプログラムファイル形式。

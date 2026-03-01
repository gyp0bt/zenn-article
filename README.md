# zenn-article

Zenn向けブログ記事の執筆・公開リポジトリ。技術基調の重厚感と知的探求のワクワク感を主軸とした連載コラムを展開する。

## デプロイ

`articles/` および `books/` ディレクトリの `.md` ファイルが、ファイル名ベースのURLマッピングでZennに自動デプロイされる。

- 記事URL: `https://zenn.dev/gyp0bt/articles/{ファイル名}`
- Zennアカウント: [gyp0bt](https://zenn.dev/gyp0bt)

## 記法

- [ZennのMarkdown記法一覧](https://zenn.dev/zenn/articles/markdown-guide)
- 数式: KaTeX（`$$` ブロック / `$` インライン）
- 図表: mermaid記法

## 連載一覧

### 梁梁接触シリーズ

有限要素法における梁梁接触の定式化と数値安定性を探究する連載。

| # | タイトル | 状態 |
|---|---------|------|
| 1 | [なぜ梁接触は壊れやすいのか？](https://zenn.dev/gyp0bt/articles/beam-beam-contact-1-why-fragile) | 下書き |
| 2 | [PTP接触はなぜ数値的に破綻しやすいのか](https://zenn.dev/gyp0bt/articles/beam-beam-contact-2-ptp-structural-issues) | 下書き |

### テニススクールの最適球拾い問題（計画中）

テニススクールにおけるボール拾いの収集効率とエネルギー効率の最適化問題。

### 伊能忠敬計画（計画中）

マッチングアプリの全国カバレッジ最適化 — 被覆問題と巡回セールスマン問題の融合。

## ドキュメント

- [CLAUDE.md](./CLAUDE.md) — AI向けコーディング規約
- [ロードマップ](./docs/roadmap.md) — 全体ロードマップ
- [ステータスインデックス](./docs/status/status-index.md) — 実装ブリーフ一覧

## 開発運用

CodexとClaude Codeの2交代制。詳細は [CLAUDE.md](./CLAUDE.md) を参照。

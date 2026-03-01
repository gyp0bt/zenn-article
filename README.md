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

### テニススクールの最適球拾い問題（執筆中）

テニススクールにおけるボール拾いの収集効率とエネルギー効率の最適化問題。

| 記事 | テーマ | 状態 |
|------|--------|------|
| [#1 問題設定とモデル化](./articles/tennis-ball-picking-1-modeling.md) | コートの幾何、ボール分布、スタイルの定式化 | 執筆済（未公開） |
| #2 エネルギーモデル | 歩行・屈伸・運搬のエネルギーコスト定式化 | 計画中 |
| #3 収集効率解析 | 各スタイルの時間効率シミュレーション | 計画中 |
| #4 最適フォーメーション | 複数人での協調戦略と数理最適解の導出 | 計画中 |
| #5 強化学習エージェントの設計 | 環境定義、報酬設計、単体エージェント訓練 | 計画中 |
| #6 最強の球拾いチーム | マルチエージェントRL、数理解との比較 | 計画中 |

- [詳細仕様書](./docs/specs/tennis-ball-picking-spec.md)
- [シミュレーションコード](./simulations/tennis_ball_picking/)

### 伊能忠敬計画（計画中）

マッチングアプリの全国カバレッジ最適化 — 被覆問題と巡回セールスマン問題の融合。

- [詳細仕様書](./docs/specs/inou-tadataka-spec.md)

## ドキュメント

- [CLAUDE.md](./CLAUDE.md) — AI向けコーディング規約
- [ロードマップ](./docs/roadmap.md) — 全体ロードマップ
- [ステータスインデックス](./docs/status/status-index.md) — 実装ブリーフ一覧

## 開発運用

CodexとClaude Codeの2交代制。詳細は [CLAUDE.md](./CLAUDE.md) を参照。

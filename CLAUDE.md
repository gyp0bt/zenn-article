# CLAUDE.md — AI向けコーディング規約

> このファイルはCodexおよびClaude Codeが参照するプロジェクト規約です。

## プロジェクト概要

Zenn向けブログ記事の執筆・公開リポジトリ。`articles/` と `books/` 配下の `.md` ファイルがZennにデプロイされる。

## リポジトリ構造

```
zenn-article/
├── CLAUDE.md          # 本ファイル（AI向け規約）
├── README.md          # プロジェクト概要
├── articles/          # Zenn記事（.md）
├── books/             # Zenn本（.md）
├── simulations/       # シミュレーションコード（Python）
└── docs/
    ├── roadmap.md     # 全体ロードマップ
    ├── specs/         # 詳細仕様書
    │   ├── tennis-ball-picking-spec.md
    │   └── inou-tadataka-spec.md
    └── status/
        ├── status-index.md  # ブリーフインデックス
        └── status-NNN.md    # 個別実装ブリーフ
```

## 運用ルール

### 2交代制

- 本プロジェクトはCodexとClaude Codeの2交代制で運用する
- 常に相手への引き継ぎを想定し、作業記録を残す
- 実装状況は `docs/status/status-{index}.md` に記録する
- 現在の最新状況はindexが最大の `status-{index}.md` を参照する

### ブランチ・コミット

- ブランチ名: `作業者-{feature-keyword}-{hash}`
- featureごとにコミットを分ける
- statusに書いた内容はgitのcommitメッセージと整合を取る
- 1 status = 1 PR程度の粒度

### ドキュメント

- すべての設計仕様は日本語で文書化する
- すべてのmarkdown文書には原則 `README.md` へのバックリンクを貼る
- 実装とドキュメントの不整合を発見したらその場で修正するか、TODOに追加する

### Zenn記事の記法

- Zenn独自のMarkdown記法を使用する（参考: https://zenn.dev/zenn/articles/markdown-guide）
- 数式はKaTeXを使用する（`$$` ブロックまたはインライン `$`）
- 図表はASCIIではなくmermaid記法を使用する
- フロントマターにはtitle, emoji, type, topics, publishedを必ず含める
- URLマッピング: `https://zenn.dev/gyp0bt/articles/{ファイル名（拡張子なし）}`

### 記事のトーン

- 技術基調の重厚感と、知的探求を純粋に楽しむワクワク感を主軸とする
- 読み物としての読了体験を重視する

### タスク管理

- コンテキスト肥大化を防ぐため、タスクはステップバイステップに分解する
  - 例: 仕様書策定→コミット→機能単体実装→テスト→lint→status作成→コミット
- 作業完了時は README, status, roadmap を更新する
- TODOはstatusファイルに記入する
- `ruff format --check` を必ず実行する（Pythonファイルがある場合）
- 確認事項や設計上の懸念はstatusファイルに書き出す

## バックリンク

- [README.md](./README.md)
- [ロードマップ](./docs/roadmap.md)
- [ステータスインデックス](./docs/status/status-index.md)

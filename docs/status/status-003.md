# Status 003: テニス球拾い #1 記事執筆・シミュレーション基盤

> [README.md](../../README.md) へ戻る | [ステータスインデックス](./status-index.md)

## 基本情報

- **日付**: 2026-03-01
- **作業者**: Claude Code
- **ブランチ**: `claude/execute-status-todos-4YF1x`
- **対応PR**: 本ブランチからmainへマージ予定

## 作業内容

### 実施事項

1. **シミュレーション基盤コード実装**
   - `simulations/tennis_ball_picking/court.py`: ITF公式規格に基づくコートジオメトリ（CourtGeometryクラス）
   - `simulations/tennis_ball_picking/distribution.py`: ガウス混合モデルによるボール分布（ストローク練習モデル・ボレー練習モデル）
   - ユニットテスト14件すべてパス
2. **テニス球拾い #1 記事執筆** — `articles/tennis-ball-picking-1-modeling.md`
   - 問題設定と動機（TSP、多目的最適化、協調戦略の側面）
   - コートジオメトリの定義（ITF公式規格準拠、有効領域669 m²）
   - ガウス混合モデルによるボール分布の定式化（5ゾーン）
   - 4つの拾い方スタイル（A: ラケット載せ、B: 手拾い、C: 打ち飛ばし集約、D: ホッパー巡回）の定式化
3. **ruff format --check** — 全Pythonファイルがフォーマット済みを確認

### 新規ファイル

- `simulations/tennis_ball_picking/__init__.py`
- `simulations/tennis_ball_picking/court.py`
- `simulations/tennis_ball_picking/distribution.py`
- `simulations/tennis_ball_picking/tests/__init__.py`
- `simulations/tennis_ball_picking/tests/test_court.py`
- `simulations/tennis_ball_picking/tests/test_distribution.py`
- `articles/tennis-ball-picking-1-modeling.md`

## TODO

- [ ] テニス球拾い #2 記事執筆（エネルギーモデル）
- [ ] エネルギーモデル実装（energy.py）
- [ ] 拾い方スタイル実装（styles.py）
- [ ] ボール分布の可視化コード（visualize.py）— 記事 #1 の図表生成用
- [ ] 伊能忠敬 #1 記事執筆開始
- [ ] 国土数値情報・人口メッシュデータの取得・前処理パイプライン構築
- [ ] Zenn CLIの導入検討
- [ ] GitHub Actions CI/CD の設定（ruff format --check 自動実行など）

## 備考・懸念

- GitHub Actions のワークフロー設定（`.github/workflows/`）が未存在。CI/CDは未設定の状態
- 記事 #1 は `published: false` で作成済み。レビュー後に公開フラグを変更予定
- 記事内のコード断片と `simulations/` 配下の実装コードの整合性を維持する運用が必要
- テニス球拾い仕様書のTODO（§10）にあった「コート可視化コード実装」は次回以降に回す

## 開発運用の所感

- 効果的: 仕様書を先に策定してから記事・コードを実装する流れがスムーズに機能
- 効果的: テストを先に書いてから実装を確認するアプローチがコード品質を担保
- 注意点: 記事のコード断片は実装コードの抜粋であり、記事更新時に実装コードとの不整合に注意が必要
- 注意点: `gh` CLI が環境に未インストールのため、GitHub Actions の確認が困難だった

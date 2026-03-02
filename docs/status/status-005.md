# Status 005: テニス球拾い #3 収集効率解析・パレートフロント

> [README.md](../../README.md) へ戻る | [ステータスインデックス](./status-index.md)

## 基本情報

- **日付**: 2026-03-02
- **作業者**: Claude Code
- **ブランチ**: `claude/execute-status-todos-LdUna`
- **対応PR**: 本ブランチからmainへマージ予定

## 作業内容

### 実施事項

1. **経路最適化コード実装** — `simulations/tennis_ball_picking/optimizer.py`
   - Greedy nearest neighbor（容量制約付き経路構築）
   - 2-opt 局所探索による経路改善
   - 時間・エネルギー同時計算のシミュレーション（`simulate_collection`）
   - 全スタイル比較関数（`compare_styles`）
   - パレートフロント抽出（`extract_pareto_front`）
   - ボール数感度分析（`sensitivity_analysis`）
   - テスト20件すべてパス

2. **テニス球拾い #3 記事執筆** — `articles/tennis-ball-picking-3-efficiency.md`
   - 経路最適化問題の設定（CVRPとしての定式化）
   - Greedy + 2-opt の解法と改善効果分析
   - 4スタイルの総合性能比較（時間・エネルギー）
   - パレートフロント導出（Style C, Dが支配的）
   - 感度分析: ボール数（50/100/150球）、分布パターン（ストローク/ボレー）
   - 考察: 現実とシミュレーション結果の乖離

3. **仕様書TODO更新**
4. **ruff format --check / ruff check** — 全Pythonファイルがクリーン
5. **全テスト68件パス**（既存48件 + 新規20件）

### 新規ファイル

- `simulations/tennis_ball_picking/optimizer.py`
- `simulations/tennis_ball_picking/tests/test_optimizer.py`
- `articles/tennis-ball-picking-3-efficiency.md`

### シミュレーション結果サマリ

- Style C（打ち飛ばし）とD（ホッパー）がパレートフロントを独占
- Style A, Bは両目的で支配される
- 結論はボール数・分布パターンに対して頑健
- 2-opt改善効果は容量の大きいスタイルほど大きい（最大8.3%）

## TODO

- [ ] テニス球拾い #4 記事執筆（最適フォーメーション・領域分割）
- [ ] 協調戦略実装（formation.py）— ボロノイ分割・密度ベース分割
- [ ] 伊能忠敬 #1 記事執筆開始
- [ ] 国土数値情報・人口メッシュデータの取得・前処理パイプライン構築
- [ ] Zenn CLIの導入検討
- [ ] 可視化コードの日本語フォント対応（環境依存; matplotlibのフォント設定）
- [ ] 記事 #1〜#3 のレビュー・公開フラグ変更

## 備考・懸念

- 記事 #3 は `published: false` で作成済み。レビュー後に公開フラグを変更予定
- optimizer.pyの2-opt実装はO(n²)の素朴な実装。100球程度では問題ないが、ボール数が大幅に増えた場合は高速化が必要
- sensitivity_analysisは試行数×ボール数×スタイル数で計算量が増加。n_trials=10, 4スタイル, 4ボール数で約2分程度
- Style Cの「打ち飛ばし」モデルは簡略化されており、着地精度のばらつき（σ=3m）をフェーズ2で反映していない。#4以降で改善の余地あり

## 開発運用の所感

- 効果的: optimizer.py → テスト → 記事のステップバイステップが安定的に機能
- 効果的: シミュレーション結果を先に取得してから記事に反映する流れが、数値の正確性を担保
- 効果的: featureごとのコミット分割（optimizer.py, 記事）が差分の追跡を容易にする
- 注意点: 感度分析の計算が重い（5試行でも2分程度）。CIで実行する場合はタイムアウトに注意

## バックリンク

- [README.md](../../README.md)
- [ロードマップ](../roadmap.md)
- [ステータスインデックス](./status-index.md)

# Status 005: テニス球拾い #3 収集効率解析・パレートフロント

> [README.md](../../README.md) へ戻る | [ステータスインデックス](./status-index.md)

## 基本情報

- **日付**: 2026-03-02
- **作業者**: Claude Code
- **ブランチ**: `claude/tennis-ball-collection-41kDO`
- **対応PR**: 本ブランチからmainへマージ予定

## 作業内容

### 実施事項

1. **ロードマップ更新**
   - テニス球拾い連載（#1〜#6）完了後に伊能忠敬計画（#1〜#7）に移行する実行順序を明記
   - v0.5〜v0.15の全マイルストーンを展開

2. **経路最適化モジュール実装** — `simulations/tennis_ball_picking/optimizer.py`
   - Greedy最近傍法（greedy_nearest_neighbor）: O(N²)の訪問順序決定
   - 2-opt局所探索（two_opt_improve）: トリップ内の経路改善
   - 経路評価関数（evaluate_route）: 時間・エネルギーの同時計算
   - スタイル比較（compare_styles）: 複数スタイルの一括比較
   - パレートフロント生成（pareto_front）: 速度変化による時間vsエネルギートレードオフ
   - テスト28件すべてパス

3. **感度分析モジュール実装** — `simulations/tennis_ball_picking/sensitivity.py`
   - ボール数スイープ（sweep_n_balls）
   - 分布パターン比較（sweep_distribution）: ストローク vs ボレー
   - カゴ位置感度（sweep_basket_position）
   - モンテカルロ分散評価（monte_carlo_variance）: 配置ランダム性の影響
   - テスト12件すべてパス

4. **テニス球拾い #3 記事執筆** — `articles/tennis-ball-picking-3-efficiency.md`
   - Greedy法と2-opt局所探索の実装解説
   - 4スタイルの定量比較（100球ストローク練習分布）
   - パレートフロントの構造分析（D > A > B の階層）
   - 感度分析: ボール数・分布パターン・配置ランダム性
   - 主要知見: ホッパー最強、屈伸が支配的、2-opt効果は容量依存

5. **ruff format --check / ruff check** — 全Pythonファイルクリーン
6. **全テスト88件パス**（前回48件 → 今回88件: +40件追加）

### 新規ファイル

- `simulations/tennis_ball_picking/optimizer.py`
- `simulations/tennis_ball_picking/sensitivity.py`
- `simulations/tennis_ball_picking/tests/test_optimizer.py`
- `simulations/tennis_ball_picking/tests/test_sensitivity.py`
- `articles/tennis-ball-picking-3-efficiency.md`

### 主要シミュレーション結果（100球、ストローク練習分布）

| スタイル | 時間 | エネルギー | トリップ数 |
|---------|------|-----------|-----------|
| Style A（ラケット載せ）| 897秒 | 204 kJ | 20 |
| Style B（手拾い直行）| 912秒 | 274 kJ | 34 |
| Style C（打ち飛ばし）| 347秒 | 23 kJ | 1 |
| Style D（ホッパー）| 310秒 | 26 kJ | 2 |

## TODO

- [ ] テニス球拾い #4 記事執筆（最適フォーメーション・協調戦略）
- [ ] 協調戦略コード実装（formation.py）— 領域分割アルゴリズム
- [ ] 記事 #1〜#3 の Zenn公開レビュー・公開フラグ変更
- [ ] 伊能忠敬 #1 記事執筆開始（テニス連載完了後）
- [ ] 国土数値情報・人口メッシュデータの取得・前処理パイプライン構築（テニス連載完了後）
- [ ] Zenn CLIの導入検討
- [ ] 可視化コードの日本語フォント対応（環境依存; matplotlibのフォント設定）
- [ ] 記事内コード断片と実装コードの整合性チェック（#1〜#3）

## 備考・懸念

- GitHub Actions の CI は mainブランチで正常動作確認済み（2件とも成功）
- 記事 #3 は `published: false` で作成済み。レビュー後に #1〜#3 を一括公開予定
- パレートフロント図はmermaid xychart-betaで描画。Zennのmermaidサポート範囲の確認が必要
- Style C の2フェーズモデルは打ち飛ばし→集約の2段階だが、現在の optimizer.py では1フェーズ（集約済み前提）として扱っている。Phase 1 のモデル化は #4 以降で検討

## 開発運用の所感

- 効果的: optimizer.py → test → sensitivity.py → test → 記事 → ruff/pytest のステップバイステップが安定的に機能
- 効果的: シミュレーション結果の数値を先に取得してから記事を書くことで、記事とコードの整合性が保たれる
- 効果的: GitHub Actions CIが正常稼働し、mainブランチの品質が保証されている
- 注意点: 記事のmermaidチャートの数値はシミュレーション結果の概数であり、厳密な値ではない（可視化の都合で丸めている）

## バックリンク

- [README.md](../../README.md)
- [ロードマップ](../roadmap.md)
- [ステータスインデックス](./status-index.md)

# Status 006: 球拾いモデル軌道修正 — 4カゴ・クロスDTL分布・Style B/C再定義

> [README.md](../../README.md) へ戻る | [ステータスインデックス](./status-index.md)

## 基本情報

- **日付**: 2026-03-02
- **作業者**: Claude Code
- **ブランチ**: `claude/optimize-ball-collection-AR6yQ`
- **対応PR**: 本ブランチからmainへマージ予定

## 作業内容

### 概要

ユーザーのフィードバックに基づき、球拾いシミュレーションの物理モデルを実際の練習環境に近づける軌道修正を実施。主に以下の3つの軸で変更を行った。

### 実施事項

1. **仕様書軌道修正** — `docs/specs/tennis-ball-picking-spec.md`
   - §3.3 クロス・ダウンザライン分布モデル新設: コーナー集中（50%）・ネットミス帯（20%）
   - §3.4 カゴ配置の再定義: 1カゴ→4カゴ（配置自由、k-medians最適化）+ 中央カート
   - §4 Style B: 手拾い直行→しゃがみ移動・カゴ持ち（容量50球、速度0.7m/s、拾い1.0秒/球）
   - §4 Style C: 打ち飛ばし2フェーズの明確化 + 打ち飛ばし比率α最適化（補題）
   - §7.2 デフォルトパラメータ: N=200球、K=4カゴ、分布=クロスDTL

2. **クロス・ダウンザライン分布実装** — `distribution.py`
   - `create_cross_dtl_distribution()`: 6ゾーンGMM（左右クロスコーナー各25%、左右DTL各10%、ネットミス20%、バックフェンス10%）
   - テスト7件追加（重み合計、ゾーン数、サンプリング、コーナー集中検証、ネットミスゾーン検証、再現性）

3. **カゴ配置モデル新規実装** — `basket.py`（新規ファイル）
   - `BasketConfig`: 4カゴ・容量50球・カート戻し時間10秒
   - `assign_balls_to_baskets()`: 最近傍カゴ割り当て
   - `optimize_basket_placement()`: k-medians + k-means++初期化
   - `compute_basket_distances()`, `total_basket_distance()`: 評価関数
   - テスト14件（BasketConfig、割り当て、最適化、距離計算）

4. **Style B/C再定義** — `styles.py`
   - Style B: 容量3球→50球、速度1.3→0.7m/s、拾い時間2.0→1.0秒/球
   - Style C: `style_c_phase1()`新設（打ち飛ばしフェーズ専用）
   - `estimate_mixed_style_c_time()`: 打ち飛ばしα混合戦略の時間推定
   - `optimize_hit_ratio()`: α最適値のグリッドサーチ
   - テスト25件（旧18件を更新 + 7件追加）

5. **経路最適化の複数カゴ対応** — `optimizer.py`
   - `MultiBasketResult`: 複数カゴ結果データクラス
   - `optimize_multi_basket()`: カゴ別経路最適化 + カート戻しコスト
   - テスト33件（旧28件 + 5件追加）

6. **ruff format --check / ruff check** — 全Pythonファイルクリーン
7. **全テスト121件パス**（前回88件 → 今回121件: +33件追加）

### 新規ファイル

- `simulations/tennis_ball_picking/basket.py`
- `simulations/tennis_ball_picking/tests/test_basket.py`

### 変更ファイル

- `docs/specs/tennis-ball-picking-spec.md` — §3.3, §3.4, §4, §7.2, §10 軌道修正
- `simulations/tennis_ball_picking/distribution.py` — `create_cross_dtl_distribution()` 追加
- `simulations/tennis_ball_picking/styles.py` — Style B/C再定義、打ち飛ばし比率最適化
- `simulations/tennis_ball_picking/optimizer.py` — 複数カゴ対応
- `simulations/tennis_ball_picking/tests/test_distribution.py` — +7件
- `simulations/tennis_ball_picking/tests/test_styles.py` — 全面更新 +7件
- `simulations/tennis_ball_picking/tests/test_optimizer.py` — +5件

### モデル変更の根拠

| 変更 | 旧モデル | 新モデル | 根拠 |
|------|----------|----------|------|
| ボール分布 | コート全体にガウス的散布 | コーナー集中（クロス/DTL） | 球出し練習はクロスかDTLへの配球が主 |
| カゴ数 | 1（中央固定） | 4（配置自由） | 実際のスクールでは4カゴを使用 |
| Style B | 手で3球持って往復 | しゃがみ移動でカゴ持ち巡回 | 実際のスクールの一般的なスタイル |
| Style C | 打ち飛ばし→自動回収 | 打ち飛ばし→手拾いorラケット載せ | 打ち飛ばし後の回収が必要（特殊型） |

### パラメータ精緻化（ユーザーフィードバック第2弾）

ユーザーの実体験に基づき、以下のパラメータを修正:

| パラメータ | 旧値 | 新値 | 根拠 |
|-----------|------|------|------|
| Style A 容量 | 5球 | 6球 | 3段ピラミッド（底3-4+中2+頂1） |
| Style A 運搬速度 | 0.9 m/s | 0.7 m/s | ピラミッド不安定で慎重歩行が必要 |
| Style A γ | 0.04 | 0.05 | 積載増でさらに不安定化 |
| Style B pick_time | 1.0 秒/球 | 0.4 秒/球 | 両手で2〜3個/秒の投入ペース |

**体感速度序列**: C+B混合 > B単独 > A（最遅）。Style D（ホッパー）は理論上最速だがスクール未設置。

## TODO

- [ ] 記事 #1〜#3 の内容をモデル軌道修正に合わせて更新（特にStyle Bの説明）
- [ ] 4カゴ + クロスDTL分布での定量シミュレーション実行・記事反映
- [ ] 打ち飛ばし比率αの最適値を各分布パターンで評価
- [ ] テニス球拾い #4 記事執筆（最適フォーメーション・協調戦略）
- [ ] 協調戦略コード実装（formation.py）— 領域分割アルゴリズム
- [ ] 記事 #1〜#3 の Zenn公開レビュー・公開フラグ変更

## 備考・懸念

- **後方互換性**: `style_c()` は `style_c_phase1()` を返すため、既存の optimizer/sensitivity コードはそのまま動作する
- **Style B の破壊的変更**: 旧Style B（容量3球）に依存するテスト・記事は今回一括修正。既存記事 #1〜#3 のStyle B記述は未更新（TODO）
- **打ち飛ばし比率最適化**: `optimize_hit_ratio()` は Greedy推定ベースの簡易版。厳密解にはGrid探索の粒度を上げるか、勾配ベース最適化が必要
- **カゴ配置最適化**: k-medians は局所解に陥る可能性あり。複数初期値からの実行が推奨
- GitHub Actions CI: mainブランチで全4件成功確認済み

## 開発運用の所感

- 効果的: ユーザーのドメイン知識フィードバックを仕様書→コード→テストの順で反映する流れが安定的に機能
- 効果的: 既存テストがあることで Style B の破壊的変更の影響範囲を即座に特定できた
- 注意点: 記事内容とコードの乖離が蓄積している（#1〜#3の記述が旧Style B基準）。次回作業で一括更新が必要

## バックリンク

- [README.md](../../README.md)
- [ロードマップ](../roadmap.md)
- [ステータスインデックス](./status-index.md)

# Status 008: 問題設定修正 — ボール物理・Style A容量・カート運用モデル

> [README.md](../../README.md) へ戻る | [ステータスインデックス](./status-index.md)

## 基本情報

- **日付**: 2026-03-03
- **作業者**: Claude Code
- **ブランチ**: `claude/fix-ball-physics-cart-wUOIX`
- **対応PR**: 本ブランチからmainへマージ予定

## 作業内容

### 概要

問題設定の3つの重大な誤りを修正し、記事#1を書き直した。

1. **ボール分布モデル**: 打ったボールはコート枠で停止しない。バウンドしてバックフェンスまで転がり、跳ね返って戻る物理を追加。
2. **Style A容量**: 6球 → 20球に修正。γも0.05 → 0.02に調整。
3. **カート・カゴ運用**: カートは移動可能。いっぱいのカゴはカートに戻す（ボールは空にせず、カゴごと載せる）。空きカゴが1つ減る。

### 実施事項

#### 1. ボール転がり物理モデル（distribution.py）
- `apply_ball_rolling()` 関数を新規追加
- GMMはボールの「着地位置」、転がり補正後が「最終静止位置」の2段階パイプライン
- 通常球: 打球方向に指数分布（平均3m）で転がる
- ネットミス球: 転がりが少ない（平均1m）
- フェンス到達時: 跳ね返り（平均0.5m）で停止
- 結果: バックフェンス際にボールが集中する現実的な分布を再現

#### 2. Style A パラメータ修正（styles.py）
- capacity: 6 → 20（慣れた人で約20球を一度に運搬可能）
- gamma: 0.05 → 0.02（20球満載時 v(20)=0.42 m/s）

#### 3. カート・カゴ運用モデル修正（basket.py, optimizer.py）
- `assign_balls_to_baskets_with_capacity()` 追加: 容量制約付きカゴ割り当て
- `optimize_multi_basket()` のカート戻しロジック変更:
  - 旧: カゴ容量超過時にdump & refill（カゴ再利用）
  - 新: カゴ1つにつき1回カートに戻す（カゴ使い捨て）
- BasketConfig.dump_time: カゴ→カート搬送時間に意味変更

#### 4. テスト
- `TestApplyBallRolling`: 6テスト追加（shape, 空入力, 有効範囲, フェンス寄り, 再現性, ネットミス転がり少）
- `TestAssignBallsWithCapacity`: 4テスト追加（容量遵守, 全割当, 最近傍優先, 溢れ再割当）
- Style A テスト: capacity=20, gamma=0.02に更新
- optimizer dump テスト: カゴ戻しモデルに更新
- **131テスト全パス**

#### 5. 記事#1 書き直し
- ボール分布セクション: 「着地してからが本番」— 転がり物理の解説を新設
- カゴ・カート運用: 「カゴの使い捨てモデル」セクションを新設
- Style A: 容量20球、速度低下式の解説
- まとめ: 転がり物理・移動式カート・カゴ使い捨てを反映

#### 6. 仕様書更新
- tennis-ball-picking-spec.md: Style A, カート運用, γ値を修正

## 変更ファイル

| ファイル | 変更内容 |
|---------|----------|
| `simulations/tennis_ball_picking/distribution.py` | `apply_ball_rolling()` 追加 |
| `simulations/tennis_ball_picking/styles.py` | Style A: capacity=20, γ=0.02 |
| `simulations/tennis_ball_picking/basket.py` | `assign_balls_to_baskets_with_capacity()` 追加、ドキュメント更新 |
| `simulations/tennis_ball_picking/optimizer.py` | 容量制約付き割り当て使用、カゴ使い捨てモデル |
| `simulations/tennis_ball_picking/tests/test_distribution.py` | 転がりテスト6件追加 |
| `simulations/tennis_ball_picking/tests/test_basket.py` | 容量制約割り当てテスト4件追加 |
| `simulations/tennis_ball_picking/tests/test_styles.py` | Style Aパラメータ更新 |
| `simulations/tennis_ball_picking/tests/test_optimizer.py` | カゴ戻しテスト更新 |
| `articles/tennis-ball-picking-1-modeling.md` | 全面書き直し |
| `docs/specs/tennis-ball-picking-spec.md` | Style A, カート運用修正 |

## テスト結果

```
131 passed in 13.68s
ruff format --check: 17 files already formatted
```

## TODO

- [ ] 記事#2, #3 のStyle A容量・カート運用記述を修正（本PRのスコープ外）
- [ ] 転がりモデルのパラメータ感度分析を記事#3に追加検討
- [ ] カート最適配置の検討（現在はデフォルトのネット脇）

## バックリンク

- [README.md](../../README.md)
- [ロードマップ](../roadmap.md)
- [ステータスインデックス](./status-index.md)

# Status 002: 詳細仕様書策定・プロジェクト再編

> [README.md](../../README.md) へ戻る | [ステータスインデックス](./status-index.md)

## 基本情報

- **日付**: 2026-03-01
- **作業者**: Claude Code
- **ブランチ**: `claude/create-project-specs-eI4BC`
- **対応PR**: 本ブランチからmainへマージ予定

## 作業内容

### 実施事項

1. **旧REAMDE.md削除** — タイポのまま残っていた旧ファイルを削除
2. **梁梁接触シリーズの削除** — 別プロジェクトへ移行のため、記事2本とREADME/roadmapからの参照を削除
   - `articles/beam-beam-contact-1-why-fragile.md` 削除
   - `articles/beam-beam-contact-2-ptp-structural-issues.md` 削除
3. **テニス球拾い問題の詳細仕様書策定** — `docs/specs/tennis-ball-picking-spec.md`
   - 全6記事構成（前半: 数理最適化、後半: 強化学習）
   - コートジオメトリ、ボール分布のガウス混合モデル
   - 4種の拾い方スタイルのパラメータ定式化
   - 中程度粒度のエネルギーモデル（歩行・屈伸・運搬 + 累積疲労）
   - 個人最適化（TSP系）・協調最適化（領域分割）の定式化
   - 強化学習: Gymnasium環境設計、単体PPO/SAC、MARL（CTDE）
4. **伊能忠敬計画の詳細仕様書策定** — `docs/specs/inou-tadataka-spec.md`
   - 全7記事構成（第一段階: 静的被覆、第二段階: 動的巡回）
   - 2021年先行実験の3課題: 幾何的被覆ギャップ、ユーザー再生成、地域差
   - 静的集合被覆 → 動的パトロール問題への発展
   - ユーザー蓄積の微分方程式モデル、均衡条件の導出
5. **README.md更新** — 梁梁接触を削除、仕様書リンクを追加
6. **roadmap.md更新** — 記事構成を最新に更新、マイルストーン更新

### 新規ファイル

- `docs/specs/tennis-ball-picking-spec.md`
- `docs/specs/inou-tadataka-spec.md`

### 削除ファイル

- `REAMDE.md`
- `articles/beam-beam-contact-1-why-fragile.md`
- `articles/beam-beam-contact-2-ptp-structural-issues.md`

## TODO

- [ ] テニス球拾い #1 記事執筆開始
- [ ] テニス球拾いシミュレーション基盤コード（court.py, distribution.py）
- [ ] 伊能忠敬 #1 記事執筆開始
- [ ] 国土数値情報・人口メッシュデータの取得・前処理パイプライン構築
- [ ] Zenn CLIの導入検討

## 備考・懸念

- 伊能忠敬計画の設計上の懸念:
  - Tinderの所在地変更頻度制限の有無（Tinder Passport課金要否）
  - 先行実験のログデータの残存状況 → 再生成レート推定精度に影響
  - 記事内でのTinder API/スクレイピング記述の範囲 → 利用規約との兼ね合い
- テニス球拾い: RL部分（#5-6）は数理最適化部分（#1-4）完了後に着手が望ましい
- 2プロジェクトとも記事数が多い（テニス6本、伊能忠敬7本）ため、並行ではなく直列で進めることを推奨

## 開発運用の所感

- 効果的: ユーザーとの対話で先行実験の情報を引き出し、仕様書の精度を大幅に向上できた
- 効果的: statusファイルのTODOを起点とした作業開始フローが機能している
- 注意点: 仕様書策定は対話的に進めるとコンテキストが肥大化しやすい。仕様書策定→コミットで区切るのが良い

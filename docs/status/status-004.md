# Status 004: テニス球拾い #2 エネルギーモデル・基盤拡張

> [README.md](../../README.md) へ戻る | [ステータスインデックス](./status-index.md)

## 基本情報

- **日付**: 2026-03-01
- **作業者**: Claude Code
- **ブランチ**: `claude/execute-status-todos-vrS4j`
- **対応PR**: 本ブランチからmainへマージ予定

## 作業内容

### 実施事項

1. **GitHub Actions CI/CD ワークフロー設定**
   - `.github/workflows/ci.yml`: ruff format --check, ruff lint, pytest を自動実行
   - push to main / PR to main で発火

2. **エネルギーモデル実装** — `simulations/tennis_ball_picking/energy.py`
   - 歩行コスト: 速度依存2次関数 c_walk(v) = α₀ + α₁v + α₂v²
   - 屈伸コスト: 累積疲労モデル E_bend^(n) = E_base·(1+β·n)
   - 運搬コスト: 姿勢制御を考慮した荷重モデル
   - 速度低下モデル: v(k) = v₀·(1-γ·k)
   - テスト16件すべてパス

3. **拾い方スタイル実装** — `simulations/tennis_ball_picking/styles.py`
   - Style A: ラケット載せ運搬（容量5球、運搬速度0.9m/s）
   - Style B: 手拾い直行（容量3球、速度1.3m/s）
   - Style C: ラケット打ち飛ばし集約（2フェーズ）
   - Style D: ホッパー巡回（容量72球、屈伸不要）
   - greedy nearest neighbor による推定時間計算
   - テスト18件すべてパス

4. **可視化コード実装** — `simulations/tennis_ball_picking/visualize.py`
   - コートライン描画 (draw_court)
   - ボール分布プロット (plot_ball_distribution)
   - 分布比較プロット (plot_distribution_comparison)
   - エネルギープロファイル棒グラフ (plot_energy_profile)

5. **テニス球拾い #2 記事執筆** — `articles/tennis-ball-picking-2-energy.md`
   - 歩行のエネルギーコストの物理学
   - 屈伸動作の累積疲労モデル
   - 運搬コストと速度低下モデル
   - 4スタイルのエネルギープロファイル比較
   - 支配的コストの分析（屈伸が35〜44%を占める）

6. **ruff format --check / ruff check** — 全Pythonファイルがクリーンを確認
7. **全テスト48件パス**

### 新規ファイル

- `.github/workflows/ci.yml`
- `simulations/tennis_ball_picking/energy.py`
- `simulations/tennis_ball_picking/styles.py`
- `simulations/tennis_ball_picking/visualize.py`
- `simulations/tennis_ball_picking/tests/test_energy.py`
- `simulations/tennis_ball_picking/tests/test_styles.py`
- `articles/tennis-ball-picking-2-energy.md`

## TODO

- [ ] テニス球拾い #3 記事執筆（収集効率解析・パレートフロント）
- [ ] 経路最適化コード実装（optimizer.py）— TSPソルバーとgreedy法の比較
- [ ] ボール配置の感度分析コード
- [ ] 伊能忠敬 #1 記事執筆開始
- [ ] 国土数値情報・人口メッシュデータの取得・前処理パイプライン構築
- [ ] Zenn CLIの導入検討
- [ ] 可視化コードの日本語フォント対応（環境依存; matplotlibのフォント設定）

## 備考・懸念

- GitHub Actions は新規設定のため、mainへの初回マージ後に動作確認が必要
- 記事 #2 は `published: false` で作成済み。レビュー後に公開フラグを変更予定
- 可視化コードは日本語フォント未インストール環境ではラベルが□に化ける（matplotlibのデフォルトフォント問題）。CIでは無視可能だが、図表生成時はフォント設定が必要
- `gh` CLIが環境に未インストールのため、GitHub Actionsの詳細なエラー確認はwebfetch経由で行った

## 開発運用の所感

- 効果的: ステップバイステップ（energy.py → styles.py → visualize.py → 記事 → lint修正）のアプローチが安定的に機能
- 効果的: 各ステップでruff format/checkとpytestを回すことで、最後にまとめてlint修正する量が少なくて済む
- 効果的: 仕様書§5のエネルギーモデル定式化がそのままコードと記事に直結し、整合性が保たれた
- 注意点: 記事内のコード断片は実装コードの要約版であり、パラメータの追加・変更時に乖離しやすい

## バックリンク

- [README.md](../../README.md)
- [ロードマップ](../roadmap.md)
- [ステータスインデックス](./status-index.md)

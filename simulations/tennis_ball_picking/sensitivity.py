"""感度分析モジュール.

ボール数・分布パターン・カゴ位置などのパラメータ変動に対する
収集効率（時間・エネルギー）の感度を分析する。
記事 #3 の感度分析セクション用。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .court import CourtGeometry
from .distribution import (
    BallDistribution,
    create_stroke_distribution,
    create_volley_distribution,
)
from .energy import EnergyParams
from .optimizer import RouteResult, optimize_route
from .styles import StyleParams


@dataclass
class SensitivityResult:
    """感度分析の1データ点.

    Attributes:
        param_name: 変化させたパラメータ名
        param_value: パラメータの値
        time: 総所要時間 [秒]
        energy: 総消費エネルギー [J]
        n_trips: トリップ数
        energy_breakdown: エネルギー内訳
    """

    param_name: str
    param_value: float
    time: float
    energy: float
    n_trips: int
    energy_breakdown: dict[str, float]


def sweep_n_balls(
    n_balls_range: NDArray[np.intp],
    style: StyleParams,
    court: CourtGeometry | None = None,
    distribution: BallDistribution | None = None,
    energy_params: EnergyParams | None = None,
    seed: int = 42,
) -> list[SensitivityResult]:
    """ボール数を変化させた感度分析.

    Args:
        n_balls_range: ボール数の配列
        style: 拾い方スタイル
        court: コートジオメトリ（Noneならデフォルト）
        distribution: ボール分布（Noneならストローク練習モデル）
        energy_params: エネルギーパラメータ
        seed: 乱数シード

    Returns:
        各ボール数に対する結果のリスト
    """
    if court is None:
        court = CourtGeometry()
    if distribution is None:
        distribution = create_stroke_distribution(court)

    rng = np.random.default_rng(seed)
    basket = court.default_basket_position()
    results: list[SensitivityResult] = []

    for n in n_balls_range:
        balls = distribution.sample(int(n), court, rng=rng)
        route = optimize_route(balls, basket, style, energy_params)
        results.append(
            SensitivityResult(
                param_name="n_balls",
                param_value=float(n),
                time=route.total_time,
                energy=route.total_energy,
                n_trips=route.n_trips,
                energy_breakdown=route.energy_breakdown,
            )
        )

    return results


def sweep_distribution(
    style: StyleParams,
    n_balls: int = 100,
    court: CourtGeometry | None = None,
    energy_params: EnergyParams | None = None,
    seed: int = 42,
) -> dict[str, RouteResult]:
    """分布パターンを変えた比較分析.

    ストローク練習 vs ボレー練習を比較する。

    Returns:
        {分布名: RouteResult} の辞書
    """
    if court is None:
        court = CourtGeometry()

    rng = np.random.default_rng(seed)
    basket = court.default_basket_position()

    distributions = {
        "ストローク練習": create_stroke_distribution(court),
        "ボレー練習": create_volley_distribution(court),
    }

    results: dict[str, RouteResult] = {}
    for name, dist in distributions.items():
        balls = dist.sample(n_balls, court, rng=rng)
        results[name] = optimize_route(balls, basket, style, energy_params)

    return results


def sweep_basket_position(
    basket_offsets: NDArray[np.float64],
    style: StyleParams,
    n_balls: int = 100,
    court: CourtGeometry | None = None,
    distribution: BallDistribution | None = None,
    energy_params: EnergyParams | None = None,
    seed: int = 42,
) -> list[SensitivityResult]:
    """カゴ位置をy方向にオフセットさせた感度分析.

    ネット脇を基準に、y方向にカゴ位置をずらした場合の影響を調べる。

    Args:
        basket_offsets: y方向のオフセット配列 [m]
        style: 拾い方スタイル
        n_balls: ボール数
        court: コートジオメトリ
        distribution: ボール分布
        energy_params: エネルギーパラメータ
        seed: 乱数シード

    Returns:
        各オフセットに対する結果のリスト
    """
    if court is None:
        court = CourtGeometry()
    if distribution is None:
        distribution = create_stroke_distribution(court)

    rng = np.random.default_rng(seed)
    base_basket = court.default_basket_position()
    balls = distribution.sample(n_balls, court, rng=rng)

    results: list[SensitivityResult] = []

    for offset in basket_offsets:
        basket = base_basket.copy()
        basket[1] += offset
        route = optimize_route(balls, basket, style, energy_params)
        results.append(
            SensitivityResult(
                param_name="basket_y_offset",
                param_value=float(offset),
                time=route.total_time,
                energy=route.total_energy,
                n_trips=route.n_trips,
                energy_breakdown=route.energy_breakdown,
            )
        )

    return results


def monte_carlo_variance(
    style: StyleParams,
    n_balls: int = 100,
    n_trials: int = 20,
    court: CourtGeometry | None = None,
    distribution: BallDistribution | None = None,
    energy_params: EnergyParams | None = None,
    seed: int = 42,
) -> dict[str, dict[str, float]]:
    """モンテカルロ法でボール配置のばらつきによる結果分散を評価.

    同じ分布パラメータから複数回サンプリングし、
    時間・エネルギーの統計量（平均・標準偏差・最小・最大）を計算する。

    Args:
        style: 拾い方スタイル
        n_balls: ボール数
        n_trials: 試行回数
        court: コートジオメトリ
        distribution: ボール分布
        energy_params: エネルギーパラメータ
        seed: 乱数シード

    Returns:
        {"time": {mean, std, min, max}, "energy": {mean, std, min, max}}
    """
    if court is None:
        court = CourtGeometry()
    if distribution is None:
        distribution = create_stroke_distribution(court)

    rng = np.random.default_rng(seed)
    basket = court.default_basket_position()

    times: list[float] = []
    energies: list[float] = []

    for _ in range(n_trials):
        balls = distribution.sample(n_balls, court, rng=rng)
        route = optimize_route(balls, basket, style, energy_params)
        times.append(route.total_time)
        energies.append(route.total_energy)

    return {
        "time": {
            "mean": float(np.mean(times)),
            "std": float(np.std(times)),
            "min": float(np.min(times)),
            "max": float(np.max(times)),
        },
        "energy": {
            "mean": float(np.mean(energies)),
            "std": float(np.std(energies)),
            "min": float(np.min(energies)),
            "max": float(np.max(energies)),
        },
    }

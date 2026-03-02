"""経路最適化モジュール.

個人のボール回収経路を最適化する。
仕様書 §6.1 に基づき、時間最小化・エネルギー最小化の
2つの目的関数に対して経路探索を行う。

手法:
- Greedy法（最近傍法）: 常に最も近いボールを拾いに行く
- 2-opt改善: Greedy解を局所探索で改善する
- パレートフロント: 時間vsエネルギーの多目的最適化
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .energy import (
    EnergyParams,
    carrying_energy,
    cumulative_bending_energy,
    speed_with_load,
    walking_energy,
)
from .styles import StyleParams, pickup_time, travel_time


@dataclass
class RouteResult:
    """経路最適化の結果.

    Attributes:
        order: ボール訪問順序（インデックス配列）
        total_time: 総所要時間 [秒]
        total_energy: 総消費エネルギー [J]
        energy_breakdown: エネルギー内訳 {"walk", "bend", "carry"}
        n_trips: カゴへの往復回数
        trip_details: 各トリップの詳細情報リスト
    """

    order: NDArray[np.intp]
    total_time: float
    total_energy: float
    energy_breakdown: dict[str, float]
    n_trips: int
    trip_details: list[dict[str, float]]


def _distance(a: NDArray[np.float64], b: NDArray[np.float64]) -> float:
    """2点間のユークリッド距離."""
    return float(np.linalg.norm(a - b))


def _build_distance_matrix(
    positions: NDArray[np.float64],
    basket: NDArray[np.float64],
) -> NDArray[np.float64]:
    """距離行列を構築する.

    index 0 がカゴ位置、index 1〜N がボール位置。

    Returns:
        shape (N+1, N+1) の距離行列
    """
    all_points = np.vstack([basket.reshape(1, 2), positions])
    n = len(all_points)
    diff = all_points[:, np.newaxis, :] - all_points[np.newaxis, :, :]
    return np.sqrt(np.sum(diff**2, axis=2)).reshape(n, n)


def greedy_nearest_neighbor(
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
    style: StyleParams,
) -> list[int]:
    """最近傍法（Greedy）で訪問順序を決定.

    カゴから出発し、常に最も近い未回収ボールを拾いに行く。
    容量に達したらカゴに戻る。

    Returns:
        ボールインデックスの訪問順序リスト
    """
    n_balls = len(ball_positions)
    if n_balls == 0:
        return []

    remaining = set(range(n_balls))
    current_pos = basket_position.copy()
    order: list[int] = []
    carried = 0

    while remaining:
        # 最近傍を探す
        best_idx = -1
        best_dist = float("inf")
        for i in remaining:
            d = _distance(ball_positions[i], current_pos)
            if d < best_dist:
                best_dist = d
                best_idx = i

        order.append(best_idx)
        current_pos = ball_positions[best_idx].copy()
        remaining.remove(best_idx)
        carried += 1

        # 容量に達したらカゴに戻る
        if carried >= style.capacity and remaining:
            current_pos = basket_position.copy()
            carried = 0

    return order


def two_opt_improve(
    order: list[int],
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
    style: StyleParams,
    max_iterations: int = 100,
) -> list[int]:
    """2-opt局所探索でトリップ内の経路を改善する.

    トリップ（カゴ→ボール回収→カゴ）ごとに2-opt改善を適用する。

    Args:
        order: 初期訪問順序
        ball_positions: ボール座標
        basket_position: カゴ座標
        style: 拾い方スタイル
        max_iterations: 最大反復回数

    Returns:
        改善された訪問順序
    """
    if len(order) <= 2:
        return list(order)

    # トリップに分割
    trips = _split_into_trips(order, style.capacity)
    improved_order: list[int] = []

    for trip in trips:
        improved_trip = _two_opt_single_trip(
            trip, ball_positions, basket_position, max_iterations
        )
        improved_order.extend(improved_trip)

    return improved_order


def _split_into_trips(order: list[int], capacity: int) -> list[list[int]]:
    """訪問順序を容量ごとのトリップに分割."""
    trips: list[list[int]] = []
    for i in range(0, len(order), capacity):
        trips.append(order[i : i + capacity])
    return trips


def _two_opt_single_trip(
    trip: list[int],
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
    max_iterations: int,
) -> list[int]:
    """1トリップ内で2-opt改善を適用."""
    if len(trip) <= 2:
        return list(trip)

    best = list(trip)
    best_cost = _trip_distance(best, ball_positions, basket_position)

    for _ in range(max_iterations):
        improved = False
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                candidate = best[:i] + best[i : j + 1][::-1] + best[j + 1 :]
                cost = _trip_distance(candidate, ball_positions, basket_position)
                if cost < best_cost - 1e-10:
                    best = candidate
                    best_cost = cost
                    improved = True
        if not improved:
            break

    return best


def _trip_distance(
    trip: list[int],
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
) -> float:
    """トリップの総移動距離を計算（カゴ→ボール群→カゴ）."""
    if not trip:
        return 0.0

    total = _distance(basket_position, ball_positions[trip[0]])
    for k in range(len(trip) - 1):
        total += _distance(ball_positions[trip[k]], ball_positions[trip[k + 1]])
    total += _distance(ball_positions[trip[-1]], basket_position)
    return total


def evaluate_route(
    order: list[int],
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
    style: StyleParams,
    energy_params: EnergyParams | None = None,
) -> RouteResult:
    """訪問順序に対する時間・エネルギーを評価.

    Args:
        order: ボール訪問順序
        ball_positions: ボール座標
        basket_position: カゴ座標
        style: 拾い方スタイル
        energy_params: エネルギーパラメータ（Noneならデフォルト）

    Returns:
        RouteResult
    """
    if energy_params is None:
        energy_params = EnergyParams()

    trips = _split_into_trips(order, style.capacity)

    total_time = 0.0
    total_e_walk = 0.0
    total_e_bend = 0.0
    total_e_carry = 0.0
    cumulative_bends = 0
    trip_details: list[dict[str, float]] = []

    for trip in trips:
        n_balls = len(trip)

        # 移動距離計算
        collect_dist = 0.0
        current = basket_position.copy()
        for idx in trip:
            collect_dist += _distance(current, ball_positions[idx])
            current = ball_positions[idx].copy()
        return_dist = _distance(current, basket_position)

        # 時間計算
        t_pick = pickup_time(n_balls, style)
        t_collect = travel_time(collect_dist, 0, style)
        t_return = travel_time(return_dist, n_balls, style)
        trip_t = t_pick + t_collect + t_return
        total_time += trip_t

        # エネルギー計算
        walk_speed = style.base_speed
        e_walk = walking_energy(collect_dist, walk_speed, energy_params)

        carry_speed = speed_with_load(style.effective_carry_speed, n_balls, style.gamma)
        e_walk += walking_energy(return_dist, carry_speed, energy_params)

        if style.requires_bending:
            e_bend_before = cumulative_bending_energy(cumulative_bends, energy_params)
            e_bend_after = cumulative_bending_energy(
                cumulative_bends + n_balls, energy_params
            )
            e_bend = e_bend_after - e_bend_before
            cumulative_bends += n_balls
        else:
            e_bend = 0.0

        e_carry = carrying_energy(return_dist, n_balls, energy_params)

        total_e_walk += e_walk
        total_e_bend += e_bend
        total_e_carry += e_carry

        trip_details.append(
            {
                "n_balls": n_balls,
                "collect_distance": collect_dist,
                "return_distance": return_dist,
                "time": trip_t,
                "energy_walk": e_walk,
                "energy_bend": e_bend,
                "energy_carry": e_carry,
            }
        )

    total_energy = total_e_walk + total_e_bend + total_e_carry

    return RouteResult(
        order=np.array(order),
        total_time=total_time,
        total_energy=total_energy,
        energy_breakdown={
            "walk": total_e_walk,
            "bend": total_e_bend,
            "carry": total_e_carry,
        },
        n_trips=len(trips),
        trip_details=trip_details,
    )


def optimize_route(
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
    style: StyleParams,
    energy_params: EnergyParams | None = None,
    use_2opt: bool = True,
    max_2opt_iterations: int = 100,
) -> RouteResult:
    """Greedy + 2-opt で経路を最適化.

    Args:
        ball_positions: shape (N, 2) のボール座標
        basket_position: shape (2,) のカゴ座標
        style: 拾い方スタイル
        energy_params: エネルギーパラメータ
        use_2opt: 2-opt改善を適用するか
        max_2opt_iterations: 2-opt最大反復回数

    Returns:
        RouteResult
    """
    order = greedy_nearest_neighbor(ball_positions, basket_position, style)

    if use_2opt and len(order) > 2:
        order = two_opt_improve(
            order,
            ball_positions,
            basket_position,
            style,
            max_iterations=max_2opt_iterations,
        )

    return evaluate_route(order, ball_positions, basket_position, style, energy_params)


def compare_styles(
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
    styles: dict[str, StyleParams],
    energy_params: EnergyParams | None = None,
    use_2opt: bool = True,
) -> dict[str, RouteResult]:
    """複数スタイルの経路最適化結果を比較.

    Args:
        ball_positions: ボール座標
        basket_position: カゴ座標
        styles: {スタイル名: パラメータ} の辞書
        energy_params: エネルギーパラメータ
        use_2opt: 2-opt改善を適用するか

    Returns:
        {スタイル名: RouteResult} の辞書
    """
    results = {}
    for name, style in styles.items():
        results[name] = optimize_route(
            ball_positions, basket_position, style, energy_params, use_2opt
        )
    return results


def pareto_front(
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
    style: StyleParams,
    energy_params: EnergyParams | None = None,
    speed_factors: NDArray[np.float64] | None = None,
) -> list[dict[str, float]]:
    """速度パラメータを変化させてパレートフロントを生成.

    移動速度を変えることで、時間とエネルギーのトレードオフを探索する。
    速度が遅いほどエネルギー効率は良いが時間がかかり、
    速度が速いほど時間は短いがエネルギー消費が増える。

    Args:
        ball_positions: ボール座標
        basket_position: カゴ座標
        style: 基準スタイル
        energy_params: エネルギーパラメータ
        speed_factors: 速度倍率の配列（デフォルト: 0.5〜1.5を20分割）

    Returns:
        パレートフロントの点リスト [{"time", "energy", "speed_factor"}, ...]
    """
    if speed_factors is None:
        speed_factors = np.linspace(0.5, 1.5, 20)

    points: list[dict[str, float]] = []

    for factor in speed_factors:
        # 速度を変化させたスタイルパラメータを作成
        modified_style = StyleParams(
            style_type=style.style_type,
            capacity=style.capacity,
            base_speed=style.base_speed * factor,
            carry_speed=(
                style.carry_speed * factor if style.carry_speed is not None else None
            ),
            pick_time=style.pick_time,
            gamma=style.gamma,
            requires_bending=style.requires_bending,
        )

        result = optimize_route(
            ball_positions, basket_position, modified_style, energy_params
        )

        points.append(
            {
                "time": result.total_time,
                "energy": result.total_energy,
                "speed_factor": float(factor),
            }
        )

    # パレート非劣解のみ抽出
    return _extract_pareto_front(points)


def _extract_pareto_front(
    points: list[dict[str, float]],
) -> list[dict[str, float]]:
    """パレート非劣解を抽出する.

    時間とエネルギーの両方を最小化する問題。
    """
    if not points:
        return []

    # 時間でソート
    sorted_points = sorted(points, key=lambda p: p["time"])

    front: list[dict[str, float]] = [sorted_points[0]]
    min_energy = sorted_points[0]["energy"]

    for p in sorted_points[1:]:
        if p["energy"] < min_energy - 1e-10:
            front.append(p)
            min_energy = p["energy"]

    return front

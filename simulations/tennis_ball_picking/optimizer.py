"""経路最適化と収集効率解析.

仕様書 §6 に基づく個人最適化問題を実装する。
- Greedy nearest neighbor による経路構築
- 2-opt 局所探索による経路改善
- 時間とエネルギーの同時評価
- パレートフロント抽出
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from .energy import (
    EnergyParams,
    bending_energy,
    carrying_energy,
    speed_with_load,
    walking_energy,
)
from .styles import StyleParams, StyleType, get_all_styles


@dataclass
class TripResult:
    """1トリップ（拾い→運搬→カゴ投入）の結果."""

    ball_indices: list[int]
    collect_distance: float  # ボール間移動距離 [m]
    return_distance: float  # 最終ボール→カゴ距離 [m]
    time: float  # 所要時間 [秒]
    energy: dict[str, float] = field(default_factory=dict)  # walk/bend/carry/total


@dataclass
class CollectionResult:
    """全ボール回収シミュレーションの結果."""

    style_type: StyleType
    trips: list[TripResult]
    total_time: float
    total_energy: dict[str, float]  # walk/bend/carry/total
    route: list[int]  # 訪問順序（全ボールindex）

    @property
    def n_trips(self) -> int:
        """往復回数."""
        return len(self.trips)

    @property
    def n_balls(self) -> int:
        """回収ボール数."""
        return len(self.route)


def _distance_matrix(
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """距離行列を計算.

    Returns:
        ball_dists: (N, N) ボール間距離行列
        basket_dists: (N,) 各ボール→カゴ距離
    """
    diff = ball_positions[:, np.newaxis, :] - ball_positions[np.newaxis, :, :]
    ball_dists = np.sqrt(np.sum(diff**2, axis=2))
    basket_dists = np.sqrt(np.sum((ball_positions - basket_position) ** 2, axis=1))
    return ball_dists, basket_dists


def greedy_route(
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
    capacity: int,
) -> list[list[int]]:
    """Greedy nearest neighbor による経路構築.

    容量制約付きで、カゴからスタートし最近傍を辿る。
    容量到達でカゴに戻り、次トリップを開始する。

    Returns:
        trips: 各トリップで訪問するボールindexのリスト
    """
    n = len(ball_positions)
    if n == 0:
        return []

    ball_dists, basket_dists = _distance_matrix(ball_positions, basket_position)
    remaining = set(range(n))
    trips: list[list[int]] = []

    while remaining:
        trip: list[int] = []
        # カゴ位置からスタート
        current_dists = basket_dists.copy()

        while remaining and len(trip) < capacity:
            # 残りのうち最近傍を選択
            best_idx = -1
            best_dist = float("inf")
            for idx in remaining:
                d = float(current_dists[idx])
                if d < best_dist:
                    best_dist = d
                    best_idx = idx
            trip.append(best_idx)
            remaining.remove(best_idx)
            # 次の基準点は今拾ったボール
            current_dists = ball_dists[best_idx]

        trips.append(trip)

    return trips


def two_opt_improve(
    trip_indices: list[int],
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
    max_iterations: int = 100,
) -> list[int]:
    """2-opt局所探索でトリップ内の経路を改善.

    カゴ→ボール1→ボール2→...→カゴ の巡回路を2-opt交換で短縮。

    Args:
        trip_indices: ボールindex列
        ball_positions: 全ボール座標
        basket_position: カゴ座標
        max_iterations: 最大反復回数

    Returns:
        改善後のボールindex列
    """
    n = len(trip_indices)
    if n <= 2:
        return trip_indices

    route = list(trip_indices)

    def route_distance(r: list[int]) -> float:
        d = float(np.linalg.norm(ball_positions[r[0]] - basket_position))
        for i in range(len(r) - 1):
            d += float(np.linalg.norm(ball_positions[r[i + 1]] - ball_positions[r[i]]))
        d += float(np.linalg.norm(ball_positions[r[-1]] - basket_position))
        return d

    best_dist = route_distance(route)

    for _ in range(max_iterations):
        improved = False
        for i in range(n - 1):
            for j in range(i + 1, n):
                new_route = route[:i] + route[i : j + 1][::-1] + route[j + 1 :]
                new_dist = route_distance(new_route)
                if new_dist < best_dist - 1e-10:
                    route = new_route
                    best_dist = new_dist
                    improved = True
                    break
            if improved:
                break
        if not improved:
            break

    return route


def simulate_collection(
    trips: list[list[int]],
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
    style: StyleParams,
    energy_params: EnergyParams | None = None,
) -> CollectionResult:
    """経路に基づくシミュレーション（時間 + エネルギー）.

    Args:
        trips: 各トリップの訪問順序
        ball_positions: shape (N, 2) のボール座標
        basket_position: shape (2,) のカゴ座標
        style: 拾い方スタイル
        energy_params: エネルギーパラメータ（Noneならデフォルト）

    Returns:
        CollectionResult
    """
    if energy_params is None:
        energy_params = EnergyParams()

    total_time = 0.0
    total_e = {"walk": 0.0, "bend": 0.0, "carry": 0.0, "total": 0.0}
    trip_results: list[TripResult] = []
    full_route: list[int] = []
    cumulative_bends = 0

    for trip_indices in trips:
        n_balls_trip = len(trip_indices)
        if n_balls_trip == 0:
            continue

        full_route.extend(trip_indices)

        # --- 移動距離計算 ---
        # カゴ→最初のボール
        collect_dist = float(
            np.linalg.norm(ball_positions[trip_indices[0]] - basket_position)
        )
        # ボール間移動
        for k in range(n_balls_trip - 1):
            collect_dist += float(
                np.linalg.norm(
                    ball_positions[trip_indices[k + 1]]
                    - ball_positions[trip_indices[k]]
                )
            )
        # 最終ボール→カゴ
        return_dist = float(
            np.linalg.norm(ball_positions[trip_indices[-1]] - basket_position)
        )

        # --- 時間計算 ---
        t_pick = n_balls_trip * style.pick_time
        # 収集中の移動（無荷重 → 荷重増加。簡略化: 平均荷重で計算）
        avg_load = n_balls_trip / 2
        v_collect = speed_with_load(style.base_speed, int(avg_load), style.gamma)
        t_collect = collect_dist / max(v_collect, 0.1)
        # カゴへの帰還（フル荷重）
        v_return = speed_with_load(
            style.effective_carry_speed, n_balls_trip, style.gamma
        )
        t_return = return_dist / max(v_return, 0.1)
        trip_time = t_pick + t_collect + t_return

        # --- エネルギー計算 ---
        # 歩行エネルギー（収集 + 帰還）
        e_walk_collect = walking_energy(collect_dist, v_collect, energy_params)
        e_walk_return = walking_energy(return_dist, v_return, energy_params)
        e_walk = e_walk_collect + e_walk_return

        # 屈伸エネルギー（スタイルが屈伸を必要とする場合のみ）
        e_bend = 0.0
        if style.requires_bending:
            for k in range(n_balls_trip):
                e_bend += bending_energy(cumulative_bends + k, energy_params)
            cumulative_bends += n_balls_trip

        # 運搬エネルギー（帰還時のみ）
        e_carry = carrying_energy(return_dist, n_balls_trip, energy_params)

        e_total = e_walk + e_bend + e_carry

        trip_result = TripResult(
            ball_indices=trip_indices,
            collect_distance=collect_dist,
            return_distance=return_dist,
            time=trip_time,
            energy={
                "walk": e_walk,
                "bend": e_bend,
                "carry": e_carry,
                "total": e_total,
            },
        )
        trip_results.append(trip_result)

        total_time += trip_time
        for key in total_e:
            total_e[key] += trip_result.energy[key]

    return CollectionResult(
        style_type=style.style_type,
        trips=trip_results,
        total_time=total_time,
        total_energy=total_e,
        route=full_route,
    )


def optimize_collection(
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
    style: StyleParams,
    energy_params: EnergyParams | None = None,
    use_2opt: bool = True,
) -> CollectionResult:
    """スタイルに基づく最適化収集シミュレーション.

    1. Greedy nearest neighbor で初期経路構築
    2. 2-opt で各トリップ内を改善
    3. 時間・エネルギーを同時計算

    Args:
        ball_positions: shape (N, 2) のボール座標
        basket_position: shape (2,) のカゴ座標
        style: 拾い方スタイル
        energy_params: エネルギーパラメータ
        use_2opt: 2-opt改善を適用するか

    Returns:
        CollectionResult
    """
    trips = greedy_route(ball_positions, basket_position, style.capacity)

    if use_2opt:
        trips = [
            two_opt_improve(trip, ball_positions, basket_position) for trip in trips
        ]

    return simulate_collection(
        trips, ball_positions, basket_position, style, energy_params
    )


def compare_styles(
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
    energy_params: EnergyParams | None = None,
    use_2opt: bool = True,
) -> dict[StyleType, CollectionResult]:
    """全スタイルで収集シミュレーションを比較.

    Returns:
        スタイル → CollectionResult の辞書
    """
    styles = get_all_styles()
    results = {}
    for style_type, style in styles.items():
        results[style_type] = optimize_collection(
            ball_positions, basket_position, style, energy_params, use_2opt
        )
    return results


def extract_pareto_front(
    points: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    """2目的最小化のパレートフロントを抽出.

    Args:
        points: (time, energy) のリスト

    Returns:
        パレート最適な点のリスト（time昇順）
    """
    if not points:
        return []

    # time昇順でソート
    sorted_pts = sorted(points, key=lambda p: p[0])
    front: list[tuple[float, float]] = []
    min_energy = float("inf")

    for t, e in sorted_pts:
        if e < min_energy:
            front.append((t, e))
            min_energy = e

    return front


def sensitivity_analysis(
    ball_counts: list[int],
    court_geometry: object,
    distribution_factory: object,
    basket_position: NDArray[np.float64],
    energy_params: EnergyParams | None = None,
    n_trials: int = 10,
    seed: int = 42,
) -> dict[int, dict[StyleType, dict[str, float]]]:
    """ボール数に対する感度分析.

    各ボール数 × 各スタイルについて複数試行の平均を算出する。

    Args:
        ball_counts: 分析するボール数のリスト
        court_geometry: CourtGeometryインスタンス
        distribution_factory: BallDistributionを生成する関数
        basket_position: カゴ座標
        energy_params: エネルギーパラメータ
        n_trials: 各条件の試行数
        seed: 乱数シード

    Returns:
        ball_count → style_type → {"time_mean", "time_std",
        "energy_mean", "energy_std"} の辞書
    """
    from .court import CourtGeometry
    from .distribution import BallDistribution

    court = court_geometry
    if not isinstance(court, CourtGeometry):
        msg = "court_geometryはCourtGeometryインスタンスである必要があります"
        raise TypeError(msg)

    rng = np.random.default_rng(seed)
    results: dict[int, dict[StyleType, dict[str, float]]] = {}

    for n_balls in ball_counts:
        results[n_balls] = {}
        styles = get_all_styles()

        for style_type, style in styles.items():
            times: list[float] = []
            energies: list[float] = []

            for _ in range(n_trials):
                dist: BallDistribution = distribution_factory(court)
                balls = dist.sample(n_balls, court, rng)
                result = optimize_collection(
                    balls, basket_position, style, energy_params
                )
                times.append(result.total_time)
                energies.append(result.total_energy["total"])

            results[n_balls][style_type] = {
                "time_mean": float(np.mean(times)),
                "time_std": float(np.std(times)),
                "energy_mean": float(np.mean(energies)),
                "energy_std": float(np.std(energies)),
            }

    return results

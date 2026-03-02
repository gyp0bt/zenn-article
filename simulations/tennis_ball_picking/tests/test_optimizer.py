"""optimizer.py のテスト."""

from __future__ import annotations

import numpy as np
import pytest

from ..court import CourtGeometry
from ..distribution import create_stroke_distribution
from ..energy import EnergyParams
from ..optimizer import (
    CollectionResult,
    compare_styles,
    extract_pareto_front,
    greedy_route,
    optimize_collection,
    sensitivity_analysis,
    simulate_collection,
    two_opt_improve,
)
from ..styles import StyleType, style_a, style_b, style_d


@pytest.fixture
def simple_balls() -> np.ndarray:
    """テスト用の簡単なボール配置（5球）."""
    return np.array(
        [
            [2.0, 3.0],
            [4.0, 1.0],
            [1.0, 5.0],
            [3.0, 2.0],
            [5.0, 4.0],
        ]
    )


@pytest.fixture
def basket() -> np.ndarray:
    """テスト用カゴ位置."""
    return np.array([0.0, 0.0])


@pytest.fixture
def energy_params() -> EnergyParams:
    """テスト用エネルギーパラメータ."""
    return EnergyParams()


class TestGreedyRoute:
    """greedy_route のテスト."""

    def test_empty(self, basket: np.ndarray) -> None:
        balls = np.empty((0, 2))
        trips = greedy_route(balls, basket, capacity=5)
        assert trips == []

    def test_single_ball(self, basket: np.ndarray) -> None:
        balls = np.array([[3.0, 4.0]])
        trips = greedy_route(balls, basket, capacity=5)
        assert len(trips) == 1
        assert trips[0] == [0]

    def test_capacity_respected(
        self, simple_balls: np.ndarray, basket: np.ndarray
    ) -> None:
        trips = greedy_route(simple_balls, basket, capacity=2)
        # 5球 ÷ 容量2 = 3トリップ
        assert len(trips) == 3
        for trip in trips:
            assert len(trip) <= 2

    def test_all_balls_visited(
        self, simple_balls: np.ndarray, basket: np.ndarray
    ) -> None:
        trips = greedy_route(simple_balls, basket, capacity=3)
        all_indices = []
        for trip in trips:
            all_indices.extend(trip)
        assert sorted(all_indices) == list(range(5))

    def test_nearest_first(self, basket: np.ndarray) -> None:
        """カゴに最も近いボールが最初に訪問される."""
        balls = np.array([[10.0, 0.0], [1.0, 0.0], [5.0, 0.0]])
        trips = greedy_route(balls, basket, capacity=10)
        assert trips[0][0] == 1  # (1,0) が最も近い


class TestTwoOptImprove:
    """two_opt_improve のテスト."""

    def test_short_route_unchanged(
        self, simple_balls: np.ndarray, basket: np.ndarray
    ) -> None:
        route = [0, 1]
        improved = two_opt_improve(route, simple_balls, basket)
        assert len(improved) == 2
        assert set(improved) == {0, 1}

    def test_improves_or_same(self, basket: np.ndarray) -> None:
        """2-optは経路を悪化させない."""
        balls = np.array(
            [
                [1.0, 0.0],
                [3.0, 0.0],
                [0.0, 2.0],
                [2.0, 2.0],
                [4.0, 2.0],
            ]
        )
        original = [0, 2, 1, 4, 3]
        improved = two_opt_improve(original, balls, basket)

        def total_dist(route: list[int]) -> float:
            d = float(np.linalg.norm(balls[route[0]] - basket))
            for i in range(len(route) - 1):
                d += float(np.linalg.norm(balls[route[i + 1]] - balls[route[i]]))
            d += float(np.linalg.norm(balls[route[-1]] - basket))
            return d

        assert total_dist(improved) <= total_dist(original) + 1e-10


class TestSimulateCollection:
    """simulate_collection のテスト."""

    def test_basic_simulation(
        self,
        simple_balls: np.ndarray,
        basket: np.ndarray,
        energy_params: EnergyParams,
    ) -> None:
        style = style_a()
        trips = greedy_route(simple_balls, basket, capacity=style.capacity)
        result = simulate_collection(trips, simple_balls, basket, style, energy_params)
        assert isinstance(result, CollectionResult)
        assert result.n_balls == 5
        assert result.total_time > 0
        assert result.total_energy["total"] > 0

    def test_energy_components(
        self,
        simple_balls: np.ndarray,
        basket: np.ndarray,
        energy_params: EnergyParams,
    ) -> None:
        style = style_a()
        trips = greedy_route(simple_balls, basket, capacity=style.capacity)
        result = simulate_collection(trips, simple_balls, basket, style, energy_params)
        e = result.total_energy
        assert e["walk"] > 0
        assert e["bend"] > 0  # Style A requires bending
        assert e["carry"] > 0
        assert abs(e["total"] - (e["walk"] + e["bend"] + e["carry"])) < 1e-6

    def test_no_bending_for_hopper(
        self,
        simple_balls: np.ndarray,
        basket: np.ndarray,
        energy_params: EnergyParams,
    ) -> None:
        style = style_d()
        trips = greedy_route(simple_balls, basket, capacity=style.capacity)
        result = simulate_collection(trips, simple_balls, basket, style, energy_params)
        assert result.total_energy["bend"] == 0.0


class TestOptimizeCollection:
    """optimize_collection のテスト."""

    def test_greedy_only(self, simple_balls: np.ndarray, basket: np.ndarray) -> None:
        style = style_b()
        result = optimize_collection(simple_balls, basket, style, use_2opt=False)
        assert result.n_balls == 5
        assert result.total_time > 0

    def test_with_2opt(self, simple_balls: np.ndarray, basket: np.ndarray) -> None:
        style = style_b()
        result_greedy = optimize_collection(simple_balls, basket, style, use_2opt=False)
        result_2opt = optimize_collection(simple_balls, basket, style, use_2opt=True)
        # 2-optは同じかより良い結果を返す
        assert result_2opt.total_time <= result_greedy.total_time + 1e-6


class TestCompareStyles:
    """compare_styles のテスト."""

    def test_all_styles_present(
        self, simple_balls: np.ndarray, basket: np.ndarray
    ) -> None:
        results = compare_styles(simple_balls, basket)
        assert set(results.keys()) == {
            StyleType.A,
            StyleType.B,
            StyleType.C,
            StyleType.D,
        }

    def test_hopper_fewer_trips(
        self, simple_balls: np.ndarray, basket: np.ndarray
    ) -> None:
        results = compare_styles(simple_balls, basket)
        # ホッパー(容量72)は5球なら1トリップ
        assert results[StyleType.D].n_trips == 1


class TestExtractParetoFront:
    """extract_pareto_front のテスト."""

    def test_empty(self) -> None:
        assert extract_pareto_front([]) == []

    def test_single_point(self) -> None:
        front = extract_pareto_front([(1.0, 2.0)])
        assert front == [(1.0, 2.0)]

    def test_dominated_removed(self) -> None:
        points = [(1.0, 3.0), (2.0, 2.0), (3.0, 1.0), (2.5, 2.5)]
        front = extract_pareto_front(points)
        # (2.5, 2.5) は (2.0, 2.0) に支配される
        assert (2.5, 2.5) not in front
        assert len(front) == 3

    def test_sorted_by_time(self) -> None:
        points = [(3.0, 1.0), (1.0, 3.0), (2.0, 2.0)]
        front = extract_pareto_front(points)
        times = [t for t, _ in front]
        assert times == sorted(times)


class TestSensitivityAnalysis:
    """sensitivity_analysis のテスト."""

    def test_basic(self, basket: np.ndarray) -> None:
        court = CourtGeometry()
        results = sensitivity_analysis(
            ball_counts=[20, 40],
            court_geometry=court,
            distribution_factory=create_stroke_distribution,
            basket_position=basket,
            n_trials=3,
            seed=42,
        )
        assert set(results.keys()) == {20, 40}
        for n_balls, style_results in results.items():
            assert StyleType.A in style_results
            for style_type, stats in style_results.items():
                assert stats["time_mean"] > 0
                assert stats["energy_mean"] > 0
                assert stats["time_std"] >= 0

    def test_more_balls_more_time(self, basket: np.ndarray) -> None:
        court = CourtGeometry()
        results = sensitivity_analysis(
            ball_counts=[20, 50],
            court_geometry=court,
            distribution_factory=create_stroke_distribution,
            basket_position=basket,
            n_trials=5,
            seed=42,
        )
        # ボール数が多いほど時間が長い
        for style_type in StyleType:
            assert (
                results[50][style_type]["time_mean"]
                > results[20][style_type]["time_mean"]
            )

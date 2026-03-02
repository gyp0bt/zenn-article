"""optimizer.py のテスト."""

import numpy as np
import pytest

from ..court import CourtGeometry
from ..energy import EnergyParams
from ..optimizer import (
    RouteResult,
    _extract_pareto_front,
    _split_into_trips,
    _trip_distance,
    compare_styles,
    evaluate_route,
    greedy_nearest_neighbor,
    optimize_route,
    pareto_front,
    two_opt_improve,
)
from ..styles import style_a, style_b, style_d


# --- フィクスチャ ---


@pytest.fixture()
def court() -> CourtGeometry:
    return CourtGeometry()


@pytest.fixture()
def basket(court: CourtGeometry) -> np.ndarray:
    return court.default_basket_position()


@pytest.fixture()
def simple_balls() -> np.ndarray:
    """単純な5点のボール配置."""
    return np.array(
        [
            [0.0, 5.0],
            [3.0, 5.0],
            [-3.0, 5.0],
            [0.0, 10.0],
            [0.0, -5.0],
        ]
    )


@pytest.fixture()
def many_balls(court: CourtGeometry) -> np.ndarray:
    """50球のランダムなボール配置."""
    rng = np.random.default_rng(42)
    x = rng.uniform(court.x_min, court.x_max, size=50)
    y = rng.uniform(court.y_min, court.y_max, size=50)
    return np.column_stack([x, y])


# --- greedy_nearest_neighbor テスト ---


class TestGreedyNearestNeighbor:
    def test_empty_balls(self, basket: np.ndarray) -> None:
        order = greedy_nearest_neighbor(np.empty((0, 2)), basket, style_b())
        assert order == []

    def test_single_ball(self, basket: np.ndarray) -> None:
        balls = np.array([[0.0, 0.0]])
        order = greedy_nearest_neighbor(balls, basket, style_b())
        assert order == [0]

    def test_visits_all_balls(
        self, simple_balls: np.ndarray, basket: np.ndarray
    ) -> None:
        order = greedy_nearest_neighbor(simple_balls, basket, style_b())
        assert sorted(order) == list(range(len(simple_balls)))

    def test_nearest_first(self, basket: np.ndarray) -> None:
        """カゴに近い順に訪問することを確認."""
        balls = np.array(
            [
                [100.0, 100.0],  # 遠い
                [basket[0], basket[1] + 0.1],  # 最も近い
                [50.0, 50.0],  # 中間
            ]
        )
        order = greedy_nearest_neighbor(balls, basket, style_d())
        assert order[0] == 1  # 最も近いボールが最初

    def test_capacity_respected(self, basket: np.ndarray) -> None:
        """容量を超えたらカゴに戻ることを確認."""
        balls = np.array(
            [
                [1.0, 1.0],
                [2.0, 2.0],
                [3.0, 3.0],
                [4.0, 4.0],
                [5.0, 5.0],
            ]
        )
        style = style_b()  # capacity=3
        order = greedy_nearest_neighbor(balls, basket, style)
        assert len(order) == 5


# --- _split_into_trips テスト ---


class TestSplitIntoTrips:
    def test_single_trip(self) -> None:
        trips = _split_into_trips([0, 1, 2], capacity=5)
        assert trips == [[0, 1, 2]]

    def test_multiple_trips(self) -> None:
        trips = _split_into_trips([0, 1, 2, 3, 4], capacity=2)
        assert trips == [[0, 1], [2, 3], [4]]

    def test_exact_capacity(self) -> None:
        trips = _split_into_trips([0, 1, 2, 3], capacity=2)
        assert trips == [[0, 1], [2, 3]]

    def test_empty(self) -> None:
        trips = _split_into_trips([], capacity=5)
        assert trips == []


# --- _trip_distance テスト ---


class TestTripDistance:
    def test_known_distance(self) -> None:
        balls = np.array([[0.0, 0.0], [3.0, 0.0], [3.0, 4.0]])
        basket = np.array([0.0, 0.0])
        d = _trip_distance([0, 1, 2], balls, basket)
        # basket(0,0)->ball0(0,0): 0 + ball0->ball1: 3 + ball1->ball2: 4 + ball2->basket: 5
        assert pytest.approx(d, abs=1e-10) == 12.0

    def test_empty_trip(self) -> None:
        balls = np.array([[1.0, 1.0]])
        basket = np.array([0.0, 0.0])
        assert _trip_distance([], balls, basket) == 0.0


# --- two_opt_improve テスト ---


class TestTwoOptImprove:
    def test_improves_or_maintains(
        self, simple_balls: np.ndarray, basket: np.ndarray
    ) -> None:
        """2-optが元の解より悪くならないことを確認."""
        style = style_b()
        initial_order = greedy_nearest_neighbor(simple_balls, basket, style)
        initial_dist = sum(
            _trip_distance(trip, simple_balls, basket)
            for trip in _split_into_trips(initial_order, style.capacity)
        )

        improved_order = two_opt_improve(initial_order, simple_balls, basket, style)
        improved_dist = sum(
            _trip_distance(trip, simple_balls, basket)
            for trip in _split_into_trips(improved_order, style.capacity)
        )

        assert improved_dist <= initial_dist + 1e-10

    def test_preserves_all_balls(
        self, simple_balls: np.ndarray, basket: np.ndarray
    ) -> None:
        style = style_b()
        order = greedy_nearest_neighbor(simple_balls, basket, style)
        improved = two_opt_improve(order, simple_balls, basket, style)
        assert sorted(improved) == sorted(order)

    def test_short_order(self, basket: np.ndarray) -> None:
        """2球以下では変更なし."""
        balls = np.array([[1.0, 1.0], [2.0, 2.0]])
        style = style_b()
        order = [0, 1]
        improved = two_opt_improve(order, balls, basket, style)
        assert sorted(improved) == [0, 1]


# --- evaluate_route テスト ---


class TestEvaluateRoute:
    def test_basic_evaluation(
        self, simple_balls: np.ndarray, basket: np.ndarray
    ) -> None:
        order = list(range(len(simple_balls)))
        result = evaluate_route(order, simple_balls, basket, style_b())

        assert isinstance(result, RouteResult)
        assert result.total_time > 0
        assert result.total_energy > 0
        assert result.n_trips >= 1
        assert len(result.trip_details) == result.n_trips
        assert result.order is not None

    def test_energy_breakdown_sums(
        self, simple_balls: np.ndarray, basket: np.ndarray
    ) -> None:
        order = list(range(len(simple_balls)))
        result = evaluate_route(order, simple_balls, basket, style_b())

        breakdown_sum = sum(result.energy_breakdown.values())
        assert pytest.approx(result.total_energy, rel=1e-10) == breakdown_sum

    def test_no_bending_for_hopper(
        self, simple_balls: np.ndarray, basket: np.ndarray
    ) -> None:
        """ホッパースタイルでは屈伸エネルギーがゼロ."""
        order = list(range(len(simple_balls)))
        result = evaluate_route(order, simple_balls, basket, style_d())
        assert result.energy_breakdown["bend"] == 0.0

    def test_trip_details_consistency(
        self, simple_balls: np.ndarray, basket: np.ndarray
    ) -> None:
        order = list(range(len(simple_balls)))
        result = evaluate_route(order, simple_balls, basket, style_b())

        total_balls = sum(int(td["n_balls"]) for td in result.trip_details)
        assert total_balls == len(simple_balls)

    def test_custom_energy_params(
        self, simple_balls: np.ndarray, basket: np.ndarray
    ) -> None:
        order = list(range(len(simple_balls)))
        light_params = EnergyParams(body_mass=40.0)
        heavy_params = EnergyParams(body_mass=80.0)

        result_light = evaluate_route(
            order, simple_balls, basket, style_b(), light_params
        )
        result_heavy = evaluate_route(
            order, simple_balls, basket, style_b(), heavy_params
        )

        assert result_heavy.total_energy > result_light.total_energy


# --- optimize_route テスト ---


class TestOptimizeRoute:
    def test_greedy_only(self, simple_balls: np.ndarray, basket: np.ndarray) -> None:
        result = optimize_route(simple_balls, basket, style_b(), use_2opt=False)
        assert isinstance(result, RouteResult)
        assert sorted(result.order.tolist()) == list(range(len(simple_balls)))

    def test_with_2opt(self, simple_balls: np.ndarray, basket: np.ndarray) -> None:
        result_greedy = optimize_route(simple_balls, basket, style_b(), use_2opt=False)
        result_2opt = optimize_route(simple_balls, basket, style_b(), use_2opt=True)

        # 2-optは同等かそれ以上の結果を出す
        assert result_2opt.total_time <= result_greedy.total_time + 1e-6

    def test_many_balls(self, many_balls: np.ndarray, basket: np.ndarray) -> None:
        result = optimize_route(many_balls, basket, style_a())
        assert result.n_trips >= 1
        assert sorted(result.order.tolist()) == list(range(len(many_balls)))


# --- compare_styles テスト ---


class TestCompareStyles:
    def test_compare_all(self, simple_balls: np.ndarray, basket: np.ndarray) -> None:
        styles = {
            "A": style_a(),
            "B": style_b(),
            "D": style_d(),
        }
        results = compare_styles(simple_balls, basket, styles)

        assert set(results.keys()) == {"A", "B", "D"}
        for name, r in results.items():
            assert isinstance(r, RouteResult)
            assert r.total_time > 0
            assert r.total_energy > 0


# --- pareto_front テスト ---


class TestParetoFront:
    def test_basic_pareto(self, simple_balls: np.ndarray, basket: np.ndarray) -> None:
        front = pareto_front(
            simple_balls,
            basket,
            style_b(),
            speed_factors=np.linspace(0.6, 1.4, 10),
        )

        assert len(front) >= 1
        for p in front:
            assert "time" in p
            assert "energy" in p
            assert "speed_factor" in p

    def test_pareto_dominance(
        self, simple_balls: np.ndarray, basket: np.ndarray
    ) -> None:
        """パレートフロント上の点は互いに非劣であることを確認."""
        front = pareto_front(
            simple_balls,
            basket,
            style_b(),
            speed_factors=np.linspace(0.5, 1.5, 20),
        )

        for i in range(len(front)):
            for j in range(len(front)):
                if i == j:
                    continue
                # 2つの点が互いに支配しない
                not_both_better = not (
                    front[i]["time"] <= front[j]["time"]
                    and front[i]["energy"] <= front[j]["energy"]
                    and (
                        front[i]["time"] < front[j]["time"]
                        or front[i]["energy"] < front[j]["energy"]
                    )
                )
                assert not_both_better, (
                    f"Point {i} dominates point {j}: {front[i]} vs {front[j]}"
                )


# --- _extract_pareto_front テスト ---


class TestExtractParetoFront:
    def test_empty(self) -> None:
        assert _extract_pareto_front([]) == []

    def test_single_point(self) -> None:
        points = [{"time": 10.0, "energy": 100.0, "speed_factor": 1.0}]
        front = _extract_pareto_front(points)
        assert len(front) == 1

    def test_dominated_removed(self) -> None:
        points = [
            {"time": 10.0, "energy": 100.0, "speed_factor": 1.0},
            {"time": 20.0, "energy": 200.0, "speed_factor": 0.5},  # 劣解
            {"time": 30.0, "energy": 50.0, "speed_factor": 0.7},  # 非劣解
        ]
        front = _extract_pareto_front(points)
        assert len(front) == 2
        times = [p["time"] for p in front]
        assert 10.0 in times
        assert 30.0 in times

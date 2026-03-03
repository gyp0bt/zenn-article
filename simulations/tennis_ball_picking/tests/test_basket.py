"""basket.py のユニットテスト."""

import numpy as np
import pytest

from simulations.tennis_ball_picking.basket import (
    BasketConfig,
    assign_balls_to_baskets,
    assign_balls_to_baskets_with_capacity,
    compute_basket_distances,
    optimize_basket_placement,
    total_basket_distance,
)
from simulations.tennis_ball_picking.court import CourtGeometry


@pytest.fixture
def court() -> CourtGeometry:
    return CourtGeometry()


class TestBasketConfig:
    def test_default_values(self) -> None:
        config = BasketConfig()
        assert config.n_baskets == 4
        assert config.basket_capacity == 50
        assert config.dump_time == 10.0

    def test_total_capacity(self) -> None:
        config = BasketConfig(n_baskets=4, basket_capacity=50)
        assert config.total_capacity == 200

    def test_cart_position_default(self, court: CourtGeometry) -> None:
        config = BasketConfig()
        pos = config.get_cart_position(court)
        expected = court.default_basket_position()
        np.testing.assert_array_almost_equal(pos, expected)

    def test_cart_position_custom(self, court: CourtGeometry) -> None:
        custom = np.array([0.0, 0.0])
        config = BasketConfig(cart_position=custom)
        pos = config.get_cart_position(court)
        np.testing.assert_array_equal(pos, custom)


class TestAssignBalls:
    def test_assign_to_nearest(self) -> None:
        balls = np.array([[0.0, 0.0], [10.0, 10.0], [5.0, 5.0]])
        baskets = np.array([[0.0, 0.0], [10.0, 10.0]])
        assignments = assign_balls_to_baskets(balls, baskets)
        assert assignments[0] == 0
        assert assignments[1] == 1
        # 中間のボールはどちらかに割り当て
        assert assignments[2] in [0, 1]

    def test_all_same_basket(self) -> None:
        balls = np.array([[1.0, 1.0], [1.1, 1.1], [0.9, 0.9]])
        baskets = np.array([[1.0, 1.0], [100.0, 100.0]])
        assignments = assign_balls_to_baskets(balls, baskets)
        np.testing.assert_array_equal(assignments, [0, 0, 0])

    def test_four_baskets(self) -> None:
        balls = np.array([[-5.0, 5.0], [5.0, 5.0], [-5.0, -5.0], [5.0, -5.0]])
        baskets = np.array([[-5.0, 5.0], [5.0, 5.0], [-5.0, -5.0], [5.0, -5.0]])
        assignments = assign_balls_to_baskets(balls, baskets)
        np.testing.assert_array_equal(assignments, [0, 1, 2, 3])


class TestOptimizeBasketPlacement:
    def test_returns_correct_shape(self) -> None:
        rng = np.random.default_rng(42)
        balls = rng.uniform(-10, 10, size=(100, 2))
        result = optimize_basket_placement(balls, n_baskets=4, rng=rng)
        assert result.shape == (4, 2)

    def test_reduces_total_distance(self) -> None:
        rng = np.random.default_rng(42)
        balls = rng.uniform(-10, 10, size=(100, 2))
        # ランダム配置
        random_baskets = rng.uniform(-10, 10, size=(4, 2))
        random_dist = total_basket_distance(balls, random_baskets)
        # 最適化配置
        optimal_baskets = optimize_basket_placement(
            balls, n_baskets=4, rng=np.random.default_rng(42)
        )
        optimal_dist = total_basket_distance(balls, optimal_baskets)
        assert optimal_dist <= random_dist

    def test_clustered_balls(self) -> None:
        """4角に集中したボールに対してカゴがそれぞれに配置される."""
        rng = np.random.default_rng(42)
        corners = [(-8, 8), (8, 8), (-8, -8), (8, -8)]
        balls_list = []
        for cx, cy in corners:
            cluster = rng.normal(loc=[cx, cy], scale=0.5, size=(25, 2))
            balls_list.append(cluster)
        balls = np.vstack(balls_list)
        baskets = optimize_basket_placement(balls, n_baskets=4, rng=rng)
        # 各カゴがそれぞれのコーナー近くにある
        for cx, cy in corners:
            dists = np.sqrt(np.sum((baskets - np.array([cx, cy])) ** 2, axis=1))
            assert dists.min() < 3.0

    def test_few_balls(self) -> None:
        """ボール数 < カゴ数でもエラーにならない."""
        balls = np.array([[0.0, 0.0], [1.0, 1.0]])
        result = optimize_basket_placement(balls, n_baskets=4)
        assert result.shape == (4, 2)

    def test_reproducibility(self) -> None:
        rng1 = np.random.default_rng(42)
        balls = rng1.uniform(-10, 10, size=(50, 2))
        r1 = optimize_basket_placement(balls, n_baskets=4, rng=np.random.default_rng(0))
        r2 = optimize_basket_placement(balls, n_baskets=4, rng=np.random.default_rng(0))
        np.testing.assert_array_equal(r1, r2)


class TestComputeBasketDistances:
    def test_correct_distances(self) -> None:
        balls = np.array([[3.0, 0.0], [0.0, 4.0]])
        baskets = np.array([[0.0, 0.0]])
        assignments = np.array([0, 0])
        dists = compute_basket_distances(balls, baskets, assignments)
        np.testing.assert_array_almost_equal(dists, [3.0, 4.0])


class TestAssignBallsWithCapacity:
    def test_respects_capacity(self) -> None:
        """各カゴの割り当て数が容量以下になる."""
        rng = np.random.default_rng(42)
        balls = rng.uniform(-10, 10, size=(100, 2))
        baskets = np.array([[-5.0, 5.0], [5.0, 5.0], [-5.0, -5.0], [5.0, -5.0]])
        assignments = assign_balls_to_baskets_with_capacity(
            balls, baskets, basket_capacity=30
        )
        for k in range(4):
            assert np.sum(assignments == k) <= 30

    def test_all_balls_assigned(self) -> None:
        """全ボールが割り当てられる."""
        rng = np.random.default_rng(42)
        balls = rng.uniform(-10, 10, size=(80, 2))
        baskets = np.array([[-5.0, 5.0], [5.0, 5.0], [-5.0, -5.0], [5.0, -5.0]])
        assignments = assign_balls_to_baskets_with_capacity(
            balls, baskets, basket_capacity=25
        )
        assert len(assignments) == 80
        assert all(0 <= a < 4 for a in assignments)

    def test_prefers_nearest(self) -> None:
        """容量に余裕がある場合は最近傍カゴに割り当てる."""
        balls = np.array([[0.1, 0.1], [9.9, 9.9]])
        baskets = np.array([[0.0, 0.0], [10.0, 10.0]])
        assignments = assign_balls_to_baskets_with_capacity(
            balls, baskets, basket_capacity=50
        )
        assert assignments[0] == 0
        assert assignments[1] == 1

    def test_overflow_to_next_nearest(self) -> None:
        """容量超過時は次に近いカゴに割り当てる."""
        balls = np.array([[0.0, 0.0], [0.1, 0.1], [0.2, 0.2]])
        baskets = np.array([[0.0, 0.0], [10.0, 10.0]])
        assignments = assign_balls_to_baskets_with_capacity(
            balls, baskets, basket_capacity=2
        )
        # 3球のうち2球がカゴ0、1球がカゴ1に溢れる
        assert np.sum(assignments == 0) == 2
        assert np.sum(assignments == 1) == 1


class TestTotalBasketDistance:
    def test_zero_distance(self) -> None:
        balls = np.array([[1.0, 1.0], [2.0, 2.0]])
        baskets = np.array([[1.0, 1.0], [2.0, 2.0]])
        assert total_basket_distance(balls, baskets) == pytest.approx(0.0)

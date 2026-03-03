"""styles.py のユニットテスト."""

import numpy as np
import pytest

from simulations.tennis_ball_picking.styles import (
    StyleType,
    estimate_mixed_style_c_time,
    estimate_total_time,
    get_all_styles,
    optimize_hit_ratio,
    pickup_time,
    style_a,
    style_b,
    style_c,
    style_c_phase1,
    style_d,
    travel_time,
    trip_time,
)


class TestStyleParams:
    def test_style_a_values(self) -> None:
        s = style_a()
        assert s.style_type == StyleType.A
        assert s.capacity == 20
        assert s.carry_speed == pytest.approx(0.7)
        assert s.gamma == pytest.approx(0.02)
        assert s.requires_bending is True

    def test_style_b_values(self) -> None:
        """Style B: しゃがみ移動・カゴ持ち（両手で2〜3個/秒）."""
        s = style_b()
        assert s.style_type == StyleType.B
        assert s.capacity == 50
        assert s.base_speed == pytest.approx(0.7)
        assert s.pick_time == pytest.approx(0.4)
        assert s.gamma == pytest.approx(0.005)
        assert s.requires_bending is True

    def test_style_c_values(self) -> None:
        s = style_c()
        assert s.style_type == StyleType.C
        assert s.pick_time == pytest.approx(2.5)
        assert s.requires_bending is False

    def test_style_c_phase1_values(self) -> None:
        s = style_c_phase1()
        assert s.capacity == 200
        assert s.requires_bending is False

    def test_style_d_values(self) -> None:
        s = style_d()
        assert s.style_type == StyleType.D
        assert s.capacity == 72
        assert s.pick_time == pytest.approx(1.5)
        assert s.requires_bending is False

    def test_effective_carry_speed_with_override(self) -> None:
        s = style_a()
        assert s.effective_carry_speed == pytest.approx(0.7)

    def test_effective_carry_speed_fallback(self) -> None:
        s = style_b()
        assert s.effective_carry_speed == pytest.approx(0.7)

    def test_get_all_styles(self) -> None:
        styles = get_all_styles()
        assert len(styles) == 4
        assert StyleType.A in styles
        assert StyleType.D in styles


class TestPickupTime:
    def test_zero_balls(self) -> None:
        assert pickup_time(0, style_a()) == pytest.approx(0.0)

    def test_multiple_balls(self) -> None:
        assert pickup_time(5, style_a()) == pytest.approx(10.0)

    def test_style_b_faster_pick(self) -> None:
        """Style B（しゃがみ）はpick_time=0.4s、Style A（ラケット載せ）は2.0s."""
        t_a = pickup_time(10, style_a())
        t_b = pickup_time(10, style_b())
        assert t_b < t_a

    def test_style_d_faster(self) -> None:
        t_a = pickup_time(10, style_a())
        t_d = pickup_time(10, style_d())
        assert t_d < t_a


class TestTravelTime:
    def test_zero_distance(self) -> None:
        assert travel_time(0.0, 0, style_b()) == pytest.approx(0.0)

    def test_basic(self) -> None:
        t = travel_time(7.0, 0, style_b())
        assert t == pytest.approx(7.0 / 0.7)

    def test_load_slows_down(self) -> None:
        t_empty = travel_time(10.0, 0, style_a())
        t_loaded = travel_time(10.0, 5, style_a())
        assert t_loaded > t_empty


class TestTripTime:
    def test_basic_trip(self) -> None:
        t = trip_time(
            collect_distance=10.0,
            return_distance=5.0,
            n_balls=3,
            style=style_b(),
        )
        assert t > 0
        # 拾い時間(0.4*3=1.2) + 移動時間 + 帰還時間
        expected_pick = 3 * 0.4
        assert t >= expected_pick


class TestEstimateTotalTime:
    def test_no_balls(self) -> None:
        basket = np.array([0.0, 0.0])
        balls = np.empty((0, 2))
        assert estimate_total_time(balls, basket, style_a()) == pytest.approx(0.0)

    def test_single_ball(self) -> None:
        basket = np.array([0.0, 0.0])
        balls = np.array([[5.0, 0.0]])
        t = estimate_total_time(balls, basket, style_b())
        # 移動5m + 拾い0.4秒 + 帰還5m（しゃがみ速度0.7）
        expected = 5.0 / 0.7 + 0.4 + 5.0 / (0.7 * (1.0 - 0.005))
        assert t == pytest.approx(expected, rel=1e-3)

    def test_style_b_large_capacity(self) -> None:
        """Style B（容量50）は10球なら1トリップ."""
        basket = np.array([0.0, 0.0])
        rng = np.random.default_rng(42)
        balls = rng.uniform(-5, 5, size=(10, 2))
        t = estimate_total_time(balls, basket, style_b())
        assert t > 0

    def test_hopper_single_trip(self) -> None:
        """ホッパー（容量72）は10球なら1トリップ."""
        basket = np.array([0.0, 0.0])
        rng = np.random.default_rng(42)
        balls = rng.uniform(-5, 5, size=(10, 2))
        t = estimate_total_time(balls, basket, style_d())
        assert t > 0


class TestMixedStyleC:
    def test_alpha_zero_is_all_direct(self) -> None:
        """α=0: 全て直接拾い."""
        rng = np.random.default_rng(42)
        balls = rng.uniform(-10, 10, size=(20, 2))
        basket = np.array([0.0, 0.0])
        target = np.array([0.0, 15.0])
        t = estimate_mixed_style_c_time(balls, basket, target, alpha=0.0, rng=rng)
        assert t > 0

    def test_alpha_one_is_all_hit(self) -> None:
        """α=1: 全て打ち飛ばし."""
        rng = np.random.default_rng(42)
        balls = rng.uniform(-10, 10, size=(20, 2))
        basket = np.array([0.0, 0.0])
        target = np.array([0.0, 15.0])
        t = estimate_mixed_style_c_time(balls, basket, target, alpha=1.0, rng=rng)
        assert t > 0

    def test_intermediate_alpha(self) -> None:
        """中間α値で正常動作."""
        rng = np.random.default_rng(42)
        balls = rng.uniform(-10, 10, size=(50, 2))
        basket = np.array([0.0, 0.0])
        target = np.array([5.0, 15.0])
        t = estimate_mixed_style_c_time(balls, basket, target, alpha=0.5, rng=rng)
        assert t > 0


class TestOptimizeHitRatio:
    def test_returns_valid_result(self) -> None:
        rng = np.random.default_rng(42)
        balls = rng.uniform(-10, 10, size=(30, 2))
        basket = np.array([0.0, 0.0])
        target = np.array([0.0, 15.0])
        result = optimize_hit_ratio(balls, basket, target, rng=rng)
        assert 0.0 <= result["alpha"] <= 1.0
        assert result["time"] > 0
        assert result["time_all_direct"] > 0

    def test_optimal_not_worse_than_all_direct(self) -> None:
        """最適αは全直接拾いよりも悪くない."""
        rng = np.random.default_rng(42)
        balls = rng.uniform(-10, 10, size=(50, 2))
        basket = np.array([0.0, 0.0])
        target = np.array([0.0, 15.0])
        result = optimize_hit_ratio(balls, basket, target, rng=rng)
        assert result["time"] <= result["time_all_direct"] + 1e-6

"""styles.py のユニットテスト."""

import numpy as np
import pytest

from simulations.tennis_ball_picking.styles import (
    StyleType,
    estimate_total_time,
    get_all_styles,
    pickup_time,
    style_a,
    style_b,
    style_c,
    style_d,
    travel_time,
    trip_time,
)


class TestStyleParams:
    def test_style_a_values(self) -> None:
        s = style_a()
        assert s.style_type == StyleType.A
        assert s.capacity == 5
        assert s.carry_speed == pytest.approx(0.9)
        assert s.gamma == pytest.approx(0.04)
        assert s.requires_bending is True

    def test_style_b_values(self) -> None:
        s = style_b()
        assert s.style_type == StyleType.B
        assert s.capacity == 3
        assert s.carry_speed is None
        assert s.gamma == pytest.approx(0.02)

    def test_style_c_values(self) -> None:
        s = style_c()
        assert s.style_type == StyleType.C
        assert s.pick_time == pytest.approx(2.5)
        assert s.requires_bending is False

    def test_style_d_values(self) -> None:
        s = style_d()
        assert s.style_type == StyleType.D
        assert s.capacity == 72
        assert s.pick_time == pytest.approx(1.5)
        assert s.requires_bending is False

    def test_effective_carry_speed_with_override(self) -> None:
        s = style_a()
        assert s.effective_carry_speed == pytest.approx(0.9)

    def test_effective_carry_speed_fallback(self) -> None:
        s = style_b()
        assert s.effective_carry_speed == pytest.approx(1.3)

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

    def test_style_d_faster(self) -> None:
        t_a = pickup_time(10, style_a())
        t_d = pickup_time(10, style_d())
        assert t_d < t_a  # ホッパーは拾い時間が短い


class TestTravelTime:
    def test_zero_distance(self) -> None:
        assert travel_time(0.0, 0, style_b()) == pytest.approx(0.0)

    def test_basic(self) -> None:
        t = travel_time(13.0, 0, style_b())
        assert t == pytest.approx(13.0 / 1.3)

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
        # 拾い時間 + 移動時間 + 帰還時間
        expected_pick = 3 * 2.0
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
        # 移動5m + 拾い2秒 + 帰還5m
        expected = 5.0 / 1.3 + 2.0 + 5.0 / (1.3 * (1.0 - 0.02))
        assert t == pytest.approx(expected, rel=1e-3)

    def test_capacity_trip(self) -> None:
        """容量オーバー時に複数トリップが必要."""
        basket = np.array([0.0, 0.0])
        # Style B (容量3) で4つのボールを配置
        balls = np.array([[1.0, 0.0], [2.0, 0.0], [3.0, 0.0], [4.0, 0.0]])
        t = estimate_total_time(balls, basket, style_b())
        # 2トリップ必要（3球 + 1球）
        assert t > 0

    def test_hopper_single_trip(self) -> None:
        """ホッパー（容量72）は10球なら1トリップ."""
        basket = np.array([0.0, 0.0])
        rng = np.random.default_rng(42)
        balls = rng.uniform(-5, 5, size=(10, 2))
        t = estimate_total_time(balls, basket, style_d())
        assert t > 0

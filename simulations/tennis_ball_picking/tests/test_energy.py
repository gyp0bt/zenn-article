"""energy.py のユニットテスト."""

import pytest

from simulations.tennis_ball_picking.energy import (
    EnergyParams,
    bending_energy,
    carrying_energy,
    cumulative_bending_energy,
    speed_with_load,
    total_trip_energy,
    walking_cost_per_kg_m,
    walking_energy,
)


@pytest.fixture
def params() -> EnergyParams:
    return EnergyParams()


class TestWalkingEnergy:
    def test_cost_per_kg_m_at_zero_speed(self, params: EnergyParams) -> None:
        c = walking_cost_per_kg_m(0.0, params)
        assert c == pytest.approx(params.alpha_0)

    def test_cost_increases_with_speed(self, params: EnergyParams) -> None:
        c1 = walking_cost_per_kg_m(1.0, params)
        c2 = walking_cost_per_kg_m(2.0, params)
        assert c2 > c1

    def test_walking_energy_zero_distance(self, params: EnergyParams) -> None:
        assert walking_energy(0.0, 1.0, params) == pytest.approx(0.0)

    def test_walking_energy_positive(self, params: EnergyParams) -> None:
        e = walking_energy(10.0, 1.3, params)
        # c_walk(1.3) = 1.5 + 0.8*1.3 + 0.3*1.3^2 = 1.5 + 1.04 + 0.507 = 3.047
        expected = 3.047 * 60.0 * 10.0
        assert e == pytest.approx(expected, rel=1e-3)


class TestBendingEnergy:
    def test_first_bend(self, params: EnergyParams) -> None:
        e = bending_energy(0, params)
        expected = 60.0 * 9.81 * 0.35 / 0.25
        assert e == pytest.approx(expected)

    def test_fatigue_increases(self, params: EnergyParams) -> None:
        e0 = bending_energy(0, params)
        e10 = bending_energy(10, params)
        assert e10 > e0
        # e10 = e_base * (1 + 0.007 * 10) = e_base * 1.07
        assert e10 == pytest.approx(e0 * 1.07)

    def test_cumulative_zero(self, params: EnergyParams) -> None:
        assert cumulative_bending_energy(0, params) == pytest.approx(0.0)

    def test_cumulative_one(self, params: EnergyParams) -> None:
        e = cumulative_bending_energy(1, params)
        assert e == pytest.approx(bending_energy(0, params))

    def test_cumulative_multiple(self, params: EnergyParams) -> None:
        e = cumulative_bending_energy(3, params)
        expected = sum(bending_energy(i, params) for i in range(3))
        assert e == pytest.approx(expected)


class TestCarryingEnergy:
    def test_zero_balls(self, params: EnergyParams) -> None:
        assert carrying_energy(10.0, 0, params) == pytest.approx(0.0)

    def test_positive(self, params: EnergyParams) -> None:
        e = carrying_energy(5.0, 3, params)
        expected = 1.5 * 3 * 0.058 * 9.81 * 5.0
        assert e == pytest.approx(expected)


class TestSpeedWithLoad:
    def test_no_load(self) -> None:
        assert speed_with_load(1.3, 0, 0.02) == pytest.approx(1.3)

    def test_load_reduces_speed(self) -> None:
        v = speed_with_load(1.3, 5, 0.02)
        expected = 1.3 * (1.0 - 0.02 * 5)
        assert v == pytest.approx(expected)

    def test_minimum_speed(self) -> None:
        v = speed_with_load(1.0, 100, 0.02)
        assert v == pytest.approx(0.1)


class TestTotalTripEnergy:
    def test_returns_all_components(self, params: EnergyParams) -> None:
        result = total_trip_energy(
            walk_distance=20.0,
            walk_speed=1.3,
            n_balls_picked=5,
            carry_distance=15.0,
            n_balls_carried=5,
            params=params,
        )
        assert "walk" in result
        assert "bend" in result
        assert "carry" in result
        assert "total" in result
        assert result["total"] == pytest.approx(
            result["walk"] + result["bend"] + result["carry"]
        )

    def test_all_components_positive(self, params: EnergyParams) -> None:
        result = total_trip_energy(
            walk_distance=10.0,
            walk_speed=1.0,
            n_balls_picked=3,
            carry_distance=8.0,
            n_balls_carried=3,
            params=params,
        )
        assert result["walk"] > 0
        assert result["bend"] > 0
        assert result["carry"] > 0

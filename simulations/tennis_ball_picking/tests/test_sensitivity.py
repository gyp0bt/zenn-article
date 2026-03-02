"""sensitivity.py のテスト."""

import numpy as np
import pytest

from ..court import CourtGeometry
from ..energy import EnergyParams
from ..sensitivity import (
    SensitivityResult,
    monte_carlo_variance,
    sweep_basket_position,
    sweep_distribution,
    sweep_n_balls,
)
from ..styles import style_a, style_b, style_d


@pytest.fixture()
def court() -> CourtGeometry:
    return CourtGeometry()


# --- sweep_n_balls テスト ---


class TestSweepNBalls:
    def test_basic(self) -> None:
        results = sweep_n_balls(
            n_balls_range=np.array([10, 30, 50]),
            style=style_b(),
        )
        assert len(results) == 3
        for r in results:
            assert isinstance(r, SensitivityResult)
            assert r.param_name == "n_balls"
            assert r.time > 0
            assert r.energy > 0

    def test_monotone_time(self) -> None:
        """ボール数が増えると時間も増える."""
        results = sweep_n_balls(
            n_balls_range=np.array([10, 30, 50, 80]),
            style=style_b(),
        )
        times = [r.time for r in results]
        for i in range(len(times) - 1):
            assert times[i + 1] > times[i]

    def test_monotone_energy(self) -> None:
        """ボール数が増えるとエネルギーも増える."""
        results = sweep_n_balls(
            n_balls_range=np.array([10, 30, 50, 80]),
            style=style_b(),
        )
        energies = [r.energy for r in results]
        for i in range(len(energies) - 1):
            assert energies[i + 1] > energies[i]

    def test_with_custom_params(self) -> None:
        results = sweep_n_balls(
            n_balls_range=np.array([20]),
            style=style_a(),
            energy_params=EnergyParams(body_mass=70.0),
        )
        assert len(results) == 1
        assert results[0].energy > 0


# --- sweep_distribution テスト ---


class TestSweepDistribution:
    def test_both_distributions(self) -> None:
        results = sweep_distribution(style=style_b(), n_balls=30)
        assert "ストローク練習" in results
        assert "ボレー練習" in results

    def test_results_differ(self) -> None:
        """異なる分布で異なる結果が出る."""
        results = sweep_distribution(style=style_b(), n_balls=50)
        stroke_time = results["ストローク練習"].total_time
        volley_time = results["ボレー練習"].total_time
        # 分布が異なるので結果も異なるはず
        assert stroke_time != volley_time


# --- sweep_basket_position テスト ---


class TestSweepBasketPosition:
    def test_basic(self) -> None:
        offsets = np.array([-5.0, 0.0, 5.0])
        results = sweep_basket_position(
            basket_offsets=offsets,
            style=style_b(),
            n_balls=30,
        )
        assert len(results) == 3
        for r in results:
            assert r.param_name == "basket_y_offset"
            assert r.time > 0

    def test_center_is_optimal_trend(self) -> None:
        """中央付近のカゴ配置が極端な端より良い傾向."""
        offsets = np.array([-10.0, 0.0, 10.0])
        results = sweep_basket_position(
            basket_offsets=offsets,
            style=style_b(),
            n_balls=50,
        )
        center_time = results[1].time
        # 極端なオフセットよりは中央が良い（少なくともどちらか一方より）
        assert center_time <= max(results[0].time, results[2].time)


# --- monte_carlo_variance テスト ---


class TestMonteCarloVariance:
    def test_basic(self) -> None:
        stats = monte_carlo_variance(
            style=style_b(),
            n_balls=30,
            n_trials=5,
        )
        assert "time" in stats
        assert "energy" in stats
        for key in ("mean", "std", "min", "max"):
            assert key in stats["time"]
            assert key in stats["energy"]

    def test_mean_within_range(self) -> None:
        stats = monte_carlo_variance(
            style=style_b(),
            n_balls=30,
            n_trials=10,
        )
        assert stats["time"]["min"] <= stats["time"]["mean"] <= stats["time"]["max"]
        assert (
            stats["energy"]["min"] <= stats["energy"]["mean"] <= stats["energy"]["max"]
        )

    def test_std_positive(self) -> None:
        """複数試行すれば標準偏差はゼロより大きい."""
        stats = monte_carlo_variance(
            style=style_b(),
            n_balls=50,
            n_trials=10,
        )
        assert stats["time"]["std"] > 0
        assert stats["energy"]["std"] > 0

    def test_hopper_no_bending(self) -> None:
        """ホッパーでもモンテカルロが正常に動作."""
        stats = monte_carlo_variance(
            style=style_d(),
            n_balls=30,
            n_trials=5,
        )
        assert stats["time"]["mean"] > 0
        assert stats["energy"]["mean"] > 0

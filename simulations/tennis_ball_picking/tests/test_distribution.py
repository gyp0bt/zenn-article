"""distribution.py のユニットテスト."""

import numpy as np
import pytest

from simulations.tennis_ball_picking.court import CourtGeometry
from simulations.tennis_ball_picking.distribution import (
    BallDistribution,
    BallZone,
    create_cross_dtl_distribution,
    create_stroke_distribution,
    create_volley_distribution,
)


@pytest.fixture
def court() -> CourtGeometry:
    return CourtGeometry()


class TestBallDistribution:
    def test_stroke_distribution_weights(self, court: CourtGeometry) -> None:
        dist = create_stroke_distribution(court)
        total_weight = sum(z.weight for z in dist.zones)
        assert total_weight == pytest.approx(1.0)

    def test_volley_distribution_weights(self, court: CourtGeometry) -> None:
        dist = create_volley_distribution(court)
        total_weight = sum(z.weight for z in dist.zones)
        assert total_weight == pytest.approx(1.0)

    def test_sample_count(self, court: CourtGeometry) -> None:
        dist = create_stroke_distribution(court)
        rng = np.random.default_rng(42)
        samples = dist.sample(100, court, rng)
        assert samples.shape == (100, 2)

    def test_samples_in_bounds(self, court: CourtGeometry) -> None:
        dist = create_stroke_distribution(court)
        rng = np.random.default_rng(42)
        samples = dist.sample(200, court, rng)
        assert court.is_in_bounds(samples).all()

    def test_reproducibility(self, court: CourtGeometry) -> None:
        dist = create_stroke_distribution(court)
        s1 = dist.sample(50, court, np.random.default_rng(123))
        s2 = dist.sample(50, court, np.random.default_rng(123))
        np.testing.assert_array_equal(s1, s2)

    def test_invalid_weights(self) -> None:
        dist = BallDistribution(
            name="invalid",
            zones=[
                BallZone(
                    name="a",
                    weight=0.3,
                    mu=np.array([0.0, 0.0]),
                    sigma=np.eye(2),
                ),
                BallZone(
                    name="b",
                    weight=0.3,
                    mu=np.array([0.0, 0.0]),
                    sigma=np.eye(2),
                ),
            ],
        )
        court = CourtGeometry()
        with pytest.raises(ValueError, match="ゾーン重みの合計"):
            dist.sample(10, court)

    def test_volley_sample(self, court: CourtGeometry) -> None:
        dist = create_volley_distribution(court)
        rng = np.random.default_rng(0)
        samples = dist.sample(80, court, rng)
        assert samples.shape == (80, 2)
        assert court.is_in_bounds(samples).all()


class TestCrossDTLDistribution:
    def test_weights_sum_to_one(self, court: CourtGeometry) -> None:
        dist = create_cross_dtl_distribution(court)
        total_weight = sum(z.weight for z in dist.zones)
        assert total_weight == pytest.approx(1.0)

    def test_zone_count(self, court: CourtGeometry) -> None:
        dist = create_cross_dtl_distribution(court)
        assert len(dist.zones) == 6

    def test_sample_count(self, court: CourtGeometry) -> None:
        dist = create_cross_dtl_distribution(court)
        rng = np.random.default_rng(42)
        samples = dist.sample(200, court, rng)
        assert samples.shape == (200, 2)

    def test_samples_in_bounds(self, court: CourtGeometry) -> None:
        dist = create_cross_dtl_distribution(court)
        rng = np.random.default_rng(42)
        samples = dist.sample(200, court, rng)
        assert court.is_in_bounds(samples).all()

    def test_corner_concentration(self, court: CourtGeometry) -> None:
        """コーナーにボールが集中することを検証."""
        dist = create_cross_dtl_distribution(court)
        rng = np.random.default_rng(42)
        samples = dist.sample(1000, court, rng)
        hl = court.half_length
        # 北側（y > hl/2）にいるボールの割合が50%以上
        north_ratio = np.mean(samples[:, 1] > hl / 2)
        assert north_ratio > 0.4

    def test_net_miss_zone(self, court: CourtGeometry) -> None:
        """ネットミスゾーンのボールが存在することを検証."""
        dist = create_cross_dtl_distribution(court)
        rng = np.random.default_rng(42)
        samples = dist.sample(1000, court, rng)
        # ネット手前（y < 0）にボールがある
        south_count = np.sum(samples[:, 1] < 0)
        assert south_count > 50  # 20%のネットミス帯があるので少なくとも50球

    def test_reproducibility(self, court: CourtGeometry) -> None:
        dist = create_cross_dtl_distribution(court)
        s1 = dist.sample(100, court, np.random.default_rng(99))
        s2 = dist.sample(100, court, np.random.default_rng(99))
        np.testing.assert_array_equal(s1, s2)

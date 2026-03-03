"""distribution.py のユニットテスト."""

import numpy as np
import pytest

from simulations.tennis_ball_picking.court import CourtGeometry
from simulations.tennis_ball_picking.distribution import (
    BallDistribution,
    BallZone,
    apply_ball_rolling,
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


class TestApplyBallRolling:
    def test_output_shape(self, court: CourtGeometry) -> None:
        """出力shapeが入力と同じ."""
        rng = np.random.default_rng(42)
        positions = rng.uniform(-5, 5, size=(100, 2))
        result = apply_ball_rolling(positions, court, rng=rng)
        assert result.shape == (100, 2)

    def test_empty_input(self, court: CourtGeometry) -> None:
        """空の入力でエラーにならない."""
        result = apply_ball_rolling(np.empty((0, 2)), court)
        assert result.shape == (0, 2)

    def test_results_in_bounds(self, court: CourtGeometry) -> None:
        """転がり後もボールが有効領域内に収まる."""
        dist = create_cross_dtl_distribution(court)
        rng = np.random.default_rng(42)
        landing = dist.sample(500, court, rng)
        result = apply_ball_rolling(landing, court, rng=rng)
        assert court.is_in_bounds(result).all()

    def test_balls_shift_toward_fences(self, court: CourtGeometry) -> None:
        """転がり後にバックフェンス寄りのボールが増える."""
        dist = create_cross_dtl_distribution(court)
        rng = np.random.default_rng(42)
        landing = dist.sample(1000, court, rng)
        rolled = apply_ball_rolling(landing, court, rng=np.random.default_rng(42))
        # バックフェンス付近（y > y_max - 3m）のボール割合が増加
        fence_zone = court.y_max - 3.0
        landing_near_fence = np.mean(landing[:, 1] > fence_zone)
        rolled_near_fence = np.mean(rolled[:, 1] > fence_zone)
        assert rolled_near_fence > landing_near_fence

    def test_reproducibility(self, court: CourtGeometry) -> None:
        """同じシードで再現可能."""
        positions = np.array([[0.0, 5.0], [3.0, 8.0], [-2.0, -3.0]])
        r1 = apply_ball_rolling(positions, court, rng=np.random.default_rng(42))
        r2 = apply_ball_rolling(positions, court, rng=np.random.default_rng(42))
        np.testing.assert_array_equal(r1, r2)

    def test_net_miss_balls_roll_less(self, court: CourtGeometry) -> None:
        """ネット手前のボールは転がりが少ない."""
        rng = np.random.default_rng(42)
        # ネット手前のボール（y < 0）
        net_miss = np.column_stack([rng.uniform(-5, 5, 100), rng.uniform(-10, -1, 100)])
        # 北側のボール（y > 0）
        north = np.column_stack([rng.uniform(-5, 5, 100), rng.uniform(5, 10, 100)])

        rolled_net = apply_ball_rolling(net_miss, court, rng=np.random.default_rng(0))
        rolled_north = apply_ball_rolling(north, court, rng=np.random.default_rng(0))

        # ネットミスの移動距離 < 北側の移動距離
        dist_net = np.mean(np.sqrt(np.sum((rolled_net - net_miss) ** 2, axis=1)))
        dist_north = np.mean(np.sqrt(np.sum((rolled_north - north) ** 2, axis=1)))
        assert dist_net < dist_north

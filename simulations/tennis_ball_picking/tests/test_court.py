"""court.py のユニットテスト."""

import numpy as np
import pytest

from simulations.tennis_ball_picking.court import CourtGeometry


@pytest.fixture
def court() -> CourtGeometry:
    return CourtGeometry()


class TestCourtGeometry:
    def test_default_dimensions(self, court: CourtGeometry) -> None:
        assert court.court_length == pytest.approx(23.77)
        assert court.doubles_width == pytest.approx(10.97)
        assert court.singles_width == pytest.approx(8.23)

    def test_half_length(self, court: CourtGeometry) -> None:
        assert court.half_length == pytest.approx(23.77 / 2)

    def test_total_area(self, court: CourtGeometry) -> None:
        expected_length = 23.77 + 2 * 6.40  # 36.57
        expected_width = 10.97 + 2 * 3.66  # 18.29
        assert court.total_area == pytest.approx(expected_length * expected_width)

    def test_bounds(self, court: CourtGeometry) -> None:
        assert court.x_min < 0
        assert court.x_max > 0
        assert court.y_min < 0
        assert court.y_max > 0
        assert court.x_max == pytest.approx(-court.x_min)
        assert court.y_max == pytest.approx(-court.y_min)

    def test_is_in_bounds(self, court: CourtGeometry) -> None:
        positions = np.array(
            [
                [0.0, 0.0],  # 中央 → 有効
                [100.0, 100.0],  # 遠方 → 無効
                [court.x_max, court.y_max],  # 境界 → 有効
                [court.x_max + 0.01, 0.0],  # 境界外 → 無効
            ]
        )
        result = court.is_in_bounds(positions)
        assert result.tolist() == [True, False, True, False]

    def test_default_basket_position(self, court: CourtGeometry) -> None:
        pos = court.default_basket_position()
        assert pos.shape == (2,)
        assert pos[1] == pytest.approx(0.0)  # ネット高さ

    def test_court_lines(self, court: CourtGeometry) -> None:
        lines = court.court_lines()
        assert "baseline_north" in lines
        assert "baseline_south" in lines
        assert "net" in lines
        assert lines["net"]["y"] == 0.0
        assert lines["baseline_north"]["y"] == pytest.approx(court.half_length)

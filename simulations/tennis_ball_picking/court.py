"""コートジオメトリ定義.

ITF公式規格に基づくテニスコートの幾何学パラメータと
有効領域（ボールが散在しうる範囲）を定義する。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class CourtGeometry:
    """ITF公式規格に基づくテニスコートの幾何学パラメータ.

    座標系: コート中央（ネット中央）を原点 (0, 0) とする。
    x軸: サイドライン方向（コート幅方向）
    y軸: ベースライン方向（コート長さ方向）
    """

    # コート本体寸法 [m]
    court_length: float = 23.77  # L: コート全長
    doubles_width: float = 10.97  # W_d: ダブルスコート幅
    singles_width: float = 8.23  # W_s: シングルスコート幅
    service_line_dist: float = 6.40  # d_sv: ネット〜サービスライン距離

    # コート外スペース [m]
    back_space: float = 6.40  # d_back: ベースライン後方スペース
    side_space: float = 3.66  # d_side: サイドライン外側スペース

    @property
    def half_length(self) -> float:
        """コート半長（ネットから片側ベースラインまで）."""
        return self.court_length / 2

    @property
    def total_length(self) -> float:
        """有効領域の全長（後方スペース含む）."""
        return self.court_length + 2 * self.back_space

    @property
    def total_width(self) -> float:
        """有効領域の全幅（サイドスペース含む）."""
        return self.doubles_width + 2 * self.side_space

    @property
    def total_area(self) -> float:
        """有効領域面積 [m^2]."""
        return self.total_length * self.total_width

    @property
    def y_min(self) -> float:
        """有効領域のy座標最小値（南端）."""
        return -(self.half_length + self.back_space)

    @property
    def y_max(self) -> float:
        """有効領域のy座標最大値（北端）."""
        return self.half_length + self.back_space

    @property
    def x_min(self) -> float:
        """有効領域のx座標最小値（西端）."""
        return -(self.doubles_width / 2 + self.side_space)

    @property
    def x_max(self) -> float:
        """有効領域のx座標最大値（東端）."""
        return self.doubles_width / 2 + self.side_space

    def default_basket_position(self) -> NDArray[np.float64]:
        """デフォルトカゴ位置（ネット脇）."""
        return np.array([self.doubles_width / 2 + 0.5, 0.0])

    def court_lines(self) -> dict[str, dict[str, float]]:
        """コートの主要ラインの座標を返す.

        Returns:
            各ラインの座標辞書。
        """
        hl = self.half_length
        hw_d = self.doubles_width / 2
        hw_s = self.singles_width / 2
        sv = self.service_line_dist

        return {
            "baseline_north": {"y": hl, "x_min": -hw_d, "x_max": hw_d},
            "baseline_south": {"y": -hl, "x_min": -hw_d, "x_max": hw_d},
            "doubles_sideline_east": {"x": hw_d, "y_min": -hl, "y_max": hl},
            "doubles_sideline_west": {"x": -hw_d, "y_min": -hl, "y_max": hl},
            "singles_sideline_east": {"x": hw_s, "y_min": -hl, "y_max": hl},
            "singles_sideline_west": {"x": -hw_s, "y_min": -hl, "y_max": hl},
            "service_line_north": {"y": sv, "x_min": -hw_s, "x_max": hw_s},
            "service_line_south": {"y": -sv, "x_min": -hw_s, "x_max": hw_s},
            "center_service_line": {"x": 0, "y_min": -sv, "y_max": sv},
            "net": {"y": 0, "x_min": -hw_d, "x_max": hw_d},
        }

    def is_in_bounds(self, positions: NDArray[np.float64]) -> NDArray[np.bool_]:
        """座標が有効領域内にあるかを判定.

        Args:
            positions: shape (N, 2) の座標配列

        Returns:
            shape (N,) のブール配列
        """
        x = positions[:, 0]
        y = positions[:, 1]
        return (
            (x >= self.x_min)
            & (x <= self.x_max)
            & (y >= self.y_min)
            & (y <= self.y_max)
        )

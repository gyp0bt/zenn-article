"""拾い方スタイルの定式化.

仕様書 §4 に基づく4種類の拾い方スタイルを定義する。
各スタイルは固有の物理パラメータと行動パターンを持つ。

v2 変更点:
- Style B: 手拾い直行 → しゃがみ移動・カゴ持ち
- Style C: 打ち飛ばし2フェーズモデルの明確化 + 打ち飛ばし比率最適化
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np
from numpy.typing import NDArray

from .energy import speed_with_load


class StyleType(Enum):
    """拾い方スタイルの種別."""

    A = "ラケット載せ運搬"
    B = "手拾い（しゃがみ移動・カゴ持ち）"
    C = "ラケット打ち飛ばし集約"
    D = "ホッパー巡回"


@dataclass(frozen=True)
class StyleParams:
    """拾い方スタイルの物理パラメータ.

    Attributes:
        style_type: スタイル種別
        capacity: 最大積載/保持数 [球]
        base_speed: 無荷重時の移動速度 [m/s]
        carry_speed: 運搬時の移動速度 [m/s]（Noneの場合base_speedを使用）
        pick_time: 拾い上げ時間 [秒/球]
        gamma: 速度低下係数 [1/球]
        requires_bending: 屈伸動作が必要か
    """

    style_type: StyleType
    capacity: int
    base_speed: float
    carry_speed: float | None = None
    pick_time: float = 2.0
    gamma: float = 0.0
    requires_bending: bool = True

    @property
    def effective_carry_speed(self) -> float:
        """実効運搬速度."""
        if self.carry_speed is not None:
            return self.carry_speed
        return self.base_speed


# --- プリセット定義 ---


def style_a() -> StyleParams:
    """Style A: ラケット載せ運搬."""
    return StyleParams(
        style_type=StyleType.A,
        capacity=5,
        base_speed=1.3,
        carry_speed=0.9,
        pick_time=2.0,
        gamma=0.04,
        requires_bending=True,
    )


def style_b() -> StyleParams:
    """Style B: 手拾い（しゃがみ移動・カゴ持ち）.

    しゃがんだ状態でカゴを持って移動し、ボールを拾って即カゴに入れる。
    カゴが手元にあるため拾い上げ→カゴ投入が速い（1.0秒/球）。
    ただし移動速度はしゃがみ姿勢のため遅い（0.7 m/s）。
    カゴ容量（50球）に達したらカートへ戻す。
    """
    return StyleParams(
        style_type=StyleType.B,
        capacity=50,
        base_speed=0.7,
        carry_speed=None,
        pick_time=1.0,
        gamma=0.005,
        requires_bending=True,
    )


def style_c_phase1() -> StyleParams:
    """Style C Phase 1: 打ち飛ばし集約フェーズ.

    ラケットで足元のボールをすくい、目標方向に飛ばす。
    屈伸動作は不要（立ったまま打てる）。
    """
    return StyleParams(
        style_type=StyleType.C,
        capacity=200,  # Phase 1では上限なし（打ち飛ばし続ける）
        base_speed=1.3,
        carry_speed=None,
        pick_time=2.5,
        gamma=0.0,
        requires_bending=False,
    )


def style_c() -> StyleParams:
    """Style C: ラケット打ち飛ばし集約（後方互換用）.

    Phase 1パラメータを返す。Phase 2はstyle_a()またはstyle_b()を使用。
    """
    return style_c_phase1()


def style_d() -> StyleParams:
    """Style D: ホッパー巡回."""
    return StyleParams(
        style_type=StyleType.D,
        capacity=72,
        base_speed=1.0,
        carry_speed=None,
        pick_time=1.5,
        gamma=0.0,
        requires_bending=False,
    )


def get_all_styles() -> dict[StyleType, StyleParams]:
    """全スタイルのパラメータ辞書を返す."""
    return {
        StyleType.A: style_a(),
        StyleType.B: style_b(),
        StyleType.C: style_c(),
        StyleType.D: style_d(),
    }


# --- 時間計算 ---


def pickup_time(n_balls: int, style: StyleParams) -> float:
    """n個のボールを拾い上げるのに要する時間 [秒]."""
    return n_balls * style.pick_time


def travel_time(distance: float, n_balls_carried: int, style: StyleParams) -> float:
    """移動にかかる時間 [秒].

    荷物による速度低下を考慮する。
    """
    v = speed_with_load(style.effective_carry_speed, n_balls_carried, style.gamma)
    if v <= 0:
        return float("inf")
    return distance / v


def trip_time(
    collect_distance: float,
    return_distance: float,
    n_balls: int,
    style: StyleParams,
) -> float:
    """1トリップ（拾い→運搬→カゴ投入）の所要時間 [秒].

    Args:
        collect_distance: ボール間の移動総距離 [m]
        return_distance: 最後のボールからカゴまでの距離 [m]
        n_balls: このトリップで拾うボール数
        style: 拾い方スタイル
    """
    t_pick = pickup_time(n_balls, style)
    t_collect = travel_time(collect_distance, 0, style)
    t_return = travel_time(return_distance, n_balls, style)
    return t_pick + t_collect + t_return


def estimate_total_time(
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
    style: StyleParams,
) -> float:
    """全ボール回収の推定時間 [秒].

    最近傍法（greedy nearest neighbor）で概算する。
    容量ごとにカゴへ往復する。

    Args:
        ball_positions: shape (N, 2) のボール座標
        basket_position: shape (2,) のカゴ座標
        style: 拾い方スタイル
    """
    n_balls = len(ball_positions)
    if n_balls == 0:
        return 0.0

    remaining = set(range(n_balls))
    current_pos = basket_position.copy()
    total_t = 0.0

    while remaining:
        # 1トリップ分を回収
        trip_balls = 0
        trip_distance = 0.0

        while remaining and trip_balls < style.capacity:
            # 最近傍を探す
            dists = {
                i: float(np.linalg.norm(ball_positions[i] - current_pos))
                for i in remaining
            }
            nearest = min(dists, key=dists.get)  # type: ignore[arg-type]
            trip_distance += dists[nearest]
            current_pos = ball_positions[nearest].copy()
            remaining.remove(nearest)
            trip_balls += 1

        # 拾い上げ時間
        total_t += pickup_time(trip_balls, style)
        # 移動時間（ボール間）
        if trip_distance > 0:
            total_t += travel_time(trip_distance, 0, style)
        # カゴへの帰還
        return_dist = float(np.linalg.norm(current_pos - basket_position))
        total_t += travel_time(return_dist, trip_balls, style)
        current_pos = basket_position.copy()

    return total_t


# --- Style C 打ち飛ばし比率最適化 ---


def estimate_mixed_style_c_time(
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
    hit_target: NDArray[np.float64],
    alpha: float,
    phase2_style: StyleParams | None = None,
    hit_sigma: float = 3.0,
    rng: np.random.Generator | None = None,
) -> float:
    """Style C混合戦略の所要時間を推定.

    ボールのうち比率αを打ち飛ばし、残り(1-α)を直接拾うの混合戦略。

    Args:
        ball_positions: shape (N, 2) のボール座標
        basket_position: shape (2,) のカゴ座標
        hit_target: shape (2,) 打ち飛ばし目標点
        alpha: 打ち飛ばし比率 [0, 1]
        phase2_style: Phase2（集約点回収）のスタイル。Noneならstyle_b()
        hit_sigma: 打ち飛ばし着地点のばらつき [m]
        rng: 乱数生成器

    Returns:
        混合戦略の推定総時間 [秒]
    """
    if rng is None:
        rng = np.random.default_rng()

    if phase2_style is None:
        phase2_style = style_b()

    n_balls = len(ball_positions)
    n_hit = int(n_balls * alpha)
    n_direct = n_balls - n_hit

    # 打ち飛ばすボール: カゴから遠い順に選択
    dists_to_basket = np.sqrt(np.sum((ball_positions - basket_position) ** 2, axis=1))
    sorted_indices = np.argsort(dists_to_basket)[::-1]
    hit_indices = sorted_indices[:n_hit]
    direct_indices = sorted_indices[n_hit:]

    total_time = 0.0

    # Phase 1: 打ち飛ばし
    if n_hit > 0:
        c_phase1 = style_c_phase1()
        hit_balls = ball_positions[hit_indices]
        total_time += estimate_total_time(hit_balls, basket_position, c_phase1)

        # Phase 2: 集約点からの回収
        # 打ち飛ばし先にばらつきを付与
        landed = np.tile(hit_target, (n_hit, 1)) + rng.normal(
            0, hit_sigma, size=(n_hit, 2)
        )
        total_time += estimate_total_time(landed, basket_position, phase2_style)

    # 直接拾い
    if n_direct > 0:
        direct_balls = ball_positions[direct_indices]
        total_time += estimate_total_time(direct_balls, basket_position, phase2_style)

    return total_time


def optimize_hit_ratio(
    ball_positions: NDArray[np.float64],
    basket_position: NDArray[np.float64],
    hit_target: NDArray[np.float64],
    phase2_style: StyleParams | None = None,
    n_alphas: int = 11,
    hit_sigma: float = 3.0,
    rng: np.random.Generator | None = None,
) -> dict[str, float]:
    """打ち飛ばし比率αの最適値を探索.

    α=0（全て直接拾い）〜α=1（全て打ち飛ばし）の範囲で
    グリッドサーチし、最小時間のαを返す。

    Returns:
        {"alpha": 最適α, "time": 最小時間, "time_all_direct": 全直接拾い時間}
    """
    if rng is None:
        rng = np.random.default_rng()

    alphas = np.linspace(0.0, 1.0, n_alphas)
    times = []

    for a in alphas:
        t = estimate_mixed_style_c_time(
            ball_positions,
            basket_position,
            hit_target,
            alpha=a,
            phase2_style=phase2_style,
            hit_sigma=hit_sigma,
            rng=np.random.default_rng(rng.integers(2**31)),
        )
        times.append(t)

    best_idx = int(np.argmin(times))
    return {
        "alpha": float(alphas[best_idx]),
        "time": times[best_idx],
        "time_all_direct": times[0],
    }

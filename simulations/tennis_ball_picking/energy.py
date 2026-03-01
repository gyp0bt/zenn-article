"""エネルギーモデル.

歩行・屈伸・運搬のエネルギーコストを定式化する。
仕様書 §5 に基づく中程度の粒度モデル。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class EnergyParams:
    """エネルギーモデルの物理パラメータ.

    Attributes:
        body_mass: 体重 [kg]
        alpha_0: 歩行コスト係数 定数項 [J/(kg·m)]
        alpha_1: 歩行コスト係数 1次項 [J·s/(kg·m²)]
        alpha_2: 歩行コスト係数 2次項 [J·s²/(kg·m³)]
        delta_h: 屈伸時の重心移動高さ [m]
        eta: 筋効率 [-]
        beta: 累積疲労係数 [-]
        ball_mass: ボール1個の質量 [kg]
        c_carry: 運搬姿勢制御コスト係数 [-]
        g: 重力加速度 [m/s²]
    """

    body_mass: float = 60.0
    alpha_0: float = 1.5
    alpha_1: float = 0.8
    alpha_2: float = 0.3
    delta_h: float = 0.35
    eta: float = 0.25
    beta: float = 0.007
    ball_mass: float = 0.058
    c_carry: float = 1.5
    g: float = 9.81


def walking_cost_per_kg_m(v: float, params: EnergyParams) -> float:
    """速度 v における歩行コスト係数 c_walk(v) [J/(kg·m)].

    c_walk(v) = α₀ + α₁·v + α₂·v²
    """
    return params.alpha_0 + params.alpha_1 * v + params.alpha_2 * v**2


def walking_energy(distance: float, speed: float, params: EnergyParams) -> float:
    """歩行エネルギー E_walk [J].

    E_walk(d, v) = c_walk(v) · m · d
    """
    c_walk = walking_cost_per_kg_m(speed, params)
    return c_walk * params.body_mass * distance


def bending_energy(n_th: int, params: EnergyParams) -> float:
    """n回目の屈伸エネルギー E_bend^(n) [J].

    E_bend = c_bend · m · g · Δh · η⁻¹
    E_bend^(n) = E_bend · (1 + β · n)

    Args:
        n_th: 何回目の屈伸か（0-indexed）
        params: エネルギーパラメータ
    """
    e_base = params.body_mass * params.g * params.delta_h / params.eta
    return e_base * (1.0 + params.beta * n_th)


def cumulative_bending_energy(n_bends: int, params: EnergyParams) -> float:
    """n回の屈伸の累積エネルギー [J].

    Σ_{i=0}^{n-1} E_bend^(i)
    """
    if n_bends <= 0:
        return 0.0
    indices = np.arange(n_bends)
    e_base = params.body_mass * params.g * params.delta_h / params.eta
    return float(np.sum(e_base * (1.0 + params.beta * indices)))


def carrying_energy(distance: float, n_balls: int, params: EnergyParams) -> float:
    """運搬エネルギー E_carry [J].

    E_carry(d, k) = c_carry · k · m_ball · g · d
    """
    return params.c_carry * n_balls * params.ball_mass * params.g * distance


def speed_with_load(base_speed: float, n_balls: int, gamma: float) -> float:
    """荷物による速度低下モデル.

    v(k) = v₀ · (1 - γ · k)

    Args:
        base_speed: 無荷重時の速度 [m/s]
        n_balls: 保持ボール数
        gamma: 速度低下係数 [1/球]

    Returns:
        低下後の速度 [m/s]（最低 0.1 m/s）
    """
    v = base_speed * (1.0 - gamma * n_balls)
    return max(v, 0.1)


def total_trip_energy(
    walk_distance: float,
    walk_speed: float,
    n_balls_picked: int,
    carry_distance: float,
    n_balls_carried: int,
    params: EnergyParams,
) -> dict[str, float]:
    """1トリップ（拾い→運搬→カゴ投入）の総エネルギーを計算.

    Returns:
        各コスト要素と合計のdict:
        - walk: 歩行エネルギー
        - bend: 屈伸エネルギー
        - carry: 運搬エネルギー
        - total: 合計
    """
    e_walk = walking_energy(walk_distance, walk_speed, params)
    e_bend = cumulative_bending_energy(n_balls_picked, params)
    e_carry = carrying_energy(carry_distance, n_balls_carried, params)
    return {
        "walk": e_walk,
        "bend": e_bend,
        "carry": e_carry,
        "total": e_walk + e_bend + e_carry,
    }

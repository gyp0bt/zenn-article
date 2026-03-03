"""ボール分布モデル.

球出し練習の種類に応じたボールの空間分布を
ガウス混合モデル（GMM）として定義する。

v3 変更点:
- ボール物理モデル追加: 着地後のバウンド・転がり・フェンス跳ね返り
  テニスボールは着地後にコート枠で停止せず、バウンドして
  バックフェンスまで転がったり、フェンスに当たって跳ね返る。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from .court import CourtGeometry


@dataclass
class BallZone:
    """ガウス混合モデルの1成分（ゾーン）."""

    name: str
    weight: float  # 混合重み w_k
    mu: NDArray[np.float64]  # 平均 (2,)
    sigma: NDArray[np.float64]  # 分散共分散行列 (2, 2)


@dataclass
class BallDistribution:
    """ボール分布モデル（ガウス混合モデル）.

    p(x) = Σ w_k * N(x | μ_k, Σ_k)
    """

    name: str
    zones: list[BallZone] = field(default_factory=list)

    def _validate_weights(self) -> None:
        """重みの合計が1であることを確認."""
        total = sum(z.weight for z in self.zones)
        if not np.isclose(total, 1.0, atol=1e-6):
            msg = f"ゾーン重みの合計が1ではありません: {total:.6f}"
            raise ValueError(msg)

    def sample(
        self,
        n_balls: int,
        court: CourtGeometry,
        rng: np.random.Generator | None = None,
    ) -> NDArray[np.float64]:
        """ガウス混合モデルからボール位置をサンプリング.

        有効領域外のサンプルは棄却・再サンプリングする。

        Args:
            n_balls: サンプリングするボール数
            court: コートジオメトリ（境界判定用）
            rng: 乱数生成器（再現性のため）

        Returns:
            shape (n_balls, 2) のボール座標配列
        """
        self._validate_weights()
        if rng is None:
            rng = np.random.default_rng()

        weights = np.array([z.weight for z in self.zones])
        samples = np.empty((0, 2))

        while samples.shape[0] < n_balls:
            remaining = n_balls - samples.shape[0]
            # 多めにサンプリング（棄却率を考慮）
            batch_size = int(remaining * 1.5) + 10

            # ゾーン割り当て
            zone_indices = rng.choice(len(self.zones), size=batch_size, p=weights)

            batch = np.empty((batch_size, 2))
            for k, zone in enumerate(self.zones):
                mask = zone_indices == k
                count = mask.sum()
                if count > 0:
                    batch[mask] = rng.multivariate_normal(
                        zone.mu, zone.sigma, size=count
                    )

            # 有効領域内のみ保持
            in_bounds = court.is_in_bounds(batch)
            samples = np.vstack([samples, batch[in_bounds]])

        return samples[:n_balls]


def apply_ball_rolling(
    landing_positions: NDArray[np.float64],
    court: CourtGeometry,
    rng: np.random.Generator | None = None,
    mean_roll: float = 3.0,
    mean_roll_net_miss: float = 1.0,
    mean_bounce_back: float = 0.5,
) -> NDArray[np.float64]:
    """着地後のバウンド・転がり・フェンス跳ね返りをシミュレート.

    テニスボールは着地後にコート枠で停止しない。
    バウンドしてバックフェンス側まで転がったり、
    フェンスに当たって跳ね返って戻ってきたりする。

    物理モデル:
    - ボールは打球方向（おおよそネットから離れる方向）に転がり続ける
    - 転がり距離は指数分布でモデル化（平均 mean_roll [m]）
    - フェンスに到達すると停止し、わずかに跳ね返る（平均 mean_bounce_back [m]）
    - ネット手前のミスショットは転がりが少ない（平均 mean_roll_net_miss [m]）

    Args:
        landing_positions: shape (N, 2) のボール着地位置
        court: コートジオメトリ（フェンス境界判定用）
        rng: 乱数生成器
        mean_roll: 通常ボールの平均転がり距離 [m]
        mean_roll_net_miss: ネットミスボールの平均転がり距離 [m]
        mean_bounce_back: フェンス跳ね返りの平均距離 [m]

    Returns:
        shape (N, 2) の最終静止位置
    """
    if rng is None:
        rng = np.random.default_rng()

    n = len(landing_positions)
    if n == 0:
        return landing_positions.copy()

    result = landing_positions.copy()

    # 転がり方向: ネット中心(0,0)から着地点への方向 + ランダムなゆらぎ
    directions = landing_positions.copy()
    norms = np.sqrt(np.sum(directions**2, axis=1, keepdims=True))
    norms = np.maximum(norms, 0.1)
    unit_dirs = directions / norms

    # 方向にランダムな角度ずれ（±17°程度）を加える
    base_angles = np.arctan2(unit_dirs[:, 1], unit_dirs[:, 0])
    angle_noise = rng.normal(0, 0.3, size=n)
    roll_angles = base_angles + angle_noise

    # 転がり距離: 指数分布
    roll_dists = rng.exponential(mean_roll, size=n)

    # ネット手前（y < 0）のボールは転がりが少ない（ネットに当たって落ちた球）
    net_miss_mask = landing_positions[:, 1] < 0
    n_net_miss = net_miss_mask.sum()
    if n_net_miss > 0:
        roll_dists[net_miss_mask] = rng.exponential(mean_roll_net_miss, size=n_net_miss)

    # 転がり適用
    result[:, 0] += roll_dists * np.cos(roll_angles)
    result[:, 1] += roll_dists * np.sin(roll_angles)

    # フェンス境界での跳ね返り
    # バックフェンス（北端）
    over_back = result[:, 1] > court.y_max
    if over_back.any():
        n_over = over_back.sum()
        bounce = rng.exponential(mean_bounce_back, size=n_over)
        result[over_back, 1] = court.y_max - bounce

    # 南フェンス
    over_south = result[:, 1] < court.y_min
    if over_south.any():
        n_over = over_south.sum()
        bounce = rng.exponential(mean_bounce_back, size=n_over)
        result[over_south, 1] = court.y_min + bounce

    # 東フェンス
    over_east = result[:, 0] > court.x_max
    if over_east.any():
        n_over = over_east.sum()
        bounce = rng.exponential(mean_bounce_back, size=n_over)
        result[over_east, 0] = court.x_max - bounce

    # 西フェンス
    over_west = result[:, 0] < court.x_min
    if over_west.any():
        n_over = over_west.sum()
        bounce = rng.exponential(mean_bounce_back, size=n_over)
        result[over_west, 0] = court.x_min + bounce

    # 最終的に有効領域内にクランプ
    result[:, 0] = np.clip(result[:, 0], court.x_min, court.x_max)
    result[:, 1] = np.clip(result[:, 1], court.y_min, court.y_max)

    return result


def create_stroke_distribution(court: CourtGeometry) -> BallDistribution:
    """ストローク練習モデル（基本モデル）を生成.

    コーチが片側（南側）から球出しし、生徒が対面コート（北側）に
    打ち返す状況を想定。

    ゾーン構成:
        - ベースライン帯（北側）: 60%
        - ネット帯: 15%
        - サイド帯: 15%（左右7.5%ずつ）
        - バックフェンス帯（北側後方）: 10%
    """
    hl = court.half_length

    zones = [
        # ベースライン帯（北側ベースライン ±3m）
        BallZone(
            name="ベースライン帯",
            weight=0.60,
            mu=np.array([0.0, hl]),
            sigma=np.array([[6.0, 0.0], [0.0, 3.0]]),
        ),
        # ネット帯（ネット ±2m）
        BallZone(
            name="ネット帯",
            weight=0.15,
            mu=np.array([0.0, 0.0]),
            sigma=np.array([[8.0, 0.0], [0.0, 1.5]]),
        ),
        # サイド帯（左）
        BallZone(
            name="サイド帯（左）",
            weight=0.075,
            mu=np.array([-(court.doubles_width / 2 + 1.0), hl * 0.3]),
            sigma=np.array([[1.5, 0.0], [0.0, 15.0]]),
        ),
        # サイド帯（右）
        BallZone(
            name="サイド帯（右）",
            weight=0.075,
            mu=np.array([court.doubles_width / 2 + 1.0, hl * 0.3]),
            sigma=np.array([[1.5, 0.0], [0.0, 15.0]]),
        ),
        # バックフェンス帯（北側後方スペース）
        BallZone(
            name="バックフェンス帯",
            weight=0.10,
            mu=np.array([0.0, hl + court.back_space * 0.6]),
            sigma=np.array([[5.0, 0.0], [0.0, 2.0]]),
        ),
    ]

    return BallDistribution(name="ストローク練習", zones=zones)


def create_volley_distribution(court: CourtGeometry) -> BallDistribution:
    """ボレー練習モデル（拡張モデル）を生成.

    ネット〜サービスライン間に集中する分布。
    """
    sv = court.service_line_dist

    zones = [
        # サービスボックス中央（北側）
        BallZone(
            name="サービスボックス（北）",
            weight=0.50,
            mu=np.array([0.0, sv / 2]),
            sigma=np.array([[5.0, 0.0], [0.0, 3.0]]),
        ),
        # サービスボックス中央（南側）
        BallZone(
            name="サービスボックス（南）",
            weight=0.30,
            mu=np.array([0.0, -sv / 2]),
            sigma=np.array([[5.0, 0.0], [0.0, 3.0]]),
        ),
        # ネット際
        BallZone(
            name="ネット際",
            weight=0.20,
            mu=np.array([0.0, 0.0]),
            sigma=np.array([[6.0, 0.0], [0.0, 1.0]]),
        ),
    ]

    return BallDistribution(name="ボレー練習", zones=zones)


def create_cross_dtl_distribution(court: CourtGeometry) -> BallDistribution:
    """クロス・ダウンザライン分布モデルを生成.

    球出し練習でクロスやダウンザラインに配球するため、
    ボールがコート後方かつ角（コーナー）に集中する分布。
    ネットミスによりネット手前にも溜まる。

    注意: このGMMはボールの「着地位置」を表す。実際のボールは
    着地後にバウンド・転がりが発生するため、最終静止位置は
    apply_ball_rolling() で補正する必要がある。

    ゾーン構成:
        - クロスコーナー左（北側左角）: 25%
        - クロスコーナー右（北側右角）: 25%
        - DTLコーナー左（北側左端）: 10%
        - DTLコーナー右（北側右端）: 10%
        - ネットミス帯（ネット手前・南側）: 20%
        - バックフェンス帯（北側後方）: 10%
    """
    hl = court.half_length
    hw_s = court.singles_width / 2

    zones = [
        # クロスコーナー左（北側ベースライン左角）
        BallZone(
            name="クロスコーナー（左）",
            weight=0.25,
            mu=np.array([-hw_s + 1.0, hl - 1.0]),
            sigma=np.array([[2.5, 0.3], [0.3, 2.0]]),
        ),
        # クロスコーナー右（北側ベースライン右角）
        BallZone(
            name="クロスコーナー（右）",
            weight=0.25,
            mu=np.array([hw_s - 1.0, hl - 1.0]),
            sigma=np.array([[2.5, -0.3], [-0.3, 2.0]]),
        ),
        # DTLコーナー左（北側左端サイドライン際）
        BallZone(
            name="DTLコーナー（左）",
            weight=0.10,
            mu=np.array([-hw_s, hl - 2.0]),
            sigma=np.array([[1.5, 0.0], [0.0, 3.0]]),
        ),
        # DTLコーナー右（北側右端サイドライン際）
        BallZone(
            name="DTLコーナー（右）",
            weight=0.10,
            mu=np.array([hw_s, hl - 2.0]),
            sigma=np.array([[1.5, 0.0], [0.0, 3.0]]),
        ),
        # ネットミス帯（ネット手前・南側に落ちる）
        BallZone(
            name="ネットミス帯",
            weight=0.20,
            mu=np.array([0.0, -2.0]),
            sigma=np.array([[8.0, 0.0], [0.0, 1.5]]),
        ),
        # バックフェンス帯（深い球のオーバー）
        BallZone(
            name="バックフェンス帯",
            weight=0.10,
            mu=np.array([0.0, hl + court.back_space * 0.5]),
            sigma=np.array([[5.0, 0.0], [0.0, 2.0]]),
        ),
    ]

    return BallDistribution(name="クロス・ダウンザライン", zones=zones)

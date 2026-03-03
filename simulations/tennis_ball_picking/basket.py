"""カゴ配置モデル.

4カゴ + 中央カートの運用をモデル化する。
仕様書 §3.4 に基づき、カゴ配置の最適化（k-medians問題）と
カゴ満杯時のカート戻し動作を扱う。

v3 変更点:
- カート移動モデル: カートは移動可能（車輪付き）で位置を最適化できる
- カゴ使い捨てモデル: いっぱいになったカゴはカートに戻し、
  ボールは空にならず（カゴごとカートに載せる）、空きカゴが1つ減る。
  カゴの再利用はない。
- 容量制約付きカゴ割り当て: 各カゴの最大容量を超えないように割り当て
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .court import CourtGeometry


@dataclass(frozen=True)
class BasketConfig:
    """カゴ・カートの構成パラメータ.

    カートは車輪付きで移動可能。いっぱいになったカゴは
    カートに載せて戻す（ボールは空にしない）。
    戻すたびに空きカゴが1つ減る。

    Attributes:
        n_baskets: カゴ数
        basket_capacity: 1カゴあたりの容量 [球]
        cart_position: カート位置 (2,)。移動可能なので最適位置に配置可能
        dump_time: カゴ→カート搬送時間 [秒]（カゴをカートまで運んで載せる時間）
    """

    n_baskets: int = 4
    basket_capacity: int = 50
    cart_position: NDArray[np.float64] | None = None
    dump_time: float = 10.0

    def get_cart_position(self, court: CourtGeometry) -> NDArray[np.float64]:
        """カート位置を取得（デフォルトはネット脇）."""
        if self.cart_position is not None:
            return self.cart_position
        return court.default_basket_position()

    @property
    def total_capacity(self) -> int:
        """全カゴの合計容量."""
        return self.n_baskets * self.basket_capacity


def assign_balls_to_baskets(
    ball_positions: NDArray[np.float64],
    basket_positions: NDArray[np.float64],
) -> NDArray[np.intp]:
    """各ボールを最近傍のカゴに割り当てる.

    Args:
        ball_positions: shape (N, 2) のボール座標
        basket_positions: shape (K, 2) のカゴ座標

    Returns:
        shape (N,) の割り当てインデックス（各ボールの最近傍カゴ番号）
    """
    # (N, 1, 2) - (1, K, 2) → (N, K, 2) → (N, K)
    diff = ball_positions[:, np.newaxis, :] - basket_positions[np.newaxis, :, :]
    dists = np.sqrt(np.sum(diff**2, axis=2))
    return np.argmin(dists, axis=1)


def assign_balls_to_baskets_with_capacity(
    ball_positions: NDArray[np.float64],
    basket_positions: NDArray[np.float64],
    basket_capacity: int = 50,
) -> NDArray[np.intp]:
    """容量制約付きで各ボールを最近傍のカゴに割り当てる.

    各カゴはbasket_capacity球までしか受け入れない。
    いっぱいになったカゴは空きカゴが減るモデルに対応し、
    溢れたボールは次に近いカゴに再割り当てされる。

    Args:
        ball_positions: shape (N, 2) のボール座標
        basket_positions: shape (K, 2) のカゴ座標
        basket_capacity: 1カゴあたりの最大容量

    Returns:
        shape (N,) の割り当てインデックス
    """
    n_balls = len(ball_positions)
    n_baskets = len(basket_positions)

    # 全ボールと全カゴの距離行列 (N, K)
    diff = ball_positions[:, np.newaxis, :] - basket_positions[np.newaxis, :, :]
    dists = np.sqrt(np.sum(diff**2, axis=2))

    assignments = np.full(n_balls, -1, dtype=np.intp)
    basket_counts = np.zeros(n_baskets, dtype=int)

    # 距離が近い順にソートして、貪欲に割り当て
    # 各ボールについて近い順のカゴリストを作る
    sorted_baskets = np.argsort(dists, axis=1)  # (N, K)

    # カゴまでの距離が近いボールから優先的に割り当て
    min_dists = dists.min(axis=1)
    ball_order = np.argsort(min_dists)

    for i in ball_order:
        for k in sorted_baskets[i]:
            if basket_counts[k] < basket_capacity:
                assignments[i] = k
                basket_counts[k] += 1
                break

    # 割り当てられなかったボールは最も近いカゴに強制割り当て
    unassigned = assignments == -1
    if unassigned.any():
        assignments[unassigned] = np.argmin(dists[unassigned], axis=1)

    return assignments


def optimize_basket_placement(
    ball_positions: NDArray[np.float64],
    n_baskets: int = 4,
    max_iterations: int = 50,
    rng: np.random.Generator | None = None,
) -> NDArray[np.float64]:
    """k-mediansでカゴ配置を最適化.

    ボールからの最近傍カゴまでの総距離を最小化する配置を求める。
    Weiszfeldアルゴリズムの簡易版（k-means初期化 + 中央値更新）。

    Args:
        ball_positions: shape (N, 2) のボール座標
        n_baskets: カゴ数
        max_iterations: 最大反復回数
        rng: 乱数生成器

    Returns:
        shape (K, 2) の最適カゴ配置
    """
    if rng is None:
        rng = np.random.default_rng()

    n_balls = len(ball_positions)
    if n_balls <= n_baskets:
        # ボール数がカゴ数以下なら各ボールにカゴを配置
        result = np.zeros((n_baskets, 2))
        result[:n_balls] = ball_positions
        return result

    # k-means++風初期化
    centers = _kmeans_plus_plus_init(ball_positions, n_baskets, rng)

    for _ in range(max_iterations):
        # 割り当て
        assignments = assign_balls_to_baskets(ball_positions, centers)

        # 中央値で更新（k-medians）
        new_centers = np.zeros_like(centers)
        for k in range(n_baskets):
            mask = assignments == k
            if mask.sum() > 0:
                new_centers[k] = np.median(ball_positions[mask], axis=0)
            else:
                new_centers[k] = centers[k]

        # 収束判定
        if np.allclose(centers, new_centers, atol=1e-6):
            break
        centers = new_centers

    return centers


def _kmeans_plus_plus_init(
    positions: NDArray[np.float64],
    k: int,
    rng: np.random.Generator,
) -> NDArray[np.float64]:
    """k-means++風の初期化."""
    n = len(positions)
    centers = np.empty((k, 2))

    # 最初の中心をランダムに選択
    idx = rng.integers(n)
    centers[0] = positions[idx]

    for i in range(1, k):
        # 各点から最近中心までの距離
        diffs = positions[:, np.newaxis, :] - centers[:i][np.newaxis, :, :]
        dists = np.sqrt(np.sum(diffs**2, axis=2))
        min_dists = np.min(dists, axis=1)

        # 距離に比例する確率で次の中心を選択
        probs = min_dists**2
        total = probs.sum()
        if total > 0:
            probs /= total
        else:
            probs = np.ones(n) / n
        idx = rng.choice(n, p=probs)
        centers[i] = positions[idx]

    return centers


def compute_basket_distances(
    ball_positions: NDArray[np.float64],
    basket_positions: NDArray[np.float64],
    assignments: NDArray[np.intp],
) -> NDArray[np.float64]:
    """各ボールから割り当てカゴまでの距離を計算.

    Args:
        ball_positions: shape (N, 2)
        basket_positions: shape (K, 2)
        assignments: shape (N,) 各ボールのカゴ番号

    Returns:
        shape (N,) の距離配列
    """
    assigned_baskets = basket_positions[assignments]
    diff = ball_positions - assigned_baskets
    return np.sqrt(np.sum(diff**2, axis=1))


def total_basket_distance(
    ball_positions: NDArray[np.float64],
    basket_positions: NDArray[np.float64],
) -> float:
    """全ボールから最近傍カゴまでの総距離.

    カゴ配置の評価関数として使用する。
    """
    assignments = assign_balls_to_baskets(ball_positions, basket_positions)
    distances = compute_basket_distances(ball_positions, basket_positions, assignments)
    return float(np.sum(distances))

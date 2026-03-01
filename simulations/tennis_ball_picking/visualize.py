"""可視化モジュール.

テニスコートとボール分布を描画する。
記事用の図表生成に使用する。
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from numpy.typing import NDArray

from .court import CourtGeometry


def draw_court(ax: Axes, court: CourtGeometry) -> None:
    """テニスコートのライン描画.

    Args:
        ax: matplotlib Axes
        court: コートジオメトリ
    """
    hl = court.half_length
    hw_d = court.doubles_width / 2
    hw_s = court.singles_width / 2
    sv = court.service_line_dist

    # ダブルスコート外枠
    rect_x = [-hw_d, hw_d, hw_d, -hw_d, -hw_d]
    rect_y = [-hl, -hl, hl, hl, -hl]
    ax.plot(rect_x, rect_y, "w-", linewidth=1.5)

    # シングルスサイドライン
    ax.plot([-hw_s, -hw_s], [-hl, hl], "w-", linewidth=0.8, alpha=0.7)
    ax.plot([hw_s, hw_s], [-hl, hl], "w-", linewidth=0.8, alpha=0.7)

    # サービスライン
    ax.plot([-hw_s, hw_s], [sv, sv], "w-", linewidth=0.8, alpha=0.7)
    ax.plot([-hw_s, hw_s], [-sv, -sv], "w-", linewidth=0.8, alpha=0.7)

    # センターサービスライン
    ax.plot([0, 0], [-sv, sv], "w-", linewidth=0.8, alpha=0.7)

    # ネット
    ax.plot([-hw_d - 0.5, hw_d + 0.5], [0, 0], "w-", linewidth=2.0)

    # 有効領域の枠
    ax.plot(
        [court.x_min, court.x_max, court.x_max, court.x_min, court.x_min],
        [court.y_min, court.y_min, court.y_max, court.y_max, court.y_min],
        "w--",
        linewidth=0.5,
        alpha=0.3,
    )


def plot_ball_distribution(
    ball_positions: NDArray[np.float64],
    court: CourtGeometry,
    title: str = "ボール分布",
    basket_position: NDArray[np.float64] | None = None,
    figsize: tuple[float, float] = (8, 12),
    save_path: str | Path | None = None,
) -> Figure:
    """ボール分布をコート上にプロット.

    Args:
        ball_positions: shape (N, 2) のボール座標
        court: コートジオメトリ
        title: プロットタイトル
        basket_position: カゴ位置（Noneの場合はデフォルト位置）
        figsize: 図のサイズ
        save_path: 保存先パス（Noneの場合は保存しない）

    Returns:
        matplotlib Figure
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # 背景をコート色（緑系）に
    ax.set_facecolor("#2d5a27")

    # コートラインを描画
    draw_court(ax, court)

    # ボールを描画
    ax.scatter(
        ball_positions[:, 0],
        ball_positions[:, 1],
        c="#ccff00",
        s=15,
        alpha=0.7,
        edgecolors="none",
        zorder=3,
    )

    # カゴ位置
    if basket_position is None:
        basket_position = court.default_basket_position()
    ax.plot(
        basket_position[0],
        basket_position[1],
        "rs",
        markersize=10,
        zorder=4,
        label="カゴ",
    )

    ax.set_xlim(court.x_min - 0.5, court.x_max + 0.5)
    ax.set_ylim(court.y_min - 0.5, court.y_max + 0.5)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=14, color="white", pad=10)
    ax.set_xlabel("x [m]", color="white")
    ax.set_ylabel("y [m]", color="white")
    ax.tick_params(colors="white")
    ax.legend(
        loc="upper left", facecolor="#2d5a27", edgecolor="white", labelcolor="white"
    )
    fig.patch.set_facecolor("#1a1a1a")
    fig.tight_layout()

    if save_path is not None:
        fig.savefig(
            save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor()
        )

    return fig


def plot_distribution_comparison(
    distributions: dict[str, NDArray[np.float64]],
    court: CourtGeometry,
    save_path: str | Path | None = None,
) -> Figure:
    """複数の分布を横並びで比較プロット.

    Args:
        distributions: {名前: ボール座標配列} の辞書
        court: コートジオメトリ
        save_path: 保存先パス
    """
    n = len(distributions)
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 12))
    if n == 1:
        axes = [axes]

    for ax, (name, positions) in zip(axes, distributions.items()):
        ax.set_facecolor("#2d5a27")
        draw_court(ax, court)
        ax.scatter(
            positions[:, 0],
            positions[:, 1],
            c="#ccff00",
            s=12,
            alpha=0.6,
            edgecolors="none",
        )
        ax.set_xlim(court.x_min - 0.5, court.x_max + 0.5)
        ax.set_ylim(court.y_min - 0.5, court.y_max + 0.5)
        ax.set_aspect("equal")
        ax.set_title(name, fontsize=12, color="white", pad=10)
        ax.set_xlabel("x [m]", color="white")
        ax.set_ylabel("y [m]", color="white")
        ax.tick_params(colors="white")

    fig.patch.set_facecolor("#1a1a1a")
    fig.tight_layout()

    if save_path is not None:
        fig.savefig(
            save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor()
        )

    return fig


def plot_energy_profile(
    styles_data: dict[str, dict[str, float]],
    save_path: str | Path | None = None,
) -> Figure:
    """各スタイルのエネルギープロファイルを棒グラフで比較.

    Args:
        styles_data: {スタイル名: {"walk": val, "bend": val, "carry": val}}
        save_path: 保存先パス
    """
    style_names = list(styles_data.keys())
    components = ["walk", "bend", "carry"]
    colors = ["#4a90d9", "#e8a838", "#d94a4a"]
    labels = ["歩行", "屈伸", "運搬"]

    x = np.arange(len(style_names))
    width = 0.6

    fig, ax = plt.subplots(figsize=(10, 6))
    bottom = np.zeros(len(style_names))

    for comp, color, label in zip(components, colors, labels):
        values = [styles_data[s].get(comp, 0) for s in style_names]
        ax.bar(x, values, width, bottom=bottom, label=label, color=color)
        bottom += np.array(values)

    ax.set_xticks(x)
    ax.set_xticklabels(style_names)
    ax.set_ylabel("エネルギー [J]")
    ax.set_title("スタイル別エネルギーコスト比較")
    ax.legend()
    fig.tight_layout()

    if save_path is not None:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig

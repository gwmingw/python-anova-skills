"""Reusable Matplotlib appearance for the user's report figures.

No data, model, axis limits, or backend is selected by this module.
Requires matplotlib. Apply appearance after any other library theme.
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


COLORS = {
    "ink": "#263746",
    "muted": "#647482",
    "grid": "#DCE3E8",
    "data": "#4C78A8",
    "secondary": "#54A28B",
    "threshold": "#C7774E",
}
SCATTER_KW = {"s": 49, "marker": "o", "color": COLORS["data"], "zorder": 4}
FIT_LINE_KW = {"color": COLORS["data"], "linewidth": 2, "linestyle": ":", "zorder": 3}
REFERENCE_LINE_KW = {
    "color": COLORS["threshold"], "linewidth": 1.2, "linestyle": ":", "zorder": 2,
}
LAYOUTS = {
    "single": {
        "shape": (1, 1), "figsize": (9, 5.8), "caption_y": 0.055,
        "adjust": {"left": 0.12, "right": 0.98, "top": 0.92, "bottom": 0.22},
    },
    "horizontal": {
        "shape": (1, 2), "figsize": (14, 5.8), "caption_y": 0.055,
        "adjust": {"left": 0.07, "right": 0.98, "top": 0.88, "bottom": 0.22, "wspace": 0.18},
    },
    "vertical": {
        "shape": (2, 1), "figsize": (9, 10.8), "caption_y": 0.035,
        "adjust": {"left": 0.12, "right": 0.98, "top": 0.94, "bottom": 0.12, "hspace": 0.38},
    },
}


def apply_style():
    """Apply shared typography and palette without changing the backend."""
    plt.rcParams.update({
        "font.family": ["Arial", "DejaVu Sans"],
        "font.size": 11,
        "axes.labelcolor": COLORS["ink"],
        "axes.edgecolor": COLORS["grid"],
        "axes.labelpad": 9,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlepad": 13,
        "xtick.color": COLORS["muted"],
        "ytick.color": COLORS["muted"],
        "text.color": COLORS["ink"],
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 300,
        "legend.frameon": False,
        "legend.fontsize": 9,
    })


def make_figure(layout="single", *, sharex=False, sharey=False):
    """Return (figure, axes) using a single, horizontal, or vertical preset."""
    config = LAYOUTS[layout]
    apply_style()
    fig, axes = plt.subplots(*config["shape"], figsize=config["figsize"],
                             sharex=sharex, sharey=sharey)
    fig.subplots_adjust(**config["adjust"])
    return fig, axes


def style_axes(ax, *, x_label=None, y_label=None, grid_axis="both",
               percent_axis=None, percent_xmax=100, percent_decimals=0,
               show_x_tick_labels=None):
    """Format axes without changing data limits or tick positions.

    percent_axis: None, 'x', 'y', or 'both'. percent_xmax is the value
    representing 100% (100 for percentages, 1 for proportions).
    grid_axis: None (no grid), 'x', 'y', or 'both'.
    """
    if percent_axis not in (None, "x", "y", "both"):
        raise ValueError("percent_axis must be None, 'x', 'y', or 'both'")
    if percent_axis is not None and percent_xmax <= 0:
        raise ValueError("percent_xmax must be positive")
    if grid_axis not in (None, "x", "y", "both"):
        raise ValueError("grid_axis must be None, 'x', 'y', or 'both'")
    if x_label is not None:
        ax.set_xlabel(x_label, labelpad=9)
    if y_label is not None:
        ax.set_ylabel(y_label, labelpad=9)
    for name in ("x", "y"):
        if percent_axis in (name, "both"):
            getattr(ax, name + "axis").set_major_formatter(
                PercentFormatter(xmax=percent_xmax, decimals=percent_decimals)
            )
    ax.grid(False, which="both", axis="both")
    if grid_axis is not None:
        ax.grid(axis=grid_axis, color=COLORS["grid"], linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    for name in ("left", "bottom"):
        ax.spines[name].set_color(COLORS["grid"])
    ax.tick_params(axis="both", which="both", length=0, colors=COLORS["muted"], pad=7)
    if show_x_tick_labels is not None:
        ax.tick_params(axis="x", labelbottom=show_x_tick_labels)


def add_caption(fig, text, *, layout="single", y=None):
    """Add a centered bottom caption; margins come from make_figure()."""
    return fig.text(0.5, LAYOUTS[layout]["caption_y"] if y is None else y,
                    text, ha="center", fontsize=12, fontweight="bold",
                    color=COLORS["ink"])


def save_figure(fig, path, *, dpi=300):
    """Save a figure at the explicit output path and return its absolute path."""
    path = Path(path).resolve()
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    return path

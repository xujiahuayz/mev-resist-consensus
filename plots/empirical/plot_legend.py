"""Shared legend strip for the empirical-section panels.

The four empirical plots (gas timeseries, gas-fee CDF, Lorenz, inversion
CDF) are laid out as two side-by-side figure pairs in the paper. Each
panel would duplicate the same 7-entry legend, wasting ~25% of the panel
area. This script builds that legend once as a thin horizontal strip
that the paper places above each pair.

Imports style constants from _style.py so the strip can never drift out
of sync with the panels.

Writes:  figures/empirical/legend.pdf
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from plots.empirical._style import (
    PERIODS, PERIOD_LABELS, PERIOD_LINESTYLE,
    SIM_LINESTYLE, SIM_COLOR, SIM_LABEL,
    period_palette,
)

OUT_PATH = PROJECT_ROOT / "figures" / "empirical" / "legend.pdf"


def main():
    period_color = period_palette()

    handles = [
        Line2D(
            [0], [0],
            color=period_color[p],
            linestyle=PERIOD_LINESTYLE[p],
            linewidth=2.5,
            label=PERIOD_LABELS[p],
        )
        for p in PERIODS
    ]
    handles.append(
        Line2D(
            [0], [0],
            color=SIM_COLOR,
            linestyle=SIM_LINESTYLE,
            linewidth=2.0,
            label=SIM_LABEL,
        )
    )

    fig = plt.figure(figsize=(16, 2.0))
    fig.legend(
        handles=handles,
        ncol=4,
        loc="center",
        frameon=False,
        fontsize=28,
        handlelength=3.5,
        handletextpad=0.8,
        columnspacing=1.6,
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()

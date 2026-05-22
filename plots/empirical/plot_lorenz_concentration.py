"""
Lorenz curves: real Ethereum block-producer concentration per period.

This figure plays a single role: it documents the *real-world counterfactual*
that any protocol change (ePBS) should improve on (or, at minimum, not
worsen). The simulated PoS curve is included for visual context, but it
sits on the equality diagonal **by construction** — the model selects from
a small uniform validator set, so the diagonal is a property of the
modelling choice, not a calibration result. Do not read the simulated
curve as a calibration claim.

Reads:   data/empirical/miner_block_counts.csv
         data/empirical/sim_baseline_validator_counts.csv  (optional context)
Writes:  figures/empirical/lorenz_concentration.pdf
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from plots.empirical._style import (
    PERIODS, PERIOD_LABELS, PERIOD_LINESTYLE, SIM_LINESTYLE, period_palette,
)

DATA_PATH     = PROJECT_ROOT / "data" / "empirical" / "miner_block_counts.csv"
SIM_DATA_PATH = PROJECT_ROOT / "data" / "empirical" / "sim_baseline_validator_counts.csv"
OUT_PATH      = PROJECT_ROOT / "figures" / "empirical" / "lorenz_concentration.pdf"


def lorenz_curve(counts):
    arr = np.sort(np.array(counts, dtype=float))
    n = len(arr)
    cum_blocks = np.cumsum(arr)
    x = np.linspace(0, 1, n + 1)
    y = np.concatenate([[0], cum_blocks / cum_blocks[-1]])
    return x, y


def main():
    if not DATA_PATH.exists():
        print(f"Missing {DATA_PATH}. Run scripts/run_empirical_analysis.py first.")
        return

    df     = pd.read_csv(DATA_PATH)
    sim_df = pd.read_csv(SIM_DATA_PATH) if SIM_DATA_PATH.exists() else None

    period_color = period_palette()

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot([0, 1], [0, 1], color="dimgrey", linestyle=":", linewidth=1.8)

    for period in PERIODS:
        sub = df[df["period"] == period]["block_count"].dropna().tolist()
        if len(sub) == 0:
            continue
        x, y = lorenz_curve(sub)
        ax.plot(
            x, y,
            color=period_color[period],
            linestyle=PERIOD_LINESTYLE[period],
            linewidth=2.5,
        )

        if sim_df is not None:
            sim_sub = sim_df[sim_df["period"] == period]["block_count"].dropna().tolist()
            if len(sim_sub) > 0:
                sx, sy = lorenz_curve(sim_sub)
                ax.plot(
                    sx, sy,
                    color=period_color[period],
                    linestyle=SIM_LINESTYLE,
                    linewidth=2.0,
                    alpha=0.6,
                )

    ax.set_xlabel("Cumulative share of producers", fontsize=30)
    ax.set_ylabel("Cumulative share of blocks", fontsize=30)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.tick_params(axis="both", labelsize=28)

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()

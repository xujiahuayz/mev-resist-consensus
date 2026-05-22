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
from matplotlib.lines import Line2D

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from blockchain_env.sim_config import VALIDATORS

DATA_PATH     = PROJECT_ROOT / "data" / "empirical" / "miner_block_counts.csv"
SIM_DATA_PATH = PROJECT_ROOT / "data" / "empirical" / "sim_baseline_validator_counts.csv"
OUT_PATH      = PROJECT_ROOT / "figures" / "empirical" / "lorenz_concentration.pdf"

PERIODS = [
    "STABLE_PRE_MERGE_2022",
    "STABLE_POST_MERGE_2022",
    "STABLE_POST_MERGE_2023",
    "FTX_COLLAPSE_NOV_2022",
    "LUNA_CRASH_MAY_2022",
    "USDC_DEPEG_MARCH_2023",
]

PERIOD_LABELS = {
    "STABLE_PRE_MERGE_2022":  "Stable (pre-merge)",
    "STABLE_POST_MERGE_2022": "Stable post-merge 2022",
    "STABLE_POST_MERGE_2023": "Stable post-merge 2023",
    "FTX_COLLAPSE_NOV_2022":  "FTX collapse",
    "LUNA_CRASH_MAY_2022":    "Luna crash",
    "USDC_DEPEG_MARCH_2023":  "USDC depeg",
}

PERIOD_LINESTYLE = {
    "STABLE_PRE_MERGE_2022":  "-",
    "STABLE_POST_MERGE_2022": "-",
    "STABLE_POST_MERGE_2023": "-",
    "FTX_COLLAPSE_NOV_2022":  "--",
    "LUNA_CRASH_MAY_2022":    "--",
    "USDC_DEPEG_MARCH_2023":  "--",
}


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

    palette = sns.color_palette("ch:rot=-.25,hue=1,light=.75", len(PERIODS) + 1)
    period_color = {p: palette[i + 1] for i, p in enumerate(PERIODS)}

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot([0, 1], [0, 1], color="dimgrey", linestyle=":", linewidth=1.8)

    legend_handles = [
        Line2D([0], [0], color="dimgrey", linestyle=":", linewidth=1.8,
               label="Perfect equality"),
    ]

    for period in PERIODS:
        sub = df[df["period"] == period]["block_count"].dropna().tolist()
        if len(sub) == 0:
            continue
        x, y = lorenz_curve(sub)
        line, = ax.plot(
            x, y,
            color=period_color[period],
            linestyle=PERIOD_LINESTYLE[period],
            linewidth=2.5,
            label=PERIOD_LABELS[period],
        )
        legend_handles.append(line)

        if sim_df is not None:
            sim_sub = sim_df[sim_df["period"] == period]["block_count"].dropna().tolist()
            if len(sim_sub) > 0:
                sx, sy = lorenz_curve(sim_sub)
                ax.plot(
                    sx, sy,
                    color=period_color[period],
                    linestyle=":",
                    linewidth=2.0,
                    alpha=0.6,
                )

    if sim_df is not None and len(sim_df) > 0:
        legend_handles.append(Line2D(
            [0], [0], color="dimgrey", linestyle=":", linewidth=2.0,
            label=f"PoS sim ({VALIDATORS} validators, uniform)",
        ))

    ax.set_xlabel("Cumulative share of producers", fontsize=22)
    ax.set_ylabel("Cumulative share of blocks", fontsize=22)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.tick_params(axis="both", labelsize=18)
    ax.legend(handles=legend_handles, fontsize=14, frameon=True, loc="upper left")

    # Annotate the role of this figure right on the plot — no implied calibration claim.
    ax.text(
        0.98, 0.02,
        f"Simulated curve hugs diagonal by construction\n"
        f"({VALIDATORS} validators, uniform selection)",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=11, color="dimgrey",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="lightgrey", alpha=0.8),
    )

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()

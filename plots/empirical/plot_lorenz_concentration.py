"""
Lorenz curves for miner block production concentration by market period.

Reads:   data/empirical/miner_block_counts.csv
         data/empirical/sim_baseline_validator_counts.csv  (optional)
Writes:  figures/empirical/lorenz_concentration.pdf

Solid lines: real Ethereum miner concentration.
Dotted lines (same color): PoS simulation validator concentration (10 validators,
50% MEV). Simulation curves sit closer to the equality diagonal because the model
has far fewer validators than real Ethereum — the comparison shows that even a
small PoS network is far less concentrated than real miner pools.
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
    """Return (x, y) for the Lorenz curve of block counts."""
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

    # Perfect equality diagonal
    ax.plot([0, 1], [0, 1], color="dimgrey", linestyle=":", linewidth=1.8,
            label="Perfect equality")

    from matplotlib.lines import Line2D
    legend_handles = []
    eq_handle = Line2D([0], [0], color="dimgrey", linestyle=":", linewidth=1.8,
                       label="Perfect equality")
    legend_handles.append(eq_handle)

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

        # Overlay simulation validator concentration for the same period
        if sim_df is not None:
            sim_sub = sim_df[sim_df["period"] == period]["block_count"].dropna().tolist()
            if len(sim_sub) > 0:
                sx, sy = lorenz_curve(sim_sub)
                ax.plot(
                    sx, sy,
                    color=period_color[period],
                    linestyle=":",
                    linewidth=2.0,
                    alpha=0.75,
                )

    if sim_df is not None and len(sim_df) > 0:
        sim_handle = Line2D([0], [0], color="dimgrey", linestyle=":", linewidth=2.0,
                            label="Simulation (50% MEV)")
        legend_handles.append(sim_handle)

    ax.set_xlabel("Cumulative Share of Miners", fontsize=30)
    ax.set_ylabel("Cumulative Share of Blocks", fontsize=30, y=0.4)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.tick_params(axis="both", labelsize=28)
    ax.legend(handles=legend_handles, fontsize=20, frameon=True, loc="upper left")

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()

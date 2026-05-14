"""
Empirical CDF of per-block transaction ordering inversion rates by market period.

Reads:   data/empirical/ordering_inversions.csv
Writes:  figures/empirical/inversion_ecdf.pdf

Each data point is one block's inversion_rate = inversion_count / max_possible.
An inversion occurs when a lower-gas-price transaction appears before a
higher-gas-price transaction, indicating non-priority ordering (potential MEV).
Palette matches the rest of the project: ch:rot=-.25,hue=1,light=.75
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

DATA_PATH = PROJECT_ROOT / "data" / "empirical" / "ordering_inversions.csv"
OUT_PATH  = PROJECT_ROOT / "figures" / "empirical" / "inversion_ecdf.pdf"

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


def ecdf(data):
    x = np.sort(data)
    y = np.arange(1, len(x) + 1) / len(x)
    return x, y


def main():
    if not DATA_PATH.exists():
        print(f"Missing {DATA_PATH}. Run scripts/run_empirical_analysis.py first.")
        return

    df = pd.read_csv(DATA_PATH)
    # Only blocks with enough transactions for meaningful inversion counts
    df = df[df["num_transactions"] >= 5]

    palette = sns.color_palette("ch:rot=-.25,hue=1,light=.75", len(PERIODS) + 1)
    period_color = {p: palette[i + 1] for i, p in enumerate(PERIODS)}

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    for period in PERIODS:
        sub = df[df["period"] == period]["inversion_rate"].dropna().to_numpy()
        if len(sub) == 0:
            continue
        x, y = ecdf(sub)
        ax.plot(
            x, y,
            color=period_color[period],
            linestyle=PERIOD_LINESTYLE[period],
            linewidth=2.5,
            label=PERIOD_LABELS[period],
        )

    ax.set_xlabel("Inversion Rate (per block)", fontsize=30)
    ax.set_ylabel("Cumulative Fraction", fontsize=30)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.tick_params(axis="both", labelsize=28)
    ax.legend(fontsize=22, frameon=True)

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()

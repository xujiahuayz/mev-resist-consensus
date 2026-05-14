"""
Mean gas fee per block over the block sequence for each market period.

Reads:   data/empirical/gas_fee_per_block.csv
Writes:  figures/empirical/gas_timeseries.pdf

X-axis is the block's position within its period (0-indexed), not the raw
block number, so all periods are comparable on the same scale. A rolling
window smooths short-term noise.
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

DATA_PATH = PROJECT_ROOT / "data" / "empirical" / "gas_fee_per_block.csv"
OUT_PATH  = PROJECT_ROOT / "figures" / "empirical" / "gas_timeseries.pdf"

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

ROLLING_WINDOW = 10


def main():
    if not DATA_PATH.exists():
        print(f"Missing {DATA_PATH}. Run scripts/run_empirical_analysis.py first.")
        return

    df = pd.read_csv(DATA_PATH)

    palette = sns.color_palette("ch:rot=-.25,hue=1,light=.75", len(PERIODS) + 1)
    period_color = {p: palette[i + 1] for i, p in enumerate(PERIODS)}

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    for period in PERIODS:
        sub = df[df["period"] == period].copy()
        if sub.empty:
            continue
        sub = sub.sort_values("block_number").reset_index(drop=True)
        sub["position"] = range(len(sub))

        fees = sub["mean_gas_fee_gwei"].to_numpy(dtype=float)
        # Rolling mean to smooth noise
        smoothed = pd.Series(fees).rolling(ROLLING_WINDOW, min_periods=1, center=True).mean().to_numpy()

        ax.plot(
            sub["position"],
            smoothed,
            color=period_color[period],
            linestyle=PERIOD_LINESTYLE[period],
            linewidth=2.5,
            label=PERIOD_LABELS[period],
        )

    ax.set_xlabel("Block Sequence Position", fontsize=30)
    ax.set_ylabel("Mean Gas Fee per Block (Gwei)", fontsize=30)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.tick_params(axis="both", labelsize=28)
    ax.yaxis.get_offset_text().set_fontsize(28)
    ax.legend(fontsize=22, frameon=True)

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()

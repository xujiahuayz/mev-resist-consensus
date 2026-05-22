"""
Per-period CDF of transaction gas fees.

These distributions are sampled directly in the simulator (see
blockchain_env/user.py and blockchain_env/data_loader.py) — this figure
documents the *calibration inputs* drawn from on-chain data per period.
It is NOT a model-vs-reality comparison: overlaying the simulator here
would be tautological (sampling from F vs. F).

Reads:   data/empirical/all_gas_fees.csv
Writes:  figures/empirical/gas_fee_cdf.pdf

Palette: ch:rot=-.25,hue=1,light=.75
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

DATA_PATH = PROJECT_ROOT / "data" / "empirical" / "all_gas_fees.csv"
OUT_PATH  = PROJECT_ROOT / "figures" / "empirical" / "gas_fee_cdf.pdf"

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

# Solid for stable, dashed for crisis — visually separates regime categories.
PERIOD_LINESTYLE = {
    "STABLE_PRE_MERGE_2022":  "-",
    "STABLE_POST_MERGE_2022": "-",
    "STABLE_POST_MERGE_2023": "-",
    "FTX_COLLAPSE_NOV_2022":  "--",
    "LUNA_CRASH_MAY_2022":    "--",
    "USDC_DEPEG_MARCH_2023":  "--",
}


def cdf(data):
    x = np.sort(data)
    y = np.arange(1, len(x) + 1) / len(x)
    return x, y


def main():
    if not DATA_PATH.exists():
        print(f"Missing {DATA_PATH}. Run scripts/run_empirical_analysis.py first.")
        return

    emp_df = pd.read_csv(DATA_PATH)
    emp_df = emp_df[emp_df["gas_fee_gwei"] > 0]

    palette = sns.color_palette("ch:rot=-.25,hue=1,light=.75", len(PERIODS) + 1)
    period_color = {p: palette[i + 1] for i, p in enumerate(PERIODS)}

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    for period in PERIODS:
        sub = emp_df[emp_df["period"] == period]["gas_fee_gwei"].dropna().to_numpy()
        if len(sub) == 0:
            continue
        x, y = cdf(sub)
        ax.plot(
            x, y,
            color=period_color[period],
            linestyle=PERIOD_LINESTYLE[period],
            linewidth=2.5,
            label=PERIOD_LABELS[period],
        )

    ax.set_xscale("log")
    ax.set_xlabel("Transaction gas fee (Gwei, log scale)", fontsize=22)
    ax.set_ylabel("Cumulative fraction", fontsize=22)
    ax.set_xlim(left=emp_df["gas_fee_gwei"].quantile(0.001))
    ax.set_ylim(0, 1)
    ax.tick_params(axis="both", labelsize=18)
    ax.legend(fontsize=14, frameon=True, title="Period sampling distribution")

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()

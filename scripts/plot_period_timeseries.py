"""
Plot gas and MEV per block over simulated block time, by period (PoS).

Uses only CSV outputs from:
    data/same_seed/by_period/<PERIOD>/pos/pos_block_data_validators20_users50.csv

Run:
    python scripts/plot_period_timeseries.py
"""

import csv
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

# Month words to strip from period labels in legend
MONTH_PATTERN = re.compile(
    r"\b(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC|MARCH|APRIL|JUNE|JULY|AUGUST|SEPT|OCTOBER|SEPTEMBER)\b",
    re.IGNORECASE,
)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

BY_PERIOD = PROJECT_ROOT / "data" / "same_seed" / "by_period"
OUT_DIR = PROJECT_ROOT / "figures" / "periods"
CONFIG = "validators20_users50"


def load_pos_blocks():
    """Return dict[period_label] -> (block_nums, gas_list, mev_list)."""
    results = {}
    if not BY_PERIOD.exists():
        return results

    for period_dir in sorted(BY_PERIOD.iterdir()):
        if not period_dir.is_dir():
            continue
        period_name = period_dir.name
        label = period_name.replace("_", " ")
        label = MONTH_PATTERN.sub("", label).strip()
        csv_path = period_dir / "pos" / f"pos_block_data_{CONFIG}.csv"
        if not csv_path.exists():
            continue

        block_nums = []
        gas_list = []
        mev_list = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    bnum = int(row.get("block_num", 0))
                    gas = float(row.get("total_gas_fee", 0))
                    mev = float(row.get("total_mev_available", 0))
                except (ValueError, TypeError):
                    continue
                block_nums.append(bnum)
                gas_list.append(gas)
                mev_list.append(mev)

        if block_nums:
            results[label] = (block_nums, gas_list, mev_list)

    return results


def plot_timeseries(period_blocks):
    """Create time-series plots of gas and MEV per block over simulated time."""
    if not period_blocks:
        print("No by_period PoS block data found for timeseries plotting.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", font_scale=1.0)
    palette = sns.color_palette("husl", n_colors=len(period_blocks))
    big_font = {"fontsize": 22}
    label_font = {"fontsize": 20}
    tick_font = 16

    # 1) Gas per block over time
    fig, ax = plt.subplots(figsize=(10, 5))
    for (period, (bnums, gas, _)), color in zip(period_blocks.items(), palette):
        ax.plot(bnums, gas, label=period, color=color, alpha=0.9, linewidth=1.2)
    ax.set_xlabel("Block number", **label_font)
    ax.set_ylabel("Gas fee per block", **label_font)
    ax.legend(fontsize=tick_font, loc="upper right")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.tick_params(axis="both", labelsize=tick_font)
    plt.tight_layout()
    gas_path = OUT_DIR / "period_timeseries_pos_gas.pdf"
    plt.savefig(gas_path, bbox_inches="tight")
    plt.close()
    print(f"Saved {gas_path}")

    # 2) MEV per block over time
    fig, ax = plt.subplots(figsize=(10, 5))
    for (period, (bnums, _, mev)), color in zip(period_blocks.items(), palette):
        ax.plot(bnums, mev, label=period, color=color, alpha=0.9, linewidth=1.2)
    ax.set_xlabel("Block number", **label_font)
    ax.set_ylabel("MEV per block", **label_font)
    ax.legend(fontsize=tick_font, loc="upper right")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.tick_params(axis="both", labelsize=tick_font)
    plt.tight_layout()
    mev_path = OUT_DIR / "period_timeseries_pos_mev.pdf"
    plt.savefig(mev_path, bbox_inches="tight")
    plt.close()
    print(f"Saved {mev_path}")


def main():
    period_blocks = load_pos_blocks()
    plot_timeseries(period_blocks)


if __name__ == "__main__":
    main()


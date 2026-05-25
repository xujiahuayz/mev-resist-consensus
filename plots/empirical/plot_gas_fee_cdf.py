"""
CDF of transaction gas fees by market period.

Reads:   data/empirical/all_gas_fees.csv
         data/empirical/sim_baseline_gas_fees.csv  (optional, from compute_simulation_baseline.py)
Writes:  figures/empirical/gas_fee_cdf.pdf

Solid lines: real Ethereum data. Dotted lines (same color): PoS simulation (50% MEV),
drawn only for periods where simulation median is within 3× of real data median —
miscalibrated periods (fallback gas fees) are silently omitted.
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

from plots.empirical._style import PERIODS, PERIOD_LABELS, PERIOD_LINESTYLE, period_palette

DATA_PATH     = PROJECT_ROOT / "data" / "empirical" / "gas_fee_per_block.csv"
SIM_DATA_PATH = PROJECT_ROOT / "data" / "empirical" / "sim_baseline_gas_fees.csv"
OUT_PATH      = PROJECT_ROOT / "figures" / "empirical" / "gas_fee_cdf.pdf"
VALUE_COL     = "mean_gas_fee_gwei"


def cdf(data):
    x = np.sort(data)
    y = np.arange(1, len(x) + 1) / len(x)
    return x, y


def main():
    if not DATA_PATH.exists():
        print(f"Missing {DATA_PATH}. Run scripts/run_empirical_analysis.py first.")
        return

    emp_df = pd.read_csv(DATA_PATH)
    emp_df = emp_df[emp_df[VALUE_COL] > 0]

    sim_df = pd.read_csv(SIM_DATA_PATH) if SIM_DATA_PATH.exists() else None
    if sim_df is not None:
        sim_df = sim_df[sim_df["gas_fee_gwei"] > 0]

    period_color = period_palette()

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    for period in PERIODS:
        sub = emp_df[emp_df["period"] == period][VALUE_COL].dropna().to_numpy()
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

        # Overlay simulation baseline only when calibration is confirmed good:
        # skip if simulation median is more than 3× off from real data median.
        if sim_df is not None:
            sim_sub = sim_df[sim_df["period"] == period]["gas_fee_gwei"].dropna().to_numpy()
            if len(sim_sub) > 0:
                real_med = np.median(sub)
                sim_med  = np.median(sim_sub)
                ratio = max(real_med, sim_med) / max(min(real_med, sim_med), 1e-9)
                if ratio <= 3.0:
                    sx, sy = cdf(sim_sub)
                    ax.plot(
                        sx, sy,
                        color=period_color[period],
                        linestyle=":",
                        linewidth=2.0,
                        alpha=0.75,
                    )
                else:
                    print(f"  SKIP sim overlay for {period}: "
                          f"real median={real_med:.0f}, sim median={sim_med:.0f} (ratio={ratio:.1f}×)")

    # Set left xlim from global min so all curves start at y≈0
    all_values = [emp_df[VALUE_COL].dropna().to_numpy()]
    if sim_df is not None:
        all_values.append(sim_df["gas_fee_gwei"].dropna().to_numpy())
    global_min = min(v.min() for v in all_values if len(v) > 0)

    ax.set_xscale("log")
    ax.minorticks_off()
    ax.grid(which="minor", visible=False)
    ax.set_xlabel("Gas Fee (Gwei)", fontsize=30)
    ax.set_ylabel("Cumulative Fraction", fontsize=30)
    ax.set_xlim(left=global_min * 0.9)
    ax.set_ylim(0, 1)
    ax.tick_params(axis="both", labelsize=28)

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()

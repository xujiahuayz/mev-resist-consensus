"""
Real-Ethereum vs simulated CDF of per-block transaction ordering inversion rates.

Solid lines: real Ethereum (data/empirical/ordering_inversions.csv).
Dashed lines (same color): PoS simulator at primary MEV fraction
                           (data/same_seed/by_period/<P>/pos/pos_block_inversions_*.csv).

Each data point is one block's inversion_rate = inversion_count / max_possible.
An inversion is a lower-priority tx (lower gas fee / gas price) appearing
before a higher-priority tx in the block. Blocks with fewer than 50
transactions are excluded on both sides — small blocks have a degenerate
inversion-rate distribution and would dominate the lower tail.

Writes:
    figures/empirical/inversion_cdf.pdf
    data/empirical/inversion_gof.csv    (per-period KS + Wasserstein-1)

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

from blockchain_env.sim_config import VALIDATORS, USERS, MEV_FRACTION_PRIMARY
from blockchain_env.gof_metrics import per_period_gof_table
from plots.empirical._style import (
    PERIODS, PERIOD_LABELS, PERIOD_LINESTYLE, SIM_LINESTYLE, period_palette,
)

EMP_PATH  = PROJECT_ROOT / "data" / "empirical" / "ordering_inversions.csv"
SIM_BASE  = PROJECT_ROOT / "data" / "same_seed" / "by_period"
OUT_FIG   = PROJECT_ROOT / "figures" / "empirical" / "inversion_cdf.pdf"
OUT_GOF   = PROJECT_ROOT / "data" / "empirical" / "inversion_gof.csv"

MIN_TX_PER_BLOCK = 50

# Primary-config sim filename suffix (V/U attacker counts at 50% MEV of the canonical scale)
_PRIMARY_V = int(round(VALIDATORS * MEV_FRACTION_PRIMARY))
_PRIMARY_U = int(round(USERS * MEV_FRACTION_PRIMARY))
SIM_FILE_NAME = f"pos_block_inversions_validators{_PRIMARY_V}_users{_PRIMARY_U}.csv"


def cdf(data):
    x = np.sort(data)
    y = np.arange(1, len(x) + 1) / len(x)
    return x, y


def _load_sim_inversions() -> pd.DataFrame:
    """Load per-period simulator inversion CSVs into a single DataFrame with 'period' column."""
    frames = []
    for period in PERIODS:
        path = SIM_BASE / period / "pos" / SIM_FILE_NAME
        if not path.exists():
            print(f"  SKIP sim overlay for {period}: {path.name} missing")
            continue
        sub = pd.read_csv(path)
        sub.insert(0, "period", period)
        frames.append(sub)
    if not frames:
        return pd.DataFrame(columns=["period", "num_transactions", "inversion_rate"])
    return pd.concat(frames, ignore_index=True)


def main():
    if not EMP_PATH.exists():
        print(f"Missing {EMP_PATH}. Run scripts/run_empirical_analysis.py first.")
        return

    emp_df = pd.read_csv(EMP_PATH)
    emp_df = emp_df[emp_df["num_transactions"] >= MIN_TX_PER_BLOCK]

    sim_df = _load_sim_inversions()
    sim_df = sim_df[sim_df["num_transactions"] >= MIN_TX_PER_BLOCK] if not sim_df.empty else sim_df

    period_color = period_palette()

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    for period in PERIODS:
        emp_sub = emp_df.loc[emp_df["period"] == period, "inversion_rate"].dropna().to_numpy()
        if emp_sub.size:
            x, y = cdf(emp_sub)
            ax.plot(x, y, color=period_color[period], linestyle=PERIOD_LINESTYLE[period],
                    linewidth=2.5)

        sim_sub = (sim_df.loc[sim_df["period"] == period, "inversion_rate"].dropna().to_numpy()
                   if not sim_df.empty else np.array([]))
        if sim_sub.size:
            x, y = cdf(sim_sub)
            ax.plot(x, y, color=period_color[period], linestyle=SIM_LINESTYLE,
                    linewidth=2.0, alpha=0.85)

    ax.set_xlabel("Inversion rate per block", fontsize=30)
    ax.set_ylabel("Cumulative fraction", fontsize=30)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.tick_params(axis="both", labelsize=28)

    plt.tight_layout()
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_FIG, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Saved {OUT_FIG}")

    # Goodness-of-fit table — only meaningful where both sides have data.
    if not sim_df.empty:
        gof = per_period_gof_table(emp_df, sim_df, value_col="inversion_rate")
        OUT_GOF.parent.mkdir(parents=True, exist_ok=True)
        gof.to_csv(OUT_GOF, index=False)
        print(f"Saved {OUT_GOF}")
        print(gof.to_string(index=False))


if __name__ == "__main__":
    main()

"""
Builder concentration: PoS vs ePBS Lorenz curves + standalone Gini table.

Reads:   data/same_seed/pos_visible80/pos_block_data_validators{n}_users*.csv
           (actual PoS simulation, 50 validators, sweeping MEV attacker fraction,
            aggregated over all user-attack configurations)
         data/builder_auction/builder_auction_blocks.csv
         data/builder_auction/builder_auction_summary.csv
           (ePBS auction simulation with log-normal capability heterogeneity,
            sigma=1.5, 50 builders, all MEV fractions 0-100%, 1000 blocks each)
Writes:  figures/ss/builder_auction_lorenz.pdf
         figures/ss/builder_auction_table.pdf

PoS: uniform random validator selection — all 5 MEV fractions produce near-identical
Lorenz curves (Gini ≈ 0.01), shown in 5 red shades.
ePBS: auction with capability heterogeneity — Gini rises from 0.71 to 0.87 with
MEV fraction, shown in 5 teal/blue shades. Table row colors match plot line colors.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

POS_DATA_DIR = PROJECT_ROOT / "data" / "same_seed" / "pos_visible80"
BLOCKS_PATH  = PROJECT_ROOT / "data" / "builder_auction" / "builder_auction_blocks.csv"
SUMMARY_PATH = PROJECT_ROOT / "data" / "builder_auction" / "builder_auction_summary.csv"
OUT_DIR      = PROJECT_ROOT / "figures" / "ss"

N_VALIDATORS = 50
N_BUILDERS   = 50

LORENZ_N_ATTACKS = [0, 5, 10, 25, 50]   # → 0%, 10%, 20%, 50%, 100% MEV
MEV_LABELS       = ["0%", "10%", "20%", "50%", "100%"]

EPBS_PALETTE = sns.color_palette("ch:rot=-.25,hue=1,light=.75", len(LORENZ_N_ATTACKS) + 1)[1:]
POS_PALETTE  = sns.color_palette("flare", len(LORENZ_N_ATTACKS) + 2)[1:-1]

LABEL_FS = 40
TICK_FS  = 34


def gini(counts: np.ndarray) -> float:
    v = np.sort(counts.astype(float))
    n = len(v)
    if n == 0 or v.sum() == 0:
        return 0.0
    return (2 * np.sum(np.arange(1, n + 1) * v) - (n + 1) * v.sum()) / (n * v.sum())


def lorenz_curve(counts: np.ndarray):
    v = np.sort(counts.astype(float))
    n = len(v)
    total = v.sum()
    if total == 0:
        return np.linspace(0, 1, n + 1), np.zeros(n + 1)
    return np.linspace(0, 1, n + 1), np.concatenate([[0.0], np.cumsum(v) / total])


def load_pos_wins(n_attack: int) -> np.ndarray:
    """Load actual PoS simulation wins for given n_attack validators, aggregated over all user counts."""
    dfs = list(POS_DATA_DIR.glob(f"pos_block_data_validators{n_attack}_users*.csv"))
    if not dfs:
        raise FileNotFoundError(f"No PoS data for n_attack={n_attack} in {POS_DATA_DIR}")
    combined = pd.concat([pd.read_csv(f) for f in dfs])
    wins = combined.groupby("validator_id").size()
    # Ensure all 50 validators are represented (fill zeros for any missing)
    full = np.zeros(N_VALIDATORS, dtype=int)
    for i, vid in enumerate(sorted(wins.index)):
        idx = int(vid.split("_")[1])
        full[idx] = wins[vid]
    return full


def plot_lorenz(blocks_df: pd.DataFrame, summary_df: pd.DataFrame):
    sns.set_theme(style="whitegrid")

    fig, ax = plt.subplots(figsize=(10, 9))

    # PoS: actual simulation data — one curve per MEV attacker fraction
    # All near-identical (Gini ≈ 0.01) because validator selection is uniform random
    pos_ginis = []
    pos_last_x, pos_last_y = None, None
    for n_attack, color in zip(LORENZ_N_ATTACKS, POS_PALETTE):
        wins = load_pos_wins(n_attack)
        pos_ginis.append(gini(wins))
        x, y = lorenz_curve(wins)
        ax.plot(x, y, color=color, linewidth=3.0, alpha=0.75)
        pos_last_x, pos_last_y = x, y

    pos_gini_val = float(np.mean(pos_ginis))

    # ePBS: auction simulation with capability heterogeneity — one curve per MEV fraction
    epbs_last_x, epbs_last_y = None, None
    for n_attack, color in zip(LORENZ_N_ATTACKS, EPBS_PALETTE):
        sub = blocks_df[blocks_df["n_attack"] == n_attack]
        win_counts = np.zeros(N_BUILDERS, dtype=int)
        for idx in sub["winner_idx"].values:
            win_counts[int(idx)] += 1
        x, y = lorenz_curve(win_counts)
        ax.plot(x, y, color=color, linewidth=3.0)
        epbs_last_x, epbs_last_y = x, y

    ax.plot([0, 1], [0, 1], color="grey", linewidth=1.5, linestyle="--", zorder=2)

    ax.set_xlabel("Cumulative share of builders", fontsize=LABEL_FS)
    ax.set_ylabel("Cumulative block share", fontsize=LABEL_FS)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.tick_params(axis="both", labelsize=TICK_FS)

    plt.tight_layout()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "builder_auction_lorenz.pdf"
    plt.savefig(out, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Saved {out}")

    return pos_ginis


def _lighten(c, alpha=0.25):
    r, g, b = matplotlib.colors.to_rgb(c)
    return (1 - alpha + alpha * r, 1 - alpha + alpha * g, 1 - alpha + alpha * b)


def plot_table(summary_df: pd.DataFrame, pos_ginis: list):
    sns.set_theme(style="white")

    epbs_ginis = [
        summary_df.loc[summary_df["n_attack"] == na, "builder_gini"].iloc[0]
        for na in LORENZ_N_ATTACKS
    ]

    n_rows = len(LORENZ_N_ATTACKS)

    # 5 columns: MEV attacker | [pos swatch] | PoS | [epbs swatch] | ePBS
    # Use newline to avoid header overflow in the narrow first column.
    col_labels = ["MEV\nattacker", "", "PoS", "", "ePBS"]
    cell_text = [
        [lbl, "", f"Gini = {pg:.3f}", "", f"Gini = {eg:.3f}"]
        for lbl, pg, eg in zip(MEV_LABELS, pos_ginis, epbs_ginis)
    ]

    fig, ax = plt.subplots(figsize=(8, 0.62 * (n_rows + 1.4)))
    ax.axis("off")

    tbl = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        loc="center",
        cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(20)
    tbl.scale(1, 1.9)

    # Give the header row extra height for the wrapped "MEV\nattacker" label.
    for col in range(5):
        cell = tbl[(0, col)]
        cell.set_height(cell.get_height() * 1.75)

    # Column widths: narrow swatches (cols 1, 3), wider data (cols 0, 2, 4)
    SWATCH_W = 0.045
    LABEL_W  = 0.22   # wide enough for "MEV\\nattacker"
    DATA_W   = 0.27
    for row in range(n_rows + 1):
        tbl[(row, 0)].set_width(LABEL_W)
        tbl[(row, 1)].set_width(SWATCH_W)
        tbl[(row, 2)].set_width(DATA_W)
        tbl[(row, 3)].set_width(SWATCH_W)
        tbl[(row, 4)].set_width(DATA_W)

    HEADER_BG = "#e8e8e8"
    ROW_BG    = "white"
    ALT_BG    = "#f5f5f5"

    # Header row: neutral grey, bold text, swatch cells match header bg
    for col in range(5):
        cell = tbl[(0, col)]
        cell.set_edgecolor("white")
        cell.set_facecolor(HEADER_BG)
        if col in (0, 2, 4):
            cell.set_text_props(weight="bold", fontsize=21)
        # Ensure multi-line header text is centered within the taller header row.
        cell.get_text().set_verticalalignment("center")

    # Data rows: swatch columns get full palette color; all other cells neutral
    for row_i, (pos_c, epbs_c) in enumerate(zip(POS_PALETTE, EPBS_PALETTE), start=1):
        bg = ROW_BG if row_i % 2 == 1 else ALT_BG

        tbl[(row_i, 0)].set_facecolor(bg)
        tbl[(row_i, 0)].set_edgecolor("white")

        tbl[(row_i, 1)].set_facecolor(pos_c)    # exact line color swatch
        tbl[(row_i, 1)].set_edgecolor("white")

        tbl[(row_i, 2)].set_facecolor(bg)
        tbl[(row_i, 2)].set_edgecolor("white")

        tbl[(row_i, 3)].set_facecolor(epbs_c)   # exact line color swatch
        tbl[(row_i, 3)].set_edgecolor("white")

        tbl[(row_i, 4)].set_facecolor(bg)
        tbl[(row_i, 4)].set_edgecolor("white")

    plt.tight_layout()
    out = OUT_DIR / "builder_auction_table.pdf"
    plt.savefig(out, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Saved {out}")


def main():
    if not BLOCKS_PATH.exists():
        print(f"Missing {BLOCKS_PATH}. Run scripts/run_builder_auction.py first.")
        return
    if not POS_DATA_DIR.exists():
        print(f"Missing {POS_DATA_DIR}. Run scripts/simulate_pos.py first.")
        return
    blocks_df  = pd.read_csv(BLOCKS_PATH)
    summary_df = pd.read_csv(SUMMARY_PATH)
    pos_ginis = plot_lorenz(blocks_df, summary_df)
    plot_table(summary_df, pos_ginis)


if __name__ == "__main__":
    main()

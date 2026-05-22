"""Shared style constants for the empirical-section plots.

Single source of truth for period order, labels, per-period linestyle,
palette, and the simulation-overlay style. Imported by every script in
plots/empirical/ so colors and linestyles in the shared legend
(figures/empirical/legend.pdf) can never drift out of sync with the
panels.
"""

import seaborn as sns

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

PALETTE_NAME = "ch:rot=-.25,hue=1,light=.75"

# Simulation-overlay style: one entry in the shared legend covers all four panels.
SIM_LINESTYLE = ":"
SIM_COLOR = "dimgrey"
SIM_LABEL = "Simulation (50% MEV)"


def period_palette():
    """Return {period_name: color} using PALETTE_NAME with n+1 entries (first reserved)."""
    palette = sns.color_palette(PALETTE_NAME, len(PERIODS) + 1)
    return {p: palette[i + 1] for i, p in enumerate(PERIODS)}

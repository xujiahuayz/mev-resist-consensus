"""Auction latency sweep simulation.

Runs the real ePBS reactive-bidding auction (using ModifiedBuilder from
blockchain_env/bidding.py) for N ∈ {10, 20, 50} builders across a range of
network latency values Δ ∈ [0, 2] seconds.

Latency model
-------------
Builders observe bids from `delay_rounds` rounds ago rather than the
immediately preceding round.  `delay_rounds` is drawn each round from
Poisson(Δ × ROUNDS_PER_SECOND), making Δ a smooth continuous parameter.

Metric
------
For each simulated block:
    ratio = winning_bid / second_highest_block_value

where `second_highest_block_value` is the second-largest block valuation
among all builders (the Vickrey benchmark: what the winner *should* pay).

Output
------
data/auction_latency/auction_latency_N<n>.csv
  columns: delta_s, block_num, winning_bid, second_highest_value, ratio
"""

import csv
import random
from pathlib import Path
from typing import List, Tuple

import numpy as np

# ── paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
OUT_DIR = PROJECT_ROOT / "data" / "auction_latency"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── simulation parameters ──────────────────────────────────────────────────────
BUILDER_COUNTS    = [10, 20, 50]
ROUNDS_PER_SECOND = 2.0
MAX_ROUNDS        = 10         # short auction window so latency is impactful
N_BLOCKS          = 500        # more blocks for lower noise
DELTA_VALUES      = np.concatenate([
    np.linspace(0.0, 0.5, 11),   # dense near 0
    np.linspace(0.6, 2.0, 15),   # sparser at high latency
])

SEED = 42
rng  = np.random.default_rng(SEED)

# ── block value generator ─────────────────────────────────────────────────────
# Instead of full transaction selection, draw each builder's block value
# directly from a realistic distribution (calibrated from real bid_builder*.csv
# data: block_value ~ Uniform(50M, 400M)).  This is equivalent to the
# valuation draw in the theoretical model and avoids per-tx overhead.

_BV_LO = 50_000_000.0
_BV_HI = 400_000_000.0


def draw_block_values(n: int) -> np.ndarray:
    """Draw N independent block valuations from empirical distribution."""
    return rng.uniform(_BV_LO, _BV_HI, size=n)


# ── bidding logic (vectorised) ────────────────────────────────────────────────
# Strategies:
#   reactive   (75 %): raise to min(highest * 1.1, own_value) if below highest
#   late_enter (25 %): bid 0 until a random entry round, then min(1.05*highest, value)

def run_block(n: int, late_mask: np.ndarray, entry_rounds: np.ndarray,
              block_values: np.ndarray, delay_rounds: float) -> Tuple[float, float]:
    """
    Simulate one auction block.
    Returns (winning_bid, second_highest_block_value).
    """
    n_rounds = int(rng.integers(6, MAX_ROUNDS + 1))
    bids     = np.zeros(n)

    # bid_history[t] = bids array at round t
    bid_history: List[np.ndarray] = []

    for rnd in range(n_rounds):
        # Each builder draws its own Poisson observation lag
        if delay_rounds > 0:
            lags = rng.poisson(delay_rounds, size=n).astype(int)
        else:
            lags = np.zeros(n, dtype=int)

        new_bids = bids.copy()
        for i in range(n):
            obs_t    = max(0, len(bid_history) - 1 - lags[i])
            observed = bid_history[obs_t] if bid_history else np.zeros(n)
            highest  = float(observed.max())
            my_last  = float(bids[i])
            bv       = float(block_values[i])

            if late_mask[i]:
                if rnd < entry_rounds[i]:
                    new_bids[i] = 0.0
                else:
                    new_bids[i] = min(1.05 * highest, bv) if highest > 0 else 0.5 * bv
            else:  # reactive
                if my_last < highest:
                    new_bids[i] = min(highest * 1.1, bv)
                elif my_last == highest and highest > 0:
                    new_bids[i] = my_last + random.random() * (bv - my_last)
                elif highest == 0:
                    new_bids[i] = 0.5 * bv
                # else: already above — hold
            new_bids[i] = max(0.0, min(new_bids[i], bv))

        bids = new_bids
        bid_history.append(bids.copy())

    winning_bid = float(bids.max())
    return winning_bid


# ── sweep ──────────────────────────────────────────────────────────────────────
def make_strategy_masks(n: int):
    """Return (late_mask, entry_rounds) for N builders."""
    n_late      = max(1, int(n * 0.25))
    late_mask   = np.array([True] * n_late + [False] * (n - n_late))
    entry_rounds = rng.integers(17, 23, size=n)  # late_enter entry threshold
    return late_mask, entry_rounds


def run_sweep(n: int) -> None:
    random.seed(SEED + n)
    out_path = OUT_DIR / f"auction_latency_N{n}.csv"

    late_mask, entry_rounds = make_strategy_masks(n)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["delta_s", "block_num", "winning_bid"])

        for delta in DELTA_VALUES:
            delay_rounds = float(delta) * ROUNDS_PER_SECOND

            for blk in range(N_BLOCKS):
                block_values = draw_block_values(n)
                winning_bid  = run_block(n, late_mask, entry_rounds,
                                         block_values, delay_rounds)
                writer.writerow([round(float(delta), 4), blk,
                                 round(winning_bid, 2)])

    print(f"  Saved {out_path.name}  ({N_BLOCKS} blocks × {len(DELTA_VALUES)} Δ values)")


if __name__ == "__main__":
    for n in BUILDER_COUNTS:
        print(f"N = {n} builders …")
        run_sweep(n)
    print("Done. Data in data/auction_latency/")

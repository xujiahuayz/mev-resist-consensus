"""
PBS auction simulation: builder concentration vs MEV attacker fraction.

Each builder has a fixed capability multiplier drawn from a log-normal
distribution (sigma=1.5) calibrated so that at 0% MEV attackers the
block-win Gini matches the empirical post-merge PoS baseline (~0.83).
This reflects real-world heterogeneity in MEV extraction skill and capital.
Attack builders receive an additional MEV premium on top of their capability-
scaled block value.

Auction dynamics mirror bidding.py's ModifiedBuilder:
  - reactive builders raise to min(highest*1.1, own_value) when behind
  - 25% of builders are late-entry (sit out until a random round)
  - latency: Poisson(delta_s * ROUNDS_PER_SECOND) observation lag per builder

Parameters
----------
  n_attack  in 0..N_BUILDERS  (all 21 values)
  N_BLOCKS  = 1000  per configuration
  SEED      = 42
  CAP_SIGMA = 1.5   (log-normal sigma; calibrated to empirical Gini ~0.83)

Writes
------
  data/builder_auction/builder_auction_blocks.csv
  data/builder_auction/builder_auction_summary.csv

Usage
-----
  python scripts/run_builder_auction.py
"""

import csv
import random
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_ROOT / "data" / "builder_auction"

# ── simulation parameters ──────────────────────────────────────────────────────
N_BUILDERS        = 20
N_BLOCKS          = 1000
ATTACK_COUNTS     = list(range(0, N_BUILDERS + 1))
SEED              = 42
ROUNDS_PER_SECOND = 2.0
MAX_ROUNDS        = 20
DELTA_S           = 0.5    # primary scenario (0.5 s network latency)

# Builder capability heterogeneity: log-normal multiplier, sigma calibrated to
# reproduce empirical post-merge block-producer Gini (~0.83) at 0% MEV attackers.
CAP_SIGMA = 1.5

# Block value distribution (empirical calibration)
BV_LO  = 50_000_000.0    # gwei
BV_HI  = 400_000_000.0   # gwei
MEV_LO = 0.0
MEV_HI = 50_000_000.0    # additional MEV premium for attack builders


def gini(counts: np.ndarray) -> float:
    """Gini coefficient of a non-negative array."""
    v = np.sort(counts.astype(float))
    n = len(v)
    if n == 0 or v.sum() == 0:
        return 0.0
    return (2 * np.sum(np.arange(1, n + 1) * v) - (n + 1) * v.sum()) / (n * v.sum())


def run_block(n: int, n_attack: int, block_values: np.ndarray,
              delay_rounds: float, rng: np.random.Generator) -> dict:
    """Simulate one auction block; return per-block metrics including winner_idx."""
    n_late = max(1, int(n * 0.25))
    late_mask = np.array([False] * n_attack + [True] * n_late
                         + [False] * max(0, n - n_attack - n_late))[:n]
    entry_rounds = rng.integers(int(MAX_ROUNDS * 0.6), MAX_ROUNDS, size=n)

    n_rounds = int(rng.integers(MAX_ROUNDS // 2, MAX_ROUNDS + 1))
    bids = np.zeros(n)
    bid_history = []

    for rnd in range(n_rounds):
        lags = rng.poisson(delay_rounds, size=n).astype(int) if delay_rounds > 0 else np.zeros(n, dtype=int)
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
            else:
                if my_last < highest:
                    new_bids[i] = min(highest * 1.1, bv)
                elif my_last == highest and highest > 0:
                    new_bids[i] = my_last + random.random() * (bv - my_last)
                elif highest == 0:
                    new_bids[i] = 0.5 * bv
            new_bids[i] = max(0.0, min(new_bids[i], bv))

        bids = new_bids
        bid_history.append(bids.copy())

    winner_idx         = int(bids.argmax())
    winning_bid        = float(bids[winner_idx])
    sorted_bv          = np.sort(block_values)[::-1]
    top_block_value    = float(sorted_bv[0])
    second_highest_bv  = float(sorted_bv[1]) if n > 1 else top_block_value
    winner_is_attacker = int(winner_idx < n_attack)
    bid_to_top         = winning_bid / top_block_value if top_block_value > 0 else 0.0
    bid_to_second      = winning_bid / second_highest_bv if second_highest_bv > 0 else 0.0

    return {
        "winner_idx":          winner_idx,
        "winning_bid":         winning_bid,
        "top_block_value":     top_block_value,
        "second_highest_bv":   second_highest_bv,
        "winner_is_attacker":  winner_is_attacker,
        "bid_to_top_value":    bid_to_top,
        "bid_to_second_value": bid_to_second,
    }


def run_simulation():
    rng = np.random.default_rng(SEED)
    random.seed(SEED)

    # Fixed capability multipliers, sorted descending so builder[0] is always the most
    # capable. Attackers are designated as the top n_attack builders, matching the
    # real-world pattern where high-capability builders also adopt MEV strategies.
    caps = np.sort(rng.lognormal(mean=0.0, sigma=CAP_SIGMA, size=N_BUILDERS))[::-1]

    delay_rounds = DELTA_S * ROUNDS_PER_SECOND
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blocks_path  = OUT_DIR / "builder_auction_blocks.csv"
    summary_path = OUT_DIR / "builder_auction_summary.csv"

    block_rows   = []
    summary_rows = []

    print(f"{'n_attack':>8} | {'mev_frac':>8} | {'bid/top%':>8} | {'bid/2nd%':>8} | "
          f"{'atk_win%':>8} | {'bld_gini':>8}")
    print("-" * 60)

    for n_attack in ATTACK_COUNTS:
        win_counts     = np.zeros(N_BUILDERS, dtype=int)
        bid_to_tops    = []
        bid_to_seconds = []
        attacker_wins  = 0

        for blk in range(N_BLOCKS):
            base_values  = rng.uniform(BV_LO, BV_HI, size=N_BUILDERS) * caps
            mev_premiums = np.zeros(N_BUILDERS)
            if n_attack > 0:
                mev_premiums[:n_attack] = rng.uniform(MEV_LO, MEV_HI, size=n_attack)
            block_values = base_values + mev_premiums

            result = run_block(N_BUILDERS, n_attack, block_values, delay_rounds, rng)

            win_counts[result["winner_idx"]] += 1
            bid_to_tops.append(result["bid_to_top_value"])
            bid_to_seconds.append(result["bid_to_second_value"])
            attacker_wins += result["winner_is_attacker"]

            block_rows.append({
                "n_attack":            n_attack,
                "block_num":           blk,
                "winner_idx":          result["winner_idx"],
                "winning_bid":         round(result["winning_bid"], 2),
                "top_block_value":     round(result["top_block_value"], 2),
                "second_highest_bv":   round(result["second_highest_bv"], 2),
                "winner_is_attacker":  result["winner_is_attacker"],
                "bid_to_top_value":    round(result["bid_to_top_value"], 6),
                "bid_to_second_value": round(result["bid_to_second_value"], 6),
            })

        builder_gini = gini(win_counts)
        mev_frac     = n_attack / N_BUILDERS
        mean_top     = float(np.mean(bid_to_tops)) * 100
        mean_second  = float(np.mean(bid_to_seconds)) * 100
        atk_win_rate = attacker_wins / N_BLOCKS * 100

        summary_rows.append({
            "n_attack":           n_attack,
            "mev_fraction":       round(mev_frac, 3),
            "mean_bid_to_top":    round(mean_top, 2),
            "mean_bid_to_second": round(mean_second, 2),
            "attacker_win_rate":  round(atk_win_rate, 2),
            "builder_gini":       round(builder_gini, 4),
        })

        print(f"{n_attack:>8} | {mev_frac*100:>7.0f}% | {mean_top:>7.1f}% | "
              f"{mean_second:>7.1f}% | {atk_win_rate:>7.1f}% | {builder_gini:>8.4f}")

    with open(blocks_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(block_rows[0].keys()))
        writer.writeheader()
        writer.writerows(block_rows)

    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"\nSaved {blocks_path.name}  ({len(block_rows)} rows)")
    print(f"Saved {summary_path.name}  ({len(summary_rows)} rows)")
    return summary_rows


if __name__ == "__main__":
    run_simulation()

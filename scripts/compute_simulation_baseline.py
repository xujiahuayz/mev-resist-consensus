"""
Extract simulation metrics for validation against real empirical data.

Uses the (validators=10, users=25) configuration — 50% attacking validators and
50% attacking users — as the "realistic MEV" baseline. This reflects moderate
MEV extraction activity consistent with real-world Ethereum conditions where a
significant fraction of validators are MEV-aware.

Reads:   data/same_seed/by_period/<PERIOD>/pos/pos_transactions_validators10_users25.csv
         data/same_seed/by_period/<PERIOD>/pos/pos_block_data_validators10_users25.csv
Writes:  data/empirical/sim_baseline_gas_fees.csv          (period, gas_fee_gwei)
         data/empirical/sim_baseline_validator_counts.csv  (period, validator_id, block_count)

Usage:
    python scripts/compute_simulation_baseline.py
"""

import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

BY_PERIOD = PROJECT_ROOT / "data" / "same_seed" / "by_period"
OUT_DIR   = PROJECT_ROOT / "data" / "empirical"

PERIODS = [
    "STABLE_PRE_MERGE_2022",
    "STABLE_POST_MERGE_2022",
    "STABLE_POST_MERGE_2023",
    "FTX_COLLAPSE_NOV_2022",
    "LUNA_CRASH_MAY_2022",
    "USDC_DEPEG_MARCH_2023",
]

# 50% attacker validators, 50% attacker users — realistic MEV scenario
V, U = 10, 25


def main():
    gas_fee_rows         = []
    validator_count_rows = []

    for period in PERIODS:
        pos_dir    = BY_PERIOD / period / "pos"
        tx_path    = pos_dir / f"pos_transactions_validators{V}_users{U}.csv"
        block_path = pos_dir / f"pos_block_data_validators{V}_users{U}.csv"

        if not tx_path.exists():
            print(f"SKIP {period}: no simulation transactions found")
            continue

        print(f"{period}: loading simulation data (validators={V}, users={U})")
        tx_df    = pd.read_csv(tx_path)
        block_df = pd.read_csv(block_path) if block_path.exists() else None

        # 1. Per-transaction gas fees (for ECDF comparison with real data)
        fees = tx_df["gas_fee"].dropna()
        fees = fees[fees > 0]
        for fee in fees:
            gas_fee_rows.append({"period": period, "gas_fee_gwei": float(fee)})

        # 2. Validator block concentration (for Lorenz curve)
        if block_df is not None:
            counts = block_df["validator_id"].value_counts()
            for vid, cnt in counts.items():
                validator_count_rows.append({
                    "period": period,
                    "validator_id": vid,
                    "block_count": int(cnt),
                })

    if not gas_fee_rows:
        print("No simulation data found. Run scripts/run_experiments_by_period.py first.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(gas_fee_rows).to_csv(OUT_DIR / "sim_baseline_gas_fees.csv", index=False)
    pd.DataFrame(validator_count_rows).to_csv(OUT_DIR / "sim_baseline_validator_counts.csv", index=False)
    print(f"\nSaved simulation baseline CSVs to {OUT_DIR}/")


if __name__ == "__main__":
    main()

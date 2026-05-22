"""
Extract simulation metrics from the canonical 50%-MEV PoS baseline.

Uses the canonical config from blockchain_env/sim_config.py with
MEV_FRACTION_PRIMARY (50%) attacking validators / users. The "(V, U)"
attacker counts below are derived from those constants so this script
stays in lockstep with the rest of the pipeline.

Reads:   data/same_seed/by_period/<PERIOD>/pos/pos_transactions_validators{V}_users{U}.csv
         data/same_seed/by_period/<PERIOD>/pos/pos_block_data_validators{V}_users{U}.csv
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

from blockchain_env.period_definitions import DEFAULT_PERIOD_NAMES
from blockchain_env.sim_config import VALIDATORS, USERS, MEV_FRACTION_PRIMARY

BY_PERIOD = PROJECT_ROOT / "data" / "same_seed" / "by_period"
OUT_DIR   = PROJECT_ROOT / "data" / "empirical"

PERIODS = DEFAULT_PERIOD_NAMES

# Attacker counts at the primary MEV fraction
V = int(round(VALIDATORS * MEV_FRACTION_PRIMARY))
U = int(round(USERS * MEV_FRACTION_PRIMARY))


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

        # 1. Per-transaction gas fees (for CDF comparison with real data)
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

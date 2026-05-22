"""
Run empirical analysis on real Ethereum block data.

Reads:   data/fetch/<PERIOD>/block_*.json  (via EthereumDataLoader.load_period_blocks)
Writes:  data/empirical/gas_fee_per_block.csv
         data/empirical/all_gas_fees.csv
         data/empirical/miner_block_counts.csv
         data/empirical/ordering_inversions.csv

Usage:
    python scripts/run_empirical_analysis.py
"""

import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from blockchain_env.data_loader import EthereumDataLoader
from blockchain_env.empirical_metrics import (
    gas_fee_per_block,
    block_concentration,
    ordering_inversions_per_block,
)

PERIODS = [
    "STABLE_PRE_MERGE_2022",
    "STABLE_POST_MERGE_2022",
    "STABLE_POST_MERGE_2023",
    "FTX_COLLAPSE_NOV_2022",
    "LUNA_CRASH_MAY_2022",
    "USDC_DEPEG_MARCH_2023",
]
OUT_DIR = PROJECT_ROOT / "data" / "empirical"


def main():
    loader = EthereumDataLoader(data_path=str(PROJECT_ROOT / "data" / "fetch"))

    gas_block_rows = []
    all_fee_rows = []
    miner_count_rows = []
    inversion_rows = []

    for period_name in PERIODS:
        blocks = loader.load_period_blocks(period_name)
        if not blocks:
            print(f"SKIP {period_name}: no blocks loaded")
            continue
        print(f"{period_name}: {len(blocks)} blocks")

        # 1. Per-block gas fee stats
        gdf = gas_fee_per_block(blocks)
        gdf.insert(0, "period", period_name)
        gas_block_rows.append(gdf)

        # 2. All individual transaction gas fees (for CDF plots)
        for b in blocks:
            bnum = b.get("block_number")
            for fee in b.get("gas_fees_gwei", []):
                try:
                    all_fee_rows.append({
                        "period": period_name,
                        "block_number": bnum,
                        "gas_fee_gwei": float(fee),
                    })
                except (TypeError, ValueError):
                    pass

        # 3. Block concentration — per-miner counts for Lorenz curves
        conc = block_concentration(blocks)
        for miner, count in conc["miner_counts"].items():
            miner_count_rows.append({
                "period": period_name,
                "miner": miner,
                "block_count": count,
            })

        # 4. Per-block ordering inversions
        idf = ordering_inversions_per_block(blocks)
        idf.insert(0, "period", period_name)
        inversion_rows.append(idf)

    if not inversion_rows:
        print("No data found. Run fetch/fetch_resume.py first.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.concat(gas_block_rows, ignore_index=True).to_csv(
        OUT_DIR / "gas_fee_per_block.csv", index=False)

    pd.DataFrame(all_fee_rows).to_csv(
        OUT_DIR / "all_gas_fees.csv", index=False)

    pd.DataFrame(miner_count_rows).to_csv(
        OUT_DIR / "miner_block_counts.csv", index=False)

    pd.concat(inversion_rows, ignore_index=True).to_csv(
        OUT_DIR / "ordering_inversions.csv", index=False)

    print(f"\nSaved 4 CSVs to {OUT_DIR}/")
    print("Next: run plots/empirical/plot_*.py to generate figures.")


if __name__ == "__main__":
    main()

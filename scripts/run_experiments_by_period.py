"""
Run PoS and PBS simulations per time period using period-specific gas/MEV from data/fetch.

Data extraction (no fallback):
- Only data extracted from data/fetch is used. If a period has no data, it is skipped; if no
  periods have data, the script exits with an error so results are never based on fallback values.
- If data/fetch has period subdirs (e.g. USDC_DEPEG_MARCH_2023/), each period is loaded from its dir.
- If data/fetch has only flat block_*.json, blocks are assigned to periods by block number using
  blockchain_env.period_definitions.BLOCK_RANGES_BY_PERIOD.

Each run sets simulation_config.gas_fee_pool and mev_pool in worker processes so User.create_transactions
samples from that period's data. Results are written under data/same_seed/by_period/<period>/pos/ and .../pbs/.

Usage:
  python scripts/run_experiments_by_period.py

Prerequisites:
  - data/fetch with either period subdirs (from fetch/fetch.py) or flat block_*.json.
  - Run fetch/fetch.py to refresh data if needed. By-period runs do not use fallback gas/MEV.
"""

import os
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

# Subset of (validators/builders, users) for by-period runs
CONFIGS = [(0, 0), (10, 25), (20, 50)]
POOL_SAMPLES = 2000


def _worker_set_period(period_name, gas_fees, mev_potentials):
    """Pool initializer: set simulation_config in each worker for period-specific transaction data."""
    from blockchain_env import simulation_config
    simulation_config.set_period_pools(period_name, gas_fees, mev_potentials)


def get_periods_with_pools():
    """
    Return list of (period_name, gas_fees_list, mev_potentials_list) using only data extracted
    from data/fetch per period. No fallback: periods with no data are skipped; if no periods
    have data, exit with an error so the pipeline uses real period data and avoids wrong results.
    """
    try:
        from blockchain_env.data_loader import EthereumDataLoader
    except ImportError as e:
        print(f"Error: {e}. Cannot load period data.")
        sys.exit(1)

    loader = EthereumDataLoader()
    names = loader.get_period_names()
    if not names:
        print(
            "No period data in data/fetch (no subdirs and no flat block_*.json in range).\n"
            "Run fetch/fetch.py to populate data/fetch, or add block_*.json so blocks fall into\n"
            "period ranges in blockchain_env/period_definitions.py. By-period runs do not use fallback."
        )
        sys.exit(1)

    out = []
    for period_name in names:
        try:
            gas_fees = loader.sample_gas_fees(period_name, n_samples=POOL_SAMPLES)
            mev_potentials = loader.get_mev_potentials(period_name, n_samples=POOL_SAMPLES)
            if not gas_fees or not mev_potentials:
                print(f"Skip period {period_name}: no gas_fees or mev_potentials (use only extracted data, no fallback).")
                continue
            out.append((period_name, gas_fees, mev_potentials))
        except Exception as e:
            print(f"Skip period {period_name}: {e}")
            continue

    if not out:
        print(
            "No periods had usable data. Ensure data/fetch contains block_*.json (or period subdirs)\n"
            "with blocks in the ranges defined in period_definitions.py. By-period runs do not use fallback."
        )
        sys.exit(1)
    return out


def run_pos_for_period(period_name, output_base, gas_fees, mev_potentials):
    """Run PoS for CONFIGS and save under output_base. Workers get period pools via initializer."""
    import scripts.simulate_pos as sim_pos
    pos_dir = os.path.join(output_base, "pos")
    os.makedirs(pos_dir, exist_ok=True)
    initargs = (period_name, gas_fees, mev_potentials)
    for v, u in CONFIGS:
        t0 = time.time()
        sim_pos.run_simulation_in_process(
            v, u,
            output_dir=pos_dir,
            pool_initializer=_worker_set_period,
            pool_initargs=initargs,
        )
        print(f"  PoS ({v},{u}) done in {time.time() - t0:.1f}s")
    return pos_dir


def run_pbs_for_period(period_name, output_base, gas_fees, mev_potentials):
    """Run PBS for CONFIGS and save under output_base."""
    import scripts.simulate_pbs as sim_pbs
    pbs_dir = os.path.join(output_base, "pbs")
    os.makedirs(pbs_dir, exist_ok=True)
    initargs = (period_name, gas_fees, mev_potentials)
    for b, u in CONFIGS:
        t0 = time.time()
        sim_pbs.run_simulation_in_process(
            b, u,
            output_dir=pbs_dir,
            pool_initializer=_worker_set_period,
            pool_initargs=initargs,
        )
        print(f"  PBS ({b},{u}) done in {time.time() - t0:.1f}s")
    return pbs_dir


def main():
    by_period_base = os.path.join("data", "same_seed", "by_period")
    periods_with_pools = get_periods_with_pools()
    print(f"Running by-period experiments for {len(periods_with_pools)} periods: {[p[0] for p in periods_with_pools]}")
    for period_name, gas_fees, mev_potentials in periods_with_pools:
        output_base = os.path.join(by_period_base, period_name)
        os.makedirs(output_base, exist_ok=True)
        print(f"\n--- {period_name} ---")
        run_pos_for_period(period_name, output_base, gas_fees, mev_potentials)
        run_pbs_for_period(period_name, output_base, gas_fees, mev_potentials)
    print(f"\nDone. Outputs under {by_period_base}/")


if __name__ == "__main__":
    main()

"""
Robustness sweep: run PoS and PBS at MEV_FRACTIONS_ROBUSTNESS for each period.

The single 50%-MEV primary run answers the headline question; this sweep
exists to show that conclusions are stable across plausible attacker
fractions (25 / 50 / 75%). Outputs land in dedicated mev_<N>/ subdirectories
so the primary results in pos/ and pbs/ are not overwritten.

Reads:   data/fetch/ (period block JSONs, loaded by EthereumDataLoader)
Writes:  data/same_seed/by_period/<PERIOD>/<protocol>/mev_<N>/...

Usage:
    python scripts/run_robustness_sweep.py
"""

import os
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from blockchain_env.sim_config import (
    VALIDATORS, BUILDERS, USERS, MEV_FRACTIONS_ROBUSTNESS, mev_dir,
)

POOL_SAMPLES = 2000


def _worker_set_period(period_name, gas_fees, mev_potentials):
    from blockchain_env import simulation_config
    simulation_config.set_period_pools(period_name, gas_fees, mev_potentials)


def _periods_with_pools():
    from blockchain_env.data_loader import EthereumDataLoader
    loader = EthereumDataLoader()
    names = loader.get_period_names()
    if not names:
        print("No period data in data/fetch. Run fetch/fetch_resume.py first.")
        sys.exit(1)
    out = []
    for name in names:
        try:
            gas_fees = loader.sample_gas_fees(name, n_samples=POOL_SAMPLES)
            mev_potentials = loader.get_mev_potentials(name, n_samples=POOL_SAMPLES)
            if gas_fees and mev_potentials:
                out.append((name, gas_fees, mev_potentials))
        except Exception as e:
            print(f"  skip {name}: {e}")
    if not out:
        print("No periods had usable data.")
        sys.exit(1)
    return out


def _attacker_counts(frac: float) -> tuple[int, int, int]:
    """Returns (attacker_validators, attacker_builders, attacker_users) at the given fraction."""
    return (
        int(round(VALIDATORS * frac)),
        int(round(BUILDERS * frac)),
        int(round(USERS * frac)),
    )


def main():
    import scripts.simulate_pos as sim_pos
    import scripts.simulate_pbs as sim_pbs

    periods = _periods_with_pools()
    print(f"Running robustness sweep across {len(periods)} periods at "
          f"MEV fractions {MEV_FRACTIONS_ROBUSTNESS}")

    for period_name, gas_fees, mev_potentials in periods:
        initargs = (period_name, gas_fees, mev_potentials)
        for frac in MEV_FRACTIONS_ROBUSTNESS:
            v_atk, b_atk, u_atk = _attacker_counts(frac)
            mev_subdir = mev_dir(frac)
            print(f"\n--- {period_name}  mev={frac:.2f}  ({v_atk}V/{b_atk}B/{u_atk}U attackers) ---")

            pos_out = PROJECT_ROOT / "data" / "same_seed" / "by_period" / period_name / "pos" / mev_subdir
            pbs_out = PROJECT_ROOT / "data" / "same_seed" / "by_period" / period_name / "pbs" / mev_subdir
            pos_out.mkdir(parents=True, exist_ok=True)
            pbs_out.mkdir(parents=True, exist_ok=True)

            t0 = time.time()
            sim_pos.run_simulation_in_process(
                v_atk, u_atk,
                output_dir=str(pos_out),
                pool_initializer=_worker_set_period,
                pool_initargs=initargs,
            )
            print(f"  PoS done in {time.time() - t0:.1f}s")

            t0 = time.time()
            sim_pbs.run_simulation_in_process(
                b_atk, u_atk,
                output_dir=str(pbs_out),
                pool_initializer=_worker_set_period,
                pool_initargs=initargs,
            )
            print(f"  PBS done in {time.time() - t0:.1f}s")

    print("\nRobustness sweep complete.")


if __name__ == "__main__":
    main()

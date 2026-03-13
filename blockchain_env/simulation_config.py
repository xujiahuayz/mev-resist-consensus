"""Simulation config for period-aware experiments.

When running experiments across time periods, the script sets
gas_fee_pool and mev_pool (sampled from fetched period data) here.
User.create_transactions() then samples from these pools so that
transaction gas fees and MEV reflect the chosen period.
"""

from typing import List, Optional

# Current period name (e.g. "STABLE_POST_MERGE_2023") for logging/labels only.
current_period_name: Optional[str] = None

# Pre-sampled gas fees and MEV potentials for the current run.
# When set, User.create_transactions uses these for period-specific transaction sampling.
gas_fee_pool: Optional[List[int]] = None
mev_pool: Optional[List[int]] = None


def set_period_pools(
    period_name: Optional[str],
    gas_fees: Optional[List[float]] = None,
    mev_potentials: Optional[List[float]] = None,
) -> None:
    """Set the pools used for transaction creation (period-specific or default)."""
    global current_period_name, gas_fee_pool, mev_pool
    current_period_name = period_name
    if gas_fees is not None:
        gas_fee_pool = [int(float(g)) for g in gas_fees]
    else:
        gas_fee_pool = None
    if mev_potentials is not None:
        mev_pool = [int(float(m)) for m in mev_potentials]
    else:
        mev_pool = None


def clear_period_pools() -> None:
    """Clear period pools so simulations use fallback again."""
    set_period_pools(None, None, None)

"""This file contains the configuration settings for the market environment."""

import random
from settings import PROJECT_ROOT

DATA_PATH = PROJECT_ROOT / "data"
FIGURE_PATH = PROJECT_ROOT / "figures"
CACHE_PATH = PROJECT_ROOT / ".cache"

BASE_FEE = 0.1
GAS_LIMIT = 1400
BUILDER_STRATEGY_LIST = ["greedy", "random", "FCFS", "mev"]
PROPOSER_STRATEGY_LIST = ["greedy", "random", "cheap"]

# Data loading from real Ethereum data
def get_gas_fees(n_samples: int = 100, period_name: str = None):
    """Get gas fees from fetched Ethereum data.
    
    Raises:
        ImportError: If data_loader module cannot be imported
        RuntimeError: If gas fees cannot be loaded from data
    """
    from data_loader import get_real_gas_fees
    gas_fees = get_real_gas_fees(period_name, n_samples)
    if not gas_fees:
        raise RuntimeError(
            f"Failed to load gas fees: No data available for period '{period_name}' "
            f"with {n_samples} samples. Please ensure data has been fetched."
        )
    return gas_fees

def get_simulation_gas_fees(period_type: str = None, era: str = None, n_samples: int = 100):
    """Get gas fees for simulation testing from specific period types or eras.
    
    Raises:
        ImportError: If data_loader module cannot be imported
        RuntimeError: If gas fees cannot be loaded from data
    """
    from data_loader import get_simulation_data
    data = get_simulation_data(period_type, era, n_samples)
    gas_fees = data.get('gas_fees', [])
    if not gas_fees:
        raise RuntimeError(
            f"Failed to load gas fees: No data available for period_type='{period_type}', "
            f"era='{era}' with {n_samples} samples. Please ensure data has been fetched."
        )
    return gas_fees

def get_mev_potentials(n_samples: int = 100, period_name: str = None):
    """Get MEV potentials from fetched Ethereum data.
    
    Raises:
        ImportError: If data_loader module cannot be imported
        RuntimeError: If MEV potentials cannot be loaded from data
    """
    from data_loader import get_real_mev_potentials
    mev_potentials = get_real_mev_potentials(period_name, n_samples)
    if not mev_potentials:
        raise RuntimeError(
            f"Failed to load MEV potentials: No data available for period '{period_name}' "
            f"with {n_samples} samples. Please ensure data has been fetched."
        )
    return mev_potentials

def get_simulation_mev_potentials(period_type: str = None, era: str = None, n_samples: int = 100):
    """Get MEV potentials for simulation testing from specific period types or eras.
    
    Raises:
        ImportError: If data_loader module cannot be imported
        RuntimeError: If MEV potentials cannot be loaded from data
    """
    from data_loader import get_simulation_data
    data = get_simulation_data(period_type, era, n_samples)
    mev_potentials = data.get('mev_potentials', [])
    if not mev_potentials:
        raise RuntimeError(
            f"Failed to load MEV potentials: No data available for period_type='{period_type}', "
            f"era='{era}' with {n_samples} samples. Please ensure data has been fetched."
        )
    return mev_potentials

# Fallback functions commented out - use real data only
# def get_fallback_gas_fees(n_samples: int = 100):
#     """Fallback hardcoded gas fees if real data not available."""
#     SAMPLE_GAS_FEES = [
#         190000, 1000000, 2300000, 170000, 1000000, 77000, 470000, 1500000, 4500000,
#         310000, 970000, 660000, 1300000, 6100000, 1500000, 130000, 120000, 2400000,
#         160000, 460000, 87000, 110000, 98000, 870000, 1900000, 120000, 530000,
#         150000, 150000, 120000, 340000, 30000000, 1200000, 120000, 670000, 82000,
#         310000, 160000, 170000, 84000, 600000, 420000, 220000, 1500000, 2600000,
#         120000, 370000, 110000, 43000000, 5200000, 110000, 79000, 110000, 2100000,
#         300000, 85000, 1400000, 2500000, 1600000, 100000, 3200000, 3600000, 19000000,
#         1100000, 260000, 1400000, 170000, 650000, 2000000, 220000, 1600000, 160000,
#         4200000, 27000000, 3500000, 2000000, 150000, 260000, 1100000, 240000,
#         630000, 5000000, 460000, 83000, 220000, 70000, 6300000, 360000, 2000000,
#         350000, 73000, 320000, 1800000, 150000, 1700000, 5000000, 80000, 420000,
#         910000, 1000000
#     ]
#     return random.sample(SAMPLE_GAS_FEES, min(n_samples, len(SAMPLE_GAS_FEES)))
#
# def get_fallback_mev_potentials(n_samples: int = 100):
#     """Fallback hardcoded MEV potentials if real data not available."""
#     MEV_POTENTIALS = [
#         6390, 73100, 0, 5640, 5180, 24700, 67900, 71800, 128000, 146000, 0, 19700,
#         18600, 545000, 13900, 47700, 7190000, 779000, 21800, 35600, 46500, 256000,
#         17000, 322000, 23500, 13900, 11200, 0, 0, 64600, 1100000, 161000, 12300,
#         769000, 0, 594000, 100000, 959000, 0, 21800, 17700000, 84800, 49100, 381000,
#         13800, 31700, 39400, 33300, 0, 75000, 15100, 66100, 510000, 283000, 30200, 0,
#         0, 15700, 43600, 35100, 285000, 8520, 0, 14200, 36800, 16400, 10700, 215000,
#         139000, 33100, 0, 32900, 3130, 410000, 0, 34700, 121000, 67500, 68100, 0, 0,
#         60700, 195000, 164000, 231000, 12800, 155000, 7840, 296000, 181000, 4320000,
#         5630, 12800, 15300, 108000, 369000, 16400, 350000, 56200, 42000, 0, 0, 0, 0,
#         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
#         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
#         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
#         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
#         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
#         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
#         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
#         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
#         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
#         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
#     ]
#     return random.sample(MEV_POTENTIALS, min(n_samples, len(MEV_POTENTIALS)))

# Legacy access for backward compatibility
SAMPLE_GAS_FEES = get_gas_fees
MEV_POTENTIALS = get_mev_potentials

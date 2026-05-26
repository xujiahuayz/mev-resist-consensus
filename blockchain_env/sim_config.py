"""Canonical simulation parameters.

Single source of truth. All simulator entry points import from here.
The primary (paper-headline) config is the values below; robustness sweeps
vary MEV_FRACTION across MEV_FRACTIONS_ROBUSTNESS.
"""

VALIDATORS = 50
BUILDERS = 50
PROPOSERS = 50
USERS = 100
BLOCKS_PER_SIM = 1000

MEV_FRACTION_PRIMARY = 0.50
MEV_FRACTIONS_ROBUSTNESS = (0.25, 0.50, 0.75)


def primary_config_label() -> str:
    """Short string suffix for output filenames at the primary MEV fraction."""
    return f"validators{VALIDATORS}_users{USERS}"


def pbs_config_label() -> str:
    return f"builders{BUILDERS}_users{USERS}"


def mev_dir(frac: float) -> str:
    """Subdirectory name for a robustness-sweep run, e.g. 'mev_50'."""
    return f"mev_{int(round(frac * 100))}"

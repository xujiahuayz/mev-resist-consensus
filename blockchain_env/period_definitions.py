"""Block number ranges per period for partitioning flat fetch data and for fetch scripts."""

# Period name -> (start_block, end_block) inclusive. Used to assign blocks to periods when
# data/fetch contains flat block_*.json (no period subdirs). Must not overlap so each block
# maps to at most one period.
BLOCK_RANGES_BY_PERIOD = {
    "LUNA_CRASH_MAY_2022": (14800000, 14801000),
    "STABLE_PRE_MERGE_2022": (15000000, 15001000),
    "FTX_COLLAPSE_NOV_2022": (16000000, 16001000),
    "STABLE_POST_MERGE_2022": (16001001, 16002000),
    "USDC_DEPEG_MARCH_2023": (16900000, 16901000),
    "STABLE_POST_MERGE_2023": (17500000, 17501000),
}

DEFAULT_PERIOD_NAMES = list(BLOCK_RANGES_BY_PERIOD.keys())


def period_for_block(block_number: int):
    """Return period name if block_number falls in any defined range, else None."""
    for name, (start, end) in BLOCK_RANGES_BY_PERIOD.items():
        if start <= block_number <= end:
            return name
    return None

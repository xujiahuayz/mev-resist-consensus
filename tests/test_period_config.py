"""Invariants for the empirical period config.

The period windows feed both the fetch pipeline and the simulator's
empirical sampling. Regressions here (overlapping ranges, mis-anchored
event dates) silently corrupt every downstream figure, so this file
guards them explicitly.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from blockchain_env.period_definitions import (
    BLOCK_RANGES_BY_PERIOD,
    DEFAULT_PERIOD_NAMES,
    period_for_block,
)

EXPECTED_PERIODS = {
    "LUNA_CRASH_MAY_2022",
    "STABLE_PRE_MERGE_2022",
    "STABLE_POST_MERGE_2022",
    "FTX_COLLAPSE_NOV_2022",
    "USDC_DEPEG_MARCH_2023",
    "STABLE_POST_MERGE_2023",
}

WINDOW_SIZE = 5000


def test_six_periods():
    assert set(BLOCK_RANGES_BY_PERIOD.keys()) == EXPECTED_PERIODS


def test_each_window_is_5000_blocks():
    for name, (start, end) in BLOCK_RANGES_BY_PERIOD.items():
        assert end - start == WINDOW_SIZE, f"{name}: expected {WINDOW_SIZE}-block span, got {end - start}"


def test_no_overlapping_ranges():
    items = sorted(BLOCK_RANGES_BY_PERIOD.items(), key=lambda kv: kv[1][0])
    for (a_name, (a_start, a_end)), (b_name, (b_start, b_end)) in zip(items, items[1:]):
        assert a_end < b_start, (
            f"Periods {a_name} ({a_start}..{a_end}) and {b_name} ({b_start}..{b_end}) overlap"
        )


@pytest.mark.parametrize("block,expected", [
    # Anchors: pick a representative block inside each window and confirm mapping.
    (14_797_500, "LUNA_CRASH_MAY_2022"),
    (15_302_500, "STABLE_PRE_MERGE_2022"),
    (15_752_500, "STABLE_POST_MERGE_2022"),
    (15_957_500, "FTX_COLLAPSE_NOV_2022"),
    (16_834_500, "USDC_DEPEG_MARCH_2023"),
    (17_502_500, "STABLE_POST_MERGE_2023"),
])
def test_period_for_block_anchors(block, expected):
    assert period_for_block(block) == expected


@pytest.mark.parametrize("block", [
    # The old duplicate-bug window: must NOT map to any period now.
    16_000_500,
    # Mar 14 2023 — post-USDC-recovery; this is what the OLD config mis-anchored to.
    16_900_500,
    # Outside all windows.
    1_000,
])
def test_period_for_block_outside_windows(block):
    assert period_for_block(block) is None


def test_default_period_names_matches_dict():
    assert set(DEFAULT_PERIOD_NAMES) == set(BLOCK_RANGES_BY_PERIOD.keys())

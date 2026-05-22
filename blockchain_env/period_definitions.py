"""Block ranges per period, loaded from fetch/periods_config.json.

Single source of truth: fetch/periods_config.json. This module exposes the
same dict-and-helper API the rest of the codebase has used historically.
"""

import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "fetch" / "periods_config.json"


def _load() -> dict[str, tuple[int, int]]:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    out: dict[str, tuple[int, int]] = {}
    for group_key in ("stable_periods", "high_volatility_periods"):
        for name, body in cfg.get(group_key, {}).items():
            out[name] = (int(body["start"]), int(body["end"]))
    return out


def _assert_invariants(ranges: dict[str, tuple[int, int]]) -> None:
    items = sorted(ranges.items(), key=lambda kv: kv[1][0])
    prev_end = -1
    prev_name = None
    for name, (start, end) in items:
        if end <= start:
            raise ValueError(f"Period {name} has non-positive span: {start}..{end}")
        if start <= prev_end:
            raise ValueError(
                f"Period {name} ({start}..{end}) overlaps with {prev_name} (ends at {prev_end})"
            )
        prev_end, prev_name = end, name


BLOCK_RANGES_BY_PERIOD: dict[str, tuple[int, int]] = _load()
_assert_invariants(BLOCK_RANGES_BY_PERIOD)
DEFAULT_PERIOD_NAMES = list(BLOCK_RANGES_BY_PERIOD.keys())


def period_for_block(block_number: int):
    """Return period name if block_number falls in any defined range, else None."""
    for name, (start, end) in BLOCK_RANGES_BY_PERIOD.items():
        if start <= block_number <= end:
            return name
    return None

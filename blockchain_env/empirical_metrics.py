"""
Pure metric functions for empirical analysis of real Ethereum block data.

All functions take a list of block dicts (from EthereumDataLoader.load_period_blocks)
and return DataFrames or dicts. No I/O.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Gas fee distribution
# ---------------------------------------------------------------------------

def gas_fee_per_block(blocks: list[dict]) -> pd.DataFrame:
    """
    Per-block gas fee summary.
    Returns DataFrame with columns:
        block_number, mean_gas_fee_gwei, median_gas_fee_gwei,
        total_gas_fees_gwei, num_transactions
    """
    rows = []
    for b in blocks:
        fees = [float(f) for f in b.get("gas_fees_gwei", []) if f is not None]
        rows.append({
            "block_number": b.get("block_number"),
            "mean_gas_fee_gwei": float(np.mean(fees)) if fees else 0.0,
            "median_gas_fee_gwei": float(np.median(fees)) if fees else 0.0,
            "total_gas_fees_gwei": float(np.sum(fees)) if fees else 0.0,
            "num_transactions": len(fees),
        })
    return pd.DataFrame(rows)


def gas_fee_stats(blocks: list[dict]) -> dict:
    """
    Summary statistics for all transaction gas fees in a set of blocks.
    Keys: mean, median, std, p25, p75, p95, p99, total_tx_count
    """
    all_fees = []
    for b in blocks:
        all_fees.extend(float(f) for f in b.get("gas_fees_gwei", []) if f is not None)
    if not all_fees:
        return {k: 0.0 for k in ("mean", "median", "std", "p25", "p75", "p95", "p99", "total_tx_count")}
    arr = np.array(all_fees)
    return {
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "std": float(arr.std()),
        "p25": float(np.percentile(arr, 25)),
        "p75": float(np.percentile(arr, 75)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "total_tx_count": len(all_fees),
    }


# ---------------------------------------------------------------------------
# Miner/builder concentration
# ---------------------------------------------------------------------------

def gini_coefficient(values: list[float]) -> float:
    """
    Gini coefficient for a list of non-negative values.
    Returns 0.0 for empty or all-zero input.
    """
    arr = np.array([v for v in values if v >= 0], dtype=float)
    n = len(arr)
    if n == 0 or arr.sum() == 0:
        return 0.0
    arr = np.sort(arr)
    idx = np.arange(1, n + 1)
    return float((2 * (idx * arr).sum() - (n + 1) * arr.sum()) / (n * arr.sum()))


def block_concentration(blocks: list[dict]) -> dict:
    """
    Miner block concentration for a period.

    Returns:
        gini: Gini coefficient over miner block counts
        top1_share: fraction of blocks by single largest miner
        top3_share: fraction by top 3 miners
        unique_miners: number of distinct miners
        total_blocks: total block count
        miner_counts: dict[address -> count], sorted descending by count
    """
    counts: dict[str, int] = {}
    for b in blocks:
        miner = b.get("miner", "unknown")
        counts[miner] = counts.get(miner, 0) + 1

    total = len(blocks)
    if total == 0:
        return {
            "gini": 0.0,
            "top1_share": 0.0,
            "top3_share": 0.0,
            "unique_miners": 0,
            "total_blocks": 0,
            "miner_counts": {},
        }

    sorted_counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
    values = list(sorted_counts.values())

    top1 = values[0] / total
    top3 = sum(values[:3]) / total

    return {
        "gini": gini_coefficient(list(counts.values())),
        "top1_share": top1,
        "top3_share": top3,
        "unique_miners": len(counts),
        "total_blocks": total,
        "miner_counts": sorted_counts,
    }


# ---------------------------------------------------------------------------
# Transaction ordering inversions
# ---------------------------------------------------------------------------

def _inversionen(arr: list[int]) -> tuple[list[int], int]:
    """Merge-sort-based inversion count. Returns (sorted_arr, inversion_count)."""
    m = len(arr)
    if m < 2:
        return arr, 0
    x1, x2 = arr[: m // 2], arr[m // 2 :]
    l1, inv1 = _inversionen(x1)
    l2, inv2 = _inversionen(x2)
    merged, cross = _modified_merge(l1, l2)
    return merged, inv1 + inv2 + cross


def _modified_merge(l1: list[int], l2: list[int]) -> tuple[list[int], int]:
    m1, m2 = len(l1), len(l2)
    merged, i, j, cross = [], 0, 0, 0
    while i < m1 and j < m2:
        if l1[i] <= l2[j]:
            merged.append(l1[i])
            i += 1
        else:
            merged.append(l2[j])
            cross += m1 - i
            j += 1
    merged.extend(l1[i:])
    merged.extend(l2[j:])
    return merged, cross


def ordering_inversions_for_block(
    block: dict,
    *,
    order_key: str = "transaction_index",
    priority_key: str = "gas_price_gwei",
    id_key: str = "hash",
) -> dict:
    """
    Inversion count comparing priority order to actual inclusion order within a block.

    Works on both empirical block dicts (default keys: transaction_index, gas_price_gwei, hash)
    and simulator-output block dicts (override to e.g. order_key="position",
    priority_key="gas_fee", id_key="id").

    Algorithm:
      1. Sort txs by priority_key descending → expected_rank[id] = position (0=highest)
      2. Read txs in actual order_key order
      3. Count inversions in the resulting rank sequence

    An inversion means a lower-priority tx (higher rank number) appears before
    a higher-priority tx (lower rank number) — evidence of non-priority ordering.

    Returns:
        block_number, num_transactions, inversion_count,
        inversion_rate (= inversion_count / max_possible),
        max_possible_inversions (= n*(n-1)//2)
    """
    txs = block.get("transactions", [])
    n = len(txs)
    block_number = block.get("block_number", 0)

    if n < 2:
        return {
            "block_number": block_number,
            "num_transactions": n,
            "inversion_count": 0,
            "inversion_rate": 0.0,
            "max_possible_inversions": 0,
        }

    try:
        by_priority = sorted(txs, key=lambda t: float(t.get(priority_key) or 0), reverse=True)
    except (TypeError, ValueError):
        by_priority = txs

    expected_rank = {tx.get(id_key, i): i for i, tx in enumerate(by_priority)}

    try:
        actual_order = sorted(txs, key=lambda t: float(t.get(order_key) or 0))
    except (TypeError, ValueError):
        actual_order = txs

    rank_sequence = [expected_rank.get(tx.get(id_key, i), i) for i, tx in enumerate(actual_order)]

    _, inv_count = _inversionen(rank_sequence)
    max_possible = n * (n - 1) // 2

    return {
        "block_number": block_number,
        "num_transactions": n,
        "inversion_count": inv_count,
        "inversion_rate": inv_count / max_possible if max_possible > 0 else 0.0,
        "max_possible_inversions": max_possible,
    }


def ordering_inversions_per_block(
    blocks: list[dict],
    *,
    order_key: str = "transaction_index",
    priority_key: str = "gas_price_gwei",
    id_key: str = "hash",
) -> pd.DataFrame:
    """Apply ordering_inversions_for_block to each block. Returns DataFrame."""
    return pd.DataFrame([
        ordering_inversions_for_block(
            b, order_key=order_key, priority_key=priority_key, id_key=id_key
        )
        for b in blocks
    ])


def ordering_inversions_from_tx_df(
    tx_df: "pd.DataFrame",
    *,
    block_key: str = "included_at",
    order_key: str = "position",
    priority_key: str = "gas_fee",
    id_key: str = "id",
) -> pd.DataFrame:
    """
    Compute per-block inversions from a flat transactions DataFrame.

    Used to postprocess simulator output CSVs (one row per transaction,
    keyed by block via `block_key`) into a per-block inversions table
    matching the schema of data/empirical/ordering_inversions.csv.
    """
    if tx_df.empty:
        return pd.DataFrame(columns=[
            "block_number", "num_transactions", "inversion_count",
            "inversion_rate", "max_possible_inversions",
        ])
    rows = []
    for bnum, group in tx_df.groupby(block_key, sort=True):
        block = {
            "block_number": int(bnum),
            "transactions": group.to_dict(orient="records"),
        }
        rows.append(ordering_inversions_for_block(
            block, order_key=order_key, priority_key=priority_key, id_key=id_key,
        ))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Period summary
# ---------------------------------------------------------------------------

def _infer_era(period_name: str) -> str:
    return "pre_merge" if "PRE_MERGE" in period_name.upper() else "post_merge"


def _infer_volatility(period_name: str) -> str:
    return "stable" if "STABLE" in period_name.upper() else "high_volatility"


def period_summary(period_name: str, blocks: list[dict]) -> dict:
    """
    Aggregate all metrics for one period into a flat dict.

    Keys: period_name, era, volatility_type, num_blocks, num_transactions,
          gas_fee_mean, gas_fee_median, gas_fee_std, gas_fee_p25, gas_fee_p75,
          gas_fee_p95, gas_fee_p99,
          gini, top1_share, top3_share, unique_miners,
          mean_inversion_rate, median_inversion_rate, mean_inversion_count
    """
    stats = gas_fee_stats(blocks)
    conc = block_concentration(blocks)
    inv_df = ordering_inversions_per_block(blocks)

    mean_inv_rate = float(inv_df["inversion_rate"].mean()) if len(inv_df) else 0.0
    median_inv_rate = float(inv_df["inversion_rate"].median()) if len(inv_df) else 0.0
    mean_inv_count = float(inv_df["inversion_count"].mean()) if len(inv_df) else 0.0

    return {
        "period_name": period_name,
        "era": _infer_era(period_name),
        "volatility_type": _infer_volatility(period_name),
        "num_blocks": len(blocks),
        "num_transactions": stats["total_tx_count"],
        "gas_fee_mean": stats["mean"],
        "gas_fee_median": stats["median"],
        "gas_fee_std": stats["std"],
        "gas_fee_p25": stats["p25"],
        "gas_fee_p75": stats["p75"],
        "gas_fee_p95": stats["p95"],
        "gas_fee_p99": stats["p99"],
        "gini": conc["gini"],
        "top1_share": conc["top1_share"],
        "top3_share": conc["top3_share"],
        "unique_miners": conc["unique_miners"],
        "mean_inversion_rate": mean_inv_rate,
        "median_inversion_rate": median_inv_rate,
        "mean_inversion_count": mean_inv_count,
    }

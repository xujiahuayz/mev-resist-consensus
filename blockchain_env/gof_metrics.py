"""Goodness-of-fit metrics for comparing empirical and simulated distributions.

Used by plot scripts to quantify the real-vs-simulated overlay where the
comparison is non-tautological (e.g. inversion CDFs).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from scipy.stats import ks_2samp, wasserstein_distance
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


def ks_distance(sample_a: np.ndarray, sample_b: np.ndarray) -> float:
    """Two-sample Kolmogorov–Smirnov statistic.

    Falls back to a hand-rolled CDF supremum if scipy is unavailable.
    Returns NaN if either sample is empty.
    """
    a = np.asarray(sample_a, dtype=float)
    b = np.asarray(sample_b, dtype=float)
    if a.size == 0 or b.size == 0:
        return float("nan")
    if _HAS_SCIPY:
        return float(ks_2samp(a, b).statistic)
    grid = np.union1d(a, b)
    cdf_a = np.searchsorted(np.sort(a), grid, side="right") / a.size
    cdf_b = np.searchsorted(np.sort(b), grid, side="right") / b.size
    return float(np.max(np.abs(cdf_a - cdf_b)))


def wasserstein_1(sample_a: np.ndarray, sample_b: np.ndarray) -> float:
    """First-order Wasserstein (earth-mover) distance between two 1-D samples.

    Falls back to a sorted-difference approximation if scipy is unavailable.
    Returns NaN if either sample is empty.
    """
    a = np.asarray(sample_a, dtype=float)
    b = np.asarray(sample_b, dtype=float)
    if a.size == 0 or b.size == 0:
        return float("nan")
    if _HAS_SCIPY:
        return float(wasserstein_distance(a, b))
    # Quantile-matched approximation: average |Q_a(p) - Q_b(p)| on a fine grid.
    q = np.linspace(0.0, 1.0, max(a.size, b.size, 1024), endpoint=False) + 0.5 / max(a.size, b.size, 1024)
    qa = np.quantile(a, q)
    qb = np.quantile(b, q)
    return float(np.mean(np.abs(qa - qb)))


def per_period_gof_table(
    emp_df: pd.DataFrame,
    sim_df: pd.DataFrame,
    value_col: str,
    period_col: str = "period",
) -> pd.DataFrame:
    """Compute KS and Wasserstein-1 between emp and sim distributions per period.

    Returns a DataFrame with columns: period, n_emp, n_sim, ks, wasserstein_1.
    """
    periods = sorted(set(emp_df[period_col]) & set(sim_df[period_col]))
    rows = []
    for period in periods:
        a = emp_df.loc[emp_df[period_col] == period, value_col].dropna().to_numpy()
        b = sim_df.loc[sim_df[period_col] == period, value_col].dropna().to_numpy()
        rows.append({
            "period": period,
            "n_emp": int(a.size),
            "n_sim": int(b.size),
            "ks": ks_distance(a, b),
            "wasserstein_1": wasserstein_1(a, b),
        })
    return pd.DataFrame(rows)

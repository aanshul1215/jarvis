"""Risk estimates for portfolio construction, all point in time (row t uses returns up to and including row t).

- Per-asset daily volatility: the Phase 5 winner (GARCH(1,1), month-start refits on 1,000 returns) where it has
  enough history, otherwise RiskMetrics EWMA (0.94), which also passed the volatility study.
- Correlation: Ledoit-Wolf constant-correlation shrinkage of the last 126 daily returns (riskmodel.shrunk_cov).
"""

from __future__ import annotations

import math

import numpy as np

from ..riskmodel import shrunk_cov
from ..volatility import MODELS, walk_forward
from .panel import Panel

CORR_WINDOW = 126
MIN_HISTORY = 20


def vol_forecasts(panel: Panel, horizon: int = 5) -> np.ndarray:
    """(T, N) forecast daily volatility known at each row; NaN until 20 returns exist."""
    r_all = panel.returns()
    out = np.full(panel.shape, np.nan)
    for j in range(panel.shape[1]):
        valid = np.where(np.isfinite(r_all[:, j]))[0]
        if len(valid) < MIN_HISTORY + 1:
            continue
        rows = valid
        r = np.log1p(r_all[rows, j])
        dates = tuple(panel.dates[i] for i in rows)
        ewma = MODELS["ewma"].path(r, None, MIN_HISTORY, len(r), horizon, 0)
        variance = np.full(len(r), np.nan)
        variance[MIN_HISTORY:] = ewma
        first, garch = walk_forward(MODELS["garch"], r, dates, horizon)
        if len(garch):
            variance[first:first + len(garch)] = garch
        out[rows, j] = np.sqrt(variance)
    return out


def correlation(returns: np.ndarray, t: int, columns: np.ndarray, window: int = CORR_WINDOW) -> np.ndarray:
    """Shrunk correlation of ``columns`` from the ``window`` rows ending at row t (missing values treated as 0)."""
    block = returns[max(1, t - window + 1):t + 1][:, columns]
    block = np.where(np.isfinite(block), block, 0.0)
    if len(block) < 30 or len(columns) < 2:
        return np.eye(len(columns))
    cov, _ = shrunk_cov(block)
    sd = np.sqrt(np.clip(np.diag(cov), 1e-18, None))
    corr = cov / np.outer(sd, sd)
    np.fill_diagonal(corr, 1.0)
    return np.clip(corr, -1, 1)


def portfolio_vol(weights: np.ndarray, vols: np.ndarray, corr: np.ndarray) -> float:
    """Forecast daily volatility of a weight vector (fractions of capital)."""
    scaled = weights * vols
    return math.sqrt(max(0.0, float(scaled @ corr @ scaled)))

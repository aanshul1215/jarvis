"""Correlation and portfolio risk (Phase 5): do we know when several positions are really one bet?

Today the Governor caps each asset separately, which treats every position as an independent bet of its own size.
That is the baseline here: a diagonal covariance (each asset's own variance, zero correlation). Candidates
(pre-registered in docs/07-awareness/MODEL_REGISTER.md):

- ``sample``: the sample covariance of the last ``WINDOW`` aligned daily returns;
- ``shrunk``: Ledoit & Wolf (2004) shrinkage of that sample covariance toward a constant-correlation matrix, with
  their estimated optimal intensity (implemented here: scikit-learn's LedoitWolf uses a scaled identity instead).

Test: every ``STEP`` observations each estimator forecasts the daily variance of an equal-weight portfolio and of
``PORTFOLIOS`` seeded random long-only portfolios over the next ``STEP`` observations; forecasts are scored with
QLIKE against the realised mean squared portfolio return. Reported, not decisive: the realised volatility of the
long-only minimum-variance portfolio from each estimator against the equal-weight (1/N) portfolio.
"""

from __future__ import annotations

import math
from datetime import date

import numpy as np

from .metrics import diebold_mariano
from .volatility import ALPHA, DEVELOPMENT_END, HOLDOUT_START, PriceSeries, qlike

WINDOW, STEP, PORTFOLIOS = 252, 21, 50
BASELINE, CANDIDATES = "diagonal", ("sample", "shrunk")


def aligned_returns(series: list[PriceSeries]) -> tuple[list[date], np.ndarray, list[str]]:
    """Log returns between consecutive dates on which every asset has a close (crypto weekends are folded in)."""
    common = sorted(set.intersection(*(set(s.dates) for s in series)))
    columns = []
    for item in series:
        price = dict(zip(item.dates, np.asarray(item.closes, dtype=float)))
        columns.append(np.diff(np.log([price[d] for d in common])))
    return common[1:], np.column_stack(columns) if columns else np.empty((0, 0)), [s.asset for s in series]


def sample_cov(x: np.ndarray) -> np.ndarray:
    centred = x - x.mean(axis=0)
    return centred.T @ centred / len(x)


def shrunk_cov(x: np.ndarray) -> tuple[np.ndarray, float]:
    """Ledoit-Wolf constant-correlation shrinkage; returns (covariance, shrinkage intensity in [0, 1])."""
    t, n = x.shape
    centred = x - x.mean(axis=0)
    s = centred.T @ centred / t
    sd = np.sqrt(np.diag(s))
    if n < 2 or np.any(sd <= 0):
        return s, 0.0
    corr = s / np.outer(sd, sd)
    r_bar = (corr.sum() - n) / (n * (n - 1))
    target = r_bar * np.outer(sd, sd)
    np.fill_diagonal(target, np.diag(s))
    y = centred ** 2
    phi_mat = y.T @ y / t - s ** 2                                     # asymptotic variances of the entries of s
    phi = phi_mat.sum()
    term1 = (centred ** 3).T @ centred / t                            # E[x_i^3 x_j]
    theta = term1 - np.diag(s)[:, None] * s                           # theta[i, j] = cov(x_i^2, x_i x_j)
    # The paper's (r/2) * sum over i != j of [sqrt(s_jj/s_ii) theta_ii,ij + sqrt(s_ii/s_jj) theta_jj,ij]; the two
    # halves are the same sum with i and j swapped, as in the authors' covCor.m.
    rho_off = r_bar * np.outer(1 / sd, sd) * theta
    np.fill_diagonal(rho_off, 0.0)
    rho = np.trace(phi_mat) + rho_off.sum()
    gamma = float(np.sum((target - s) ** 2))
    intensity = 0.0 if gamma <= 0 else float(max(0.0, min(1.0, (phi - rho) / gamma / t)))
    return intensity * target + (1 - intensity) * s, intensity


def estimate(name: str, x: np.ndarray) -> np.ndarray:
    if name == "diagonal":
        return np.diag(np.diag(sample_cov(x)))
    if name == "sample":
        return sample_cov(x)
    if name == "shrunk":
        return shrunk_cov(x)[0]
    raise ValueError(f"unknown estimator {name}")


def min_variance_weights(cov: np.ndarray) -> np.ndarray:
    """Long-only, fully invested minimum-variance weights."""
    from scipy.optimize import minimize

    n = len(cov)
    scaled = cov / np.mean(np.diag(cov))  # daily variances are ~1e-4: rescale so the optimiser's tolerance bites
    result = minimize(lambda w: float(w @ scaled @ w), np.full(n, 1 / n), jac=lambda w: 2 * scaled @ w,
                      method="SLSQP", bounds=[(0, 1)] * n, constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
                      options={"maxiter": 500, "ftol": 1e-12})
    w = np.clip(result.x, 0, None)
    return w / w.sum() if w.sum() > 0 else np.full(n, 1 / n)


def random_portfolios(n_assets: int, count: int = PORTFOLIOS, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = np.zeros((count, n_assets))
    for k in range(count):
        size = int(rng.integers(2, min(8, n_assets) + 1))
        chosen = rng.choice(n_assets, size=size, replace=False)
        out[k, chosen] = rng.dirichlet(np.ones(size))
    return out


def compare(series: list[PriceSeries], *, split: str = "DEVELOPMENT", seed: int = 0) -> dict:
    """Pre-registered pass rule: a candidate passes if the one-sided Diebold-Mariano p-value of its mean QLIKE gain
    over the diagonal baseline, across evaluation periods, is below 0.05 / 2. The winner is the passing candidate
    with the larger gain; otherwise the baseline stays."""
    if len(series) < 2:
        raise ValueError("a correlation study needs at least two assets")
    days, x, assets = aligned_returns(series)
    n = x.shape[1]
    weights = np.vstack([np.full((1, n), 1 / n), random_portfolios(n, seed=seed)])
    names = (BASELINE, *CANDIDATES)
    losses = {m: [] for m in names}
    min_var = {m: [] for m in names}
    equal_weight, period_starts, intensities = [], [], []
    for origin in range(WINDOW, len(x) - STEP + 1, STEP):
        start, end = days[origin], days[origin + STEP - 1]
        if (split == "DEVELOPMENT" and end > DEVELOPMENT_END) or (split == "HOLDOUT" and start < HOLDOUT_START):
            continue
        past, future = x[origin - WINDOW:origin], x[origin:origin + STEP]
        realised = np.mean((future @ weights.T) ** 2, axis=0)
        for m in names:
            cov = estimate(m, past)
            forecast = np.einsum("ki,ij,kj->k", weights, cov, weights)
            losses[m].append(float(np.mean(qlike(realised, forecast))))
            min_var[m].append(future @ min_variance_weights(cov))
        equal_weight.append(future @ np.full(n, 1 / n))
        intensities.append(shrunk_cov(past)[1])
        period_starts.append(start.isoformat())
    if not period_starts:
        return {"split": split, "periods": 0, "note": "not enough aligned history", "winner": BASELINE}
    tests, passing = {}, []
    threshold = ALPHA / len(CANDIDATES)
    for m in CANDIDATES:
        test = diebold_mariano(np.asarray(losses[BASELINE]) - np.asarray(losses[m]), 1)
        tests[m] = {**test, "passed": bool(test["p_value"] < threshold)}
        if tests[m]["passed"]:
            passing.append((test["mean"], m))

    def annual_vol(chunks: list[np.ndarray]) -> float:
        return float(np.std(np.concatenate(chunks)) * math.sqrt(252))

    return {"split": split, "assets": assets, "periods": len(period_starts), "first_period": period_starts[0],
            "last_period": period_starts[-1], "p_threshold": threshold,
            "mean_qlike": {m: float(np.mean(v)) for m, v in losses.items()}, "versus_baseline": tests,
            "mean_shrinkage_intensity": float(np.mean(intensities)),
            "realised_annual_vol": {"equal_weight": annual_vol(equal_weight),
                                    **{f"min_variance_{m}": annual_vol(v) for m, v in min_var.items()}},
            "winner": max(passing)[1] if passing else BASELINE}


def portfolio_volatility(notionals: dict[str, float], returns: dict[str, np.ndarray], estimator: str = "shrunk") -> dict:
    """Forecast daily dollar volatility of the open book, and the same with correlations ignored.

    ``returns`` holds each asset's recent aligned daily log returns (same length). The ratio of the two numbers is
    a crowding measure: near 1 the positions diversify each other, near sqrt(n) they behave as one bet.
    """
    held = [a for a, v in notionals.items() if v and a in returns]
    if not held:
        return {"assets": [], "daily_vol": 0.0, "independent_daily_vol": 0.0, "crowding": None}
    x = np.column_stack([returns[a] for a in held])
    cov = estimate(estimator, x) if len(held) > 1 else sample_cov(x)
    w = np.asarray([notionals[a] for a in held], dtype=float)
    total = math.sqrt(max(0.0, float(w @ cov @ w)))
    independent = math.sqrt(float(np.sum(w ** 2 * np.diag(cov))))
    return {"assets": held, "daily_vol": total, "independent_daily_vol": independent,
            "crowding": total / independent if independent > 0 else None}

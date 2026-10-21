"""Fast, honest simulation of a target-weight portfolio (research path).

Weights decided at row t (after its close) are traded at row t + 1's open and held to row t + 2's open, so the
return earned for decision t is open[t+2] / open[t+1] - 1. Costs: per-side spread and fee on every change in
weight (``Panel.cost_bps``), and a borrow fee on short positions. Between trades, weights drift with prices; a
no-trade band skips changes too small to be worth their cost (the same rule the executor uses): round 3 skips a
change smaller than 1% of capital or 20% of the target position, whichever is larger.

The paper desk computes the same weights with the same functions and trades them through the broker; a replay of
the executor checks that the two paths agree.
"""

from __future__ import annotations

import math
from datetime import date

import numpy as np

from .panel import BORROW_BPS_PER_YEAR, Panel

BAND = 0.01       # skip a trade when the weight change is under 1% of capital (about $100 on $10,000) ...
BAND_REL = 0.20   # ... or under 20% of the target position (round 3: drift is tolerated, churn is not)


def apply_band(target: np.ndarray, current: np.ndarray, band: float = BAND, relative: float = BAND_REL) -> np.ndarray:
    """Keep the current weight where the change is below the band; always allow closing a position fully."""
    change = np.abs(target - current)
    keep = (change < np.maximum(band, relative * np.abs(target))) & (target != 0)
    return np.where(keep, current, target)


def simulate(panel: Panel, weights: np.ndarray, *, start: int = 0, end: int | None = None,
             cost_multiplier: float = 1.0, band: float = BAND, relative: float = BAND_REL,
             rebalance_rows: set[int] | None = None) -> dict:
    """Daily returns of trading ``weights`` (T, N) between rows ``start`` and ``end``.

    Returns {"dates", "returns", "turnover", "gross", "net", "short"} where dates[k] is the day the return was earned
    (the holding day, row t + 1) and the exposures are the weights actually held after the band. With
    ``rebalance_rows``, trades happen only on those rows (and on the first row); positions drift in between.
    """
    t_total, n = panel.shape
    end = t_total - 2 if end is None else min(end, t_total - 2)
    opens = panel.open
    cost = panel.cost_bps() / 10_000 * cost_multiplier
    borrow = BORROW_BPS_PER_YEAR / 10_000 / 252
    held = np.zeros(n)
    dates, rets, turnover, gross, net, short = [], [], [], [], [], []
    for t in range(start, end):
        target = np.nan_to_num(weights[t], nan=0.0)
        if rebalance_rows is not None and t not in rebalance_rows and held.any():
            target = held
        tradable = np.isfinite(opens[t + 1])
        target = np.where(tradable, target, held)  # no price to trade at: keep the position as it is
        new = apply_band(target, held, band, relative)
        traded = np.abs(new - held)
        priced = tradable & np.isfinite(opens[t + 2])
        move = np.where(priced, opens[t + 2] / np.where(priced, opens[t + 1], 1.0) - 1, 0.0)
        r = float(new @ move) - float(traded @ cost) - float(np.clip(-new, 0, None).sum() * borrow)
        # Weights drift with prices until the next decision.
        value = 1 + float(new @ move)
        held = new * (1 + move) / value if value > 0 else np.zeros(n)
        dates.append(panel.dates[t + 1])
        rets.append(r)
        turnover.append(float(traded.sum()))
        gross.append(float(np.abs(new).sum()))
        net.append(float(new.sum()))
        short.append(float(np.clip(-new, 0, None).sum()))
    return {"dates": dates, "returns": np.array(rets), "turnover": np.array(turnover), "gross": np.array(gross),
            "net": np.array(net), "short": np.array(short)}


def stats(dates: list[date], returns: np.ndarray) -> dict:
    """Annualised summary of a daily return series."""
    if len(returns) < 2:
        return {"days": len(returns)}
    equity = np.cumprod(1 + returns)
    years = max((dates[-1] - dates[0]).days / 365.25, 1e-9)
    sd = float(np.std(returns, ddof=1))
    drawdown = equity / np.maximum.accumulate(np.maximum(equity, 1.0)) - 1
    downside = returns[returns < 0]
    cagr = float(equity[-1] ** (1 / years) - 1) if equity[-1] > 0 else -1.0
    return {"start": dates[0].isoformat(), "end": dates[-1].isoformat(), "days": len(returns),
            "total_return": float(equity[-1] - 1), "cagr": cagr, "annual_vol": sd * math.sqrt(252),
            "sharpe": float(np.mean(returns) / sd * math.sqrt(252)) if sd > 0 else None,
            "sortino": float(np.mean(returns) / np.std(downside, ddof=1) * math.sqrt(252)) if len(downside) > 1 else None,
            "max_drawdown": float(drawdown.min()), "calmar": cagr / -float(drawdown.min()) if drawdown.min() < 0 else None,
            "worst_day": float(returns.min()), "best_day": float(returns.max())}

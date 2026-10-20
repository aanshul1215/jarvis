"""Performance metrics on daily equity series. Returns are after all modelled costs."""

from __future__ import annotations

import math
from datetime import date, datetime

import numpy as np

from .timeframes import NEW_YORK


def daily_series(points: list[tuple[datetime, float]]) -> list[tuple[date, float]]:
    """Last value of each New York calendar day."""
    by_day: dict[date, float] = {}
    for when, value in sorted(points):
        by_day[when.astimezone(NEW_YORK).date()] = value
    return sorted(by_day.items())


def daily_returns(series: list[tuple[date, float]]) -> np.ndarray:
    values = np.asarray([v for _, v in series], dtype=float)
    return values[1:] / values[:-1] - 1 if len(values) > 1 else np.asarray([])


def periods_per_year(series: list[tuple[date, float]]) -> float:
    if len(series) < 2:
        return 252.0
    years = (series[-1][0] - series[0][0]).days / 365.25
    return (len(series) - 1) / years if years > 0 else 252.0


def summarize(series: list[tuple[date, float]]) -> dict:
    if len(series) < 2:
        return {"days": len(series)}
    r = daily_returns(series)
    per_year = periods_per_year(series)
    years = (series[-1][0] - series[0][0]).days / 365.25
    total = series[-1][1] / series[0][1] - 1
    values = np.asarray([v for _, v in series])
    drawdown = values / np.maximum.accumulate(values) - 1
    worst = np.sort(r)[:max(1, math.ceil(len(r) * 0.05))]
    std = float(np.std(r, ddof=1)) if len(r) > 1 else 0.0
    downside = r[r < 0]
    return {
        "start": series[0][0].isoformat(), "end": series[-1][0].isoformat(), "days": len(series),
        "total_return": float(total),
        "cagr": float((1 + total) ** (1 / years) - 1) if years > 0 and total > -1 else None,
        "annual_volatility": std * math.sqrt(per_year),
        "sharpe": float(np.mean(r) / std * math.sqrt(per_year)) if std > 0 else None,
        "sortino": float(np.mean(r) / np.std(downside, ddof=1) * math.sqrt(per_year)) if len(downside) > 1 else None,
        "max_drawdown": float(drawdown.min()),
        "expected_shortfall_5pct_daily": float(worst.mean()),
        "best_day": float(r.max()), "worst_day": float(r.min()),
    }


def trade_stats(outcomes: list[dict]) -> dict:
    pnls = [float(o["gross_pnl_estimate"]) for o in outcomes]
    wins, losses = [p for p in pnls if p > 0], [p for p in pnls if p <= 0]
    return {"trades": len(pnls), "win_rate": len(wins) / len(pnls) if pnls else None,
            "average_win": float(np.mean(wins)) if wins else None,
            "average_loss": float(np.mean(losses)) if losses else None,
            "profit_factor": (sum(wins) / -sum(losses)) if losses and sum(losses) < 0 else None,
            "gross_pnl": float(sum(pnls)), "note": "trade P&L is gross; the equity curve includes all costs"}


def block_bootstrap_pvalue(excess: np.ndarray, *, block: int = 20, resamples: int = 2000, seed: int = 0) -> float:
    """One-sided p-value for 'mean excess return > 0' using a circular block bootstrap under the null.

    Daily returns are autocorrelated and fat-tailed, so resampling blocks of consecutive days keeps that structure.
    """
    n = len(excess)
    if n < 2 * block:
        return 1.0
    observed = float(np.mean(excess))
    centred = excess - observed
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n, size=(resamples, math.ceil(n / block)))
    index = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(resamples, -1)[:, :n] % n
    means = centred[index].mean(axis=1)
    return float((np.sum(means >= observed) + 1) / (resamples + 1))

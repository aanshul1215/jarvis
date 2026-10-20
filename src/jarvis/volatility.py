"""Volatility forecasting (Phase 5): candidate models, an honest walk-forward comparison, and position sizing.

Every forecaster answers one question at a forecast origin t: what will the average daily variance of log returns
be over the next ``h`` observations, using only returns up to and including t?

Models (pre-registered in docs/07-awareness/MODEL_REGISTER.md):
- ``rolling20`` (baseline): mean squared return over the last 20 observations, the "simple moving average of
  recent volatility" the workflow names as the bar to beat.
- ``ewma``: RiskMetrics exponentially weighted variance, decay 0.94 (J.P. Morgan 1996).
- ``har``: HAR model in variance levels (Corsi 2009 structure: last day, 5-day and 22-day averages), fitted by OLS
  directly for each horizon. Squared daily returns stand in for intraday realised variance, which the free data
  does not provide. A non-positive forecast falls back to the 22-day average.
- ``garch``: GARCH(1,1) with zero mean, fitted by maximum likelihood.

Fitted models use a rolling window of the last ``WINDOW`` returns and are refitted at each calendar-month boundary,
using only returns before the first observation of the month. The study and the live sizing code call the same
functions, so what is evaluated is exactly what trades.

Forecasts are compared with QLIKE (Patton 2011: robust to the noise in squared returns as a variance proxy), with a
Diebold-Mariano test on the loss differences.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np

from .contracts import AssetClass, Bar
from .metrics import diebold_mariano
from .timeframes import NEW_YORK

WINDOW = 1000                 # returns in each fitting window (about four years of stock sessions)
HORIZONS = (1, 5, 21)
PRIMARY_HORIZON = 5           # the horizon that decides the comparison and drives sizing
ALPHA = 0.05
DEVELOPMENT_END, HOLDOUT_START = date(2023, 12, 31), date(2024, 1, 1)
TARGET_DAILY_VOL, MAX_SCALE = 0.01, 1.5  # sizing: 1% daily (~16%/year) risk per position at the base notional
# History a fitted model needs at decision time: WINDOW returns before the current month started, plus that month.
HISTORY_BARS = WINDOW + 60
HISTORY_DAYS = {AssetClass.EQUITY: 1600, AssetClass.CRYPTO: 1100}


@dataclass(frozen=True)
class PriceSeries:
    asset: str
    group: str                 # "EQUITY" or "CRYPTO": the pass rule needs the model to help in both
    dates: tuple[date, ...]    # date of each close
    closes: np.ndarray

    def returns(self) -> tuple[np.ndarray, tuple[date, ...]]:
        """Log returns and the date each one became known (the date of its closing price)."""
        closes = np.asarray(self.closes, dtype=float)
        return np.diff(np.log(closes)), tuple(self.dates[1:])


def bar_returns(bars: list[Bar]) -> tuple[np.ndarray, tuple[date, ...], np.ndarray]:
    """Log returns of daily bars, the trading date of each, and the closes (stocks: New York session date; crypto:
    the UTC day the bar starts)."""
    def day(bar: Bar) -> date:
        tz = NEW_YORK if bar.asset_class == AssetClass.EQUITY else None
        return bar.start_at.astimezone(tz).date() if tz else bar.start_at.date()

    closes = np.asarray([b.close for b in bars], dtype=float)
    return np.diff(np.log(closes)), tuple(day(b) for b in bars[1:]), closes


def month_starts(dates: tuple[date, ...] | list[date]) -> list[int]:
    """Indices of the first observation of each calendar month (the refit points)."""
    return [i for i in range(1, len(dates)) if (dates[i].year, dates[i].month) != (dates[i - 1].year, dates[i - 1].month)]


class Forecaster:
    name = "base"
    fitted = False

    def fit(self, window: np.ndarray, horizon: int) -> Any:
        return None

    def path(self, r: np.ndarray, params: Any, start: int, stop: int, horizon: int, fit_start: int) -> np.ndarray:
        """Forecasts at origins ``start``..``stop - 1``; the one at t may use only ``r[: t + 1]``."""
        raise NotImplementedError


class RollingMean(Forecaster):
    name = "rolling20"

    def __init__(self, length: int = 20):
        self.length = length

    def path(self, r, params, start, stop, horizon, fit_start):
        cumulative = np.concatenate([[0.0], np.cumsum(r[:stop] ** 2)])
        origins = np.arange(start, stop)
        return (cumulative[origins + 1] - cumulative[origins + 1 - self.length]) / self.length


class Ewma(Forecaster):
    name = "ewma"

    def __init__(self, decay: float = 0.94):
        self.decay = decay

    def path(self, r, params, start, stop, horizon, fit_start):
        from scipy.signal import lfilter

        begin = max(0, start - WINDOW)  # 0.94**1000 is negligible: the result does not depend on older data
        seed = float(np.mean(r[begin:begin + 20] ** 2))
        x = (1 - self.decay) * r[begin:stop] ** 2
        s, _ = lfilter([1.0], [1.0, -self.decay], x, zi=[self.decay * seed])
        return s[start - begin:]


def _har_design(r2: np.ndarray, origins: np.ndarray) -> np.ndarray:
    cumulative = np.concatenate([[0.0], np.cumsum(r2)])
    weekly = (cumulative[origins + 1] - cumulative[origins - 4]) / 5
    monthly = (cumulative[origins + 1] - cumulative[origins - 21]) / 22
    return np.column_stack([np.ones(len(origins)), r2[origins], weekly, monthly])


class Har(Forecaster):
    name = "har"
    fitted = True

    def fit(self, window, horizon):
        r2 = window ** 2
        origins = np.arange(21, len(window) - horizon)
        cumulative = np.concatenate([[0.0], np.cumsum(r2)])
        target = (cumulative[origins + 1 + horizon] - cumulative[origins + 1]) / horizon
        beta, *_ = np.linalg.lstsq(_har_design(r2, origins), target, rcond=None)
        return beta

    def path(self, r, params, start, stop, horizon, fit_start):
        design = _har_design(r[:stop] ** 2, np.arange(start, stop))
        forecast = design @ params
        return np.where(forecast > 0, forecast, design[:, 3])


class Garch(Forecaster):
    name = "garch"
    fitted = True
    SCALE = 100.0  # fit on percent returns for numerical stability

    @staticmethod
    def _filter(r: np.ndarray, omega: float, alpha: float, beta: float, initial: float) -> np.ndarray:
        """sigma2[i] = variance predicted for r[i]; sigma2[0] = initial, then the GARCH(1,1) recursion."""
        from scipy.signal import lfilter

        following, _ = lfilter([1.0], [1.0, -beta], omega + alpha * r ** 2, zi=[beta * initial])
        return np.concatenate([[initial], following])  # length len(r) + 1: the last is the next-step forecast

    def fit(self, window, horizon):
        from scipy.optimize import minimize

        x = window * self.SCALE
        variance = float(np.var(x))

        def loss(theta):
            omega, alpha, beta = theta
            sigma2 = self._filter(x, omega, alpha, beta, variance)[:-1]
            if not np.all(np.isfinite(sigma2)) or np.any(sigma2 <= 0):
                return 1e12
            return 0.5 * float(np.sum(np.log(sigma2) + x ** 2 / sigma2))

        start = np.array([0.02 * variance, 0.08, 0.90])
        result = minimize(loss, start, method="SLSQP",
                          bounds=[(1e-6 * variance, variance), (0.0, 0.5), (0.0, 0.9999)],
                          constraints=[{"type": "ineq", "fun": lambda t: 0.9999 - t[1] - t[2]}],
                          options={"maxiter": 200, "ftol": 1e-10})
        theta = result.x if np.all(np.isfinite(result.x)) and loss(result.x) <= loss(start) else start
        return {"omega": float(theta[0]), "alpha": float(theta[1]), "beta": float(theta[2]),
                "initial": variance, "converged": bool(result.success)}

    def path(self, r, params, start, stop, horizon, fit_start):
        x = r[fit_start:stop] * self.SCALE
        sigma2 = self._filter(x, params["omega"], params["alpha"], params["beta"], params["initial"])
        nxt = sigma2[start - fit_start + 1:]  # forecast for t + 1 made at origin t
        persistence = params["alpha"] + params["beta"]
        if persistence < 1:
            long_run = params["omega"] / (1 - persistence)
            factor = (1 - persistence ** horizon) / ((1 - persistence) * horizon)
            nxt = long_run + (nxt - long_run) * factor
        return nxt / self.SCALE ** 2


MODELS = {m.name: m for m in (RollingMean(), Ewma(), Har(), Garch())}
BASELINE = "rolling20"
CANDIDATES = ("ewma", "har", "garch")


def forecast_block(model: Forecaster, r: np.ndarray, refit: int, stop: int, horizon: int,
                   window: int = WINDOW) -> np.ndarray:
    """Forecasts for origins ``refit``..``stop - 1`` with parameters fitted on the ``window`` returns before ``refit``."""
    fit_start = refit - window
    if fit_start < 0:
        raise ValueError("not enough history for the fitting window")
    params = model.fit(r[fit_start:refit], horizon) if model.fitted else None
    return model.path(r, params, refit, stop, horizon, fit_start)


def walk_forward(model: Forecaster, r: np.ndarray, dates: tuple[date, ...], horizon: int,
                 window: int = WINDOW) -> tuple[int, np.ndarray]:
    """(first origin, forecasts for every origin from it to the end), refitting at each month boundary."""
    refits = [i for i in month_starts(dates) if i >= window]
    if not refits:
        return len(r), np.asarray([])
    bounds = refits + [len(r)]
    blocks = [forecast_block(model, r, a, b, horizon, window) for a, b in zip(bounds[:-1], bounds[1:])]
    return refits[0], np.concatenate(blocks)


def qlike(proxy: np.ndarray, forecast: np.ndarray) -> np.ndarray:
    """Patton's QLIKE in the form proxy/forecast + log(forecast); lower is better."""
    return proxy / forecast + np.log(forecast)


def _targets(r: np.ndarray, first: int, horizon: int) -> np.ndarray:
    r2 = r ** 2
    cumulative = np.concatenate([[0.0], np.cumsum(r2)])
    origins = np.arange(first, len(r) - horizon)
    return (cumulative[origins + 1 + horizon] - cumulative[origins + 1]) / horizon


def _in_split(dates: tuple[date, ...], origin: int, horizon: int, split: str) -> bool:
    if split == "DEVELOPMENT":
        return dates[origin + horizon] <= DEVELOPMENT_END
    if split == "HOLDOUT":
        return dates[origin] >= HOLDOUT_START
    raise ValueError(f"unknown split {split}")


def compare(series: list[PriceSeries], *, horizon: int = PRIMARY_HORIZON, split: str = "DEVELOPMENT",
            window: int = WINDOW, models: tuple[str, ...] = (BASELINE, *CANDIDATES)) -> dict:
    """Walk-forward comparison of every model against the baseline, per asset and pooled across assets.

    Pre-registered pass rule for a candidate: in every asset group (stocks, crypto) present, the one-sided
    Diebold-Mariano p-value of the QLIKE improvement over the baseline, averaged across that group's assets per date,
    is below 0.05 / (number of candidates) and the mean improvement is positive. Groups are tested separately because
    their calendars differ. The winner is the passing candidate with the largest mean improvement (averaged over
    groups); if none passes, the baseline is used.
    """
    candidates = [m for m in models if m != BASELINE]
    threshold = ALPHA / max(1, len(candidates))
    per_asset, pooled = {}, {m: {} for m in candidates}
    for item in series:
        r, dates = item.returns()
        forecasts = {}
        first = None
        for name in models:
            start, values = walk_forward(MODELS[name], r, dates, horizon, window)
            first = start if first is None else first
            forecasts[name] = values
        if first is None or first >= len(r) - horizon:
            per_asset[item.asset] = {"group": item.group, "origins": 0, "note": "not enough history"}
            continue
        target = _targets(r, first, horizon)
        keep = np.array([_in_split(dates, t, horizon, split) for t in range(first, len(r) - horizon)], dtype=bool)
        if not keep.any():
            per_asset[item.asset] = {"group": item.group, "origins": 0, "note": "no origins in this split"}
            continue
        origin_dates = [dates[t] for t in range(first, len(r) - horizon)]
        losses = {name: qlike(target, forecasts[name][:len(target)])[keep] for name in models}
        mse = {name: float(np.mean((target - forecasts[name][:len(target)])[keep] ** 2)) for name in models}
        kept_dates = [d for d, k in zip(origin_dates, keep) if k]
        row = {"group": item.group, "origins": int(keep.sum()), "first_origin": kept_dates[0].isoformat(),
               "last_origin": kept_dates[-1].isoformat(),
               "mean_qlike": {name: float(np.mean(v)) for name, v in losses.items()}, "mse": mse, "versus_baseline": {}}
        for name in candidates:
            d = losses[BASELINE] - losses[name]
            row["versus_baseline"][name] = diebold_mariano(d, horizon)
            for day, value in zip(kept_dates, d):
                pooled[name].setdefault(item.group, {}).setdefault(day, []).append(float(value))
        per_asset[item.asset] = row
    summary, passing = {}, []
    for name in candidates:
        tests = {g: diebold_mariano(np.asarray([np.mean(v[d]) for d in sorted(v)]), horizon)
                 for g, v in pooled[name].items()}
        passed = bool(tests and all(t["p_value"] < threshold and t["mean"] > 0 for t in tests.values()))
        gain = float(np.mean([t["mean"] for t in tests.values()])) if tests else 0.0
        summary[name] = {"by_group": tests, "mean_improvement": gain, "passed": passed}
        if passed:
            passing.append((gain, name))
    winner = max(passing)[1] if passing else BASELINE
    return {"horizon": horizon, "split": split, "window": window, "p_threshold": threshold, "baseline": BASELINE,
            "per_asset": per_asset, "candidates": summary, "winner": winner}


def forecast_now(model_name: str, r: np.ndarray, dates: tuple[date, ...], horizon: int = PRIMARY_HORIZON,
                 window: int = WINDOW, cache: dict | None = None) -> float | None:
    """Average daily variance forecast at the latest return, exactly as the walk-forward study computes it.

    Fitted models use the parameters fitted at the start of the current month; ``cache`` keeps them between calls.
    Returns None when the history is too short for the model.
    """
    model = MODELS[model_name]
    t = len(r) - 1
    if t < 21:
        return None
    if not model.fitted:
        return float(model.path(r, None, t, t + 1, horizon, max(0, t - window))[0])
    starts = [i for i in month_starts(dates) if i <= t]
    if not starts or starts[-1] < window:
        return None
    refit = starts[-1]
    key = (model_name, horizon, dates[refit], hashlib.sha256(r[refit - window:refit].tobytes()).hexdigest())
    if cache is not None and key in cache:
        params = cache[key]
    else:
        params = model.fit(r[refit - window:refit], horizon)
        if cache is not None:
            cache[key] = params
    return float(model.path(r, params, t, t + 1, horizon, refit - window)[0])


def scaled_notional(base_notional: float, forecast_daily_vol: float | None, *, target: float = TARGET_DAILY_VOL,
                    max_scale: float = MAX_SCALE) -> float | None:
    """Volatility-targeted order size: the base notional when the forecast equals the target, less when riskier.

    Returns None without a usable forecast, so the caller blocks the entry instead of guessing a size.
    """
    if forecast_daily_vol is None or not math.isfinite(forecast_daily_vol) or forecast_daily_vol <= 0:
        return None
    return base_notional * min(max_scale, target / forecast_daily_vol)

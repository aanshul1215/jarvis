"""The allocator: how much of each sleeve to run in the current situation, then the risk overlay.

Blend methods (each a logged trial in the development study; the register fixes them in advance):
- ``equal``: every sleeve the same share.
- ``recent``: sleeves weighted by their last six months' return per unit of variance (strategy momentum).
- ``regime``: by each sleeve's past return per unit of variance in the current plain-language regime.
- ``situational``: a ridge regression per sleeve learns, from the twelve situation features, the sleeve's return
  over the next month; sleeves are weighted by predicted return per unit of variance.
All except ``equal`` keep half of the weight on equal shares (estimation errors are large; this is the main guard
against chasing noise) and may leave the other half in cash when nothing looks good. Weights are refitted at each
month start using only rows before it, and need two years of history (before that: equal).

Risk overlay, applied every day to the blended weights:
1. scale the blend to ``TARGET_VOL`` annual volatility (shrunk correlation, GARCH/EWMA volatilities), times the
   share the blend keeps invested;
2. caps: gross exposure 1.5, any one asset 30% of capital, crypto 20% in total, shorts 30% in total;
3. drawdown control: full size below a 10% drawdown, falling linearly to a quarter of size at 20%, kept at a
   quarter beyond (the owner's 25% limit is also a hard stop in the live Governor).
"""

from __future__ import annotations

import math
from datetime import date

import numpy as np

from .backtest import BAND, apply_band
from .panel import BORROW_BPS_PER_YEAR, Panel
from .risk import correlation, portfolio_vol

TARGET_VOL, GROSS_CAP, ASSET_CAP, CRYPTO_CAP, SHORT_CAP = 0.15, 1.5, 0.30, 0.20, 0.30
DD_START, DD_FLOOR_AT, DD_FLOOR = 0.10, 0.20, 0.25
SHRINK, HORIZON, MIN_TRAIN_ROWS, RECENT_WINDOW, MIN_REGIME_ROWS = 0.5, 21, 504, 126, 60
METHODS = ("equal", "recent", "regime", "situational")


def month_starts(dates: list[date]) -> list[int]:
    return [i for i in range(1, len(dates)) if (dates[i].year, dates[i].month) != (dates[i - 1].year, dates[i - 1].month)]


def _score_to_blend(score: np.ndarray) -> np.ndarray:
    s = len(score)
    positive = np.clip(np.nan_to_num(score), 0, None)
    model = positive / positive.sum() if positive.sum() > 0 else np.zeros(s)
    return SHRINK * np.full(s, 1 / s) + (1 - SHRINK) * model


def blend_schedule(method: str, sleeve_returns: np.ndarray, features: np.ndarray, labels: list[str],
                   dates: list[date]) -> np.ndarray:
    """(T, S) blend weights per row. ``sleeve_returns[t]`` is what each sleeve earned from row t's open to row
    t + 1's open, so it is complete only at row t + 1's open: the weights set at a month-start row m (after its
    close) use rows up to m - 1 only, and hold until the next month start."""
    t_total, s = sleeve_returns.shape
    out = np.full((t_total, s), 1 / s)
    if method == "equal":
        return out
    if method not in METHODS:
        raise ValueError(f"unknown blend method {method}")
    r = np.nan_to_num(sleeve_returns)
    refits = set(month_starts(dates))
    current = np.full(s, 1 / s)
    for m in range(t_total):
        if m in refits and m >= MIN_TRAIN_ROWS:
            if method == "recent":
                window = r[m - RECENT_WINDOW:m]
                var = window.var(axis=0)
                current = _score_to_blend(np.where(var > 0, window.mean(axis=0) / var, 0.0))
            elif method == "regime":
                same = [i for i in range(1, m) if labels[i] == labels[m]]
                if len(same) >= MIN_REGIME_ROWS:
                    window = r[same]
                    var = window.var(axis=0)
                    current = _score_to_blend(np.where(var > 0, window.mean(axis=0) / var, 0.0))
            else:
                current = _situational(r, features, m)
        out[m] = current
    return out


def _situational(r: np.ndarray, x: np.ndarray, m: int) -> np.ndarray:
    from sklearn.linear_model import Ridge

    s = r.shape[1]
    last = m - 1 - HORIZON  # the last training row whose 21-day target (rows t+1..t+21) ends by row m - 1
    if last < 252:
        return np.full(s, 1 / s)
    growth = np.vstack([np.prod(1 + r[t + 1:t + 1 + HORIZON], axis=0) - 1 for t in range(252, last + 1)])
    inputs = x[252:last + 1]
    variance = r[max(1, m - RECENT_WINDOW):m].var(axis=0) * HORIZON
    score = np.zeros(s)
    for k in range(s):
        model = Ridge(alpha=float(len(inputs))).fit(inputs, growth[:, k])
        predicted = float(model.predict(x[m:m + 1])[0])
        score[k] = predicted / variance[k] if variance[k] > 0 else 0.0
    return _score_to_blend(score)


def overlay(blended: np.ndarray, invested: float, t: int, panel: Panel, vols: np.ndarray, returns: np.ndarray,
            drawdown: float) -> np.ndarray:
    """Final target weights for row t from the blended sleeve weights (see the module docstring)."""
    w = np.nan_to_num(blended).copy()
    live = np.where((w != 0) & np.isfinite(vols[t]) & (vols[t] > 0))[0]
    if not len(live):
        return np.zeros_like(w)
    w = np.where(np.isfinite(vols[t]), w, 0.0)
    vol = portfolio_vol(w[live], vols[t, live], correlation(returns, t, live))
    if vol <= 0:
        return np.zeros_like(w)
    w = w * (TARGET_VOL / math.sqrt(252) / vol) * invested
    gross = np.abs(w).sum()
    if gross > GROSS_CAP:
        w *= GROSS_CAP / gross
    w = np.clip(w, -ASSET_CAP, ASSET_CAP)
    crypto = np.array([c.value == "CRYPTO" for c in panel.classes])
    crypto_long = w[crypto & (w > 0)].sum()
    if crypto_long > CRYPTO_CAP:
        w[crypto & (w > 0)] *= CRYPTO_CAP / crypto_long
    shorts = -w[w < 0].sum()
    if shorts > SHORT_CAP:
        w[w < 0] *= SHORT_CAP / shorts
    if drawdown >= DD_START:
        cut = min(1.0, (drawdown - DD_START) / (DD_FLOOR_AT - DD_START))
        w *= 1 - cut * (1 - DD_FLOOR)
    return w


def run_portfolio(panel: Panel, sleeve_weights: list[np.ndarray], blend: np.ndarray, vols: np.ndarray,
                  returns: np.ndarray, *, start: int, end: int | None = None, cost_multiplier: float = 1.0) -> dict:
    """Simulate the whole system day by day (decision at row t, traded at row t + 1's open), including the
    drawdown control, which needs the system's own equity so far."""
    t_total, n = panel.shape
    end = t_total - 2 if end is None else min(end, t_total - 2)
    stack = np.stack([np.nan_to_num(w) for w in sleeve_weights])  # (S, T, N)
    cost = panel.cost_bps() / 10_000 * cost_multiplier
    borrow = BORROW_BPS_PER_YEAR / 10_000 / 252
    held = np.zeros(n)
    equity, peak = 1.0, 1.0
    out = {"dates": [], "returns": [], "turnover": [], "gross": [], "net": [], "short": [], "drawdown": [], "weights": {}}
    for t in range(start, end):
        b = blend[t]
        invested = float(b.sum())
        mix = np.tensordot(b / invested if invested > 0 else b, stack[:, t, :], axes=1)
        target = overlay(mix, invested, t, panel, vols, returns, 1 - equity / peak)
        tradable = np.isfinite(panel.open[t + 1]) & np.isfinite(panel.open[t + 2])
        target = np.where(tradable, target, np.where(np.isfinite(panel.open[t + 1]), 0.0, held))
        new = apply_band(target, held, BAND)
        traded = np.abs(new - held)
        move = np.where(tradable, panel.open[t + 2] / panel.open[t + 1] - 1, 0.0)
        r = float(new @ move) - float(traded @ cost) - float(np.clip(-new, 0, None).sum() * borrow)
        value = 1 + float(new @ move)
        held = new * (1 + move) / value if value > 0 else np.zeros(n)
        equity *= 1 + r
        peak = max(peak, equity)
        out["dates"].append(panel.dates[t + 1])
        out["returns"].append(r)
        out["turnover"].append(float(traded.sum()))
        out["gross"].append(float(np.abs(new).sum()))
        out["net"].append(float(new.sum()))
        out["short"].append(float(np.clip(-new, 0, None).sum()))
        out["drawdown"].append(1 - equity / peak)
        out["weights"][panel.dates[t]] = new
    for key in ("returns", "turnover", "gross", "net", "short", "drawdown"):
        out[key] = np.array(out[key])
    return out

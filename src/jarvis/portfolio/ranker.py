"""The learning ranker (round 2): one model that weighs every signal for every asset, in every situation.

Each week, for every asset, the model sees:
- every strategy sleeve's view of that asset (its weight, as a share of the sleeve's gross);
- the asset's own state: 1-, 3-, 6- and 12-month returns, 12-1 month momentum, forecast volatility, distance from
  its 200-day average, recent news sentiment, whether an earnings release just came out;
- the twelve situation features (market state and the AI/power build-out);
- the asset's group (equity index, sector, single stock, bond, commodity, crypto).
It predicts the asset's return over the next week relative to the other assets, in units of its own volatility
(so a quiet bond and a volatile chip stock are comparable). A gradient-boosted tree model learns interactions such
as "momentum helps in calm uptrends but not right after a crash" on its own.

Walk-forward: the model is refitted every 4 weeks on every past week whose outcome was complete before the refit,
never on later data; it needs two years of history first. Weights: long the top fifth by predicted score, short the
bottom fifth where shorting is allowed (never crypto), sized by score over volatility, then risk-scaled like every
other sleeve. Parameters are fixed in the register before the run.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

import numpy as np

from ..contracts import parse_utc
from ..timeframes import NEW_YORK
from .sleeves import GROUPS, Context, _lag_ratio, _sma, risk_scale

HORIZON = 5                 # rows: one trading week
REFIT_EVERY = 4             # weekly decisions between refits
MIN_TRAIN_WEEKS = 104
QUANTILE = 0.2
MODEL_PARAMS = {"max_depth": 3, "learning_rate": 0.05, "max_iter": 200, "min_samples_leaf": 200,
                "l2_regularization": 1.0, "random_state": 0}
GROUP_NAMES = list(GROUPS)


def week_starts(dates) -> list[int]:
    """Rows that begin a new trading week (the decision rows of a weekly rebalance)."""
    return [i for i in range(1, len(dates)) if dates[i].isocalendar()[:2] != dates[i - 1].isocalendar()[:2]]


def asset_features(ctx: Context) -> tuple[np.ndarray, list[str]]:
    """(T, N, F) per-asset features known at each row's close."""
    p = ctx.panel
    c = p.close
    names = ["ret_21", "ret_63", "ret_126", "ret_252", "mom_12_1", "vol", "dist_sma200", "news_z", "news_count",
             "earnings_recent"]
    t_total, n = p.shape
    f = np.full((t_total, n, len(names)), np.nan)
    f[:, :, 7:10] = 0.0  # no news / no earnings event unless recorded (an all-blank column breaks the model's binning)
    for k, lag in enumerate((21, 63, 126, 252)):
        f[:, :, k] = _lag_ratio(c, lag)
    f[:, :, 4] = _lag_ratio(c, 252, skip=21)
    f[:, :, 5] = ctx.vols
    with np.errstate(invalid="ignore", divide="ignore"):
        f[:, :, 6] = c / _sma(c, 200) - 1
    if ctx.news is not None:
        for t in week_starts(p.dates):
            moment = ctx.decision_time(t)
            for j, asset in enumerate(p.assets):
                news = ctx.news(asset, moment)
                f[t, j, 7] = news.get("news_sentiment_z") if news.get("news_sentiment_z") is not None else 0.0
                f[t, j, 8] = news.get("news_count_24h", 0)
    if ctx.earnings is not None:
        for j, asset in enumerate(p.assets):
            if asset not in GROUPS["single_stock"]:
                continue
            events = sorted(parse_utc(e["available_at"]) for e in ctx.earnings(asset, ctx.decision_time(t_total - 1)))
            for t in week_starts(p.dates):
                close = datetime.combine(p.dates[t], time(16, 0), tzinfo=NEW_YORK)
                f[t, j, 9] = float(any(close - timedelta(days=7) < e <= close for e in events))
    return f, names


def build_design(ctx: Context, sleeves: list[np.ndarray], situation: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """(T, N, K) design: sleeve views, asset features, situation (same for all assets), group one-hot."""
    own, own_names = asset_features(ctx)
    t_total, n = ctx.panel.shape
    views = []
    for w in sleeves:
        gross = np.abs(w).sum(axis=1, keepdims=True)
        with np.errstate(invalid="ignore", divide="ignore"):
            views.append(np.where(gross > 0, w / gross, 0.0))
    view = np.stack(views, axis=2)
    situ = np.repeat(situation[:, None, :], n, axis=1)
    group = np.zeros((t_total, n, len(GROUP_NAMES)))
    for j, asset in enumerate(ctx.panel.assets):
        for g, name in enumerate(GROUP_NAMES):
            if asset in GROUPS[name]:
                group[:, j, g] = 1.0
    design = np.concatenate([view, own, situ, group], axis=2)
    names = [f"sleeve_{k}" for k in range(len(sleeves))] + own_names + \
        [f"situation_{k}" for k in range(situation.shape[1])] + [f"group_{g}" for g in GROUP_NAMES]
    return design, names


def targets(ctx: Context) -> np.ndarray:
    """(T, N) next-week return from row t + 1's open to row t + 6's open, over forecast volatility, minus the
    cross-sectional mean (what the ranker predicts). Complete only at row t + 6's open."""
    o = ctx.panel.open
    t_total, n = o.shape
    y = np.full((t_total, n), np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        fwd = o[1 + HORIZON:] / o[1:t_total - HORIZON] - 1
        y[:t_total - 1 - HORIZON] = fwd / (ctx.vols[:t_total - 1 - HORIZON] * np.sqrt(HORIZON))
    y = np.where(np.isfinite(y), y, np.nan)
    return y - np.nanmean(y, axis=1, keepdims=True)


def ranker(ctx: Context, sleeves: list[np.ndarray], situation: np.ndarray) -> tuple[np.ndarray, dict]:
    """Weights (T, N) from the walk-forward ranker (non-zero on weekly decision rows, held in between) and a small
    report (refits, training rows, feature importance at the last refit is not computed: trees are inspected later)."""
    from sklearn.ensemble import HistGradientBoostingRegressor

    design, names = build_design(ctx, sleeves, situation)
    y = targets(ctx)
    p = ctx.panel
    t_total, n = p.shape
    weeks = week_starts(p.dates)
    raw = np.zeros((t_total, n))
    shortable = p.shortable()
    model, refits, trained_rows = None, 0, 0
    for k, m in enumerate(weeks):
        if k >= MIN_TRAIN_WEEKS and (model is None or k % REFIT_EVERY == 0):
            # Training weeks whose outcome (open of row t + 6) is known by the decision at row m's close.
            rows = [t for t in weeks[:k] if t + 1 + HORIZON <= m]
            x = design[rows].reshape(-1, design.shape[2])
            target = y[rows].reshape(-1)
            keep = np.isfinite(target) & np.isfinite(x[:, len(sleeves) + 5])  # needs a volatility forecast
            if keep.sum() > 1000:
                model = HistGradientBoostingRegressor(**MODEL_PARAMS).fit(x[keep], target[keep])
                refits += 1
                trained_rows = int(keep.sum())
        if model is None:
            continue
        x_now = design[m]
        live = np.isfinite(x_now[:, len(sleeves) + 5]) & np.isfinite(p.close[m])
        if live.sum() < 10:
            continue
        score = np.full(n, np.nan)
        score[live] = model.predict(x_now[live])
        lo, hi = np.nanquantile(score, [QUANTILE, 1 - QUANTILE])
        long = live & (score >= hi) & (score > 0)
        short = live & (score <= lo) & (score < 0) & shortable
        with np.errstate(invalid="ignore", divide="ignore"):
            raw[m] = np.where(long | short, score / ctx.vols[m], 0.0)
    # Hold each week's weights until the next decision row.
    held = np.zeros((t_total, n))
    current = np.zeros(n)
    decision_rows = set(weeks)
    for t in range(t_total):
        if t in decision_rows:
            current = np.nan_to_num(raw[t])
        held[t] = current
    return risk_scale(ctx, held), {"refits": refits, "last_training_rows": trained_rows, "features": len(names)}

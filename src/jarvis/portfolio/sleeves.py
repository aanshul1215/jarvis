"""Strategy sleeves: each turns point-in-time data into target weights for every asset, every day.

A sleeve's raw weights are risk-scaled so that, on its own, it targets ``SLEEVE_VOL`` annual volatility (using the
shrunk correlation and per-asset volatility known that day), with gross exposure capped at ``SLEEVE_GROSS``. That
makes sleeves comparable, so the blender can mix them by situation without one dominating by sheer size.

Rules and parameters are fixed here before any development run (docs/09-portfolio/PORTFOLIO_REGISTER.md); a change
is a new version and a new logged trial. Evidence for each family is cited in the register.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from typing import Callable

import numpy as np

from ..contracts import AssetClass, parse_utc
from ..timeframes import NEW_YORK
from .panel import Panel
from .risk import correlation, portfolio_vol

SLEEVE_VOL, SLEEVE_GROSS = 0.10, 2.0

# Asset groups (for cross-sectional rules and pairs). Fixed list, not chosen by results.
GROUPS = {
    "equity_index": ("SPY", "QQQ", "IWM", "DIA", "EFA", "EEM"),
    "sector": ("XLF", "XLK", "XLE", "XLV", "XLY", "XLP", "XLI", "XLU", "XLB", "SMH", "VNQ"),
    "single_stock": ("AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "JPM", "XOM", "UNH"),
    "bond": ("TLT", "IEF", "SHY", "TIP", "HYG", "LQD"),
    "commodity": ("GLD", "SLV", "DBC", "USO", "CPER"),
    "crypto": ("BTC/USD", "ETH/USD"),
}
EQUITY_RISK = GROUPS["equity_index"] + GROUPS["sector"] + GROUPS["single_stock"]
# Pairs with a clear economic link (same index, sector leader vs its ETF, related commodities or bond tenors).
PAIRS = (("SPY", "DIA"), ("QQQ", "XLK"), ("TLT", "IEF"), ("IEF", "TIP"), ("SHY", "IEF"), ("GLD", "SLV"),
         ("HYG", "LQD"), ("EFA", "EEM"), ("XLE", "XOM"), ("USO", "XLE"), ("DBC", "USO"), ("XLF", "JPM"),
         ("XLV", "UNH"), ("XLY", "AMZN"), ("SMH", "NVDA"), ("XLK", "MSFT"), ("XLK", "AAPL"), ("GOOGL", "META"),
         ("CPER", "XLB"), ("XLU", "VNQ"))
THEME_BASKET = ("SMH", "NVDA", "XLU", "XLB", "CPER")
HYPERSCALERS = ("MSFT", "GOOGL", "AMZN", "META")


@dataclass
class Context:
    """Everything a sleeve may read, all point in time. Built once per panel by ``prepare``."""

    panel: Panel
    vols: np.ndarray                     # (T, N) forecast daily volatility
    returns: np.ndarray                  # (T, N) close-to-close returns
    earnings: Callable[[str, datetime], list[dict]] | None = None
    news: Callable[[str, datetime], dict] | None = None
    capex_growth: np.ndarray | None = None  # (T,) hyperscaler capex growth known at each row, NaN if unknown
    cache: dict = field(default_factory=dict)

    def decision_time(self, t: int) -> datetime:
        """When row t's decision is taken in research: 21:15 UTC on its date (after the stock close + 15 min)."""
        return datetime.combine(self.panel.dates[t], time(21, 15), tzinfo=timezone.utc)

    def cols(self, names) -> np.ndarray:
        return np.array([self.panel.assets.index(a) for a in names if a in self.panel.assets], dtype=int)


# --- shared helpers ------------------------------------------------------------------------------------------------

def _lag_ratio(close: np.ndarray, k: int, skip: int = 0) -> np.ndarray:
    out = np.full(close.shape, np.nan)
    out[k:] = close[k - skip:len(close) - skip] / close[:len(close) - k] - 1 if skip else close[k:] / close[:-k] - 1
    return out


def _sma(close: np.ndarray, k: int) -> np.ndarray:
    c = np.where(np.isfinite(close), close, 0.0)
    counts = np.isfinite(close).astype(float)
    cs, cc = np.cumsum(c, axis=0), np.cumsum(counts, axis=0)
    out = np.full(close.shape, np.nan)
    s = cs[k - 1:].copy()
    n = cc[k - 1:].copy()
    s[1:] -= cs[:-k]
    n[1:] -= cc[:-k]
    with np.errstate(invalid="ignore", divide="ignore"):
        out[k - 1:] = np.where(n == k, s / k, np.nan)
    return out


def _rsi(close: np.ndarray, k: int) -> np.ndarray:
    delta = np.diff(close, axis=0, prepend=np.nan)
    gain, loss = np.clip(delta, 0, None), np.clip(-delta, 0, None)
    out = np.full(close.shape, np.nan)
    for t in range(k, len(close)):
        g, l = np.nanmean(gain[t - k + 1:t + 1], axis=0), np.nanmean(loss[t - k + 1:t + 1], axis=0)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[t] = np.where(l == 0, 100.0, 100 - 100 / (1 + g / l))
    return out


def risk_scale(ctx: Context, raw: np.ndarray, target: float = SLEEVE_VOL, gross: float = SLEEVE_GROSS) -> np.ndarray:
    """Scale each row of raw weights to the sleeve's volatility target (shrunk correlation), capping gross."""
    out = np.zeros(raw.shape)
    daily_target = target / math.sqrt(252)
    for t in range(raw.shape[0]):
        w = np.nan_to_num(raw[t])
        live = np.where((w != 0) & np.isfinite(ctx.vols[t]))[0]
        if not len(live):
            continue
        w = np.where(np.isfinite(ctx.vols[t]), w, 0.0)
        corr = correlation(ctx.returns, t, live)
        vol = portfolio_vol(w[live], ctx.vols[t, live], corr)
        if vol <= 0:
            continue
        scaled = w * (daily_target / vol)
        g = np.abs(scaled).sum()
        out[t] = scaled * (gross / g) if g > gross else scaled
    return out


def _inverse_vol(ctx: Context, mask: np.ndarray, sign: np.ndarray | float = 1.0) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        w = np.where(mask & np.isfinite(ctx.vols) & (ctx.vols > 0), sign / ctx.vols, 0.0)
    return np.nan_to_num(w)


def _hold_machine(entry: np.ndarray, exit_: np.ndarray, max_hold: int) -> np.ndarray:
    """Positions from entry/exit signals: enter on entry, leave on exit or after ``max_hold`` rows."""
    t_total, n = entry.shape
    pos = np.zeros((t_total, n), dtype=bool)
    age = np.zeros(n, dtype=int)
    for t in range(t_total):
        prev = pos[t - 1] if t else np.zeros(n, dtype=bool)
        age = np.where(prev, age + 1, 0)
        stay = prev & ~exit_[t] & (age < max_hold)
        pos[t] = stay | (~prev & entry[t])
        age = np.where(pos[t] & ~prev, 0, age)
    return pos


def _shortable_mask(ctx: Context) -> np.ndarray:
    return np.broadcast_to(ctx.panel.shortable(), ctx.panel.shape)


# --- new strategy families -----------------------------------------------------------------------------------------

def trend_xasset(ctx: Context) -> np.ndarray:
    """Cross-asset time-series momentum: the average sign of the 3-, 6- and 12-month returns, inverse-volatility
    weighted, long or short (shorts only where allowed). Every asset class, crypto included (long only)."""
    c = ctx.panel.close
    signs = [np.sign(_lag_ratio(c, k)) for k in (63, 126, 252)]
    signal = np.nanmean(np.stack(signs), axis=0)
    signal = np.where(np.isfinite(_lag_ratio(c, 252)), signal, np.nan)
    signal = np.where(_shortable_mask(ctx) | (signal > 0), signal, 0.0)
    return risk_scale(ctx, _inverse_vol(ctx, np.isfinite(signal), np.nan_to_num(signal)))


def xs_momentum(ctx: Context) -> np.ndarray:
    """Cross-sectional 12-1 month momentum among stocks and equity ETFs: long the top fifth, short the bottom fifth,
    inverse-volatility weighted, rebalanced daily on the same ranking."""
    c = ctx.panel.close
    mom = _lag_ratio(c, 252, skip=21)
    cols = ctx.cols(EQUITY_RISK)
    sign = np.zeros(c.shape)
    for t in range(c.shape[0]):
        m = mom[t, cols]
        ok = np.isfinite(m)
        if ok.sum() < 10:
            continue
        lo, hi = np.quantile(m[ok], [0.2, 0.8])
        sign[t, cols[ok & (m >= hi)]] = 1.0
        sign[t, cols[ok & (m <= lo)]] = -1.0
    return risk_scale(ctx, _inverse_vol(ctx, sign != 0, sign))


def low_volatility(ctx: Context) -> np.ndarray:
    """Low-volatility anomaly: long the least volatile third of stocks and equity ETFs (by 1-year realised
    volatility), inverse-volatility weighted. Long only (a defensive sleeve)."""
    r = ctx.returns
    cols = ctx.cols(EQUITY_RISK)
    mask = np.zeros(r.shape, dtype=bool)
    for t in range(252, r.shape[0]):
        rv = np.nanstd(r[t - 251:t + 1, cols], axis=0)
        ok = np.isfinite(rv) & (np.isfinite(r[t - 251:t + 1, cols]).sum(axis=0) > 200)
        if ok.sum() < 10:
            continue
        cut = np.quantile(rv[ok], 1 / 3)
        mask[t, cols[ok & (rv <= cut)]] = True
    return risk_scale(ctx, _inverse_vol(ctx, mask))


def pairs(ctx: Context, pair_list=PAIRS) -> np.ndarray:
    """Pairs trading on economically linked pairs. Hedge ratio from a 252-day regression of log prices; trade when
    the spread is 2 standard deviations (60-day) from its mean and its half-life is 1-30 days; exit at 0.5, stop at 4
    or after 20 days. Market-neutral by construction: the rich leg is shorted (only stocks/ETFs)."""
    c = ctx.panel.close
    raw = np.zeros(c.shape)
    for a, b in pair_list:
        if a not in ctx.panel.assets or b not in ctx.panel.assets:
            continue
        ia, ib = ctx.panel.index(a), ctx.panel.index(b)
        la, lb = np.log(c[:, ia]), np.log(c[:, ib])
        state, age, beta_used, blocked = 0, 0, 1.0, 0
        for t in range(252, c.shape[0]):
            x, y = lb[t - 251:t + 1], la[t - 251:t + 1]
            if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
                state = 0
                continue
            beta, alpha = np.polyfit(x, y, 1)
            spread = y - (alpha + beta * x)
            recent = spread[-60:]
            sd = recent.std()
            if sd <= 0:
                continue
            z = (spread[-1] - recent.mean()) / sd
            lagged, diff = spread[:-1] - spread[:-1].mean(), np.diff(spread)
            phi = float(lagged @ diff / (lagged @ lagged)) if lagged @ lagged > 0 else 0.0
            half_life = -math.log(2) / phi if phi < 0 else float("inf")
            if blocked and (abs(z) < 2 or np.sign(z) != blocked):
                blocked = 0  # the spread has come back (or flipped): the pair may trade again
            if state:
                age += 1
                if abs(z) > 4 or age >= 20:
                    state, blocked = 0, state  # stopped out or timed out: no re-entry on the same divergence
                elif abs(z) < 0.5 or np.sign(z) != state:
                    state = 0
            if not state and abs(z) >= 2 and np.sign(z) != blocked and 1 <= half_life <= 30 and 0.2 <= beta <= 5:
                state, age, beta_used = int(np.sign(z)), 0, float(beta)
            if state:
                # z > 0: a is rich -> short a, long beta x b, in value terms so the hedge holds. Each pair is
                # sized by its spread's daily volatility so that quiet and noisy pairs carry similar risk.
                spread_vol = float(np.std(np.diff(recent)))
                size = 0.01 / spread_vol if spread_vol > 0 else 0.0
                raw[t, ia] += -state * size
                raw[t, ib] += state * beta_used * size
    shortable = ctx.panel.shortable()
    raw = np.where((raw < 0) & ~shortable, 0.0, raw)
    return risk_scale(ctx, raw)


def news_sentiment(ctx: Context) -> np.ndarray:
    """Unusually positive news (FinBERT): 24-hour headline sentiment at least 2 standard errors above the asset's own
    previous 60 days, from 3+ headlines; hold 5 days or until it turns as negative. Long only."""
    if ctx.news is None:
        return np.zeros(ctx.panel.shape)
    t_total, n = ctx.panel.shape
    entry, exit_ = np.zeros((t_total, n), dtype=bool), np.zeros((t_total, n), dtype=bool)
    for t in range(t_total):
        moment = ctx.decision_time(t)
        for j, asset in enumerate(ctx.panel.assets):
            f = ctx.news(asset, moment)
            z = f.get("news_sentiment_z")
            if z is None:
                continue
            entry[t, j] = f["news_count_24h"] >= 3 and z >= 2
            exit_[t, j] = z <= -2
    return risk_scale(ctx, _inverse_vol(ctx, _hold_machine(entry, exit_, 5)))


def theme_ai_power(ctx: Context) -> np.ndarray:
    """AI/power build-out theme (owner request, after Aschenbrenner 2024): hold the theme basket (semiconductors,
    NVIDIA, utilities, materials, copper) in proportion to how fast the four hyperscalers' reported capital
    spending is growing (0 at <= 0% growth, full at >= 40%), but only while the basket is beating SPY over 6 months.
    Capital spending comes from SEC filings, counted from the day each filing became public."""
    t_total, n = ctx.panel.shape
    raw = np.zeros((t_total, n))
    if ctx.capex_growth is None:
        return raw
    cols = ctx.cols(THEME_BASKET)
    spy = ctx.panel.index("SPY") if "SPY" in ctx.panel.assets else None
    rel = _lag_ratio(ctx.panel.close, 126)
    for t in range(t_total):
        g = ctx.capex_growth[t]
        if not np.isfinite(g) or spy is None or not np.isfinite(rel[t, spy]):
            continue
        basket = np.nanmean(rel[t, cols]) if np.isfinite(rel[t, cols]).any() else np.nan
        if not np.isfinite(basket) or basket <= rel[t, spy]:
            continue
        strength = float(np.clip(g / 0.40, 0, 1))
        for j in cols:
            if np.isfinite(ctx.vols[t, j]) and ctx.vols[t, j] > 0:
                raw[t, j] = strength / ctx.vols[t, j]
    return risk_scale(ctx, raw)


# --- the earlier library, as weight sleeves (same rules as strategies.py) ------------------------------------------

def trend_sma200(ctx: Context) -> np.ndarray:
    c = ctx.panel.close
    above = c > _sma(c, 200)
    entry = above & (_lag_ratio(c, 126) > 0)
    return risk_scale(ctx, _inverse_vol(ctx, _hold_machine(entry, ~above, 252)))


def meanrev_rsi2(ctx: Context) -> np.ndarray:
    c = ctx.panel.close
    equity = np.broadcast_to(np.array([cl == AssetClass.EQUITY for cl in ctx.panel.classes]), c.shape)
    entry = equity & (_rsi(c, 2) < 10) & (c > _sma(c, 200))
    return risk_scale(ctx, _inverse_vol(ctx, _hold_machine(entry, c > _sma(c, 5), 5)))


def volatility_breakout(ctx: Context) -> np.ndarray:
    c, r = ctx.panel.close, ctx.returns
    v20 = np.full(c.shape, np.nan)
    v252 = np.full(c.shape, np.nan)
    for t in range(252, c.shape[0]):
        v20[t] = np.nanstd(r[t - 19:t + 1], axis=0)
        v252[t] = np.nanstd(r[t - 251:t + 1], axis=0)
    prior_high = np.full(c.shape, np.nan)
    prior_low = np.full(c.shape, np.nan)
    for t in range(21, c.shape[0]):
        prior_high[t] = np.nanmax(ctx.panel.high[t - 20:t], axis=0)
        prior_low[t] = np.nanmin(ctx.panel.low[t - 20:t], axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        entry = (v20 / v252 < 0.75) & (c > prior_high)
    return risk_scale(ctx, _inverse_vol(ctx, _hold_machine(entry, c < prior_low, 20)))


def breakout_volume(ctx: Context) -> np.ndarray:
    c, vol = ctx.panel.close, ctx.panel.volume
    prior_high = np.full(c.shape, np.nan)
    rel_volume = np.full(c.shape, np.nan)
    for t in range(21, c.shape[0]):
        prior_high[t] = np.nanmax(ctx.panel.high[t - 20:t], axis=0)
        with np.errstate(invalid="ignore", divide="ignore"):
            rel_volume[t] = vol[t] / np.nanmean(vol[t - 20:t], axis=0)
    entry = (c > prior_high) & (rel_volume >= 1.5)
    return risk_scale(ctx, _inverse_vol(ctx, _hold_machine(entry, np.zeros(c.shape, dtype=bool), 3)))


def relative_strength(ctx: Context) -> np.ndarray:
    c = ctx.panel.close
    mom = _lag_ratio(c, 252, skip=21)
    cols = ctx.cols(EQUITY_RISK + GROUPS["bond"] + GROUPS["commodity"])
    mask = np.zeros(c.shape, dtype=bool)
    held: set[int] = set()
    for t in range(c.shape[0]):
        m = mom[t, cols]
        ok = np.isfinite(m)
        if ok.sum() < 6:
            held = set()
            continue
        order = [cols[i] for i in np.argsort(-np.where(ok, m, -np.inf)) if ok[i]]
        rank = {j: k + 1 for k, j in enumerate(order)}
        held = {j for j in held if rank.get(j, 99) <= 5 and mom[t, j] > 0}
        for j in order[:3]:
            if mom[t, j] > 0:
                held.add(j)
        mask[t, list(held)] = True
    return risk_scale(ctx, _inverse_vol(ctx, mask))


def earnings_drift(ctx: Context) -> np.ndarray:
    if ctx.earnings is None:
        return np.zeros(ctx.panel.shape)
    c, vol = ctx.panel.close, ctx.panel.volume
    t_total, n = c.shape
    entry = np.zeros((t_total, n), dtype=bool)
    for j, asset in enumerate(ctx.panel.assets):
        if asset not in GROUPS["single_stock"]:
            continue
        events = [parse_utc(e["available_at"]) for e in ctx.earnings(asset, ctx.decision_time(t_total - 1))]
        for t in range(21, t_total):
            bar_end = datetime.combine(ctx.panel.dates[t], time(16, 0), tzinfo=NEW_YORK)  # the session close
            previous_close = datetime.combine(ctx.panel.dates[t - 1], time(16, 0), tzinfo=NEW_YORK)
            # Released after the previous session closed (so Friday-evening and weekend releases count on Monday).
            if not any(previous_close < e <= bar_end for e in events):
                continue
            avg = np.nanmean(vol[t - 20:t, j])
            if c[t - 1, j] > 0 and c[t, j] / c[t - 1, j] - 1 > 0.02 and avg > 0 and vol[t, j] >= 1.5 * avg:
                entry[t, j] = True
    return risk_scale(ctx, _inverse_vol(ctx, _hold_machine(entry, np.zeros((t_total, n), dtype=bool), 20)))


# Sleeves blended into the portfolio. Dropped after round-1 development (negative or zero Sharpe, 2017-2021): pairs,
# meanrev_rsi2, breakout_volume, xs_momentum. Round 3 (v1.2.0): relative_strength is replaced by the momentum ranker
# (ranker.py), which the study appends as the last sleeve.
ACTIVE = ("trend_xasset", "low_volatility", "news_sentiment", "theme_ai_power", "trend_sma200", "volatility_breakout",
          "earnings_drift")

SLEEVES: dict[str, Callable[[Context], np.ndarray]] = {
    "trend_xasset": trend_xasset, "xs_momentum": xs_momentum, "low_volatility": low_volatility, "pairs": pairs,
    "news_sentiment": news_sentiment, "theme_ai_power": theme_ai_power, "trend_sma200": trend_sma200,
    "meanrev_rsi2": meanrev_rsi2, "volatility_breakout": volatility_breakout, "breakout_volume": breakout_volume,
    "relative_strength": relative_strength, "earnings_drift": earnings_drift,
}

"""Situational awareness for the portfolio: what the market and the big picture look like at each decision.

Two layers, every value point in time (known at the row's decision time):

- **Market state** (how risky and how directional the market is): S&P 500 trend and volatility shift, VIX level and
  term structure, credit stress (high-yield vs Treasuries, Baa spread change), rate moves, breadth, dispersion
  between stocks, and the crypto trend.
- **Big picture** (after Aschenbrenner, *Situational Awareness*, 2024: follow the structural build-out): the
  AI/power basket's lead over the S&P 500, and the growth of the four hyperscalers' reported capital spending
  (SEC filings, counted from the day each became public).

Each feature is standardised with its own history up to that day (no future mean or variance). ``regime`` gives a
plain-language label for reports; the blender itself learns from the continuous features.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

import numpy as np

from ..contracts import parse_utc
from ..macro import AsOfSeries
from ..storage import LocalStorage
from .panel import Panel
from .sleeves import EQUITY_RISK, HYPERSCALERS, THEME_BASKET, Context, _lag_ratio, _sma

FEATURES = ("spy_trend", "spy_vol_shift", "vix", "vix_term", "credit_rel", "baa_change", "rates_change", "breadth",
            "dispersion", "crypto_trend", "theme_lead", "capex_growth")
MIN_STANDARDISE = 252


def capex_growth(store: LocalStorage, dates: list[date]) -> np.ndarray:
    """Hyperscalers' capital spending growth known at each date: the sum of each company's latest reported quarter
    over the same quarter a year earlier. NaN until all four have a year-on-year pair."""
    quarters: dict[str, list[tuple[datetime, date, float]]] = {}
    for ticker in HYPERSCALERS:
        rows = []
        for r in store.read_table("edgar", "facts", ticker):
            if r["metric"] != "capex" or not r["duration_days"] or not 80 <= r["duration_days"] <= 100:
                continue
            rows.append((parse_utc(r["available_at"]), date.fromisoformat(r["period_end"]), float(r["value"])))
        quarters[ticker] = sorted(rows)
    out = np.full(len(dates), np.nan)
    for i, d in enumerate(dates):
        moment = datetime.combine(d, time(21, 15), tzinfo=timezone.utc)
        now_sum = before_sum = 0.0
        complete = True
        for ticker, rows in quarters.items():
            known: dict[date, float] = {}
            for available, end, value in rows:
                if available <= moment:
                    known[end] = value  # a later filing of the same quarter replaces the earlier one
            if not known:
                complete = False
                break
            latest = max(known)
            prior = [e for e in known if abs((latest - e).days - 365) <= 20]
            if not prior:
                complete = False
                break
            now_sum += abs(known[latest])
            before_sum += abs(known[prior[0]])
        if complete and before_sum > 0:
            out[i] = now_sum / before_sum - 1
    return out


def raw_features(ctx: Context, store: LocalStorage) -> np.ndarray:
    p, r = ctx.panel, ctx.returns
    t_total = p.shape[0]
    x = np.full((t_total, len(FEATURES)), np.nan)
    col = {name: k for k, name in enumerate(FEATURES)}
    spy = p.index("SPY")
    close = p.close
    x[:, col["spy_trend"]] = close[:, spy] / _sma(close[:, [spy]], 200)[:, 0] - 1
    for t in range(252, t_total):
        x[t, col["spy_vol_shift"]] = np.nanstd(r[t - 19:t + 1, spy]) / np.nanstd(r[t - 251:t + 1, spy]) - 1
    series = {s: AsOfSeries(store.read_table("macro", s)) for s in ("VIXCLS", "VXVCLS", "BAA10Y", "DGS10")}
    for t in range(t_total):
        moment = ctx.decision_time(t)
        vix, vxv = series["VIXCLS"].at(moment), series["VXVCLS"].at(moment)
        x[t, col["vix"]] = vix if vix is not None else np.nan
        x[t, col["vix_term"]] = vix / vxv if vix is not None and vxv else np.nan
        baa, baa_q = series["BAA10Y"].at(moment), series["BAA10Y"].at(moment - timedelta(days=91))
        x[t, col["baa_change"]] = baa - baa_q if baa is not None and baa_q is not None else np.nan
        y10, y10_q = series["DGS10"].at(moment), series["DGS10"].at(moment - timedelta(days=91))
        x[t, col["rates_change"]] = y10 - y10_q if y10 is not None and y10_q is not None else np.nan
    if "HYG" in p.assets and "IEF" in p.assets:
        r63 = _lag_ratio(close, 63)
        x[:, col["credit_rel"]] = r63[:, p.index("HYG")] - r63[:, p.index("IEF")]
    eq = ctx.cols(EQUITY_RISK)
    with np.errstate(invalid="ignore"):
        above = close[:, eq] > _sma(close[:, eq], 200)
        known = np.isfinite(_sma(close[:, eq], 200))
        x[:, col["breadth"]] = np.where(known.sum(axis=1) >= 10, (above & known).sum(axis=1) / np.maximum(known.sum(axis=1), 1), np.nan)
        r21 = _lag_ratio(close, 21)
        x[:, col["dispersion"]] = np.nanstd(r21[:, eq], axis=1)
    if "BTC/USD" in p.assets:
        btc = p.index("BTC/USD")
        x[:, col["crypto_trend"]] = close[:, btc] / _sma(close[:, [btc]], 200)[:, 0] - 1
    r126 = _lag_ratio(close, 126)
    theme = ctx.cols(THEME_BASKET)
    with np.errstate(invalid="ignore"):
        x[:, col["theme_lead"]] = np.nanmean(r126[:, theme], axis=1) - r126[:, spy]
    if ctx.capex_growth is not None:
        x[:, col["capex_growth"]] = ctx.capex_growth
    return x


def standardise(x: np.ndarray, minimum: int = MIN_STANDARDISE) -> np.ndarray:
    """Each row scaled with the mean and standard deviation of that column's own history up to the row; 0 where
    unknown (and before ``minimum`` observations), clipped to +-4."""
    out = np.zeros(x.shape)
    for k in range(x.shape[1]):
        values = x[:, k]
        seen = np.isfinite(values)
        total = np.cumsum(np.where(seen, values, 0.0))
        total_sq = np.cumsum(np.where(seen, values ** 2, 0.0))
        count = np.cumsum(seen)
        with np.errstate(invalid="ignore", divide="ignore"):
            mean = total / count
            sd = np.sqrt(np.maximum(total_sq / count - mean ** 2, 0.0))
            z = (values - mean) / sd
        out[:, k] = np.where(seen & (count >= minimum) & (sd > 0), np.clip(z, -4, 4), 0.0)
    return out


REGIMES = ("crisis", "bear", "bull_volatile", "bull_calm")


def regime(raw_row: np.ndarray) -> str:
    """Plain-language label for reports (not used for decisions): crisis when VIX >= 30 or its term structure is
    inverted; otherwise bear below the 200-day average, else bull, volatile when recent volatility is above normal."""
    f = dict(zip(FEATURES, raw_row))
    if (np.isfinite(f["vix"]) and f["vix"] >= 30) or (np.isfinite(f["vix_term"]) and f["vix_term"] >= 1):
        return "crisis"
    if np.isfinite(f["spy_trend"]) and f["spy_trend"] < 0:
        return "bear"
    return "bull_volatile" if np.isfinite(f["spy_vol_shift"]) and f["spy_vol_shift"] > 0 else "bull_calm"

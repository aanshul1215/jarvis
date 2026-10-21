"""The enhanced-index stock book (docs/10-shortterm/ENHANCED_INDEX_STUDY.md).

Own the whole liquid universe, sized by risk (1 / volatility), tilted by a fixed signal score (event drift and
momentum) between 0.5x and 1.5x, weekly, with per-stock and per-industry caps; at month starts, move into the
strongest bonds and commodities only in a clear stock-market downtrend (12-month return below T-bills and SPY below
its 200-day average).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..portfolio.core import tbill_growth
from .book import Instruments, defensive_targets, event_signal, percentile_rank
from .reversal import Market, lagged_return

VOL_DAYS, VOL_MIN = 63, 40
STOCK_CAP, GROUP_CAP = 0.03, 0.25
BAND, BAND_REL = 0.001, 0.25
TILT_LOW = 0.5


def weekly_rows(dates, rows: list[int]) -> set[int]:
    return {t for t in rows if t == rows[0] or dates[t].isocalendar()[:2] != dates[t - 1].isocalendar()[:2]}


def volatility(close: np.ndarray) -> np.ndarray:
    r = lagged_return(close, 1)
    sd = pd.DataFrame(r).rolling(VOL_DAYS, min_periods=VOL_MIN).std().to_numpy()
    return np.where(sd > 0, sd, np.nan)


def cap_weights(w: dict[int, float], groups: dict[int, str]) -> dict[int, float]:
    """Normalise to 1, then enforce the stock and industry caps, spreading any excess over uncapped names."""
    w = {j: v for j, v in w.items() if v > 0}
    for _ in range(50):
        total = sum(w.values())
        w = {j: v / total for j, v in w.items()}
        changed = False
        for j, v in w.items():
            if v > STOCK_CAP + 1e-12:
                w[j] = STOCK_CAP
                changed = True
        by_group: dict[str, float] = {}
        for j, v in w.items():
            by_group[groups[j]] = by_group.get(groups[j], 0.0) + v
        for g, total_g in by_group.items():
            if total_g > GROUP_CAP + 1e-12:
                scale = GROUP_CAP / total_g
                for j in w:
                    if groups[j] == g:
                        w[j] *= scale
                changed = True
        if not changed:
            break
        # Spread the removed weight over names below their caps, in proportion.
        free = [j for j in w if w[j] < STOCK_CAP - 1e-12 and by_group.get(groups[j], 0) < GROUP_CAP - 1e-12]
        missing = 1.0 - sum(w.values())
        base = sum(w[j] for j in free)
        if missing > 1e-12 and base > 0:
            for j in free:
                w[j] += missing * w[j] / base
    total = sum(w.values())
    return {j: v / total for j, v in w.items()} if total > 1 + 1e-9 else w


def targets(inst: Instruments, m: Market, universe: dict[str, list[str]], groups: dict[str, str], spy_close: np.ndarray,
            rates: np.ndarray, rows: list[int], *, tilt: bool = True, switch: bool = True,
            sleeve: float = 0.0) -> tuple[dict, dict]:
    """{row: target weights or None (no trade)} and a report. With ``sleeve`` > 0 (study 7) that share of capital is
    always in the month's defensive choice (bonds/commodities by their own trend, else SHY) and the switch is off."""
    if sleeve:
        switch = False
    col = {s: j for j, s in enumerate(m.symbols)}
    members = np.zeros(m.close.shape, dtype=bool)
    for t, d in enumerate(m.dates):
        for s in universe.get(f"{d.year:04d}-{d.month:02d}", []):
            if s in col:
                members[t, col[s]] = True
    members &= np.isfinite(m.close) & (np.nan_to_num(m.raw_close) >= 5)
    vol = volatility(m.close)
    ev = event_signal(m, spy_close)
    r126 = lagged_return(m.close, 126)
    r12_1 = np.full(m.close.shape, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        r12_1[252:] = m.close[231:-21] / m.close[:-252] - 1
    growth = tbill_growth(rates)
    spy_252 = np.full(len(spy_close), np.nan)
    spy_252[252:] = spy_close[252:] / spy_close[:-252] - 1
    spy_200 = pd.Series(spy_close).rolling(200, min_periods=200).mean().to_numpy()
    group_of = {j: groups.get(m.symbols[j], "UNKNOWN") for j in range(len(m.symbols))}
    weekly = weekly_rows(m.dates, rows)
    out, risk_on, defensive_now = {}, True, None
    report = {"sleeve_months": {}, "decisions": 0, "risk_off_decisions": 0, "names_sum": 0, "max_group_share": 0.0, "max_stock_weight": 0.0}
    for t in rows:
        d = m.dates[t]
        month_start = t == rows[0] or d.month != m.dates[t - 1].month
        if month_start and switch:
            down = (np.isfinite(spy_252[t]) and np.isfinite(growth[t]) and spy_252[t] < growth[t]
                    and np.isfinite(spy_200[t]) and spy_close[t] < spy_200[t])
            risk_on = not down
        if sleeve and (month_start or defensive_now is None):
            defensive_now = defensive_targets(inst, t, growth)
            report["sleeve_months"][d.isoformat()] = sorted(inst.symbols[j] for j in defensive_now)
        if (t not in weekly and not month_start) or (not risk_on and not month_start):
            out[t] = None  # no trade today (risk-off holdings are chosen once a month)
            continue
        report["decisions"] += 1
        if not risk_on:
            out[t] = defensive_targets(inst, t, growth)
            report["risk_off_decisions"] += 1
            continue
        mem = members[t] & np.isfinite(vol[t]) & (t + 1 < len(m.dates)) & np.isfinite(m.open[min(t + 1, len(m.dates) - 1)])
        names = np.where(mem)[0]
        if not len(names):
            out[t] = None
            continue
        base = 1.0 / vol[t, names]
        if tilt:
            mom = np.nanmean(np.stack([percentile_rank(r126[t], mem), percentile_rank(r12_1[t], mem)]), axis=0)
            score = (np.nan_to_num(percentile_rank(ev[t], mem), nan=0.5) + np.nan_to_num(mom, nan=0.5)) / 2
            base = base * (TILT_LOW + score[names])
        w = cap_weights(dict(zip(names.tolist(), base.tolist())), group_of)
        if sleeve:
            combined = {j: v * (1 - sleeve) for j, v in w.items()}
            for j, v in defensive_now.items():
                combined[j] = combined.get(j, 0.0) + v * sleeve
            out[t] = combined
        else:
            out[t] = w
        report["names_sum"] += len(w)
        share: dict[str, float] = {}
        for j, v in w.items():
            share[group_of[j]] = share.get(group_of[j], 0.0) + v
        report["max_group_share"] = max(report["max_group_share"], max(share.values()))
        report["max_stock_weight"] = max(report["max_stock_weight"], max(w.values()))
    report["risk_off_share"] = report["risk_off_decisions"] / max(1, report["decisions"])
    report["average_names"] = report.pop("names_sum") / max(1, report["decisions"] - report["risk_off_decisions"])
    return out, report

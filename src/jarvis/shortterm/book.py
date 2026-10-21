"""The Jarvis stock book (docs/10-shortterm/STOCK_BOOK_STUDY.md).

A fully invested book of up to 30 liquid US stocks chosen daily by a fixed-weight score (event drift, momentum,
bounce), switched at month starts into the strongest bonds and commodities when the stock market's 12-month trend is
below T-bills. Simulated exactly at daily opens: decisions after a close, trades at the next open, positions drift
between trades, a no-trade band, per-side costs, cash at T-bills, delisted stocks exit at their last close (known
failures at zero).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from ..contracts import AssetClass
from ..portfolio.core import tbill_growth
from ..storage import LocalStorage
from ..timeframes import NEW_YORK
from .events import EXCESS, volume_ratio
from .reversal import COST_REST, COST_TOP100, Market, lagged_return

MAX_NAMES, KEEP_RANK, GROUP_CAP = 30, 60, 9
EVENT_DAYS = 20
DEFENSIVE = ("TLT", "IEF", "TIP", "LQD", "GLD", "SLV", "DBC", "CPER", "USO")
SAFE = "SHY"
ETF_COST = {"CPER": 0.0015}
ETF_DEFAULT_COST = 0.0005
BAND, BAND_REL = 0.01, 0.20
WEIGHTS = {"B1": (1.0, 1.0, 0.5, True), "A1": (1.0, 1.0, 0.5, False), "A2": (0.0, 1.0, 0.0, True),
           "A3": (1.0, 0.0, 0.0, True), "A4": (1.0, 1.0, 0.0, True)}  # event, momentum, bounce, market switch


@dataclass
class Instruments:
    dates: list[date]
    symbols: list[str]
    is_stock: np.ndarray
    open: np.ndarray
    close: np.ndarray
    last_row: np.ndarray
    failed_after: dict[int, int]


def load_etfs(store: LocalStorage, dates: list[date], names) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    index = {d: i for i, d in enumerate(dates)}
    out = {}
    for s in names:
        o, c = np.full(len(dates), np.nan), np.full(len(dates), np.nan)
        for b in store.load_bars(s, AssetClass.EQUITY, dataset="1Day-adjusted"):
            i = index.get(b.start_at.astimezone(NEW_YORK).date())
            if i is not None:
                o[i], c[i] = b.open, b.close
        out[s] = (o, c)
    return out


def combine(m: Market, etfs: dict[str, tuple[np.ndarray, np.ndarray]]) -> Instruments:
    names = list(etfs)
    o = np.column_stack([m.open] + [etfs[s][0] for s in names])
    c = np.column_stack([m.close] + [etfs[s][1] for s in names])
    last = np.concatenate([m.last_row, [len(m.dates) - 1] * len(names)])
    stock = np.array([True] * len(m.symbols) + [False] * len(names))
    return Instruments(m.dates, m.symbols + names, stock, o, c, last, dict(m.failed_after))


def percentile_rank(x: np.ndarray, members: np.ndarray) -> np.ndarray:
    """Ranks in [0, 1] over the member columns (ties averaged); NaN elsewhere or where x is missing."""
    out = np.full(x.shape, np.nan)
    ok = members & np.isfinite(x)
    if ok.sum() > 1:
        out[ok] = (pd.Series(x[ok]).rank(method="average").to_numpy() - 1) / (ok.sum() - 1)
    return out


def event_signal(m: Market, spy_close: np.ndarray) -> np.ndarray:
    """1 on a high-volume jump day, fading linearly to 0 over EVENT_DAYS sessions (strongest remaining value)."""
    r1 = lagged_return(m.close, 1)
    spy_r = np.full(len(spy_close), np.nan)
    spy_r[1:] = spy_close[1:] / spy_close[:-1] - 1
    ratio = volume_ratio(m.volume)
    with np.errstate(invalid="ignore"):
        hit = (r1 >= 0.04) & ((r1 - spy_r[:, None]) >= EXCESS) & (ratio >= 3.0)
    out = np.zeros(m.close.shape)
    for k in range(EVENT_DAYS):
        shifted = np.zeros(hit.shape, dtype=bool)
        shifted[k:] = hit[:len(hit) - k]
        out = np.maximum(out, shifted * (1 - k / EVENT_DAYS))
    return out


def stock_scores(m: Market, members: np.ndarray, spy_close: np.ndarray, weights) -> np.ndarray:
    """(T, N) composite score of the stocks in each day's universe."""
    w_event, w_mom, w_bounce = weights
    ev = event_signal(m, spy_close)
    r126 = lagged_return(m.close, 126)
    r12_1 = np.full(m.close.shape, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        r12_1[252:] = m.close[231:-21] / m.close[:-252] - 1
    r5 = lagged_return(m.close, 5)
    out = np.full(m.close.shape, np.nan)
    for t in range(len(m.dates)):
        mem = members[t]
        if mem.sum() < 2:
            continue
        parts, total = [], 0.0
        if w_event:
            parts.append(w_event * np.nan_to_num(percentile_rank(ev[t], mem), nan=0.5))
            total += w_event
        if w_mom:
            mom = np.nanmean(np.stack([percentile_rank(r126[t], mem), percentile_rank(r12_1[t], mem)]), axis=0)
            parts.append(w_mom * np.nan_to_num(mom, nan=0.5))
            total += w_mom
        if w_bounce:
            parts.append(w_bounce * np.nan_to_num(percentile_rank(-r5[t], mem), nan=0.5))
            total += w_bounce
        out[t] = np.where(mem, sum(parts) / total, np.nan)
    return out


def defensive_targets(inst: Instruments, t: int, rates_growth: np.ndarray) -> dict[int, float]:
    """Top 3 bonds/commodities by composite momentum with a 12-month return above T-bills; the rest in SHY."""
    col = {s: j for j, s in enumerate(inst.symbols)}
    c = inst.close
    cands = [col[s] for s in DEFENSIVE if s in col and t >= 252 and np.isfinite(c[t, col[s]]) and np.isfinite(c[t - 252, col[s]])]
    if not cands:
        return {col[SAFE]: 1.0}
    def r(j, k, skip=0):
        return c[t - skip, j] / c[t - k, j] - 1
    sig = np.array([[r(j, 63), r(j, 126), r(j, 252, 21)] for j in cands])
    ranks = np.mean([pd.Series(sig[:, i]).rank().to_numpy() for i in range(3)], axis=0)
    order = [cands[i] for i in np.argsort(-ranks, kind="stable")]
    chosen = [j for j in order if r(j, 252) > rates_growth[t]][:3]
    out = {j: 1 / 3 for j in chosen}
    if len(chosen) < 3:
        out[col[SAFE]] = out.get(col[SAFE], 0.0) + (3 - len(chosen)) / 3
    return out


def targets(inst: Instruments, m: Market, universe: dict[str, list[str]], groups: dict[str, str], spy_close: np.ndarray,
            rates: np.ndarray, rows: list[int], variant: str = "B1") -> tuple[dict[int, dict[int, float]], dict]:
    """Target weights decided after each row's close, and a report."""
    w_event, w_mom, w_bounce, switch = WEIGHTS[variant]
    col = {s: j for j, s in enumerate(m.symbols)}
    members = np.zeros(m.close.shape, dtype=bool)
    for t, d in enumerate(m.dates):
        for s in universe.get(f"{d.year:04d}-{d.month:02d}", []):
            if s in col:
                members[t, col[s]] = True
    members &= np.isfinite(m.close) & (np.nan_to_num(m.raw_close) >= 5)
    score = stock_scores(m, members, spy_close, (w_event, w_mom, w_bounce))
    growth = tbill_growth(rates)
    spy_252 = np.full(len(spy_close), np.nan)
    spy_252[252:] = spy_close[252:] / spy_close[:-252] - 1
    out, held, risk_on = {}, [], True
    report = {"risk_off_days": 0, "days": 0, "names_sum": 0, "max_group_share": 0.0}
    for t in rows:
        d = m.dates[t]
        if t == rows[0] or d.month != m.dates[t - 1].month:
            risk_on = (not switch) or bool(np.isfinite(spy_252[t]) and np.isfinite(growth[t]) and spy_252[t] > growth[t])
        report["days"] += 1
        if not risk_on:
            held = []
            out[t] = defensive_targets(inst, t, growth)
            report["risk_off_days"] += 1
            continue
        s = score[t]
        ranked = [j for j in np.argsort(-np.nan_to_num(s, nan=-1), kind="stable") if np.isfinite(s[j])]
        rank = {j: k + 1 for k, j in enumerate(ranked)}
        held = [j for j in held if rank.get(j, 10 ** 6) <= KEEP_RANK]
        count: dict[str, int] = {}
        for j in held:
            g = groups.get(m.symbols[j], "UNKNOWN")
            count[g] = count.get(g, 0) + 1
        for j in ranked:
            if len(held) >= MAX_NAMES:
                break
            if j in held or not (t + 1 < len(m.dates) and np.isfinite(m.open[t + 1, j])):
                continue
            g = groups.get(m.symbols[j], "UNKNOWN")
            if count.get(g, 0) >= GROUP_CAP:
                continue
            held.append(j)
            count[g] = count.get(g, 0) + 1
        out[t] = {j: 1 / MAX_NAMES for j in held}
        report["names_sum"] += len(held)
        if held:
            report["max_group_share"] = max(report["max_group_share"], max(count.values()) / MAX_NAMES)
    report["risk_off_share"] = report.pop("risk_off_days") / max(1, report["days"])
    report["average_names"] = report.pop("names_sum") / max(1, report["days"])
    return out, report


def simulate(inst: Instruments, decided: dict[int, dict[int, float]], costs: np.ndarray, rates: np.ndarray, *,
             cost_multiplier: float = 1.0) -> dict:
    """Exact daily simulation from target weights. ``costs`` (T, N) per side."""
    rows = sorted(decided)
    n = len(inst.symbols)
    h = np.zeros(n)          # weights after the last open's trades, drifted to the current open
    dates, rets, turnover, ended = [], [], [], 0
    gone = np.zeros(n, dtype=bool)
    for t in rows:
        d = t + 1
        if d + 1 >= len(inst.dates):
            break
        target = np.zeros(n)
        for j, w in decided[t].items():
            target[j] = w
        target[gone] = 0.0
        new = h.copy()
        for j in np.where((target > 0) | (h > 0))[0]:
            if target[j] == 0:
                new[j] = 0.0
            elif h[j] == 0 or abs(target[j] - h[j]) > max(BAND, BAND_REL * target[j]):
                new[j] = target[j]
        over = new.sum() - 1.0
        if over > 1e-12:  # never borrow: scale down only the purchases
            buys = np.clip(new - h, 0, None)
            new -= buys * min(1.0, over / buys.sum()) if buys.sum() > 0 else 0
        traded = np.abs(new - h)
        cost = float(traded @ (costs[t] * cost_multiplier))
        cash = 1.0 - new.sum()
        rel = np.ones(n)
        for j in np.where(new > 0)[0]:
            p0, p1 = inst.open[d, j], inst.open[d + 1, j]
            if np.isfinite(p0) and np.isfinite(p1):
                rel[j] = p1 / p0
            elif d + 1 > inst.last_row[j]:  # the stock's data ends: it leaves the book now
                last_close = inst.close[inst.last_row[j], j]
                rel[j] = 0.0 if j in inst.failed_after else (last_close / p0 if np.isfinite(p0) else 1.0)
                gone[j] = True
                ended += 1
        growth = float(new @ rel) + cash * (1 + np.nan_to_num(rates[t]) / 252)
        r = growth - cost - 1.0
        h = np.where(gone, 0.0, new * rel) / growth if growth > 0 else np.zeros(n)
        if gone.any():  # proceeds of stocks that left are cash now
            h[gone] = 0.0
        dates.append(inst.dates[d + 1])
        rets.append(r)
        turnover.append(float(traded.sum()))
    return {"dates": dates, "returns": np.array(rets), "turnover": np.array(turnover), "data_ended_exits": ended}


def cost_table(inst: Instruments, m: Market, universe: dict[str, list[str]]) -> np.ndarray:
    col = {s: j for j, s in enumerate(m.symbols)}
    out = np.full((len(inst.dates), len(inst.symbols)), COST_REST)
    for j in range(len(m.symbols), len(inst.symbols)):
        out[:, j] = ETF_COST.get(inst.symbols[j], ETF_DEFAULT_COST)
    for t, d in enumerate(inst.dates):
        for rank, s in enumerate(universe.get(f"{d.year:04d}-{d.month:02d}", [])[:100]):
            if s in col:
                out[t, col[s]] = COST_TOP100
    return out

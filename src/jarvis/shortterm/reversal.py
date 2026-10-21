"""Short-term reversal study (docs/10-shortterm/REVERSAL_STUDY.md): buy recent losers among liquid stocks, hold 5 days.

Bookkeeping is exact: the lane is five sub-accounts. Sub-account j trades the baskets decided on sessions t with
t = j (mod 5); each basket is bought at the next open and sold five sessions later, at the same open where that
sub-account's next basket is bought. There is no hidden rebalancing between sub-accounts. A basket is bought and
held (equal weights at entry). A stock whose data ends while held exits at its last close, except a known
failure (``data.KNOWN_FAILURES``) held past its last listed day, which is valued at zero.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd

from .data import KNOWN_FAILURES

HOLD, SLOTS, TOP = 5, 5, 10
COST_TOP100, COST_REST = 0.0004, 0.0008  # per side


@dataclass
class Market:
    """Wide daily arrays (sessions x symbols) built from the long bar tables."""

    dates: list[date]
    symbols: list[str]
    open: np.ndarray      # adjusted
    close: np.ndarray     # adjusted
    raw_close: np.ndarray
    last_row: np.ndarray  # last row with data per symbol
    failed_after: dict[int, int] = field(default_factory=dict)  # symbol column -> last listed row (known failures)

    @classmethod
    def from_frames(cls, adjusted: pd.DataFrame, raw: pd.DataFrame) -> "Market":
        def wide(df, col):
            d = df.assign(day=df["timestamp"].dt.tz_convert("America/New_York").dt.date)
            return d.pivot_table(index="day", columns="symbol", values=col, aggfunc="last")

        o, c, rc = wide(adjusted, "open"), wide(adjusted, "close"), wide(raw, "close")
        days = sorted(set(o.index) | set(rc.index))
        syms = sorted(set(o.columns) | set(rc.columns))
        o, c, rc = (x.reindex(index=days, columns=syms) for x in (o, c, rc))
        oc = c.to_numpy(dtype=float)
        last = np.array([np.max(np.where(np.isfinite(oc[:, j]))[0]) if np.isfinite(oc[:, j]).any() else -1
                         for j in range(len(syms))])
        until = dict(KNOWN_FAILURES)
        failed = {}
        for j, s in enumerate(syms):
            if s in until and last[j] >= 0 and days[last[j]] <= until[s]:
                failed[j] = int(last[j])
        return cls(days, syms, o.to_numpy(dtype=float), oc, rc.to_numpy(dtype=float), last, failed)


def lagged_return(close: np.ndarray, k: int) -> np.ndarray:
    out = np.full(close.shape, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        out[k:] = close[k:] / close[:-k] - 1
    return out


def trade_path(m: Market, j: int, t: int, cost: float) -> tuple[np.ndarray, bool]:
    """Value of $1 put into stock j at open t+1 (after the entry cost), at each open t+1 .. t+1+HOLD, after the
    exit cost at the end. Returns (path of length HOLD + 1, whether the stock's data ended while held)."""
    path = np.empty(HOLD + 1)
    entry = m.open[t + 1, j]
    last_price = entry
    ended = False
    for k in range(HOLD + 1):
        d = t + 1 + k
        price = m.open[d, j] if d < len(m.dates) else np.nan
        if not np.isfinite(price):
            if d > m.last_row[j]:  # the stock's data has ended
                ended = True
                if j in m.failed_after:
                    price = 0.0  # known failure: shareholders were wiped out
                else:
                    price = m.close[m.last_row[j], j]  # acquired / delisted otherwise: last close
            else:
                price = last_price  # a missing bar inside the data (halt): carry the last price
        last_price = price
        path[k] = (1 - cost) * price / entry
    path[-1] *= (1 - cost)
    return path, ended


def simulate(m: Market, baskets: dict[int, list[int]], costs: np.ndarray, cash_rate: np.ndarray, *,
             cost_multiplier: float = 1.0) -> dict:
    """Daily lane returns (open to open, dated by the later open) and per-trade records. ``baskets`` maps every
    decision row t of the test (consecutive sessions) to stock columns (an empty list means cash); ``costs`` is the
    per-side cost, (N,) or per decision row (T, N); ``cash_rate`` (T,) the annual T-bill rate known at each row."""
    t_total = len(m.dates)
    rows = sorted(t for t in baskets if t + 1 + HOLD < t_total)
    trades, segments = [], {}
    for t in rows:
        names = baskets[t]
        if names:
            paths = []
            for j in names:
                cost = costs[t, j] if costs.ndim == 2 else costs[j]
                path, ended = trade_path(m, j, t, cost * cost_multiplier)
                paths.append(path)
                trades.append({"decision": m.dates[t], "symbol": m.symbols[j], "net": float(path[-1] - 1),
                               "ended": ended, "failed": ended and j in m.failed_after})
            segments[t] = np.mean(paths, axis=0)
        else:  # nothing qualifies: this sub-account holds cash for the holding period
            segments[t] = (1 + np.nan_to_num(cash_rate[t]) / 252) ** np.arange(HOLD + 1)
    if not rows:
        return {"dates": [], "returns": np.array([]), "trades": trades}
    first = rows[0]
    curves = np.full((SLOTS, t_total), np.nan)
    for s in range(SLOTS):
        value = 1.0 / SLOTS
        curves[s, first + 1:] = value  # cash until its first basket
        for t in rows[s::SLOTS]:
            seg = segments[t]
            curves[s, t + 1:t + 1 + HOLD] = value * seg[:HOLD]
            value *= seg[HOLD]
            curves[s, t + 1 + HOLD:] = value  # until the next basket overwrites it
    end = rows[-1] + 1 + HOLD
    total = curves[:, first + 1:end + 1].sum(axis=0)
    dates = m.dates[first + 2:end + 1]
    return {"dates": dates, "returns": total[1:] / total[:-1] - 1, "trades": trades}

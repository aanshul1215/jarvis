"""Event drift study (docs/10-shortterm/EVENT_DRIFT_STUDY.md): buy liquid stocks after a high-volume jump, hold weeks.

The lane has ``SLOTS`` slots of equal starting size. Each slot holds one trade at a time and earns T-bills while
free. A trade is bought at the open after the event and sold at the open ``hold`` sessions later (or earlier on a
fade exit), all at adjusted prices. Delisting rules are the same as the reversal study's.
"""

from __future__ import annotations

from datetime import date

import numpy as np

from .reversal import Market, lagged_return

SLOTS, HOLD = 20, 20
VARIANTS = {"E1": {"move": 0.04, "volume": 3.0, "hold": 20},
            "E2": {"move": 0.04, "volume": 3.0, "hold": 10},
            "E3": {"move": 0.04, "volume": 3.0, "hold": 20, "trend": True},
            "E4": {"move": 0.06, "volume": 4.0, "hold": 20},
            "E5": {"move": 0.04, "volume": 3.0, "hold": 20, "fade": True}}
EXCESS = 0.03


def volume_ratio(volume: np.ndarray, window: int = 20) -> np.ndarray:
    """Volume over the average of the previous ``window`` sessions (NaN until enough history)."""
    out = np.full(volume.shape, np.nan)
    v = np.where(np.isfinite(volume), volume, np.nan)
    for t in range(window, len(v)):
        base = np.nanmean(v[t - window:t], axis=0)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[t] = v[t] / base
    return out


def events(m: Market, universe: dict[str, list[str]], rows: list[int], spy_close: np.ndarray, spy_up: np.ndarray,
           rule: dict, ratio: np.ndarray) -> dict[int, list[int]]:
    """Stock columns with an event at each decision row t, strongest (return in excess of SPY) first."""
    col = {s: j for j, s in enumerate(m.symbols)}
    r1 = lagged_return(m.close, 1)
    spy_r = np.full(len(spy_close), np.nan)
    spy_r[1:] = spy_close[1:] / spy_close[:-1] - 1
    out = {}
    for t in rows:
        if rule.get("trend") and not spy_up[t]:
            out[t] = []
            continue
        key = f"{m.dates[t].year:04d}-{m.dates[t].month:02d}"
        names = [col[s] for s in universe.get(key, []) if s in col]
        hits = [j for j in names if np.isfinite(r1[t, j]) and r1[t, j] >= rule["move"] and np.isfinite(spy_r[t])
                and r1[t, j] - spy_r[t] >= EXCESS and np.isfinite(ratio[t, j]) and ratio[t, j] >= rule["volume"]
                and m.raw_close[t, j] >= 5 and t + 1 < len(m.dates) and np.isfinite(m.open[t + 1, j])]
        out[t] = sorted(hits, key=lambda j: -(r1[t, j] - spy_r[t]))
    return out


def trade_path(m: Market, j: int, t: int, cost: float, hold: int, fade_level: float | None = None) -> tuple[np.ndarray, bool, int]:
    """Value of $1 bought at open t+1 at each open t+1 .. t+1+hold (flat after an early exit). Returns the path,
    whether the data ended, and the number of sessions actually held."""
    path = np.empty(hold + 1)
    entry = m.open[t + 1, j]
    last, ended, exit_k = entry, False, hold
    for k in range(hold + 1):
        d = t + 1 + k
        if k > exit_k:
            path[k] = path[exit_k]
            continue
        price = m.open[d, j] if d < len(m.dates) else np.nan
        if not np.isfinite(price):
            if d > m.last_row[j]:
                ended = True
                price = 0.0 if j in m.failed_after else m.close[m.last_row[j], j]
            else:
                price = last
        last = price
        path[k] = (1 - cost) * price / entry
        if fade_level is not None and exit_k == hold and k < hold and d < len(m.dates) \
                and np.isfinite(m.close[d, j]) and m.close[d, j] < fade_level:
            exit_k = k + 1  # the jump has been given back: sell at the next open
    path[exit_k] *= 1 - cost
    path[exit_k + 1:] = path[exit_k]
    return path, ended, exit_k


def simulate(m: Market, signals: dict[int, list[int]], costs: np.ndarray, cash_rate: np.ndarray, rule: dict, *,
             cost_multiplier: float = 1.0, slots: int = SLOTS) -> dict:
    """Daily lane returns (open to open) and per-trade records."""
    rows = sorted(signals)
    if not rows:
        return {"dates": [], "returns": np.array([]), "trades": [], "average_slots_used": 0.0}
    hold = rule["hold"]
    value = np.full(slots, 1.0 / slots)
    trade = [None] * slots  # (start open row, starting value, path, column)
    held: set[int] = set()
    trades, curve, used = [], [], []
    first, last = rows[0] + 1, min(rows[-1] + 1 + hold, len(m.dates) - 1)
    for d in range(first, last + 1):
        for s in range(slots):  # trades whose exit open is today finish now
            if trade[s] is not None and d - trade[s][0] >= len(trade[s][2]) - 1:
                start, v0, path, j = trade[s]
                value[s] = v0 * path[-1]
                trade[s] = None
                held.discard(j)
            elif trade[s] is None and d > first:
                value[s] *= 1 + np.nan_to_num(cash_rate[d - 1]) / 252
        t = d - 1
        if t in signals:
            for j in signals[t]:
                free = [s for s in range(slots) if trade[s] is None]
                if not free:
                    break
                if j in held:
                    continue
                cost = (costs[t, j] if costs.ndim == 2 else costs[j]) * cost_multiplier
                fade = m.open[t, j] if rule.get("fade") else None
                path, ended, kept = trade_path(m, j, t, cost, hold, fade)
                s = free[0]
                trade[s] = (d, value[s], path[:kept + 1], j)
                held.add(j)
                trades.append({"decision": m.dates[t], "symbol": m.symbols[j], "net": float(path[kept] - 1),
                               "ended": ended, "failed": ended and j in m.failed_after, "held": kept})
        total = sum(value[s] if trade[s] is None else trade[s][1] * trade[s][2][d - trade[s][0]] for s in range(slots))
        curve.append(total)
        used.append(sum(x is not None for x in trade))
    curve = np.array(curve)
    return {"dates": m.dates[first + 1:last + 1], "returns": curve[1:] / curve[:-1] - 1, "trades": trades,
            "average_slots_used": float(np.mean(used))}

"""The momentum ranker (round 3, v1.2.0): which equities to own, and when to keep them instead of selling.

Replaces round 2's learning ranker (it lost money: its predictions had almost no information, IC +0.017) and the
relative-strength sleeve (the same idea, done less carefully). Design and evidence: docs/09-portfolio/RANKER_DESIGN.md.
The score was validated before use on 89 years of independent data (Kenneth French's 49 US industries, 1927-2015:
mean monthly IC +0.068, t = 8.1, positive in all nine sub-periods).

What it ranks: the 17 equity ETFs, plus a single stock only while it was one of the ten largest US companies at the
previous year-end. That keeps 2026's hindsight (we picked NVIDIA and Tesla because they won) out of the past.

Score (no fitted weights): the average cross-sectional rank of the 3-month, 6-month and 12-1 month returns.

Hold-or-sell, decided at each month start:
- sell a holding when it falls below 9th place, stops being eligible, or its 12-1 month return turns negative;
- buy from the top 4 (positive 12-1 month return only) until 4 names are held, at most 2 new names a month (a full
  rebuild is allowed when nothing is held), and at most 2 names from the big-tech cluster;
- a holding's weight is fixed when it is bought (1 / its volatility then) and kept until it is sold, so the sleeve
  does not trade just because volatilities move; the whole sleeve is then risk-scaled like every other sleeve.
The entry price and unrealised profit or loss are never used (they carry no information about future returns, and
using them is the disposition effect).
"""

from __future__ import annotations

from datetime import date

import numpy as np

from .sleeves import GROUPS, Context, _lag_ratio, risk_scale

ENTER_TOP, HOLD_TOP, MAX_HELD, MAX_NEW_PER_MONTH, MAX_TECH, MIN_NAMES = 4, 9, 4, 2, 2, 10
ETFS = GROUPS["equity_index"] + GROUPS["sector"]
TECH_CLUSTER = ("QQQ", "XLK", "SMH", "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA")

# Which of the universe's single stocks were among the ten largest US companies by market value at each year-end
# (RECALLED; borderline: XOM at end-2018 and JPM at end-2022 were about 10th). A stock is eligible during year Y only
# if it was a member at the end of year Y - 1, which was public information at the time.
TOP10_AT_YEAR_END = {
    2015: ("AAPL", "GOOGL", "MSFT", "XOM", "AMZN", "META"),
    2016: ("AAPL", "GOOGL", "MSFT", "XOM", "AMZN", "META", "JPM"),
    2017: ("AAPL", "GOOGL", "MSFT", "AMZN", "META", "JPM", "XOM"),
    2018: ("MSFT", "AAPL", "AMZN", "GOOGL", "META", "JPM", "XOM"),
    2019: ("AAPL", "MSFT", "GOOGL", "AMZN", "META", "JPM"),
    2020: ("AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA"),
    2021: ("AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "UNH", "JPM"),
    2022: ("AAPL", "MSFT", "GOOGL", "AMZN", "UNH", "XOM", "JPM"),
    2023: ("AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"),
    2024: ("AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "TSLA"),
    2025: ("NVDA", "AAPL", "GOOGL", "MSFT", "AMZN", "META", "TSLA"),
}


def week_starts(dates) -> list[int]:
    """Rows that begin a new trading week (the decision rows of a weekly rebalance)."""
    return [i for i in range(1, len(dates)) if dates[i].isocalendar()[:2] != dates[i - 1].isocalendar()[:2]]


def month_starts(dates) -> list[int]:
    return [i for i in range(1, len(dates)) if (dates[i].year, dates[i].month) != (dates[i - 1].year, dates[i - 1].month)]


def eligible(asset: str, day: date) -> bool:
    if asset in ETFS:
        return True
    if asset in GROUPS["single_stock"]:
        # After the last recorded year-end the latest list is used; it must be extended every January.
        known = [y for y in TOP10_AT_YEAR_END if y <= day.year - 1]
        return bool(known) and asset in TOP10_AT_YEAR_END[max(known)]
    return False


def signals(close: np.ndarray) -> list[np.ndarray]:
    return [_lag_ratio(close, 63), _lag_ratio(close, 126), _lag_ratio(close, 252, skip=21)]


def composite(sig: list[np.ndarray], t: int, cols: list[int]) -> np.ndarray:
    """Average cross-sectional rank (0 = worst, 1 = best) of the signals over ``cols`` at row t."""
    ranks = []
    for s in sig:
        x = s[t, cols]
        ranks.append(np.argsort(np.argsort(x)) / (len(cols) - 1))
    return np.mean(ranks, axis=0)


def ranker(ctx: Context) -> tuple[np.ndarray, dict]:
    """Weights (T, N), risk-scaled, and a small report (decisions, entries, exits, average names held)."""
    raw, report = entry_weights(ctx)
    return risk_scale(ctx, raw), report


def holdings(ctx: Context, **rules) -> tuple[np.ndarray, dict]:
    """(T, N) True where the ranker holds a name (used by the round 5 core)."""
    raw, report = entry_weights(ctx, **rules)
    return raw != 0, report


def entry_weights(ctx: Context, *, universe=None, enter_top: int = ENTER_TOP, hold_top: int = HOLD_TOP,
                  max_held: int = MAX_HELD, max_new: int = MAX_NEW_PER_MONTH,
                  max_tech: int = MAX_TECH) -> tuple[np.ndarray, dict]:
    """Raw weights (1 / volatility, fixed at entry) of the hold-or-sell rule. ``universe`` (asset names) replaces
    the eligibility rule for variants."""
    p = ctx.panel
    t_total, n = p.shape
    sig = signals(p.close)
    mom = sig[2]
    decisions = set(month_starts(p.dates))
    tech = {p.index(a) for a in TECH_CLUSTER if a in p.assets}
    raw = np.zeros((t_total, n))
    held: dict[int, float] = {}  # column -> raw weight fixed at entry
    report = {"decisions": 0, "entries": 0, "exits": 0, "held_rows": 0, "names_held_sum": 0}
    for t in range(t_total):
        if t in decisions:
            cols = [j for j, a in enumerate(p.assets) if (eligible(a, p.dates[t]) if universe is None else a in universe)
                    and all(np.isfinite(s[t, j]) for s in sig) and np.isfinite(ctx.vols[t, j]) and ctx.vols[t, j] > 0]
            if len(cols) < MIN_NAMES:
                report["exits"] += len(held)
                held = {}
            else:
                report["decisions"] += 1
                score = composite(sig, t, cols)
                order = [cols[i] for i in np.argsort(-score, kind="stable")]
                rank = {j: k + 1 for k, j in enumerate(order)}
                for j in list(held):
                    if rank.get(j, 10 ** 6) > hold_top or not mom[t, j] > 0:
                        del held[j]
                        report["exits"] += 1
                rebuild, added = not held, 0
                for j in order[:enter_top]:
                    if len(held) >= max_held or (not rebuild and added >= max_new):
                        break
                    if j in held or not mom[t, j] > 0:
                        continue
                    if j in tech and sum(1 for h in held if h in tech) >= max_tech:
                        continue
                    held[j] = 1.0 / ctx.vols[t, j]
                    added += 1
                    report["entries"] += 1
        for j, w in held.items():
            raw[t, j] = w
        if held:
            report["held_rows"] += 1
            report["names_held_sum"] += len(held)
    report["average_names_held"] = report.pop("names_held_sum") / max(1, report["held_rows"])
    return raw, report

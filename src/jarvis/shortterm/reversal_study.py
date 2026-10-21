"""Run the registered reversal study (docs/10-shortterm/REVERSAL_STUDY.md) and log it once.

Development first: every candidate R1-R5 and the benchmark R0. Then, only for the candidate the registered rule
chooses (if any), the confirmation and the holdout, with R0 and SPY alongside. The later periods of the other
candidates are never computed.
"""

from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from ..contracts import AssetClass, iso, utc_now
from ..macro import load_macro
from ..portfolio.backtest import stats
from ..portfolio.core import known_rate
from ..storage import LocalStorage
from ..timeframes import NEW_YORK
from .reversal import COST_REST, COST_TOP100, TOP, Market, lagged_return, simulate

SPLITS = {"DEVELOPMENT": (date(2016, 2, 1), date(2021, 12, 31)), "CONFIRMATION": (date(2022, 1, 1), date(2023, 12, 31)),
          "HOLDOUT": (date(2024, 1, 1), date(2100, 1, 1))}
CANDIDATES = ("R1", "R2", "R3", "R4", "R5")
VERSION = "reversal-1.0.0"


def month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def cost_matrix(m: Market, universe: dict[str, list[str]]) -> np.ndarray:
    col = {s: j for j, s in enumerate(m.symbols)}
    out = np.full((len(m.dates), len(m.symbols)), COST_REST)
    for t, d in enumerate(m.dates):
        for rank, s in enumerate(universe.get(month_key(d), [])):
            if rank < 100 and s in col:
                out[t, col[s]] = COST_TOP100
    return out


def known_series(dates: list[date], rows: list[dict]) -> np.ndarray:
    """Value known at each date: the latest observation dated before it (published the next day)."""
    obs = sorted((date.fromisoformat(r["observation_date"]), r["value"]) for r in rows if r.get("value") is not None)
    out, k, last = np.full(len(dates), np.nan), 0, None
    for i, d in enumerate(dates):
        while k < len(obs) and obs[k][0] < d:
            last = obs[k][1]
            k += 1
        if last is not None:
            out[i] = last
    return out


def filters(m: Market, store: LocalStorage) -> dict[str, np.ndarray]:
    vix = known_series(m.dates, load_macro(store, "VIXCLS"))
    median = pd.Series(vix).rolling(252, min_periods=200).median().to_numpy()
    spy = {b.start_at.astimezone(NEW_YORK).date(): b.close
           for b in store.load_bars("SPY", AssetClass.EQUITY, dataset="1Day-adjusted")}
    spy_close = pd.Series([spy.get(d, np.nan) for d in m.dates]).ffill()
    sma = spy_close.rolling(200, min_periods=200).mean()
    return {"vix_high": np.nan_to_num(vix) >= np.where(np.isfinite(median), median, np.inf),
            "spy_up": (spy_close > sma).to_numpy(), "spy_close": spy_close.to_numpy()}


def select(m: Market, universe: dict[str, list[str]], variant: str, rows: list[int], f: dict) -> dict[int, list[int]]:
    col = {s: j for j, s in enumerate(m.symbols)}
    r5, r1 = lagged_return(m.close, 5), lagged_return(m.close, 1)
    out = {}
    for t in rows:
        if (variant == "R3" and not f["vix_high"][t]) or (variant == "R4" and not f["spy_up"][t]):
            out[t] = []
            continue
        names = [col[s] for s in universe.get(month_key(m.dates[t]), []) if s in col]
        score = r1 if variant == "R2" else r5
        ok = [j for j in names if np.isfinite(score[t, j]) and m.raw_close[t, j] >= 5 and t + 1 < len(m.dates)
              and np.isfinite(m.open[t + 1, j]) and not (variant == "R5" and score[t, j] < -0.25)]
        out[t] = sorted(ok, key=lambda j: score[t, j])[:TOP]
    return out


def equal_weight(m: Market, universe: dict[str, list[str]], costs: np.ndarray, rows: list[int]) -> dict:
    """R0: the month's universe, equal weight, bought at the first open of the month and held to the next."""
    col = {s: j for j, s in enumerate(m.symbols)}
    value, dates, rets = 1.0, [], []
    starts = [t for t in rows if t == rows[0] or month_key(m.dates[t]) != month_key(m.dates[t - 1])]
    for a, b in zip(starts, starts[1:] + [rows[-1]]):
        names = [col[s] for s in universe.get(month_key(m.dates[a]), []) if s in col and np.isfinite(m.open[a, col[s]])]
        length = b - a
        if not names or length <= 0:
            continue
        paths = []
        for j in names:
            p, _ = _hold_path(m, j, a, length, costs[a, j])
            paths.append(p)
        basket = np.mean(paths, axis=0)
        for k in range(1, length + 1):
            dates.append(m.dates[a + k])
            rets.append(basket[k] / basket[k - 1] - 1)
        value *= basket[-1]
    return {"dates": dates, "returns": np.array(rets)}


def _hold_path(m: Market, j: int, a: int, length: int, cost: float) -> tuple[np.ndarray, bool]:
    path, entry, last, ended = np.empty(length + 1), m.open[a, j], m.open[a, j], False
    for k in range(length + 1):
        d = a + k
        price = m.open[d, j] if d < len(m.dates) else np.nan
        if not np.isfinite(price):
            if d > m.last_row[j]:
                ended = True
                price = 0.0 if j in m.failed_after else m.close[m.last_row[j], j]
            else:
                price = last
        last = price
        path[k] = (1 - cost) * price / entry
    path[-1] *= 1 - cost
    return path, ended


def summary(run: dict, first: date, last: date, rates_by_date: dict) -> dict:
    keep = [i for i, d in enumerate(run["dates"]) if first <= d <= last]
    if len(keep) < 2:
        return {"days": len(keep)}
    dates = [run["dates"][i] for i in keep]
    r = run["returns"][keep]
    s = stats(dates, r)
    excess = r - np.array([np.nan_to_num(rates_by_date.get(d, 0.0)) / 252 for d in dates])
    s["sharpe_above_tbills"] = float(excess.mean() / excess.std(ddof=1) * math.sqrt(252)) if excess.std() > 0 else None
    trades = [x for x in run.get("trades", []) if first <= x["decision"] <= last]
    if trades:
        net = np.array([x["net"] for x in trades])
        years = max((min(last, dates[-1]) - first).days, 1) / 365.25
        s.update({"trades": len(trades), "trades_per_year": len(trades) / years, "average_net_per_trade": float(net.mean()),
                  "win_rate": float((net > 0).mean()), "data_ended_exits": sum(x["ended"] for x in trades),
                  "known_failure_exits": sum(x["failed"] for x in trades)})
    return s


def run_study(home: Path, store: LocalStorage, m: Market, universe: dict[str, list[str]]) -> dict:
    from ..studies import StudyRegistry

    registry = StudyRegistry(Path(home))
    registry.path = Path(home) / "research" / "shortterm_studies.jsonl"
    if any(r.get("version") == VERSION for r in registry.records()):
        raise PermissionError(f"{VERSION} has already been run; the registered study runs once")
    f = filters(m, store)
    tbill = {row["observation_date"]: row["value"] for row in load_macro(store, "DTB3")}
    rates = known_rate(m.dates, tbill)
    by_date = dict(zip(m.dates, rates))
    costs = cost_matrix(m, universe)
    first, last = SPLITS["DEVELOPMENT"]
    dev_rows = [t for t, d in enumerate(m.dates) if first <= d <= last and t >= 5]
    dev = {"R0": summary(equal_weight(m, universe, costs, dev_rows), first, last, by_date)}
    dev_runs = {}
    for v in CANDIDATES:
        baskets = select(m, universe, v, dev_rows, f)
        run = simulate(m, baskets, costs, rates)
        doubled = simulate(m, baskets, costs, rates, cost_multiplier=2.0)
        dev[v] = summary(run, first, last, by_date)
        dev[v]["double_costs"] = summary(doubled, first, last, by_date)
        dev_runs[v] = baskets
    r0 = dev["R0"]
    passed = [v for v in CANDIDATES if (dev[v].get("sharpe_above_tbills") or -9) >= (r0.get("sharpe_above_tbills") or 9) + 0.20
              and dev[v].get("max_drawdown", -1) >= r0.get("max_drawdown", 0)
              and dev[v]["double_costs"].get("average_net_per_trade", -1) > 0]
    chosen = max(passed, key=lambda v: dev[v]["sharpe_above_tbills"]) if passed else None
    later = {}
    if chosen:
        for split in ("CONFIRMATION", "HOLDOUT"):
            a, b = SPLITS[split]
            rows = [t for t, d in enumerate(m.dates) if a <= d <= b and t >= 5]
            baskets = select(m, universe, chosen, rows, f)
            later[split] = {chosen: summary(simulate(m, baskets, costs, rates), a, b, by_date),
                            "R0": summary(equal_weight(m, universe, costs, rows), a, b, by_date)}
            later[split][chosen]["double_costs"] = summary(simulate(m, baskets, costs, rates, cost_multiplier=2.0), a, b, by_date)
            r0s, cs = later[split]["R0"], later[split][chosen]
            later[split]["passed"] = bool((cs.get("sharpe_above_tbills") or -9) >= (r0s.get("sharpe_above_tbills") or 9)
                                          and cs.get("max_drawdown", -1) >= -0.25)
    record = {"created_at": iso(utc_now()), "version": VERSION, "spec": {"study": "short_term_reversal", "split": "ALL"},
              "status": "COMPLETED", "data_last_date": m.dates[-1].isoformat(), "development": dev,
              "passed_development": passed, "chosen": chosen, "later": later}
    return registry.append(json.loads(json.dumps(record, default=str)))


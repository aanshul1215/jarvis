"""Intraday momentum study (docs/10-shortterm/INTRADAY_MOMENTUM_STUDY.md): first half-hour -> last half-hour."""

from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from ..contracts import iso, utc_now
from ..macro import load_macro
from ..portfolio.backtest import stats
from ..portfolio.core import known_rate
from ..storage import LocalStorage

SPLITS = {"DEVELOPMENT": (date(2016, 2, 1), date(2021, 12, 31)), "CONFIRMATION": (date(2022, 1, 1), date(2023, 12, 31)),
          "HOLDOUT": (date(2024, 1, 1), date(2100, 1, 1))}
COST_INDEX, COST_STOCK = 0.0001, 0.0003
VERSION = "intraday-momentum-1.0.0"


def daily_table(bars: pd.DataFrame) -> pd.DataFrame:
    """One row per (symbol, session): first half-hour return, twelfth half-hour return, last half-hour open/close."""
    ny = bars["timestamp"].dt.tz_convert("America/New_York")
    b = bars.assign(day=ny.dt.date, slot=ny.dt.strftime("%H:%M"))
    first = b[b["slot"] == "09:30"].set_index(["symbol", "day"])["close"].rename("first_close")
    twelfth = b[b["slot"] == "15:00"].set_index(["symbol", "day"])
    last = b[b["slot"] == "15:30"].set_index(["symbol", "day"])
    out = pd.concat([first, (twelfth["close"] / twelfth["open"] - 1).rename("r12"),
                     last["open"].rename("last_open"), last["close"].rename("last_close")], axis=1).reset_index()
    out = out.sort_values(["symbol", "day"])
    out["prev_close"] = out.groupby("symbol")["last_close"].shift(1)
    out["r_first"] = out["first_close"] / out["prev_close"] - 1
    out["r_last"] = out["last_close"] / out["last_open"] - 1
    return out


def strategy_returns(table: pd.DataFrame, variant: str, top50: dict[str, list[str]], days: list[date],
                     cost_multiplier: float = 1.0) -> tuple[dict[date, float], list[float]]:
    """{day: net return of the traded half-hour (0 if not traded)} and the list of per-trade net returns."""
    out, trades = {}, []
    if variant in ("I0", "I1", "I4", "I5"):
        t = table[table["symbol"] == "SPY"].set_index("day")
    elif variant == "I2":
        t = table[table["symbol"] == "QQQ"].set_index("day")
    else:
        t = None
    if t is not None:
        t = t[["r_first", "r12", "r_last"]].dropna(subset=["r_first", "r_last"])
        median = t["r_first"].abs().shift(1).rolling(60, min_periods=60).median()
        cost = 2 * COST_INDEX * cost_multiplier
        for d in days:
            if d not in t.index:
                continue
            row = t.loc[d]
            go = {"I0": True, "I1": row["r_first"] > 0, "I2": row["r_first"] > 0,
                  "I4": row["r_first"] > 0 and np.isfinite(median.get(d, np.nan)) and abs(row["r_first"]) > median[d],
                  "I5": row["r_first"] > 0 and np.isfinite(row["r12"]) and row["r12"] > 0}[variant]
            if go:
                net = (1 + row["r_last"]) * (1 - COST_INDEX * cost_multiplier) ** 2 - 1
                out[d] = float(net)
                trades.append(float(net))
        return out, trades
    stocks = table.dropna(subset=["r_first", "r_last"]).set_index(["day", "symbol"])
    by_day = {d: g for d, g in stocks.reset_index().groupby("day")}
    for d in days:
        names = set(top50.get(f"{d.year:04d}-{d.month:02d}", []))
        g = by_day.get(d)
        if g is None:
            continue
        g = g[g["symbol"].isin(names) & (g["r_first"] > 0)]
        if len(g):
            net = (1 + g["r_last"]) * (1 - COST_STOCK * cost_multiplier) ** 2 - 1
            out[d] = float(net.mean())
            trades += net.tolist()
    return out, trades


def summarise(daily: dict[date, float], trades: list[float], days: list[date], rates_by_date: dict) -> dict:
    cash = np.array([np.nan_to_num(rates_by_date.get(d, 0.0)) / 252 for d in days])
    r = np.array([daily.get(d, 0.0) for d in days]) + cash
    s = stats(days, r)
    excess = r - cash
    s["sharpe_above_tbills"] = float(excess.mean() / excess.std(ddof=1) * math.sqrt(252)) if excess.std() > 0 else None
    years = max((days[-1] - days[0]).days, 1) / 365.25
    t = np.array(trades) if trades else np.array([0.0])
    s.update({"trades_per_year": len(trades) / years, "average_net_per_trade": float(t.mean()),
              "hit_rate": float((t > 0).mean()), "share_of_days_traded": len(daily) / len(days)})
    return s


def run_study(home: Path, store: LocalStorage, bars: pd.DataFrame, top50: dict[str, list[str]]) -> dict:
    from ..studies import StudyRegistry

    registry = StudyRegistry(Path(home))
    registry.path = Path(home) / "research" / "shortterm_studies.jsonl"
    if any(r.get("version") == VERSION for r in registry.records()):
        raise PermissionError(f"{VERSION} has already been run; the registered study runs once")
    table = daily_table(bars)
    sessions = sorted(table.loc[table["symbol"] == "SPY", "day"].unique())
    rates = known_rate(sessions, {row["observation_date"]: row["value"] for row in load_macro(store, "DTB3")})
    by_date = dict(zip(sessions, rates))

    def period(split):
        a, b = SPLITS[split]
        return [d for d in sessions if a <= d <= b]

    dev_days = period("DEVELOPMENT")
    dev = {}
    for v in ("I0", "I1", "I2", "I3", "I4", "I5"):
        daily, trades = strategy_returns(table, v, top50, dev_days)
        dev[v] = summarise(daily, trades, dev_days, by_date)
        d2, t2 = strategy_returns(table, v, top50, dev_days, 2.0)
        dev[v]["double_costs"] = summarise(d2, t2, dev_days, by_date)
    base = dev["I0"].get("sharpe_above_tbills") or 0.0
    passed = [v for v in ("I1", "I2", "I3", "I4", "I5")
              if (dev[v].get("sharpe_above_tbills") or -9) >= max(base + 0.20, 0.50)
              and dev[v]["double_costs"]["average_net_per_trade"] > 0]
    chosen = max(passed, key=lambda v: dev[v]["sharpe_above_tbills"]) if passed else None
    later = {}
    if chosen:
        for split in ("CONFIRMATION", "HOLDOUT"):
            days = period(split)
            res = {}
            for v in (chosen, "I0"):
                daily, trades = strategy_returns(table, v, top50, days)
                res[v] = summarise(daily, trades, days, by_date)
            c = res[chosen]
            res["passed"] = bool((c.get("sharpe_above_tbills") or -9) >= max(0.5, (res["I0"].get("sharpe_above_tbills") or 0) + 1e-9)
                                 and c["max_drawdown"] >= -0.25)
            later[split] = res
    record = {"created_at": iso(utc_now()), "version": VERSION, "spec": {"study": "intraday_momentum", "split": "ALL"},
              "status": "COMPLETED", "data_last_date": str(sessions[-1]), "development": dev, "passed_development": passed,
              "chosen": chosen, "later": later}
    return registry.append(json.loads(json.dumps(record, default=str)))

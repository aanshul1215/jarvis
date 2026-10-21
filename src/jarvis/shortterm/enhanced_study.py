"""Run the registered enhanced-index study (docs/10-shortterm/ENHANCED_INDEX_STUDY.md) once and log it."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ..contracts import iso, utc_now
from ..macro import load_macro
from ..portfolio.core import known_rate
from ..storage import LocalStorage
from .book import DEFENSIVE, SAFE, combine, cost_table, load_etfs, simulate
from .book_study import SPLITS
from .enhanced import BAND, BAND_REL, targets
from .reversal import Market
from .reversal_study import cost_matrix, equal_weight, summary

VERSION = "enhanced-index-1.0.0"
VERSION_V2 = "enhanced-index-2.0.0"  # study 7: 80% stocks + 20% defensive sleeve


def run_study(home: Path, store: LocalStorage, m: Market, universe: dict[str, list[str]], groups: dict[str, str]) -> dict:
    from ..studies import StudyRegistry

    registry = StudyRegistry(Path(home))
    registry.path = Path(home) / "research" / "shortterm_studies.jsonl"
    if any(r.get("version") == VERSION for r in registry.records()):
        raise PermissionError(f"{VERSION} has already been run; the registered study runs once")
    etfs = load_etfs(store, m.dates, DEFENSIVE + (SAFE, "SPY"))
    inst = combine(m, etfs)
    spy_open, spy_close = etfs["SPY"]
    rates = known_rate(m.dates, {row["observation_date"]: row["value"] for row in load_macro(store, "DTB3")})
    by_date = dict(zip(m.dates, rates))
    costs = cost_table(inst, m, universe)
    stock_costs = cost_matrix(m, universe)

    def rows_of(split):
        a, b = SPLITS[split]
        return [t for t, d in enumerate(m.dates) if a <= d <= b]

    def book(split, *, tilt=True, switch=True, multiplier=1.0):
        rows = rows_of(split)
        decided, report = targets(inst, m, universe, groups, spy_close, rates, rows, tilt=tilt, switch=switch)
        run = simulate(inst, decided, costs, rates, cost_multiplier=multiplier, band=BAND, band_rel=BAND_REL)
        a, b = SPLITS[split]
        s = summary(run, a, b, by_date)
        years = max((min(b, run["dates"][-1]) - a).days, 1) / 365.25
        s.update({"annual_turnover": float(run["turnover"].sum() / years), "data_ended_exits": run["data_ended_exits"],
                  **report})
        return s

    def benchmarks(split):
        rows = rows_of(split)
        a, b = SPLITS[split]
        spy_rows = [t for t in rows if t + 1 < len(m.dates) and np.isfinite(spy_open[t]) and np.isfinite(spy_open[t + 1])]
        spy = {"dates": [m.dates[t + 1] for t in spy_rows],
               "returns": np.array([spy_open[t + 1] / spy_open[t] - 1 for t in spy_rows])}
        return {"R0": summary(equal_weight(m, universe, stock_costs, rows), a, b, by_date),
                "C0": book(split, tilt=False, switch=False), "SPY": summary(spy, a, b, by_date)}

    def evaluate(split):
        res = {"X1": book(split), **benchmarks(split)}
        res["X1"]["double_costs"] = book(split, multiplier=2.0)
        return res

    dev = evaluate("DEVELOPMENT")
    x, r0 = dev["X1"], dev["R0"]
    passed = bool((x.get("sharpe_above_tbills") or -9) >= (r0.get("sharpe_above_tbills") or 9) + 0.10
                  and x.get("cagr", -1) > r0.get("cagr", 9)
                  and (x["double_costs"].get("sharpe_above_tbills") or -9) >= (r0.get("sharpe_above_tbills") or 9)
                  and x["double_costs"].get("cagr", -1) >= r0.get("cagr", 9))
    later = {}
    if passed:
        for split in ("CONFIRMATION", "HOLDOUT"):
            res = evaluate(split)
            xs, rs = res["X1"], res["R0"]
            res["passed"] = bool((xs.get("sharpe_above_tbills") or -9) >= (rs.get("sharpe_above_tbills") or 9)
                                 and xs.get("cagr", -1) >= rs.get("cagr", 9) and xs.get("max_drawdown", -1) >= -0.25)
            later[split] = res
    record = {"created_at": iso(utc_now()), "version": VERSION, "spec": {"study": "enhanced_index", "split": "ALL"},
              "status": "COMPLETED", "data_last_date": m.dates[-1].isoformat(), "development": dev,
              "passed_development": passed, "later": later}
    return registry.append(json.loads(json.dumps(record, default=str)))


def run_study_v2(home: Path, store: LocalStorage, m: Market, universe: dict[str, list[str]], groups: dict[str, str]) -> dict:
    """Study 7 (docs/10-shortterm/ENHANCED_INDEX_V2_STUDY.md), once."""
    from ..studies import StudyRegistry

    registry = StudyRegistry(Path(home))
    registry.path = Path(home) / "research" / "shortterm_studies.jsonl"
    if any(r.get("version") == VERSION_V2 for r in registry.records()):
        raise PermissionError(f"{VERSION_V2} has already been run; the registered study runs once")
    etfs = load_etfs(store, m.dates, DEFENSIVE + (SAFE, "SPY"))
    inst = combine(m, etfs)
    spy_open, spy_close = etfs["SPY"]
    rates = known_rate(m.dates, {row["observation_date"]: row["value"] for row in load_macro(store, "DTB3")})
    by_date = dict(zip(m.dates, rates))
    costs = cost_table(inst, m, universe)
    stock_costs = cost_matrix(m, universe)

    def rows_of(split):
        a, b = SPLITS[split]
        return [t for t, d in enumerate(m.dates) if a <= d <= b]

    def book(split, *, tilt=True, sleeve=0.20, multiplier=1.0):
        rows = rows_of(split)
        decided, report = targets(inst, m, universe, groups, spy_close, rates, rows, tilt=tilt, switch=False, sleeve=sleeve)
        run = simulate(inst, decided, costs, rates, cost_multiplier=multiplier, band=BAND, band_rel=BAND_REL)
        a, b = SPLITS[split]
        s = summary(run, a, b, by_date)
        years = max((min(b, run["dates"][-1]) - a).days, 1) / 365.25
        s.update({"annual_turnover": float(run["turnover"].sum() / years), "data_ended_exits": run["data_ended_exits"],
                  **report})
        return s

    def evaluate(split):
        rows = rows_of(split)
        a, b = SPLITS[split]
        spy_rows = [t for t in rows if t + 1 < len(m.dates) and np.isfinite(spy_open[t]) and np.isfinite(spy_open[t + 1])]
        spy = {"dates": [m.dates[t + 1] for t in spy_rows],
               "returns": np.array([spy_open[t + 1] / spy_open[t] - 1 for t in spy_rows])}
        res = {"X2": book(split), "R0": summary(equal_weight(m, universe, stock_costs, rows), a, b, by_date),
               "C0": book(split, tilt=False, sleeve=0.0), "SPY": summary(spy, a, b, by_date)}
        res["X2"]["double_costs"] = book(split, multiplier=2.0)
        return res

    dev = evaluate("DEVELOPMENT")
    x, r0 = dev["X2"], dev["R0"]
    r0_sharpe = r0.get("sharpe_above_tbills") or 9
    passed = bool((x.get("sharpe_above_tbills") or -9) >= r0_sharpe + 0.10
                  and x.get("max_drawdown", -1) > r0.get("max_drawdown", 0)
                  and (x["double_costs"].get("sharpe_above_tbills") or -9) >= r0_sharpe)
    later = {}
    if passed:
        for split in ("CONFIRMATION", "HOLDOUT"):
            res = evaluate(split)
            xs, rs = res["X2"], res["R0"]
            res["passed"] = bool((xs.get("sharpe_above_tbills") or -9) >= (rs.get("sharpe_above_tbills") or 9)
                                 and xs.get("max_drawdown", -1) >= max(-0.25, rs.get("max_drawdown", -1)))
            later[split] = res
    record = {"created_at": iso(utc_now()), "version": VERSION_V2, "spec": {"study": "enhanced_index_v2", "split": "ALL"},
              "status": "COMPLETED", "data_last_date": m.dates[-1].isoformat(), "development": dev,
              "passed_development": passed, "later": later}
    return registry.append(json.loads(json.dumps(record, default=str)))

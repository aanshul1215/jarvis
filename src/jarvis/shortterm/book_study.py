"""Run the registered stock book study (docs/10-shortterm/STOCK_BOOK_STUDY.md) once and log it."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np

from ..contracts import iso, utc_now
from ..macro import load_macro
from ..portfolio.core import known_rate
from ..storage import LocalStorage
from .book import DEFENSIVE, SAFE, cost_table, combine, load_etfs, simulate, targets
from .reversal import Market
from .reversal_study import cost_matrix, equal_weight, summary

SPLITS = {"DEVELOPMENT": (date(2017, 1, 3), date(2021, 12, 31)), "CONFIRMATION": (date(2022, 1, 1), date(2023, 12, 31)),
          "HOLDOUT": (date(2024, 1, 1), date(2100, 1, 1))}
VERSION = "stock-book-1.0.0"


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

    def book(variant, split, multiplier=1.0):
        rows = rows_of(split)
        decided, report = targets(inst, m, universe, groups, spy_close, rates, rows, variant)
        run = simulate(inst, decided, costs, rates, cost_multiplier=multiplier)
        a, b = SPLITS[split]
        s = summary(run, a, b, by_date)
        years = max((min(b, run["dates"][-1]) - a).days, 1) / 365.25
        s.update({"annual_turnover": float(run["turnover"].sum() / years), "data_ended_exits": run["data_ended_exits"],
                  **report})
        return s

    def benchmarks(split):
        rows = rows_of(split)
        a, b = SPLITS[split]
        r0 = summary(equal_weight(m, universe, stock_costs, rows), a, b, by_date)
        spy_rows = [t for t in rows if t + 1 < len(m.dates) and np.isfinite(spy_open[t]) and np.isfinite(spy_open[t + 1])]
        spy = {"dates": [m.dates[t + 1] for t in spy_rows],
               "returns": np.array([spy_open[t + 1] / spy_open[t] - 1 for t in spy_rows])}
        return {"R0": r0, "SPY": summary(spy, a, b, by_date)}

    dev = {"B1": book("B1", "DEVELOPMENT"), **benchmarks("DEVELOPMENT")}
    dev["B1"]["double_costs"] = book("B1", "DEVELOPMENT", 2.0)
    ablations = {v: book(v, "DEVELOPMENT") for v in ("A1", "A2", "A3", "A4")}
    r0 = dev["R0"].get("sharpe_above_tbills") or 9
    b1 = dev["B1"]
    passed = bool((b1.get("sharpe_above_tbills") or -9) >= r0 + 0.20
                  and b1.get("max_drawdown", -1) >= dev["R0"].get("max_drawdown", 0)
                  and (b1["double_costs"].get("sharpe_above_tbills") or -9) >= r0)
    later = {}
    if passed:
        for split in ("CONFIRMATION", "HOLDOUT"):
            res = {"B1": book("B1", split), **benchmarks(split)}
            res["B1"]["double_costs"] = book("B1", split, 2.0)
            res["passed"] = bool((res["B1"].get("sharpe_above_tbills") or -9) >= (res["R0"].get("sharpe_above_tbills") or 9)
                                 and res["B1"].get("max_drawdown", -1) >= -0.25)
            later[split] = res
    record = {"created_at": iso(utc_now()), "version": VERSION, "spec": {"study": "stock_book", "split": "ALL"},
              "status": "COMPLETED", "data_last_date": m.dates[-1].isoformat(), "development": dev,
              "ablations_development_only": ablations, "passed_development": passed, "later": later}
    return registry.append(json.loads(json.dumps(record, default=str)))

"""Run the registered event drift study (docs/10-shortterm/EVENT_DRIFT_STUDY.md) once and log it."""

from __future__ import annotations

import json
from pathlib import Path

from ..contracts import iso, utc_now
from ..macro import load_macro
from ..portfolio.core import known_rate
from ..storage import LocalStorage
from .events import VARIANTS, events, simulate, volume_ratio
from .reversal import Market
from .reversal_study import SPLITS, cost_matrix, equal_weight, filters, summary

VERSION = "event-drift-1.0.0"


def _summary(run: dict, first, last, by_date) -> dict:
    s = summary(run, first, last, by_date)
    s["average_slots_used"] = run.get("average_slots_used")
    return s


def run_study(home: Path, store: LocalStorage, m: Market, universe: dict[str, list[str]]) -> dict:
    from ..studies import StudyRegistry

    registry = StudyRegistry(Path(home))
    registry.path = Path(home) / "research" / "shortterm_studies.jsonl"
    if any(r.get("version") == VERSION for r in registry.records()):
        raise PermissionError(f"{VERSION} has already been run; the registered study runs once")
    f = filters(m, store)
    rates = known_rate(m.dates, {row["observation_date"]: row["value"] for row in load_macro(store, "DTB3")})
    by_date = dict(zip(m.dates, rates))
    costs = cost_matrix(m, universe)
    ratio = volume_ratio(m.volume)

    def run(variant, a, b, multiplier=1.0):
        rows = [t for t, d in enumerate(m.dates) if a <= d <= b and t >= 21]
        signals = events(m, universe, rows, f["spy_close"], f["spy_up"], VARIANTS[variant], ratio)
        return simulate(m, signals, costs, rates, VARIANTS[variant], cost_multiplier=multiplier), rows

    first, last = SPLITS["DEVELOPMENT"]
    dev = {}
    for v in VARIANTS:
        result, rows = run(v, first, last)
        dev[v] = _summary(result, first, last, by_date)
        dev[v]["double_costs"] = _summary(run(v, first, last, 2.0)[0], first, last, by_date)
    dev["E0"] = summary(equal_weight(m, universe, costs, rows), first, last, by_date)
    e0 = dev["E0"]
    passed = [v for v in VARIANTS if (dev[v].get("sharpe_above_tbills") or -9) >= (e0.get("sharpe_above_tbills") or 9) + 0.20
              and dev[v].get("max_drawdown", -1) >= e0.get("max_drawdown", 0)
              and dev[v]["double_costs"].get("average_net_per_trade", -1) > 0]
    chosen = max(passed, key=lambda v: dev[v]["sharpe_above_tbills"]) if passed else None
    later = {}
    if chosen:
        for split in ("CONFIRMATION", "HOLDOUT"):
            a, b = SPLITS[split]
            result, rows = run(chosen, a, b)
            later[split] = {chosen: _summary(result, a, b, by_date),
                            "E0": summary(equal_weight(m, universe, costs, rows), a, b, by_date)}
            later[split][chosen]["double_costs"] = _summary(run(chosen, a, b, 2.0)[0], a, b, by_date)
            c, e = later[split][chosen], later[split]["E0"]
            later[split]["passed"] = bool((c.get("sharpe_above_tbills") or -9) >= (e.get("sharpe_above_tbills") or 9)
                                          and c.get("max_drawdown", -1) >= -0.25)
    record = {"created_at": iso(utc_now()), "version": VERSION, "spec": {"study": "event_drift", "split": "ALL"},
              "status": "COMPLETED", "data_last_date": m.dates[-1].isoformat(), "development": dev,
              "passed_development": passed, "chosen": chosen, "later": later}
    return registry.append(json.loads(json.dumps(record, default=str)))

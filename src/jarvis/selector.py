"""Strategy selector (Phase 7): decide how much of each strategy to run, and test whether that beats not choosing.

Pipeline (pre-registered in docs/08-selector/SELECTOR_REGISTER.md):

1. **Sleeves.** Each strategy is replayed alone through the real trading code. Its daily returns and its completed
   trades (entry features, exit time, net return) are the evidence the selector learns from.
2. **Allocation schedule.** At each month start, a selector turns the sleeves' history *before that date* into a size
   multiplier per strategy (1 = base size, 0 = no new entries, at most ``MAX_MULTIPLIER``). An allocator is handed
   only the truncated history, so it cannot see later data.
3. **Combined replay.** All strategies trade together through the real code (one position per asset, Governor, costs)
   with the multipliers applied to new entries: the same mechanism the paper desk uses.
4. **Chain of stages**, each kept only if it beats the best version so far (the plan's Phase 7):
   equal weight (baseline) -> regime lookup -> meta-labelling filter -> contextual bandit.

A stage passes only with a block-bootstrap p-value below 0.05 / 3 for its daily excess return over the incumbent,
a smaller maximum drawdown, a positive excess when every cost is doubled, and no stopped run. If nothing passes, the
system runs the equal-weight blend, which the workflow calls a legitimate outcome. The holdout does not repeat the
chain: it tests only the configuration development selected, against equal weight, once, at p < 0.05.
"""

from __future__ import annotations

import bisect
import hashlib
from dataclasses import replace
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Callable

import numpy as np

from .contracts import AssetClass, iso, parse_utc, utc_now
from .metrics import block_bootstrap_pvalue
from .regime import static_labels
from .storage import LocalStorage, _canonical, _hash
from .timeframes import NEW_YORK
from .volatility import DEVELOPMENT_END, HOLDOUT_START, bar_returns

SELECTOR_VERSION = "1.0.0"
ALPHA, STAGES = 0.05, ("regime_lookup", "meta_label", "bandit")
MIN_HISTORY_DAYS = 252        # sleeve days before any selector may deviate from equal weight
MIN_REGIME_DAYS = 60          # in-regime days a strategy needs before regime lookup judges it
MAX_MULTIPLIER = 2.0          # a selected strategy runs at most twice its base size (then the Governor's caps)
MIN_BANDIT_MONTHS = 12
BANDIT_PRIOR_SD, BANDIT_SAMPLES = 0.05, 2000
META_FEATURES = ("ret_20", "ret_60", "rsi_14", "dist_sma_200", "volatility_ratio_20_252", "atr_14_pct",
                 "relative_volume", "dist_high_252")
META_MIN_TRADES, META_MIN_CLASS, META_THRESHOLD = 50, 10, 0.5
META_PURGE = timedelta(days=7)  # a trade is learnable only once its exit was decided at least this long ago


# --- evidence ------------------------------------------------------------------------------------------------------

def sleeve_returns(series: list[tuple[date, float]]) -> list[tuple[date, float]]:
    """Daily returns of an equity curve, each dated by the day it was earned."""
    return [(series[i][0], series[i][1] / series[i - 1][1] - 1) for i in range(1, len(series)) if series[i - 1][1] > 0]


def market_labels(store: LocalStorage, proxy: tuple[str, AssetClass], dataset: str) -> dict[date, int]:
    """Trend/volatility label of the market proxy at each close (0 down-calm, 1 down-volatile, 2 up-calm,
    3 up-volatile). The Phase 5 regime study found no predictive gain; Phase 7 tests the label for choosing."""
    bars = store.load_bars(proxy[0], proxy[1], dataset=dataset)
    if len(bars) < 300:
        return {}
    r, _, closes = bar_returns(bars)
    labels = static_labels("trend_vol", r, closes, None)
    # Dated by the New York day on which each label became known (a crypto daily bar can finish after midnight UTC).
    known = [b.available_at.astimezone(NEW_YORK).date() for b in bars[1:]]
    return {d: int(v) for d, v in zip(known, labels) if v >= 0}


def month_starts(start: datetime, end: datetime) -> list[datetime]:
    """Midnight New York time on the first day of each month in [start, end], as UTC."""
    out, year, month = [], start.astimezone(NEW_YORK).year, start.astimezone(NEW_YORK).month
    while True:
        moment = datetime(year, month, 1, tzinfo=NEW_YORK).astimezone(timezone.utc)
        if moment > end:
            return out
        if moment >= start:
            out.append(moment)
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)


def _before(history: dict[str, list[tuple[date, float]]], day: date) -> dict[str, list[tuple[date, float]]]:
    return {s: [(d, r) for d, r in rows if d < day] for s, rows in history.items()}


def _label_before(labels: dict[date, int], day: date) -> int | None:
    days = sorted(d for d in labels if d < day)
    return labels[days[-1]] if days else None


# --- allocators: each sees only history dated before ``day`` --------------------------------------------------------

def equal_weight(strategies, history, labels, day, rng) -> dict[str, float]:
    return {s: 1 / len(strategies) for s in strategies}


def regime_lookup(strategies, history, labels, day, rng) -> dict[str, float]:
    """Hold the strategies whose past average daily return in the current market regime was positive, equally;
    nothing selected means no new entries (cash)."""
    if max((len(v) for v in history.values()), default=0) < MIN_HISTORY_DAYS:
        return equal_weight(strategies, history, labels, day, rng)
    current = _label_before(labels, day)
    if current is None:
        return equal_weight(strategies, history, labels, day, rng)
    known = sorted(labels)
    chosen = []
    for s in strategies:
        # Each day's return is paired with the label known before that day, as the label is used: predictively.
        in_regime = [r for d, r in history.get(s, [])
                     if (i := bisect.bisect_left(known, d) - 1) >= 0 and labels[known[i]] == current]
        if len(in_regime) >= MIN_REGIME_DAYS and np.mean(in_regime) > 0:
            chosen.append(s)
    return {s: (1 / len(chosen) if s in chosen else 0.0) for s in strategies}


def _context(label: int | None) -> np.ndarray:
    trend, vol = (label // 2, label % 2) if label is not None else (0.5, 0.5)
    return np.array([1.0, trend, vol])


def bandit(strategies, history, labels, day, rng) -> dict[str, float]:
    """Contextual Thompson sampling. Each strategy's monthly return is modelled as Bayesian linear regression on the
    market context (constant, trend, volatility state) at the month's start. Weight = the share of posterior draws
    in which the strategy has the best expected return and that return is positive; the rest stays in cash."""
    months: dict[tuple[int, int], dict[str, float]] = {}
    for s, rows in history.items():
        for d, r in rows:
            months.setdefault((d.year, d.month), {}).setdefault(s, 0.0)
            months[(d.year, d.month)][s] += r
    keys = sorted(months)
    if len(keys) < MIN_BANDIT_MONTHS:
        return equal_weight(strategies, history, labels, day, rng)
    x_now = _context(_label_before(labels, day))
    draws = []
    for s in strategies:
        rows = [(_context(_label_before(labels, date(y, m, 1))), months[(y, m)][s]) for y, m in keys if s in months[(y, m)]]
        if len(rows) < MIN_BANDIT_MONTHS:
            draws.append(np.full(BANDIT_SAMPLES, -np.inf))
            continue
        x = np.vstack([c for c, _ in rows])
        y = np.array([v for _, v in rows])
        noise = max(float(np.var(y)), 1e-8)
        precision = x.T @ x / noise + np.eye(3) / BANDIT_PRIOR_SD ** 2
        cov = np.linalg.inv(precision)
        mean = cov @ x.T @ y / noise
        draws.append(rng.multivariate_normal(mean, (cov + cov.T) / 2, BANDIT_SAMPLES) @ x_now)
    draws = np.column_stack(draws)
    best = np.argmax(draws, axis=1)
    positive = draws[np.arange(len(draws)), best] > 0
    return {s: float(np.mean((best == i) & positive)) for i, s in enumerate(strategies)}


ALLOCATORS = {"equal_weight": equal_weight, "regime_lookup": regime_lookup, "bandit": bandit}


class Allocation:
    """Month-by-month size multipliers per strategy; ``allocation(now)`` returns the ones in force at ``now``."""

    def __init__(self, schedule: list[tuple[datetime, dict[str, float]]]):
        self.schedule = sorted(schedule, key=lambda item: item[0])
        self.times = [t for t, _ in self.schedule]

    def __call__(self, now: datetime) -> dict[str, float]:
        i = bisect.bisect_right(self.times, now) - 1
        return self.schedule[i][1] if i >= 0 else {}

    def records(self) -> list[dict]:
        return [{"from": iso(t), "multipliers": m} for t, m in self.schedule]


def build_allocation(kind: str, strategies: list[str], history: dict[str, list[tuple[date, float]]],
                     labels: dict[date, int], moments: list[datetime], seed: int = 0) -> Allocation:
    allocator = ALLOCATORS[kind]
    schedule = []
    for moment in moments:
        day = moment.astimezone(NEW_YORK).date()
        rng = np.random.default_rng([seed, day.year, day.month])
        visible = _before(history, day)                                     # the allocator never sees later days
        weights = allocator(strategies, visible, {d: v for d, v in labels.items() if d < day}, day, rng)
        schedule.append((moment, {s: min(MAX_MULTIPLIER, w * len(strategies)) for s, w in weights.items()}))
    return Allocation(schedule)


# --- meta-labelling ------------------------------------------------------------------------------------------------

class MetaLabelFilter:
    """Per strategy and calendar year, a logistic regression on the entry features predicts whether a trade will be
    profitable after costs; entries with a predicted probability below 0.5 are skipped. Each year's model learns only
    from that strategy's trades whose exit was decided at least ``META_PURGE`` before 1 January. Without enough
    trades (50, with 10 of each outcome) the strategy is not filtered that year."""

    def __init__(self, trades: list[dict], years: list[int]):
        from sklearn.linear_model import LogisticRegression

        self.models: dict[tuple[str, int], tuple] = {}
        self.training_sizes: dict[str, dict[int, int]] = {}
        by_strategy: dict[str, list[dict]] = {}
        for t in trades:
            if t.get("exit_decided_at") and all(t["features"].get(f) is not None for f in META_FEATURES):
                by_strategy.setdefault(t["strategy_id"], []).append(t)
        for strategy, rows in by_strategy.items():
            for year in years:
                cutoff = datetime(year, 1, 1, tzinfo=NEW_YORK).astimezone(timezone.utc) - META_PURGE
                train = [t for t in rows if parse_utc(t["exit_decided_at"]) < cutoff]
                labels = np.array([t["net_return"] > 0 for t in train], dtype=int)
                self.training_sizes.setdefault(strategy, {})[year] = len(train)
                if len(train) < META_MIN_TRADES or min(labels.sum(), len(labels) - labels.sum()) < META_MIN_CLASS:
                    continue
                x = np.array([[t["features"][f] for f in META_FEATURES] for t in train], dtype=float)
                centre, scale = x.mean(axis=0), x.std(axis=0)
                scale[scale == 0] = 1.0
                model = LogisticRegression(C=1.0, max_iter=1000).fit((x - centre) / scale, labels)
                self.models[(strategy, year)] = (centre, scale, model)

    def __call__(self, strategy_id: str, snapshot, now: datetime) -> bool:
        fitted = self.models.get((strategy_id, now.astimezone(NEW_YORK).year))
        if fitted is None:
            return True
        values = [snapshot.values.get(f) for f in META_FEATURES]
        if any(v is None for v in values):
            return True
        centre, scale, model = fitted
        x = (np.array(values, dtype=float) - centre) / scale
        return float(model.predict_proba(x[None, :])[0, 1]) >= META_THRESHOLD

    def summary(self) -> dict:
        return {"models": len(self.models), "training_trades": self.training_sizes}


# --- comparison ----------------------------------------------------------------------------------------------------

def _excess(candidate: list[tuple[date, float]], incumbent: list[tuple[date, float]]) -> np.ndarray:
    a, b = dict(sleeve_returns(candidate)), dict(sleeve_returns(incumbent))
    return np.array([a[d] - b[d] for d in sorted(set(a) & set(b))])


def stage_gate(candidate: dict, incumbent: dict, candidate_stressed: dict, incumbent_stressed: dict,
               threshold: float) -> dict:
    excess = _excess(candidate["series"], incumbent["series"])
    stressed = _excess(candidate_stressed["series"], incumbent_stressed["series"])
    p_value = block_bootstrap_pvalue(excess) if len(excess) else 1.0
    dd_c, dd_i = candidate["metrics"].get("max_drawdown"), incumbent["metrics"].get("max_drawdown")
    reasons = []
    if p_value >= threshold:
        reasons.append("NOT_SIGNIFICANT")
    if dd_c is None or dd_i is None or dd_c <= dd_i:
        reasons.append("DRAWDOWN_NOT_SMALLER")
    if not len(stressed) or np.mean(stressed) <= 0:
        reasons.append("FAILS_DOUBLE_COSTS")
    if candidate.get("stopped") or candidate_stressed.get("stopped"):
        reasons.append("RUN_STOPPED")
    return {"passed": not reasons, "reasons": reasons, "p_value": p_value, "p_threshold": threshold,
            "mean_daily_excess": float(np.mean(excess)) if len(excess) else None,
            "mean_daily_excess_double_costs": float(np.mean(stressed)) if len(stressed) else None,
            "max_drawdown": {"candidate": dd_c, "incumbent": dd_i}}


def _summary(result: dict) -> dict:
    keep = ("total_return", "cagr", "annual_volatility", "sharpe", "max_drawdown", "days")
    return {**{k: result["metrics"].get(k) for k in keep}, "fills": result["fills"], "trades": result["trades"]["trades"]}


def run_selection(store: LocalStorage, base, *, split: str = "DEVELOPMENT", proxy: tuple[str, AssetClass] | None = None,
                  run=None, seed: int = 0, progress: Callable[[str], None] | None = None,
                  confirm: str | None = None) -> dict:
    """Sleeves, schedules and, on development, the chain of stages; on the holdout, one test of the configuration
    development selected (``confirm``) against equal weight. ``base`` is a ``BacktestSpec`` naming every strategy and
    the full data period; ``run`` defaults to ``harness.run_backtest`` (injectable for tests)."""
    from .harness import run_backtest

    run = run or run_backtest
    note = progress or (lambda message: None)
    dev_end = datetime.combine(DEVELOPMENT_END, time(23, 59), tzinfo=NEW_YORK).astimezone(timezone.utc)
    hold_start = datetime.combine(HOLDOUT_START, time(0), tzinfo=NEW_YORK).astimezone(timezone.utc)
    if split == "DEVELOPMENT":
        window = (base.start, min(base.end, dev_end))
    elif split == "HOLDOUT":
        window = (max(base.start, hold_start), base.end)
        if confirm is None:
            raise ValueError("the holdout tests the configuration development selected; pass confirm=<name>")
    else:
        raise ValueError(f"unknown split {split}")
    strategies = [v.split("@")[0] for v in base.strategy_versions]
    if len(set(strategies)) != len(strategies):
        raise ValueError("one version per strategy: allocations are keyed by strategy id")
    history, trades = {}, []
    for version in base.strategy_versions:
        note(f"sleeve {version}")
        result = run(store, replace(base, strategy_versions=(version,), start=base.start, end=window[1]))
        if result.get("stopped"):  # a truncated sleeve would silently look like a strategy that never trades
            raise RuntimeError(f"sleeve {version} stopped: {result['stopped']}")
        history[version.split("@")[0]] = sleeve_returns(result["series"])
        trades.extend(result["trade_records"])
    if proxy is None:
        equities = [a for a in base.assets if a[1] == AssetClass.EQUITY]
        proxy = next((a for a in base.assets if a[0] == "SPY"), equities[0] if equities else base.assets[0])
    labels = market_labels(store, proxy, base.dataset)
    moments = month_starts(base.start, window[1])
    allocations = {k: build_allocation(k, strategies, history, labels, moments, seed) for k in ("regime_lookup", "bandit")}
    meta = MetaLabelFilter(trades, list(range(window[0].astimezone(NEW_YORK).year,
                                              window[1].astimezone(NEW_YORK).year + 1)))
    combined = replace(base, start=window[0], end=window[1])
    doubled = replace(combined, costs=replace(combined.costs, multiplier=combined.costs.multiplier * 2))
    cache: dict = {}

    def replay(name: str, allocation, entry_filter, stressed: bool) -> dict:
        key = (name, stressed)
        if key not in cache:
            note(f"combined {name}{' (double costs)' if stressed else ''}")
            cache[key] = run(store, doubled if stressed else combined, allocation=allocation, entry_filter=entry_filter)
        return cache[key]

    def config(name: str) -> dict:
        kind = name.split("+")[0]
        return {"name": name, "allocation": allocations.get(kind), "filter": meta if name.endswith("+meta") else None}

    incumbent = config("equal_weight")
    if split == "HOLDOUT":
        stages = []
        if confirm != "equal_weight":
            cand = config(confirm)
            args = [(c["name"], c["allocation"], c["filter"]) for c in (cand, incumbent)]
            gate = stage_gate(replay(*args[0], False), replay(*args[1], False), replay(*args[0], True),
                              replay(*args[1], True), ALPHA)
            stages.append({"stage": "holdout_confirmation", "candidate": confirm, "incumbent": "equal_weight",
                           "gate": gate, "candidate_result": _summary(replay(*args[0], False)),
                           "incumbent_result": _summary(replay(*args[1], False))})
            incumbent = cand if gate["passed"] else incumbent
        else:
            replay("equal_weight", None, None, False)
        return {"split": split, "window": [iso(window[0]), iso(window[1])], "strategies": strategies,
                "market_proxy": proxy[0], "development_selected": confirm, "stages": stages,
                "selected": incumbent["name"], "confirmed": confirm == "equal_weight" or bool(stages and stages[0]["gate"]["passed"]),
                "equal_weight_result": _summary(replay("equal_weight", None, None, False)),
                "allocations": {k: a.records() for k, a in allocations.items()}, "meta_label": meta.summary()}
    stages, threshold = [], ALPHA / len(STAGES)
    for stage in STAGES:
        if stage == "regime_lookup":
            cand = {"name": stage, "allocation": allocations["regime_lookup"], "filter": incumbent["filter"]}
        elif stage == "meta_label":
            cand = {"name": f"{incumbent['name']}+meta", "allocation": incumbent["allocation"], "filter": meta}
        else:
            cand = {"name": "bandit" + ("+meta" if incumbent["filter"] else ""), "allocation": allocations["bandit"],
                    "filter": incumbent["filter"]}
        args = [(c["name"], c["allocation"], c["filter"]) for c in (cand, incumbent)]
        gate = stage_gate(replay(*args[0], False), replay(*args[1], False), replay(*args[0], True),
                          replay(*args[1], True), threshold)
        stages.append({"stage": stage, "candidate": cand["name"], "incumbent": incumbent["name"], "gate": gate,
                       "candidate_result": _summary(replay(*args[0], False)),
                       "incumbent_result": _summary(replay(*args[1], False))})
        if gate["passed"]:
            incumbent = cand
    return {"split": split, "window": [iso(window[0]), iso(window[1])], "strategies": strategies,
            "market_proxy": proxy[0], "stages": stages, "selected": incumbent["name"],
            "allocations": {k: a.records() for k, a in allocations.items()}, "meta_label": meta.summary(),
            "sleeves": {s: {"days": len(v), "mean_daily": float(np.mean([r for _, r in v])) if v else None}
                        for s, v in history.items()}}


# --- registry ------------------------------------------------------------------------------------------------------

def _fingerprint(base) -> str:
    key = {"strategies": sorted(base.strategy_versions), "assets": sorted(a for a, _ in base.assets),
           "dataset": base.dataset, "sizing": base.sizing, "volatility_model": base.volatility_model,
           "version": SELECTOR_VERSION}
    return _hash(_canonical(key))[:20]


def run_selector_study(home: Path, base, *, split: str = "DEVELOPMENT", progress=None) -> dict:
    from .harness import _code_version
    from .studies import StudyRegistry

    registry = StudyRegistry(Path(home))
    registry.path = Path(home) / "research" / "selector_studies.jsonl"
    fingerprint = _fingerprint(base)
    confirm = None
    if split == "HOLDOUT":
        if registry.holdout_used(fingerprint):
            raise PermissionError("selector holdout already evaluated for this configuration; it may be used once")
        developed = [r for r in registry.records() if r["fingerprint"] == fingerprint
                     and r["spec"]["split"] == "DEVELOPMENT" and r["status"] == "COMPLETED"]
        if not developed:
            raise PermissionError("record the development result before the holdout (pre-registered order)")
        confirm = developed[-1]["result"]["selected"]
    record = {"created_at": iso(utc_now()), "code_version": _code_version(), "fingerprint": fingerprint,
              "selector_version": SELECTOR_VERSION, "evidence": "BACKTEST",
              "spec": {"split": split, "strategies": list(base.strategy_versions), "assets": [a for a, _ in base.assets],
                       "dataset": base.dataset, "start": iso(base.start), "end": iso(base.end), "sizing": base.sizing,
                       "volatility_model": base.volatility_model}}
    if split == "HOLDOUT":
        registry.claim_holdout(record)
    try:
        with LocalStorage(Path(home), writer=False) as store:
            record.update({"status": "COMPLETED", "result": run_selection(store, base, split=split, progress=progress,
                                                                            confirm=confirm)})
    except Exception as exc:
        record.update({"status": "FAILED", "error": f"{type(exc).__name__}: {exc}"})
        registry.append(record)
        raise
    return registry.append(record)

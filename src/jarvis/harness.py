"""Evaluation harness (Phase 3): replay real history through the real trading code and judge the result honestly.

One run replays stored bars through PaperDesk -> TradingEngine -> strategies -> Governor -> ReplayBroker, the same
code path as paper trading. Every run, including failures, is appended to ``research/experiments.jsonl``.

A strategy PASSES only if all of these hold:
1. no leak alarm (annualised Sharpe above 3, or a win rate above 75% over 30+ trades, is treated as a leak);
2. at least 30 completed trades;
3. its daily returns beat the benchmark (equal-weight universe, rebalanced monthly) with a one-sided block-bootstrap
   p-value below 0.05 divided by the number of runs registered for that strategy (a Bonferroni correction, so
   trying many variants raises the bar);
4. it beat the benchmark in at least 60% of calendar years (walk-forward consistency);
5. it still beats the benchmark on average with every cost doubled;
6. it passes the future-poisoning test: at several cut-off times the replay is repeated with every bar after the
   cut-off scrambled, and no strategy signal before the cut-off may change. This catches leaks of any size,
   including ones too small for the statistical alarm in (1).
The final holdout period may be evaluated only once per strategy fingerprint; the registry enforces it.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import tempfile
from collections import defaultdict
from dataclasses import asdict, dataclass, field, replace
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

from .config import PaperAsset, PaperRuntime
from .contracts import AssetClass, iso, utc_now
from .macro import load_macro
from .metrics import block_bootstrap_pvalue, daily_returns, daily_series, summarize, trade_stats
from .replay import CostModel, LookAheadError, ReplayBroker, ReplayClock, ReplayData
from .risk import RiskPolicy
from .runner import PaperDesk
from .storage import LocalStorage, _canonical, _hash
from .strategies import baseline_specs, research_specs

ALPHA = 0.05
LEAK_SHARPE, LEAK_WIN_RATE, MIN_TRADES, MIN_YEAR_SHARE = 3.0, 0.75, 30, 0.6


@dataclass(frozen=True)
class BacktestSpec:
    strategy_versions: tuple[str, ...]
    assets: tuple[tuple[str, AssetClass], ...]
    dataset: str
    timeframe: str
    start: datetime
    end: datetime
    split: str = "DEVELOPMENT"   # DEVELOPMENT or HOLDOUT
    initial_cash: float = 10_000.0
    order_notional: float = 1_000.0
    costs: CostModel = field(default_factory=CostModel)
    seed: int = 0

    def fingerprint(self) -> str:
        """Identifies the strategy configuration (not the period), for trial counting and the holdout rule."""
        key = {"strategies": sorted(self.strategy_versions), "assets": sorted(a for a, _ in self.assets),
               "dataset": self.dataset, "timeframe": self.timeframe, "order_notional": self.order_notional,
               "seed": self.seed}
        return _hash(_canonical(key))[:20]


def _policy(spec: BacktestSpec) -> RiskPolicy:
    strategies = tuple(sorted({v.split("@")[0] for v in spec.strategy_versions}))
    return RiskPolicy("BACKTEST", tuple(a for a, _ in spec.assets), strategies,
                      max_order_notional=spec.order_notional * 1.5, max_asset_notional=spec.order_notional * 3,
                      max_portfolio_notional=spec.initial_cash, max_daily_loss=spec.initial_cash * 0.05,
                      max_drawdown=0.5, max_spread_bps=100, max_quote_age_seconds=3600,
                      paper_enabled=True, crypto_enabled=True, owner_approved=True)


def run_backtest(data_store: LocalStorage, spec: BacktestSpec, *, data_cls=ReplayData, specs=None) -> dict:
    """Replay one period; returns the equity curve, trades and metrics (no gate, no registry write)."""
    clock = ReplayClock(spec.start)
    data = data_cls(data_store, spec.assets, spec.dataset, clock, spec.costs)
    broker = ReplayBroker(clock, data, spec.costs, cash=spec.initial_cash)
    runtime = PaperRuntime(tuple(PaperAsset(s, c, spec.order_notional) for s, c in spec.assets),
                           spec.strategy_versions, 60, spec.timeframe)
    points, exposure, stopped = [], [], None
    with tempfile.TemporaryDirectory(prefix="jarvis-replay-") as work:
        with LocalStorage(Path(work) / "journal", durable=False, cache_events=False) as journal:
            desk = PaperDesk(journal, broker, data, _policy(spec), runtime, clock=clock,
                             specs=specs if specs is not None else baseline_specs() + research_specs(),
                             seed=spec.seed, persist_market_data=False)
            for moment in data.schedule(spec.start, spec.end):
                clock.now = moment
                broker.step()
                result = desk.run_once()
                state = broker.state()
                points.append((moment, state.equity))
                exposure.append(sum(abs(v) for v in (state.position_values or {}).values()) / state.equity
                                if state.equity > 0 else 0.0)
                if result["mode"] != "PAPER":
                    stopped = {"at": iso(moment), "result": result}
                    break
            events = [row["event"] for row in journal.read_events()]
            outcomes = [e["payload"] for e in events if e["event_type"] == "TRADE_OUTCOME"]
            # Decisions the future-poisoning test compares: strategy signals and the orders' execution inputs.
            candidates = sorted([("SIGNAL", e["payload"]["detected_at"], e["payload"]["candidate_id"], 0.0, 0.0)
                                 for e in events if e["event_type"] == "CANDIDATE"] +
                                [("ORDER", e["payload"]["decided_at"], e["payload"]["client_order_id"],
                                  round(float(e["payload"]["quantity"]), 10),
                                  round(float(e["payload"]["reference_price"]), 10))
                                 for e in events if e["event_type"] == "ORDER_INTENT"])
    if data.lookahead_violations:  # the runner turns errors into SAFE; a look-ahead must abort the evaluation
        raise LookAheadError(data.lookahead_violations[0])
    series = daily_series(points)
    return {"series": series, "candidates": candidates,
            "average_exposure": float(np.mean(exposure)) if exposure else 0.0, "metrics": summarize(series),
            "trades": trade_stats(outcomes),
            "fills": len(broker.fills), "stopped": stopped,
            "turnover": sum(f["quantity"] * f["price"] for f in broker.fills) / spec.initial_cash}


def _scramble(bar, rng: random.Random):
    opening = bar.open * (1 + rng.uniform(-0.05, 0.05))
    closing = bar.close * (1 + rng.uniform(-0.05, 0.05))
    return replace(bar, open=opening, close=closing, high=max(opening, closing) * (1 + rng.uniform(0, 0.02)),
                   low=min(opening, closing) * (1 - rng.uniform(0, 0.02)), volume=bar.volume * rng.uniform(0.3, 3))


def poisoned(data_cls, cutoff: datetime, seed: int = 99):
    """The data class under test, with every bar that becomes available after ``cutoff`` scrambled.

    Only the strategy-facing bars change; the broker's fill index keeps the real bars, so order fills (and hence
    which assets are busy) are identical and cannot cause a false alarm.
    """

    class Poisoned(data_cls):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            rng = random.Random(seed)
            for symbol, bars in self.bars.items():
                self.bars[symbol] = [_scramble(b, rng) if b.available_at > cutoff else b for b in bars]

    return Poisoned


def future_poisoning_check(data_store: LocalStorage, spec: BacktestSpec, *, data_cls=ReplayData, specs=None,
                           cutoffs: int = 8, warmup: timedelta = timedelta(days=90)) -> dict:
    """Strategy signals and order inputs (quantity, limit price) before a cut-off must not depend on later data."""
    schedule = ReplayData(data_store, spec.assets, spec.dataset, ReplayClock(spec.start), spec.costs).schedule(
        spec.start, spec.end)
    picks = [schedule[int(len(schedule) * (i + 1) / (cutoffs + 1))] for i in range(cutoffs)] if schedule else []
    changed = []
    for moment in picks:
        cutoff = moment + timedelta(minutes=1)
        window = replace(spec, start=max(spec.start, moment - warmup), end=cutoff)
        clean = run_backtest(data_store, window, data_cls=data_cls, specs=specs)["candidates"]
        dirty = run_backtest(data_store, window, data_cls=poisoned(data_cls, cutoff), specs=specs)["candidates"]
        if clean != dirty:
            changed.append(iso(cutoff))
    return {"cutoffs": len(picks), "cutoffs_with_changed_signals": changed, "passed": not changed}


def benchmarks(data_store: LocalStorage, spec: BacktestSpec) -> dict[str, list[tuple[date, float]]]:
    """Buy-and-hold equal weight, equal weight rebalanced monthly (with costs), and cash at the T-bill rate."""
    clock = ReplayClock(spec.start)
    data = ReplayData(data_store, spec.assets, spec.dataset, clock, spec.costs)
    schedule = data.schedule(spec.start, spec.end)
    cost = {s: spec.costs.half_spread(c) + spec.costs.fee(c) for s, c in spec.assets}
    hold, monthly, points = {}, {}, defaultdict(list)
    cash_hold = cash_monthly = spec.initial_cash
    last_month = None
    for moment in schedule:
        clock.now = moment
        prices = {s: data.last_close(s) for s, _ in spec.assets}
        if any(p is None for p in prices.values()):
            continue
        if not hold:
            share = spec.initial_cash / len(prices)
            hold = {s: share * (1 - cost[s]) / p for s, p in prices.items()}
            cash_hold = 0.0
        month = (moment.year, moment.month)
        if month != last_month:
            value = cash_monthly + sum(monthly.get(s, 0.0) * p for s, p in prices.items())
            target = value / len(prices)
            for s, p in prices.items():
                trade = target - monthly.get(s, 0.0) * p
                value -= abs(trade) * cost[s]
            target = value / len(prices)
            monthly = {s: target / p for s, p in prices.items()}
            cash_monthly, last_month = 0.0, month
        points["equal_weight_buy_and_hold"].append((moment, cash_hold + sum(q * prices[s] for s, q in hold.items())))
        points["equal_weight_monthly"].append((moment, cash_monthly + sum(q * prices[s] for s, q in monthly.items())))
    result = {name: daily_series(p) for name, p in points.items()}
    rates = {row["observation_date"]: row["value"] for row in load_macro(data_store, "DTB3")}
    if rates and result.get("equal_weight_monthly"):
        value, series, rate = spec.initial_cash, [], 0.0
        days = [d for d, _ in result["equal_weight_monthly"]]
        for i, day in enumerate(days):
            rate = rates.get(day.isoformat(), rate)
            if i:
                value *= (1 + rate / 100) ** ((day - days[i - 1]).days / 365)
            series.append((day, value))
        result["cash_tbill"] = series
    return result


def _aligned_excess(strategy: list[tuple[date, float]], benchmark: list[tuple[date, float]]) -> tuple[np.ndarray, list[date]]:
    bench = dict(benchmark)
    common = [(d, v) for d, v in strategy if d in bench]
    days = [d for d, _ in common]
    s = daily_returns(common)
    b = daily_returns([(d, bench[d]) for d in days])
    return s - b, days[1:]


def evaluate_gate(base: dict, stressed: dict, bench: dict, *, trials: int, poisoning: dict | None = None) -> dict:
    reasons, checks = [], {}
    metrics, trades = base["metrics"], base["trades"]
    sharpe, win = metrics.get("sharpe"), trades.get("win_rate")
    statistical = (sharpe is not None and sharpe > LEAK_SHARPE) or \
        (trades["trades"] >= MIN_TRADES and win is not None and win > LEAK_WIN_RATE)
    structural = poisoning is not None and not poisoning["passed"]
    leak = statistical or structural
    checks.update({"leak_alarm": leak, "statistical_leak_alarm": statistical, "future_poisoning": poisoning})
    if leak:
        reasons.append("LEAK_SUSPECTED")
    checks["trades"] = trades["trades"]
    if trades["trades"] < MIN_TRADES:
        reasons.append("TOO_FEW_TRADES")
    excess, days = _aligned_excess(base["series"], bench["equal_weight_monthly"])
    threshold = ALPHA / max(1, trials)
    p_value = block_bootstrap_pvalue(excess) if len(excess) else 1.0
    checks.update({"mean_daily_excess": float(np.mean(excess)) if len(excess) else None,
                   "bootstrap_p_value": p_value, "p_threshold": threshold, "trials": trials})
    if p_value >= threshold:
        reasons.append("NOT_SIGNIFICANT_VS_BENCHMARK")
    by_year: dict[int, list[float]] = defaultdict(list)
    for day, value in zip(days, excess):
        by_year[day.year].append(float(value))
    positive_years = [y for y, v in by_year.items() if np.sum(v) > 0]
    share = len(positive_years) / len(by_year) if by_year else 0.0
    checks["years_beating_benchmark"] = f"{len(positive_years)}/{len(by_year)}"
    if share < MIN_YEAR_SHARE:
        reasons.append("INCONSISTENT_ACROSS_YEARS")
    if len(excess):  # informational: market-adjusted return, so a mostly-in-cash strategy can be read fairly
        bench_map = dict(bench["equal_weight_monthly"])
        common = [(d, v) for d, v in base["series"] if d in bench_map]
        s_r, b_r = daily_returns(common), daily_returns([(d, bench_map[d]) for d, _ in common])
        beta = float(np.cov(s_r, b_r)[0, 1] / np.var(b_r, ddof=1)) if len(b_r) > 2 and np.var(b_r) > 0 else 0.0
        checks.update({"beta_to_benchmark": beta, "alpha_annualised": float(np.mean(s_r - beta * b_r) * 252),
                       "average_exposure": base.get("average_exposure")})
    stressed_excess, _ = _aligned_excess(stressed["series"], bench["equal_weight_monthly"])
    checks["mean_daily_excess_double_costs"] = float(np.mean(stressed_excess)) if len(stressed_excess) else None
    if not len(stressed_excess) or np.mean(stressed_excess) <= 0:
        reasons.append("FAILS_DOUBLE_COSTS")
    if base["stopped"]:
        reasons.append("RUN_STOPPED")
    return {"passed": not reasons, "reasons": reasons, "checks": checks}


class ExperimentRegistry:
    """Append-only, hash-chained record of every evaluation, including failures and holdout access."""

    def __init__(self, home: Path):
        self.path = Path(home) / "research" / "experiments.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def records(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line]

    def trials(self, strategy_versions: tuple[str, ...]) -> int:
        key = sorted(strategy_versions)
        return sum(1 for r in self.records() if sorted(r["spec"]["strategy_versions"]) == key)

    def holdout_used(self, fingerprint: str) -> bool:
        return any(r["fingerprint"] == fingerprint and r["spec"]["split"] == "HOLDOUT" for r in self.records())

    def append(self, record: dict) -> dict:
        previous = self.records()
        prev_hash = previous[-1]["hash"] if previous else "0" * 64
        item = {**record, "seq": len(previous) + 1, "prev_hash": prev_hash}
        item["hash"] = _hash(prev_hash.encode() + _canonical(item))
        with open(self.path, "ab") as stream:
            stream.write(_canonical(item) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        return item


def _code_version() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=Path(__file__).parent, capture_output=True,
                              text=True, timeout=10).stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _data_fingerprint(data_store: LocalStorage, spec: BacktestSpec) -> str:
    digests = []
    for symbol, cls in sorted(spec.assets):
        manifest = data_store._bars_path(symbol, cls, spec.dataset).with_suffix(".manifest.json")
        digests.append(json.loads(manifest.read_text())["sha256"] if manifest.exists() else "missing")
    return _hash("|".join(digests).encode())[:20]


def _spec_record(spec: BacktestSpec) -> dict:
    return {"strategy_versions": list(spec.strategy_versions), "assets": [a for a, _ in spec.assets],
            "dataset": spec.dataset, "timeframe": spec.timeframe, "start": iso(spec.start), "end": iso(spec.end),
            "split": spec.split, "initial_cash": spec.initial_cash, "order_notional": spec.order_notional,
            "costs": spec.costs.as_dict(), "seed": spec.seed}


def evaluate(data_home: Path, spec: BacktestSpec, *, data_cls=ReplayData, specs=None) -> dict:
    """Run base and doubled-cost replays plus benchmarks, apply the gate, and register the result."""
    registry = ExperimentRegistry(data_home)
    if spec.split == "HOLDOUT" and registry.holdout_used(spec.fingerprint()):
        raise PermissionError("holdout already evaluated for this strategy configuration; it may be used once")
    record = {"created_at": iso(utc_now()), "code_version": _code_version(), "fingerprint": spec.fingerprint(),
              "spec": _spec_record(spec), "evidence": "BACKTEST"}
    try:
        with LocalStorage(Path(data_home), writer=False) as store:
            record["data_fingerprint"] = _data_fingerprint(store, spec)
            base = run_backtest(store, spec, data_cls=data_cls, specs=specs)
            stressed = run_backtest(store, replace(spec, costs=replace(spec.costs, multiplier=spec.costs.multiplier * 2)),
                                    data_cls=data_cls, specs=specs)
            bench = benchmarks(store, spec)
            poisoning = future_poisoning_check(store, spec, data_cls=data_cls, specs=specs)
        trials = registry.trials(spec.strategy_versions) + 1
        gate = evaluate_gate(base, stressed, bench, trials=trials, poisoning=poisoning)
        record.update({"status": "COMPLETED", "metrics": base["metrics"], "trades": base["trades"],
                       "turnover": base["turnover"], "average_exposure": base["average_exposure"], "metrics_double_costs": stressed["metrics"],
                       "benchmarks": {k: summarize(v) for k, v in bench.items()}, "gate": gate})
    except Exception as exc:
        record.update({"status": "FAILED", "error": f"{type(exc).__name__}: {exc}"})
        registry.append(record)
        raise
    return registry.append(record)

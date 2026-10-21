"""The portfolio study: build everything, develop on 2016-2021, confirm once on 2022-2023, final check on 2024+.

Protocol (owner decision 2026-10-20; docs/09-portfolio/PORTFOLIO_REGISTER.md):
- Development (decisions dated 2017-01-01..2021-12-31; 2016 is warm-up): every blend method is a logged trial.
  The configuration chosen is the method with the highest Sharpe ratio after costs whose worst drawdown stays
  within 25%; its deflated Sharpe ratio (Bailey & Lopez de Prado) accounts for how many trials were run.
- Confirmation (2022-01-01..2023-12-31, the 2022 bear market included) and holdout (2024-01-01 onward): run once
  each, only for the chosen configuration, claimed in the registry before they run. Pass rule for both: Sharpe at
  least SPY's, worst drawdown within 25%, and more total return than T-bills.
Every sleeve is always included; the allocator decides how much of each to run, so no sleeve is dropped by
looking at results.
"""

from __future__ import annotations

import hashlib
import math
from datetime import date, datetime
from pathlib import Path

import numpy as np

from ..contracts import AssetClass, iso, utc_now
from ..edgar import EarningsCalendar
from ..history import UniverseAsset
from ..macro import load_macro
from ..sentiment import SentimentIndex
from ..storage import LocalStorage, _canonical, _hash
from .allocator import MARGIN_RATE, MARGIN_SPREAD, METHODS, RANKER, RANKER_SHARE, blend_schedule, run_portfolio
from .ranker import ranker, week_starts
from .backtest import simulate, stats
from .panel import Panel, build_panel
from .risk import vol_forecasts
from .situation import FEATURES, capex_growth, raw_features, regime, standardise
from .sleeves import ACTIVE, SLEEVES, Context

VERSION = "1.3.0"  # round 4: 6-month drawdown reference, trend on asset classes only, ranker share 25%
MIN_TRIALS = 25    # the deflated Sharpe counts at least this many trials (every look at the data so far)
PERIODS = {"DEVELOPMENT": (date(2017, 1, 1), date(2021, 12, 31)),
           "CONFIRMATION": (date(2022, 1, 1), date(2023, 12, 31)),
           "HOLDOUT": (date(2024, 1, 1), date(2100, 1, 1))}
MAX_DRAWDOWN = 0.25


class Book:
    """Everything computed once from the data: panel, risk inputs, sleeves, situation."""

    def __init__(self, store: LocalStorage, universe: list[UniverseAsset]):
        self.panel = build_panel(store, universe)
        p = self.panel
        self.returns = p.returns()
        self.vols = vol_forecasts(p)
        equities = [a.symbol for a in universe if a.asset_class == AssetClass.EQUITY]
        news = SentimentIndex(store)
        self.ctx = Context(p, self.vols, self.returns, earnings=EarningsCalendar(store, equities),
                           news=news if news else None, capex_growth=capex_growth(store, p.dates))
        self.raw = raw_features(self.ctx, store)
        self.features = standardise(self.raw)
        self.labels = [regime(row) for row in self.raw]
        self.ranker_weights, self.ranker_report = ranker(self.ctx)
        self.sleeve_names = list(ACTIVE) + [RANKER]
        self.sleeves = [SLEEVES[name](self.ctx) for name in ACTIVE] + [self.ranker_weights]
        self.rebalance_rows = set(week_starts(p.dates))
        self.sleeve_returns = np.zeros((p.shape[0], len(self.sleeves)))
        for k, w in enumerate(self.sleeves):
            sim = simulate(p, w, start=0)
            for d, r in zip(sim["dates"], sim["returns"]):
                self.sleeve_returns[p.dates.index(d), k] = r
        rates = {row["observation_date"]: row["value"] for row in load_macro(store, "DTB3")}
        self.tbill = rates
        self.margin_rates = margin_schedule(p.dates, rates)

    def blend(self, method: str) -> np.ndarray:
        """The blend schedule every path uses (research, confirmation, holdout and the paper desk)."""
        return blend_schedule(method, self.sleeve_returns, self.features, self.labels, self.panel.dates,
                              ranker_share=RANKER_SHARE)

    def rows(self, period: str) -> tuple[int, int]:
        first, last = PERIODS[period]
        idx = [i for i, d in enumerate(self.panel.dates) if first <= d <= last]
        return (idx[0], idx[-1]) if idx else (0, -1)


def margin_schedule(dates: list[date], tbill: dict[str, float]) -> np.ndarray:
    """Annual margin rate known at each row: the latest 3-month T-bill observation dated before the row's date
    (FRED publishes a day's rate the next day) plus MARGIN_SPREAD; MARGIN_RATE before any observation."""
    obs = sorted((date.fromisoformat(k), v) for k, v in tbill.items() if v is not None)
    out, k, last = np.full(len(dates), MARGIN_RATE), 0, None
    for i, d in enumerate(dates):
        while k < len(obs) and obs[k][0] < d:
            last = obs[k][1]
            k += 1
        if last is not None:
            out[i] = last / 100 + MARGIN_SPREAD
    return out


def slice_stats(result: dict, first: date, last: date) -> dict:
    keep = [i for i, d in enumerate(result["dates"]) if first <= d <= last]
    if not keep:
        return {"days": 0}
    dates = [result["dates"][i] for i in keep]
    r = result["returns"][keep]
    out = stats(dates, r)
    for key in ("turnover", "gross", "net", "short"):
        if key in result:
            out[f"average_{key}"] = float(np.mean(np.asarray(result[key])[keep]))
    out["annual_turnover"] = out.pop("average_turnover", 0.0) * 252
    return out


def benchmarks(book: Book, first_row: int) -> dict[str, dict]:
    p = book.panel
    t, n = p.shape
    out = {}
    spy = np.zeros((t, n))
    spy[:, p.index("SPY")] = 1.0
    out["SPY"] = simulate(p, spy, start=first_row)
    basket = np.zeros((t, n))
    eq = [i for i, c in enumerate(p.classes) if c == AssetClass.EQUITY]
    basket[:, eq] = 1 / len(eq)
    out["equal_weight_universe"] = simulate(p, basket, start=first_row, band=0.02, relative=0.0)
    mix = np.zeros((t, n))
    mix[:, p.index("SPY")], mix[:, p.index("IEF")] = 0.6, 0.4
    out["60_40"] = simulate(p, mix, start=first_row, band=0.02, relative=0.0)
    return out


def deflated_sharpe(returns: np.ndarray, trial_sharpes: list[float], min_trials: int = 1) -> dict:
    """Probability that the true Sharpe exceeds the best one expected by luck across the trials (Bailey and
    Lopez de Prado 2014). Sharpe ratios here are per day."""
    from scipy import stats as st

    r = np.asarray(returns)
    n_obs = len(r)
    sd = r.std(ddof=1)
    sr = r.mean() / sd if sd > 0 else 0.0
    n_trials = max(min_trials, len(trial_sharpes))
    var_trials = float(np.var(trial_sharpes, ddof=1)) if n_trials > 1 else 0.0
    gamma = 0.5772156649
    expected_max = math.sqrt(var_trials) * ((1 - gamma) * st.norm.ppf(1 - 1 / n_trials)
                                            + gamma * st.norm.ppf(1 - 1 / (n_trials * math.e))) if n_trials > 1 else 0.0
    skew, kurt = float(st.skew(r)), float(st.kurtosis(r, fisher=False))
    denominator = math.sqrt(max(1e-12, 1 - skew * sr + (kurt - 1) / 4 * sr ** 2))
    z = (sr - expected_max) * math.sqrt(n_obs - 1) / denominator
    return {"daily_sharpe": sr, "expected_max_daily_sharpe_by_luck": expected_max, "trials": n_trials,
            "deflated_sharpe_probability": float(st.norm.cdf(z))}


class PortfolioRegistry:
    def __init__(self, home: Path):
        from ..studies import StudyRegistry

        self.inner = StudyRegistry(Path(home))
        self.inner.path = Path(home) / "research" / "portfolio_studies.jsonl"

    def records(self):
        return self.inner.records()

    def append(self, record):
        return self.inner.append(record)


def fingerprint(book: Book) -> str:
    """Identifies the system design (not the data's end date, which moves every day), so the once-only rule for
    the confirmation and the holdout cannot be side-stepped by re-running development on newer data."""
    key = {"version": VERSION, "assets": book.panel.assets, "sleeves": book.sleeve_names, "features": FEATURES}
    return _hash(_canonical(key))[:20]


def run_development(home: Path, book: Book) -> dict:
    """Run every blend method on the development period and log each as a trial; return the chosen one."""
    registry = PortfolioRegistry(home)
    first, last = PERIODS["DEVELOPMENT"]
    start = next(i for i, d in enumerate(book.panel.dates) if d >= first)
    # Decision t earns the return dated row t + 1, so the last development decision is the row before the last
    # development day: no confirmation-period return enters development.
    end = max(i for i, d in enumerate(book.panel.dates) if d <= last)
    sleeves = {name: slice_stats({"dates": book.panel.dates, "returns": book.sleeve_returns[:, k]}, first, last)
               for k, name in enumerate(book.sleeve_names)}
    results, trials = {}, []
    for method in METHODS:
        blend = book.blend(method)
        run = run_portfolio(book.panel, book.sleeves, blend, book.vols, book.returns, start=start, end=end,
                            rebalance_rows=book.rebalance_rows, margin_rates=book.margin_rates)
        doubled = run_portfolio(book.panel, book.sleeves, blend, book.vols, book.returns, start=start, end=end,
                                cost_multiplier=2.0, rebalance_rows=book.rebalance_rows, margin_rates=book.margin_rates)
        results[method] = {"stats": slice_stats(run, first, last),
                           "stats_double_costs": slice_stats(doubled, first, last),
                           "average_blend": dict(zip(book.sleeve_names, blend[start:end].mean(axis=0).round(3).tolist())),
                           "_returns": run["returns"]}
        trials.append(results[method]["stats"].get("sharpe") or 0.0)
    eligible = [m for m in METHODS if results[m]["stats"].get("max_drawdown", -1) >= -MAX_DRAWDOWN]
    chosen = max(eligible, key=lambda m: results[m]["stats"].get("sharpe") or -9) if eligible else None
    # Every development trial ever logged counts against the chosen one (register: every version is a trial).
    history = [v["stats"].get("sharpe") or 0.0 for r in registry.records() if r["spec"]["split"] == "DEVELOPMENT"
               for v in r.get("methods", {}).values()]
    daily = [s / math.sqrt(252) for s in history + trials]
    dsr = deflated_sharpe(results[chosen]["_returns"], daily, MIN_TRIALS) if chosen else None
    if chosen:  # sensitivity, not used to choose: today's retail margin rate (7%) charged throughout
        blend = book.blend(chosen)
        flat = run_portfolio(book.panel, book.sleeves, blend, book.vols, book.returns, start=start, end=end,
                             rebalance_rows=book.rebalance_rows)
        results[chosen]["stats_margin_7pct"] = slice_stats(flat, first, last)
    bench = {k: slice_stats(v, first, last) for k, v in benchmarks(book, start).items()}
    for v in results.values():
        v.pop("_returns")
    record = {"created_at": iso(utc_now()), "fingerprint": fingerprint(book), "version": VERSION,
              "spec": {"split": "DEVELOPMENT", "period": [first.isoformat(), last.isoformat()]},
              "status": "COMPLETED" if chosen else "NO_ELIGIBLE_CONFIGURATION",
              "data_last_date": book.panel.dates[-1].isoformat(),
              "methods": results, "chosen": chosen, "deflated_sharpe": dsr, "benchmarks": bench, "sleeves": sleeves,
              "regime_share": {r: book.labels[start:end].count(r) / (end - start) for r in set(book.labels[start:end])},
              "ranker": book.ranker_report}
    return registry.append(record)


def run_once(home: Path, book: Book, split: str) -> dict:
    """Confirmation or holdout: the chosen configuration only, once, claimed before it runs."""
    registry = PortfolioRegistry(home)
    fp = fingerprint(book)
    records = registry.records()
    developed = [r for r in records if r["fingerprint"] == fp and r["spec"]["split"] == "DEVELOPMENT"
                 and r.get("chosen")]
    if not developed:
        raise PermissionError("no development result with an eligible configuration for this design")
    if any(r["fingerprint"] == fp and r["spec"]["split"] == split for r in records):
        raise PermissionError(f"{split} already evaluated for this configuration; it may be used once")
    if split == "HOLDOUT" and not any(r["fingerprint"] == fp and r["spec"]["split"] == "CONFIRMATION"
                                      and r.get("status") == "COMPLETED" for r in records):
        raise PermissionError("run the confirmation before the holdout")
    chosen = developed[-1]["chosen"]
    first, last = PERIODS[split]
    claim = {"created_at": iso(utc_now()), "fingerprint": fp, "version": VERSION, "status": "STARTED",
             "spec": {"split": split, "method": chosen}}
    registry.append(claim)
    start_row = next(i for i, d in enumerate(book.panel.dates) if d >= PERIODS["DEVELOPMENT"][0])
    blend = book.blend(chosen)
    run = run_portfolio(book.panel, book.sleeves, blend, book.vols, book.returns, start=start_row,
                        rebalance_rows=book.rebalance_rows, margin_rates=book.margin_rates)
    doubled = run_portfolio(book.panel, book.sleeves, blend, book.vols, book.returns, start=start_row,
                            cost_multiplier=2.0, rebalance_rows=book.rebalance_rows, margin_rates=book.margin_rates)
    result = slice_stats(run, first, last)
    bench = {k: slice_stats(v, first, last) for k, v in benchmarks(book, start_row).items()}
    tbill = _tbill_return(book, first, min(last, book.panel.dates[-1]))
    checks = {"sharpe_at_least_spy": (result.get("sharpe") or -9) >= (bench["SPY"].get("sharpe") or 9),
              "drawdown_within_limit": result.get("max_drawdown", -1) >= -MAX_DRAWDOWN,
              "beats_tbills": result.get("total_return", -1) > tbill}
    record = {**claim, "status": "COMPLETED", "stats": result, "stats_double_costs": slice_stats(doubled, first, last),
              "benchmarks": bench, "tbill_total_return": tbill, "checks": checks, "passed": all(checks.values())}
    return registry.append(record)


def _tbill_return(book: Book, first: date, last: date) -> float:
    value, rate, previous = 1.0, 0.0, None
    for d in book.panel.dates:
        if not first <= d <= last:
            continue
        rate = book.tbill.get(d.isoformat(), rate)
        if previous is not None:
            value *= (1 + rate / 100) ** ((d - previous).days / 365)
        previous = d
    return value - 1

"""Golden days: one real desk decision, recorded with everything it read, replayed offline as a regression test.

``jarvis golden --desk <desk> --record`` (market hours; read-only on the desk's paper account) writes
``JARVIS_HOME/golden/<desk>/<day>/``:
- ``home/``: a JARVIS home holding exactly the stored bars and macro tables the target builder read, copied as they
  were served (``RecordingStore``), plus the stock book's short-term input files;
- ``deskstate/config/``: copies of the desk's owner policy, capital baseline and high-water mark that day;
- ``inputs.json``: the broker state and capital, the market-open flag, every quote and shortable answer the planner
  received, in order, with the clock reading that went with each quote, and the hashes of the copied files;
- ``expected.json``: the target weights, their diagnostics and the planned orders. The plan is a full rebalance:
  what the desk would order if that day were a rebalance day, whatever the calendar said.
``replay`` rebuilds the targets and the plan from a recording with the current code and desk settings
(``desks.DESKS``); ``jarvis golden`` and ``tests/test_golden_days.py`` report every difference as a behaviour change
to review. A recording is replayed once as soon as it is written, so an incomplete one is never kept.
Recordings hold exchange and FRED data, which may not be redistributed: they stay in JARVIS_HOME and never enter
the repository.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
from dataclasses import asdict
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from unittest import mock

import numpy as np

from .config import load_policy
from .contracts import Mode, iso, parse_utc, utc_now
from .desks import desk_approved, desk_home, desk_options
from .engine import TradingEngine
from .history import load_universe
from .market_data import Quote
from .risk import BrokerState, Governor
from .storage import LocalStorage
from .strategies import StrategyRegistry

STOCKBOOK_FILES = ("live_daily_adjusted.parquet", "live_daily_raw.parquet", "universe_top300.json", "sic.json")
DESK_STATE_FILES = ("owner-policy.json", "capital-baseline.json", "equity-high-water.json")
DAY = re.compile(r"\d{4}-\d{2}-\d{2}$")


class RecordingStore:
    """Reads through to the main store and copies every bar series and table it serves into ``sink``. Any other
    store access fails loudly, so a builder that starts reading something new cannot leave a recording incomplete."""

    def __init__(self, inner: LocalStorage, sink: LocalStorage):
        self.inner, self.sink = inner, sink

    def load_bars(self, asset_id, asset_class, **kwargs):
        bars = self.inner.load_bars(asset_id, asset_class, **kwargs)
        if bars:
            self.sink.save_bars(bars, dataset=kwargs.get("dataset", "bars"))
        return bars

    def read_table(self, *parts):
        rows = self.inner.read_table(*parts)
        if rows:
            self.sink.write_table(*parts, rows=rows)
        return rows

    def __getattr__(self, name):
        raise AttributeError(f"golden recording does not capture store.{name}; add it to RecordingStore")


class RecordingQuotes:
    """The planner's quote source, recorded: each quote (or the error raised instead) and the clock reading after
    it, which the planner also uses, so a replay judges quote age exactly as the recording did."""

    def __init__(self, inner):
        self.inner, self.rows, self.now = inner, {}, utc_now()

    def latest_quote(self, asset, asset_class):
        try:
            quote = self.inner.latest_quote(asset, asset_class)
        except Exception as exc:
            self.rows.setdefault(asset, []).append({"error": type(exc).__name__})
            raise
        self.now = utc_now()
        self.rows.setdefault(asset, []).append({
            "bid": quote.bid, "ask": quote.ask, "at": iso(quote.at), "observed_at": iso(quote.observed_at),
            "feed": quote.feed, "latency_ms": quote.latency_ms, "now": iso(self.now)})
        return quote

    def clock(self):
        return self.now


class ReplayQuotes:
    """Serves the recorded quotes in order, with the clock reading that went with each."""

    def __init__(self, rows: dict):
        self.rows, self.now = {asset: list(v) for asset, v in rows.items()}, None

    def latest_quote(self, asset, asset_class):
        if not self.rows.get(asset):
            raise LookupError(f"no recorded quote for {asset}")
        row = self.rows[asset].pop(0)
        if "error" in row:
            raise type(row["error"], (Exception,), {})("recorded error")
        self.now = parse_utc(row["now"])
        return Quote(asset, asset_class, row["bid"], row["ask"], parse_utc(row["at"]), parse_utc(row["observed_at"]),
                     row["feed"], row["latency_ms"])

    def clock(self):
        return self.now


class RecordingBroker:
    """The two questions the planner asks the broker, answered by the read-only desk account and recorded."""

    def __init__(self, inner):
        self.inner, self.market_open, self.shortable_answers = inner, None, {}

    def equity_market_open(self) -> bool:
        self.market_open = bool(self.inner.equity_market_open())
        return self.market_open

    def shortable(self, asset_id: str) -> bool:
        self.shortable_answers[asset_id] = bool(self.inner.shortable(asset_id))
        return self.shortable_answers[asset_id]


class ReplayBroker:
    def __init__(self, market_open: bool, shortable: dict[str, bool]):
        self.market_open, self.answers = market_open, dict(shortable)

    def equity_market_open(self) -> bool:
        return self.market_open

    def shortable(self, asset_id: str) -> bool:
        if asset_id not in self.answers:
            raise LookupError(f"no recorded shortable answer for {asset_id}")
        return self.answers[asset_id]


def _builder(desk: str, home: Path, store, universe):
    from .desks import SectorBuilder, StockBookBuilder

    return SectorBuilder(store, universe) if desk == "sector" else StockBookBuilder(home, store)


def _plan(desk: str, builder, weights, policy, state, capital, broker, quotes, scratch):
    from .portfolio.executor import PortfolioDesk

    planner = PortfolioDesk(scratch, broker, quotes, policy, builder.instruments(), clock=quotes.clock,
                            approved=desk_approved(policy, builder), **{**desk_options(desk), "pause": 0.0})
    return planner.plan(weights, state, capital)


def _plain(value):
    """JSON-ready copy (numpy scalars and arrays, enums, dates, sets), so recordings and replays compare alike."""
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted(_plain(v) for v in value)
    if isinstance(value, (list, tuple, np.ndarray)):
        return [_plain(v) for v in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return _plain(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    return value


def _outputs(weights: dict, diagnostics: dict, report) -> dict:
    return _plain({"weights": dict(sorted(weights.items())), "diagnostics": diagnostics, "halted": report.halted,
                   "planned": [asdict(o) for o in report.planned], "skipped": dict(sorted(report.skipped.items()))})


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _input_files(folder: Path) -> dict[str, str]:
    names = ["deskstate/config/owner-policy.json", "universe.json"] + [f"home/shortterm/{n}" for n in STOCKBOOK_FILES]
    return {name: _sha256(folder / name) for name in names if (folder / name).exists()}


def _write(path: Path, document: dict) -> None:
    path.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n")


def _commit() -> str:
    try:
        return subprocess.run(["git", "-C", str(Path(__file__).resolve().parents[2]), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def record(main_home: Path, desk: str, universe_path: Path | None, broker, data, *, day: str | None = None) -> Path:
    """Record today's decision for ``desk``: targets from the stored data and a full-rebalance plan against the desk's
    account. ``broker`` and ``data`` must be read-only (no order is ever sent). The recording is replayed at once; if
    it does not reproduce itself it is renamed ``<day>.failed`` and an error is raised."""
    from .timeframes import NEW_YORK

    main_home = Path(main_home)
    day = day or datetime.now(NEW_YORK).date().isoformat()
    folder = main_home / "golden" / desk / day
    if folder.exists():
        raise FileExistsError(f"{folder} is already recorded")
    if desk == "sector" and universe_path is None:
        raise ValueError("recording the sector desk needs its universe file")
    if not broker.equity_market_open():
        raise RuntimeError("record during market hours: with the market closed every order is skipped")
    home, state_home = folder / "home", folder / "deskstate"
    (state_home / "config").mkdir(parents=True)
    for name in DESK_STATE_FILES:
        source = desk_home(main_home, desk) / "config" / name
        if source.exists():
            shutil.copy2(source, state_home / "config" / name)
    universe = None
    if desk == "sector":
        shutil.copy2(universe_path, folder / "universe.json")
        universe = load_universe(folder / "universe.json")
    else:
        (home / "shortterm").mkdir(parents=True)
        for name in STOCKBOOK_FILES:
            shutil.copy2(main_home / "shortterm" / name, home / "shortterm" / name)
    with LocalStorage(main_home, writer=False) as source, LocalStorage(home) as sink:
        builder = _builder(desk, home, RecordingStore(source, sink), universe)
    weights, diagnostics = builder.targets()
    policy = load_policy(state_home)
    with LocalStorage(state_home) as scratch:
        # The executor's own capital and drawdown rules, run on copies of the desk's baseline and high-water files.
        engine = TradingEngine(scratch, broker, Governor(policy), StrategyRegistry([]), Mode.PAPER)
        state = engine._risk_state()
        capital = engine.desk_equity
        quotes, answers = RecordingQuotes(data), RecordingBroker(broker)
        report = _plan(desk, builder, weights, policy, state, capital, answers, quotes, scratch)
    expected = _outputs(weights, diagnostics, report)
    _write(folder / "inputs.json", {
        "desk": desk, "day": day, "recorded_at": iso(utc_now()), "commit": _commit(), "state": _plain(asdict(state)),
        "capital": capital, "market_open": answers.market_open, "shortable": answers.shortable_answers,
        "quotes": quotes.rows, "files": _input_files(folder)})
    _write(folder / "expected.json", expected)
    problems = compare(expected, replay(folder))
    if problems:
        folder.rename(folder.with_name(f"{day}.failed"))
        raise RuntimeError(f"the recording does not reproduce itself ({len(problems)} differences): {problems[:5]}")
    return folder


def replay(folder: Path) -> dict:
    """The targets and plan rebuilt from a recording with the current code and desk settings."""
    folder = Path(folder)
    inputs = json.loads((folder / "inputs.json").read_text())
    changed = [name for name, digest in inputs["files"].items() if _sha256(folder / name) != digest]
    if changed:
        raise ValueError(f"recording files changed since they were recorded: {changed}")
    desk, home = inputs["desk"], folder / "home"
    universe = load_universe(folder / "universe.json") if desk == "sector" else None
    with LocalStorage(home, writer=False) as store:
        builder = _builder(desk, home, store, universe)
    weights, diagnostics = builder.targets()
    policy = load_policy(folder / "deskstate")
    state = BrokerState(**{**inputs["state"], "open_order_ids": tuple(inputs["state"]["open_order_ids"])})
    with tempfile.TemporaryDirectory() as tmp:
        # Recorded quotes need no waiting: the planner's re-check pause for wide quotes is skipped.
        with LocalStorage(Path(tmp), durable=False) as scratch, mock.patch("jarvis.portfolio.executor.time.sleep"):
            report = _plan(desk, builder, weights, policy, state, inputs["capital"],
                           ReplayBroker(inputs["market_open"], inputs["shortable"]), ReplayQuotes(inputs["quotes"]),
                           scratch)
    return _outputs(weights, diagnostics, report)


def compare(expected, actual, path: str = "") -> list[str]:
    """Every difference between a recorded and a replayed output (numbers equal to 1e-9 relative)."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        out = []
        for key in sorted(set(expected) | set(actual)):
            where = f"{path}/{key}"
            if key not in actual:
                out.append(f"{where}: gone (was {_short(expected[key])})")
            elif key not in expected:
                out.append(f"{where}: new ({_short(actual[key])})")
            else:
                out += compare(expected[key], actual[key], where)
        return out
    if isinstance(expected, list) and isinstance(actual, list):
        out = [] if len(expected) == len(actual) else [f"{path}: {len(expected)} items recorded, {len(actual)} now"]
        for i, (e, a) in enumerate(zip(expected, actual)):
            out += compare(e, a, f"{path}[{i}]")
        return out
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (expected, actual)):
        return [] if math.isclose(expected, actual, rel_tol=1e-9, abs_tol=1e-12) else [f"{path}: {expected!r} -> {actual!r}"]
    return [] if expected == actual else [f"{path}: {_short(expected)} -> {_short(actual)}"]


def _short(value) -> str:
    text = json.dumps(value, default=str)
    return text if len(text) <= 80 else text[:77] + "..."


def recordings(main_home: Path, desk: str | None = None) -> list[Path]:
    root = Path(main_home) / "golden"
    if not root.exists():
        return []
    return sorted(day for folder in root.iterdir() if folder.is_dir() and desk in (None, folder.name)
                  for day in folder.iterdir() if DAY.match(day.name) and (day / "expected.json").exists())


def check(main_home: Path, desk: str | None = None) -> list[dict]:
    """Replay every recording; PASS means today's code makes exactly the recorded decision."""
    results = []
    for folder in recordings(main_home, desk):
        expected = json.loads((folder / "expected.json").read_text())
        try:
            problems = compare(expected, replay(folder))
        except Exception as exc:
            problems = [f"replay failed: {type(exc).__name__}: {exc}"]
        results.append({"desk": folder.parent.name, "day": folder.name, "status": "FAIL" if problems else "PASS",
                         "differences": len(problems), "first": problems[:10]})
    return results

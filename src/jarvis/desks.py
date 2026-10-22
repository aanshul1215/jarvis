"""Round 7 paper desks: the sector rotation and the stock book, each on its own Alpaca paper account.

Each desk has its own JARVIS home (``JARVIS_HOME/desks/<desk>``: owner policy, journal, high-water mark), so its
reconciliation sees only its own orders and positions, and reads market data from the main home. Targets come from
exactly the research code:
- sector rotation (v1.5.0, docs/09-portfolio/ROUND6_DESIGN.md): decided on the first session of each month;
- stock book (enhanced-index-2.0.0, docs/10-shortterm/ENHANCED_INDEX_V2_STUDY.md): decided on the first session
  of each week (and of each month for the bonds/commodities sleeve).
The daily cycle runs the morning after a decision session (decision after the close, trade the next day).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .contracts import AssetClass
from .history import UniverseAsset

DESKS = {
    "sector": {"strategy_id": "sector_rotation", "keys": ("ALPACA_SECTOR_KEY_ID", "ALPACA_SECTOR_SECRET_KEY"),
               "fractional": False, "band": 0.01, "band_rel": 0.20, "pause": 0.4, "quote_retries": 2},
    "stockbook": {"strategy_id": "stock_book", "keys": ("ALPACA_STOCKBOOK_KEY_ID", "ALPACA_STOCKBOOK_SECRET_KEY"),
                  "fractional": True, "band": 0.001, "band_rel": 0.25, "pause": 0.4, "quote_retries": 2},
}


def desk_home(main_home: Path, desk: str) -> Path:
    return Path(main_home) / "desks" / desk


def desk_keys(desk: str) -> tuple[str | None, str | None]:
    key_name, secret_name = DESKS[desk]["keys"]
    return os.environ.get(key_name), os.environ.get(secret_name)


def desk_options(desk: str) -> dict:
    """The PortfolioDesk settings the desk trades with (no drawdown brake by design; the Governor's stops remain)."""
    cfg = DESKS[desk]
    return {"strategy_id": cfg["strategy_id"], "fractional": cfg["fractional"], "band": cfg["band"],
            "band_rel": cfg["band_rel"], "use_brake": False, "pause": cfg["pause"],
            "quote_retries": cfg["quote_retries"]}


def desk_approved(policy, builder) -> set[str] | None:
    """The tradable list when the owner approved a rule (the month's top-300 stocks) as well as fixed assets."""
    if "shortterm_top300" in policy.approved_asset_rules and hasattr(builder, "approved"):
        return set(policy.approved_assets) | builder.approved()
    return None


class SectorBuilder:
    method = "sector-rotation-1.5.0"

    def __init__(self, store, universe: list[UniverseAsset]):
        from .portfolio.core import known_rate, sector_weights
        from .portfolio.study import CoreBook

        self.book = CoreBook(store, universe)
        p = self.book.panel
        self.rates = known_rate(p.dates, self.book.tbill)
        self.weights, self.report = sector_weights(self.book.ctx, self.rates)
        self.t = p.shape[0] - 1

    def is_rebalance_day(self) -> bool:
        from .portfolio.ranker import month_starts

        return self.t in set(month_starts(self.book.panel.dates))

    def instruments(self) -> list[UniverseAsset]:
        return [UniverseAsset(a, AssetClass.EQUITY) for a in self.book.panel.assets if "/" not in a]

    def targets(self, drawdown: float = 0.0) -> tuple[dict[str, float], dict]:
        p = self.book.panel
        w = self.weights[self.t]
        weights = {a: float(x) for a, x in zip(p.assets, w) if x > 1e-9}
        return weights, {"decision_row_date": p.dates[self.t].isoformat(), "method": self.method,
                         "rebalance_day": self.is_rebalance_day(), "filter": self.report.get("risk_on_decisions")}


class StockBookBuilder:
    method = "enhanced-index-2.0.0"

    def __init__(self, main_home: Path, store):
        from .macro import load_macro
        from .portfolio.core import known_rate
        from .shortterm.book import DEFENSIVE, SAFE, combine, load_etfs
        from .shortterm.enhanced import targets
        from .shortterm.reversal import Market

        folder = Path(main_home) / "shortterm"
        adjusted = pd.read_parquet(folder / "live_daily_adjusted.parquet")
        raw = pd.read_parquet(folder / "live_daily_raw.parquet")
        self.universe = json.loads((folder / "universe_top300.json").read_text())
        groups = {s: v["group"] for s, v in json.loads((folder / "sic.json").read_text()).items()}
        m = Market.from_frames(adjusted, raw)  # adjusted bars cleaned (docs/10-shortterm/DATA_CLEANING.md)
        flags = m.adjustment_flags
        fixed = [] if flags is None else flags[flags["spurious"]].itertuples()
        self.data_fixes = [f"{f.symbol} {f.timestamp.tz_convert('America/New_York').date()}" for f in fixed]
        etfs = load_etfs(store, m.dates, DEFENSIVE + (SAFE, "SPY"))
        self.inst = combine(m, etfs)
        rates = known_rate(m.dates, {r["observation_date"]: r["value"] for r in load_macro(store, "DTB3")})
        self.t = len(m.dates) - 1
        today = m.dates[self.t]
        first = next(i for i, d in enumerate(m.dates) if (d.year, d.month) == (today.year, today.month))
        rows = list(range(first, self.t + 1))
        self.decided, self.report = targets(self.inst, m, self.universe, groups, etfs["SPY"][1], rates, rows, sleeve=0.20)
        self.dates = m.dates
        self.month_key = f"{today.year:04d}-{today.month:02d}"
        self.missing_month = self.month_key not in self.universe

    def is_rebalance_day(self) -> bool:
        return not self.missing_month and self.decided.get(self.t) is not None

    def approved(self) -> set[str]:
        from .shortterm.book import DEFENSIVE, SAFE

        return set(self.universe.get(self.month_key, [])) | set(DEFENSIVE) | {SAFE}

    def instruments(self) -> list[UniverseAsset]:
        return [UniverseAsset(s, AssetClass.EQUITY) for s in self.inst.symbols]

    def targets(self, drawdown: float = 0.0) -> tuple[dict[str, float], dict]:
        latest = [t for t in sorted(self.decided) if self.decided[t] is not None]
        w = self.decided[latest[-1]] if latest else {}
        weights = {self.inst.symbols[j]: float(v) for j, v in w.items() if v > 1e-9}
        return weights, {"decision_row_date": self.dates[self.t].isoformat(), "method": self.method,
                         "rebalance_day": self.is_rebalance_day(), "names": len(weights),
                         "sleeve": self.report.get("sleeve_months"),
                         "universe_month_missing": self.missing_month, "adjusted_data_fixes": self.data_fixes}


def desk_status(main_home: Path) -> dict:
    """Read-only summary of each desk from its own journal (no broker call): the latest cycle, why orders were
    skipped, whether the build is complete and which owner policy is in force."""
    from collections import Counter

    from .storage import LocalStorage

    out = {}
    for desk in DESKS:
        home = desk_home(main_home, desk)
        if not (home / "journal" / "operational.jsonl").exists():
            out[desk] = {"status": "NOT_STARTED"}
            continue
        with LocalStorage(home, writer=False) as store:
            events = [row["event"] for row in store.read_events()]
        cycles = [e for e in events if e["event_type"] == "PORTFOLIO_CYCLE"]
        targets = [e for e in events if e["event_type"] == "PORTFOLIO_TARGET"]
        last = cycles[-1]["payload"] if cycles else {}
        statuses = Counter(e["payload"].get("status") for e in events if e["event_type"] == "ORDER_UPDATE")
        policy = json.loads((home / "config" / "owner-policy.json").read_text())
        out[desk] = {"status": "HALTED" if last.get("halted") else ("RUNNING" if cycles else "NO_CYCLE_YET"),
                     "last_cycle_at": cycles[-1]["at"] if cycles else None, "cycles": len(cycles),
                     "capital": last.get("capital"), "orders_last_cycle": last.get("orders"),
                     "note": last.get("note"), "skipped_last_cycle": dict(Counter(last.get("skipped", {}).values())),
                     "decision_row_date": targets[-1]["payload"].get("decision_row_date") if targets else None,
                     "target_names": len(targets[-1]["payload"].get("weights", {})) if targets else 0,
                     "order_updates": dict(statuses), "build_complete": (home / "config" / "desk-build-complete.json").exists(),
                     "policy": policy.get("version"), "allocated_capital": policy.get("allocated_capital")}
    return out


def ensure_desk_home(main_home: Path, desk: str) -> Path:
    """Create the desk's home with its owner policy on first use (paper only; owner-signed values in the doc)."""
    home = desk_home(main_home, desk)
    (home / "config").mkdir(parents=True, exist_ok=True)
    policy = home / "config" / "owner-policy.json"
    if not policy.exists():
        main = json.loads((Path(main_home) / "config" / "owner-policy.json").read_text())
        cfg = DESKS[desk]
        base = {"version": f"owner-2026-10-21-{desk}", "approved_strategies": [cfg["strategy_id"]],
                "max_daily_loss": main["max_daily_loss"], "max_drawdown": main["max_drawdown"],
                "max_spread_bps": main["max_spread_bps"], "max_quote_age_seconds": main["max_quote_age_seconds"],
                "paper_enabled": True, "crypto_enabled": False, "owner_approved": True, "allocated_capital": 10000,
                "max_portfolio_notional": 10000}
        if desk == "sector":
            from .portfolio.sleeves import GROUPS

            base.update({"approved_assets": list(GROUPS["sector"]) + ["SHY"], "max_order_notional": 4000,
                         "max_asset_notional": 4000})
        else:
            from .shortterm.book import DEFENSIVE, SAFE

            # Owner decision 2026-10-21: 2% spread limit for the stock book, because the free IEX quotes show
            # spreads far wider than the real market's on many large stocks; buys still carry a limit price.
            base.update({"approved_assets": list(DEFENSIVE) + [SAFE], "approved_asset_rules": ["shortterm_top300"],
                         "max_order_notional": 1500, "max_asset_notional": 1500, "max_spread_bps": 200})
        policy.write_text(json.dumps(base, indent=2))
    return home

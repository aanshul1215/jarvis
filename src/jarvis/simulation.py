"""Accelerated mock paper soak (Phase 1 exit test).

Drives the real PaperDesk loop on a simulated clock with synthetic data and a mock broker that behaves like a
messy real one: some entry orders fill partially or not at all and complete later, the vendor amends recent
bars, crypto fees are taken from the coin received, and equities trade only in session hours. Nothing here
touches a network or a real account, and nothing here is market evidence.
"""

from __future__ import annotations

import random
import time
from collections import Counter
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .broker import BrokerError, MockBroker
from .config import PaperAsset, PaperRuntime
from .contracts import AssetClass, Bar, BrokerOrder, parse_utc
from .market_data import Quote
from .risk import RiskPolicy
from .runner import PaperDesk
from .storage import LocalStorage

SOAK_ASSETS = (("AAPL", AssetClass.EQUITY, 250.0), ("MSFT", AssetClass.EQUITY, 250.0),
               ("BTC/USD", AssetClass.CRYPTO, 100.0), ("ETH/USD", AssetClass.CRYPTO, 100.0))
SOAK_START = datetime(2026, 1, 5, 13, 0, tzinfo=timezone.utc)  # a Monday; fixed so runs are reproducible


class SimClock:
    def __init__(self, start: datetime):
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


class SimMarketData:
    """Hourly bars on a seeded random walk with occasional volume breakouts and vendor amendments."""

    def __init__(self, clock: SimClock, seed: int, *, amend_probability: float = 0.02):
        self.clock, self.seed, self.amend_probability = clock, seed, amend_probability
        self.origin = clock.now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=48)
        self._paths: dict[str, list[Bar]] = {}
        self._amended: set[tuple[str, int]] = set()
        self._rng = random.Random(f"{seed}:vendor")

    def _bar(self, symbol: str, cls: AssetClass, index: int, previous: float) -> Bar:
        rng = random.Random(f"{self.seed}:{symbol}:{index}")
        change = rng.gauss(0, 0.004)
        breakout = rng.random() < 0.06
        if breakout:
            change += 0.02
        close = previous * (1 + change)
        start = self.origin + timedelta(hours=index)
        end = start + timedelta(hours=1)
        return Bar(symbol, cls, start, end, end + timedelta(minutes=1), previous,
                   max(previous, close) * 1.001, min(previous, close) * 0.999, close,
                   (3000.0 if breakout else 1000.0) + rng.randint(0, 50), "SOAK_SIM", "SIMULATED", "SIM")

    def _completed(self, symbol: str, cls: AssetClass) -> list[Bar]:
        count = int((self.clock.now - self.origin - timedelta(minutes=1)) / timedelta(hours=1))
        path = self._paths.setdefault(symbol, [])
        while len(path) < count:
            previous = path[-1].close if path else (100.0 if cls == AssetClass.EQUITY else 1000.0)
            path.append(self._bar(symbol, cls, len(path), previous))
        return path[:count]

    def recent_bars(self, symbol, cls, *, start, end, limit, timeframe="1Hour"):
        bars = self._completed(symbol, cls)
        if bars and self._rng.random() < self.amend_probability:
            self._amended.add((symbol, len(bars) - 1))  # the vendor amends the newest bar (late prints)
        shown = [replace(b, volume=b.volume + 7) if (symbol, i) in self._amended else b
                 for i, b in enumerate(bars)]
        shown = [b for b in shown if start <= b.end_at <= end][-limit:]
        return shown, {"feed": "SIMULATED", "rows": len(shown)}

    def latest_quote(self, symbol, cls):
        price = self._completed(symbol, cls)[-1].close
        now = self.clock.now
        return Quote(symbol, cls, price * 0.9999, price * 1.0001, now, now, "SIMULATED", 1.0)


class SimBroker(MockBroker):
    """Mock broker with partial fills, unfilled entries, late fills, session hours and crypto fees in coin."""

    CRYPTO_FEE = 0.0025

    def __init__(self, clock: SimClock, seed: int, *, cash: float, p_unfilled: float = 0.15,
                 p_partial: float = 0.20, p_late_fill: float = 0.3):
        super().__init__(cash=cash)
        self.clock = clock
        self.rng = random.Random(f"{seed}:broker")
        self.p_unfilled, self.p_partial, self.p_late_fill = p_unfilled, p_partial, p_late_fill
        self.reference: dict[str, float] = {}
        self.classes: dict[str, AssetClass] = {}

    def equity_market_open(self) -> bool:
        now = self.clock.now
        minutes = now.hour * 60 + now.minute
        return now.weekday() < 5 and 14 * 60 + 30 <= minutes < 21 * 60  # 09:30-16:00 New York (EST)

    def _charge_coin_fee(self, asset_id: str, side: str, quantity: float) -> None:
        if side == "BUY" and quantity > 0 and self.classes.get(asset_id) == AssetClass.CRYPTO:
            self.positions[asset_id] -= quantity * self.CRYPTO_FEE

    def submit(self, client_order_id, asset_id, asset_class, side, quantity, reference_price) -> BrokerOrder:
        if client_order_id in self.orders:
            return self.orders[client_order_id]
        draw = self.rng.random()
        if side == "BUY":
            self.fill_fraction = 0.0 if draw < self.p_unfilled else 0.5 if draw < self.p_unfilled + self.p_partial else 1.0
        else:
            self.fill_fraction = 1.0
        self.classes[asset_id] = asset_class
        self.reference[client_order_id] = reference_price
        order = super().submit(client_order_id, asset_id, asset_class, side, quantity, reference_price)
        self._charge_coin_fee(asset_id, side, order.filled_quantity)
        return order

    def tick(self) -> int:
        """Complete some working orders, as a real venue would between polls. Returns orders completed."""
        completed = 0
        for client_id, order in list(self.orders.items()):
            if order.status not in ("ACCEPTED", "PARTIALLY_FILLED") or self.rng.random() >= self.p_late_fill:
                continue
            remaining = round(order.quantity - order.filled_quantity, 8)
            price = self.reference[client_id]
            if order.side == "BUY" and remaining * price > self.cash:
                continue
            self.cash -= remaining * price
            self.positions[order.asset_id] = self.positions.get(order.asset_id, 0) + remaining
            self.last_prices[order.asset_id] = price
            self._charge_coin_fee(order.asset_id, order.side, remaining)
            self.orders[client_id] = replace(order, filled_quantity=order.quantity, average_price=price,
                                             status="FILLED")
            completed += 1
        return completed


def soak_policy() -> RiskPolicy:
    return RiskPolicy("SOAK_MOCK_ONLY", tuple(symbol for symbol, _, _ in SOAK_ASSETS), ("breakout-volume",),
                      max_order_notional=300, max_asset_notional=600, max_portfolio_notional=2000,
                      max_daily_loss=500, max_drawdown=0.25, max_spread_bps=30, max_quote_age_seconds=120,
                      paper_enabled=True, crypto_enabled=True, owner_approved=True)


def run_soak(home: Path, *, hours: float = 24, poll_seconds: int = 60, seed: int = 7) -> dict:
    """Run the paper loop for ``hours`` of simulated time; report whether it ever stopped itself."""
    clock = SimClock(SOAK_START)
    runtime = PaperRuntime(tuple(PaperAsset(s, c, n) for s, c, n in SOAK_ASSETS), ("breakout-volume@1.0.0",),
                           poll_seconds)
    cycles = int(hours * 3600 / poll_seconds)
    report: dict = {"evidence": "SYNTHETIC_MOCK_ONLY", "seed": seed, "simulated_hours": hours,
                    "poll_seconds": poll_seconds, "cycles_planned": cycles, "cycles_completed": 0,
                    "stopped": None, "late_fills": 0}
    began = time.perf_counter()
    with LocalStorage(home) as store:
        data = SimMarketData(clock, seed)
        broker = SimBroker(clock, seed, cash=10_000)
        desk = PaperDesk(store, broker, data, soak_policy(), runtime, clock=clock)
        for cycle in range(cycles):
            report["late_fills"] += broker.tick()
            try:
                result = desk.run_once()
            except BrokerError as exc:
                report["stopped"] = {"cycle": cycle, "at": clock.now.isoformat(), "error": str(exc)}
                break
            if result["mode"] != "PAPER":
                report["stopped"] = {"cycle": cycle, "at": clock.now.isoformat(), "result": result}
                break
            report["cycles_completed"] = cycle + 1
            clock.advance(poll_seconds)
        events = [row["event"] for row in store.read_events()]
        overdue = []
        intents = {e["payload"].get("client_order_id"): e for e in events if e["event_type"] == "ORDER_INTENT"}
        for client_id in broker.state().open_order_ids:
            intent = intents.get(client_id)
            if intent and parse_utc(intent["payload"]["expires_at"]) < clock.now - timedelta(seconds=2 * poll_seconds):
                overdue.append(client_id)
        state = broker.state()
    with LocalStorage(home) as reopened:  # re-verifies the whole hash chain from disk
        report["journal_events_verified"] = len(reopened.read_events())
    kinds = Counter(e["event_type"] for e in events)
    report.update({
        "wall_seconds": round(time.perf_counter() - began, 1),
        "event_counts": {k: kinds[k] for k in ("CANDIDATE", "ORDER_INTENT", "BROKER_ORDER", "ORDER_UPDATE",
                                                "ORDER_CANCEL", "EXIT_ORDER", "TRADE_OUTCOME",
                                                "POSITION_ADJUSTMENT", "SESSION_SKIP", "CYCLE_ERROR")},
        "bar_revisions_stored": sum(max((b.revision for b in store_bars), default=1) - 1
                                    for store_bars in _all_bars(home)),
        "broker_orders": dict(Counter(o.status for o in broker.orders.values())),
        "overdue_open_entry_orders": overdue,
        "final_positions": {k: round(v, 8) for k, v in state.positions.items() if abs(v) > 1e-12},
        "passed": report["stopped"] is None and not overdue and report["cycles_completed"] == cycles,
    })
    return report


def _all_bars(home: Path):
    with LocalStorage(home, writer=False) as store:
        for symbol, cls, _ in SOAK_ASSETS:
            yield store.load_bars(symbol, cls, all_revisions=True)

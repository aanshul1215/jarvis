"""The portfolio executor: trade the system's target weights on the Alpaca paper account, safely.

Each daily cycle (run once, at about 10:00 New York time, after the previous session's bars are stored):
1. reconcile with the broker (the same durable-journal rules as the rest of the desk: an order intent is written
   before every submission, and an unknown order or position stops trading);
2. compute today's target weights with exactly the research code (``TargetBuilder``: panel, sleeves, situation,
   the development-chosen blend method, the risk overlay with the desk's own drawdown);
3. turn weights into orders against the desk's capital (the owner's allocated capital plus its own profit or loss):
   sells first, then buys; skip changes under the no-trade band; whole shares for stocks (shorts must be whole);
4. enforce the owner policy on every order: per-order and per-asset caps, crypto never short, shorts at most 30%
   of capital, stale or wide quotes skipped, and after a daily-loss or drawdown stop only risk-reducing orders.
Buys are marketable limit orders (ask + 0.2%); sells are market orders.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np

from ..contracts import AssetClass, LedgerEvent, Mode, iso, new_id, utc_now
from ..engine import TradingEngine
from ..history import UniverseAsset
from ..market import stable_id
from ..risk import Governor, RiskPolicy
from ..storage import LocalStorage
from ..strategies import StrategyRegistry
from .allocator import SHORT_CAP, blend_schedule, overlay
from .backtest import BAND
from .situation import FEATURES

BUY_LIMIT_MARGIN = 0.002


class TargetBuilder:
    """Today's target weights from the research pipeline, for a given blend method."""

    def __init__(self, store: LocalStorage, universe: list[UniverseAsset], method: str):
        from .study import Book

        self.book = Book(store, universe)
        self.method = method
        self.blend = blend_schedule(method, self.book.sleeve_returns, self.book.features, self.book.labels,
                                    self.book.panel.dates)

    def targets(self, drawdown: float) -> tuple[dict[str, float], dict]:
        b, p = self.book, self.book.panel
        t = p.shape[0] - 1
        blend = self.blend[t]
        invested = float(blend.sum())
        stack = np.stack([np.nan_to_num(w[t]) for w in b.sleeves])
        mix = (blend / invested if invested > 0 else blend) @ stack
        weights = overlay(mix, invested, t, p, b.vols, b.returns, drawdown)
        diagnostics = {"decision_row_date": p.dates[t].isoformat(), "method": self.method,
                       "blend": dict(zip(b.sleeve_names, np.round(blend, 4).tolist())), "invested_share": invested,
                       "regime": b.labels[t], "situation": dict(zip(FEATURES, np.round(b.raw[t], 4).tolist())),
                       "drawdown_used": drawdown}
        return {a: float(w) for a, w in zip(p.assets, weights) if abs(w) > 1e-6}, diagnostics


@dataclass
class PlannedOrder:
    asset: str
    asset_class: AssetClass
    side: str
    quantity: float
    reference_price: float
    target_weight: float
    current_value: float
    reason: str = ""


@dataclass
class CycleReport:
    capital: float
    halted: bool
    planned: list[PlannedOrder] = field(default_factory=list)
    skipped: dict[str, str] = field(default_factory=dict)
    results: dict[str, str] = field(default_factory=dict)


class PortfolioDesk:
    def __init__(self, store: LocalStorage, broker, data, policy: RiskPolicy, universe: list[UniverseAsset], *,
                 clock=utc_now):
        if not policy.owner_approved or not policy.paper_enabled:
            raise ValueError("owner paper approval required")
        if "portfolio" not in policy.approved_strategies:
            raise ValueError("the owner policy does not approve the portfolio system ('portfolio' strategy)")
        if not policy.allocated_capital:
            raise ValueError("the portfolio desk needs allocated_capital in the owner policy")
        self.store, self.broker, self.data, self.policy, self.clock = store, broker, data, policy, clock
        self.universe = {a.symbol: a for a in universe if a.symbol in policy.approved_assets}
        self.engine = TradingEngine(store, broker, Governor(policy), StrategyRegistry([]), Mode.PAPER)

    def _event(self, kind: str, payload: dict, asset: str | None = None, reasons: tuple[str, ...] = ()) -> None:
        self.store.append_event(LedgerEvent(new_id("evt"), kind, utc_now(), new_id("pf"), asset_id=asset,
                                            payload=payload, reason_codes=reasons))

    def capital_and_state(self):
        self.engine.reconcile()
        state = self.engine._risk_state()
        return self.engine.desk_equity, state

    def plan(self, weights: dict[str, float], state, capital: float) -> CycleReport:
        p = self.policy
        halted = state.daily_pnl <= -p.max_daily_loss or state.drawdown >= p.max_drawdown
        report = CycleReport(capital, halted)
        equity_open = self.broker.equity_market_open()
        values = dict(state.position_values or {})
        shorts_now = -sum(v for v in values.values() if v < 0)
        sells, buys = [], []
        for asset, info in self.universe.items():
            target_w = weights.get(asset, 0.0)
            current_qty = state.positions.get(asset, 0.0)
            if target_w == 0 and abs(current_qty) < 1e-12:
                continue
            if info.asset_class == AssetClass.EQUITY and not equity_open:
                report.skipped[asset] = "MARKET_CLOSED"
                continue
            try:
                quote = self.data.latest_quote(asset, info.asset_class)
            except Exception as exc:  # no quote: leave the position as it is
                report.skipped[asset] = f"NO_QUOTE:{type(exc).__name__}"
                continue
            if self.clock() - quote.at > timedelta(seconds=p.max_quote_age_seconds):
                report.skipped[asset] = "STALE_QUOTE"
                continue
            if quote.spread_bps > p.max_spread_bps:
                report.skipped[asset] = "WIDE_SPREAD"
                continue
            mid = (quote.bid + quote.ask) / 2
            current = current_qty * mid
            target = float(np.clip(target_w * capital, -p.max_asset_notional, p.max_asset_notional))
            if info.asset_class == AssetClass.CRYPTO:
                target = max(0.0, target)
            delta = target - current
            if abs(delta) < BAND * capital:
                continue
            reducing = abs(target) < abs(current) and np.sign(target) in (0, np.sign(current))
            if halted and not reducing:
                report.skipped[asset] = "LOSS_STOP_ACTIVE"
                continue
            delta = float(np.clip(delta, -p.max_order_notional, p.max_order_notional))
            side = "BUY" if delta > 0 else "SELL"
            price = quote.ask * (1 + BUY_LIMIT_MARGIN) if side == "BUY" else quote.bid
            quantity = abs(delta) / price
            if info.asset_class == AssetClass.EQUITY:
                quantity = float(math.floor(quantity + 1e-9))
            else:
                quantity = math.floor(quantity * 1e8) / 1e8
                if side == "SELL":
                    quantity = min(quantity, max(0.0, current_qty))
            if quantity <= 0:
                report.skipped[asset] = "BELOW_ONE_UNIT"
                continue
            new_value = current + (quantity if side == "BUY" else -quantity) * mid
            if side == "SELL" and new_value < 0:
                extra_short = -new_value - max(0.0, -current)
                if shorts_now + extra_short > SHORT_CAP * capital + 1e-6:
                    report.skipped[asset] = "SHORT_CAP"
                    continue
                shorts_now += extra_short
            order = PlannedOrder(asset, info.asset_class, side, quantity, price, target_w, current)
            (sells if side == "SELL" else buys).append(order)
        report.planned = sells + buys
        return report

    def run_once(self, builder: TargetBuilder, *, decision_day: str) -> dict:
        capital, state = self.capital_and_state()
        weights, diagnostics = builder.targets(state.drawdown)
        self._event("PORTFOLIO_TARGET", {"capital": capital, "weights": weights, **diagnostics})
        report = self.plan(weights, state, capital)
        for order in report.planned:
            client_id = stable_id("pf", decision_day, order.asset, order.side, f"{order.quantity:.8f}")
            self.engine._record("ORDER_INTENT", client_id, asset_id=order.asset, payload={
                "intent_id": client_id, "client_order_id": client_id, "asset_class": order.asset_class.value,
                "decided_at": iso(self.clock()), "reference_price": order.reference_price, "quantity": order.quantity,
                "side": order.side, "strategy_id": "portfolio", "strategy_version": builder.method,
                "target_weight": order.target_weight, "current_value": order.current_value, "capital": capital,
                "decision_mid": None})
            try:
                placed = self.broker.submit(client_id, order.asset, order.asset_class, order.side, order.quantity,
                                            order.reference_price)
            except Exception as exc:  # recorded; reconciliation on the next run settles uncertain submissions
                report.results[order.asset] = f"ERROR:{type(exc).__name__}"
                self._event("ORDER_ERROR", {"client_order_id": client_id}, order.asset, (type(exc).__name__,))
                continue
            self.engine._record("BROKER_ORDER", client_id, asset_id=order.asset, payload={
                "client_order_id": client_id, "broker_order_id": placed.broker_order_id, "side": order.side,
                "status": placed.status, "filled_quantity": placed.filled_quantity,
                "average_price": placed.average_price})
            report.results[order.asset] = placed.status
        summary = {"capital": capital, "halted": report.halted, "orders": len(report.planned),
                   "results": report.results, "skipped": report.skipped,
                   "planned": [{"asset": o.asset, "side": o.side, "quantity": o.quantity,
                                "target_weight": round(o.target_weight, 4)} for o in report.planned]}
        self._event("PORTFOLIO_CYCLE", summary)
        return {**summary, "diagnostics": diagnostics}

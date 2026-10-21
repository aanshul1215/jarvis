"""The portfolio executor: trade the system's target weights on the Alpaca paper account, safely.

Each daily cycle (run once, at about 10:00 New York time, after the previous session's bars are stored):
1. reconcile with the broker (the same durable-journal rules as the rest of the desk: an order intent is written
   before every submission, and an unknown order or position stops trading), then cancel this desk's own unfilled
   orders from earlier cycles so a new plan never stacks on top of them;
2. compute today's target weights with exactly the research code (``TargetBuilder``: panel, sleeves, situation,
   the development-chosen blend method, the risk overlay with the desk's own drawdown);
3. turn weights into orders against the desk's capital (the owner's allocated capital plus its own profit or loss):
   sells first, then buys; skip changes under the no-trade band (a full exit is always allowed); whole shares for
   stocks (shorts must be whole); a close sells or buys back exactly the position; a long-to-short flip is done in
   two cycles (close, then open);
4. enforce the owner policy on every order: per-order, per-asset and total-holdings caps, buying power, crypto only
   if enabled and never short, shorts only where the broker allows them and at most 30% of capital, stale, future
   or wide quotes skipped, and after a daily-loss or drawdown stop only risk-reducing orders.
Buys are marketable limit orders (ask + 0.2%); sells are market orders. A submission the broker has no record of is
recorded as rejected, so a predictable refusal (for example "not shortable") cannot lock the desk in SAFE mode.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import timedelta

import numpy as np

from ..contracts import AssetClass, LedgerEvent, Mode, iso, new_id, utc_now
from ..engine import TradingEngine
from ..history import UniverseAsset
from ..market import stable_id
from ..risk import CLOCK_SKEW, Governor, RiskPolicy
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
    kind: str = ""  # CLOSE, REDUCE or ADD


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

    def cancel_own_open_orders(self) -> list[str]:
        """Cancel this desk's unfilled orders from earlier cycles (crypto orders are good-till-cancelled)."""
        cancelled = []
        for client_id in self.broker.state().open_order_ids:
            intent = self.store.index.intents.get(client_id)
            if intent and intent["payload"].get("strategy_id") == "portfolio":
                self.broker.cancel(client_id)
                self._event("ORDER_CANCEL", {"client_order_id": client_id}, intent.get("asset_id"), ("NEW_CYCLE",))
                cancelled.append(client_id)
        return cancelled

    def plan(self, weights: dict[str, float], state, capital: float) -> CycleReport:
        p = self.policy
        halted = state.daily_pnl <= -p.max_daily_loss or state.drawdown >= p.max_drawdown
        report = CycleReport(capital, halted)
        equity_open = self.broker.equity_market_open()
        values = dict(state.position_values or {})
        shorts_now = -sum(v for v in values.values() if v < 0)
        gross_now = sum(abs(v) for v in values.values())
        cash_left = min(state.buying_power, state.cash)
        now = self.clock()
        sells, buys = [], []
        for asset, info in self.universe.items():
            target_w = weights.get(asset, 0.0)
            current_qty = state.positions.get(asset, 0.0)
            if target_w == 0 and abs(current_qty) < 1e-12:
                continue
            if info.asset_class == AssetClass.CRYPTO and not p.crypto_enabled:
                target_w = 0.0  # crypto not enabled by the owner: only exits
            if info.asset_class == AssetClass.EQUITY and not equity_open:
                report.skipped[asset] = "MARKET_CLOSED"
                continue
            try:
                quote = self.data.latest_quote(asset, info.asset_class)
            except Exception as exc:  # no quote: leave the position as it is
                report.skipped[asset] = f"NO_QUOTE:{type(exc).__name__}"
                continue
            if now - quote.at > timedelta(seconds=p.max_quote_age_seconds) or quote.at > now + CLOCK_SKEW:
                report.skipped[asset] = "STALE_OR_FUTURE_QUOTE"
                continue
            if quote.spread_bps > p.max_spread_bps:
                report.skipped[asset] = "WIDE_SPREAD"
                continue
            mid = (quote.bid + quote.ask) / 2
            current = current_qty * mid
            target = float(np.clip(target_w * capital, -p.max_asset_notional, p.max_asset_notional))
            if info.asset_class == AssetClass.CRYPTO:
                target = max(0.0, target)
            if current and target and np.sign(target) != np.sign(current):
                target = 0.0  # a flip is done in two cycles: close today, open the other side next time
            delta = target - current
            closing = target == 0 and current != 0
            reducing = abs(target) < abs(current) and (target == 0 or np.sign(target) == np.sign(current))
            if abs(delta) < BAND * capital and not closing:
                continue
            if halted and not reducing:
                report.skipped[asset] = "LOSS_STOP_ACTIVE"
                continue
            side = "BUY" if delta > 0 else "SELL"
            price = quote.ask * (1 + BUY_LIMIT_MARGIN) if side == "BUY" else quote.bid
            if closing:
                quantity = abs(current_qty)  # exactly the position: no stub, never an accidental short
            else:
                # Adding risk is sized at the limit price (so the order never costs more than the cap); reducing
                # is sized at the mid and never exceeds the position.
                quantity = min(abs(delta), p.max_order_notional) / (mid if reducing else price)
                if reducing:
                    quantity = min(quantity, abs(current_qty))
                quantity = float(math.floor(quantity + 1e-9)) if info.asset_class == AssetClass.EQUITY \
                    else math.floor(quantity * 1e8) / 1e8
            if quantity <= 0:
                report.skipped[asset] = "BELOW_ONE_UNIT"
                continue
            new_value = current + (quantity if side == "BUY" else -quantity) * mid
            if new_value < -1e-9:
                if info.asset_class == AssetClass.CRYPTO or not self.broker.shortable(asset):
                    report.skipped[asset] = "NOT_SHORTABLE"
                    continue
                extra_short = -new_value - max(0.0, -current)
                if shorts_now + extra_short > SHORT_CAP * capital + 1e-6:
                    report.skipped[asset] = "SHORT_CAP"
                    continue
                shorts_now += extra_short
            gross_change = abs(new_value) - abs(current)
            if gross_change > 0 and gross_now + gross_change > p.max_portfolio_notional + 1e-6:
                report.skipped[asset] = "PORTFOLIO_CAP"
                continue
            if side == "BUY" and new_value > 0 and quantity * price > cash_left:
                report.skipped[asset] = "BUYING_POWER"
                continue
            gross_now += gross_change
            if side == "BUY":
                cash_left -= quantity * price
            order = PlannedOrder(asset, info.asset_class, side, quantity, price, target_w, current,
                                 "CLOSE" if closing else ("REDUCE" if reducing else "ADD"))
            (sells if side == "SELL" else buys).append(order)
        report.planned = sells + buys
        return report

    def run_once(self, builder: TargetBuilder, *, decision_day: str) -> dict:
        capital, state = self.capital_and_state()
        cancelled = self.cancel_own_open_orders()
        if cancelled:  # partial fills may have changed positions: reconcile again before planning
            capital, state = self.capital_and_state()
        weights, diagnostics = builder.targets(state.drawdown)
        self._event("PORTFOLIO_TARGET", {"capital": capital, "weights": weights, **diagnostics})
        report = self.plan(weights, state, capital)
        for order in report.planned:
            client_id = stable_id("pf", decision_day, order.asset, order.side, f"{order.quantity:.8f}")
            if client_id in self.store.index.intents:
                report.results[order.asset] = "ALREADY_SENT"
                continue
            self.engine._record("ORDER_INTENT", client_id, asset_id=order.asset, payload={
                "intent_id": client_id, "client_order_id": client_id, "asset_class": order.asset_class.value,
                "decided_at": iso(self.clock()), "reference_price": order.reference_price, "quantity": order.quantity,
                "side": order.side, "strategy_id": "portfolio", "strategy_version": builder.method,
                "target_weight": order.target_weight, "current_value": order.current_value, "capital": capital,
                "kind": order.kind})
            try:
                placed = self.broker.submit(client_id, order.asset, order.asset_class, order.side, order.quantity,
                                            order.reference_price)
            except Exception as exc:
                # If the broker has no record of the order, it was refused: record that, so reconciliation does
                # not mistake it for a lost order. If the broker cannot be asked, leave it to reconciliation.
                try:
                    known = self.broker.find_order(client_id)
                except Exception:
                    known = "UNKNOWN"
                if known is None:
                    self.engine._record("ORDER_UPDATE", client_id, asset_id=order.asset, payload={
                        "client_order_id": client_id, "side": order.side, "status": "REJECTED",
                        "filled_quantity": 0.0, "average_price": None, "error": type(exc).__name__})
                    report.results[order.asset] = f"REJECTED:{type(exc).__name__}"
                else:
                    report.results[order.asset] = f"UNCERTAIN:{type(exc).__name__}"
                continue
            self.engine._record("BROKER_ORDER", client_id, asset_id=order.asset, payload={
                "client_order_id": client_id, "broker_order_id": placed.broker_order_id, "side": order.side,
                "status": placed.status, "filled_quantity": placed.filled_quantity,
                "average_price": placed.average_price})
            report.results[order.asset] = placed.status
        summary = {"capital": capital, "halted": report.halted, "orders": len(report.planned),
                   "cancelled_open_orders": len(cancelled), "results": report.results, "skipped": report.skipped,
                   "planned": [{"asset": o.asset, "side": o.side, "quantity": o.quantity, "kind": o.kind,
                                "target_weight": round(o.target_weight, 4)} for o in report.planned]}
        self._event("PORTFOLIO_CYCLE", summary)
        return {**summary, "diagnostics": diagnostics}

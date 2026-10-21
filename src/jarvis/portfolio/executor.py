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
import time
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
from .allocator import DD_WINDOW, SHORT_CAP, drawdown_multiplier, overlay
from .backtest import BAND, BAND_REL
from .situation import FEATURES

BUY_LIMIT_MARGIN = 0.002
EQUITY_HISTORY = "portfolio-equity-history"  # the desk's equity per decision day, for the drawdown control
BUILD_COMPLETE = "desk-build-complete"  # written after a new desk's first full pass with nothing skipped


class TargetBuilder:
    """Today's target weights from the research pipeline, for a given blend method."""

    def __init__(self, store: LocalStorage, universe: list[UniverseAsset], method: str):
        from .study import Book

        self.book = Book(store, universe)
        self.method = method
        self.blend = self.book.blend(method)

    def is_rebalance_day(self) -> bool:
        """Weekly rebalance: the latest stored session is the first of its week (the research rule)."""
        p = self.book.panel
        return (p.shape[0] - 1) in self.book.rebalance_rows

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
                       "drawdown_used": drawdown, "rebalance_day": self.is_rebalance_day()}
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
    """``strategy_id`` names the desk in the owner policy and in every order intent. The round 7 desks (sector
    rotation, stock book) pass ``use_brake=False`` (no drawdown brake by design; the Governor's stops remain), their
    own research no-trade band, and the stock book ``fractional=True``. ``approved`` replaces the policy's asset list
    when the owner approved a rule instead (for example the month's top-300 stocks)."""

    def __init__(self, store: LocalStorage, broker, data, policy: RiskPolicy, universe: list[UniverseAsset], *,
                 clock=utc_now, strategy_id: str = "portfolio", fractional: bool = False, band: float = BAND,
                 band_rel: float = BAND_REL, use_brake: bool = True, pause: float = 0.0,
                 approved: set[str] | None = None, quote_retries: int = 0):
        if not policy.owner_approved or not policy.paper_enabled:
            raise ValueError("owner paper approval required")
        if strategy_id not in policy.approved_strategies:
            raise ValueError(f"the owner policy does not approve the '{strategy_id}' desk")
        if not policy.allocated_capital:
            raise ValueError("the portfolio desk needs allocated_capital in the owner policy")
        self.store, self.broker, self.data, self.policy, self.clock = store, broker, data, policy, clock
        self.strategy_id, self.fractional, self.band, self.band_rel = strategy_id, fractional, band, band_rel
        self.use_brake, self.pause, self.quote_retries = use_brake, pause, quote_retries
        allowed = set(policy.approved_assets) if approved is None else approved
        self.universe = {a.symbol: a for a in universe if a.symbol in allowed}
        self.engine = TradingEngine(store, broker, Governor(policy), StrategyRegistry([]), Mode.PAPER)

    def _event(self, kind: str, payload: dict, asset: str | None = None, reasons: tuple[str, ...] = ()) -> None:
        self.store.append_event(LedgerEvent(new_id("evt"), kind, utc_now(), new_id("pf"), asset_id=asset,
                                            payload=payload, reason_codes=reasons))

    def capital_and_state(self):
        self.engine.reconcile()
        state = self.engine._risk_state()
        return self.engine.desk_equity, state

    def brake_drawdown(self, capital: float, day: str) -> float:
        """Drawdown from the highest desk equity of the last DD_WINDOW decision days (the research rule); the
        Governor's hard stop keeps using the all-time peak."""
        try:
            history = [h for h in self.store.load_json(EQUITY_HISTORY)["equity"] if h[0] != day]
        except FileNotFoundError:
            history = []
        history = (history + [[day, capital]])[-DD_WINDOW:]
        if getattr(self.store, "durable", True):
            self.store.publish_json(EQUITY_HISTORY, {"equity": history})
        peak = max(e for _, e in history)
        return 1 - capital / peak if peak > 0 else 0.0

    def _built(self) -> bool:
        try:
            self.store.load_json(BUILD_COMPLETE)
            return True
        except FileNotFoundError:
            return False

    def cancel_own_open_orders(self) -> list[str]:
        """Cancel this desk's unfilled orders from earlier cycles (crypto orders are good-till-cancelled)."""
        cancelled = []
        for client_id in self.broker.state().open_order_ids:
            intent = self.store.index.intents.get(client_id)
            if intent and intent["payload"].get("strategy_id") == self.strategy_id:
                self.broker.cancel(client_id)
                self._event("ORDER_CANCEL", {"client_order_id": client_id}, intent.get("asset_id"), ("NEW_CYCLE",))
                cancelled.append(client_id)
        return cancelled

    def plan(self, weights: dict[str, float], state, capital: float, *, reduce_only: bool = False) -> CycleReport:
        p = self.policy
        halted = state.daily_pnl <= -p.max_daily_loss or state.drawdown >= p.max_drawdown or reduce_only
        report = CycleReport(capital, halted)
        equity_open = self.broker.equity_market_open()
        values = dict(state.position_values or {})
        shorts_now = -sum(v for v in values.values() if v < 0)
        gross_now = sum(abs(v) for v in values.values())
        cash_left = state.buying_power  # margin is allowed (owner: up to 2x); the holdings cap bounds the total
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
            now = self.clock()  # per quote: fetching hundreds of quotes takes minutes
            if now - quote.at > timedelta(seconds=p.max_quote_age_seconds) or quote.at > now + CLOCK_SKEW:
                report.skipped[asset] = "STALE_OR_FUTURE_QUOTE"
                continue
            for _ in range(self.quote_retries):  # free single-exchange quotes widen briefly; look again
                if quote.spread_bps <= p.max_spread_bps:
                    break
                time.sleep(2.0)
                try:
                    quote = self.data.latest_quote(asset, info.asset_class)
                except Exception:
                    break
                now = self.clock()
                if now - quote.at > timedelta(seconds=p.max_quote_age_seconds) or quote.at > now + CLOCK_SKEW:
                    break
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
            if abs(delta) < max(self.band * capital, self.band_rel * abs(target)) and not closing:
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
                if info.asset_class == AssetClass.EQUITY and not self.fractional:
                    quantity = float(math.floor(quantity + 1e-9))
                elif info.asset_class == AssetClass.EQUITY:
                    quantity = math.floor(quantity * 1e4) / 1e4  # fractional shares
                    if quantity * mid < 1.0:  # Alpaca's minimum fractional order is $1
                        report.skipped[asset] = "BELOW_ONE_DOLLAR"
                        continue
                else:
                    quantity = math.floor(quantity * 1e8) / 1e8
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
        brake = self.brake_drawdown(capital, decision_day) if self.use_brake else 0.0
        weights, diagnostics = builder.targets(brake)
        diagnostics = {**diagnostics, "all_time_drawdown": state.drawdown}
        self._event("PORTFOLIO_TARGET", {"capital": capital, "weights": weights, **diagnostics})
        rebalance = getattr(builder, "is_rebalance_day", lambda: True)()
        building = not self._built()
        if not rebalance and building:
            rebalance = True  # a new desk keeps building its target positions until one full pass skips nothing
            diagnostics = {**diagnostics, "initial_build": True}
        if not rebalance and drawdown_multiplier(brake) >= 1.0:
            summary = {"capital": capital, "halted": False, "orders": 0, "cancelled_open_orders": len(cancelled),
                       "results": {}, "skipped": {}, "planned": [], "note": "not a rebalance day; holding"}
            self._event("PORTFOLIO_CYCLE", summary)
            return {**summary, "diagnostics": diagnostics}
        # Between weekly rebuilds only risk-reducing orders are allowed (the drawdown control tightening).
        report = self.plan(weights, state, capital, reduce_only=not rebalance)
        for order in report.planned:
            client_id = stable_id("pf", decision_day, order.asset, order.side, f"{order.quantity:.8f}")
            if client_id in self.store.index.intents:
                report.results[order.asset] = "ALREADY_SENT"
                continue
            self.engine._record("ORDER_INTENT", client_id, asset_id=order.asset, payload={
                "intent_id": client_id, "client_order_id": client_id, "asset_class": order.asset_class.value,
                "decided_at": iso(self.clock()), "reference_price": order.reference_price, "quantity": order.quantity,
                "side": order.side, "strategy_id": self.strategy_id, "strategy_version": builder.method,
                "target_weight": order.target_weight, "current_value": order.current_value, "capital": capital,
                "kind": order.kind})
            if self.pause:
                time.sleep(self.pause)  # stay inside the broker's request rate limit on large rebalances
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
        if building and not report.halted and set(report.skipped.values()) <= {"BELOW_ONE_DOLLAR"}:
            if getattr(self.store, "durable", True):
                self.store.publish_json(BUILD_COMPLETE, {"day": decision_day, "orders": len(report.planned)})
        summary = {"capital": capital, "halted": report.halted, "orders": len(report.planned),
                   "cancelled_open_orders": len(cancelled), "results": report.results, "skipped": report.skipped,
                   "planned": [{"asset": o.asset, "side": o.side, "quantity": o.quantity, "kind": o.kind,
                                "target_weight": round(o.target_weight, 4)} for o in report.planned]}
        self._event("PORTFOLIO_CYCLE", summary)
        return {**summary, "diagnostics": diagnostics}

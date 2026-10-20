"""Fast decision path: evidence -> strategy -> Governor -> durable intent -> broker."""

from __future__ import annotations

import math
from dataclasses import asdict, replace
from datetime import datetime, timedelta
from typing import Any

from .broker import BrokerAdapter, BrokerError, UncertainSubmission
from .contracts import AssetClass, Bar, Candidate, LedgerEvent, Mode, StrategyIntent, iso, new_id, utc_now
from .market import features_for, scan, stable_id, validate_feed
from .risk import BrokerState, Governor
from .storage import LocalStorage, StorageError
from .strategies import StrategyRegistry, select_intent


# Alpaca takes the crypto trading fee from the asset received, so after a crypto buy the broker position is
# slightly smaller than the filled quantity (research briefs 18 and 21; confirm on the first paper fill).
# Shortfalls up to this fraction of the quantity bought are recorded as fee adjustments instead of SAFE.
CRYPTO_FEE_TOLERANCE = 0.004
EQUITY_HIGH_WATER = "equity-high-water"
# Simulated brokers allowed to execute in SHADOW mode (mock, soak and replay); never a real broker adapter.
MOCK_BROKERS = ("MockBroker", "SimBroker", "ReplayBroker")
# Quantities are sent with at most this many decimals, rounded down so a sell never exceeds the position.
QUANTITY_DECIMALS = 8
# A leftover position worth less than this (for example fee dust after a crypto exit) is treated as flat.
# ASSUMPTION: confirm the broker's minimum order size per asset in the Phase 0 probe.
DUST_NOTIONAL = 1.0


def sellable_quantity(position: float) -> float:
    scale = 10 ** QUANTITY_DECIMALS
    return math.floor(position * scale + 1e-6) / scale if position > 0 else 0.0


def is_dust(position: float, price: float) -> bool:
    return position <= 0 or sellable_quantity(position) * price < DUST_NOTIONAL


class TradingEngine:
    def __init__(self, store: LocalStorage, broker: BrokerAdapter, governor: Governor,
                 registry: StrategyRegistry, mode: Mode):
        self.store, self.broker, self.governor, self.registry, self.mode = store, broker, governor, registry, mode
        self._ready = False

    def reconcile(self) -> None:
        """Broker truth is checked before new risk after each process start."""
        index = self.store.index
        for client_id in list(index.intents):
            previous = index.latest_order.get(client_id)
            if previous and previous["payload"].get("status") in ("FILLED", "CANCELED", "REJECTED", "EXPIRED"):
                continue
            order = self.broker.find_order(client_id)
            if order is None:
                self.mode = Mode.SAFE
                raise BrokerError("durable order intent has no broker record; SAFE")
            if order is not None and (previous is None or previous["payload"].get("status") != order.status
                                      or float(previous["payload"].get("filled_quantity", 0)) != order.filled_quantity):
                self._record("ORDER_UPDATE", client_id, asset_id=order.asset_id, payload={
                    "client_order_id": client_id, "broker_order_id": order.broker_order_id,
                    "side": order.side, "status": order.status,
                    "filled_quantity": order.filled_quantity, "average_price": order.average_price})
        state = self.broker.state()
        if not state.reconciled:
            self.mode = Mode.SAFE
            raise BrokerError("broker unreconciled")
        if any(client_id not in index.intents and client_id not in index.latest_order
               for client_id in state.open_order_ids):
            self.mode = Mode.SAFE
            raise BrokerError("unknown broker order; SAFE")
        expected: dict[str, float] = {}
        bought: dict[str, float] = {}
        for event in index.latest_order.values():
            asset = event.get("asset_id")
            side = event["payload"].get("side", "BUY")
            filled = float(event["payload"].get("filled_quantity", 0))
            if asset:
                expected[asset] = expected.get(asset, 0) + (filled if side == "BUY" else -filled)
                if side == "BUY":
                    bought[asset] = bought.get(asset, 0) + filled
        for asset, delta in index.adjustments.items():
            expected[asset] = expected.get(asset, 0) + delta
        for asset in sorted(set(expected) | set(state.positions)):
            difference = state.positions.get(asset, 0) - expected.get(asset, 0)
            if abs(difference) <= 1e-7:
                continue
            is_crypto = asset in index.crypto_assets or "/" in asset
            if is_crypto and difference < 0 and -difference <= bought.get(asset, 0) * CRYPTO_FEE_TOLERANCE + 1e-9:
                self._record("POSITION_ADJUSTMENT", new_id("fee"), asset_id=asset,
                             payload={"delta": difference, "reason": "CRYPTO_FEE_IN_RECEIVED_ASSET",
                                      "evidence": "UNVERIFIED_UNTIL_PAPER_PROBE"},
                             reason_codes=("CRYPTO_FEE_ADJUSTMENT",))
                continue
            self.mode = Mode.SAFE
            raise BrokerError("unknown or mismatched broker position; SAFE")
        self._record("RECONCILED", new_id("reconcile"), payload={"open_orders": len(state.open_order_ids),
                                                                  "positions": state.positions})
        self._ready = True

    def _risk_state(self) -> BrokerState:
        """Broker state plus drawdown from the stored equity high-water mark (a fraction of peak equity)."""
        state = self.broker.state()
        try:
            peak = float(self.store.load_json(EQUITY_HIGH_WATER)["equity"])
        except FileNotFoundError:
            peak = 0.0
        if state.equity > peak:
            self.store.publish_json(EQUITY_HIGH_WATER, {"equity": state.equity, "at": iso(utc_now())})
            peak = state.equity
        drawdown = 1 - state.equity / peak if peak > 0 else 0.0
        return replace(state, drawdown=max(state.drawdown, drawdown))

    def _record(self, kind: str, correlation_id: str, *, asset_id: str | None = None,
                payload: dict[str, Any] | None = None, reason_codes: tuple[str, ...] = ()) -> str:
        return self.store.append_event(LedgerEvent(new_id("evt"), kind, utc_now(), correlation_id,
                                                   asset_id=asset_id, payload=payload or {},
                                                   reason_codes=reason_codes))

    def process(self, bars: list[Bar], *, as_of: datetime | None = None,
                reference_price: float | None = None, spread_bps: float = 5,
                quantity: float = 1, quote_at: datetime | None = None) -> list[dict[str, Any]]:
        if not self._ready:
            raise BrokerError("reconcile before processing")
        now = as_of or utc_now()
        if self.mode == Mode.PAPER and (quote_at is None or reference_price is None):
            self._record("NO_TRADE", new_id("quote"), reason_codes=("VERIFIED_QUOTE_REQUIRED",))
            return []
        valid, reasons = validate_feed(bars)
        if not valid:
            self._record("DATA_QUARANTINE", new_id("feed"), reason_codes=reasons)
            return []
        snapshot = features_for(bars, now)
        self.store.save_features([snapshot])
        self._record("FEATURE_SNAPSHOT", snapshot.snapshot_id, asset_id=snapshot.asset_id,
                     payload={"snapshot_id": snapshot.snapshot_id, "values": snapshot.values,
                              "available_at": iso(snapshot.available_at)})
        results = []
        for candidate in scan(snapshot, now):
            self._record("CANDIDATE", candidate.candidate_id, asset_id=candidate.asset_id,
                         payload={"candidate_id": candidate.candidate_id, "trigger": candidate.trigger,
                                  "score": candidate.score, "expires_at": iso(candidate.expires_at)})
            price = reference_price if reference_price is not None else bars[-1].close
            intent = select_intent(candidate, snapshot, self.registry, self.mode, now,
                                   quantity=quantity, reference_price=price)
            if intent is None:
                self._record("NO_TRADE", candidate.candidate_id, asset_id=candidate.asset_id,
                             reason_codes=("NO_APPROVED_STRATEGY",))
                results.append({"candidate": candidate.candidate_id, "result": "FLAT"})
                continue
            client_id = stable_id("jarvis", intent.intent_id)
            risk = self.governor.assess(intent, self._risk_state(), self.mode, now, quote_at or bars[-1].available_at,
                                         spread_bps, client_id, self.store.index.entry_ids,
                                         mock=self.broker.__class__.__name__ in MOCK_BROKERS)
            self._record("RISK_DECISION", candidate.candidate_id, asset_id=candidate.asset_id,
                         payload={"intent_id": intent.intent_id, "result": risk.result,
                                  "policy_version": risk.policy_version}, reason_codes=risk.reason_codes)
            if risk.result != "ALLOW":
                results.append({"candidate": candidate.candidate_id, "result": "BLOCK", "reasons": risk.reason_codes})
                continue
            # A durable intent always precedes the external call.
            self._record("ORDER_INTENT", candidate.candidate_id, asset_id=candidate.asset_id,
                         payload={"intent_id": intent.intent_id, "client_order_id": client_id,
                                  "asset_class": intent.asset_class.value,
                                  "expires_at": iso(intent.expires_at),
                                  "quantity": risk.allowed_quantity, "side": intent.side,
                                  "strategy_id": intent.strategy_id, "strategy_version": intent.strategy_version,
                                  "model_id": intent.model_id, "model_version": intent.model_version,
                                  "entry_bar_end_at": iso(bars[-1].end_at),
                                  "exit_after_bars": intent.exit_after_bars})
            try:
                order = self.broker.submit(client_id, intent.asset_id, intent.asset_class,
                                           intent.side, risk.allowed_quantity, intent.reference_price)
            except UncertainSubmission:
                order = self.broker.find_order(client_id)
                if order is None:
                    self.mode = Mode.SAFE
                    self._record("ORDER_UNKNOWN", candidate.candidate_id, reason_codes=("BROKER_LOOKUP_MISSING",))
                    results.append({"candidate": candidate.candidate_id, "result": "SAFE"})
                    continue
            except BrokerError as exc:
                self.mode = Mode.SAFE
                self._record("ORDER_ERROR", candidate.candidate_id, asset_id=candidate.asset_id,
                             reason_codes=(type(exc).__name__,))
                results.append({"candidate": candidate.candidate_id, "result": "SAFE"})
                continue
            self._record("BROKER_ORDER", candidate.candidate_id, asset_id=candidate.asset_id,
                         payload={"client_order_id": client_id, "broker_order_id": order.broker_order_id,
                                  "side": order.side,
                                  "status": order.status, "filled_quantity": order.filled_quantity,
                                  "average_price": order.average_price})
            results.append({"candidate": candidate.candidate_id, "result": order.status,
                            "client_order_id": client_id})
        return results

    def exit_position(self, asset_id: str, asset_class, price: float, *, reason: str) -> str:
        if not self._ready or self.mode not in (Mode.SHADOW, Mode.PAPER):
            raise BrokerError("exit path unavailable")
        state = self.broker.state()
        position = state.positions.get(asset_id, 0)
        if is_dust(position, price):
            return "FLAT"
        qty = sellable_quantity(position)
        # The exit ID is tied to the entry it closes. An ID built from asset, reason and quantity alone repeats on
        # the next identical trade, so the old filled exit was found and no new sell was ever placed.
        index = self.store.index
        entries = index.entries_by_asset.get(asset_id, [])
        client_id = stable_id("exit", asset_id, entries[-1]["payload"]["client_order_id"] if entries else "no-entry",
                              reason, str(qty))
        self._record("EXIT_INTENT", client_id, asset_id=asset_id,
                     payload={"client_order_id": client_id, "quantity": qty, "reason": reason})
        order = self.broker.find_order(client_id)
        if order is None:
            try:
                order = self.broker.submit(client_id, asset_id, asset_class, "SELL", qty, price)
            except UncertainSubmission:
                order = self.broker.find_order(client_id)
                if order is None:
                    self.mode = Mode.SAFE
                    self._record("ORDER_UNKNOWN", client_id, asset_id=asset_id,
                                 reason_codes=("EXIT_BROKER_LOOKUP_MISSING",))
                    return "SAFE"
        self._record("EXIT_ORDER", client_id, asset_id=asset_id,
                     payload={"client_order_id": client_id, "broker_order_id": order.broker_order_id,
                              "side": "SELL",
                              "status": order.status, "filled_quantity": order.filled_quantity})
        already_recorded = client_id in index.outcome_ids
        if order.status == "FILLED" and order.average_price is not None and not already_recorded:
            by_client = index.buy_orders_by_asset.get(asset_id, {})
            fills = [event for event in by_client.values()
                       # A partially filled entry whose remainder was cancelled or expired still opened the position.
                       if event["payload"].get("side") == "BUY"
                       and float(event["payload"].get("filled_quantity") or 0) > 0]
            costs = []
            remaining = order.filled_quantity
            for entry in reversed(fills):
                if remaining <= 0:
                    break
                if entry["payload"].get("average_price") is None:
                    continue
                used = min(remaining, float(entry["payload"]["filled_quantity"]))
                costs.append((used, float(entry["payload"]["average_price"])))
                remaining -= used
            if costs and remaining <= 1e-8:
                entry_price = sum(q * p for q, p in costs) / sum(q for q, _ in costs)
                strategy = entries[-1]["payload"] if entries else {}
                self._record("TRADE_OUTCOME", client_id, asset_id=asset_id,
                             payload={"entry_price_estimate": entry_price, "exit_price": order.average_price,
                                      "filled_quantity": order.filled_quantity,
                                      "gross_pnl_estimate": (order.average_price - entry_price) * order.filled_quantity,
                                      "fees_and_slippage": "UNKNOWN", "reason": reason,
                                      "strategy_id": strategy.get("strategy_id"),
                                      "strategy_version": strategy.get("strategy_version"),
                                      "model_id": strategy.get("model_id"),
                                      "model_version": strategy.get("model_version"),
                                      "evidence_class": getattr(self.broker, "evidence_class", "PAPER")})
        return order.status

    def monitor_positions(self, bars: list[Bar]) -> list[dict[str, Any]]:
        """Apply the strategy's recorded time exit to reconciled open positions."""
        if not self._ready:
            raise BrokerError("reconcile before monitoring")
        if not bars:
            return []
        asset = bars[-1].asset_id
        if is_dust(self.broker.state().positions.get(asset, 0), bars[-1].close):
            return []
        for intent in reversed(self.store.index.entries_by_asset.get(asset, [])):
            payload = intent["payload"]
            entry_end = payload.get("entry_bar_end_at")
            limit = payload.get("exit_after_bars")
            if entry_end is None or limit is None:
                continue
            from .contracts import parse_utc
            elapsed = sum(b.end_at > parse_utc(entry_end) for b in bars)
            if elapsed >= limit:
                status = self.exit_position(asset, bars[-1].asset_class, bars[-1].close, reason="TIME_EXIT")
                return [{"asset_id": asset, "exit_reason": "TIME_EXIT", "status": status}]
            return [{"asset_id": asset, "exit_reason": "HOLD", "bars_remaining": limit - elapsed}]
        self.mode = Mode.SAFE
        self._record("POSITION_UNKNOWN", new_id("position"), asset_id=asset,
                     reason_codes=("MISSING_ENTRY_CONTRACT",))
        return [{"asset_id": asset, "exit_reason": "SAFE"}]

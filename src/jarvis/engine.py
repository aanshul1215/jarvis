"""Fast decision path: evidence -> strategy -> Governor -> durable intent -> broker."""

from __future__ import annotations

import math
from dataclasses import asdict, replace
from datetime import datetime, timedelta
from typing import Any

from .broker import BrokerAdapter, BrokerError, UncertainSubmission
from .contracts import (AssetClass, Bar, Candidate, FeatureSnapshot, LedgerEvent, Mode, StrategyIntent, iso, new_id,
                        parse_utc, utc_now)
from .market import features_for, scan, stable_id, validate_feed
from .risk import BrokerState, Governor
from .storage import LocalStorage, StorageError
from .strategies import DecisionContext, OpenPosition, StrategyRegistry, select_intent


# Alpaca takes the crypto trading fee from the asset received, so after a crypto buy the broker position is
# slightly smaller than the filled quantity (research briefs 18 and 21; confirm on the first paper fill).
# Shortfalls up to this fraction of the quantity bought are recorded as fee adjustments instead of SAFE.
CRYPTO_FEE_TOLERANCE = 0.004
EQUITY_HIGH_WATER = "equity-high-water"
CAPITAL_BASELINE = "capital-baseline"  # account equity when JARVIS first ran with an allocated capital
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


def _round_down(quantity: float, asset_class: AssetClass) -> float:
    if asset_class == AssetClass.EQUITY:
        return float(math.floor(quantity + 1e-9))
    scale = 10 ** QUANTITY_DECIMALS
    return math.floor(quantity * scale + 1e-6) / scale


class TradingEngine:
    def __init__(self, store: LocalStorage, broker: BrokerAdapter, governor: Governor,
                 registry: StrategyRegistry, mode: Mode):
        self.store, self.broker, self.governor, self.registry, self.mode = store, broker, governor, registry, mode
        self._ready = False
        self._peak: float | None = None  # equity high-water mark, loaded once from the store
        self._baseline: float | None = None  # account equity at the first run, when capital is allocated
        # Phase 7 strategy selector hooks (None = every strategy at its base size, no trade filter):
        # ``allocation(now)`` -> {strategy_id: size multiplier}; ``entry_filter(strategy_id, snapshot, now)`` -> bool.
        self.allocation = None
        self.entry_filter = None

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
        """Broker state plus drawdown from the stored equity high-water mark (a fraction of peak equity).

        With an allocated capital, the equity tracked is JARVIS's own: the allocation plus the account's change since
        the first run (recorded once as the baseline), so a large paper account cannot hide a large loss.
        """
        state = self.broker.state()
        equity = state.equity
        allocated = getattr(self.governor.policy, "allocated_capital", None) if self.governor.policy else None
        if allocated:
            durable = getattr(self.store, "durable", True)
            if self._baseline is None:
                try:
                    self._baseline = float(self.store.load_json(CAPITAL_BASELINE)["account_equity"])
                except FileNotFoundError:
                    self._baseline = state.equity
                    if durable:
                        self.store.publish_json(CAPITAL_BASELINE, {"account_equity": state.equity,
                                                                   "allocated_capital": allocated, "at": iso(utc_now())})
            equity = allocated + (state.equity - self._baseline)
        if self._peak is None:
            try:
                self._peak = float(self.store.load_json(EQUITY_HIGH_WATER)["equity"])
            except FileNotFoundError:
                self._peak = 0.0
        peak = self._peak
        if equity > peak:
            self._peak = peak = equity
            if getattr(self.store, "durable", True):  # replays keep the peak in memory only
                self.store.publish_json(EQUITY_HIGH_WATER, {"equity": equity, "at": iso(utc_now())})
        drawdown = 1 - equity / peak if peak > 0 else 0.0
        return replace(state, drawdown=max(state.drawdown, drawdown))

    def _record(self, kind: str, correlation_id: str, *, asset_id: str | None = None,
                payload: dict[str, Any] | None = None, reason_codes: tuple[str, ...] = ()) -> str:
        return self.store.append_event(LedgerEvent(new_id("evt"), kind, utc_now(), correlation_id,
                                                   asset_id=asset_id, payload=payload or {},
                                                   reason_codes=reason_codes))

    def process(self, bars: list[Bar], *, as_of: datetime | None = None,
                reference_price: float | None = None, spread_bps: float = 5,
                quantity: float = 1, quote_at: datetime | None = None,
                feature_horizon: timedelta = timedelta(hours=1),
                persist_features: bool = True, context: DecisionContext | None = None,
                snapshot: FeatureSnapshot | None = None, sizing: dict[str, Any] | None = None) -> list[dict[str, Any]]:
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
        if snapshot is None or snapshot.asset_id != bars[-1].asset_id:
            snapshot = features_for(bars, now, horizon=feature_horizon)
        if persist_features:
            self.store.save_features([snapshot])
        self._record("FEATURE_SNAPSHOT", snapshot.snapshot_id, asset_id=snapshot.asset_id,
                     payload={"snapshot_id": snapshot.snapshot_id, "values": snapshot.values,
                              "available_at": iso(snapshot.available_at)})
        # Strategy detectors decide what is tradable; the generic scanner adds other anomalies for observation only.
        merged = {c.trigger: c for c in scan(snapshot, now)}
        merged.update({c.trigger: c for c in self.registry.candidates(snapshot, now, self.mode, context)})
        results = []
        for candidate in sorted(merged.values(), key=lambda c: c.score, reverse=True):
            self._record("CANDIDATE", candidate.candidate_id, asset_id=candidate.asset_id,
                         payload={"candidate_id": candidate.candidate_id, "trigger": candidate.trigger,
                                  "score": candidate.score, "detected_at": iso(candidate.detected_at),
                                  "expires_at": iso(candidate.expires_at)})
            price = reference_price if reference_price is not None else bars[-1].close
            intent = select_intent(candidate, snapshot, self.registry, self.mode, now,
                                   quantity=quantity, reference_price=price)
            if intent is None:
                self._record("NO_TRADE", candidate.candidate_id, asset_id=candidate.asset_id,
                             reason_codes=("NO_APPROVED_STRATEGY",))
                results.append({"candidate": candidate.candidate_id, "result": "FLAT"})
                continue
            if self.entry_filter is not None and not self.entry_filter(intent.strategy_id, snapshot, now):
                self._record("NO_TRADE", candidate.candidate_id, asset_id=candidate.asset_id,
                             payload={"strategy_id": intent.strategy_id}, reason_codes=("META_FILTER",))
                results.append({"candidate": candidate.candidate_id, "result": "FILTERED"})
                continue
            multiplier = 1.0
            if self.allocation is not None:
                multiplier = float(self.allocation(now).get(intent.strategy_id, 1.0))
                scaled = intent.quantity * multiplier
                policy = self.governor.policy
                cap = policy.max_order_notional / intent.reference_price \
                    if policy is not None and intent.reference_price > 0 else None
                if cap is not None:  # never push an order past the owner's cap, even after rounding
                    scaled = min(scaled, cap)
                scaled = _round_down(scaled, intent.asset_class)
                if cap is not None and scaled > cap:
                    unit = 1.0 if intent.asset_class == AssetClass.EQUITY else 10 ** -QUANTITY_DECIMALS
                    scaled = max(0.0, scaled - unit)
                if scaled <= 0:
                    self._record("NO_TRADE", candidate.candidate_id, asset_id=candidate.asset_id,
                                 payload={"strategy_id": intent.strategy_id, "allocation_multiplier": multiplier},
                                 reason_codes=("ALLOCATION_ZERO",))
                    results.append({"candidate": candidate.candidate_id, "result": "FLAT"})
                    continue
                intent = replace(intent, quantity=scaled)
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
                                  "decided_at": iso(now), "reference_price": intent.reference_price,
                                  "expires_at": iso(intent.expires_at),
                                  "quantity": risk.allowed_quantity, "side": intent.side,
                                  "strategy_id": intent.strategy_id, "strategy_version": intent.strategy_version,
                                  "model_id": intent.model_id, "model_version": intent.model_version,
                                  "entry_bar_end_at": iso(bars[-1].end_at),
                                  "exit_after_bars": intent.exit_after_bars, "spread_bps": spread_bps,
                                  "snapshot_id": snapshot.snapshot_id, "allocation_multiplier": multiplier,
                                  **(sizing or {}),
                                  "ordered_notional": risk.allowed_quantity * intent.reference_price})
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

    def exit_position(self, asset_id: str, asset_class, price: float, *, reason: str,
                      decided_at: datetime | None = None) -> str:
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
                     payload={"client_order_id": client_id, "quantity": qty, "reason": reason, "side": "SELL",
                              "decided_at": iso(decided_at) if decided_at else None,
                              "reference_price": price, "asset_class": getattr(asset_class, "value", asset_class)})
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
                              "side": "SELL", "status": order.status, "filled_quantity": order.filled_quantity,
                              "average_price": order.average_price})
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
                                      "entry_client_order_id": strategy.get("client_order_id"),
                                      "exit_decided_at": iso(decided_at) if decided_at else None,
                                      "model_id": strategy.get("model_id"),
                                      "model_version": strategy.get("model_version"),
                                      "evidence_class": getattr(self.broker, "evidence_class", "PAPER")})
        return order.status

    def monitor_positions(self, bars: list[Bar], context: DecisionContext | None = None,
                          snapshot: FeatureSnapshot | None = None) -> list[dict[str, Any]]:
        """Manage an open position with the exit rules of the strategy that opened it.

        Order of checks: maximum holding time, then (from the first new bar after entry) the strategy's stop-loss
        in ATRs below the entry price, then the strategy's own exit signal. Exits are market sells.
        """
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
            elapsed = sum(b.end_at > parse_utc(entry_end) for b in bars)
            reason = "TIME_EXIT" if elapsed >= limit else None
            strategy = self.registry.implementation(payload.get("strategy_id"), payload.get("strategy_version"))
            if reason is None and strategy is not None and elapsed >= 1:
                if snapshot is None or snapshot.asset_id != asset:
                    snapshot = features_for(bars, max(b.available_at for b in bars))
                fill = self.store.index.latest_order.get(payload["client_order_id"], {}).get("payload", {})
                entry_price = fill.get("average_price")
                atr, close = snapshot.values.get("atr_14"), snapshot.values.get("close")
                if strategy.stop_loss_atr and entry_price and atr and close is not None \
                        and close <= entry_price - strategy.stop_loss_atr * atr:
                    reason = "STOP_LOSS"
                else:
                    reason = strategy.exit_reason(snapshot, OpenPosition(asset, entry_price, elapsed), context)
            if reason:
                status = self.exit_position(asset, bars[-1].asset_class, bars[-1].close, reason=reason,
                                            decided_at=max(b.available_at for b in bars))
                return [{"asset_id": asset, "exit_reason": reason, "status": status}]
            return [{"asset_id": asset, "exit_reason": "HOLD", "bars_remaining": limit - elapsed}]
        self.mode = Mode.SAFE
        self._record("POSITION_UNKNOWN", new_id("position"), asset_id=asset,
                     reason_codes=("MISSING_ENTRY_CONTRACT",))
        return [{"asset_id": asset, "exit_reason": "SAFE"}]

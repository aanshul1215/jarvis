"""Bounded paper decision cycle. Research runs in a separate CLI process."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta

from .broker import BrokerAdapter, BrokerError
from .config import PaperRuntime
from .contracts import AssetClass, LedgerEvent, Mode, new_id, utc_now
from .engine import TradingEngine
from .market_data import AlpacaMarketData
from .review import review_outcomes
from .risk import Governor, RiskPolicy
from .storage import LocalStorage
from .strategies import StrategyRegistry, baseline_specs


class PaperDesk:
    def __init__(self, store: LocalStorage, broker: BrokerAdapter, data: AlpacaMarketData,
                 policy: RiskPolicy, runtime: PaperRuntime):
        if not policy.owner_approved or not policy.paper_enabled:
            raise ValueError("owner paper approval required")
        available = {(spec.strategy_id, spec.version): spec for spec in baseline_specs()}
        approved = []
        for key in runtime.strategy_versions:
            if "@" not in key:
                raise ValueError("strategy version must be strategy-id@version")
            identifier, version = key.rsplit("@", 1)
            if identifier not in policy.approved_strategies or (identifier, version) not in available:
                raise ValueError("strategy version not approved or unavailable")
            approved.append(replace(available[(identifier, version)], approval="PAPER"))
        self.store, self.broker, self.data = store, broker, data
        self.policy, self.runtime = policy, runtime
        self.engine = TradingEngine(store, broker, Governor(policy), StrategyRegistry(approved), Mode.PAPER)

    def _event(self, kind: str, asset: str, status: str, reasons: tuple[str, ...] = (), payload: dict | None = None) -> None:
        self.store.append_event(LedgerEvent(new_id("evt"), kind, utc_now(), new_id("cycle"),
                                            asset_id=asset, status=status, reason_codes=reasons,
                                            payload=payload or {}))

    def run_once(self, *, now: datetime | None = None) -> dict:
        self.engine.reconcile()
        clock = now or utc_now()
        outcomes = {}
        for asset in self.runtime.assets:
            symbol, cls = asset.symbol, asset.asset_class
            if not self.broker.asset_eligible(symbol, cls):
                self._event("ASSET_BLOCK", symbol, "BLOCK", ("BROKER_ASSET_INELIGIBLE",))
                outcomes[symbol] = "BLOCK_ASSET"
                continue
            if cls == AssetClass.EQUITY and not self.broker.equity_market_open():
                self._event("SESSION_SKIP", symbol, "SKIPPED", ("EQUITY_MARKET_CLOSED",))
                outcomes[symbol] = "MARKET_CLOSED"
                continue
            try:
                lookback = timedelta(days=30) if cls == AssetClass.EQUITY else timedelta(hours=72)
                bars, diagnostics = self.data.recent_bars(symbol, cls, start=clock - lookback,
                                                          end=clock, limit=500)
                self._event("DATA_ACCESS", symbol, "RECORDED", payload=diagnostics)
                if len(bars) < 22:
                    self._event("DATA_BLOCK", symbol, "BLOCK", ("INSUFFICIENT_BARS",))
                    outcomes[symbol] = "BLOCK_DATA"
                    continue
                if clock - bars[-1].end_at > timedelta(hours=2):
                    self._event("DATA_BLOCK", symbol, "BLOCK", ("STALE_LAST_BAR",),
                                {"bar_end_at": bars[-1].end_at.isoformat()})
                    outcomes[symbol] = "BLOCK_DATA"
                    continue
                self.store.save_bars(bars)
                quote = self.data.latest_quote(symbol, cls)
                if utc_now() - quote.at > timedelta(seconds=self.policy.max_quote_age_seconds):
                    self._event("QUOTE_BLOCK", symbol, "BLOCK", ("STALE_QUOTE",),
                                {"feed": quote.feed, "quote_at": quote.at.isoformat()})
                    outcomes[symbol] = "BLOCK_QUOTE"
                    continue
                self._event("QUOTE_ACCESS", symbol, "RECORDED",
                            payload={"feed": quote.feed, "quote_at": quote.at.isoformat(),
                                     "observed_at": quote.observed_at.isoformat(),
                                     "access_latency_ms": quote.latency_ms,
                                     "attribution": "API_REQUEST_DURATION_ONLY"})
                current_state = self.broker.state()
                if current_state.open_order_ids:
                    self._event("ORDER_MONITOR", symbol, "BLOCK", ("OPEN_ORDERS_REQUIRE_RECONCILIATION",),
                                {"open_order_count": len(current_state.open_order_ids)})
                    outcomes[symbol] = "OPEN_ORDER_HOLD"
                    continue
                monitor = self.engine.monitor_positions(bars)
                if monitor and monitor[0].get("exit_reason") == "TIME_EXIT":
                    outcomes[symbol] = monitor
                    continue
                quantity = int(asset.order_notional / quote.ask) if cls == AssetClass.EQUITY else round(asset.order_notional / quote.ask, 8)
                if quantity <= 0:
                    self._event("SIZE_BLOCK", symbol, "BLOCK", ("ORDER_NOTIONAL_BELOW_UNIT",))
                    outcomes[symbol] = "BLOCK_SIZE"
                    continue
                outcomes[symbol] = self.engine.process(bars, as_of=utc_now(), reference_price=quote.ask,
                                                       quote_at=quote.at, spread_bps=quote.spread_bps,
                                                       quantity=quantity)
                if self.engine.mode == Mode.SAFE:
                    break
            except Exception as exc:
                self.engine.mode = Mode.SAFE
                self._event("CYCLE_ERROR", symbol, "SAFE", (type(exc).__name__,))
                outcomes[symbol] = "SAFE"
                break
        review_outcomes(self.store)
        return {"mode": self.engine.mode.value, "assets": outcomes}

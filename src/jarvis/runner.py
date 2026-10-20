"""Bounded paper decision cycle. Research runs in a separate CLI process."""

from __future__ import annotations

import math
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Callable

from .broker import BrokerAdapter, BrokerError
from .config import PaperRuntime
from .contracts import AssetClass, LedgerEvent, Mode, iso, new_id, parse_utc, utc_now
from .engine import DUST_NOTIONAL, TradingEngine
from .market_data import AlpacaMarketData
from .review import review_outcomes
from .risk import Governor, RiskPolicy
from .storage import LocalStorage
from .contracts import StrategySpec
from .market import features_for
from .strategies import DecisionContext, StrategyRegistry, baseline_specs
from .timeframes import settings as timeframe_settings
from .regime import REGIME_NAMES, live_label
from .volatility import BASELINE as BASELINE_VOL
from .volatility import HISTORY_BARS, HISTORY_DAYS, bar_returns, forecast_now, scaled_notional


# Fallback lifetime for an entry order whose intent predates the recorded expiry field.
ENTRY_ORDER_MAX_AGE = timedelta(minutes=30)


class PaperDesk:
    def __init__(self, store: LocalStorage, broker: BrokerAdapter, data: AlpacaMarketData,
                 policy: RiskPolicy, runtime: PaperRuntime, *, clock: Callable[[], datetime] = utc_now,
                 specs: list[StrategySpec] | None = None, seed: int = 0, persist_market_data: bool = True,
                 earnings: Callable[[str, datetime], list[dict]] | None = None, situation=None, information=None):
        """``specs`` and ``persist_market_data=False`` exist for the evaluation harness; the paper CLI uses the
        defaults (baseline strategies only, bars saved every cycle)."""
        if not policy.owner_approved or not policy.paper_enabled:
            raise ValueError("owner paper approval required")
        available = {(spec.strategy_id, spec.version): spec for spec in (specs if specs is not None else baseline_specs())}
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
        self.clock = clock  # injectable so replays and soak tests can run on simulated time
        self.persist_market_data = persist_market_data
        self.earnings = earnings  # earnings releases known at a time, for event strategies
        self.situation = situation  # awareness.SituationBuilder: recorded each cycle when given
        self.information = information  # sentiment.SentimentIndex for information strategies
        self._vol_cache: dict = {}  # fitted volatility-model parameters, refitted at month starts
        self._regime_cache: dict = {}  # fitted hidden-Markov parameters, the same way
        self._reviewed_outcomes = -1  # outcome count at the last review report
        self.engine = TradingEngine(store, broker, Governor(policy), StrategyRegistry(approved, seed=seed), Mode.PAPER)

    def _event(self, kind: str, asset: str, status: str, reasons: tuple[str, ...] = (), payload: dict | None = None) -> None:
        self.store.append_event(LedgerEvent(new_id("evt"), kind, utc_now(), new_id("cycle"),
                                            asset_id=asset, status=status, reason_codes=reasons,
                                            payload=payload or {}))

    def _resolve_open_orders(self, clock: datetime) -> set[str]:
        """Cancel entry orders that outlived their candidate; return the assets that still have a working order.

        Only an asset with a working order waits. Previously any open order held every asset, including exits of
        other positions, and nothing ever cancelled it.
        """
        open_ids = self.broker.state().open_order_ids
        if not open_ids:
            return set()
        intents = self.store.index.intents
        held: set[str] = set()
        for client_id in open_ids:
            intent = intents.get(client_id)
            if intent is None:
                raise BrokerError("open broker order without a recorded intent")
            asset = intent.get("asset_id")
            held.add(asset)  # wait for the broker to confirm the cancel or fill at the next reconcile
            if intent["event_type"] != "ORDER_INTENT":
                continue  # exit orders are never cancelled here
            expires = intent["payload"].get("expires_at")
            deadline = parse_utc(expires) if expires else parse_utc(intent["at"]) + ENTRY_ORDER_MAX_AGE
            if clock > deadline:
                self.broker.cancel(client_id)
                self._event("ORDER_CANCEL", asset, "CANCEL_REQUESTED", ("ENTRY_ORDER_EXPIRED",),
                            {"client_order_id": client_id, "deadline": iso(deadline)})
        return held

    def _asset_state(self, bars) -> dict:
        """Per-asset awareness: trend/volatility regime and (daily bars) the volatility forecast used for sizing."""
        if self.runtime.timeframe != "1Day":
            return {}
        r, dates, closes = bar_returns(bars)
        label = live_label(self.runtime.regime_model, r, dates, closes, cache=self._regime_cache)
        model = self.runtime.volatility_model
        variance = forecast_now(model, r, dates, cache=self._vol_cache)
        if variance is None and model != BASELINE_VOL:
            # A fitted model needs 1,000 returns before the current month; until then the registered baseline sizes
            # the order, and the order records which model did (MODEL_REGISTER.md, "Use").
            model, variance = BASELINE_VOL, forecast_now(BASELINE_VOL, r, dates)
        return {"regime": REGIME_NAMES.get(label) if label is not None else None, "volatility_model_used": model,
                "forecast_daily_vol": variance ** 0.5 if variance is not None and variance > 0 else None}

    def run_once(self, *, now: datetime | None = None) -> dict:
        self.engine.reconcile()
        clock = now or self.clock()
        outcomes = {}
        try:
            held = self._resolve_open_orders(clock)
        except Exception as exc:
            self.engine.mode = Mode.SAFE
            self._event("CYCLE_ERROR", "PORTFOLIO", "SAFE", (type(exc).__name__,))
            return {"mode": self.engine.mode.value, "assets": outcomes}
        ready = []  # pass 1: data for every asset that can be considered this cycle
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
                frame = timeframe_settings(self.runtime.timeframe, cls)
                lookback, limit = frame.lookback, 500
                if self.runtime.sizing == "volatility":  # fitted forecasters need about four years of daily bars
                    lookback, limit = max(lookback, timedelta(days=HISTORY_DAYS[cls])), HISTORY_BARS
                bars, diagnostics = self.data.recent_bars(symbol, cls, start=clock - lookback,
                                                          end=clock, limit=limit, timeframe=self.runtime.timeframe)
                self._event("DATA_ACCESS", symbol, "RECORDED", payload=diagnostics)
                if len(bars) < 22:
                    self._event("DATA_BLOCK", symbol, "BLOCK", ("INSUFFICIENT_BARS",))
                    outcomes[symbol] = "BLOCK_DATA"
                    continue
                if clock - bars[-1].end_at > frame.max_bar_age:
                    self._event("DATA_BLOCK", symbol, "BLOCK", ("STALE_LAST_BAR",),
                                {"bar_end_at": bars[-1].end_at.isoformat()})
                    outcomes[symbol] = "BLOCK_DATA"
                    continue
                if self.persist_market_data:
                    self.store.save_bars(bars)
                ready.append((asset, bars, frame))
            except Exception as exc:
                self.engine.mode = Mode.SAFE
                self._event("CYCLE_ERROR", symbol, "SAFE", (type(exc).__name__,))
                outcomes[symbol] = "SAFE"
                break
        if self.engine.mode != Mode.SAFE:
            # Pass 2: one consistent, point-in-time view of every asset, so cross-asset strategies (relative
            # strength) rank against the same moment, then exits and entries per asset.
            decided_at = self.clock()
            try:
                snapshots = {a.symbol: features_for(b, decided_at, horizon=f.feature_horizon) for a, b, f in ready}
                states = {a.symbol: self._asset_state(b) for a, b, _ in ready}
                situation = None
                if self.situation is not None:
                    state = self.engine._risk_state()
                    values = state.position_values or {}
                    situation = self.situation.build(decided_at, snapshots, assets=states, desk={
                        "drawdown": state.drawdown, "equity": state.equity,
                        "open_positions": sum(1 for v in values.values() if abs(v) >= DUST_NOTIONAL),
                        "gross_exposure": sum(abs(v) for v in values.values()) / state.equity if state.equity > 0 else None})
                    self._event("SITUATION", "*", "RECORDED", payload=situation)
                context = DecisionContext(decided_at, snapshots, self.earnings, situation, self.information)
            except Exception as exc:  # same rule as everywhere in the cycle: an unexpected error stops trading
                self.engine.mode = Mode.SAFE
                self._event("CYCLE_ERROR", "*", "SAFE", (type(exc).__name__,))
                ready = []
            for asset, bars, frame in ready:
                symbol, cls = asset.symbol, asset.asset_class
                try:
                    quote = self.data.latest_quote(symbol, cls)
                    # Decision time is read when the decision is made, after the quote was fetched; the cycle
                    # start (``clock``) is earlier and would make a fresh quote look like it came from the future.
                    if self.clock() - quote.at > timedelta(seconds=self.policy.max_quote_age_seconds):
                        self._event("QUOTE_BLOCK", symbol, "BLOCK", ("STALE_QUOTE",),
                                    {"feed": quote.feed, "quote_at": quote.at.isoformat()})
                        outcomes[symbol] = "BLOCK_QUOTE"
                        continue
                    self._event("QUOTE_ACCESS", symbol, "RECORDED",
                                payload={"feed": quote.feed, "quote_at": quote.at.isoformat(),
                                         "observed_at": quote.observed_at.isoformat(),
                                         "access_latency_ms": quote.latency_ms,
                                         "attribution": "API_REQUEST_DURATION_ONLY"})
                    if symbol in held:
                        self._event("ORDER_MONITOR", symbol, "BLOCK", ("OPEN_ORDER_FOR_ASSET",))
                        outcomes[symbol] = "OPEN_ORDER_HOLD"
                        continue
                    snapshot = context.snapshots.get(symbol)
                    monitor = self.engine.monitor_positions(bars, context, snapshot)
                    if monitor:
                        # One position per asset, owned by the strategy that opened it: an exit was just placed,
                        # or the position is held and no other strategy may add to it.
                        outcomes[symbol] = monitor if monitor[0].get("exit_reason") != "HOLD" else "IN_POSITION"
                        if self.engine.mode == Mode.SAFE:
                            break
                        continue
                    notional = asset.order_notional
                    vol = states[symbol].get("forecast_daily_vol")
                    sizing = {"sizing": self.runtime.sizing, "base_notional": asset.order_notional,
                              "volatility_model": self.runtime.volatility_model, "forecast_daily_vol": vol,
                              "volatility_model_used": states[symbol].get("volatility_model_used"),
                              "decision_mid": (quote.bid + quote.ask) / 2}
                    if self.runtime.sizing == "volatility":
                        notional = scaled_notional(asset.order_notional, vol)
                        if notional is None:
                            self._event("SIZE_BLOCK", symbol, "BLOCK", ("NO_VOLATILITY_FORECAST",))
                            outcomes[symbol] = "BLOCK_SIZE"
                            continue
                        # A calm asset may be scaled up to 1.5x its base, but never past the owner's per-order cap.
                        notional = min(notional, self.policy.max_order_notional)
                    sizing["notional"] = notional
                    # Round down so the order value never exceeds the chosen notional.
                    quantity = int(notional / quote.ask) if cls == AssetClass.EQUITY \
                        else math.floor(notional / quote.ask * 1e8) / 1e8
                    if quantity <= 0:
                        self._event("SIZE_BLOCK", symbol, "BLOCK", ("ORDER_NOTIONAL_BELOW_UNIT",))
                        outcomes[symbol] = "BLOCK_SIZE"
                        continue
                    outcomes[symbol] = self.engine.process(bars, as_of=self.clock(), reference_price=quote.ask,
                                                           quote_at=quote.at, spread_bps=quote.spread_bps,
                                                           quantity=quantity, feature_horizon=frame.feature_horizon,
                                                           persist_features=self.persist_market_data, context=context,
                                                           snapshot=snapshot, sizing=sizing)
                    if self.engine.mode == Mode.SAFE:
                        break
                except Exception as exc:
                    self.engine.mode = Mode.SAFE
                    self._event("CYCLE_ERROR", symbol, "SAFE", (type(exc).__name__,))
                    outcomes[symbol] = "SAFE"
                    break
        # The review report re-reads the whole journal, so rebuild it only when a new outcome exists, and never in
        # replays (persist_market_data=False), where the harness computes its own statistics.
        outcome_count = len(self.store.index.outcome_ids)
        if self.persist_market_data and outcome_count != self._reviewed_outcomes:
            review_outcomes(self.store)
            self._reviewed_outcomes = outcome_count
        return {"mode": self.engine.mode.value, "assets": outcomes}

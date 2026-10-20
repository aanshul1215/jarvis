"""Deterministic, default-deny portfolio Governor."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .contracts import AssetClass, Mode, RiskDecision, StrategyIntent, new_id, require_utc

# The exchange's quote timestamps and this computer's clock are never exactly in step: the first paper-account probe
# (2026-10-20) saw a BTC/USD quote stamped 80 ms after the local time it was received. A quote this little ahead is
# accepted; anything further ahead still blocks, because it would mean a clock or data fault.
CLOCK_SKEW = timedelta(seconds=2)


@dataclass(frozen=True)
class RiskPolicy:
    version: str
    approved_assets: tuple[str, ...]
    approved_strategies: tuple[str, ...]
    max_order_notional: float
    max_asset_notional: float
    max_portfolio_notional: float
    max_daily_loss: float
    max_drawdown: float
    max_spread_bps: float
    max_quote_age_seconds: float
    paper_enabled: bool = False
    crypto_enabled: bool = False
    owner_approved: bool = False
    # Capital the owner assigns to JARVIS when the broker account holds more (the Alpaca paper account starts at
    # $100,000). The drawdown limit is then measured on this amount plus JARVIS's own gains and losses since it
    # started, not on the whole account. None = the whole account.
    allocated_capital: float | None = None

    def __post_init__(self) -> None:
        numeric = (self.max_order_notional, self.max_asset_notional, self.max_portfolio_notional,
                   self.max_daily_loss, self.max_drawdown, self.max_spread_bps, self.max_quote_age_seconds)
        if any(v <= 0 for v in numeric):
            raise ValueError("risk limits must be positive")


@dataclass(frozen=True)
class BrokerState:
    cash: float
    buying_power: float
    equity: float
    positions: dict[str, float]
    position_values: dict[str, float] | None = None
    open_order_ids: tuple[str, ...] = ()
    reconciled: bool = False
    daily_pnl: float = 0.0
    drawdown: float = 0.0


class Governor:
    def __init__(self, policy: RiskPolicy | None, *, killed: bool = False):
        self.policy = policy
        self.killed = killed

    def assess(self, intent: StrategyIntent, state: BrokerState, mode: Mode, now: datetime,
               quote_at: datetime, spread_bps: float, client_order_id: str,
               existing_ids: set[str], *, mock: bool = False) -> RiskDecision:
        require_utc(now)
        reasons: list[str] = []
        p = self.policy
        if self.killed or mode in (Mode.HALT, Mode.SAFE):
            reasons.append("KILL_OR_SAFE")
        if not state.reconciled:
            reasons.append("BROKER_UNRECONCILED")
        if p is None or not p.owner_approved:
            reasons.append("OWNER_POLICY_MISSING")
        if mode != Mode.PAPER and not (mock and mode == Mode.SHADOW):
            reasons.append("MODE_NOT_EXECUTABLE")
        if mode == Mode.PAPER and (p is None or not p.paper_enabled):
            reasons.append("PAPER_NOT_ENABLED")
        if now > intent.expires_at:
            reasons.append("CANDIDATE_EXPIRED")
        if intent.quantity <= 0 or intent.reference_price <= 0:
            reasons.append("INVALID_SIZE_OR_PRICE")
        if client_order_id in existing_ids or client_order_id in state.open_order_ids:
            reasons.append("DUPLICATE_ORDER")
        if p is not None:
            if intent.asset_id not in p.approved_assets:
                reasons.append("ASSET_NOT_APPROVED")
            if intent.strategy_id not in p.approved_strategies:
                reasons.append("STRATEGY_NOT_APPROVED")
            if intent.asset_class == AssetClass.CRYPTO and not p.crypto_enabled:
                reasons.append("CRYPTO_NOT_APPROVED")
            if now - require_utc(quote_at) > timedelta(seconds=p.max_quote_age_seconds) or quote_at > now + CLOCK_SKEW:
                reasons.append("STALE_OR_FUTURE_QUOTE")
            if spread_bps > p.max_spread_bps or spread_bps < 0:
                reasons.append("SPREAD_LIMIT")
            notional = intent.quantity * intent.reference_price
            if notional > p.max_order_notional:
                reasons.append("ORDER_LIMIT")
            if notional + state.positions.get(intent.asset_id, 0) * intent.reference_price > p.max_asset_notional:
                reasons.append("ASSET_EXPOSURE_LIMIT")
            if state.position_values is None and state.positions:
                reasons.append("POSITION_VALUES_UNVERIFIED")
            portfolio_value = sum(abs(v) for v in (state.position_values or {}).values())
            if notional + portfolio_value > p.max_portfolio_notional:
                reasons.append("PORTFOLIO_LIMIT")
            if notional > state.buying_power or notional > state.cash:
                reasons.append("BUYING_POWER")
            if state.daily_pnl <= -p.max_daily_loss or state.drawdown >= p.max_drawdown:
                reasons.append("LOSS_LIMIT")
        return RiskDecision(new_id("risk"), intent.intent_id, now, "BLOCK" if reasons else "ALLOW",
                            tuple(reasons), p.version if p else "NONE", 0 if reasons else intent.quantity)

"""Typed records shared across desks. Times are timezone-aware UTC."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must have UTC timezone")
    return value.astimezone(timezone.utc)


def iso(value: datetime) -> str:
    return require_utc(value).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    return require_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class AssetClass(str, Enum):
    EQUITY = "EQUITY"
    CRYPTO = "CRYPTO"


class Mode(str, Enum):
    OFF = "OFF"
    OBSERVE = "OBSERVE"
    SHADOW = "SHADOW"
    PAPER = "PAPER"
    SAFE = "SAFE"
    HALT = "HALT"


@dataclass(frozen=True)
class Bar:
    asset_id: str
    asset_class: AssetClass
    start_at: datetime
    end_at: datetime
    available_at: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source_id: str
    feed: str
    venue: str = ""
    revision: int = 1

    def __post_init__(self) -> None:
        for t in (self.start_at, self.end_at, self.available_at):
            require_utc(t)
        if not self.start_at < self.end_at <= self.available_at:
            raise ValueError("invalid bar time ordering")
        if min(self.open, self.high, self.low, self.close) <= 0 or self.volume < 0:
            raise ValueError("invalid price or volume")
        if not self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high:
            raise ValueError("inconsistent OHLC")


@dataclass(frozen=True)
class FeatureSnapshot:
    snapshot_id: str
    asset_id: str
    asset_class: AssetClass
    as_of: datetime
    available_at: datetime
    expires_at: datetime
    source_ids: tuple[str, ...]
    values: dict[str, float | None]
    feature_version: str = "features-v1"
    quality: str = "VALID"

    def __post_init__(self) -> None:
        for t in (self.as_of, self.available_at, self.expires_at):
            require_utc(t)
        if self.available_at > self.expires_at:
            raise ValueError("feature expiry before availability")


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    asset_id: str
    asset_class: AssetClass
    detected_at: datetime
    expires_at: datetime
    snapshot_id: str
    trigger: str
    score: float
    status: str = "DETECTED"


@dataclass(frozen=True)
class StrategySpec:
    strategy_id: str
    version: str
    asset_classes: tuple[AssetClass, ...]
    required_features: tuple[str, ...]
    entry_trigger: str
    exit_after_bars: int
    max_cost_bps: float
    approval: str = "RESEARCH"
    model_id: str = "baseline"
    model_version: str = "v1"

    def __post_init__(self) -> None:
        if self.exit_after_bars < 1 or self.max_cost_bps < 0:
            raise ValueError("invalid strategy exit/cost")


@dataclass(frozen=True)
class StrategyIntent:
    intent_id: str
    candidate_id: str
    asset_id: str
    asset_class: AssetClass
    strategy_id: str
    strategy_version: str
    model_id: str
    model_version: str
    created_at: datetime
    expires_at: datetime
    side: str
    quantity: float
    reference_price: float
    exit_after_bars: int
    evidence_snapshot_id: str


@dataclass(frozen=True)
class RiskDecision:
    decision_id: str
    intent_id: str
    at: datetime
    result: str
    reason_codes: tuple[str, ...]
    policy_version: str
    allowed_quantity: float = 0.0


@dataclass(frozen=True)
class BrokerOrder:
    client_order_id: str
    broker_order_id: str
    asset_id: str
    side: str
    quantity: float
    filled_quantity: float
    average_price: float | None
    status: str
    submitted_at: datetime


@dataclass(frozen=True)
class LedgerEvent:
    event_id: str
    event_type: str
    at: datetime
    correlation_id: str
    asset_id: str | None = None
    asset_class: AssetClass | None = None
    strategy_id: str | None = None
    strategy_version: str | None = None
    model_id: str | None = None
    model_version: str | None = None
    opportunity_id: str | None = None
    trade_id: str | None = None
    source_id: str | None = None
    source_event_at: datetime | None = None
    first_available_at: datetime | None = None
    processing_latency_ms: float | None = None
    status: str = "RECORDED"
    reason_codes: tuple[str, ...] = ()
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("at", "source_event_at", "first_available_at"):
            if data[key] is not None:
                data[key] = iso(data[key])
        if self.asset_class is not None:
            data["asset_class"] = self.asset_class.value
        return data

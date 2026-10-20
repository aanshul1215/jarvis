"""Strict local owner policy loading. Configuration is never inferred from a model."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .contracts import AssetClass
from .risk import RiskPolicy


POLICY_FIELDS = {"version", "approved_assets", "approved_strategies", "max_order_notional",
                 "max_asset_notional", "max_portfolio_notional", "max_daily_loss", "max_drawdown",
                 "max_spread_bps", "max_quote_age_seconds", "paper_enabled", "crypto_enabled", "owner_approved"}
OPTIONAL_POLICY_FIELDS = {"allocated_capital"}


def load_policy(home: Path) -> RiskPolicy:
    path = home / "config" / "owner-policy.json"
    data = json.loads(path.read_text())
    unknown = set(data) - POLICY_FIELDS - OPTIONAL_POLICY_FIELDS
    missing = POLICY_FIELDS - set(data)
    if unknown or missing:
        raise ValueError(f"owner policy keys invalid: missing={sorted(missing)}, unknown={sorted(unknown)}")
    if type(data["paper_enabled"]) is not bool or type(data["owner_approved"]) is not bool or type(data["crypto_enabled"]) is not bool:
        raise ValueError("policy approvals must be booleans")
    if not data["owner_approved"] or not data["paper_enabled"]:
        raise ValueError("owner paper approval is not enabled")
    if not all(isinstance(x, str) and x for x in data["approved_assets"] + data["approved_strategies"]):
        raise ValueError("policy allowlists must be nonempty strings")
    if not data["approved_assets"] or not data["approved_strategies"]:
        raise ValueError("policy allowlists are empty")
    for key in ("max_order_notional", "max_asset_notional", "max_portfolio_notional", "max_daily_loss",
                "max_drawdown", "max_spread_bps", "max_quote_age_seconds"):
        if type(data[key]) not in (int, float) or not 0 < data[key] < float("inf"):
            raise ValueError(f"invalid risk limit: {key}")
    if "allocated_capital" in data and (type(data["allocated_capital"]) not in (int, float)
                                        or not 0 < data["allocated_capital"] < float("inf")):
        raise ValueError("invalid allocated_capital")
    return RiskPolicy(**{**data, "approved_assets": tuple(data["approved_assets"]),
                         "approved_strategies": tuple(data["approved_strategies"])})


@dataclass(frozen=True)
class PaperAsset:
    symbol: str
    asset_class: AssetClass
    order_notional: float


@dataclass(frozen=True)
class PaperRuntime:
    assets: tuple[PaperAsset, ...]
    strategy_versions: tuple[str, ...]
    poll_seconds: int
    timeframe: str = "1Hour"  # bar size the strategies decide on: "1Hour" or "1Day"
    sizing: str = "fixed"     # "fixed": order_notional; "volatility": scaled by the forecast (daily bars only)
    volatility_model: str = "rolling20"  # the Phase 5 study's winner (docs/07-awareness/MODEL_REGISTER.md)
    regime_model: str = "trend_vol"      # regime label recorded for awareness: none, sma200, trend_vol or hmm2

    def __post_init__(self) -> None:
        from .volatility import MODELS

        if self.sizing not in ("fixed", "volatility"):
            raise ValueError("sizing must be fixed or volatility")
        if self.sizing == "volatility" and self.timeframe != "1Day":
            raise ValueError("volatility sizing is validated on daily bars only")
        if self.volatility_model not in MODELS:
            raise ValueError(f"unknown volatility model {self.volatility_model}")
        if self.regime_model not in ("none", "sma200", "trend_vol", "hmm2"):
            raise ValueError(f"unknown regime model {self.regime_model}")


def load_paper_runtime(home: Path, policy: RiskPolicy) -> PaperRuntime:
    data = json.loads((home / "config" / "paper-runtime.json").read_text())
    if not {"assets", "strategy_versions", "poll_seconds"} <= set(data) <= {"assets", "strategy_versions",
                                                                            "poll_seconds", "timeframe", "sizing",
                                                                            "volatility_model", "regime_model"}:
        raise ValueError("invalid paper runtime keys")
    if data.get("timeframe", "1Hour") not in ("1Hour", "1Day"):
        raise ValueError("timeframe must be 1Hour or 1Day")
    if type(data["poll_seconds"]) is not int or data["poll_seconds"] < 60:
        raise ValueError("paper polling must be at least 60 seconds")
    versions = data["strategy_versions"]
    if not isinstance(versions, list) or not versions or any(not isinstance(v, str) or not v for v in versions):
        raise ValueError("approved paper strategy versions required")
    assets = []
    for item in data["assets"]:
        if set(item) != {"symbol", "asset_class", "order_notional"}:
            raise ValueError("invalid paper asset keys")
        asset = PaperAsset(item["symbol"], AssetClass(item["asset_class"]), item["order_notional"])
        if not asset.symbol or asset.symbol not in policy.approved_assets:
            raise ValueError("asset not in owner policy")
        if type(asset.order_notional) not in (int, float) or not 0 < asset.order_notional <= policy.max_order_notional:
            raise ValueError("order notional invalid or above owner limit")
        if asset.asset_class == AssetClass.CRYPTO and not policy.crypto_enabled:
            raise ValueError("crypto not enabled by owner")
        assets.append(asset)
    if not assets or len({a.symbol for a in assets}) != len(assets):
        raise ValueError("paper assets missing or duplicated")
    return PaperRuntime(tuple(assets), tuple(versions), data["poll_seconds"], data.get("timeframe", "1Hour"),
                        data.get("sizing", "fixed"), data.get("volatility_model", "rolling20"),
                        data.get("regime_model", "trend_vol"))

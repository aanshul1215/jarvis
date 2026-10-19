"""Versioned strategy selection. Only explicitly eligible versions can create intents."""

from __future__ import annotations

from datetime import datetime

from .contracts import AssetClass, Candidate, FeatureSnapshot, Mode, StrategyIntent, StrategySpec
from .market import stable_id


def baseline_specs() -> list[StrategySpec]:
    return [
        StrategySpec("breakout-volume", "1.0.0", (AssetClass.EQUITY, AssetClass.CRYPTO),
                     ("breakout_20", "relative_volume"), "BREAKOUT_VOLUME", 3, 20, approval="MOCK"),
    ]


class StrategyRegistry:
    def __init__(self, specs: list[StrategySpec]):
        self.specs = {(s.strategy_id, s.version): s for s in specs}

    def eligible(self, mode: Mode, asset_class) -> list[StrategySpec]:
        allowed = {Mode.OFF: set(), Mode.OBSERVE: set(), Mode.SHADOW: {"MOCK", "SHADOW", "PAPER"},
                   Mode.PAPER: {"PAPER"}, Mode.SAFE: set(), Mode.HALT: set()}[mode]
        return [s for s in self.specs.values() if s.approval in allowed and asset_class in s.asset_classes]


def select_intent(candidate: Candidate, snapshot: FeatureSnapshot, registry: StrategyRegistry,
                  mode: Mode, now: datetime, *, quantity: float = 1.0, reference_price: float) -> StrategyIntent | None:
    if now > candidate.expires_at or now > snapshot.expires_at or candidate.snapshot_id != snapshot.snapshot_id:
        return None
    for spec in registry.eligible(mode, candidate.asset_class):
        if spec.entry_trigger != candidate.trigger or any(snapshot.values.get(k) is None for k in spec.required_features):
            continue
        return StrategyIntent(stable_id("intent", candidate.candidate_id, spec.strategy_id, spec.version), candidate.candidate_id, candidate.asset_id, candidate.asset_class,
                              spec.strategy_id, spec.version, spec.model_id, spec.model_version, now,
                              candidate.expires_at, "BUY", quantity, reference_price, spec.exit_after_bars,
                              snapshot.snapshot_id)
    return None

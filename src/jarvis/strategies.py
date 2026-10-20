"""Versioned strategies and selection. Only explicitly eligible versions can create intents.

A strategy is a plug-in that turns a point-in-time FeatureSnapshot into an entry score (or nothing). It never sees
future data, never sizes the order and never bypasses the Governor; the engine, risk gate and broker code are the
same in backtests, paper trading and (later) live trading.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from .contracts import AssetClass, Candidate, FeatureSnapshot, Mode, StrategyIntent, StrategySpec
from .market import stable_id


class Strategy(ABC):
    def __init__(self, spec: StrategySpec):
        self.spec = spec

    @abstractmethod
    def entry_score(self, snapshot: FeatureSnapshot) -> float | None:
        """A positive score when the strategy wants to enter, else None. Must be deterministic."""


class BreakoutVolume(Strategy):
    """Close above the prior 20-bar high on at least 1.5x normal volume (the original baseline)."""

    def entry_score(self, snapshot: FeatureSnapshot) -> float | None:
        breakout, volume = snapshot.values.get("breakout_20"), snapshot.values.get("relative_volume")
        if breakout is None or volume is None or not (breakout > 0 and volume >= 1.5):
            return None
        return float(breakout * volume)


class RandomEntry(Strategy):
    """Research control: enters on a seeded coin flip. Any evaluation gate must reject it.

    The decision is a hash of (seed, asset, bar time), so a replay is reproducible and the "randomness" cannot see
    the future.
    """

    probability = 0.05

    def __init__(self, spec: StrategySpec, seed: int = 0):
        super().__init__(spec)
        self.seed = seed

    def entry_score(self, snapshot: FeatureSnapshot) -> float | None:
        digest = hashlib.sha256(f"{self.seed}|{snapshot.asset_id}|{snapshot.as_of.isoformat()}".encode()).digest()
        draw = int.from_bytes(digest[:8], "big") / 2 ** 64
        return 1.0 if draw < self.probability else None


IMPLEMENTATIONS: dict[str, type[Strategy]] = {"breakout-volume": BreakoutVolume, "random-entry": RandomEntry}


def baseline_specs() -> list[StrategySpec]:
    return [
        StrategySpec("breakout-volume", "1.0.0", (AssetClass.EQUITY, AssetClass.CRYPTO),
                     ("breakout_20", "relative_volume"), "BREAKOUT_VOLUME", 3, 20, approval="MOCK"),
    ]


def research_specs() -> list[StrategySpec]:
    """Controls used only by the evaluation harness; never approved for paper or live."""
    return [StrategySpec("random-entry", "1.0.0", (AssetClass.EQUITY, AssetClass.CRYPTO), (), "RANDOM_ENTRY", 3, 20,
                         approval="RESEARCH")]


class StrategyRegistry:
    def __init__(self, specs: list[StrategySpec], *, seed: int = 0):
        self.specs = {(s.strategy_id, s.version): s for s in specs}
        self.impls: dict[tuple[str, str], Strategy] = {}
        for key, spec in self.specs.items():
            cls = IMPLEMENTATIONS.get(spec.strategy_id)
            if cls is None:
                raise ValueError(f"no implementation for strategy {spec.strategy_id}")
            self.impls[key] = cls(spec, seed) if cls is RandomEntry else cls(spec)

    def eligible(self, mode: Mode, asset_class) -> list[StrategySpec]:
        allowed = {Mode.OFF: set(), Mode.OBSERVE: set(), Mode.SHADOW: {"MOCK", "SHADOW", "PAPER"},
                   Mode.PAPER: {"PAPER"}, Mode.SAFE: set(), Mode.HALT: set()}[mode]
        return [s for s in self.specs.values() if s.approval in allowed and asset_class in s.asset_classes]

    def candidates(self, snapshot: FeatureSnapshot, now: datetime, mode: Mode) -> list[Candidate]:
        """Entry candidates from every eligible strategy, using only the snapshot (point-in-time features)."""
        if snapshot.quality != "VALID" or now < snapshot.available_at or now > snapshot.expires_at:
            return []
        found = []
        for spec in self.eligible(mode, snapshot.asset_class):
            if any(snapshot.values.get(k) is None for k in spec.required_features):
                continue
            score = self.impls[(spec.strategy_id, spec.version)].entry_score(snapshot)
            if score is not None:
                found.append(Candidate(stable_id("cand", snapshot.snapshot_id, spec.entry_trigger), snapshot.asset_id,
                                       snapshot.asset_class, now, min(snapshot.expires_at, now + timedelta(minutes=30)),
                                       snapshot.snapshot_id, spec.entry_trigger, score))
        return found


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

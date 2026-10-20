"""Versioned strategies and selection. Only explicitly eligible versions can create intents.

A strategy is a plug-in that turns point-in-time features into an entry score and, once in a position, an exit
reason. It never sees future data, never sizes the order and never bypasses the Governor; the engine, risk gate and
broker code are the same in backtests, paper trading and (later) live trading. All strategies are long-only and use
fixed parameters chosen before testing (see docs/06-strategies/STRATEGY_REGISTER.md), so the experiment registry's
trial count stays honest. Parameters are part of the version: changing one means a new version and a new trial.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable

from .contracts import AssetClass, Candidate, FeatureSnapshot, Mode, StrategyIntent, StrategySpec, parse_utc
from .market import stable_id


@dataclass(frozen=True)
class DecisionContext:
    """What a strategy may know besides its own asset's features, all as of ``now``."""

    now: datetime
    snapshots: dict[str, FeatureSnapshot] = field(default_factory=dict)  # every asset processed this cycle
    earnings: Callable[[str, datetime], list[dict]] | None = None        # releases known at a time

    def rank(self, asset_id: str, feature: str) -> tuple[int, int] | None:
        """(rank, count) of ``asset_id`` by ``feature`` among same-class assets, 1 = highest."""
        own = self.snapshots.get(asset_id)
        if own is None or own.values.get(feature) is None:
            return None
        peers = [s.values[feature] for s in self.snapshots.values()
                 if s.asset_class == own.asset_class and s.values.get(feature) is not None]
        return 1 + sum(v > own.values[feature] for v in peers), len(peers)


@dataclass(frozen=True)
class OpenPosition:
    asset_id: str
    entry_price: float | None
    bars_held: int


class Strategy(ABC):
    stop_loss_atr: float | None = None  # exit if the close falls this many ATRs below the entry price

    def __init__(self, spec: StrategySpec):
        self.spec = spec

    @abstractmethod
    def entry_score(self, snapshot: FeatureSnapshot, context: DecisionContext | None = None) -> float | None:
        """A positive score when the strategy wants to enter, else None. Must be deterministic."""

    def exit_reason(self, snapshot: FeatureSnapshot, position: OpenPosition,
                    context: DecisionContext | None = None) -> str | None:
        """A reason to leave before the time limit, or None to keep holding."""
        return None


class BreakoutVolume(Strategy):
    """Close above the prior 20-bar high on at least 1.5x normal volume; hold 3 bars (the original baseline)."""

    def entry_score(self, snapshot, context=None):
        breakout, volume = snapshot.values.get("breakout_20"), snapshot.values.get("relative_volume")
        if breakout is None or volume is None or not (breakout > 0 and volume >= 1.5):
            return None
        return float(breakout * volume)


class TrendSma200(Strategy):
    """Time-series trend: hold while the close is above its 200-bar average and the 6-month return is positive."""

    def entry_score(self, snapshot, context=None):
        v = snapshot.values
        if v.get("dist_sma_200") is None or v.get("ret_126") is None:
            return None
        return float(v["dist_sma_200"]) if v["dist_sma_200"] > 0 and v["ret_126"] > 0 else None

    def exit_reason(self, snapshot, position, context=None):
        distance = snapshot.values.get("dist_sma_200")
        return "TREND_BROKEN" if distance is not None and distance < 0 else None


class MeanReversionRsi2(Strategy):
    """Buy a sharp 2-bar pullback (RSI(2) below 10) only inside a long-term uptrend; exit on the bounce."""

    stop_loss_atr = 2.0

    def entry_score(self, snapshot, context=None):
        v = snapshot.values
        if v.get("rsi_2") is None or v.get("dist_sma_200") is None:
            return None
        return float(10 - v["rsi_2"]) if v["rsi_2"] < 10 and v["dist_sma_200"] > 0 else None

    def exit_reason(self, snapshot, position, context=None):
        v = snapshot.values
        if v.get("close") is not None and v.get("sma_5") is not None and v["close"] > v["sma_5"]:
            return "REVERTED"
        return None


class VolatilityBreakout(Strategy):
    """After volatility contracts (20-bar volatility under 75% of its 1-year level), buy a close above the prior
    20-bar high; exit on a close below the prior 20-bar low."""

    stop_loss_atr = 2.0

    def entry_score(self, snapshot, context=None):
        v = snapshot.values
        ratio, breakout = v.get("volatility_ratio_20_252"), v.get("breakout_20")
        if ratio is None or breakout is None or not (ratio < 0.75 and breakout > 0):
            return None
        return float(breakout / ratio)

    def exit_reason(self, snapshot, position, context=None):
        breakdown = snapshot.values.get("breakdown_20")
        return "BROKE_DOWN" if breakdown is not None and breakdown < 0 else None


class RelativeStrength(Strategy):
    """Cross-sectional momentum: hold the 3 strongest assets by 12-1 month return if that return is positive;
    sell when an asset drops out of the top 5 (a buffer that avoids churning) or its return turns negative."""

    top, keep = 3, 5

    def entry_score(self, snapshot, context=None):
        momentum = snapshot.values.get("mom_12_1")
        place = context.rank(snapshot.asset_id, "mom_12_1") if context else None
        if momentum is None or place is None or place[1] < 2 * self.top:
            return None  # ranking needs a real cross-section
        return float(momentum) if place[0] <= self.top and momentum > 0 else None

    def exit_reason(self, snapshot, position, context=None):
        momentum = snapshot.values.get("mom_12_1")
        place = context.rank(snapshot.asset_id, "mom_12_1") if context else None
        if momentum is not None and momentum < 0:
            return "MOMENTUM_NEGATIVE"
        if place is not None and place[0] > self.keep:
            return "RANK_DROPPED"
        return None


class PostEarningsDrift(Strategy):
    """After an earnings release, buy if the first full trading bar after it rose more than 2% on at least 1.5x
    normal volume (a price-based proxy for a positive surprise; free data has no analyst consensus); hold 20 bars."""

    stop_loss_atr = 2.0

    def entry_score(self, snapshot, context=None):
        if context is None or context.earnings is None:
            return None
        v = snapshot.values
        if v.get("return_1") is None or v.get("relative_volume") is None:
            return None
        bar_end = snapshot.as_of
        recent = [e for e in context.earnings(snapshot.asset_id, context.now)
                  if bar_end - timedelta(days=1, hours=1) < parse_utc(e["available_at"]) < bar_end]
        if not recent or not (v["return_1"] > 0.02 and v["relative_volume"] >= 1.5):
            return None
        return float(v["return_1"])


class RandomEntry(Strategy):
    """Research control: enters on a seeded coin flip. Any evaluation gate must reject it.

    The decision is a hash of (seed, asset, bar time), so a replay is reproducible and the "randomness" cannot see
    the future.
    """

    probability = 0.05

    def __init__(self, spec: StrategySpec, seed: int = 0):
        super().__init__(spec)
        self.seed = seed

    def entry_score(self, snapshot, context=None):
        digest = hashlib.sha256(f"{self.seed}|{snapshot.asset_id}|{snapshot.as_of.isoformat()}".encode()).digest()
        draw = int.from_bytes(digest[:8], "big") / 2 ** 64
        return 1.0 if draw < self.probability else None


IMPLEMENTATIONS: dict[str, type[Strategy]] = {
    "breakout-volume": BreakoutVolume, "trend-sma200": TrendSma200, "meanrev-rsi2": MeanReversionRsi2,
    "volatility-breakout": VolatilityBreakout, "relative-strength": RelativeStrength,
    "earnings-drift": PostEarningsDrift, "random-entry": RandomEntry}

EQ, CR = AssetClass.EQUITY, AssetClass.CRYPTO


def baseline_specs() -> list[StrategySpec]:
    return [
        StrategySpec("breakout-volume", "1.0.0", (EQ, CR), ("breakout_20", "relative_volume"), "BREAKOUT_VOLUME",
                     3, 20, approval="MOCK"),
    ]


def library_specs() -> list[StrategySpec]:
    """Phase 4 strategy library: RESEARCH until a strategy passes the evaluation gate and the owner approves it.
    exit_after_bars is a maximum holding period; most of these exit earlier on their own signal."""
    return [
        StrategySpec("trend-sma200", "1.0.0", (EQ, CR), ("dist_sma_200", "ret_126"), "TREND_SMA200", 252, 20,
                     approval="RESEARCH"),
        StrategySpec("meanrev-rsi2", "1.0.0", (EQ,), ("rsi_2", "dist_sma_200", "sma_5"), "MEANREV_RSI2", 5, 20,
                     approval="RESEARCH"),
        StrategySpec("volatility-breakout", "1.0.0", (EQ, CR), ("volatility_ratio_20_252", "breakout_20"),
                     "VOL_BREAKOUT", 20, 20, approval="RESEARCH"),
        StrategySpec("relative-strength", "1.0.0", (EQ,), ("mom_12_1",), "RELATIVE_STRENGTH", 63, 20,
                     approval="RESEARCH"),
        StrategySpec("earnings-drift", "1.0.0", (EQ,), ("return_1", "relative_volume"), "EARNINGS_DRIFT", 20, 20,
                     approval="RESEARCH"),
    ]


def research_specs() -> list[StrategySpec]:
    """Controls used only by the evaluation harness; never approved for paper or live."""
    return [StrategySpec("random-entry", "1.0.0", (EQ, CR), (), "RANDOM_ENTRY", 3, 20, approval="RESEARCH")]


def all_specs() -> list[StrategySpec]:
    return baseline_specs() + library_specs() + research_specs()


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

    def implementation(self, strategy_id: str, version: str) -> Strategy | None:
        return self.impls.get((strategy_id, version))

    def candidates(self, snapshot: FeatureSnapshot, now: datetime, mode: Mode,
                   context: DecisionContext | None = None) -> list[Candidate]:
        """Entry candidates from every eligible strategy, using only point-in-time information."""
        if snapshot.quality != "VALID" or now < snapshot.available_at or now > snapshot.expires_at:
            return []
        found = []
        for spec in self.eligible(mode, snapshot.asset_class):
            if any(snapshot.values.get(k) is None for k in spec.required_features):
                continue
            score = self.impls[(spec.strategy_id, spec.version)].entry_score(snapshot, context)
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

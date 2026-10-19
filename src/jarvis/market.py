"""Separate equity/crypto feature clocks and a bounded, explainable scanner."""

from __future__ import annotations

import math
import hashlib
from datetime import datetime, timedelta
from statistics import mean, pstdev

from .contracts import AssetClass, Bar, Candidate, FeatureSnapshot, require_utc


def stable_id(prefix: str, *parts: str) -> str:
    return prefix + "_" + hashlib.sha256("|".join(parts).encode()).hexdigest()[:24]


def features_for(bars: list[Bar], as_of: datetime, *, horizon: timedelta = timedelta(hours=1)) -> FeatureSnapshot:
    require_utc(as_of)
    known = [b for b in bars if b.available_at <= as_of]
    known.sort(key=lambda b: b.end_at)
    if not known:
        raise ValueError("no historically available bars")
    asset, cls = known[-1].asset_id, known[-1].asset_class
    if any(b.asset_id != asset or b.asset_class != cls for b in known):
        raise ValueError("mixed asset feature input")
    last = known[-1]
    closes = [b.close for b in known]
    returns = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    previous = known[-2] if len(known) > 1 else None
    prior_high = max((b.high for b in known[-21:-1]), default=None)
    prior_volume = mean([b.volume for b in known[-21:-1]]) if previous else None
    body = last.close - last.open
    values: dict[str, float | None] = {
        "return_1": returns[-1] if returns else None,
        "gap": last.open / previous.close - 1 if previous else None,
        "sma_5": mean(closes[-5:]) if len(closes) >= 5 else None,
        "sma_20": mean(closes[-20:]) if len(closes) >= 20 else None,
        "momentum_5": closes[-1] / closes[-6] - 1 if len(closes) >= 6 else None,
        "volatility_20": pstdev(returns[-20:]) if len(returns) >= 20 else None,
        "relative_volume": last.volume / prior_volume if prior_volume and prior_volume > 0 else None,
        "breakout_20": (last.close / prior_high - 1) if prior_high else None,
        "candle_body_ratio": body / (last.high - last.low) if last.high > last.low else 0.0,
        "candle_bullish": 1.0 if body > 0 else 0.0,
        "trend_strength": (mean(closes[-5:]) / mean(closes[-20:]) - 1) if len(closes) >= 20 else None,
    }
    if cls == AssetClass.CRYPTO:
        values["session_gap_applicable"] = 0.0
        values["gap"] = None  # crypto has no regular session open
    else:
        values["session_gap_applicable"] = 1.0
    return FeatureSnapshot(
        snapshot_id=stable_id("snap", asset, cls.value, last.end_at.isoformat(), last.source_id, str(last.revision)), asset_id=asset, asset_class=cls, as_of=last.end_at,
        available_at=last.available_at, expires_at=last.available_at + horizon,
        source_ids=tuple(f"{b.source_id}:{b.end_at.isoformat()}:{b.revision}" for b in known[-21:]),
        values=values,
    )


def scan(snapshot: FeatureSnapshot, now: datetime, *, max_candidates: int = 10) -> list[Candidate]:
    require_utc(now)
    if snapshot.quality != "VALID" or now < snapshot.available_at or now > snapshot.expires_at:
        return []
    v = snapshot.values
    triggers: list[tuple[str, float]] = []
    if v["breakout_20"] is not None and v["relative_volume"] is not None:
        if v["breakout_20"] > 0 and v["relative_volume"] >= 1.5:
            triggers.append(("BREAKOUT_VOLUME", float(v["breakout_20"] * v["relative_volume"])))
    if snapshot.asset_class == AssetClass.EQUITY and v["gap"] is not None:
        if abs(v["gap"]) >= 0.02 and (v["relative_volume"] or 0) >= 1.5:
            triggers.append(("EQUITY_GAP_VOLUME", float(abs(v["gap"]))))
    if (v["momentum_5"] or 0) > 0.03 and (v["relative_volume"] or 0) >= 2:
        triggers.append(("MOMENTUM_VOLUME", float(v["momentum_5"])))
    return [
        Candidate(stable_id("cand", snapshot.snapshot_id, name), snapshot.asset_id, snapshot.asset_class, now,
                  min(snapshot.expires_at, now + timedelta(minutes=30)), snapshot.snapshot_id, name, score)
        for name, score in sorted(triggers, key=lambda item: item[1], reverse=True)[:max_candidates]
    ]


def validate_feed(bars: list[Bar]) -> tuple[bool, tuple[str, ...]]:
    if not bars:
        return False, ("NO_DATA",)
    ordered = sorted(bars, key=lambda b: b.end_at)
    reasons = []
    if len({(b.asset_id, b.end_at, b.revision) for b in bars}) != len(bars):
        reasons.append("DUPLICATE_BAR")
    if any(a.end_at >= b.end_at for a, b in zip(ordered, ordered[1:])):
        reasons.append("NON_INCREASING_TIME")
    if any(not math.isfinite(b.close) or not math.isfinite(b.volume) for b in bars):
        reasons.append("NON_FINITE_DATA")
    return not reasons, tuple(reasons)

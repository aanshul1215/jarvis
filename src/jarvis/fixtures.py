"""Explicitly synthetic multiasset fixtures; never represented as market evidence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math

from .contracts import AssetClass, Bar


def synthetic_bars(asset_id: str = "AAPL", asset_class: AssetClass = AssetClass.EQUITY) -> list[Bar]:
    base = datetime(2026, 10, 1, 13, 0, tzinfo=timezone.utc)
    price = 100.0 if asset_class == AssetClass.EQUITY else 1000.0
    bars = []
    for index in range(26):
        start = base + timedelta(hours=index)
        end = start + timedelta(hours=1)
        close = price + index * (0.15 if asset_class == AssetClass.EQUITY else 1.5)
        if index == 25:
            close += 4 if asset_class == AssetClass.EQUITY else 40
        opn = close - (0.2 if asset_class == AssetClass.EQUITY else 2)
        bars.append(Bar(asset_id, asset_class, start, end, end + timedelta(seconds=1), opn,
                        close + 0.1, opn - 0.1, close, 3000 if index == 25 else 1000,
                        "SYNTHETIC_FIXTURE", "SYNTHETIC", "NONE"))
    return bars


def research_bars(asset_id: str = "AAPL", asset_class: AssetClass = AssetClass.EQUITY) -> list[Bar]:
    """Deterministic synthetic history with both up and down outcomes."""
    base = datetime(2025, 1, 1, 14, 0, tzinfo=timezone.utc)
    bars = []
    price = 100.0 if asset_class == AssetClass.EQUITY else 1000.0
    for index in range(260):
        start = base + timedelta(hours=index if asset_class == AssetClass.CRYPTO else index * 24)
        end = start + timedelta(hours=1)
        change = 0.004 * math.sin(index * .43) + 0.002 * math.cos(index * .17)
        if index % 37 == 0:
            change += 0.025
        old, price = price, price * (1 + change)
        high, low = max(old, price) * 1.002, min(old, price) * .998
        bars.append(Bar(asset_id, asset_class, start, end, end + timedelta(seconds=1),
                        old, high, low, price, 3000 if index % 37 == 0 else 1000 + index % 13,
                        "SYNTHETIC_FIXTURE", "SYNTHETIC", "NONE"))
    return bars

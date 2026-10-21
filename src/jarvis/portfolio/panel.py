"""Aligned daily price panel for the whole universe, built point in time.

Rows are US trading days (the stock calendar); columns are assets. For a stock or ETF, row d holds the session of
day d (09:30-16:00 New York), known from 16:15. Crypto trades every day: row d holds the Alpaca daily bar of UTC day
d, which closes at 00:00 UTC on d + 1. A decision for row d is therefore taken after both have closed (the paper
desk decides the next morning). Weekend crypto moves are carried into the next row's return, not lost.

Execution prices: the target weights decided at row d trade at row d + 1's ``open``. For stocks that is the next
session's open; for crypto it is the first price of UTC day d + 1, i.e. the close the decision was based on (no
look-ahead, slightly optimistic timing, measured later as implementation shortfall).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np

from ..contracts import AssetClass
from ..history import UniverseAsset
from ..storage import LocalStorage
from ..timeframes import NEW_YORK

EQUITY_DATASET, CRYPTO_DATASET = "1Day-adjusted", "1Day-raw"
# Per-side trading cost in basis points (spread + fee), as in replay.CostModel, plus a thin-ETF premium.
COST_BPS = {AssetClass.EQUITY: 5.0, AssetClass.CRYPTO: 30.0}
THIN = {"CPER": 15.0}  # copper ETF: 47 zero-volume days since 2016; assume wider spreads
BORROW_BPS_PER_YEAR = 100.0  # stock/ETF borrow fee assumed for shorts (general collateral is usually lower)


@dataclass
class Panel:
    dates: list[date]
    assets: list[str]
    classes: list[AssetClass]
    open: np.ndarray    # (T, N), NaN where the asset has no data yet
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray

    @property
    def shape(self) -> tuple[int, int]:
        return self.close.shape

    def index(self, asset: str) -> int:
        return self.assets.index(asset)

    def returns(self) -> np.ndarray:
        """Close-to-close simple returns; row d is the return from row d - 1 to row d (NaN where unknown)."""
        out = np.full(self.close.shape, np.nan)
        out[1:] = self.close[1:] / self.close[:-1] - 1
        return out

    def cost_bps(self) -> np.ndarray:
        return np.array([THIN.get(a, COST_BPS[c]) for a, c in zip(self.assets, self.classes)])

    def shortable(self) -> np.ndarray:
        """Alpaca does not short crypto; stocks and ETFs may be shorted (owner decision 2026-10-20)."""
        return np.array([c == AssetClass.EQUITY for c in self.classes])

    def until(self, last: int) -> "Panel":
        """The panel as known at row ``last`` (inclusive): later rows are cut off, not masked."""
        cut = slice(0, last + 1)
        return Panel(self.dates[cut], self.assets, self.classes, self.open[cut], self.high[cut], self.low[cut],
                     self.close[cut], self.volume[cut])


def _session_day(bar) -> date:
    return bar.start_at.astimezone(NEW_YORK).date()


def build_panel(store: LocalStorage, universe: list[UniverseAsset], *, start: date | None = None,
                end: date | None = None) -> Panel:
    equities = [a for a in universe if a.asset_class == AssetClass.EQUITY]
    crypto = [a for a in universe if a.asset_class == AssetClass.CRYPTO]
    series: dict[str, dict[date, tuple]] = {}
    for asset in equities:
        series[asset.symbol] = {_session_day(b): (b.open, b.high, b.low, b.close, b.volume)
                                for b in store.load_bars(asset.symbol, asset.asset_class, dataset=EQUITY_DATASET)}
    calendar = sorted(set().union(*(set(s) for s in series.values()))) if series else []
    if start:
        calendar = [d for d in calendar if d >= start]
    if end:
        calendar = [d for d in calendar if d <= end]
    for asset in crypto:
        bars = store.load_bars(asset.symbol, asset.asset_class, dataset=CRYPTO_DATASET)
        by_utc_day = {b.start_at.date(): b for b in bars}
        rows: dict[date, tuple] = {}
        days = sorted(by_utc_day)
        j = 0
        for d in calendar:
            # Last crypto bar of a UTC day on or before d (weekend moves reach the next row through its close).
            while j < len(days) and days[j] <= d:
                j += 1
            if j == 0:
                continue
            bar = by_utc_day[days[j - 1]]
            if (d - days[j - 1]).days > 3:
                continue  # stale: no recent crypto data
            rows[d] = (None, bar.high, bar.low, bar.close, bar.volume)
        series[asset.symbol] = rows
    assets = [a.symbol for a in equities + crypto]
    classes = [a.asset_class for a in equities + crypto]
    t, n = len(calendar), len(assets)
    arrays = {k: np.full((t, n), np.nan) for k in ("open", "high", "low", "close", "volume")}
    position = {d: i for i, d in enumerate(calendar)}
    for j, asset in enumerate(assets):
        for d, values in series[asset].items():
            i = position.get(d)
            if i is None:
                continue
            for key, value in zip(("open", "high", "low", "close", "volume"), values):
                if value is not None:
                    arrays[key][i, j] = value
        if classes[j] == AssetClass.CRYPTO:
            # Crypto "open" of row d = the price at the start of UTC day d = the previous row's close.
            arrays["open"][1:, j] = arrays["close"][:-1, j]
    return Panel(calendar, assets, classes, **arrays)

"""Historical bar back-fill from Alpaca into point-in-time datasets (Phase 2).

Datasets per asset (``market/<class>/<asset>/<dataset>.parquet``):
- equities: ``1Day-raw``, ``1Day-adjusted`` (splits and dividends), ``1Hour-raw``;
- crypto: ``1Day-raw``, ``1Hour-raw``.

Availability is deterministic, so rebuilding a dataset from scratch gives identical files: a bar is treated as
known ``AVAILABILITY_LAG`` after it ends. For equities the lag is 15 minutes, matching the free plan's restriction
on the most recent 15 minutes of consolidated (SIP) data. Adjusted prices are rewritten by later splits and
dividends, so use them for returns, not for price-level features.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .contracts import AssetClass, Bar, LedgerEvent, iso, new_id, require_utc, utc_now
from .quality import check_bars
from .storage import LocalStorage

AVAILABILITY_LAG = {AssetClass.EQUITY: timedelta(minutes=15), AssetClass.CRYPTO: timedelta(minutes=1)}
STEP = {"1Day": timedelta(days=1), "1Hour": timedelta(hours=1)}
DATASETS = {AssetClass.EQUITY: (("1Day", "raw"), ("1Day", "all"), ("1Hour", "raw")),
            AssetClass.CRYPTO: (("1Day", "raw"), ("1Hour", "raw"))}
CHUNK = timedelta(days=366)  # one request window; the SDK pages within it


@dataclass(frozen=True)
class UniverseAsset:
    symbol: str
    asset_class: AssetClass


def load_universe(path: Path) -> list[UniverseAsset]:
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in ("version", "equities", "crypto"):
        if key not in data:
            raise ValueError(f"universe file missing '{key}'")
    assets = [UniverseAsset(s, AssetClass.EQUITY) for s in data["equities"]]
    assets += [UniverseAsset(s, AssetClass.CRYPTO) for s in data["crypto"]]
    symbols = [a.symbol for a in assets]
    if not assets or len(set(symbols)) != len(symbols) or not all(isinstance(s, str) and s for s in symbols):
        raise ValueError("universe symbols must be unique non-empty strings")
    if any("/" not in a.symbol for a in assets if a.asset_class == AssetClass.CRYPTO):
        raise ValueError("crypto symbols use the BASE/QUOTE form, e.g. BTC/USD")
    return assets


def dataset_name(timeframe: str, adjustment: str) -> str:
    return f"{timeframe}-{'adjusted' if adjustment == 'all' else adjustment}"


def _request(asset: UniverseAsset, timeframe: str, adjustment: str, start: datetime, end: datetime, feed: str):
    from alpaca.data.enums import Adjustment, DataFeed
    from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    frame = TimeFrame.Day if timeframe == "1Day" else TimeFrame.Hour
    if asset.asset_class == AssetClass.EQUITY:
        return StockBarsRequest(symbol_or_symbols=asset.symbol, timeframe=frame, start=start, end=end,
                                adjustment=Adjustment(adjustment), feed=DataFeed(feed))
    return CryptoBarsRequest(symbol_or_symbols=asset.symbol, timeframe=frame, start=start, end=end)


def to_bars(asset: UniverseAsset, timeframe: str, models: list[Any], *, source_id: str, feed: str) -> list[Bar]:
    bars = []
    for model in models:
        start = require_utc(model.timestamp)
        end = start + STEP[timeframe]
        bars.append(Bar(asset.symbol, asset.asset_class, start, end, end + AVAILABILITY_LAG[asset.asset_class],
                        float(model.open), float(model.high), float(model.low), float(model.close),
                        float(model.volume), source_id, feed, "ALPACA"))
    return bars


def backfill(store: LocalStorage, stock_client: Any, crypto_client: Any, assets: list[UniverseAsset], *,
             start: datetime, end: datetime | None = None, feed: str = "sip",
             timeframes: tuple[str, ...] = ("1Day", "1Hour")) -> dict:
    """Download history for every asset and dataset and merge it into the store; returns a quality report.

    ``end`` defaults to 16 minutes ago so a free account never requests the restricted most recent SIP window.
    Re-running is incremental and idempotent: unchanged bars are skipped, vendor amendments become revisions.
    """
    require_utc(start)
    end = end or (utc_now() - timedelta(minutes=16))
    report: dict[str, dict] = {}
    for asset in assets:
        for timeframe, adjustment in DATASETS[asset.asset_class]:
            if timeframe not in timeframes:
                continue
            name = dataset_name(timeframe, adjustment)
            source_id = f"ALPACA_{feed.upper()}_{name}" if asset.asset_class == AssetClass.EQUITY else f"ALPACA_CRYPTO_{name}"
            bars: list[Bar] = []
            window = start
            while window < end:
                window_end = min(window + CHUNK, end)
                request = _request(asset, timeframe, adjustment, window, window_end, feed)
                response = (stock_client.get_stock_bars(request) if asset.asset_class == AssetClass.EQUITY
                            else crypto_client.get_crypto_bars(request))
                models = response.data.get(asset.symbol, [])
                bars += to_bars(asset, timeframe, models, source_id=source_id,
                                feed=feed if asset.asset_class == AssetClass.EQUITY else "crypto-us")
                window = window_end
            bars = [b for b in bars if b.end_at <= end]  # never store a bar that had not finished
            if bars:
                store.save_bars(bars, dataset=name)
            stored = store.load_bars(asset.symbol, asset.asset_class, dataset=name)
            step = STEP[timeframe] if asset.asset_class == AssetClass.CRYPTO else None
            quality = check_bars(stored, expected_step=step)
            report[f"{asset.symbol}:{name}"] = {"downloaded": len(bars), "stored": quality["rows"],
                                                "first": quality.get("first"), "last": quality.get("last"),
                                                "issues": quality["counts"]}
    store.append_event(LedgerEvent(new_id("evt"), "HISTORY_BACKFILL", utc_now(), new_id("backfill"),
                                   source_id="ALPACA", payload={"start": iso(start), "end": iso(end),
                                                                "feed": feed, "datasets": report}))
    store.export_csv("history-backfill", [{"dataset": k, **{x: (json.dumps(y) if isinstance(y, dict) else y)
                                                                for x, y in v.items()}}
                                          for k, v in report.items()])
    return report


def alpaca_clients(key_id: str, secret: str):
    """Read-only historical data clients (market data needs the paper keys; no trading access is used)."""
    from alpaca.data import CryptoHistoricalDataClient, StockHistoricalDataClient

    return StockHistoricalDataClient(key_id, secret), CryptoHistoricalDataClient(key_id, secret)


def default_start() -> datetime:
    return datetime(2016, 1, 1, tzinfo=timezone.utc)

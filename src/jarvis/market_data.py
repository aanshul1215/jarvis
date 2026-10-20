"""Read-only Alpaca data boundary with explicit equity and crypto feed provenance."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from time import perf_counter

from .contracts import AssetClass, Bar, require_utc, utc_now
from .timeframes import bar_window


@dataclass(frozen=True)
class Quote:
    asset_id: str
    asset_class: AssetClass
    bid: float
    ask: float
    at: datetime
    observed_at: datetime
    feed: str
    latency_ms: float

    @property
    def spread_bps(self) -> float:
        return (self.ask - self.bid) / ((self.ask + self.bid) / 2) * 10000


class AlpacaMarketData:
    def __init__(self, key_id: str, secret: str, *, stock_feed: str = "iex"):
        from alpaca.data import CryptoHistoricalDataClient, StockHistoricalDataClient
        from alpaca.data.enums import DataFeed

        if stock_feed not in ("iex", "sip", "delayed_sip"):
            raise ValueError("unsupported stock feed")
        self.stock_feed = DataFeed(stock_feed)
        self.stock = StockHistoricalDataClient(key_id, secret)
        self.crypto = CryptoHistoricalDataClient(key_id, secret)

    def recent_bars(self, asset_id: str, asset_class: AssetClass, *, start: datetime,
                    end: datetime, limit: int = 200, timeframe: str = "1Hour") -> tuple[list[Bar], dict]:
        from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest
        from alpaca.data.timeframe import TimeFrame

        require_utc(start)
        require_utc(end)
        if not start < end or limit < 1 or limit > 1000:
            raise ValueError("invalid historical window or limit")
        began = perf_counter()
        frame = TimeFrame.Day if timeframe == "1Day" else TimeFrame.Hour
        if asset_class == AssetClass.EQUITY:
            request = StockBarsRequest(symbol_or_symbols=asset_id, start=start, end=end,
                                       timeframe=frame, limit=limit, feed=self.stock_feed)
            response = self.stock.get_stock_bars(request)
            feed = self.stock_feed.value
        else:
            request = CryptoBarsRequest(symbol_or_symbols=asset_id, start=start, end=end,
                                        timeframe=frame, limit=limit)
            response = self.crypto.get_crypto_bars(request)
            feed = "crypto-us-default"
        observed = utc_now()
        models = response.data.get(asset_id, [])
        bars = []
        for model in models:
            start_at, end_at = bar_window(asset_class, timeframe, model.timestamp)
            if end_at > observed:
                continue  # never process a still-open bar
            bars.append(Bar(asset_id, asset_class, start_at, end_at, observed, float(model.open),
                            float(model.high), float(model.low), float(model.close), float(model.volume),
                            "ALPACA_MARKET_DATA", feed, "ALPACA"))
        return bars, {"feed": feed, "requested_start": start.isoformat(), "requested_end": end.isoformat(),
                      "observed_at": observed.isoformat(), "access_latency_ms": round((perf_counter() - began) * 1000, 3),
                      "rows": len(bars), "attribution": "API_REQUEST_DURATION_ONLY"}

    def latest_quote(self, asset_id: str, asset_class: AssetClass) -> Quote:
        from alpaca.data.requests import CryptoLatestQuoteRequest, StockLatestQuoteRequest

        began = perf_counter()
        if asset_class == AssetClass.EQUITY:
            request = StockLatestQuoteRequest(symbol_or_symbols=asset_id, feed=self.stock_feed)
            data = self.stock.get_stock_latest_quote(request)
            feed = self.stock_feed.value
        else:
            request = CryptoLatestQuoteRequest(symbol_or_symbols=asset_id)
            data = self.crypto.get_crypto_latest_quote(request)
            feed = "crypto-us-default"
        observed = utc_now()
        model = data.get(asset_id)
        if model is None:
            raise ValueError("quote missing")
        bid, ask = float(model.bid_price), float(model.ask_price)
        if bid <= 0 or ask < bid:
            raise ValueError("invalid quote")
        return Quote(asset_id, asset_class, bid, ask, require_utc(model.timestamp), observed,
                     feed, round((perf_counter() - began) * 1000, 3))

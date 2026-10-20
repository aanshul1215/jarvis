from datetime import timedelta
from types import SimpleNamespace

from alpaca.data.enums import DataFeed

from jarvis.contracts import AssetClass, utc_now
from jarvis.market_data import AlpacaMarketData


class FakeDataClient:
    def __init__(self, symbol):
        self.symbol = symbol

    def get_stock_bars(self, request):
        return self._bars()

    def get_crypto_bars(self, request):
        return self._bars()

    def _bars(self):
        return SimpleNamespace(data={self.symbol: [SimpleNamespace(timestamp=utc_now() - timedelta(hours=3),
            open=100, high=102, low=99, close=101, volume=1000)]})

    def get_stock_latest_quote(self, request):
        return self._quote()

    def get_crypto_latest_quote(self, request):
        return self._quote()

    def _quote(self):
        return {self.symbol: SimpleNamespace(timestamp=utc_now(), bid_price=100, ask_price=101)}


def test_equity_crypto_read_only_data_boundary():
    for symbol, cls in (("AAPL", AssetClass.EQUITY), ("BTC/USD", AssetClass.CRYPTO)):
        data = AlpacaMarketData.__new__(AlpacaMarketData)
        data.stock_feed = DataFeed.IEX
        data.stock = FakeDataClient(symbol)
        data.crypto = FakeDataClient(symbol)
        now = utc_now()
        bars, diagnostics = data.recent_bars(symbol, cls, start=now - timedelta(days=1), end=now)
        assert len(bars) == 1
        assert bars[0].asset_id == symbol and bars[0].available_at >= bars[0].end_at
        assert diagnostics["attribution"] == "API_REQUEST_DURATION_ONLY"
        quote = data.latest_quote(symbol, cls)
        assert quote.spread_bps > 0 and quote.latency_ms >= 0


class LongHistoryClient(FakeDataClient):
    """Returns 1,200 hourly bars oldest first, as Alpaca does, and records whether a request limit was sent."""

    def __init__(self, symbol):
        super().__init__(symbol)
        self.limits = []

    def _bars(self):
        now = utc_now()
        return SimpleNamespace(data={self.symbol: [SimpleNamespace(timestamp=now - timedelta(hours=1201 - i),
                                                                   open=100 + i, high=101 + i, low=99 + i, close=100 + i, volume=1000)
                                                   for i in range(1200)]})

    def get_stock_bars(self, request):
        self.limits.append(request.limit)
        return self._bars()


def test_long_history_keeps_the_newest_bars_not_the_oldest():
    data = AlpacaMarketData.__new__(AlpacaMarketData)
    data.stock_feed = DataFeed.IEX
    data.stock = data.crypto = LongHistoryClient("AAPL")
    now = utc_now()
    bars, _ = data.recent_bars("AAPL", AssetClass.EQUITY, start=now - timedelta(days=60), end=now, limit=1060)
    assert len(bars) == 1060 and bars[-1].close == 100 + 1199   # newest bar kept
    assert data.stock.limits == [None]                           # whole window requested, then trimmed

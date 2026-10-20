from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace

from jarvis.broker import MockBroker
from jarvis.config import PaperAsset, PaperRuntime
from jarvis.contracts import AssetClass, utc_now
from jarvis.fixtures import synthetic_bars
from jarvis.market_data import Quote
from jarvis.risk import RiskPolicy
from jarvis.runner import PaperDesk
from jarvis.storage import LocalStorage


class FixtureData:
    def __init__(self, stale=False):
        self.stale = stale
        self.anchor = utc_now()

    def recent_bars(self, symbol, cls, *, start, end, limit, timeframe="1Hour"):
        source = synthetic_bars(symbol, cls)
        shift = self.anchor - source[-1].end_at - timedelta(minutes=30 if not self.stale else 180)
        return [replace(b, start_at=b.start_at + shift, end_at=b.end_at + shift,
                        available_at=b.available_at + shift) for b in source], {"feed": "SYNTHETIC", "rows": 26}

    def latest_quote(self, symbol, cls):
        price = synthetic_bars(symbol, cls)[-1].close
        return Quote(symbol, cls, price - .01, price, utc_now(), utc_now(), "SYNTHETIC", 1)


def _policy():
    return RiskPolicy("paper-test", ("AAPL", "BTC/USD"), ("breakout-volume",),
                      500, 500, 1000, 100, .25, 30, 3600,
                      paper_enabled=True, crypto_enabled=True, owner_approved=True)


def test_paper_cycle_contract_with_mock_broker(tmp_path):
    runtime = PaperRuntime((PaperAsset("AAPL", AssetClass.EQUITY, 250),
                            PaperAsset("BTC/USD", AssetClass.CRYPTO, 100)),
                           ("breakout-volume@1.0.0",), 60)
    with LocalStorage(tmp_path / "desk") as store:
        broker = MockBroker(cash=1000)
        desk = PaperDesk(store, broker, FixtureData(), _policy(), runtime)
        result = desk.run_once()
        assert result["mode"] == "PAPER"
        assert len(broker.orders) == 2
        assert all(x.status == "FILLED" for x in broker.orders.values())
        before = len(broker.orders)
        result = desk.run_once()
        assert len(broker.orders) == before


def test_stale_bar_blocks_paper_cycle(tmp_path):
    runtime = PaperRuntime((PaperAsset("AAPL", AssetClass.EQUITY, 250),),
                           ("breakout-volume@1.0.0",), 60)
    with LocalStorage(tmp_path / "desk") as store:
        broker = MockBroker(cash=1000)
        result = PaperDesk(store, broker, FixtureData(stale=True), _policy(), runtime).run_once()
        assert result["assets"]["AAPL"] == "BLOCK_DATA"
        assert not broker.orders

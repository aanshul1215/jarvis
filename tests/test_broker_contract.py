from types import SimpleNamespace

from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

from jarvis.broker import AlpacaPaperBroker, BrokerError
from jarvis.contracts import AssetClass, utc_now


class FakeTradingClient:
    def __init__(self):
        self.requests = []

    def submit_order(self, request):
        self.requests.append(request)
        return SimpleNamespace(id="paper-id", symbol=request.symbol, filled_qty="0",
                               filled_avg_price=None, status=SimpleNamespace(value="accepted"),
                               submitted_at=utc_now())


def test_paper_buy_limit_and_exit_market_boundary():
    broker = AlpacaPaperBroker.__new__(AlpacaPaperBroker)
    broker.client = FakeTradingClient()
    broker.enable_orders = True
    broker.asset_eligible = lambda symbol, cls: True
    broker.find_order = lambda client_id: None
    broker.submit("entry", "AAPL", AssetClass.EQUITY, "BUY", 2, 100.12)
    broker.submit("exit", "AAPL", AssetClass.EQUITY, "SELL", 2, 99.1)
    assert isinstance(broker.client.requests[0], LimitOrderRequest)
    assert broker.client.requests[0].limit_price == 100.12
    assert isinstance(broker.client.requests[1], MarketOrderRequest)
    broker.enable_orders = False
    try:
        broker.submit("blocked", "AAPL", AssetClass.EQUITY, "BUY", 1, 100)
    except BrokerError as exc:
        assert "disabled" in str(exc)
    else:
        raise AssertionError("paper enablement gate failed")

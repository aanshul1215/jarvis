"""Regression tests for the Phase 1 blockers found in the review of feature/jarvis-v1-implementation."""

from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace

import pytest

from jarvis.broker import AlpacaPaperBroker, BrokerError, MockBroker, normalize_symbol
from jarvis.config import PaperAsset, PaperRuntime
from jarvis.contracts import AssetClass, Mode, StrategyIntent, utc_now
from jarvis.engine import EQUITY_HIGH_WATER, TradingEngine
from jarvis.fixtures import synthetic_bars
from jarvis.market_data import Quote
from jarvis.risk import BrokerState, Governor, RiskPolicy
from jarvis.runner import PaperDesk
from jarvis.storage import LocalStorage
from jarvis.strategies import StrategyRegistry, baseline_specs


def _policy(**overrides):
    values = dict(version="phase1-test", approved_assets=("AAPL", "BTC/USD"),
                  approved_strategies=("breakout-volume",), max_order_notional=500, max_asset_notional=500,
                  max_portfolio_notional=1000, max_daily_loss=100, max_drawdown=.25, max_spread_bps=30,
                  max_quote_age_seconds=3600, paper_enabled=True, crypto_enabled=True, owner_approved=True)
    values.update(overrides)
    return RiskPolicy(**values)


class FixtureData:
    """Synthetic bars ending 30 minutes before a fixed anchor, so hourly timestamps are stable across polls."""

    def __init__(self):
        self.anchor = utc_now()
        self.revise_last = False

    def recent_bars(self, symbol, cls, *, start, end, limit, timeframe="1Hour"):
        source = synthetic_bars(symbol, cls)
        shift = self.anchor - source[-1].end_at - timedelta(minutes=30)
        bars = [replace(b, start_at=b.start_at + shift, end_at=b.end_at + shift,
                        available_at=b.available_at + shift) for b in source]
        if self.revise_last:
            bars[-1] = replace(bars[-1], volume=bars[-1].volume + 7)
        return bars, {"feed": "SYNTHETIC", "rows": len(bars)}

    def latest_quote(self, symbol, cls):
        price = synthetic_bars(symbol, cls)[-1].close
        return Quote(symbol, cls, price - .01, price, utc_now(), utc_now(), "SYNTHETIC", 1)


def _runtime(*assets):
    table = {"AAPL": PaperAsset("AAPL", AssetClass.EQUITY, 250),
             "BTC/USD": PaperAsset("BTC/USD", AssetClass.CRYPTO, 100)}
    return PaperRuntime(tuple(table[a] for a in assets), ("breakout-volume@1.0.0",), 60)


def _events(store, kind):
    return [row["event"] for row in store.read_events() if row["event"]["event_type"] == kind]


def test_second_identical_trade_places_a_new_exit(tmp_path):
    with LocalStorage(tmp_path / "desk") as store:
        broker = MockBroker(cash=1000)
        engine = TradingEngine(store, broker, Governor(_policy(max_quote_age_seconds=60)),
                               StrategyRegistry(baseline_specs()), Mode.SHADOW)
        engine.reconcile()
        for day in (1, 2):
            shift = timedelta(days=day)
            bars = [replace(b, start_at=b.start_at + shift, end_at=b.end_at + shift,
                            available_at=b.available_at + shift) for b in synthetic_bars()]
            engine.process(bars, as_of=bars[-1].available_at, quantity=1)
            assert broker.state().positions["AAPL"] == 1
            assert engine.exit_position("AAPL", AssetClass.EQUITY, bars[-1].close + 1, reason="TIME_EXIT") == "FILLED"
            assert broker.state().positions["AAPL"] == 0
        assert sum(order.side == "SELL" for order in broker.orders.values()) == 2
        assert len(_events(store, "TRADE_OUTCOME")) == 2


def test_repeated_exit_call_does_not_duplicate_the_outcome(tmp_path):
    with LocalStorage(tmp_path / "desk") as store:
        broker = MockBroker(cash=1000)
        engine = TradingEngine(store, broker, Governor(_policy(max_quote_age_seconds=60)),
                               StrategyRegistry(baseline_specs()), Mode.SHADOW)
        engine.reconcile()
        bars = synthetic_bars()
        engine.process(bars, as_of=bars[-1].available_at, quantity=1)
        engine.exit_position("AAPL", AssetClass.EQUITY, bars[-1].close, reason="TIME_EXIT")
        broker.positions["AAPL"] = 1.0  # same quantity reappears: the stored, filled exit must not be re-counted
        engine.exit_position("AAPL", AssetClass.EQUITY, bars[-1].close, reason="TIME_EXIT")
        assert len(_events(store, "TRADE_OUTCOME")) == 1


def test_expired_entry_order_is_cancelled_and_frees_the_desk(tmp_path):
    data = FixtureData()
    with LocalStorage(tmp_path / "desk") as store:
        broker = MockBroker(cash=1000, fill_fraction=0.0)
        desk = PaperDesk(store, broker, data, _policy(), _runtime("BTC/USD"))
        first = desk.run_once()
        assert first["mode"] == "PAPER"
        assert broker.state().open_order_ids  # an entry that never filled
        held = desk.run_once()
        assert held["assets"]["BTC/USD"] == "OPEN_ORDER_HOLD"
        assert not _events(store, "ORDER_CANCEL")  # not yet expired
        desk.run_once(now=utc_now() + timedelta(minutes=45))
        assert _events(store, "ORDER_CANCEL")
        assert not broker.state().open_order_ids
        after = desk.run_once()
        assert after["mode"] == "PAPER" and after["assets"]["BTC/USD"] != "OPEN_ORDER_HOLD"


def test_open_order_holds_only_its_own_asset(tmp_path):
    data = FixtureData()
    with LocalStorage(tmp_path / "desk") as store:
        broker = MockBroker(cash=1000, fill_fraction=0.0)
        PaperDesk(store, broker, data, _policy(), _runtime("BTC/USD")).run_once()
        assert broker.state().open_order_ids
        broker.fill_fraction = 1.0
        result = PaperDesk(store, broker, data, _policy(), _runtime("BTC/USD", "AAPL")).run_once()
        assert result["assets"]["BTC/USD"] == "OPEN_ORDER_HOLD"
        assert any(row.get("result") == "FILLED" for row in result["assets"]["AAPL"])


def test_vendor_bar_revision_is_stored_not_safe(tmp_path):
    data = FixtureData()
    with LocalStorage(tmp_path / "desk") as store:
        broker = MockBroker(cash=1000)
        desk = PaperDesk(store, broker, data, _policy(), _runtime("AAPL"))
        assert desk.run_once()["mode"] == "PAPER"
        data.revise_last = True
        assert desk.run_once()["mode"] == "PAPER"
        revisions = store.load_bars("AAPL", AssetClass.EQUITY, all_revisions=True)
        assert max(b.revision for b in revisions) == 2
        assert len(store.load_bars("AAPL", AssetClass.EQUITY)) == len(synthetic_bars())


def test_crypto_fee_shortfall_is_recorded_but_a_real_mismatch_is_still_safe(tmp_path):
    data = FixtureData()
    with LocalStorage(tmp_path / "desk") as store:
        broker = MockBroker(cash=1000)
        PaperDesk(store, broker, data, _policy(), _runtime("BTC/USD")).run_once()
        bought = broker.positions["BTC/USD"]
        broker.positions["BTC/USD"] = bought * (1 - 0.0025)  # fee taken from the coin received
        result = PaperDesk(store, broker, data, _policy(), _runtime("BTC/USD")).run_once()
        assert result["mode"] == "PAPER"
        adjustment = _events(store, "POSITION_ADJUSTMENT")
        assert len(adjustment) == 1 and adjustment[0]["payload"]["delta"] == pytest.approx(-bought * 0.0025)
        PaperDesk(store, broker, data, _policy(), _runtime("BTC/USD")).run_once()
        assert len(_events(store, "POSITION_ADJUSTMENT")) == 1  # not re-applied on later cycles
        broker.positions["BTC/USD"] = bought * 0.95  # far beyond any fee
        with pytest.raises(BrokerError, match="mismatched"):
            PaperDesk(store, broker, data, _policy(), _runtime("BTC/USD")).run_once()


def test_drawdown_from_stored_peak_blocks_new_risk(tmp_path):
    with LocalStorage(tmp_path / "desk") as store:
        broker = MockBroker(cash=1000)
        store.publish_json(EQUITY_HIGH_WATER, {"equity": 2000.0, "at": "2026-10-01T00:00:00Z"})
        engine = TradingEngine(store, broker, Governor(_policy(max_quote_age_seconds=60)),
                               StrategyRegistry(baseline_specs()), Mode.SHADOW)
        engine.reconcile()
        bars = synthetic_bars()
        result = engine.process(bars, as_of=bars[-1].available_at, quantity=1)
        blocked = [row for row in result if row["result"] == "BLOCK"]
        assert blocked and "LOSS_LIMIT" in blocked[0]["reasons"]
        assert not broker.orders


def test_daily_loss_limit_blocks_new_risk():
    now = utc_now()
    intent = StrategyIntent("i", "c", "AAPL", AssetClass.EQUITY, "breakout-volume", "1.0.0", "baseline", "v1",
                            now, now + timedelta(minutes=1), "BUY", 1, 100, 3, "snap")
    state = BrokerState(1000, 1000, 1000, {}, reconciled=True, daily_pnl=-150)
    decision = Governor(_policy()).assess(intent, state, Mode.SHADOW, now, now, 2, "coid", set(), mock=True)
    assert decision.result == "BLOCK" and "LOSS_LIMIT" in decision.reason_codes


class FakeAccountClient:
    def __init__(self, last_equity="1100"):
        self.last_equity = last_equity

    def get_account(self):
        return SimpleNamespace(cash="500", buying_power="500", equity="1000", last_equity=self.last_equity)

    def get_all_positions(self):
        return [SimpleNamespace(symbol="BTCUSD", qty="0.01", market_value="650",
                                asset_class=SimpleNamespace(value="crypto"))]

    def get_orders(self, request):
        return []


def test_alpaca_state_reports_daily_pnl_and_normalises_crypto_symbols():
    broker = AlpacaPaperBroker.__new__(AlpacaPaperBroker)
    broker.client = FakeAccountClient()
    state = broker.state()
    assert state.daily_pnl == pytest.approx(-100)
    assert state.positions == {"BTC/USD": 0.01}
    broker.client = FakeAccountClient(last_equity=None)
    with pytest.raises(BrokerError, match="last_equity"):
        broker.state()


def test_symbol_normalisation():
    assert normalize_symbol("BTCUSD", "crypto") == "BTC/USD"
    assert normalize_symbol("ETHUSDT", "crypto") == "ETH/USDT"
    assert normalize_symbol("BTC/USD", "crypto") == "BTC/USD"
    assert normalize_symbol("AAPL", "us_equity") == "AAPL"


def test_second_writer_gets_a_clear_error(tmp_path):
    with LocalStorage(tmp_path / "desk"):
        with pytest.raises(Exception) as caught:
            LocalStorage(tmp_path / "desk")
        assert type(caught.value).__name__ == "StorageError"

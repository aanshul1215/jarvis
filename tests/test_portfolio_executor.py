"""Portfolio executor: weights become safe paper orders (caps, shorts, stops), journaled and reconcilable."""

from datetime import timedelta

import pytest

from jarvis.broker import MockBroker
from jarvis.contracts import AssetClass, utc_now
from jarvis.history import UniverseAsset
from jarvis.market_data import Quote
from jarvis.portfolio.executor import PortfolioDesk
from jarvis.risk import RiskPolicy
from jarvis.storage import LocalStorage

UNIVERSE = [UniverseAsset("SPY", AssetClass.EQUITY), UniverseAsset("TLT", AssetClass.EQUITY),
            UniverseAsset("GLD", AssetClass.EQUITY), UniverseAsset("BTC/USD", AssetClass.CRYPTO)]
PRICES = {"SPY": 500.0, "TLT": 100.0, "GLD": 200.0, "BTC/USD": 50_000.0}


class Quotes:
    def __init__(self, prices=PRICES, spread_bps=2.0):
        self.prices, self.spread = dict(prices), spread_bps

    def latest_quote(self, asset, cls):
        mid = self.prices[asset]
        half = mid * self.spread / 20_000
        now = utc_now()
        return Quote(asset, cls, mid - half, mid + half, now, now, "test", 1.0)


class FixedTargets:
    method = "test"

    def __init__(self, weights):
        self.weights = weights

    def targets(self, drawdown):
        return self.weights, {"drawdown_used": drawdown}


def policy(**kw):
    values = dict(version="t", approved_assets=tuple(PRICES), approved_strategies=("portfolio",),
                  max_order_notional=1500, max_asset_notional=3000, max_portfolio_notional=10_000,
                  max_daily_loss=300, max_drawdown=0.25, max_spread_bps=50, max_quote_age_seconds=60,
                  paper_enabled=True, crypto_enabled=True, owner_approved=True, allocated_capital=10_000.0)
    values.update(kw)
    return RiskPolicy(**values)


def desk(store, broker, **kw):
    return PortfolioDesk(store, broker, Quotes(), policy(**kw), UNIVERSE)


def test_builds_positions_with_caps_whole_shares_and_sells_first(tmp_path):
    with LocalStorage(tmp_path / "d") as store:
        broker = MockBroker(cash=100_000, allow_short=True)
        result = desk(store, broker).run_once(FixedTargets({"SPY": 0.25, "TLT": -0.10, "BTC/USD": 0.05}),
                                              decision_day="2026-10-21")
        assert [o["side"] for o in result["planned"]] == ["SELL", "BUY", "BUY"]            # sells first
        assert broker.positions["TLT"] == -10                                                # $1,000 short, whole shares
        assert broker.positions["SPY"] == 2                                                  # $2,500 wanted, $1,500 cap
        assert broker.positions["BTC/USD"] == pytest.approx(500 / (50_005 * 1.002), abs=1e-8)  # $500 at ask + 0.2%
        events = [row["event"]["event_type"] for row in store.read_events()]
        assert events.count("ORDER_INTENT") == 3 and events.index("ORDER_INTENT") < events.index("BROKER_ORDER")


def test_crypto_is_never_shorted_and_short_cap_holds(tmp_path):
    with LocalStorage(tmp_path / "d") as store:
        broker = MockBroker(cash=100_000, allow_short=True)
        result = desk(store, broker).run_once(FixedTargets({"BTC/USD": -0.2, "TLT": -0.15, "GLD": -0.15,
                                                            "SPY": -0.15}), decision_day="2026-10-21")
        assert "BTC/USD" not in broker.positions
        short_value = -sum(q * PRICES[a] for a, q in broker.positions.items() if q < 0)
        assert short_value <= 3_000 + 1e-6 and "SHORT_CAP" in result["skipped"].values()


def test_after_a_loss_stop_only_risk_reducing_orders_go_through(tmp_path):
    with LocalStorage(tmp_path / "d") as store:
        broker = MockBroker(cash=100_000, allow_short=True)
        d = desk(store, broker)
        d.run_once(FixedTargets({"SPY": 0.15, "TLT": 0.10}), decision_day="2026-10-21")
        broker.cash -= 3_000                                                               # desk down $3,000 = 30%
        result = d.run_once(FixedTargets({"SPY": 0.30, "TLT": 0.0, "GLD": 0.10}), decision_day="2026-10-22")
        assert result["halted"]
        assert result["skipped"].get("SPY") == "LOSS_STOP_ACTIVE" and result["skipped"].get("GLD") == "LOSS_STOP_ACTIVE"
        assert broker.positions["TLT"] == 0                                                 # the exit was allowed


def test_restart_reconciles_shorts_and_a_rerun_day_places_no_duplicates(tmp_path):
    with LocalStorage(tmp_path / "d") as store:
        broker = MockBroker(cash=100_000, allow_short=True)
        targets = FixedTargets({"TLT": -0.10, "SPY": 0.10})
        desk(store, broker).run_once(targets, decision_day="2026-10-21")
        before = dict(broker.positions)
    with LocalStorage(tmp_path / "d") as store:                                            # a new process
        again = desk(store, broker).run_once(targets, decision_day="2026-10-21")
        assert broker.positions == before and again["orders"] == 0                       # reconciled, nothing new

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


def test_closing_a_short_buys_back_exactly_and_a_reduce_never_flips(tmp_path):
    with LocalStorage(tmp_path / "d") as store:
        broker = MockBroker(cash=100_000, allow_short=True)
        d = desk(store, broker)
        d.run_once(FixedTargets({"TLT": -0.10, "SPY": 0.12}), decision_day="2026-10-21")
        assert broker.positions == {"TLT": -10, "SPY": 2}                               # $1,200 at ~$501 = 2 shares
        d.run_once(FixedTargets({"TLT": 0.0, "SPY": -0.10}), decision_day="2026-10-22")    # close short; flip SPY
        assert broker.positions["TLT"] == 0                                                 # no 1-share stub
        assert broker.positions["SPY"] == 0                                                 # flip: closed first...
        d.run_once(FixedTargets({"SPY": -0.11}), decision_day="2026-10-23")              # capital is a bit under $10k
        assert broker.positions["SPY"] == -2                                                # ...short opened next cycle


def test_a_refused_order_is_recorded_and_does_not_lock_the_desk(tmp_path):
    class Refusing(MockBroker):
        def submit(self, client_order_id, asset_id, asset_class, side, quantity, reference_price):
            if asset_id == "GLD":
                from jarvis.broker import UncertainSubmission
                raise UncertainSubmission("broker said no")
            return super().submit(client_order_id, asset_id, asset_class, side, quantity, reference_price)

    with LocalStorage(tmp_path / "d") as store:
        broker = Refusing(cash=100_000, allow_short=True)
        first = desk(store, broker).run_once(FixedTargets({"GLD": 0.10, "SPY": 0.12}), decision_day="2026-10-21")
        assert first["results"]["GLD"].startswith("REJECTED") and broker.positions["SPY"] == 2
        second = desk(store, broker).run_once(FixedTargets({"SPY": 0.12}), decision_day="2026-10-22")
        assert second["orders"] == 0                                                        # reconciled, no SAFE


def test_unshortable_assets_and_disabled_crypto_are_respected(tmp_path):
    with LocalStorage(tmp_path / "d") as store:
        broker = MockBroker(cash=100_000, allow_short=False)
        result = desk(store, broker, crypto_enabled=False).run_once(
            FixedTargets({"TLT": -0.10, "BTC/USD": 0.05}), decision_day="2026-10-21")
        assert result["skipped"]["TLT"] == "NOT_SHORTABLE" and "BTC/USD" not in broker.positions


def test_unfilled_orders_from_an_earlier_cycle_are_cancelled_before_planning(tmp_path):
    with LocalStorage(tmp_path / "d") as store:
        broker = MockBroker(cash=100_000, allow_short=True, fill_fraction=0.5)
        d = desk(store, broker)
        d.run_once(FixedTargets({"TLT": 0.10}), decision_day="2026-10-21")                 # 9 ordered, 4.5 filled
        assert broker.positions["TLT"] == 4.5 and broker.state().open_order_ids
        result = d.run_once(FixedTargets({"TLT": 0.10}), decision_day="2026-10-22")
        assert result["cancelled_open_orders"] == 1
        assert not [c for c in broker.state().open_order_ids if broker.orders[c].status == "PARTIALLY_FILLED"
                    and c in result.get("results", {})]


def test_round7_desk_options_fractional_band_strategy_and_no_brake(tmp_path):
    with LocalStorage(tmp_path / "d") as store:
        broker = MockBroker(cash=10_000)
        d = PortfolioDesk(store, broker, Quotes(), policy(approved_strategies=("stock_book",)), UNIVERSE,
                          strategy_id="stock_book", fractional=True, band=0.001, band_rel=0.25, use_brake=False)
        result = d.run_once(FixedTargets({"SPY": 0.004, "TLT": 0.0}), decision_day="2026-10-21")
        assert broker.positions["SPY"] == pytest.approx(0.0798)  # $40 at the $501.05 limit, 4 decimals
        intents = [r["event"] for r in store.read_events() if r["event"]["event_type"] == "ORDER_INTENT"]
        assert intents and all(e["payload"]["strategy_id"] == "stock_book" for e in intents)
        with pytest.raises(FileNotFoundError):
            store.load_json("portfolio-equity-history")                           # no brake bookkeeping
        tiny = PortfolioDesk(store, broker, Quotes(), policy(approved_strategies=("stock_book",)), UNIVERSE,
                             strategy_id="stock_book", fractional=True, band=0.0, band_rel=0.0, use_brake=False)
        report = tiny.plan({"TLT": 0.00005}, broker.state(), 10_000)
        assert report.skipped.get("TLT") == "BELOW_ONE_DOLLAR"
    with pytest.raises(ValueError):
        PortfolioDesk(store, broker, Quotes(), policy(), UNIVERSE, strategy_id="stock_book")   # not approved


def test_an_empty_desk_builds_at_once_then_holds_until_its_rebalance_day(tmp_path):
    class NotToday(FixedTargets):
        def is_rebalance_day(self):
            return False

    with LocalStorage(tmp_path / "d") as store:
        broker = MockBroker(cash=10_000)
        d = PortfolioDesk(store, broker, Quotes(), policy(approved_strategies=("sector_rotation",)), UNIVERSE,
                          strategy_id="sector_rotation", use_brake=False)
        first = d.run_once(NotToday({"SPY": 0.3, "TLT": 0.3}), decision_day="2026-10-21")
        assert first["orders"] == 2 and first["diagnostics"].get("initial_build")
        second = d.run_once(NotToday({"SPY": 0.0, "TLT": 0.6}), decision_day="2026-10-22")
        assert second["orders"] == 0 and second["note"] == "not a rebalance day; holding"


def test_quotes_are_checked_against_the_time_each_is_fetched(tmp_path):
    clock = {"t": utc_now()}

    class SlowQuotes(Quotes):
        def latest_quote(self, asset, cls):
            clock["t"] += timedelta(seconds=30)                      # each quote takes 30 seconds to arrive
            mid = self.prices[asset]
            return Quote(asset, cls, mid * 0.9999, mid * 1.0001, clock["t"], clock["t"], "test", 1.0)

    with LocalStorage(tmp_path / "d") as store:
        broker = MockBroker(cash=10_000)
        d = PortfolioDesk(store, broker, SlowQuotes(), policy(approved_strategies=("stock_book",)), UNIVERSE,
                          clock=lambda: clock["t"], strategy_id="stock_book", use_brake=False)
        report = d.plan({"SPY": 0.1, "TLT": 0.1, "GLD": 0.1}, broker.state(), 10_000)
        assert not report.skipped and len(report.planned) == 3


def test_a_partial_first_build_keeps_building_until_nothing_is_skipped(tmp_path):
    class NotToday(FixedTargets):
        def is_rebalance_day(self):
            return False

    with LocalStorage(tmp_path / "d") as store:
        broker = MockBroker(cash=10_000)
        quotes = Quotes()
        d = PortfolioDesk(store, broker, quotes, policy(approved_strategies=("stock_book",)), UNIVERSE,
                          strategy_id="stock_book", use_brake=False)
        quotes.spread = 80.0                                          # every quote too wide: nothing can be bought
        first = d.run_once(NotToday({"SPY": 0.3, "TLT": 0.3}), decision_day="2026-10-21")
        assert first["orders"] == 0 and first["diagnostics"]["initial_build"]
        quotes.spread = 2.0
        second = d.run_once(NotToday({"SPY": 0.3, "TLT": 0.3}), decision_day="2026-10-22")
        assert second["orders"] == 2 and second["diagnostics"]["initial_build"]
        third = d.run_once(NotToday({"SPY": 0.0, "TLT": 0.6}), decision_day="2026-10-23")
        assert third["orders"] == 0                                   # built: now waits for its rebalance day

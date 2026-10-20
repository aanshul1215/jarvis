"""Phase 3 exit tests: the evaluation harness rejects noise and catches leaks (synthetic data only)."""

import bisect
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from jarvis.contracts import AssetClass, Bar, StrategySpec
from jarvis.harness import BacktestSpec, ExperimentRegistry, evaluate
from jarvis.replay import CostModel, LookAheadError, ReplayBroker, ReplayClock, ReplayData
from jarvis.storage import LocalStorage
from jarvis.strategies import IMPLEMENTATIONS, Strategy, baseline_specs, research_specs

from synthetic import SYMBOLS, build_market

UTC = timezone.utc
ASSETS = tuple((s, AssetClass.EQUITY) for s in SYMBOLS)
START, END = datetime(2016, 3, 1, tzinfo=UTC), datetime(2018, 6, 29, tzinfo=UTC)


@pytest.fixture(scope="module")
def market(tmp_path_factory):
    home = tmp_path_factory.mktemp("market") / "data"
    with LocalStorage(home) as store:
        build_market(store)
    return home


def _spec(versions, **kw):
    return BacktestSpec(versions, ASSETS, "1Day-adjusted", "1Day", START, END, **kw)


class CandleContinuation(Strategy):
    """Enters after a strong up-candle and holds one bar. On a random walk this has no edge.

    With OracleData the "current price" handed to the order is today's not-yet-known close, so buy limits fill
    cheaply on up days and miss down days: a leak in the execution inputs rather than the signal, the same class of
    mistake as v1's next-day-return feature. It earns a Sharpe near 2, below the statistical alarm."""

    def entry_score(self, snapshot):
        bullish, body = snapshot.values.get("candle_bullish"), snapshot.values.get("candle_body_ratio")
        return 1.0 if bullish == 1.0 and body is not None and body > 0.6 else None


CANDLE = StrategySpec("candle-continuation", "1.0.0", (AssetClass.EQUITY,), ("candle_body_ratio",), "CANDLE_UP",
                      1, 20, approval="RESEARCH")


class OracleData(ReplayData):
    """A leak that slipped past every guard: each read also sees the next, not-yet-available bar."""

    def visible(self, symbol):
        return self.bars[symbol][:bisect.bisect_right(self._available[symbol], self.clock.now) + 1]

    def _checked(self, symbol):
        return self.visible(symbol)

    def recent_bars(self, symbol, cls, *, start, end, limit, timeframe="1Hour"):
        return [b for b in self.visible(symbol)[-limit * 2:] if start <= b.end_at][-limit:], {"feed": "ORACLE"}


class LeakyBugData(ReplayData):
    """A data bug that leaks one future bar but leaves the guard in place."""

    def visible(self, symbol):
        return self.bars[symbol][:bisect.bisect_right(self._available[symbol], self.clock.now) + 1]


def test_random_entry_fails_the_gate_and_raises_the_bar_for_later_trials(market):
    first = evaluate(market, _spec(("random-entry@1.0.0",), seed=1))
    second = evaluate(market, _spec(("random-entry@1.0.0",), seed=2))
    for record in (first, second):
        assert record["status"] == "COMPLETED" and not record["gate"]["passed"]
        assert "LEAK_SUSPECTED" not in record["gate"]["reasons"]
    assert second["gate"]["checks"]["p_threshold"] < first["gate"]["checks"]["p_threshold"]  # more trials, stricter


def test_planted_v1_style_leak_is_flagged_and_honest_run_is_not(market, monkeypatch):
    monkeypatch.setitem(IMPLEMENTATIONS, "candle-continuation", CandleContinuation)
    specs = baseline_specs() + research_specs() + [CANDLE]
    honest = evaluate(market, _spec(("candle-continuation@1.0.0",)), specs=specs)
    leaked = evaluate(market, _spec(("candle-continuation@1.0.0",)), specs=specs, data_cls=OracleData)
    assert "LEAK_SUSPECTED" not in honest["gate"]["reasons"] and not honest["gate"]["passed"]
    assert "LEAK_SUSPECTED" in leaked["gate"]["reasons"] and not leaked["gate"]["passed"]
    checks = leaked["gate"]["checks"]
    assert not checks["statistical_leak_alarm"]                 # too small for the Sharpe / win-rate alarm...
    assert not checks["future_poisoning"]["passed"]             # ...but the structural test catches it
    assert honest["gate"]["checks"]["future_poisoning"]["passed"]


def test_a_data_bug_that_leaks_the_future_aborts_the_evaluation(market):
    with pytest.raises(LookAheadError):
        evaluate(market, _spec(("breakout-volume@1.0.0",)), data_cls=LeakyBugData)
    assert ExperimentRegistry(market).records()[-1]["status"] == "FAILED"


def test_holdout_may_be_evaluated_once(tmp_path):
    home = tmp_path / "data"
    with LocalStorage(home) as store:
        build_market(store, end=datetime(2017, 1, 1, tzinfo=UTC))
    spec = BacktestSpec(("breakout-volume@1.0.0",), ASSETS, "1Day-adjusted", "1Day",
                        datetime(2016, 9, 1, tzinfo=UTC), datetime(2016, 12, 30, tzinfo=UTC), split="HOLDOUT")
    evaluate(home, spec)
    with pytest.raises(PermissionError, match="once"):
        evaluate(home, spec)
    records = ExperimentRegistry(home).records()
    assert [r["seq"] for r in records] == [1] and records[0]["prev_hash"] == "0" * 64


def _bar(start, o, h, l, c):
    return Bar("AAA", AssetClass.EQUITY, start, start + timedelta(hours=6, minutes=30),
               start + timedelta(hours=6, minutes=45), o, h, l, c, 1000, "T", "T")


class OneAssetStore:
    def __init__(self, bars):
        self.bars = bars

    def load_bars(self, symbol, cls, dataset):
        return self.bars


def test_replay_fills_at_the_next_open_with_costs_and_honours_limits():
    day = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    bars = [_bar(day, 100, 101, 99, 100), _bar(day + timedelta(days=1), 103, 104, 98, 102),
            _bar(day + timedelta(days=2), 106, 107, 105, 106)]
    clock = ReplayClock(day + timedelta(hours=7))
    costs = CostModel(equity_half_spread_bps=10)
    data = ReplayData(OneAssetStore(bars), [("AAA", AssetClass.EQUITY)], "1Day-adjusted", clock, costs)
    broker = ReplayBroker(clock, data, costs, cash=1000)
    order = broker.submit("buy", "AAA", AssetClass.EQUITY, "BUY", 2, 100.1)  # limit at yesterday's ask
    assert order.status == "ACCEPTED"                                           # nothing fills before the next open
    clock.now = day + timedelta(days=1)                                          # next open gaps to 103 > limit...
    broker.step()
    assert broker.orders["buy"].average_price == pytest.approx(100.1)           # ...but the low traded through it
    clock.now = day + timedelta(days=2, hours=7)
    broker.submit("sell", "AAA", AssetClass.EQUITY, "SELL", 2, 106)
    clock.now = day + timedelta(days=3)
    broker.step()
    assert broker.orders["sell"].status == "ACCEPTED"                           # no later bar: still working
    with pytest.raises(LookAheadError):
        clock.now = day - timedelta(days=1)
        data.visible = lambda symbol: bars                                       # simulate a bug serving the future
        data.latest_quote("AAA", AssetClass.EQUITY)

"""Phase 4 strategy library: entry and exit rules, cross-asset ranking, earnings timing and replay integration."""

from datetime import datetime, timedelta, timezone

import pytest

from jarvis.broker import MockBroker
from jarvis.contracts import AssetClass, Bar, FeatureSnapshot, Mode
from jarvis.edgar import EarningsCalendar
from jarvis.engine import TradingEngine
from jarvis.harness import BacktestSpec, future_poisoning_check, run_backtest
from jarvis.risk import Governor, RiskPolicy
from jarvis.storage import LocalStorage
from jarvis.strategies import (DecisionContext, MeanReversionRsi2, OpenPosition, PostEarningsDrift, RelativeStrength,
                               StrategyRegistry, TrendSma200, VolatilityBreakout, all_specs, library_specs)

from synthetic import SYMBOLS, build_market

UTC = timezone.utc
NOW = datetime(2024, 3, 6, 14, 31, tzinfo=UTC)
SPECS = {s.strategy_id: s for s in all_specs()}


def snap(asset="AAA", cls=AssetClass.EQUITY, as_of=NOW - timedelta(hours=22), **values):
    return FeatureSnapshot(f"snap_{asset}", asset, cls, as_of, as_of + timedelta(minutes=15),
                           as_of + timedelta(days=4), (), values)


def test_trend_enters_above_the_200_bar_average_and_exits_below_it():
    trend = TrendSma200(SPECS["trend-sma200"])
    assert trend.entry_score(snap(dist_sma_200=0.05, ret_126=0.1)) == pytest.approx(0.05)
    assert trend.entry_score(snap(dist_sma_200=0.05, ret_126=-0.1)) is None
    assert trend.entry_score(snap(dist_sma_200=-0.01, ret_126=0.1)) is None
    position = OpenPosition("AAA", 100.0, 10)
    assert trend.exit_reason(snap(dist_sma_200=-0.001), position) == "TREND_BROKEN"
    assert trend.exit_reason(snap(dist_sma_200=0.02), position) is None


def test_mean_reversion_buys_pullbacks_only_in_uptrends_and_exits_on_the_bounce():
    meanrev = MeanReversionRsi2(SPECS["meanrev-rsi2"])
    assert meanrev.entry_score(snap(rsi_2=4.0, dist_sma_200=0.1)) == pytest.approx(6.0)
    assert meanrev.entry_score(snap(rsi_2=4.0, dist_sma_200=-0.1)) is None
    assert meanrev.entry_score(snap(rsi_2=30.0, dist_sma_200=0.1)) is None
    assert meanrev.exit_reason(snap(close=101.0, sma_5=100.0), OpenPosition("AAA", 99.0, 1)) == "REVERTED"
    assert meanrev.stop_loss_atr == 2.0


def test_volatility_breakout_needs_contraction_then_a_range_break():
    vb = VolatilityBreakout(SPECS["volatility-breakout"])
    assert vb.entry_score(snap(volatility_ratio_20_252=0.6, breakout_20=0.01)) == pytest.approx(0.01 / 0.6)
    assert vb.entry_score(snap(volatility_ratio_20_252=0.9, breakout_20=0.01)) is None
    assert vb.exit_reason(snap(breakdown_20=-0.002), OpenPosition("AAA", 100.0, 3)) == "BROKE_DOWN"


def test_relative_strength_ranks_within_the_asset_class_with_a_buffer():
    rs = RelativeStrength(SPECS["relative-strength"])
    momentum = {f"S{i}": 0.30 - i * 0.05 for i in range(8)}          # S0 strongest ... S7 weakest
    snaps = {a: snap(a, mom_12_1=m) for a, m in momentum.items()}
    snaps["BTC/USD"] = snap("BTC/USD", AssetClass.CRYPTO, mom_12_1=5.0)  # other class: never ranked against stocks
    context = DecisionContext(NOW, snaps)
    assert context.rank("S0", "mom_12_1") == (1, 8)
    assert rs.entry_score(snaps["S2"], context) == pytest.approx(0.20)  # third: enters
    assert rs.entry_score(snaps["S3"], context) is None                 # fourth: does not enter...
    assert rs.exit_reason(snaps["S3"], OpenPosition("S3", 1, 5), context) is None  # ...but a holder keeps it (top 5)
    assert rs.exit_reason(snaps["S5"], OpenPosition("S5", 1, 5), context) == "RANK_DROPPED"
    assert rs.exit_reason(snaps["S7"], OpenPosition("S7", 1, 5), context) == "MOMENTUM_NEGATIVE"
    assert rs.entry_score(snaps["S0"], DecisionContext(NOW, {"S0": snaps["S0"]})) is None  # no cross-section


def test_earnings_drift_uses_only_releases_published_during_the_latest_bar():
    drift = PostEarningsDrift(SPECS["earnings-drift"])
    bar_end = datetime(2024, 3, 5, 21, 0, tzinfo=UTC)                    # 16:00 New York, reaction day
    release = {"available_at": "2024-03-04T21:31:00Z", "earnings_release": True}  # 16:31 the day before
    calendar = lambda ticker, as_of: [release] if as_of >= datetime(2024, 3, 4, 21, 31, tzinfo=UTC) else []  # noqa: E731
    reaction = snap(as_of=bar_end, return_1=0.035, relative_volume=2.0)
    assert drift.entry_score(reaction, DecisionContext(NOW, {}, calendar)) == pytest.approx(0.035)
    assert drift.entry_score(snap(as_of=bar_end, return_1=0.01, relative_volume=2.0),
                             DecisionContext(NOW, {}, calendar)) is None              # reaction too small
    later = snap(as_of=bar_end + timedelta(days=1), return_1=0.035, relative_volume=2.0)
    assert drift.entry_score(later, DecisionContext(NOW, {}, calendar)) is None       # release is a day old
    assert drift.entry_score(reaction, DecisionContext(NOW, {}, lambda t, a: [])) is None


def _bars(closes, start=datetime(2023, 1, 2, 14, 30, tzinfo=UTC)):
    bars = []
    for i, close in enumerate(closes):
        s = start + timedelta(days=i)
        bars.append(Bar("AAA", AssetClass.EQUITY, s, s + timedelta(hours=6, minutes=30), s + timedelta(hours=6, minutes=45),
                        close, close * 1.01, close * 0.99, close, 1000, "T", "T"))
    return bars


def test_engine_applies_the_owning_strategys_stop_loss_and_signal_exit(tmp_path):
    specs = [s.__class__(**{**s.__dict__, "approval": "MOCK"}) for s in library_specs() if s.strategy_id == "meanrev-rsi2"]
    policy = RiskPolicy("t", ("AAA",), ("meanrev-rsi2",), 5000, 5000, 5000, 1000, 0.5, 100, 10**6,
                        owner_approved=True, crypto_enabled=True)
    # 230 bars of a gentle uptrend, then a sharp two-day pullback: RSI(2) falls below 10 inside the uptrend.
    closes = [100 + i * 0.2 for i in range(230)] + [139.0, 136.0]
    bars = _bars(closes)
    with LocalStorage(tmp_path / "desk") as store:
        broker = MockBroker(cash=10_000)
        engine = TradingEngine(store, broker, Governor(policy), StrategyRegistry(specs), Mode.SHADOW)
        engine.reconcile()
        engine.process(bars, as_of=bars[-1].available_at, quantity=10, feature_horizon=timedelta(days=4))
        assert broker.state().positions.get("AAA") == 10
        crash = _bars(closes + [120.0])                                    # next bar: far below entry - 2 ATR
        assert engine.monitor_positions(crash)[0]["exit_reason"] == "STOP_LOSS"
        assert broker.state().positions["AAA"] == 0
        engine.process(bars, as_of=bars[-1].available_at, quantity=10, feature_horizon=timedelta(days=4))
        assert broker.state().positions["AAA"] == 0                        # same bar's candidate is not re-entered


LIB_SYMBOLS = SYMBOLS + ("EEE", "FFF", "GGG", "HHH")  # relative strength needs at least 6 assets to rank


@pytest.fixture(scope="module")
def market(tmp_path_factory):
    home = tmp_path_factory.mktemp("lib") / "data"
    with LocalStorage(home) as store:
        build_market(store, end=datetime(2018, 1, 1, tzinfo=UTC), symbols=LIB_SYMBOLS)
        for symbol in LIB_SYMBOLS:
            # Place synthetic earnings releases after the close on the day before genuinely strong, heavy-volume
            # bars, so the drift strategy really trades (random release dates would almost never qualify).
            bars = store.load_bars(symbol, AssetClass.EQUITY, dataset="1Day-adjusted")
            strong = [i for i in range(21, len(bars)) if bars[i].close / bars[i - 1].close - 1 > 0.02
                      and bars[i].volume >= 1.5 * sum(b.volume for b in bars[i - 20:i]) / 20][:4]
            rows = [{"ticker": symbol, "accession": f"{symbol}-{n}", "form": "8-K", "items": "2.02",
                     "filing_date": bars[i - 1].end_at.date().isoformat(), "earnings_release": True,
                     "available_at": (bars[i - 1].end_at + timedelta(minutes=31)).isoformat().replace("+00:00", "Z"),
                     "acceptance_source": "INDEX_PAGE"} for n, i in enumerate(strong)]
            if rows:
                store.write_table("edgar", "filings", symbol, rows=rows)
    return home


@pytest.mark.parametrize("strategy", [s.strategy_id for s in library_specs()])
def test_every_library_strategy_trades_in_replay_without_leaks(market, strategy):
    spec = BacktestSpec((f"{strategy}@1.0.0",), tuple((s, AssetClass.EQUITY) for s in LIB_SYMBOLS), "1Day-adjusted",
                        "1Day", datetime(2016, 3, 1, tzinfo=UTC), datetime(2017, 12, 29, tzinfo=UTC))
    with LocalStorage(market, writer=False) as store:
        result = run_backtest(store, spec)
        assert result["stopped"] is None
        assert result["fills"] > 0, "the strategy never traded, so this test would prove nothing"
        assert result["series"] and result["metrics"]["days"] > 400
        assert future_poisoning_check(store, spec, cutoffs=4)["passed"]


def test_earnings_calendar_is_point_in_time(market):
    with LocalStorage(market, writer=False) as store:
        calendar = EarningsCalendar(store, list(LIB_SYMBOLS))
        events = calendar("AAA", datetime(2018, 1, 1, tzinfo=UTC))
        assert events, "fixture placed no releases for AAA"
        first = datetime.fromisoformat(events[0]["available_at"].replace("Z", "+00:00"))
        assert calendar("AAA", first - timedelta(seconds=1)) == []
        assert calendar("AAA", first)[-1] == events[0]

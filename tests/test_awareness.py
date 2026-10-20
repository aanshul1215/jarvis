"""Phase 5 situational-awareness models: each must find structure that exists, find none where none exists, and
never look ahead. Synthetic data only; not market evidence."""

from datetime import date, datetime, timedelta, timezone

import numpy as np
import pytest

from jarvis import regime, riskmodel, volatility
from jarvis.awareness import SituationBuilder
from jarvis.macro import AsOfSeries
from jarvis.broker import MockBroker
from jarvis.contracts import AssetClass, FeatureSnapshot, Mode
from jarvis.costs import MIN_FILLS, compare as compare_costs, estimate_bps, fixed_bps, realised_costs
from jarvis.engine import TradingEngine
from jarvis.harness import BacktestSpec, future_poisoning_check, run_backtest
from jarvis.metrics import diebold_mariano
from jarvis.risk import Governor, RiskPolicy
from jarvis.storage import LocalStorage
from jarvis.strategies import StrategyRegistry, library_specs
from jarvis.volatility import PriceSeries

from synthetic import SYMBOLS, build_market

UTC = timezone.utc


def weekdays(n, start=date(1995, 1, 2)):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return tuple(out)


def from_returns(r, name="A", group="EQUITY"):
    return PriceSeries(name, group, weekdays(len(r) + 1), 100 * np.exp(np.concatenate([[0.0], np.cumsum(r)])))


def garch_returns(n, seed, omega=2e-6, alpha=0.08, beta=0.9):
    rng = np.random.default_rng(seed)
    s2, out = omega / (1 - alpha - beta), np.empty(n)
    for i in range(n):
        out[i] = rng.standard_normal() * np.sqrt(s2)
        s2 = omega + alpha * out[i] ** 2 + beta * s2
    return out


def switching_returns(n, seed):
    rng = np.random.default_rng(seed)
    state, out = 0, np.empty(n)
    for i in range(n):
        if rng.random() < (0.01 if state == 0 else 0.03):
            state = 1 - state
        out[i] = rng.normal(0.0006, 0.008) if state == 0 else rng.normal(-0.001, 0.025)
    return out


# --- statistics -----------------------------------------------------------------------------------------------------

def test_diebold_mariano_detects_a_real_gain_and_not_noise():
    rng = np.random.default_rng(0)
    null = [diebold_mariano(rng.normal(0.0, 1, 500), 5)["p_value"] < 0.05 for _ in range(400)]
    assert 0.02 < np.mean(null) < 0.09                                # rejects about 5% of the time under the null
    assert diebold_mariano(rng.normal(0.15, 1, 3000), 5)["p_value"] < 0.001
    assert diebold_mariano(np.ones(10))["p_value"] == 1.0  # too short to judge


# --- volatility -----------------------------------------------------------------------------------------------------

def test_volatility_study_recognises_a_garch_process():
    series = [from_returns(garch_returns(6000, 1), "A", "EQUITY"), from_returns(garch_returns(6000, 2), "B", "CRYPTO")]
    result = volatility.compare(series, horizon=5)
    assert result["candidates"]["garch"]["passed"]
    assert result["winner"] in ("garch", "har", "ewma")
    row = result["per_asset"]["A"]
    assert row["mean_qlike"]["garch"] < row["mean_qlike"]["rolling20"]


@pytest.mark.parametrize("name", list(volatility.MODELS))
def test_volatility_forecasts_never_use_later_returns_and_match_the_live_path(name):
    r = garch_returns(2600, 3)
    dates = weekdays(len(r))
    model = volatility.MODELS[name]
    first, clean = volatility.walk_forward(model, r, dates, 5)
    cut = first + 700
    poisoned = r.copy()
    poisoned[cut + 1:] = np.random.default_rng(9).normal(0, 0.2, len(r) - cut - 1)  # wild future
    _, dirty = volatility.walk_forward(model, poisoned, dates, 5)
    assert np.allclose(clean[:cut - first + 1], dirty[:cut - first + 1], rtol=1e-12, atol=0)
    live = volatility.forecast_now(name, r[:cut + 1], dates[:cut + 1], 5, cache={})
    assert live == pytest.approx(clean[cut - first], rel=1e-9)


def test_live_forecast_needs_enough_history_and_sizing_scales_with_risk():
    r = garch_returns(900, 4)
    assert volatility.forecast_now("garch", r, weekdays(len(r))) is None   # less than the fitting window
    assert volatility.forecast_now("rolling20", r, weekdays(len(r))) > 0
    assert volatility.scaled_notional(1000, 0.01) == pytest.approx(1000)
    assert volatility.scaled_notional(1000, 0.04) == pytest.approx(250)
    assert volatility.scaled_notional(1000, 0.001) == pytest.approx(1500)   # capped
    assert volatility.scaled_notional(1000, None) is None


# --- regimes --------------------------------------------------------------------------------------------------------

def test_regime_study_finds_real_regimes():
    result = regime.compare([from_returns(switching_returns(8000, 5), "A", "EQUITY"),
                             from_returns(switching_returns(8000, 6), "B", "CRYPTO")])
    assert result["tests"]["hmm2_vs_sma200"]["passed"] and result["tests"]["hmm2_vs_none"]["passed"]
    assert result["winner"] == "hmm2"


def test_regime_study_passes_nothing_when_there_are_no_regimes():
    rng = np.random.default_rng(7)
    result = regime.compare([from_returns(rng.normal(0.0003, 0.012, 2600), "A", "EQUITY"),
                             from_returns(rng.normal(0.0003, 0.012, 2600), "B", "CRYPTO")])
    assert result["winner"] in ("none", "sma200")


def test_live_regime_label_matches_the_study_labels():
    r = switching_returns(800, 8)
    closes = 100 * np.exp(np.concatenate([[0.0], np.cumsum(r)]))
    for name in ("none", "sma200", "trend_vol"):
        study = regime.static_labels(name, r, closes, None)
        for t in (300, 555, len(r) - 1):
            assert regime.current_label(name, r[:t + 1], closes[:t + 2]) == study[t]


def test_stress_flags_use_only_vix_published_before_the_decision():
    day = date(2024, 3, 5)
    vix = AsOfSeries([{"observation_date": "2024-03-04", "value": 15.0, "available_at": "2024-03-04T22:00:00Z", "revision": 1},
                      {"observation_date": "2024-03-05", "value": 40.0, "available_at": "2024-03-05T22:00:00Z", "revision": 1}])
    none = AsOfSeries([])
    assert regime.stress_flags((day,), "EQUITY", vix.at, none.at)[0] == 0   # 22:00 UTC is after the 21:15 decision
    assert regime.stress_flags((day,), "CRYPTO", vix.at, none.at)[0] == 1   # crypto decides at 01:15 UTC next day
    assert regime.stress_flags((date(2024, 3, 1),), "EQUITY", vix.at, none.at)[0] == -1  # no VIX yet
    inverted = AsOfSeries([{"observation_date": "2024-03-04", "value": 16.0, "available_at": "2024-03-04T22:00:00Z", "revision": 1}])
    assert regime.stress_flags((day,), "EQUITY", vix.at, inverted.at)[0] == 0   # 15 / 16 < 1
    assert regime.is_stressed(17.0, 16.0) and not regime.is_stressed(17.0, 18.0) and regime.is_stressed(25.0, None)


def test_live_hmm_label_matches_the_study():
    r = switching_returns(1400, 13)
    dates = weekdays(len(r))
    closes = 100 * np.exp(np.concatenate([[0.0], np.cumsum(r)]))
    first, _, labels = regime.detector_scores("hmm2", r, closes, dates, window=1000)
    for t in (first, first + 37, len(r) - 1):
        live = regime.live_label("hmm2", r[:t + 1], dates[:t + 1], closes[:t + 2], window=1000, cache={})
        assert live == labels[t - first]
    assert regime.live_label("hmm2", r[:500], dates[:500], closes[:501]) is None    # history too short


# --- correlation risk -----------------------------------------------------------------------------------------------

def correlated_series(corr, n=2000, assets=6, seed=11):
    rng = np.random.default_rng(seed)
    c = np.full((assets, assets), corr)
    np.fill_diagonal(c, 1)
    vol = np.linspace(0.008, 0.03, assets)
    r = rng.multivariate_normal(np.zeros(assets), c * np.outer(vol, vol), n)
    return [from_returns(r[:, i], f"S{i}") for i in range(assets)]


def test_risk_study_sees_correlation_only_when_it_exists():
    assert riskmodel.compare(correlated_series(0.6))["winner"] in ("sample", "shrunk")
    assert riskmodel.compare(correlated_series(0.0))["winner"] == "diagonal"


def test_shrinkage_is_a_valid_covariance_and_crowding_flags_one_big_bet():
    rng = np.random.default_rng(12)
    cov, intensity = riskmodel.shrunk_cov(rng.standard_normal((60, 8)) * 0.01)
    assert 0 <= intensity <= 1 and np.all(np.linalg.eigvalsh(cov) > 0)
    common = rng.normal(0, 0.01, 250)
    same = {a: common + rng.normal(0, 1e-4, 250) for a in "ABCD"}
    risk = riskmodel.portfolio_volatility({a: 1000 for a in same}, same)
    assert risk["crowding"] == pytest.approx(2.0, rel=0.02)          # four copies of one bet: sqrt(4)
    separate = {a: rng.normal(0, 0.01, 250) for a in "ABCD"}
    assert riskmodel.portfolio_volatility({a: 1000 for a in separate}, separate)["crowding"] == pytest.approx(1, abs=0.15)


# --- costs ----------------------------------------------------------------------------------------------------------

def test_cost_model_and_realised_shortfall_from_the_journal(tmp_path):
    assert fixed_bps(AssetClass.EQUITY) == pytest.approx(5) and fixed_bps(AssetClass.CRYPTO) == pytest.approx(30)
    assert estimate_bps(AssetClass.EQUITY, spread_bps=2) == pytest.approx(1)
    assert estimate_bps(AssetClass.EQUITY, spread_bps=2, daily_vol=0.02, order_notional=1e6,
                        average_daily_value=1e8) == pytest.approx(1 + 20)   # 1 x 2% x sqrt(1%) = 20 bps
    rows = [{"asset_class": AssetClass.EQUITY, "shortfall_bps": 1.0, "spread_bps": 2.0, "daily_vol": None}] * MIN_FILLS
    rows = [dict(r, shortfall_bps=1.0 + 0.1 * (i % 3)) for i, r in enumerate(rows)]
    assert compare_costs(rows[:10])["result"] == "INSUFFICIENT_DATA"
    assert compare_costs(rows)["mae_model_bps"] < compare_costs(rows)["mae_fixed_bps"]
    specs = [s.__class__(**{**s.__dict__, "approval": "MOCK"}) for s in library_specs() if s.strategy_id == "meanrev-rsi2"]
    policy = RiskPolicy("t", ("AAA",), ("meanrev-rsi2",), 5000, 5000, 5000, 1000, 0.5, 100, 10**6,
                        owner_approved=True, crypto_enabled=True)
    from test_strategies import _bars
    closes = [100 + i * 0.2 for i in range(230)] + [139.0, 136.0]
    with LocalStorage(tmp_path / "desk") as store:
        broker = MockBroker(cash=10_000)
        engine = TradingEngine(store, broker, Governor(policy), StrategyRegistry(specs), Mode.SHADOW)
        engine.reconcile()
        bars = _bars(closes)
        engine.process(bars, as_of=bars[-1].available_at, quantity=10, feature_horizon=timedelta(days=4),
                       sizing={"sizing": "fixed"})
        engine.exit_position("AAA", AssetClass.EQUITY, 136.0, reason="TEST")
        realised = realised_costs(store)
    assert {r["side"] for r in realised} == {"BUY", "SELL"}
    assert all(r["asset_id"] == "AAA" and r["asset_class"] == AssetClass.EQUITY for r in realised)


# --- awareness ------------------------------------------------------------------------------------------------------

def test_as_of_series_respects_publication_time_and_revisions():
    rows = [{"observation_date": "2024-01-02", "value": 10.0, "available_at": "2024-01-02T22:00:00Z", "revision": 1},
            {"observation_date": "2024-01-03", "value": 11.0, "available_at": "2024-01-03T22:00:00Z", "revision": 1},
            {"observation_date": "2024-01-02", "value": 12.0, "available_at": "2024-01-05T00:00:00Z", "revision": 2}]
    series = AsOfSeries(rows)
    assert series.at(datetime(2024, 1, 2, 21, tzinfo=UTC)) is None
    assert series.at(datetime(2024, 1, 3, 12, tzinfo=UTC)) == 10.0
    assert series.at(datetime(2024, 1, 4, tzinfo=UTC)) == 11.0
    assert series.at(datetime(2024, 1, 6, tzinfo=UTC)) == 11.0   # a revision of an older day does not replace newer


def test_situation_snapshot_combines_stress_breadth_events_and_desk_state(tmp_path):
    now = datetime(2024, 3, 6, 15, tzinfo=UTC)
    with LocalStorage(tmp_path / "data") as store:
        store.write_table("macro", "VIXCLS", rows=[{"series_id": "VIXCLS", "observation_date": "2024-03-05",
                                                    "value": 30.0, "available_at": "2024-03-05T22:00:00Z",
                                                    "revision": 1, "source": "t"}])
        store.write_table("calendar", "events", rows=[{"event_type": "FOMC_DECISION", "event_at": "2024-03-20T18:00:00Z",
                                                       "available_at": "2024-01-01T00:00:00Z", "cancelled": False}])
        builder = SituationBuilder(store)

    def snap(asset, **values):
        return FeatureSnapshot(f"s_{asset}", asset, AssetClass.EQUITY, now, now, now + timedelta(days=1), (), values)

    snaps = {"A": snap("A", dist_sma_200=0.1, ret_20=0.02, dist_high_252=0.0, return_1=0.01),
             "B": snap("B", dist_sma_200=-0.1, ret_20=-0.02, dist_high_252=-0.2, return_1=-0.01)}
    view = builder.build(now, snaps, desk={"drawdown": 0.02})
    assert view["market"]["vix"] == 30.0 and view["market"]["stress"] is True
    assert view["breadth"]["above_sma_200"] == 0.5 and view["breadth"]["at_252_high"] == 0.5
    assert view["calendar"]["hours_to_fomc"] == pytest.approx(14 * 24 + 3)
    assert view["desk"]["drawdown"] == 0.02


# --- integration ----------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def market(tmp_path_factory):
    home = tmp_path_factory.mktemp("vol") / "data"
    with LocalStorage(home) as store:
        build_market(store, start=datetime(2015, 1, 1, tzinfo=UTC), end=datetime(2017, 7, 1, tzinfo=UTC))
    return home


def test_volatility_sizing_in_replay_is_point_in_time(market):
    spec = BacktestSpec(("random-entry@1.0.0",), tuple((s, AssetClass.EQUITY) for s in SYMBOLS), "1Day-adjusted",
                        "1Day", datetime(2016, 3, 1, tzinfo=UTC), datetime(2017, 3, 1, tzinfo=UTC),
                        sizing="volatility", volatility_model="garch")  # under 1,000 returns: baseline sizes
    with LocalStorage(market, writer=False) as store:
        result = run_backtest(store, spec)
        orders = [c for c in result["candidates"] if c[0] == "ORDER"]
        assert result["fills"] > 0 and orders
        # Random-walk daily volatility is about 1.3%, so a $1,000 entry is usually cut to roughly $550-900 (the noisy
        # 20-day baseline sizes it here: under 1,000 returns of history GARCH cannot be fitted), less up to one
        # share (~$100) for rounding down to whole shares.
        notionals = [quantity * price for _, _, _, quantity, price in orders]
        assert all(300 < n <= 1500 for n in notionals), (min(notionals), max(notionals))  # never above the 1.5x cap
        assert len({round(n) for n in notionals}) > 3                     # sizes move with the forecast
        assert future_poisoning_check(store, spec, cutoffs=3)["passed"]


def test_holdout_needs_a_recorded_development_run_and_runs_once(tmp_path):
    from jarvis.studies import run_study
    home = tmp_path / "data"
    rng = np.random.default_rng(14)
    with LocalStorage(home) as store:
        for series_id, start in (("NASDAQCOM", date(2012, 1, 2)), ("CBBTCUSD", date(2015, 1, 1))):
            days = weekdays(4000, start) if series_id == "NASDAQCOM" else                 tuple(start + timedelta(days=i) for i in range(4300))
            closes = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, len(days))))
            store.write_table("macro", series_id, rows=[{"series_id": series_id, "observation_date": d.isoformat(),
                                                         "value": float(c), "available_at": f"{d.isoformat()}T23:00:00Z",
                                                         "revision": 1, "source": "test"} for d, c in zip(days, closes)])
    with pytest.raises(PermissionError, match="development"):
        run_study(home, "risk", split="HOLDOUT")
    assert run_study(home, "risk")["status"] == "COMPLETED"
    assert run_study(home, "risk", split="HOLDOUT")["status"] == "COMPLETED"
    with pytest.raises(PermissionError, match="once"):
        run_study(home, "risk", split="HOLDOUT")


def test_registry_appends_from_parallel_threads_keep_one_chain(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    from jarvis.studies import StudyRegistry
    registry = StudyRegistry(tmp_path)
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(lambda i: registry.append({"fingerprint": str(i), "spec": {"split": "DEVELOPMENT"}}), range(40)))
    rows = registry.records()
    assert [r["seq"] for r in rows] == list(range(1, 41))
    assert all(rows[i]["prev_hash"] == rows[i - 1]["hash"] for i in range(1, len(rows)))

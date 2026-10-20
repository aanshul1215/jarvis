"""Phase 7 strategy selector: point-in-time allocations, each stage learns planted structure and finds none in noise,
and the hooks act on real orders. Synthetic data only; not market evidence."""

from datetime import date, datetime, timedelta, timezone

import numpy as np
import pytest

from jarvis import selector
from jarvis.broker import MockBroker
from jarvis.contracts import AssetClass, FeatureSnapshot, Mode
from jarvis.engine import TradingEngine
from jarvis.harness import BacktestSpec
from jarvis.risk import Governor, RiskPolicy
from jarvis.storage import LocalStorage
from jarvis.strategies import StrategyRegistry, library_specs

from synthetic import SYMBOLS, build_market
from test_strategies import _bars

UTC = timezone.utc


def planted(days=1100, seed=0):
    """Two strategies: A earns in up-volatile months (label 3) and loses in down-calm months (label 0); B the reverse.
    Regimes persist: the market label switches every six months."""
    rng = np.random.default_rng(seed)
    labels, history = {}, {"A": [], "B": []}
    d = date(2016, 1, 4)
    while len(history["A"]) < days:
        if d.weekday() < 5:
            label = 3 if ((d.year * 12 + d.month - 1) // 6) % 2 else 0
            labels[d] = label
            sign = 1 if label == 3 else -1
            history["A"].append((d, sign * 0.002 + rng.normal(0, 0.004)))
            history["B"].append((d, -sign * 0.002 + rng.normal(0, 0.004)))
        d += timedelta(days=1)
    return history, labels


def moment(y, m):
    return selector.month_starts(datetime(y, m, 1, tzinfo=UTC), datetime(y, m, 2, 12, tzinfo=UTC))[0]


def test_allocations_never_see_later_history():
    history, labels = planted()
    moments = selector.month_starts(datetime(2017, 1, 1, tzinfo=UTC), datetime(2019, 6, 1, tzinfo=UTC))
    clean = {k: selector.build_allocation(k, ["A", "B"], history, labels, moments).records() for k in selector.ALLOCATORS}
    cut = date(2018, 3, 1)
    poisoned = {s: [(d, r if d < cut else 5.0 * (-1) ** i) for i, (d, r) in enumerate(rows)] for s, rows in history.items()}
    flipped = {d: (3 - v if d >= cut else v) for d, v in labels.items()}
    dirty = {k: selector.build_allocation(k, ["A", "B"], poisoned, flipped, moments).records() for k in selector.ALLOCATORS}
    for k in selector.ALLOCATORS:
        before = [r for r in clean[k] if r["from"] <= "2018-03-01T05:00:00Z"]   # includes the cut-off month
        assert before and before == dirty[k][:len(before)], k


def test_regime_lookup_and_bandit_learn_a_planted_regime_effect():
    history, labels = planted()
    for y, m, winner in ((2019, 3, "B"), (2019, 9, "A")):  # mid-block months: Jan-Jun 2019 label 0, Jul-Dec label 3
        when = moment(y, m)
        loser = {"A": "B", "B": "A"}[winner]
        alloc = selector.build_allocation("regime_lookup", ["A", "B"], history, labels, [when])(when)
        assert alloc[winner] == 2.0 and alloc[loser] == 0.0
        weights = selector.build_allocation("bandit", ["A", "B"], history, labels, [when])(when)
        assert weights[winner] > 1.4                                         # most posterior draws pick it


def test_selectors_stay_near_equal_weight_without_structure():
    rng = np.random.default_rng(3)
    history, labels = planted()
    noise = {s: [(d, rng.normal(0, 0.004)) for d, _ in rows] for s, rows in history.items()}
    when = moment(2019, 3)
    weights = selector.build_allocation("bandit", ["A", "B"], noise, labels, [when])(when)
    assert max(weights.values()) < 1.8                                       # no confident bet on noise
    early = selector.build_allocation("regime_lookup", ["A", "B"], history, labels, [moment(2016, 6)])(moment(2016, 6))
    assert early == {"A": 1.0, "B": 1.0}                                     # under a year of history: equal weight


def snap(**values):
    now = datetime(2024, 3, 6, 15, tzinfo=UTC)
    return FeatureSnapshot("s", "AAA", AssetClass.EQUITY, now, now, now + timedelta(days=1), (), values)


def trades_with_signal(n=200, seed=4):
    rng = np.random.default_rng(seed)
    rows, start = [], datetime(2018, 1, 1, tzinfo=UTC)
    for i in range(n):
        features = {f: float(rng.normal()) for f in selector.META_FEATURES}
        exit_at = start + timedelta(days=4 * i)
        rows.append({"strategy_id": "s", "features": features, "exit_decided_at": exit_at.isoformat(),
                     "net_return": 0.01 if features["ret_20"] + 0.3 * rng.normal() > 0 else -0.01})
    return rows


def test_meta_label_filter_learns_from_past_trades_only():
    trades = trades_with_signal()
    meta = selector.MetaLabelFilter(trades, [2019, 2020])
    good = {f: 0.0 for f in selector.META_FEATURES} | {"ret_20": 1.5}
    bad = good | {"ret_20": -1.5}
    when = datetime(2020, 6, 1, tzinfo=UTC)
    assert meta("s", snap(**good), when) and not meta("s", snap(**bad), when)
    cutoff = datetime(2020, 1, 1, 5, tzinfo=UTC) - selector.META_PURGE
    learnable = sum(datetime.fromisoformat(t["exit_decided_at"]) < cutoff for t in trades)
    assert meta.training_sizes["s"][2020] == learnable                        # later exits are not used
    assert meta("other", snap(**bad), when)                                   # no model: not filtered
    assert meta("s", snap(ret_20=-2.0), when)                                 # missing features: not filtered


def test_engine_applies_multipliers_and_the_filter_to_new_entries(tmp_path):
    specs = [s.__class__(**{**s.__dict__, "approval": "MOCK"}) for s in library_specs() if s.strategy_id == "meanrev-rsi2"]
    policy = RiskPolicy("t", ("AAA",), ("meanrev-rsi2",), 5000, 5000, 5000, 1000, 0.5, 100, 10**6,
                        owner_approved=True, crypto_enabled=True)
    bars = _bars([100 + i * 0.2 for i in range(230)] + [139.0, 136.0])
    for multiplier, filtered, expected in ((0.5, False, 5), (0.0, False, 0), (1.0, True, 0), (5.0, False, 36)):
        with LocalStorage(tmp_path / f"desk{multiplier}{filtered}") as store:
            broker = MockBroker(cash=10_000)
            engine = TradingEngine(store, broker, Governor(policy), StrategyRegistry(specs), Mode.SHADOW)
            engine.allocation = lambda now, m=multiplier: {"meanrev-rsi2": m}
            engine.entry_filter = (lambda s, snapshot, now: False) if filtered else None
            engine.reconcile()
            engine.process(bars, as_of=bars[-1].available_at, quantity=10, feature_horizon=timedelta(days=4))
            assert broker.state().positions.get("AAA", 0) == expected        # 5x capped at $5,000 / $136 = 36 shares
            reasons = [r for row in store.read_events() for r in row["event"]["reason_codes"]]
            assert ("META_FILTER" in reasons) == filtered and ("ALLOCATION_ZERO" in reasons) == (multiplier == 0.0)


LIB = ("breakout-volume@1.0.0", "meanrev-rsi2@1.0.0", "random-entry@1.0.0")
UNIVERSE = SYMBOLS + ("EEE", "FFF")


@pytest.fixture(scope="module")
def market(tmp_path_factory):
    home = tmp_path_factory.mktemp("sel") / "data"
    with LocalStorage(home) as store:
        build_market(store, start=datetime(2015, 1, 1, tzinfo=UTC), end=datetime(2018, 1, 1, tzinfo=UTC), symbols=UNIVERSE)
    return home


def test_selector_study_on_noise_keeps_equal_weight_and_enforces_the_holdout_order(market):
    base = BacktestSpec(LIB, tuple((s, AssetClass.EQUITY) for s in UNIVERSE), "1Day-adjusted", "1Day",
                        datetime(2016, 3, 1, tzinfo=UTC), datetime(2017, 12, 29, tzinfo=UTC))
    with pytest.raises(PermissionError, match="development"):
        selector.run_selector_study(market, base, split="HOLDOUT")
    record = selector.run_selector_study(market, base)
    result = record["result"]
    assert record["status"] == "COMPLETED" and [s["stage"] for s in result["stages"]] == list(selector.STAGES)
    assert result["selected"] == "equal_weight"                               # a random walk offers nothing to select
    assert all(not s["gate"]["passed"] for s in result["stages"])
    assert all(v["days"] > 400 for v in result["sleeves"].values())
    assert result["allocations"]["regime_lookup"] and result["meta_label"]["training_trades"]


def curve(returns, start=date(2016, 1, 4)):
    value, out, d = 10_000.0, [], start
    out.append((d - timedelta(days=1), value))
    for r in returns:
        value *= 1 + r
        out.append((d, value))
        d += timedelta(days=1)
    return out


def result(returns):
    from jarvis.metrics import summarize
    series = curve(returns)
    return {"series": series, "metrics": summarize(series), "stopped": None}


def test_stage_gate_needs_significance_a_smaller_drawdown_and_robustness_to_costs():
    rng = np.random.default_rng(8)
    base = rng.normal(0.0003, 0.01, 1500)
    better = base * 0.8 + 0.0006                       # higher return, lower volatility: real improvement
    noise = base + rng.normal(0, 0.002, 1500)
    crash = better.copy()
    crash[700:720] = -0.03                             # better on average but a much deeper drawdown
    t = selector.ALPHA / 3
    assert selector.stage_gate(result(better), result(base), result(better), result(base), t)["passed"]
    gate = selector.stage_gate(result(noise), result(base), result(noise), result(base), t)
    assert not gate["passed"] and "NOT_SIGNIFICANT" in gate["reasons"]
    assert "DRAWDOWN_NOT_SMALLER" in selector.stage_gate(result(crash), result(base), result(crash), result(base), t)["reasons"]
    costly = selector.stage_gate(result(better), result(base), result(better - 0.002), result(base), t)
    assert costly["reasons"] == ["FAILS_DOUBLE_COSTS"]


def test_trade_records_charge_only_fees_on_top_of_fill_prices():
    from jarvis.harness import trade_records
    from jarvis.replay import CostModel
    events = [{"event_type": "ORDER_INTENT", "payload": {"client_order_id": "e1", "asset_class": "CRYPTO",
                                                         "decided_at": "2020-01-01T00:00:00Z", "snapshot_id": "s1"}},
              {"event_type": "FEATURE_SNAPSHOT", "payload": {"snapshot_id": "s1", "values": {"ret_20": 0.1}}},
              {"event_type": "TRADE_OUTCOME", "asset_id": "BTC/USD",
               "payload": {"entry_client_order_id": "e1", "entry_price_estimate": 100.0, "exit_price": 101.0,
                           "strategy_id": "x", "exit_decided_at": "2020-01-05T00:00:00Z"}}]
    row = trade_records(events, CostModel())[0]
    assert row["net_return"] == pytest.approx(0.01 - 2 * 0.0025)            # fill prices already hold the spread
    assert row["features"] == {"ret_20": 0.1} and row["exit_decided_at"].startswith("2020-01-05")


def fake_run(store, spec, allocation=None, entry_filter=None):
    """Stands in for a replay: a strategy's sleeve earns a fixed drift; an allocated blend earns more."""
    days = [spec.start.date() + timedelta(days=i) for i in range((spec.end - spec.start).days)]
    rng = np.random.default_rng(len(spec.strategy_versions))
    drift = 0.0008 if allocation is not None else 0.0002
    returns = rng.normal(drift, 0.005, len(days))
    series = [(d, 10_000 * float(np.prod(1 + returns[:i + 1]))) for i, d in enumerate(days)]
    from jarvis.metrics import summarize
    return {"series": series, "trade_records": [], "stopped": None, "metrics": summarize(series), "fills": 10,
            "trades": {"trades": 5}}


def test_holdout_only_confirms_the_development_choice(tmp_path):
    base = BacktestSpec(("a@1", "b@1"), (("AAA", AssetClass.EQUITY),), "1Day-adjusted", "1Day",
                        datetime(2016, 3, 1, tzinfo=UTC), datetime(2025, 6, 30, tzinfo=UTC))
    with LocalStorage(tmp_path / "data") as store:
        with pytest.raises(ValueError, match="confirm"):
            selector.run_selection(store, base, split="HOLDOUT", run=fake_run)
        result = selector.run_selection(store, base, split="HOLDOUT", run=fake_run, confirm="regime_lookup")
    assert [s["stage"] for s in result["stages"]] == ["holdout_confirmation"]
    assert result["stages"][0]["gate"]["p_threshold"] == selector.ALPHA          # one test, no Bonferroni split
    assert result["development_selected"] == "regime_lookup" and result["window"][0].startswith("2024-01-01T05")


def test_an_interrupted_holdout_cannot_be_run_again(market, monkeypatch):
    base = BacktestSpec(LIB, tuple((s, AssetClass.EQUITY) for s in UNIVERSE), "1Day-adjusted", "1Day",
                        datetime(2016, 3, 1, tzinfo=UTC), datetime(2017, 12, 29, tzinfo=UTC))
    if not any(r["spec"]["split"] == "DEVELOPMENT" for r in selector_registry(market)):
        selector.run_selector_study(market, base)

    def killed(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(selector, "run_selection", killed)
    with pytest.raises(KeyboardInterrupt):
        selector.run_selector_study(market, base, split="HOLDOUT")
    with pytest.raises(PermissionError, match="once"):
        selector.run_selector_study(market, base, split="HOLDOUT")


def selector_registry(home):
    import json
    path = home / "research" / "selector_studies.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

"""Short-horizon lane: exact bookkeeping, no look-ahead, survivorship handling. Synthetic data only."""

from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

from jarvis.shortterm import data as D
from jarvis.shortterm import reversal as R
from jarvis.shortterm.reversal_study import select


def market(prices: np.ndarray, symbols=None, failed=None) -> R.Market:
    t, n = prices.shape
    days = [date(2020, 1, 1) + timedelta(days=i) for i in range(t)]
    symbols = symbols or [f"S{j}" for j in range(n)]
    last = np.array([np.max(np.where(np.isfinite(prices[:, j]))[0]) for j in range(n)])
    return R.Market(days, symbols, prices.copy(), prices.copy(), prices.copy(), last, failed or {})


def test_growth_is_compounded_exactly_across_sub_accounts():
    g = 0.001
    prices = 100 * (1 + g) ** np.arange(60)[:, None] * np.ones((1, 3))
    m = market(prices)
    baskets = {t: [0, 1, 2] for t in range(5, 40)}
    run = R.simulate(m, baskets, np.zeros(3), np.zeros(60))
    r = run["returns"]
    assert np.allclose(r[4:-4], g)                              # fully invested, no costs: the stocks' own growth
    assert np.allclose(r[:4], g * np.arange(1, 5) / 5, rtol=1e-3)  # the five sub-accounts start one day apart
    flat = R.simulate(market(np.full((60, 3), 50.0)), baskets, np.full(3, 0.001), np.zeros(60))
    per_trade = {round(x["net"], 10) for x in flat["trades"]}
    assert per_trade == {round(0.999 * 0.999 - 1, 10)}          # one entry and one exit cost per trade


def test_a_known_failure_is_worth_zero_and_an_acquisition_its_last_close():
    prices = np.full((30, 2), 20.0)
    prices[12:, :] = np.nan                                     # both stop trading after row 11
    m = market(prices, failed={0: 11})                          # stock 0 failed; stock 1 was acquired
    path0, ended0 = R.trade_path(m, 0, 8, 0.0)
    path1, ended1 = R.trade_path(m, 1, 8, 0.0)
    assert ended0 and ended1 and path0[-1] == 0.0 and path1[-1] == pytest.approx(1.0)


def test_cash_baskets_earn_tbills_and_returns_are_dated_after_the_open():
    m = market(np.full((40, 1), 10.0))
    run = R.simulate(m, {t: [] for t in range(5, 20)}, np.zeros(1), np.full(40, 0.0252))
    assert np.all(run["returns"] >= 0) and run["returns"].max() == pytest.approx(0.0001)
    assert run["dates"][0] == m.dates[7]


def test_selection_ignores_the_future():
    rng = np.random.default_rng(3)
    prices = 50 * np.exp(np.cumsum(rng.normal(0, 0.02, (80, 30)), axis=0))
    m = market(prices)
    universe = {f"{d.year:04d}-{d.month:02d}": m.symbols for d in m.dates}
    f = {"vix_high": np.ones(80, dtype=bool), "spy_up": np.ones(80, dtype=bool)}
    rows = list(range(10, 60))
    before = select(m, universe, "R1", rows, f)
    changed = prices.copy()
    changed[61:] *= 3.0                                         # rewrite everything after the last decision + 1
    after = select(market(changed), universe, "R1", rows, f)
    assert before == after and all(len(v) == R.TOP for v in before.values())


def test_universe_for_a_month_uses_only_the_previous_month():
    ts = lambda y, m: datetime(y, m, 1, 5, tzinfo=timezone.utc)
    monthly = pd.DataFrame([
        {"symbol": "A", "timestamp": ts(2020, 1), "close": 10, "volume": 100, "vwap": 10},
        {"symbol": "B", "timestamp": ts(2020, 1), "close": 10, "volume": 50, "vwap": 10},
        {"symbol": "B", "timestamp": ts(2020, 2), "close": 10, "volume": 999, "vwap": 10},
        {"symbol": "A", "timestamp": ts(2020, 2), "close": 3, "volume": 100, "vwap": 3},
    ])
    u = D.monthly_universe(monthly, n=1)
    assert u["2020-02"] == ["A"]                                # January's leader, not February's
    assert D.TICKER.match("AAPL") and not D.TICKER.match("0029900E0")
    assert D.looks_like_fund("SPDR S&P 500 ETF Trust") and not D.looks_like_fund("Apple Inc. Common Stock")


def test_event_slots_hold_one_trade_each_and_fade_exit_sells_early():
    from jarvis.shortterm import events as E
    prices = np.full((80, 3), 100.0)
    m = market(prices)
    m.volume = np.ones((80, 3))
    rule = {"hold": 10}
    signals = {t: [0, 1, 2] for t in range(25, 40)}
    run = E.simulate(m, signals, np.zeros(3), np.zeros(80), rule, slots=2)
    assert len(run["trades"]) >= 2 and run["average_slots_used"] <= 2      # never more trades open than slots
    assert np.allclose(run["returns"], 0.0)                                 # flat prices, no costs, no cash rate
    falling = prices.copy()
    falling[31:, 0] = 90.0                                                  # closes below the entry-day open
    path, _, kept = E.trade_path(market(falling), 0, 29, 0.0, 10, fade_level=100.0)
    assert kept == 2 and path[-1] == pytest.approx(0.9)                     # sold at the next open, then flat


def test_event_rule_needs_a_jump_beating_spy_on_heavy_volume():
    from jarvis.shortterm import events as E
    prices = np.full((40, 2), 50.0)
    prices[30:, 0] = 53.0                                                   # +6% on day 30
    prices[30:, 1] = 53.0
    m = market(prices)
    m.volume = np.ones((40, 2))
    m.volume[30, 0] = 5.0                                                   # only stock 0 trades heavy volume
    universe = {f"{d.year:04d}-{d.month:02d}": m.symbols for d in m.dates}
    spy = np.full(40, 400.0)
    hits = E.events(m, universe, [30], spy, np.ones(40, dtype=bool), E.VARIANTS["E1"], E.volume_ratio(m.volume))
    assert hits[30] == [0]


def test_intraday_signal_uses_the_morning_and_trades_only_the_last_half_hour():
    from jarvis.shortterm import intraday as I
    rows = []
    for k, day in enumerate([date(2020, 3, 2), date(2020, 3, 3), date(2020, 3, 4)]):
        for slot, (o, c) in {"09:30": (100, 101 if k != 2 else 99), "15:00": (101, 101), "15:30": (101, 102)}.items():
            ts = pd.Timestamp(f"{day} {slot}", tz="America/New_York").tz_convert("UTC")
            rows.append({"symbol": "SPY", "timestamp": ts, "open": o, "high": c, "low": o, "close": c, "volume": 1})
    table = I.daily_table(pd.DataFrame(rows))
    days = sorted(table["day"].unique())
    traded, trades = I.strategy_returns(table, "I1", {}, days)
    # day 2: previous 16:00 close 102 -> 10:00 close 101 is negative: no trade; day 3 likewise; day 1 has no
    # previous close. So nothing trades, whatever happens in the last half-hour.
    assert traded == {} and trades == []
    always, _ = I.strategy_returns(table, "I0", {}, days)
    assert always[days[1]] == pytest.approx(102 / 101 * (1 - I.COST_INDEX) ** 2 - 1)

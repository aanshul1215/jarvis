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

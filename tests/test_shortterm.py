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


def _frames(series: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(adjusted, raw) long bar tables from {symbol: (adjusted closes, raw closes, adjusted volumes, raw volumes)}."""
    tables = ([], [])
    for s, (ac, rc, av, rv) in series.items():
        for i in range(len(ac)):
            ts = datetime(2020, 3, 2, 5, tzinfo=timezone.utc) + timedelta(days=i)
            for rows, c, v in ((tables[0], ac[i], av[i]), (tables[1], rc[i], rv[i])):
                rows.append({"symbol": s, "timestamp": ts, "open": c, "high": c, "low": c, "close": c, "volume": v,
                             "vwap": c, "trades": 1})
    return pd.DataFrame(tables[0]), pd.DataFrame(tables[1])


def _corporate_actions() -> tuple[pd.DataFrame, pd.DataFrame]:
    v = [1000] * 4
    return _frames({
        # spin-off on day 2 (raw -13%) that the vendor adjusted as a 1:5 reverse split; a 1% dividend before day 1
        "SPIN": ([495.0, 505.0, 88.0, 89.0], [100.0, 101.0, 88.0, 89.0], [200, 200, 1000, 1000], v),
        "SPLT": ([50.0, 51.0, 51.0, 52.0], [100.0, 102.0, 51.0, 52.0], [2000, 2000, 1000, 1000], v),   # 2:1
        "BIG": ([10.0, 10.2, 10.3, 10.1], [200.0, 204.0, 10.3, 10.1], [20000, 20000, 1000, 1000], v),  # 20:1
        "JUMP": ([25.0, 25.0, 26.25, 26.0], [100.0, 100.0, 26.25, 26.0], [4000, 4000, 1000, 1000], v),  # 4:1, +5% day
    })


def test_adjustment_check_flags_unexplained_gaps_and_marks_the_vendor_made_ones():
    assert D.split_like([0.5, 1 / 3, 2.0, 0.257, 0.26, 10.4, 0.871]).tolist() == [True, True, True, True, False,
                                                                                   False, False]
    adjusted, raw = _corporate_actions()
    flags = D.adjustment_flags(adjusted, raw)
    assert sorted(flags["symbol"]) == ["BIG", "JUMP", "SPIN"]          # SPLT: the raw ratio is a 2:1 split
    assert set(flags.loc[flags["spurious"], "symbol"]) == {"SPIN"}     # BIG, JUMP: real splits, adjusted correctly
    spin = flags[flags["symbol"] == "SPIN"].iloc[0]
    assert spin["r_adj"] == pytest.approx(88 / 505 - 1) and spin["r_raw"] == pytest.approx(88 / 101 - 1)
    assert spin["price_step"] == pytest.approx(0.2) and spin["volume_step"] == pytest.approx(5.0)


def test_cleaning_undoes_only_the_vendor_made_jump_and_keeps_other_adjustments():
    adjusted, raw = _corporate_actions()
    cleaned, flags = D.clean_adjusted(adjusted, raw)
    spin, spin_raw = (t[t["symbol"] == "SPIN"].reset_index(drop=True) for t in (cleaned, raw))
    c, rc = spin["close"].to_numpy(), spin_raw["close"].to_numpy()
    assert c[2] / c[1] == pytest.approx(rc[2] / rc[1])                 # the day's adjusted return is the raw one
    assert c[1] / c[0] == pytest.approx(505 / 495)                     # earlier returns are unchanged
    assert c[0] / rc[0] == pytest.approx(0.99)                         # and the earlier dividend is still adjusted
    assert spin["volume"].tolist() == spin_raw["volume"].tolist()      # volumes line up with raw again
    others = cleaned["symbol"] != "SPIN"
    pd.testing.assert_frame_equal(cleaned[others], adjusted[others])   # real splits keep their adjustment
    assert not D.adjustment_flags(cleaned, raw)["spurious"].any()
    m = R.Market.from_frames(adjusted, raw)                            # research and the live desk load through here
    j = m.symbols.index("SPIN")
    assert m.close[2, j] / m.close[1, j] == pytest.approx(88 / 101) and m.adjustment_flags["spurious"].sum() == 1
    old = R.Market.from_frames(adjusted, raw, clean=False)
    assert old.close[2, j] / old.close[1, j] == pytest.approx(88 / 505) and old.adjustment_flags is None
    untouched, none = D.clean_adjusted(*_frames({"SPLT": ([50.0, 51.0], [100.0, 51.0], [2, 1], [1, 1])}))
    assert none.empty and len(untouched) == 2


def test_fetch_bars_asks_again_for_a_symbol_left_out_of_a_long_answer():
    from alpaca.data.timeframe import TimeFrame

    class Client:  # like the data API on 2026-10-22: DOW silently missing from a multi-symbol answer
        def __init__(self):
            self.calls = []

        def get_stock_bars(self, request):
            symbols = list(request.symbol_or_symbols)
            self.calls.append(symbols)
            bar = {"t": "2020-03-02T05:00:00Z", "o": 1.0, "h": 1.0, "l": 1.0, "c": 1.0, "v": 10}
            return {s: [bar] for s in symbols if s != "NONE" and not (s == "DOW" and len(symbols) > 2)}

    client = Client()
    start, end = datetime(2020, 3, 1, tzinfo=timezone.utc), datetime(2020, 3, 3, tzinfo=timezone.utc)
    bars = D.fetch_bars(client, ["AAA", "BBB", "DOW", "NONE"], TimeFrame.Day, start, end, pause=0.0)
    assert sorted(bars["symbol"]) == ["AAA", "BBB", "DOW"]
    assert client.calls == [["AAA", "BBB", "DOW", "NONE"], ["DOW", "NONE"]]   # one more request, for the empty ones


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


def _book_setup(t_total=420, n=45, seed=21):
    from jarvis.shortterm import book as B
    rng = np.random.default_rng(seed)
    prices = 50 * np.exp(np.cumsum(rng.normal(0.0004, 0.02, (t_total, n)), axis=0))
    days = [date(2016, 1, 4) + timedelta(days=i) for i in range(t_total)]
    syms = [f"S{j:02d}" for j in range(n)]
    last = np.full(n, t_total - 1)
    m = R.Market(days, syms, prices.copy(), prices.copy(), prices.copy(), last, {}, np.ones((t_total, n)))
    etf_names = B.DEFENSIVE + (B.SAFE, "SPY")
    etfs = {s: (100 * np.exp(np.cumsum(rng.normal(0.0002, 0.01, t_total))),) * 2 for s in etf_names}
    inst = B.combine(m, etfs)
    universe = {f"{d.year:04d}-{d.month:02d}": syms for d in days}
    groups = {s: ("A" if j < 25 else f"G{j}") for j, s in enumerate(syms)}
    return B, m, inst, universe, groups, etfs["SPY"][1]


def test_stock_book_caps_names_and_industries_and_never_borrows():
    B, m, inst, universe, groups, spy = _book_setup()
    rates = np.full(len(m.dates), 0.02)
    rows = list(range(300, 400))
    decided, report = B.targets(inst, m, universe, groups, spy, rates, rows, "A1")  # always in stocks
    for t, w in decided.items():
        assert len(w) <= B.MAX_NAMES and sum(w.values()) <= 1 + 1e-9
        assert sum(1 for j in w if groups[m.symbols[j]] == "A") <= B.GROUP_CAP
    run = B.simulate(inst, decided, np.full((len(m.dates), len(inst.symbols)), 0.0005), rates)
    assert len(run["returns"]) > 50 and np.all(np.isfinite(run["returns"]))


def test_stock_book_risk_off_holds_only_bonds_commodities_or_shy():
    B, m, inst, universe, groups, spy = _book_setup()
    falling_spy = np.linspace(400, 200, len(m.dates))               # 12-month return far below T-bills
    rates = np.full(len(m.dates), 0.02)
    decided, report = B.targets(inst, m, universe, groups, falling_spy, rates, list(range(300, 360)), "B1")
    allowed = {inst.symbols.index(s) for s in B.DEFENSIVE + (B.SAFE,)}
    assert report["risk_off_share"] == 1.0
    assert all(set(w) <= allowed and abs(sum(w.values()) - 1) < 1e-9 for w in decided.values())


def test_stock_book_ignores_the_future_and_values_a_failure_at_zero():
    B, m, inst, universe, groups, spy = _book_setup()
    rates = np.full(len(m.dates), 0.02)
    rows = list(range(300, 380))
    full, _ = B.targets(inst, m, universe, groups, spy, rates, rows, "B1")
    cut = 381
    m2 = R.Market(m.dates[:cut], m.symbols, m.open[:cut], m.close[:cut], m.raw_close[:cut],
                  np.minimum(m.last_row, cut - 1), {}, m.volume[:cut])
    inst2 = B.Instruments(inst.dates[:cut], inst.symbols, inst.is_stock, inst.open[:cut], inst.close[:cut],
                          np.minimum(inst.last_row, cut - 1), {})
    part, _ = B.targets(inst2, m2, universe, groups, spy[:cut], rates[:cut], rows, "B1")
    assert full == part
    j = next(iter(full[rows[0]]))
    dead = B.Instruments(inst.dates, inst.symbols, inst.is_stock, inst.open.copy(), inst.close.copy(),
                         inst.last_row.copy(), {j: rows[0] + 3})
    dead.open[rows[0] + 4:, j] = np.nan
    dead.last_row[j] = rows[0] + 3
    one = {t: {j: 1.0} for t in rows[:10]}
    run = B.simulate(dead, one, np.zeros((len(m.dates), len(inst.symbols))), np.zeros(len(m.dates)))
    assert run["data_ended_exits"] == 1 and np.prod(1 + run["returns"]) == pytest.approx(0.0, abs=1e-12)


def test_enhanced_index_is_fully_invested_capped_weekly_and_tilted():
    from jarvis.shortterm import enhanced as X
    B, m, inst, universe, groups, spy = _book_setup(t_total=460, n=60)
    rates = np.full(len(m.dates), 0.02)
    rows = list(range(300, 440))
    decided, report = X.targets(inst, m, universe, groups, spy, rates, rows, switch=False)
    trading = {t for t, w in decided.items() if w is not None}
    assert trading <= X.weekly_rows(m.dates, rows) | {t for t in rows if m.dates[t].month != m.dates[t - 1].month}
    col_group = {j: groups[s] for j, s in enumerate(m.symbols)}
    for t in trading:
        w = decided[t]
        assert abs(sum(w.values()) - 1) < 1e-6 and max(w.values()) <= X.STOCK_CAP + 1e-9
        assert sum(v for j, v in w.items() if col_group[j] == "A") <= X.GROUP_CAP + 1e-6
    flat, _ = X.targets(inst, m, universe, groups, spy, rates, rows, tilt=False, switch=False)
    t = min(trading)
    assert decided[t] != flat[t]                                            # the tilt changes the weights
    run = B.simulate(inst, decided, np.zeros((len(m.dates), len(inst.symbols))), rates, band=X.BAND, band_rel=X.BAND_REL)
    assert np.all(np.isfinite(run["returns"]))


def test_enhanced_v2_keeps_a_fifth_in_the_monthly_defensive_choice():
    from jarvis.shortterm import enhanced as X
    B, m, inst, universe, groups, spy = _book_setup(t_total=460, n=60)
    rates = np.full(len(m.dates), 0.02)
    rows = list(range(300, 440))
    decided, report = X.targets(inst, m, universe, groups, spy, rates, rows, sleeve=0.2)
    defensive = {inst.symbols.index(s) for s in B.DEFENSIVE + (B.SAFE,)}
    for t, w in decided.items():
        if w is None:
            continue
        assert abs(sum(w.values()) - 1) < 1e-6
        assert abs(sum(v for j, v in w.items() if j in defensive) - 0.2) < 1e-6
    assert report["sleeve_months"] and report["risk_off_share"] == 0

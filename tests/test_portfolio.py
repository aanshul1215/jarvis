"""Portfolio layer: nothing may depend on the future, the risk rules must hold, and the arithmetic must be right.
Synthetic prices only; not market evidence."""

from datetime import date, timedelta

import numpy as np
import pytest

from jarvis.contracts import AssetClass
from jarvis.portfolio import allocator, sleeves as sl
from jarvis.portfolio.backtest import apply_band, simulate, stats
from jarvis.portfolio.panel import Panel
from jarvis.portfolio.risk import vol_forecasts
from jarvis.portfolio.situation import FEATURES, standardise

NAMES = [a for group in ("equity_index", "sector", "single_stock", "bond", "commodity") for a in sl.GROUPS[group]]
CRYPTO = list(sl.GROUPS["crypto"])


def weekdays(n, start=date(2015, 1, 5)):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def synthetic_panel(n_days=700, seed=0):
    rng = np.random.default_rng(seed)
    assets = NAMES + CRYPTO
    n = len(assets)
    common = rng.normal(0.0003, 0.008, n_days)[:, None]
    drift = rng.normal(0.0002, 0.0004, n)
    vol = rng.uniform(0.006, 0.03, n)
    r = drift + 0.6 * common + rng.normal(0, 1, (n_days, n)) * vol
    close = 100 * np.exp(np.cumsum(r, axis=0))
    opens = close * np.exp(rng.normal(0, 0.002, close.shape))
    high, low = np.maximum(opens, close) * 1.005, np.minimum(opens, close) * 0.995
    volume = rng.lognormal(13, 0.4, close.shape)
    close[:300, assets.index("BTC/USD")] = np.nan  # crypto history starts later, as on Alpaca
    for arr in (opens, high, low, volume):
        arr[:300, assets.index("BTC/USD")] = np.nan
    classes = [AssetClass.CRYPTO if a in CRYPTO else AssetClass.EQUITY for a in assets]
    return Panel(weekdays(n_days), assets, classes, opens, high, low, close, volume)


def context(panel):
    return sl.Context(panel, vol_forecasts(panel), panel.returns())


@pytest.fixture(scope="module")
def book():
    panel = synthetic_panel()
    ctx = context(panel)
    return panel, ctx, {name: fn(ctx) for name, fn in sl.SLEEVES.items() if name not in ("news_sentiment", "earnings_drift", "theme_ai_power")}


def test_every_sleeve_ignores_the_future(book):
    panel, _, full = book
    cut = 520
    short = context(panel.until(cut))
    for name, weights in full.items():
        again = sl.SLEEVES[name](short)
        assert np.allclose(weights[:cut + 1], again, atol=1e-12), name


def test_sleeves_respect_shorting_and_size_rules(book):
    panel, ctx, full = book
    crypto = [panel.index(a) for a in CRYPTO]
    for name, w in full.items():
        assert np.all(w[:, crypto] >= 0), f"{name} shorts crypto"
        assert np.abs(w).sum(axis=1).max() <= sl.SLEEVE_GROSS + 1e-9, name
    assert (full["pairs"] < 0).any() and (full["pairs"] > 0).any()          # pairs really are long/short
    assert (full["trend_xasset"] < 0).any()                                    # trend can be short
    assert (full["low_volatility"] >= 0).all()                                 # long-only sleeves stay long


def test_risk_scaling_hits_the_sleeve_volatility_target(book):
    panel, ctx, full = book
    from jarvis.portfolio.risk import correlation, portfolio_vol
    t = 600
    w = full["trend_xasset"][t]
    live = np.where(w != 0)[0]
    vol = portfolio_vol(w[live], ctx.vols[t, live], correlation(ctx.returns, t, live)) * np.sqrt(252)
    assert vol == pytest.approx(sl.SLEEVE_VOL, rel=1e-6) or np.abs(w).sum() == pytest.approx(sl.SLEEVE_GROSS)


def test_volatility_and_features_ignore_the_future():
    panel = synthetic_panel(400, seed=3)
    full = vol_forecasts(panel)
    part = vol_forecasts(panel.until(300))
    assert np.allclose(full[:301], part, equal_nan=True)
    x = np.random.default_rng(1).normal(size=(400, len(FEATURES)))
    z_full, z_part = standardise(x, minimum=50), standardise(x[:250], minimum=50)
    assert np.allclose(z_full[:250], z_part)


def test_blends_use_only_completed_sleeve_returns():
    rng = np.random.default_rng(4)
    dates = weekdays(900)
    r = rng.normal(0.0003, 0.01, (900, 4))
    x = rng.normal(size=(900, len(FEATURES)))
    labels = [("bull_calm", "bear")[i // 90 % 2] for i in range(900)]
    m = allocator.month_starts(dates)
    m = [i for i in m if i >= allocator.MIN_TRAIN_ROWS][2]
    for method in allocator.METHODS:
        clean = allocator.blend_schedule(method, r, x, labels, dates)
        dirty_r = r.copy()
        dirty_r[m:] = rng.normal(0.05, 0.2, dirty_r[m:].shape)                # row m's return is not known at m
        dirty = allocator.blend_schedule(method, dirty_r, x, labels, dates)
        assert np.allclose(clean[:m + 1], dirty[:m + 1]), method
        assert np.all(clean >= 0) and np.all(clean.sum(axis=1) <= 1 + 1e-9)


def test_overlay_caps_and_drawdown_control():
    panel = synthetic_panel(400, seed=5)
    vols, rets = vol_forecasts(panel), panel.returns()
    n = panel.shape[1]
    mix = np.full(n, 0.5)
    mix[[panel.index("TLT"), panel.index("IEF"), panel.index("GLD")]] = -2.0
    w = allocator.overlay(mix, 1.0, 350, panel, vols, rets, drawdown=0.0)
    assert np.abs(w).sum() <= allocator.GROSS_CAP + 1e-9
    assert np.abs(w).max() <= allocator.ASSET_CAP + 1e-9
    assert -w[w < 0].sum() <= allocator.SHORT_CAP + 1e-9
    crypto = [panel.index(a) for a in CRYPTO]
    assert w[crypto].clip(0).sum() <= allocator.CRYPTO_CAP + 1e-9
    half = allocator.overlay(mix, 1.0, 350, panel, vols, rets, drawdown=0.15)
    floor = allocator.overlay(mix, 1.0, 350, panel, vols, rets, drawdown=0.30)
    assert np.allclose(half, w * (1 - 0.5 * 0.75)) and np.allclose(floor, w * 0.25)


def test_simulation_arithmetic_and_band():
    panel = synthetic_panel(60, seed=6)
    w = np.zeros(panel.shape)
    spy = panel.index("SPY")
    w[:, spy] = 1.0
    sim = simulate(panel, w, start=0, band=0.0)
    expected0 = panel.open[2, spy] / panel.open[1, spy] - 1 - 0.0005                    # buy once: 5 bps
    assert sim["returns"][0] == pytest.approx(expected0)
    assert sim["returns"][1] == pytest.approx(panel.open[3, spy] / panel.open[2, spy] - 1, abs=2e-5)
    assert sim["dates"][0] == panel.dates[1]
    held = np.array([0.2, 0.3])
    assert np.allclose(apply_band(np.array([0.203, 0.0]), held, 0.005), [0.2, 0.0])     # small change skipped; exit kept
    s = stats(sim["dates"], sim["returns"])
    assert s["days"] == len(sim["returns"]) and s["max_drawdown"] <= 0


def test_portfolio_drawdown_control_ignores_the_next_open():
    panel = synthetic_panel(420, seed=8)
    ctx = context(panel)
    w = [sl.trend_xasset(ctx), sl.low_volatility(ctx)]
    blend = np.full((panel.shape[0], 2), 0.5)
    k = 380
    clean = allocator.run_portfolio(panel, w, blend, ctx.vols, ctx.returns, start=260, end=k + 1)
    bumped = panel.open.copy()
    bumped[k + 1] *= 0.5                                       # a crash in the open after decision k
    dirty_panel = Panel(panel.dates, panel.assets, panel.classes, bumped, panel.high, panel.low, panel.close, panel.volume)
    dirty = allocator.run_portfolio(dirty_panel, w, blend, ctx.vols, ctx.returns, start=260, end=k + 1)
    assert np.allclose(clean["targets"][panel.dates[k]], dirty["targets"][panel.dates[k]])


def test_pairs_do_not_reenter_after_a_stop():
    panel = synthetic_panel(400, seed=9)
    a, b = panel.index("GLD"), panel.index("SLV")
    close = panel.close.copy()
    rng = np.random.default_rng(2)
    base = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 400)))
    close[:, b] = base
    close[:, a] = base * np.exp(rng.normal(0, 0.004, 400))
    close[300:, a] *= np.linspace(1, 1.25, 100)                # a drifts away for good: stop, no re-entry
    p2 = Panel(panel.dates, panel.assets, panel.classes, close, close, close, close, panel.volume)
    ctx = context(p2)
    w = sl.pairs(ctx, pair_list=(("GLD", "SLV"),))
    in_trade = w[:, a] != 0
    entries = int(np.sum(in_trade[1:] & ~in_trade[:-1]))
    later = in_trade[340:]
    assert entries >= 1 and not later[-30:].any()              # the runaway divergence is not traded again


def test_learning_ranker_ignores_the_future():
    from jarvis.portfolio.ranker import ranker
    panel = synthetic_panel(700, seed=10)
    ctx = context(panel)
    sleeves_now = [sl.trend_xasset(ctx), sl.low_volatility(ctx)]
    situation = np.zeros((panel.shape[0], len(FEATURES)))
    full, report = ranker(ctx, sleeves_now, situation)
    assert report["refits"] >= 1 and np.abs(full[600:]).sum() > 0               # it trained and traded
    cut = 640
    short = context(panel.until(cut))
    part, _ = ranker(short, [sl.trend_xasset(short), sl.low_volatility(short)], situation[:cut + 1])
    assert np.allclose(full[:cut + 1], part, atol=1e-10)
    crypto = [panel.index(a) for a in CRYPTO]
    assert np.all(full[:, crypto] >= 0)


def test_weekly_rebalance_holds_between_rebuilds_and_margin_is_charged():
    from jarvis.portfolio.ranker import week_starts
    panel = synthetic_panel(420, seed=11)
    ctx = context(panel)
    w = [sl.trend_xasset(ctx)]
    blend = np.ones((panel.shape[0], 1))
    rows = set(week_starts(panel.dates))
    run = allocator.run_portfolio(panel, w, blend, ctx.vols, ctx.returns, start=260, end=400, rebalance_rows=rows)
    traded_days = [d for d, x in zip(run["dates"], run["turnover"]) if x > 1e-12]
    decision_days = {panel.dates[t + 1] for t in rows if 260 <= t < 400}
    assert set(traded_days) <= decision_days | {run["dates"][0]}
    lev = np.zeros(panel.shape)
    lev[:, :30] = 0.05                                              # 30 positions of 5%: 1.5x gross, within the caps
    flat = panel.open.copy()
    flat[:] = 100.0
    still = Panel(panel.dates, panel.assets, panel.classes, flat, flat, flat, flat, panel.volume)
    vols = np.full(panel.shape, 0.01)
    res = allocator.run_portfolio(still, [lev], np.ones((panel.shape[0], 1)), vols, np.zeros(panel.shape),
                                  start=260, end=280)
    daily_after_entry = res["returns"][3:]
    gross = res["gross"][3:]
    expected = -np.clip(gross - 1.0, 0, None) * allocator.MARGIN_RATE / 252
    assert np.allclose(daily_after_entry, expected, atol=1e-12) and gross.max() > 1.0

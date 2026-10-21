"""Round 5 core: trend-filtered momentum rotation, the design chosen on 1930-1985 history and confirmed on 1986-2015
(Kenneth French 49 industries; docs/09-portfolio/ROUND5_DESIGN.md), carried over to ETFs unchanged in spirit.

Once a month (the first session of each month, decided after its close, traded at the next open):
1. Trend filter: if SPY's 12-month total return beats the 12-month return of T-bills (from the 3-month T-bill rate
   known each day), the system is risk-on; otherwise risk-off.
2. Risk-on: hold the momentum ranker's names (ranker.py: ETFs plus point-in-time top-10 stocks; enter top 4, keep
   while top 9, at most 2 new a month, at most 2 big-tech names), each at 1/4 of capital; an empty slot is held in
   the risk-off asset.
3. Risk-off: everything in the risk-off asset (SHY, short-term Treasuries, the closest ETF to T-bills).
Positions drift between monthly rebalances. There is no leverage, no volatility targeting and no drawdown brake:
round 4's post-mortem and the independent audit found those three cost the most. The owner's 25% drawdown stop
stays in the live Governor.
"""

from __future__ import annotations

from datetime import date

import numpy as np

from .ranker import MAX_HELD, holdings, month_starts
from .sleeves import Context

TREND_LOOKBACK = 252
MARKET, RISK_OFF, BONDS = "SPY", "SHY", "IEF"


def known_rate(dates: list[date], tbill: dict[str, float]) -> np.ndarray:
    """Annual T-bill rate (decimal) known at each row: the latest observation dated before the row's date (FRED
    publishes a day's rate the next day); NaN before the first observation."""
    obs = sorted((date.fromisoformat(k), v) for k, v in tbill.items() if v is not None)
    out, k, last = np.full(len(dates), np.nan), 0, None
    for i, d in enumerate(dates):
        while k < len(obs) and obs[k][0] < d:
            last = obs[k][1]
            k += 1
        if last is not None:
            out[i] = last / 100
    return out


def tbill_growth(rates: np.ndarray, lookback: int = TREND_LOOKBACK) -> np.ndarray:
    """Growth of $1 in T-bills over the last ``lookback`` rows, accrued daily at the rate known each day."""
    daily = np.log1p(np.nan_to_num(rates) / 252)
    cum = np.concatenate([[0.0], np.cumsum(daily)])
    out = np.full(len(rates), np.nan)
    for t in range(lookback, len(rates)):
        if np.isfinite(rates[t - lookback + 1:t + 1]).all():
            out[t] = np.expm1(cum[t + 1] - cum[t - lookback + 1])
    return out


def trend_on(close: np.ndarray, col: int, rates: np.ndarray, lookback: int = TREND_LOOKBACK) -> np.ndarray:
    """(T,) True where the asset's lookback total return beats T-bills' (NaN history -> False)."""
    ret = np.full(len(close), np.nan)
    ret[lookback:] = close[lookback:, col] / close[:-lookback, col] - 1
    bills = tbill_growth(rates, lookback)
    return np.isfinite(ret) & np.isfinite(bills) & (ret > bills)


def core_weights(ctx: Context, rates: np.ndarray, *, held: np.ndarray | None = None,
                 bond_switch: bool = False, slots: int = MAX_HELD) -> tuple[np.ndarray, dict]:
    """Target weights (T, N), constant between month starts, and a report. ``held`` (T, N) bool overrides the
    ranker's holdings (for variants). With ``bond_switch`` the risk-off asset is IEF while IEF's own 12-month
    return beats T-bills, SHY otherwise (a reported variant, not the registered design)."""
    p = ctx.panel
    t_total, n = p.shape
    if held is None:
        held, _ = holdings(ctx)
    market, safe, bonds = p.index(MARKET), p.index(RISK_OFF), p.index(BONDS)
    on = trend_on(p.close, market, rates)
    bonds_on = trend_on(p.close, bonds, rates)
    decisions = set(month_starts(p.dates))
    out = np.zeros((t_total, n))
    current = np.zeros(n)
    report = {"decisions": 0, "risk_on_decisions": 0, "switches": 0}
    state = None
    for t in range(t_total):
        if t in decisions and t >= TREND_LOOKBACK:
            report["decisions"] += 1
            w = np.zeros(n)
            parking = bonds if bond_switch and bonds_on[t] else safe
            if on[t]:
                report["risk_on_decisions"] += 1
                names = np.where(held[t])[0]
                w[names] = 1.0 / slots
                w[parking] += 1.0 - w.sum()
            else:
                w[parking] = 1.0
            if state is not None and state != bool(on[t]):
                report["switches"] += 1
            state = bool(on[t])
            current = w
        out[t] = current
    check_unlevered(out)
    return out, report


def check_unlevered(weights: np.ndarray) -> None:
    """Round 5 guard (round 4's losses came from leverage): long only and never more than 100% invested."""
    if (weights < -1e-12).any() or (weights.sum(axis=1) > 1 + 1e-9).any():
        raise AssertionError("core weights must be long-only and sum to at most 1 (no leverage, no shorts)")


# Round 6 (v1.5.0): the sector form of the core, as the long-history study validated it (sectors, not single stocks).
SECTOR_ENTER, SECTOR_HOLD = 3, 6


def sector_weights(ctx: Context, rates: np.ndarray) -> tuple[np.ndarray, dict]:
    """The 12 sector ETFs (XLC included from round 6): hold the top 3 by composite momentum, keep while in the top 6,
    one third each, under the same 12-month trend filter and SHY risk-off asset as the core."""
    from .ranker import holdings
    from .sleeves import GROUPS

    held, report = holdings(ctx, universe=GROUPS["sector"], enter_top=SECTOR_ENTER, hold_top=SECTOR_HOLD,
                            max_held=SECTOR_ENTER)
    w, filt = core_weights(ctx, rates, held=held, slots=SECTOR_ENTER)
    return w, {**filt, "ranker": report}

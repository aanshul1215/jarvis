# Search for a Sharpe-2 engine (2026-10-22/23)

**Owner direction (2026-10-22):** at least +15% a month is non-negotiable, in any asset class. There is to be no new paper account until an approach credibly reaches it. The owner also wants something "close to what HFT firms use", and better stock selection rather than simply volatile stocks.

**What the target needs:** 15% a month is about +435% a year, a log growth of 1.68 a year.
- At full Kelly that needs an after-cost Sharpe of about **1.8**; at half Kelly, about **2.1**.
- It also needs leverage of 4–20×. Reg-T stock margin allows 2× overnight; Alpaca allows 4× intraday; micro futures allow about 17×; US retail FX allows up to 50:1.
- Everything tested before this had a Sharpe of about 1.

**HFT-inspired design principles tested:**
- market-neutral books;
- high breadth: many small bets a day;
- short holding periods;
- execution at the opening and closing auctions;
- a combined stock-picking model;
- capacity-limited niches that large funds can't use.

## Research brief (agent, sources in its report; key facts)

**Best documented results:**
- Renaissance Medallion: 66.1% a year gross and 39.2% net, 1988–2018.
- No audited precedent exists for +15% a month.

**Retail base rates:**
- Taiwan day traders: under 1% predictably profitable (Barber, Lee, Liu & Odean).
- Brazil: 97% of day traders who persisted beyond 300 days lost money (Chague et al.).
- Quantopian: across 888 algorithms, backtest Sharpe explained less than 2.5% of out-of-sample performance.

**Net Sharpe above 2 in recent literature:** found only in two places.
- **LLM news sentiment:** about 3 in 2021–23, decaying to about 1.2 by early 2024.
- **Offshore crypto perpetual carry:** not available to a US resident.

**Everything else, after costs:** a Sharpe of about 1–1.8. Anomalies decay by about 58% after publication (McLean & Pontiff).

**Access:**
- **PDT rule:** FINRA retired it (SEC approval 2026-04-14; effective 2026-06-04). Alpaca now gives 4× intraday buying power from $2,000 of equity.
- **Alpaca:** no futures or FX. Its crypto is not offered in Texas. It supports opening- and closing-auction orders (cutoffs 09:28 and 15:50 ET), and easy-to-borrow shorts with no borrow fee.
- **Futures** via IBKR, Tradovate/NinjaTrader or tastytrade; **FX** via OANDA or IBKR.

## Study A: edge map of 11 market-neutral, short-horizon signals (`JARVIS_TEMP/edge/`)

**Design** (pre-registered; development 2016-02 to 2021-12 only, filtered at load, with 2022 onwards never in memory):
- **Universe:** the point-in-time top 300.
- **Book:** long the top decile, short the bottom decile.
- **Costs:** auction costs of 1.5–3 bp per side, plus 0.5%/yr borrow.
- **Timing brackets:** optimistic (same close) and conservative (next close).
- **Signals (S1–S11):** 1-day, residual and 5-day residual reversal; overnight persistence; intraday persistence; tug-of-war; opening-gap reversal; intraday periodicity (Heston-Korajczyk-Sadka); volume shock; a composite; and a walk-forward gradient-boosted model.

**Result: no signal advances.**
- All 11 have a negative Sharpe at base cost under both timings.
- The best before costs is S6, tug-of-war, at 1.01 (deflated 0.74).
- The edge per dollar traded is 0–1.8 bp, below even auction costs.
- Even with free trading, nothing approaches a Sharpe of 2.
- The confirmation and holdout periods stay unseen for these signals.

## Study B: SPY/QQQ intraday momentum (Zarattini, Aziz & Barbon 2024; `JARVIS_TEMP/zim/`)

**Rules:**
- **Noise band:** the band around the open (14-day average move by time of day), checked at HH:00 and HH:30.
- **Exits:** a trailing exit at the band or VWAP; flat at the close.
- **Sizing:** volatility-sized, capped at 4×.
- **Costs:** $0.0045 per share per side.

**Results** (CAGR / Sharpe above T-bills / max drawdown):

| Trial | Development 2016-02→2021 | Confirmation 2022–23 | Holdout 2024→2026-10 | Post-publication 2024-05→ | Decision |
|---|---|---|---|---|---|
| SPY | +12.5% / 0.81 / −28% | +30.9% / 1.75 / −11% | not run | not run | dropped (development < 1.0) |
| **QQQ** | +17.6% / 1.08 / −20% | +30.7% / 1.96 / −7% | **+21.0% / 1.06 / −15%** | +19.7% / 0.98 / −15% | **candidate component** |
| 50/50 | +15.3% / 1.05 / −22% | +31.0% / 2.02 / −7% | +12.6% / 0.62 / −14% | +10.1% / 0.46 / −14% | candidate (weak; flat in 2025–26) |

**About QQQ:**
- Correlation with SPY is −0.11 to +0.03, and with the desks −0.20 to +0.08.
- Costs barely matter.
- No month reached +15%; the best was +13.8%. Reaching +15% a month would need about 16×.
- The holdout's 2.8 years give a Sharpe standard error of about ±0.75.

**Caveats:**
- Before 2024, the periods overlap the paper's own sample, so they are a replication.
- Fills are at bar closes.
- Whole-share and fractional-short limits are not modelled.

## Study C: opening-range breakout on the 20 "Stocks in Play" (Zarattini, Barbon & Aziz 2024; `JARVIS_TEMP/orb/`)

**Rules:**
- **Universe:** the point-in-time top 1,500, with price ≥ $5, average volume ≥ 1M and ATR ≥ $0.50.
- **Selection:** the 20 highest relative-volume names in the first 5 minutes.
- **Entry:** a stop entry at the 5-minute range, in the direction of the first candle.
- **Exit:** a stop at 10% of ATR; the close (MOC) otherwise.
- **Sizing:** 1% risk per trade, capped at 4×.
- **Costs:** $0.0035 per share, plus 5 bp slippage on stop fills and 1 bp on MOC fills.
- **Same-minute rule:** if the entry and the stop fall in the same minute, the stop counts as hit.

**Result: NOT A CANDIDATE; the holdout was never computed.**

| Period | Costs | CAGR | Sharpe | Max DD |
|---|---|---|---|---|
| Development 2016-02→2021 | base | −80% | −7.91 | −100% |
| Confirmation 2022–23 | base | −81% | −7.39 | −96% |
| Development | zero | −48% | −3.22 | −98% |

**Why it fails:**
- 47% of trades reach their stop in the entry minute (the median stop is 0.32% of price, and entries cluster at 09:35).
- **Gentler fill rules (diagnostic only):**
  - letting the stop trigger only from the next minute gives Sharpe 2.32 / 1.58 on commissions alone, but −0.40 / −1.02 at base cost;
  - letting the entry minute stop out only if it closes beyond the stop gives 3.19 / 2.59 on commissions alone, but 0.46 / −0.06 at base cost.
- So the paper's ~2.8 is reproducible only with favourable stop fills and no slippage. The gross edge is about 8–13 bp per trade, and slippage of 1–6 bp per side erases it.

## Conclusion

- **Nothing found reaches a Sharpe of 2 after costs.**
- **The one new component that survived out of sample is QQQ intraday momentum** (Sharpe about 1, uncorrelated with the desks). It is a building block for a multi-strategy stack, not a 15%-a-month engine.
- **Data issues found on the way:**
  - Alpaca's multi-symbol endpoint silently drops some symbols.
  - Spin-offs are adjusted as if they were reverse splits.

  Both are fixed in `shortterm/data.py` (DATA_CLEANING.md).
- **On hold by owner decision (2026-10-22):**
  - the news-sentiment study (model approved and downloaded: `mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis`, Apache-2.0);
  - a retest on ranks 301–1,500;
  - the Kronos crypto challenger (D1-K);
  - the intraday execution engine.

## Data added (local, in `JARVIS_HOME/shortterm/`, each with a SHA-256 manifest; never in the repository)

- **`universe_top1500.json`:** point-in-time monthly top-1,500 lists, built with the same candidate rules as the top 300. 31 of 38,700 top-300 stock-month slots lack bars.
- **`daily_adjusted_ext.parquet`, `daily_raw_ext.parquet`:** daily bars for the 2,518 extra symbols. Also `monthly_bars_ext.parquet`.
- **`intraday30_ext/`:** 30-minute regular-session bars for the 790 symbols not in `intraday30` (2016–2026), about 23.4 million rows. Unlike the old `intraday30` filter, it drops after-hours bars on early-close days.
  - **Gaps:** 139 symbols have sessions with no 30-minute bars (12,196 sessions in total, about 0.6%). They are mostly thinly traded or renamed listings. Any study using this data should drop those symbol-days.
- **`orb/`:** opening 5-minute bars for the top-1,500 universe and 1-minute bars for each day's ORB selections. About 3,300 bars were recovered by single-symbol requests.

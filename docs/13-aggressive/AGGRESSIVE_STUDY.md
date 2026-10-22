# Aggressive engine study (Task 2). Registered 2026-10-22 before any combined result was computed

## Owner request

- Volatile stocks and crypto.
- At least +15% a month.
- Evaluation daily or weekly.
- "Changing limits".
- A smarter engine because the risk is higher.
- Integrate AI repositories such as Kronos.

## Evidence that shaped this design (`JARVIS_TEMP/vol2/`)

**Our data, 2017–2026:**
- **The most volatile 10% of the top 300 compounded −1.4% a year (max drawdown −85%).** Volatility drag turns a +9.5% arithmetic mean negative. The middle bucket compounded 12%; SPY 15%.
- **A prior month's return does not predict a +15% month.**
- **Volatile-stock momentum and vol-managed momentum made 10–12% a year** with drawdowns of −67% to −79%, and were far worse with leverage.
- **The BTC/ETH 50-day trend rule had Sharpe 1.23** (helped by 2017; about 0.97 since 2021). It cut drawdowns from −88% to −55%.
- **Sustaining +15% a month needs Sharpe of about 1.8 at full Kelly, or 2.1 at half Kelly.** No series reached that.

**Literature:**
- the low-volatility / IVOL / MAX anomalies;
- momentum crashes;
- vol-managed momentum (good for momentum; mixed elsewhere);
- crypto time-series momentum;
- fractional Kelly with shrunk means;
- stop-losses help only on microcaps;
- vol targeting helps equities.

**What the evidence supports:** about **25–40% a year with 25–40% drawdowns** from diversified trend and momentum sleeves with portfolio-level risk targeting. Not volatile stock picking. **15% a month is not a design target.**

## Components (all already built and tested)

**Equity core E:** 50% sector rotation (v1.5.0) and 50% stock book (enhanced-index-2.0.0).
- Daily return series 2017–2026, as reproduced in `JARVIS_TEMP/daily50/lev/series.parquet` (columns `sector`, `stock`, dates aligned).
- The two halves are rebalanced to 50/50 at each month start.

**Crypto trend sleeve C:**
- **Holdings:** BTC and ETH, 50/50.
- **Signals:** each coin's exposure is the **average of three signals**: close above its 50-day, 100-day and 200-day moving averages. It is therefore 0, ⅓, ⅔ or 1.
  - The 100- and 200-day averages are the red team's protection against the hand-picked 50-day average. Nothing here is fitted.
- **Timing:** signals use the coin's daily close (FRED Coinbase) on or before the previous US trading day; exposure applies from the next US session.
- **Returns:** coin returns between consecutive US trading days, so weekend moves arrive on Monday, as an ETF sees them.
- **Costs:** spot ETFs (IBIT/ETHA): 0.05% per side on exposure changes, a 0.25% yearly fee on exposure held. The uninvested share earns T-bills.
- **Proxy:** the coins stand in for the ETFs before 2024.

## Designs (4 trials plus 1 conditional AI challenger; all reported)

| id | Rule |
|---|---|
| **D0** | E alone (baseline: what is running now) |
| **D1** | 75% E + 25% C, rebalanced to target weights at each month start (5 bps on the traded amount) |
| **D2** | D1 scaled to a **25% annual volatility target**. Forecast: an EWMA (λ = 0.94) of D1's daily returns, using data to the previous day. Scale = min(1.5, 0.25 ÷ forecast), applied next day. Borrowing above 1.0× pays T-bill + 3.5%. Changes in scale cost 5 bps on the change. **No drawdown brake** (round 4 found brakes sold at the bottom). |
| **D3** | As D2 with a **35% target and a 2.0× cap** (the Reg-T maximum) |
| **D1-K** *(conditional)* | D1 with the crypto signal from **Kronos-small** instead of the trend average. Settings: weekly (first US session of each week); 10 paths, 5 days ahead, from the coin's last 256 daily bars; the coin is held for the week if the median path's 5-day return is positive. Code and weights as in `OPTIONS_STUDY.md`. Runs only **2024-07 → 2026-10** (after Kronos's pretraining), once the options Kronos job has freed the CPU. It is compared only with D1 over the same weeks. |

## Periods and pass rules

- **Periods:** development 2017–2021; confirmation 2022–2023; holdout 2024 to 2026-10.
- **Honest caveat:** the equity components and the crypto trend idea have all been looked at over these years before. What is new and untested is the **combination and the risk targeting**. This tests portfolio construction; it does not discover a new edge.
- **D1 passes** if, in **every** period, its Sharpe (above T-bills) is at least D0's and its worst drawdown is no worse than −35%.
- **D2 and D3 pass** if, in every period, their CAGR is above D1's and their worst drawdown is within −40% (D2) or −50% (D3).
- **The engine adopted** is the most aggressive design that passes. If none passes, D0 stays.
- **D1-K is adopted** only if its Sharpe is above D1's over 2024-07 → 2026-10. The power is low, so the result is descriptive.

## Reported for every design and period

- CAGR, volatility, Sharpe, max drawdown, worst day, week and month.
- Monthly and weekly return distributions, and the share of months at +15% or more and at −15% or less.
- Average exposure and leverage.
- **$ per trading day** on $10,000 and $20,000, both year-one and median.

## The risk engine and limits (design; implemented only for the adopted design)

**Limits change from the current 25% hard stop:**
- **Alerts:** at −15% and −25% drawdown, an alert, not a stop.
- **Hard stop:** **−40%** (D2) or **−50%** (D3), from the all-time peak. It halts new risk only.
- **Daily loss stop:** 3× the forecast daily volatility in dollars, instead of a fixed $300.
- **Other caps:**
  - crypto ETFs at most 35% of capital;
  - any single stock at most 5%;
  - total gross at most the design's cap.

**Monitoring (daily and weekly; judging the strategy only on a statistically meaningful horizon):**
- **Daily:** exposure against plan; slippage against the model; realised against target volatility.
- **Weekly:**
  - **CUSUM** of live-minus-expected return (about 1 false alarm per 7 years);
  - the live drawdown against the backtest's simulated 95th percentile;
  - hit rate against binomial bounds.
- **No retuning on weekly results.** Changes go through a new registered study.

## Result (run once 2026-10-22; `JARVIS_TEMP/aggr/`; deviations written before results)

CAGR / Sharpe above T-bills / max drawdown:

| Design | Dev 2017–21 | Conf 2022–23 | Holdout 2024–26/10 | Full 2017–26 |
|---|---|---|---|---|
| D0 (current desks) | 14.2% / 0.81 / −31.1% | 7.0% / 0.31 / −10.8% | 24.6% / 1.23 / −15.4% | 15.6% / 0.84 / −31.1% |
| D1 (+25% crypto trend) | 54.7% / 1.97 / −32.6% | 8.7% / 0.46 / −12.5% | 27.1% / 1.41 / −15.4% | 36.1% / 1.58 / −32.6% |
| D2 (25% vol target, ≤1.5×) | 57.1% / 1.99 / −28.6% | 9.5% / 0.39 / −19.2% | 33.2% / 1.28 / −23.2% | 39.2% / 1.51 / −28.6% |
| D3 (35% vol target, ≤2×) | 82.1% / 1.98 / −38.0% | 9.6% / 0.35 / −25.7% | 42.6% / 1.26 / −30.6% | 53.1% / 1.50 / −38.0% |

**Pass rules:** all four designs pass in every period, so **D3 is adopted by the registered rule.**

**Distributions:**
- Months at +15% or more (full period): D3 14.5%, D2 11.1%, D1 6.0%, D0 0.
- Months at −15% or worse: none.
- D3's median month is +2.0%.
- **D3 bootstrap (117 twelve-month windows):**
  - P(average ≥ +15%/month) = 1.7%: two windows, both starting in 2017.
  - P(daily-path drawdown ≤ −30%) = 19.7%.
  - Median 12-month return +39%; 5th percentile −13%.

**Caveats found by the study itself:**
- **2017 dominates development.** In 2017 alone D1 made +220% and D3 +445%. Over 2018–21: D0 12.5%, D1 28.7%, D3 38.1%.
- **Leverage lowered the Sharpe after 2021:** in confirmation D3 0.35 vs D1 0.46; in holdout 1.26 vs 1.41.
- **D3's confirmation edge over D1 is under 1 point of CAGR.** With one extra session of lag it falls to 7.92% vs 7.89%.
- **D3 sat at the 2× cap 93% of the time,** so it is effectively "D1 at about 2×".
- **The crypto timing may credit overnight coin moves** that a US-hours ETF trade would partly miss.

**Red-team review pending** before any implementation.

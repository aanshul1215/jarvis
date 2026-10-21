# Jarvis stock book (study 5). Registered 2026-10-21 before any result

**Owner direction (2026-10-21):** build and test the stock book; a stock-trading approach that also trades commodities and bonds, smarter than rounds 1–4.

**Why this design.**
- Studies 1 and 3 found real per-trade edges:
  - reversal: about +0.2% per trade;
  - event drift: +1.8% net per trade.
- As standalone strategies they lost to simply holding the liquid market. They were either too concentrated or mostly in cash.
- **So the book stays fully invested,** and the signals choose which stocks it holds.
- **Momentum** was validated on 89 years of industry data (French 49).
- **The 12-month trend switch** was validated on 1930–1985 history and confirmed on 1986–2015.

## Universe and data

- **Stocks:** each month's 300 most-traded US common stocks by the previous month's dollar volume, price at least $5. The candidate list is survivorship-aware, and known failures are valued at zero after their last listed day.
- **Prices:** daily adjusted Alpaca SIP bars.
- **Industry:** the SEC SIC code (first 2 digits). Stocks the SEC no longer lists form one "UNKNOWN" group.
- **Defensive instruments:** TLT, IEF, TIP, LQD (bonds), GLD, SLV, DBC, CPER, USO (commodities), and SHY (T-bill proxy). These come from the existing ETF store, adjusted.

## Daily stock score (after each close, using that day's data and earlier only)

1. **Event:** a high-volume jump (study 3's E1 rule) scores 1 on its day and fades linearly to 0 over 20 sessions. If there were several, the strongest remaining value counts.
   - The day's return is at least +4%;
   - it beats SPY's by at least 3%;
   - volume is at least 3× its 20-day average.
2. **Momentum:** the average of the cross-sectional percentile ranks of the 126-day return and the 12-1 month return.
3. **Bounce:** the percentile rank of minus the 5-day return.
4. **Composite** = (rank of event + momentum + 0.5 × bounce) ÷ 2.5.
   - The weights are fixed in advance; nothing is fitted. Bounce has half weight because its measured edge was small.
   - Ranks are taken within that day's universe, with ties averaged.

**News sentiment is not included.** Our FinBERT archive covers only the 39 symbols of the old universe, and including it would make the score uneven across stocks. It is a future addition once news is collected for the whole universe.

## Holdings

**Risk-on (stock mode):**
- **Hold up to 30 stocks**, equal target weight (1/30 each).
- **Each day:**
  - **sell** a holding if it ranks below 60th, leaves the month's universe, or has no price;
  - **buy** the highest-ranked stocks not held until 30 are held;
  - **industry cap:** at most 9 names (30%) from one SIC 2-digit group.
- **No-trade band:** a weight drifts unless it is more than max(1%, 20% of target) away from its target. Entries and full exits always trade.

**Market situation** (decided at each month start, as validated):
- **Risk-on** while SPY's 252-day total return beats T-bills' over the same period.
- **Risk-off:** stocks are sold. The money goes to the **top 3 defensive instruments**, ranked by the average rank of their 3-month, 6-month and 12-1 month returns. Each must have a 12-month return above T-bills to be held; any slot left unfilled goes to SHY.

**General:**
- No leverage, and no shorting. Cash earns T-bills.
- **Costs per side:**
  - stocks: 4 bps (top 100) or 8 bps (ranks 101–300);
  - ETFs: 5 bps (CPER 15).

**Crypto** is a separate lane, studied in study 2, and is not part of this test.

## Splits and decision rule

- **Splits:**
  - development: decisions 2017-01-03 to 2021-12-31 (momentum and the trend filter need 2016 as warm-up);
  - confirmation: 2022–2023;
  - holdout: 2024 onward.
  - None of the stock-level studies has looked at the later two periods.
- **Benchmark R0:** equal weight of the month's 300, rebalanced monthly. SPY and the round 6 sector rotation are also reported.
- **The book (B1) passes development if all three hold:**
  - its Sharpe above T-bills ≥ R0's + 0.20;
  - its worst drawdown is no worse than R0's;
  - at double costs, its Sharpe above T-bills ≥ R0's.
- **If it passes, it runs once on confirmation and once on holdout.** In each it must have a Sharpe above T-bills ≥ R0's and a worst drawdown within 25%.
- **Ablations, for information only** (development period only, never adopted from this run):
  - A1 without the market switch (always stocks);
  - A2 momentum only;
  - A3 event only;
  - A4 without bounce.

## Reported

- CAGR, Sharpe above T-bills, worst drawdown, volatility;
- turnover and cost drag;
- average names held, share of time risk-off;
- the largest industry share;
- exits caused by a stock's data ending.

# Jarvis enhanced-index stock book (study 6). Registered 2026-10-21 before any result

**Owner direction (2026-10-21):** build and test the enhanced-index stock book.

**Why this design** (from study 5's failure):
- the 30-stock book swung about 32% a year, because momentum and event picks are volatile names;
- it churned about 47× a year, driven by the daily bounce signal;
- the monthly market switch whipsawed in 2017–21.

The signals themselves are real (study 3: +1.8% net per event trade; momentum validated over 89 years). So this book owns the whole liquid market, sizes each stock by its risk, and only **tilts** the weights toward the signals.

## Rules

- **Universe:** each month's top 300 by the previous month's dollar volume, price at least $5. The same survivorship-aware data as studies 1, 3 and 5.
- **Decisions:** after the close of the first session of each week; trades at the next open. Positions drift between decisions. A stock leaving the universe is sold at the next weekly decision. A stock whose data ends exits at once (a known failure at zero).
- **Base weight:** 1 ÷ the stock's volatility (standard deviation of its last 63 daily returns, at least 40 of them).
- **Score:** (percentile rank of the event signal + momentum) ÷ 2, ranked within the universe.
  - **The event signal:** study 5's fading 20-session high-volume-jump signal.
  - **Momentum:** the average rank of the 126-day and 12-1 month returns.
  - **No bounce component.**
- **Tilt:** the target weight is proportional to base weight × (0.5 + score), so the strongest stock gets 1.5× and the weakest 0.5×. Weights are normalised to 100% (fully invested).
- **Caps:**
  - 3% per stock;
  - 25% per SEC SIC 2-digit industry (excess is spread over the other stocks in proportion).
- **No-trade band:** a weight is traded only if it is more than max(0.10% of capital, 25% of its target) away from the target. Entries and exits always trade.
- **Market switch:**
  - **When:** decided at each month start, and **only in a clear downtrend**: risk-off only if SPY's 12-month return is below T-bills' **and** SPY is below its 200-day average. This is the "F4" rule; in the long-history test it had the best 1986–2015 result of the six filters but was not selected there, so this is a new choice, stated as such.
  - **Risk-off:** the top 3 bonds and commodities by composite momentum with a 12-month return above T-bills (TLT, IEF, TIP, LQD, GLD, SLV, DBC, CPER, USO); any unfilled slot goes to SHY.
- **No leverage, no shorting.** Costs per side: stocks 4 / 8 bps by liquidity rank; ETFs 5 bps (CPER 15). Cash earns T-bills.

## Benchmarks

- **R0:** equal weight of the 300, monthly.
- **C0:** the same inverse-volatility 300 **without** the tilt and without the market switch, weekly with the same band. It isolates what the signals add.
- **SPY.**

## Splits and decision rule

- **Splits:** development 2017-01-03 to 2021-12-31; confirmation 2022–2023; holdout 2024 onward. The later two remain unseen by every stock-level study.
- **The bar for this design is lower than the +0.20 used for the standalone strategies** (stated before running): an enhanced index aims for a smaller, steadier improvement.
- **The book (X1) passes development if all three hold:**
  - its Sharpe above T-bills ≥ R0's + 0.10;
  - its CAGR > R0's;
  - at double costs, its Sharpe above T-bills ≥ R0's and its CAGR ≥ R0's.
- **If it passes, it runs once on confirmation and once on holdout,** with R0, C0 and SPY alongside. **In each it passes** if its Sharpe above T-bills ≥ R0's, its CAGR ≥ R0's, and its worst drawdown is within 25%.
- **Reported, not used to decide:** X1 against C0, which shows whether the tilt helps beyond risk weighting.

## Reported

- CAGR, Sharpe above T-bills, worst drawdown, volatility;
- turnover, number of names, largest industry share, risk-off share;
- exits caused by a stock's data ending.

**Practical note for live use:** 300 positions on $10,000 means positions of about $10–100, which needs fractional shares. Alpaca supports these for most US stocks. A live version may hold only the largest-weight names; that would be its own registered variant.

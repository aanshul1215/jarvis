# Round 6 (v1.5.0): sector rotation. Registered 2026-10-20 before its first run

**Owner request:** "if we fix this version and try to improve what does the numbers look like then in comparison to spy and other versions".

## What changed from round 5's sector variant, and why

1. **XLC added** (communication services: Alphabet, Meta, Netflix and others). The variant could not hold the sector that contains two of the largest US companies. History starts 2018-06-19, so XLC can be ranked from mid-2019, once it has 12 months of returns.
2. **Faster crash filters tested and rejected on independent history.**
   - Candidates (French 49 industries in the sector form; pre-registered at `longhist/pre_registration_filters.txt`; 6 trials):
     - the 10-month average;
     - both signals required, or either signal enough;
     - a 2-standard-deviation one-month crash brake;
     - 3/6/12-month votes.
   - **Selection, 1930–1985:** the 12-month filter had the highest Sharpe (0.65). None of the faster filters beat it, so it stays.
   - **Its confirmation, 1986–2015:** 12.1% a year, max drawdown −21.4%, against the market's 10.4% and −50.2%.
3. **Kept as validated:** the risk-off asset (SHY), monthly decisions, the 3/6/12-1 composite score, top 3 / keep while top 6, equal thirds, and no leverage. The bond-switch variant made no difference in round 5.

## Rules

Each month, at the first session, decided after its close and traded at the next open.

1. **Risk-on** when SPY's 252-day total return beats the T-bills' return over the same period (accrued daily at the rate known each day).
2. **Risk-on:**
   - **Choose from:** the 12 sector ETFs (XLF, XLK, XLE, XLV, XLY, XLP, XLI, XLU, XLB, SMH, VNQ, XLC).
   - **Rank by:** the average cross-sectional rank of the 3-month, 6-month and 12-1 month returns.
   - **Hold** the top 3 (a positive 12-1 return is required). Keep a holding while it is in the top 6; refill from the top.
   - **Size:** one third each. An unfilled slot is held in SHY.
3. **Risk-off:** 100% SHY.
4. **Positions drift between monthly decisions.** The no-trade band is unchanged (the larger of 1% of capital and 20% of the target). Costs: 5 bps per side.
5. **Guards from round 5 stay:** long only, total at most 100% (`check_unlevered`), no volatility targeting, no drawdown brake. The live Governor's 25% stop stays.

## Reported (run once, every period: 2017–2021, 2022–2023, 2024–2026, 2017–2026)

- **The round 6 sector rotation**, with normal and doubled costs.
- **Earlier versions:** round 5's sector variant without XLC, and the round 5 core.
- **Benchmarks:**
  - SPY, QQQ and 60/40;
  - **equal weight of all 29 ETFs (fair: no hand-picked stocks)**;
  - equal weight of all 39 (includes the 2026-chosen stocks: hindsight).
- **Metrics:** CAGR, Sharpe and Sharpe above T-bills, worst drawdown, turnover. Also the month-by-month holdings.
- **Deflated Sharpe:** counts every trial logged so far.

**Honesty:** these rules were fixed by 1927–2015 evidence plus one data fix (XLC). Every 2016–2026 period has been looked at before, so this is not a clean out-of-sample test. Live paper trading is the next honest one.

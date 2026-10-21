# Enhanced index v2: 80% stocks + a permanent 20% bonds/commodities sleeve (study 7). Registered 2026-10-21 before its run

**Owner decision (2026-10-21):** register "Stocks + permanent 20% sleeve" for the single test on the untouched 2022–2026 data.

**Disclosure.** Study 6's diagnostic, run after its result, showed that the stock part *without* the month-start switch earned 17.2% a year (Sharpe 0.94) in 2017–21. So this design's development period is not blind for its stock part. **The decisive test is confirmation (2022–2023) and holdout (2024+)**, which no stock-level study has looked at.

## Rules

- **80% stock part:** study 6's enhanced index, with the switch removed.
  - **Universe:** the point-in-time top 300 stocks.
  - **Weights:** 1 ÷ volatility (63 days), tilted by (0.5 + score). The score is the average rank of the event signal and of momentum.
  - **Caps:** 3% per stock and 25% per SIC 2-digit industry, within the stock part.
  - **Timing:** weekly decisions, with a no-trade band of max(0.10%, 25% of the target).
- **20% sleeve**, chosen at each month start:
  - **Choose from:** TLT, IEF, TIP, LQD, GLD, SLV, DBC, CPER, USO.
  - **Hold:** the top 3 by composite momentum (3-month, 6-month and 12-1 month ranks), each only while its 12-month return beats T-bills. Any unfilled slot goes to SHY.
  - **Size:** 6.67% of capital each.
  - **Between month starts:** the same sleeve holdings are kept, and the weekly decisions re-state them, so the band prevents churn.
- **Always both parts.** There is no all-or-nothing switch, no leverage and no shorting.
- **Costs** as before: stocks 4 / 8 bps, ETFs 5 bps (CPER 15). Cash earns T-bills.

## Benchmarks

- **R0:** the equal-weight 300, monthly.
- **C0:** the inverse-volatility 300, no tilt.
- **SPY.**

## Decision rule (stated before running)

**The purpose of the sleeve is lower risk, so the yearly return is reported against R0 and SPY but is not a pass condition.**

- **Development, 2017–2021.** It passes if:
  - its Sharpe above T-bills ≥ R0's + 0.10;
  - its worst drawdown is smaller than R0's;
  - at double costs, its Sharpe above T-bills ≥ R0's.
- **Confirmation (2022–2023) and holdout (2024+), each run once,** only if development passes. In each it passes if:
  - its Sharpe above T-bills ≥ R0's;
  - its worst drawdown is within 25% and no worse than R0's.

## Reported

For each period:
- CAGR, Sharpe above T-bills, worst drawdown, volatility, turnover;
- the sleeve's holdings by month;
- the same figures for R0, C0 and SPY.

## Result (run once, 2026-10-21; version enhanced-index-2.0.0): PASSED development, confirmation and holdout

CAGR / Sharpe above T-bills / worst drawdown / volatility:

| | 2017–2021 (development) | 2022–2023 (confirmation) | 2024–2026-10 (holdout) |
|---|---|---|---|
| **X2: 80% stocks + 20% sleeve** | **16.0% / 1.00 / −28.2% / 14.9%** | **1.8% / −0.03 / −18.1% / 16.2%** | **18.3% / 0.98 / −15.8% / 13.8%** |
| X2 at double costs | 15.7% / 0.98 | 1.5% / −0.05 | 18.0% / 0.96 |
| R0 equal-weight 300 | 15.8% / 0.77 / −35.9% | −2.5% / −0.13 / −31.4% | 16.8% / 0.68 / −22.8% |
| C0 inverse-vol 300 | 16.8% / 0.92 / −33.5% | 0.7% / −0.06 / −23.3% | 14.9% / 0.75 / −17.5% |
| SPY | 18.2% / 0.99 / −32.0% | 1.6% / −0.00 / −26.3% | 20.4% / 0.99 / −19.8% |

**Whole period, 2017-01 to 2026-10, compounded:**

| | Growth of $10,000 | Per year |
|---|---|---|
| X2 | about $34,700 | 13.5% |
| SPY | $39,800 | 15.2% |
| R0 | $30,500 | 12.1% |

- **Turnover:** about 3.5–3.8× a year. Doubled costs take about 0.3% a year.
- **Verdict:**
  - It passes every registered check.
  - It beat the equal-weight 300 in all three periods, on return and risk.
  - It roughly matched SPY's Sharpe in development and holdout, with a smaller worst drawdown every time (−28% / −18% / −16% against −32% / −26% / −20%).
  - It trailed SPY's raw return over the whole period by about 1.7 points a year.
- **Caveat:** development was not blind for the stock part (study 6 diagnostic). Confirmation and holdout were.

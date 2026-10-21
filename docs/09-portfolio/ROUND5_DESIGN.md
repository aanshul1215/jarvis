# Round 5 (v1.4.0): the trend-filtered momentum core. Registered 2026-10-20 before its first run

**Owner request (2026-10-20):** "go through everything we did until now, see what we can improve and get me some good numbers on the tests carried out on all time periods of data"; "we need to address this as well in the new design. we dont want to repeat mistakes."

## Evidence this design comes from (none of it tuned on 2016–2026)

**1. Return attribution of v1.3.0, 2024–2026, against the equal-weight universe.**
- Bonds were held at 49%, earning about 1.4% a year: −7.2% a year.
- Exposure timing (vol targeting and the drawdown brake): −6.9% a year.
- Margin interest: −3.75% a year.
- Every sleeve made money; the momentum ranker contributed the most in every period.

**2. Independent code audit.**
- **No look-ahead bugs.** But sleeves were scored without financing costs, and three sleeves borrowed to hold bonds:
  - `trend_xasset` (long 1.79);
  - `trend_sma200` (1.46);
  - `volatility_breakout` (1.11).
- **Vol targeting raised leverage into the April 2025 crash,** because the bond-heavy mix looked calm.
- **The drawdown brake cut gross from 1.9× to 0.4×** the day before the +9.5% rebound, and stayed at about half until June.
- **The equal-weight benchmark was understated:** sale proceeds were left idle as cash.

**3. Long-history design search** on French 49 industries plus FRED T-bill and 10-year yields; no 2016+ data.
- 30 candidates were written down before running.
- **Selected on 1930–1985:** D3, "top 8 of 49 industries by composite momentum (hold while in the top 16) while the market's 12-month return beats T-bills; otherwise T-bills".
- **Confirmed once on 1986–2015:** 13.0% a year, max drawdown −29%, against the market's 10.4% and −50%.
- Deflated against the luck allowance for 30 trials: probability 0.445, so the edge is not proven.

**4. Research review.**
- Published tactical systems have mostly trailed SPY since publication.
- Their reliable benefit is smaller drawdowns.
- Leverage through retail margin (Alpaca: 7.75%) rarely pays.

## Rules

Each month, at the first session, decided after its close and traded at the next open.

1. **Trend filter:**
   - SPY's 252-day total return against the 252-day return of T-bills, accrued daily at the 3-month rate known each day.
   - If SPY is higher, the system is **risk-on**.
2. **Risk-on:** hold the momentum ranker's names (`ranker.py`, unchanged from round 3), each at 25% of capital. Slots it doesn't fill are held in SHY.
   - **Eligible names:** the 17 equity ETFs, plus stocks that were US top-10 by value at the previous year-end.
   - **Score:** the average rank of 3-month, 6-month and 12-1 month returns.
   - **Entry and exit:** enter the top 4; keep while in the top 9. A positive 12-1 return is required.
   - **Limits:** at most 2 new names a month, and at most 2 big-tech names.
3. **Risk-off:** 100% SHY.
4. **Positions drift between monthly rebalances.** The no-trade band is unchanged (the larger of 1% of capital and 20% of the target).
5. **Costs** as before: 5 bps per side for stocks and ETFs.

**What it does not do:** there are no other sleeves in this core. The satellites can be considered later, on their own evidence.

## Mistakes that must not be repeated, and how each is prevented

| Mistake (rounds 2–4) | Guard in round 5 |
|---|---|
| Sleeves scored without paying for borrowed money; bond-heavy sleeves looked better than they were | The core never borrows. Every result also reports the Sharpe **above T-bills**, so cash-like holdings get no free credit |
| Leverage into bonds at 7.3% interest | No leverage. `core.check_unlevered` raises an error if any weight is negative or the total is above 100%. The test suite asserts it. The paper policy's holdings cap returns to $10,000 when the core trades |
| Vol targeting raised leverage before a crash | No volatility targeting. Weights are fixed (25% each) and change only at the monthly decision |
| Drawdown brake sold at the bottom and stayed small through the rebound | No drawdown brake. The only risk switch is the slow 12-month trend filter, checked monthly. The owner's 25% stop from the all-time peak stays in the live Governor (no new risk beyond it) |
| A benchmark that left cash idle | Benchmarks are fully invested and rebalanced monthly: SPY, QQQ, the equal-weight universe and 60/40 |
| Weekly churn | Monthly decisions; about 5 trades a year in the long-history test |

## Testing and reporting

- **Run once** over every period: 2017–2021, 2022–2023, 2024–2026, and 2017–2026 in full. Decisions start in 2017; 2016 is warm-up.
- **Report for the core, both costs and doubled costs:**
  - CAGR, volatility;
  - Sharpe, and Sharpe above T-bills;
  - worst drawdown, turnover.
- **Benchmarks:** SPY, QQQ, the equal-weight universe and 60/40.
- **The design traded is the registered core above.** Two variants are reported for transparency and are **not** used to choose:
  - (a) the ranker restricted to the 11 sector ETFs (top 3, hold while in the top 6), the long-history agent's mapping;
  - (b) risk-off in IEF while IEF's own 12-month return beats T-bills, otherwise SHY.
- **Honesty:**
  - Every 2016–2026 period has been looked at by earlier versions.
  - These rules were fixed by 1927–2015 evidence and the round 3 ranker, not by tuning on 2016–2026, but the 2016–2026 numbers are not a clean out-of-sample test.
  - The deflated Sharpe counts every development trial logged so far (at least 25).
  - Live paper trading is the next honest test.

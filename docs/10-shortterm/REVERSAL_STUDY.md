# Short-horizon lane, study 1: short-term reversal in liquid US stocks. Registered 2026-10-21 before any result

**Owner direction (2026-10-21):** build the branch-3 hours-to-days system for stocks and crypto; research first, and decide the capital split after results.

**Why this family first.** Prices of large stocks tend to bounce back partly after a sharp fall over a few days. Buying them supplies liquidity to forced or impatient sellers.
- **Evidence:** Jegadeesh 1990; Lehmann 1990; Nagel 2012, *Evaporating Liquidity* (all RECALLED).
- **Nagel's finding:** the profits are larger when market uncertainty (VIX) is high. That is a natural use of the situational-awareness inputs.
- **Known weakness:** the effect has shrunk among large stocks, and costs eat much of it.

## Data (`JARVIS_HOME/shortterm/`, SHA-256 manifests)

- **Universe for month M:** the 300 highest dollar-volume US common stocks of month M − 1 with a price of at least $5.
- **Candidates:**
  - every NYSE, NASDAQ or AMEX stock in Alpaca's active and inactive lists;
  - plus the named large failures 2016–2026 in `shortterm/data.py`, `KNOWN_FAILURES`.
- **Bars:** daily SIP, split- and dividend-adjusted, used for returns. Raw closes are used for the $5 price test.
- **Failures:** a known failure still held after its last listed day is valued at **zero** (total loss). Any other stock whose data ends while held exits at its last close; these are counted and reported.

## Rules common to every candidate

- **Decision** after each day's close; buy at the next open.
- **Holding:** 5 trading days, sold at the open 5 sessions after entry.
- **Long only** (branch-3: no shorting at launch).
- **Sizing:** each day's basket gets one fifth of the lane's capital, split equally across its names, so up to 5 overlapping baskets are open at once. If a day has fewer qualifying names, the unused share stays in cash, earning T-bills.
- **Costs per side:**
  - 4 bps for the 100 most-traded names;
  - 8 bps for ranks 101–300.

  Also reported at double costs and at zero.

## Candidates (trials)

| id | Rule |
|---|---|
| R0 | Benchmark: equal weight of the month's 300, rebalanced monthly. SPY is also reported |
| R1 | Buy the 10 worst 5-day returns |
| R2 | Buy the 10 worst 1-day returns |
| R3 | R1, but only on days when the VIX is at or above its trailing 252-day median (Nagel). Otherwise cash |
| R4 | R1, but only while SPY is above its 200-day average (avoid buying into bear markets) |
| R5 | R1, excluding names down more than 25% over the 5 days (large falls are more likely real news than noise) |

## Splits and decision rule

- **Development:** decisions 2016-02-01 to 2021-12-31.
- **Confirmation:** 2022–2023.
- **Holdout:** 2024-01-01 onward.
- **A candidate passes development if:**
  - its Sharpe above T-bills beats R0's by at least 0.20;
  - its worst drawdown is no worse than R0's;
  - its average net return per trade is positive at **double** costs.
- **Choice:** among the candidates that pass, the highest development Sharpe is chosen.
- **The chosen candidate runs once on confirmation and once on holdout,** with R0 and SPY alongside.
  - **It passes** if, in both periods, its Sharpe above T-bills is at least R0's and its worst drawdown stays within 25%.
  - **If nothing passes development,** the result is reported as a failure. Nothing is tuned and rerun.

## Reported

For every candidate:
- CAGR and Sharpe above T-bills;
- worst drawdown;
- trades per year and average net return per trade;
- win rate;
- turnover and cost drag;
- share of time invested;
- the number of exits caused by a stock's data ending.
## Result (run once, 2026-10-21; registry `research/shortterm_studies.jsonl`, version reversal-1.0.0)

**Development, 2016-02 to 2021-12.**

| id | CAGR | Sharpe above T-bills | Worst drawdown | Volatility | Trades/yr | Avg net per trade | CAGR at 2× costs |
|---|---|---|---|---|---|---|---|
| R0 equal-weight 300 | **16.8%** | **0.85** | −35.9% | 19.3% | — | — | — |
| R1 5-day losers | 5.6% | 0.31 | −60.6% | 39.7% | 2,523 | +0.23% | −1.4% |
| R2 1-day losers | 8.8% | 0.39 | −54.1% | 35.4% | 2,523 | +0.26% | +1.6% |
| R3 R1 when the VIX is high | 8.4% | 0.39 | −57.4% | 29.3% | 1,004 | +0.60% | +5.5% |
| R4 R1 when SPY is in an uptrend | −5.7% | −0.05 | −48.6% | 31.8% | 1,999 | −0.10% | −10.6% |
| R5 R1 without falls over 25% | 8.2% | 0.37 | −54.3% | 36.1% | 2,523 | +0.26% | +1.0% |

**Decision: nothing passed.** No candidate came within 0.45 of R0's Sharpe, and every drawdown was far deeper. So no confirmation or holdout was run.

**Reading:**
- **The bounce is real but small.** It is about +0.2–0.6% per 5-day trade before costs.
- **Concentration destroys it.** A 10-stock basket of the week's biggest losers carries about 30–40% volatility. Compounding at that volatility, plus costs, wipes out the bounce.
- **The VIX condition (R3) helped**, as Nagel found, but not nearly enough.
- **Data ended inside a trade only 2–6 times**, and no known failure was ever held.

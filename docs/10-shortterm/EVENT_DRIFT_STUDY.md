# Short-horizon lane, study 3: event drift in liquid US stocks. Registered 2026-10-21 before any result

**Owner direction (2026-10-21):** Jarvis's main business is trading individual stocks (plus commodities, bonds and crypto) at hours-to-days horizons, with a smarter decision layer. The ETF sector rotation is kept aside.

**Why this family.**
- **The effect:** when a large stock jumps sharply on heavy volume (usually earnings or other news), its price tends to keep drifting the same way for days to weeks.
  - Post-earnings drift: Bernard & Thomas 1989 (RECALLED).
  - Drift after large price moves with high volume: Gervais, Kaniel & Mingelgrin 2001, *high-volume return premium* (RECALLED).
- **Our earlier evidence:** the `earnings_drift` sleeve had a Sharpe of 1.36 on its own in 2024–26, on 10 stocks.
- **What this study changes:** the whole liquid market, and many events at once.
- **Lesson from study 1** (reversal): concentration and frequent trading killed a real effect. So here there are many slots, each held for weeks.

## Data

The same as study 1:
- the monthly top 300 by prior-month dollar volume, price at least $5;
- survivorship-aware candidates; known failures valued at zero after their last listed day;
- daily adjusted bars, with split-adjusted volume.

## Event (decided after the close of day t)

All four must hold:
- the stock's return that day is at least **+4%**;
- that return beats SPY's by at least **3%**;
- volume is at least **3×** its average over the previous 20 sessions;
- the stock is in the month's universe.

## Trading

- **Slots:** the lane has **20 slots of equal starting size**. Each slot holds one trade at a time; a free slot earns T-bills.
- **Entry:** events fill free slots at the next open, strongest first by return in excess of SPY. A stock already held is skipped.
- **Exit:** at the open 20 sessions after entry, unless a variant says otherwise.
- **Long only.**
- **Costs as study 1:** 4 bps per side for the top 100, 8 bps for the rest. Also reported at double.

## Candidates (trials)

| id | Rule |
|---|---|
| E0 | Benchmark: equal weight of the month's 300, monthly (study 1's R0) |
| E1 | The event rule above, hold 20 sessions |
| E2 | E1, hold 10 sessions |
| E3 | E1, only while SPY is above its 200-day average |
| E4 | Stronger events: at least +6% and at least 4× volume (the 3% excess rule unchanged) |
| E5 | E1 with a fade exit: sell at the next open if the stock closes below the event day's open (the jump has been given back) |

## Splits and decision rule (identical to study 1)

- **Development:** 2016-02-01 to 2021-12-31. **Confirmation:** 2022–2023. **Holdout:** 2024 onward.
- **A candidate passes development if:**
  - its Sharpe above T-bills is at least E0's + 0.20;
  - its worst drawdown is no worse than E0's;
  - its average net return per trade is positive at double costs.
- **The best passer runs once** on confirmation and once on holdout. **It passes** if, in both, its Sharpe above T-bills is at least E0's and its worst drawdown stays within 25%.
- **If nothing passes,** that is the result.

## Reported

For each candidate:
- CAGR, Sharpe above T-bills, worst drawdown;
- trades per year, average net per trade, win rate;
- the average number of slots in use;
- exits caused by a stock's data ending.

## Result (run once, 2026-10-21; version event-drift-1.0.0)

**Development, 2016-02 to 2021-12.**

| id | CAGR | Sharpe above T-bills | Worst drawdown | Volatility | Trades/yr | Avg net per trade | Win rate | Avg slots used (of 20) |
|---|---|---|---|---|---|---|---|---|
| E0 equal-weight 300 | **16.9%** | **0.86** | −35.9% | 19.3% | — | — | — | — |
| E1 base, 20 days | 9.9% | 0.51 | −30.7% | 21.1% | 149 | **+1.78%** | 57% | 11.7 |
| E2 10 days | 8.5% | 0.45 | −31.7% | 20.4% | 166 | +0.81% | 52% | 6.6 |
| E3 E1 in SPY uptrends | 11.9% | 0.62 | −25.0% | 19.9% | 126 | +1.64% | 56% | 9.9 |
| E4 stronger events | 8.5% | 0.57 | **−16.7%** | 14.5% | 70 | **+2.51%** | 57% | 5.5 |
| E5 fade exit | 4.2% | 0.30 | −22.7% | 13.7% | 167 | +0.59% | 42% | 7.3 |

**Decision: nothing passed** (the bar was a Sharpe of 1.06). So no confirmation or holdout was run; both periods remain unseen for this data.

**Reading:**
- **The effect is real and survives costs.** It earned +1.8% net per 20-day trade (+1.65% at double costs), and 57% of trades won.
- **But capital sits idle.** About 40–70% of the slots were empty, earning T-bills of about 1% in 2016–21. So the lane as a whole earned less than simply holding the 300 stocks.
- **The events are useful as signals that tilt a fully invested book,** not as a standalone strategy that is mostly in cash. That is an architecture conclusion, to be tested as its own pre-registered design. It is not a reason to rerun this one.

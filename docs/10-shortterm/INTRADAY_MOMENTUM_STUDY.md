# Short-horizon lane, study 4: intraday momentum (first half-hour → last half-hour). Registered 2026-10-21 before any result

**Why this family.**
- **The effect:** Gao, Han, Li & Zhou (2018, *Journal of Financial Economics*, "Market intraday momentum", RECALLED). The market's return from the previous close to 10:00 predicts its return in the last half-hour of the day. They report it for SPY back to 1993, stronger on volatile days and when the 15:00–15:30 half-hour agrees.
- **Why it suits a cost-sensitive system:** one round trip a day in the most liquid instruments.
- **Owner direction:** test it on individual stocks too, not only index funds.

## Data

- **Bars:** Alpaca 30-minute SIP bars, raw prices, regular session (bars starting 09:30 to 15:30 New York time).
- **Instruments:** SPY, QQQ, and every stock in a month's top 50 by the previous month's dollar volume. That is a point-in-time list taken from the study 1 universe.
- **Days skipped:** days without a 15:30 bar (early closes) are not traded.

## Definitions (day d)

- **First half-hour return:** the close of the 09:30 bar ÷ the previous session's 15:30-bar close (its 16:00 close) − 1. This includes the overnight move, as in the paper.
- **Twelfth half-hour return:** the close of the 15:00 bar ÷ its open − 1.
- **Trade:**
  - Buy at the open of the 15:30 bar and sell at its close (the 16:00 close). That is one round trip, all intraday.
  - Long only. Out of the trade, capital earns T-bills.
- **Costs per side:**
  - 1 bp for SPY and QQQ;
  - 3 bps for the top-50 stocks.

  Also reported at double.

## Candidates

| id | Rule |
|---|---|
| I0 | Baseline: buy SPY in the last half-hour every day, unconditionally |
| I1 | SPY: buy in the last half-hour if the first half-hour return > 0 |
| I2 | QQQ: the same rule as I1 |
| I3 | Top-50 stocks: each stock on its own signal (its first half-hour return > 0). Equal weight across the stocks that qualify that day |
| I4 | I1, but only on days when \|first half-hour return\| is above its trailing 60-day median |
| I5 | I1, but only if the twelfth half-hour return is also > 0 |

## Splits and decision rule

- **Splits:** development 2016-02-01 to 2021-12-31; confirmation 2022–2023; holdout 2024 onward.
- **A candidate passes development if all three hold:**
  - its Sharpe above T-bills is at least I0's + 0.20, and at least 0.50;
  - its average net return per trade is positive at double costs.
- **The best passer runs once on confirmation and once on holdout.** In each period it passes if:
  - its Sharpe above T-bills is at least 0.50 and above I0's;
  - its worst drawdown is within 25%.
- **Otherwise the result is a failure.**

**Note:**
- **Small returns are expected.** Capital is at work only 30 minutes a day, so even a real edge gives modest annual returns on its own.
- **Its value would be as an add-on:** it uses buying power only intraday, and holds nothing overnight.

## Reported

For each candidate:
- CAGR, Sharpe above T-bills, worst drawdown;
- trades per year, average net per trade, hit rate;
- the share of days traded.

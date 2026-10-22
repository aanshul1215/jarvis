# Pre-registration: <study name>

**Written:** <date and time>, before any return was computed. SHA-256 of this file: recorded in `deviations.txt`.

## 1. Question and hypothesis

- **Owner request (verbatim):**
- **Hypothesis:**
- **Why it could work:** who is on the other side, and why the edge has not been competed away.
- **Evidence:** papers and earlier Jarvis studies. Mark anything not verified as RECALLED.
- **What would falsify it:**

## 2. Data

- **Sources and files**, with SHA-256 manifests:
- **Universe:** point-in-time rule and survivorship handling (`KNOWN_FAILURES` valued at zero).
- **Adjustments:** raw or adjusted, and where each is used.
- **Known data problems, and how they are handled:**

## 3. Rules (implemented exactly)

- **Decision time,** and the data available at that time:
- **Signal:**
- **Entry and exit,** with order type and fill rule (auction, limit, stop; same-bar ambiguity resolved conservatively):
- **Sizing and leverage cap:**
- **Costs:** base, double the base, and zero.
- **Trials:** list each one. No variants beyond these.

## 4. Periods

- **Development:**
- **Confirmation:**
- **Holdout:** run once, only for trials that pass.
- **Post-publication window,** if replicating a paper:

## 5. Decision rule

- **Passing development and confirmation needs:**
- **Keeping it after the holdout needs:**
- **Trial count for the deflated Sharpe:** this study plus the related earlier ones.

## 6. Metrics

CAGR, volatility, Sharpe above T-bills, max drawdown, worst day/week/month, trades per day, win rate, average net P&L per trade (bps), turnover, Sharpe by year, the share of months at +15% or more, correlation with SPY and with the running desks, and the monthly return implied at the allowed leverage.

## 7. Sanity checks

- a hand-traced example;
- an independent re-implementation of the core;
- a look-ahead truncation test;
- counts at each stage.

# Strategy register (pre-registration)

Written 2026-10-19, **before any strategy has been run on real market data.** Each entry fixes the hypothesis, rules,
parameters, exits and evaluation plan in advance. Changing any rule or parameter creates a new version, which is a
new trial: the evaluation gate divides its significance threshold by the number of runs registered for a strategy,
so every retry makes passing harder.

Evidence tags follow the rest of the repository: **FETCHED** (the source was opened during the October research),
**RECALLED** (from memory, not re-opened), with the research brief (`docs/01-research/NN`) or review
(`docs/03-review/SNN`) where it was discussed. Nothing here is investment advice.

## Common rules for every strategy

- Long-only, long or flat. One position per asset; the strategy that opened it owns its exit.
- Decisions on completed bars only; orders fill at the next bar's open (daily stocks: the next session's open).
- Sizing: a base of $1,000 per entry (of $10,000), scaled by the Phase 5 volatility forecast: notional = base ×
  min(1.5, 1% ÷ forecast daily volatility), rounded down to whole shares for stocks. The Governor's limits apply
  unchanged. *Amended 2026-10-19, before any real-data run* (originally a fixed dollar amount): the workflow makes
  the volatility forecast set position size for every strategy. The forecaster is the winner of the pre-registered
  study in `docs/07-awareness/MODEL_REGISTER.md`; runs use `backtest --sizing volatility --volatility-model <winner>`.
- Costs: 5 bps per side for stocks; 25 bps fee plus 5 bps spread per side for crypto; every evaluation is repeated
  with costs doubled.
- Exits: each strategy's own signal, an optional stop-loss measured in ATRs below the entry price, and a maximum
  holding period (`exit_after_bars`).

## Pre-registered evaluation plan

| Item | Fixed choice |
|---|---|
| Data | `1Day-adjusted` Alpaca SIP bars for the confirmed universe (`config/universe.example.json` until edited) |
| Development period | 2016-03-01 to 2023-12-31 |
| Holdout | 2024-01-01 to the latest data, evaluated **once** per strategy configuration, only after the development result is recorded |
| Benchmark | Equal-weight universe rebalanced monthly (with costs); also equal-weight buy-and-hold and cash at the T-bill rate |
| Pass rule | The gate in `src/jarvis/harness.py`: no leak alarm, future-poisoning test passed, ≥30 trades, block-bootstrap p-value below 0.05 ÷ trials versus the benchmark, ≥60% of years ahead of it, still ahead with costs doubled |
| Trial budget | One development run per strategy version. A strategy that fails is recorded as a negative result, not tuned |
| Expectation | Most of these strategies are expected to **fail** against a fully invested benchmark after costs (briefs 09, 18). A failure is a valid, recorded outcome |

## The strategies

### 1. `breakout-volume@1.0.0` (existing baseline)

- **Bet:** a close above the prior 20-bar high on heavy volume tends to continue for a few bars.
- **Entry:** `breakout_20 > 0` and `relative_volume ≥ 1.5`. **Exit:** after 3 bars. **Stop:** none.
- **Evidence:** practitioner channel-breakout rules (Donchian-style) — RECALLED; no peer-reviewed support found in
  the October research. Brief 09 found short-horizon technical edges rarely survive retail costs.
- **Would prove it wrong:** no significant excess over the benchmark, or excess that vanishes with doubled costs.

### 2. `trend-sma200@1.0.0` — time-series trend

- **Bet:** assets above their long-term average with a positive 6-month return keep trending; being out during
  long declines cuts drawdowns.
- **Entry:** close above its 200-bar average and `ret_126 > 0`. **Exit:** close below the 200-bar average
  (`TREND_BROKEN`); maximum 252 bars. **Stop:** none (the trend filter is the exit).
- **Evidence:** Faber, *A Quantitative Approach to Tactical Asset Allocation* (10-month average rule) — FETCHED (S01,
  brief 18); Moskowitz, Ooi & Pedersen 2012, *Time Series Momentum* — FETCHED (S01). Brief 18: the honest
  expectation is roughly −1 to +1 point a year versus holding the same assets, with smaller drawdowns — a risk
  reducer more than a return source.
- **Would prove it wrong:** fails the gate; or passes on return but not on drawdown.

### 3. `meanrev-rsi2@1.0.0` — short-term mean reversion in an uptrend

- **Bet:** a sharp 2-bar pullback inside a long-term uptrend tends to bounce within days.
- **Entry:** `rsi_2 < 10` and close above the 200-bar average. **Exit:** close above the 5-bar average
  (`REVERTED`); maximum 5 bars. **Stop:** 2 ATR below entry.
- **Evidence:** short-term reversal in returns (Lehmann 1990; Jegadeesh 1990) — RECALLED, studied mostly
  cross-sectionally at weekly/monthly horizons; the RSI(2) rule itself is practitioner (Connors & Alvarez) —
  RECALLED, no peer-reviewed test found. Brief 09: reversal profits shrink sharply after costs.
- **Would prove it wrong:** fails the gate; or high win rate with losses larger than wins (check average win/loss).

### 4. `volatility-breakout@1.0.0` — breakout after volatility contraction

- **Bet:** after unusually quiet periods, a break above the recent range starts a larger move.
- **Entry:** 20-bar volatility below 75% of its 1-year level and close above the prior 20-bar high.
  **Exit:** close below the prior 20-bar low (`BROKE_DOWN`); maximum 20 bars. **Stop:** 2 ATR below entry.
- **Evidence:** volatility clustering is well documented (ARCH/GARCH literature) — RECALLED; the contraction-then-
  breakout trading rule is practitioner ("squeeze") — RECALLED, no peer-reviewed test found.
- **Would prove it wrong:** fails the gate.

### 5. `relative-strength@1.0.0` — cross-sectional momentum

- **Bet:** the assets with the strongest 12-month returns (skipping the latest month) keep outperforming for a
  while; an absolute filter avoids holding "the best of a falling market".
- **Entry:** rank 1–3 by `mom_12_1` among the universe's stocks/ETFs at the same decision moment, and
  `mom_12_1 > 0`. **Exit:** rank worse than 5 (`RANK_DROPPED`) or `mom_12_1 < 0` (`MOMENTUM_NEGATIVE`);
  maximum 63 bars. **Stop:** none. Needs at least 6 ranked assets.
- **Evidence:** Jegadeesh & Titman 1993 (stock momentum) and industry/asset-class momentum — RECALLED; dual
  momentum's absolute filter (Antonacci) — FETCHED (S01). McLean & Pontiff: published anomalies decay about 58%
  after publication — FETCHED (brief 18).
- **Caveat:** the 10 single stocks in the proposed universe were picked by today's size (survivorship bias), which
  flatters momentum; read any result on them with that in mind, and prefer the ETF-only view.
- **Would prove it wrong:** fails the gate; or the result depends on the single stocks only.

### 6. `earnings-drift@1.0.0` — post-earnings drift (price-reaction proxy)

- **Bet:** after a strongly positive reaction to an earnings release, prices keep drifting up for weeks.
- **Entry:** an 8-K item 2.02 release (SEC index-page acceptance time) became public during the latest bar, and that
  bar rose more than 2% on at least 1.5× normal volume. **Exit:** maximum 20 bars. **Stop:** 2 ATR below entry.
- **Evidence:** post-earnings-announcement drift (Bernard & Thomas 1989) and drift after the earnings-announcement
  return (Brandt, Kishore, Santa-Clara & Venkatachalam 2008) — RECALLED; brief 09 notes the drift has weakened in
  recent decades (Martineau, unverified). Free data has no analyst consensus, so the price reaction stands in for
  the earnings surprise.
- **Caveat:** about 10 stocks × 4 releases a year gives few trades; the 30-trade minimum may not be reached.
- **Would prove it wrong:** fails the gate; too few trades is recorded as inconclusive, not as a pass.

### 7. `news-sentiment@1.0.0` — unusually positive news (added 2026-10-20, Phase 6)

Registered before any headline had been scored: the news archive had been downloaded, but no sentiment number
existed yet.

- **Bet:** a burst of unusually positive news about an asset is followed by a few days of continued gains, because
  news is absorbed into prices gradually.
- **Data:**
  - Alpaca/Benzinga headlines for the universe, from 2016. Each counts from its creation time plus one minute, or from its last update if it was edited more than ten minutes later.
  - Each headline is scored by FinBERT (`ProsusAI/finbert`, revision `0bc2ac10`), run locally: P(positive) − P(negative).
- **Signal:**
  - The mean score of headlines that became available in the last 24 hours, compared with the asset's own previous 60 days, in standard errors.
  - This needs at least 3 recent headlines and 20 baseline headlines.
- **Entry:** z ≥ 2. **Exit:** z ≤ −2 (`SENTIMENT_TURNED`); maximum 5 bars. **Stop:** 2 ATR below entry.
- **Evidence:**
  - Tetlock (2007): media pessimism predicts short-term market declines (RECALLED).
  - Tetlock, Saar-Tsechansky & Macskassy (2008): negative words in firm news predict earnings and returns (RECALLED).
  - Both studies used the *negative* side. A long-only test of the positive side is a weaker version of the idea.
- **Caveats:**
  - The FinBERT licence is non-commercial (CC BY-NC-SA 4.0). Research and paper trading only, until it is replaced or cleared.
  - Headline coverage is uneven: more for large stocks, little for sector ETFs, so expect few signals on ETFs.
  - Crypto history in Alpaca bars starts only in 2021.
- **Would prove it wrong:** fails the gate; or too few trades (recorded as inconclusive).

### Control: `random-entry@1.0.0`

- Enters on a seeded coin flip (5% of bars), exits after 3 bars. Exists only so the gate can be shown to reject
  noise; never approved for paper or live.

## Results — development period 2016-03-01 to 2023-12-31 (run 2026-10-20)

**Setup:**
- 27 US stocks and ETFs, Alpaca SIP daily bars (adjusted). Crypto bars on Alpaca start only in 2021, so crypto was not part of these runs.
- $10,000 account, $1,000 base entry sized by the GARCH volatility forecast.
- Code 8d04e90 (runs 1–4) and f152a38 (runs 5–7); the code paths these strategies use are identical.
- Entries 1–7 in `JARVIS_HOME/research/experiments.jsonl`.
- Each strategy has had **one** trial, and none was tuned.

| Strategy | Run | Return / yr | Sharpe | Worst drawdown | Capital invested | Trades | Alpha / yr (beta-adjusted) | Bootstrap p | Years ahead | Leak test | Gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `breakout-volume@1.0.0` | 6 | 0.1% | 0.09 | -5% | 8% | 594 | -0.2% | 1.00 | 2/8 | pass | FAILED |
| `trend-sma200@1.0.0` | 3 | 8.8% | 1.11 | -16% | 56% | 319 | +2.9% | 0.99 | 3/8 | pass | FAILED |
| `meanrev-rsi2@1.0.0` | 4 | 2.8% | 0.44 | -17% | 35% | 2,804 | -1.3% | 1.00 | 1/8 | pass | FAILED |
| `volatility-breakout@1.0.0` | 2 | 3.8% | 0.73 | -7% | 35% | 488 | +1.4% | 1.00 | 1/8 | pass | FAILED |
| `relative-strength@1.0.0` | 1 | 4.1% | 1.09 | -6% | 16% | 161 | +1.3% | 1.00 | 2/8 | pass | FAILED |
| `earnings-drift@1.0.0` | 5 | 0.6% | 0.48 | -3% | 3% | 90 | +0.2% | 1.00 | 2/8 | pass | FAILED |
| `random-entry@1.0.0` (control) | 7 | -0.4% | -0.09 | -10% | 25% | 1,782 | -3.1% | 1.00 | 1/8 | pass | FAILED (as it must) |

Benchmarks over the same period:
- Equal weight, rebalanced monthly: 18.1% a year, Sharpe 1.09, worst drawdown -30%.
- Equal-weight buy and hold: 25.5%, 1.06, -42%.
- T-bills: 1.6%.

**Reading the results:**
- **Every strategy failed** the pre-registered gate against the fully invested equal-weight benchmark, as this register expected. Each failed for the same three reasons: not significant, behind in most years, and not robust to doubled costs.
- No leak was found: every run passed the future-poisoning test.
- The random control failed, so the gate does reject noise.
- **Trend following** behaved as the research predicted (brief 18). It matched the benchmark's risk-adjusted return (Sharpe 1.11 vs 1.09) with about half the drawdown. It is a risk reducer, not a return source.
- **Relative strength** had a similar Sharpe at very low exposure.
- **Low capital use** dominates the comparison:
  - $1,000 entries on a $10,000 account left 3–56% of the capital invested, against 100% for the benchmark.
  - Almost no strategy can beat a fully invested benchmark on raw daily return that way.
  - This was known when the gate was written. Changing the sizing or the comparison now would be a new, separately counted trial, and it is listed as an open decision for the owner, not applied after the fact.
- **The universe favours holding:** it was chosen in 2026 and includes NVDA, META and TSLA, so it flatters buy and hold (survivorship bias), which raises the bar for every strategy.
- The holdout (2024 onward) was not used: no strategy passed development.

## Pre-registration v1.1 — core-satellite (owner decision 2026-10-20, before any v1.1 run)

**Why:** in the development results above, most capital sat idle ($1,000 entries on a $10,000 account). The owner chose
to test the strategies in a way that uses the whole account. The v1.0 results stand unchanged.

**Rule (same for every strategy, nothing tuned per strategy):**
- Idle capital is held in the equal-weight basket of the universe (the benchmark itself, rebalanced monthly), not in cash.
- Each strategy's positions are paid for out of that basket.
- The account is therefore always fully invested. The gate asks one question: do the strategy's holdings beat the basket they displace?
- Daily return = strategy return + yesterday's idle share × basket return − the cost of moving the change in the idle share in or out of the basket (5 bps per side; doubled in the stress test).
- Implemented as `core_satellite()` in `src/jarvis/harness.py`, with `backtest --overlay core_satellite`.

**What stays the same:**
- The same strategies (`@1.0.0` rules), universe, period (2016-03-01 to 2023-12-31), GARCH sizing, costs, gate and leak tests.

**Trials:**
- Each strategy's v1.1 run is its **second** registered run, so its significance threshold is 0.05 ÷ 2 = 0.025.
- The random control is run too: with no skill, it should land close to the basket and fail.

**Expectation:** a strategy with no stock-picking skill ends up near the benchmark minus its extra trading costs, and fails. Passing requires the strategy's chosen positions to beat the basket, consistently and after doubled costs.

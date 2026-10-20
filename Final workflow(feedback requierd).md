# JARVIS — Final workflow (feedback required)

**Status:** proposed, 2026-10-19 (situational-awareness section added 2026-10-19). Not yet approved. Comments and suggested changes are welcome — see [Feedback](#feedback) at the end.

## Goal

A system of agents that feeds on price data, social-media sentiment, financial data and news, and trades **paper money on Alpaca**. It learns which strategy to use in which market situation, and is judged honestly: it must beat simple benchmarks on unseen data, after costs, with smaller drawdowns.

## Principles

- **Paper money only.** Real money only by a separate, explicit decision of the owner — never automatically.
- **No HFT pretence.** Alpaca gives ~100 ms+ access, IEX-only stock quotes on the free plan and no stock order book, so speed and order-flow edges are out of reach. We use the mid-frequency quant toolkit instead: situational awareness, volatility forecasting, risk management, cost modelling and rigorous validation.
- **Every model earns its place.** A model is kept only if it beats a simple baseline on data it never saw. More data and more models can make the system worse.
- **Agents produce information, not orders.** AI agents turn news, filings and social posts into numbers; deterministic code and the risk gate place orders.
- **Log everything.** Every experiment, including failures, is recorded so we always know how many ideas were tried.
- **Near-zero budget.** Free data tiers, local models where possible, capped batch use of Claude.
- **Success definition:** beats buy-and-hold and an equal-weight blend on unseen periods, after costs, with a smaller worst-case drawdown.

## Phase plan

Durations are rough planning estimates for part-time work, not commitments. Each phase ends with an **exit test** that must pass before the next phase starts.

### Phase 0 — Setup and decisions (week 1)

- Record the new direction in the repo's decision log.
- Revoke the old exposed keys (OpenAI key from the Hugging Face Space; search key in the Colab archive).
- Open an Alpaca paper account and **reset its balance to realistic capital** ($1,000–$10,000), not the $100,000 default.
- Keep API keys only in the local environment, never in the repo.
- Run `alpaca-check` and record answers to:
  - Is crypto tradable for the account in Texas?
  - Do fractional limit orders work?
  - Do hourly stock bars include pre-market and after-hours?
  - How is the crypto fee taken (from the received coin or in USD)?
  - Is the news feed included in the free plan?
- Agree the split of work between owner and teammate.

**Exit test:** every question above has a recorded answer; no secrets in the repo.

### Phase 1 — Fix the foundation (weeks 1–2)

- Fix the blockers found in the review of `feature/jarvis-v1-implementation`:
  1. Windows crash when saving price and feature files (`fsync` on a read-only handle).
  2. Second exit of the same asset/quantity reuses the old order ID, so it never sells.
  3. One unfilled order freezes every asset, including exits; no cancel path.
  4. A vendor-amended price bar sends the desk to SAFE.
  5. Daily-loss and drawdown limits are never checked.
  6. Crypto fee taken from the received coin breaks reconciliation.
- Turn each reproduction script into a test.
- Add GitHub Actions CI on Windows and Linux.
- Merge into `main` through a pull request.

**Exit test:** all tests pass on Windows in CI; a mock paper loop runs 24 hours without stopping itself.

### Phase 2 — Data layer (weeks 2–4)

- **Prices:** backfill history for 20–30 liquid stocks/ETFs plus BTC and ETH (Alpaca; stocks back to about 2016 on the free plan). Keep raw and split/dividend-adjusted versions.
- **Financial data:** company fundamentals and filing dates from SEC EDGAR; macro series from FRED.
- **Situational-awareness inputs** (see Phase 5): market-stress and rate series from FRED; daily bars for a broader
  breadth universe (for example S&P 500 members); the exchange trading calendar; the Fed meeting and economic-release
  calendars. Collect these from the start so they cover the full backtest period.
- **Start the social and news collectors now** — Reddit (after checking its API terms), crypto social sources, news if available — storing every item with its first-seen time. Sentiment can only be tested on data we have archived ourselves, so every week of delay is a week of history lost.
- Data-quality checks: missing bars, spikes, duplicates.

**Exit test:** rebuilding the dataset from scratch gives identical files (hash-verified); a planted future-data leak is caught.

### Phase 3 — Evaluation harness (weeks 3–5) — the most important phase

- One code path: the backtester uses the same feature, strategy and risk code as paper trading.
- Realistic per-asset costs: spread for stocks; 0.30–0.50% per round trip for crypto.
- Walk-forward testing (train on the past, test on the next unseen period), plus a final holdout touched once.
- Experiment log: every backtest run recorded, failures included.
- Benchmarks: buy-and-hold, equal-weight universe, cash.
- Metrics: return after costs, worst drawdown, average loss on the worst days, turnover.

**Exit test:** the legacy v1 TSLA leakage case is caught; a random strategy fails to pass.

### Phase 4 — Strategy library (weeks 5–7)

Six to eight genuinely different base strategies, each written down before it is tested and kept on record whether it wins or loses:

1. Trend — moving-average or 12-month momentum
2. Mean reversion — short-term dips, stretched moves
3. Breakout — the existing `breakout-volume` strategy
4. Volatility breakout — sharp moves after quiet periods
5. Relative strength — rank the universe, hold the strongest
6. Event-driven — drift after earnings filings (EDGAR dates)
7. Sentiment-driven — added in Phase 6 once archived data exists

**Exit test:** each strategy has a daily return series on unseen periods — the raw material for the selector.

### Phase 5 — Situational awareness models (weeks 6–9)

| Model | Baseline it must beat |
|---|---|
| Volatility forecaster (HAR-RV / GARCH) | Simple moving average of recent volatility |
| Regime detector (rule-based, then change-point or filtered HMM) | Above/below the 200-day average |
| Correlation / risk model | Equal-weight risk |
| Transaction-cost model | Fixed cost assumption |

**Exit test:** each model beats its baseline on unseen data, or it is dropped. The volatility forecast then sets position size for every strategy.

#### Situational awareness: the full picture

The models above summarise the market. Situational awareness also needs the raw signals below, computed point-in-time
(only what was known at the decision moment) and fed to the regime detector, the risk gate and the strategy selector.

| Area | Signals | Free source (to verify in Phase 0/2) | Why it matters |
|---|---|---|---|
| Market-wide stress | VIX level and change; high-yield credit spread; 10-year and 2-year Treasury yields and their gap | FRED (`VIXCLS`, `BAMLH0A0HYM2`, `DGS10`, `DGS2`, `T10Y2Y`); check history length and terms for the ICE BofA series | Separates calm, nervous and crisis markets; most strategies behave differently in each |
| Market breadth | Share of stocks above their 200-day average; advancing vs declining stocks; new highs vs new lows | Computed from Alpaca daily bars over a broad universe | A rally on narrow breadth behaves differently from a broad one |
| Scheduled events | Earnings dates; Fed (FOMC) meetings; CPI and jobs releases | EDGAR filing history (past earnings); Federal Reserve and BLS published calendars; a free forward earnings calendar is still an open question | Volatility and risk jump around events; strategies may stand aside or size down |
| Liquidity | Spread and volume relative to normal, by time of day | Alpaca quotes and bars (IEX-only for stocks on the free plan) | Wide spreads and thin volume turn a good signal into a losing trade |
| Calendar | Time of day, day of week, holidays and half-days, crypto weekends | Alpaca market calendar | Opening and closing hours, holidays and weekend crypto have different behaviour |
| Crypto-specific | BTC vs ETH relative move; crypto–equity correlation; weekend flag | Alpaca crypto bars | Crypto regimes and stock regimes are linked but not the same |
| Cross-asset | Rolling correlations between holdings and with the broad market | Computed from stored bars | Several positions can secretly be one bet |
| The system's own state | Open positions, recent losses, drawdown from peak, correlation of open trades | The journal and broker reconciliation | Awareness includes itself: after losses or crowded positions, risk is cut |

**Test for every signal:** it is added only if it improves a downstream decision (regime labels, risk sizing or
strategy selection) on unseen data, compared with the same model without it. Signals that do not help are recorded as
negative results and removed.

### Phase 6 — Information agents (weeks 8–11)

- News and social sentiment scored by a **local FinBERT model** (free, runs on the laptop).
- **Claude agents** read filings and news into structured fields — event type, surprise, materiality — in batches under a monthly spend cap.
- Social signals: mention counts, spikes, novelty, and a pump-like-spike flag.
- Every feature carries its first-seen timestamp. Agent output is a number the system uses, never an order.

**Exit test:** features flow into the store; a sentiment strategy is tested on the archived period (expect this period to be short at first).

### Phase 7 — Strategy selector (weeks 10–14)

Built in three versions, each kept only if it beats the previous one:

1. **Regime lookup** — use the strategies that historically did best in the current regime.
2. **Meta-labelling** — a model predicts whether each strategy's current signal will pay off, and filters or sizes it.
3. **Contextual bandit** — learns online from paper results which strategies to weight in current conditions.

**Exit test:** beats the equal-weight blend of all strategies on unseen periods, after costs, with smaller drawdowns. If not, the system runs the equal-weight blend — a legitimate outcome.

### Phase 8 — Full paper trading (week ~12 onward)

- Each cycle: data → features and regime → strategies → selector → volatility-based sizing → risk gate → Alpaca paper order → journal.
- Daily report; weekly memo written by Claude.
- Drift monitor flags when paper results diverge from what the backtest expected.
- The bandit keeps learning from paper outcomes.

**Exit test:** three months with no unexplained broker mismatches, and paper results within the range the backtest predicted.

### Phase 9 — Monthly review loop

- Add or retire strategies through the harness; retrain models on schedule; log every decision.
- Real money only by a separate, explicit owner decision.

## Additional models considered (ranked by likely usefulness)

| Model | Purpose | Outlook |
|---|---|---|
| Volatility forecaster | Position size and stops | Strongest evidence; build first |
| Regime / change-point detector | Market state for the selector | Useful if strictly point-in-time |
| Strategy selector / meta-labeller | Choose or filter strategies | Valuable once the strategy library exists |
| Transaction-cost model | Spread and slippage by asset and time | Often decides profit vs loss |
| Risk / correlation model | Prevents several trades being one bet | Standard practice |
| Sentiment and event extractor | News, filings, social → numbers | Good use of agents; weak, fast-decaying predictive evidence |
| Anomaly / data-quality model | Bad prices, pump spikes, broken feeds | Protects every other model |
| Drift monitor | Detects when a model stops working | Needed once paper trading runs |
| Direction forecaster | Up/down prediction | Most tempting, least reliable; expect near coin-flip |

## Roles

| Who | Responsibility |
|---|---|
| Owner | Decisions, Alpaca account, risk limits, pull-request review |
| Teammate | Implementation lead |
| Claude | Writes and reviews code, designs strategy specs, researches each model before it is built, runs the information agents |

## Immediate next actions

1. Phase 0 checklist (owner, about one evening).
2. Phase 1 blocker fixes (about 2–4 developer days).
3. Start the Phase 2 data collectors as early as possible — sentiment history only accumulates going forward.

## Feedback

This workflow needs review before it is adopted. Please comment on:

- The phase order and the exit tests — are any too strict or too loose?
- The starting universe (20–30 stocks/ETFs plus BTC and ETH).
- Which social and news sources we can legally and cheaply use.
- The base strategy list in Phase 4.
- The success definition.

How to give feedback: open a GitHub issue titled `Workflow feedback: <topic>`, or open a pull request that edits this file with the reason in the description.

Nothing in this document is investment, tax or legal advice.

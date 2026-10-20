# Strategy selector register (pre-registration)

Written 2026-10-20, **before the selector has been run on real market data** (that run needs the Alpaca back-fill).
It fixes how the selector is built and judged. Changing a rule or constant is a new `SELECTOR_VERSION` in
`src/jarvis/selector.py`. Every run is appended to `JARVIS_HOME/research/selector_studies.jsonl`.
- The holdout may be evaluated once, and only after the development result is recorded (enforced in code).
- A holdout is claimed in the registry *before* it runs, so an interrupted run cannot be repeated.

Evidence tags: **FETCHED** (opened by a research agent; URL in the cited brief) and **RECALLED** (not re-opened).
Nothing here is investment advice.

## What the selector decides

At the start of every month it decides a **size multiplier for each strategy**:
- 1 is the base size, and 0 means no new entries.
- The multiplier is at most 2, and the order also stays within the Governor's per-order cap.

It applies to new entries only. Open positions keep the exit rules of the strategy that opened them. A second
mechanism, the meta-label filter, can veto individual entries. Both act inside the real order path
(`TradingEngine.allocation` / `entry_filter`), so the replay and the paper desk use the same code.

## How it is evaluated

1. **Sleeves.** Each registered strategy is replayed alone over the full data period, with volatility sizing (GARCH, per `docs/07-awareness`). This gives its daily returns and completed trades.
2. **Schedules.**
   - At each month start (midnight New York time), every allocator is given only the sleeve returns and market labels dated **before** that day.
   - This is tested by scrambling everything after a cut-off: earlier allocations must not change.
3. **Combined replay.** All strategies trade together through the real code, with the schedule applied. This includes one position per asset, the Governor, costs and the GARCH sizing.
4. **Chain** (the workflow's Phase 7): each stage is compared with the best version so far, and kept only if it passes.

| Stage | Candidate | Rule |
|---|---|---|
| Baseline | Equal weight | Every strategy at multiplier 1 |
| 1 | Regime lookup | Market label = trend/volatility state of the proxy (SPY, else the first stock), dated by the New York day on which it became known. The label used is the last one known before the month.<br>Each past daily return is judged against the label known before that day, matching how the label is used.<br>Strategies whose past average daily sleeve return in that regime is positive, with at least 60 in-regime days, are held equally. None selected means no new entries.<br>Equal weight until 252 sleeve days exist |
| 2 | Meta-labelling | Per strategy and calendar year, a logistic regression (C = 1, standardised) on 8 entry features: `ret_20`, `ret_60`, `rsi_14`, `dist_sma_200`, `volatility_ratio_20_252`, `atr_14_pct`, `relative_volume`, `dist_high_252`.<br>It predicts whether the trade's return after modelled costs is positive; entries below a probability of 0.5 are skipped.<br>It trains only on trades whose exit was decided at least 7 days before 1 January, and needs ≥ 50 trades with ≥ 10 of each outcome; otherwise there is no filter that year.<br>It is applied on top of the incumbent allocation |
| 3 | Contextual bandit | Thompson sampling. Each strategy's monthly sleeve return is modelled by Bayesian linear regression on the month-start context (constant, trend, volatility state), with a prior standard deviation of 0.05 and 2,000 draws.<br>Weight = the share of draws in which the strategy is best and its expected return is positive; the rest goes to cash. Needs 12 months; otherwise equal weight.<br>It keeps the incumbent's filter |

**Asymmetry to keep in mind:**
- With GARCH sizing, a calm asset's order is already at 1.5× base, which is the Governor's per-order cap in backtests. A multiplier of 2 therefore often adds little.
- Multipliers below 1 always cut exposure in full.
- So a selector that holds fewer strategies tends to have *smaller drawdowns* by construction. That is why the significance and doubled-cost tests are required as well.

**Pass rule for a stage** (all must hold, against the incumbent):
- The one-sided circular block-bootstrap p-value of the mean daily excess return is below 0.05 ÷ 3.
- The maximum drawdown is smaller.
- The mean excess is still positive when every cost is doubled for both.
- The run did not stop.

If no stage passes, the desk runs **equal weight**. The workflow calls this a legitimate outcome.

| Split | Combined replay window | History available to the selector |
|---|---|---|
| Development | 2016-03-01 to 2023-12-31 (New York time) — the full chain of stages | Sleeves over the same period |
| Holdout | 2024-01-01 to the latest data — **only the configuration development selected**, against equal weight, one test at p < 0.05 (if development kept equal weight, there is nothing to confirm) | Sleeves from 2016, but each allocation still only sees days before it |

## Honest expectations

- Choosing among strategies rarely beats holding them equally once estimation error is counted. In DeMiguel, Garlappi & Uppal (2009), none of 14 optimised allocation rules reliably beat 1/N out of sample (RECALLED). The most likely outcome here is that equal weight stays.
- Decisions are monthly: about 90 in the development period, which is little data for a learner. The bandit is expected to stay close to equal weight.
- Meta-labelling evidence is mostly book-level and simulated (López de Prado 2018; Meyer, Barziy & Joubert; brief 10, F11–F12, RECALLED / snippet only). Each strategy has few trades a year, so many years will have no model.
- The Phase 5 regime study found no predictive value in the regime labels. Stage 1 tests a different use (choosing strategies), so a failure here would confirm that result rather than contradict it.

## Live use (Phase 8)

The chosen configuration's schedule must be recomputed each month from sleeve replays on the stored bars, and read by the paper desk. That job and its tests belong to Phase 8. Until a stage passes, the paper desk runs every strategy at multiplier 1.

## Results — development 2016-03-01 to 2023-12-31 (run 2026-10-20)

Registry entry 1 in `selector_studies.jsonl`, code 6162e2a.
- **Desk:** all six registered strategies on the 27-stock/ETF universe, with GARCH sizing, trading together through the real code.
- **Market proxy:** SPY.

| Stage | Candidate vs incumbent | Return / yr | Sharpe | Worst drawdown | Bootstrap p | Result |
|---|---|---|---|---|---|---|
| Baseline | Equal weight (all strategies at multiplier 1) | 10.5% | 1.25 | -14.2% | — | incumbent |
| 1 | Regime lookup | 11.1% | 1.24 | -16.3% | 0.27 | FAILED (not significant; larger drawdown) |
| 2 | Equal weight + meta-label filter (30 yearly models) | 9.4% | 1.15 | -15.3% | 0.91 | FAILED (not significant; larger drawdown) |
| 3 | Contextual bandit | 11.2% | 1.26 | -18.9% | 0.22 | FAILED (not significant; larger drawdown) |

**Selected: equal weight.** No stage beat it, which matches the expectation stated before the run (DeMiguel et al.). The
regime lookup and the bandit earned slightly more, but with larger drawdowns and nothing close to significance. The
meta-label filter made results worse.

**For comparison** (from the strategy register), over the same period:
- the six strategies run alone: 0.1–8.8% a year, Sharpe 0.09–1.11;
- holding the 27 assets equally: 18.1% a year, Sharpe 1.09, worst drawdown -30%.

**The combined desk:**
- It diversifies well: its Sharpe of 1.25 is above every single strategy's and above the benchmark's. Its drawdown is less than half the benchmark's.
- It earns less than holding everything, because much of the capital sits idle (see the capital-use note in `docs/06-strategies`).
- This is a description, not a test: the desk as a whole was not pre-registered as a strategy against the benchmark.

**Holdout:** development kept equal weight, so there is no selector configuration to confirm. Running the holdout
would only record the equal-weight desk's 2024+ performance, once.

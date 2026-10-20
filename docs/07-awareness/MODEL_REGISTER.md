# Situational-awareness model register (pre-registration)

Written 2026-10-19 and committed **before any of these models was run on real market data.** It fixes each model,
its baseline, the data, the split and the pass rule, as `docs/06-strategies/STRATEGY_REGISTER.md` does for
strategies. Changing a rule or constant is a new study version (`STUDY_VERSION` in `src/jarvis/studies.py`), and
every run is appended to `JARVIS_HOME/research/model_studies.jsonl`. The holdout may be evaluated once per study.

Evidence tags: **FETCHED** (a source was opened on 2026-10-19 by the reference-check agent; URL given),
**RECALLED** (from memory or secondary summaries, not confirmed). Nothing here is investment advice.

## Common rules

| Item | Fixed choice |
|---|---|
| Returns | Daily log close-to-close returns |
| Fitting | Rolling window of the last 1,000 returns (about four years of stock sessions), refitted at every calendar-month start using only returns before the month began. The live code calls the same functions (`forecast_now`, `current_label`), and tests check that both give the same number |
| Development | Forecast origins whose whole target window ends by 2023-12-31 |
| Holdout | Origins from 2024-01-01; evaluated **once**, after the development result is recorded |
| Significance | One-sided Diebold–Mariano test on the loss differences, with Newey–West (Bartlett) variance. The lag count is Andrews' (1991) AR(1) plug-in bandwidth, and never fewer than 2h. Then the Harvey–Leybourne–Newbold small-sample factor, and a t distribution with T − 1 degrees of freedom. Bonferroni: 0.05 ÷ number of candidates. **Calibration (simulated before any real run):** the textbook h − 1 lags rejected 7–16% of true nulls at a nominal 5% when loss differences were persistent; this rule rejected 5–8%. So p-values remain slightly optimistic, which is one reason for the per-group rule below |
| Pooling | Done **per asset group** (stocks, crypto), because their calendars differ. Within a group, loss differences are averaged across assets per date and tested. A candidate passes only if it passes in **every** group present |
| Order | The development result must be recorded before the holdout runs (enforced in code) |

### Data sources

1. **`fred`** (no broker keys needed): daily closes from FRED.
   - NASDAQCOM, from 1971.
   - SP500 and DJIA: FRED shows only the last ten years.
   - CBBTCUSD (from 2014) and CBETHUSD (from 2016): Coinbase prices taken at 17:00 Pacific.
   - FETCHED from the series pages at https://fred.stlouisfed.org/series/<ID>.
   - Each provider prohibits reproduction, so the raw series stay in `JARVIS_HOME` and are never committed. Only the summary statistics below are recorded.
   - Index closes include no dividends; this matters little for volatility.
2. **`bars`**: the universe's Alpaca daily bars (`1Day-adjusted`), once the paper keys allow a backfill. This is the run that matters for the traded assets. It is a separate study (its own fingerprint and holdout).

## 1. Volatility forecaster (`model-study --kind volatility`)

- **Target:** the average daily variance of returns over the next h observations, forecast at the close of day t.
- **Primary horizon:** h = 5. Secondary horizons h = 1 and h = 21 are reported, but they do not decide anything.
- **Loss:** QLIKE in the form proxy/forecast + log(forecast), with squared returns as the noisy variance proxy. MSE is reported as well.
  - Patton (2011): MSE and QLIKE are the loss functions whose rankings are not distorted by a noisy but conditionally unbiased proxy. FETCHED: https://users.nber.org/~confer/2006/si2006/efww/patton.pdf

| Model | Rule | Evidence |
|---|---|---|
| `rolling20` **(baseline)** | Mean squared return of the last 20 observations | The workflow's named baseline |
| `ewma` | RiskMetrics exponentially weighted variance, decay 0.94 | FETCHED: RiskMetrics Technical Document (1996), Appendix C, which gives 0.94 as the daily decay |
| `har` | Variance-level HAR, fitted by OLS separately for each horizon. Regressors: the last squared return, the 5-day mean and the 22-day mean. A non-positive forecast is replaced by the 22-day mean | FETCHED: Corsi (2009), which uses 5- and 22-day averages and OLS. His baseline is in volatility (square-root) units, and squared daily returns here stand in for intraday realised variance, so this is a deliberate simplification |
| `garch` | GARCH(1,1) with zero mean, fitted by maximum likelihood on percent returns | FETCHED: Hansen & Lunde (2001 working paper), which found no model significantly better than GARCH(1,1) for exchange rates. In IBM data, models with a leverage effect did better |

**Pass rule:**
- A candidate passes when, in every asset group, its p-value is below 0.05 ÷ 3 and its mean QLIKE gain is positive.
- The **winner** is the passing candidate with the largest mean gain, averaged over groups. If none passes, the baseline wins.

**Use:**
- The winner's forecast sets position size for every strategy (`sizing="volatility"`):
  - notional = base notional × min(1.5, 1% ÷ forecast daily volatility).
  - A position therefore risks about 1% a day at the base size: less for volatile assets, up to 1.5× for calm ones, never above the owner's per-order cap. Quantities are rounded down.
- If there is no forecast, the entry is blocked rather than guessed.
- *Added 2026-10-19, after the model study but before any strategy run:* when the winner cannot be fitted yet (it
  needs 1,000 returns before the current month, about four years, and Alpaca history starts in 2016), the baseline
  `rolling20` sizes the order instead. Each order records `volatility_model_used`. This does not change any
  model-study rule or result.
- Volatility-managed exposure has improved risk-adjusted returns for equity factors:
  - FETCHED: Moreira & Muir (2017), NBER w22208.
  - RECALLED (secondary summaries of Harvey et al. 2018): tail risk and drawdowns fell across asset classes.
- **Amendment to the strategy register:** before any real-data strategy run, the strategies are evaluated with this sizing. This changes the fixed-dollar rule in `STRATEGY_REGISTER.md`, and is recorded there.

## 2. Regime detector (`model-study --kind regime`)

- **Target:** the log return over the next 21 observations.
- **Score:** Gaussian log score, using a mean and variance per regime label estimated from the training window's past targets (each training target ends before the first origin it is used for).
  - A label with fewer than 30 training targets uses the window's overall statistics.
  - A detector is useful only if knowing the label improves the forecast of what comes next.

| Detector | Rule |
|---|---|
| `none` (reference) | No regime: the window's overall mean and variance |
| `sma200` **(baseline)** | Close above or below its 200-observation average |
| `trend_vol` | `sma200` crossed with a volatility state (20-observation variance above or below its median over the last 252), giving four regimes |
| `hmm2` | Two-state Gaussian hidden Markov model, fitted by EM from a fixed starting point each month (so the live code reproduces it exactly), and read through the **forward filter only**. Smoothed probabilities use later data and so would be look-ahead. FETCHED (statsmodels documentation of the filter and the Kim smoother); the filtered-versus-smoothed point is RECALLED from Hamilton (1989) |
| `trend_vol_stress` (ablation) | `trend_vol`, plus a stress state when VIX ≥ 25, or when VIX ≥ VXV (term-structure inversion) |

**Pass rule:**
- A candidate (`trend_vol`, `hmm2`) passes if it beats **both** `sma200` and `none` in every asset group, with p below 0.05 ÷ 2 and a positive gain.
- `sma200` against `none` uses the same threshold, 0.05 ÷ 2.
- The winner is the passing candidate with the larger gain over `sma200`. If none passes:
  - `sma200` is kept only if it beats `none`;
  - otherwise the winner is `none`.

**Ablation (the workflow's "every signal must earn its place" rule):**
- The FRED stress signal is kept only if `trend_vol_stress` beats `trend_vol` at p < 0.05, positive in every group.
- This is judged on origins where VIX was known at decision time.
- **Timing:** VIX is treated as known at 22:00 UTC on its date.
  - Stock decisions are taken at 21:15 UTC, so they use the previous day's VIX.
  - Crypto decisions are taken at 01:15 UTC the next day.
- The thresholds (25, and a ratio of 1) are conventional rules of thumb, RECALLED, and fixed here before testing.

**Note:** much of any gain is expected to come from variance (calm against turbulent periods) rather than direction. That is still awareness, and the regime table in the output shows both. The real test of a regime's usefulness is Phase 7: whether choosing strategies by regime beats not choosing.

## 3. Correlation / risk model (`model-study --kind risk`)

- **Baseline (`diagonal`):** each asset's own variance with zero correlation. This is what per-asset caps implicitly assume: every position is an independent bet.
- **Candidates:**
  - `sample`: the sample covariance of the last 252 aligned returns.
  - `shrunk`: Ledoit & Wolf (2004) shrinkage toward the constant-correlation matrix, with their estimated optimal intensity. FETCHED: https://econ-papers.upf.edu/papers/691.pdf
  - This is written from the paper and the authors' code structure, because scikit-learn's `LedoitWolf` shrinks toward a scaled identity instead (FETCHED from the scikit-learn documentation).
- **Test:** every 21 observations, each estimator forecasts the daily variance of an equal-weight portfolio and of 50 seeded random long-only portfolios over the next 21 observations. Scored with QLIKE against the realised mean squared portfolio return.
- **Pass:** p < 0.05 ÷ 2 against `diagonal`. The winner is the candidate with the larger gain.
- **Reported, not decisive:** the realised volatility of the long-only minimum-variance portfolio built with each estimator, against 1/N. This is not the evaluation Ledoit & Wolf used: they measured tracking error against a benchmark.
- **Data caveat:** the `fred` source has only five closely linked series (three US indices and two cryptocurrencies), and only about ten years of overlap. It is a preliminary check; the `bars` run on the universe decides.
- **Use (Phase 8):** `portfolio_volatility()` gives the open book's forecast dollar volatility and a crowding ratio. The ratio is near 1 when positions diversify and near √n when they are one bet. The Governor will cap these once the model has passed on the universe.

## 4. Transaction-cost model (`cost-report`)

- **Baseline:** the replay's fixed costs (5 bps per side for stocks; 25 bps fee plus 5 bps spread for crypto).
- **Model:** half the quoted spread at decision time, plus the fee, plus square-root impact (coefficient 1 × daily volatility × √(order value ÷ daily traded value)). The impact law is RECALLED. The test below omits the impact term because daily traded value is not recorded yet; at orders of a few thousand dollars it is close to zero.
- **Test:** the mean absolute error of each prediction against realised implementation shortfall, measured from the **mid price** at decision time. Entries record the quote mid; exits use the last bar close. Fees are excluded from both. It needs at least 50 paper fills. Pass at p < 0.05.
- **Caveat:** for daily strategies the fill comes at the next open, so the shortfall includes the overnight move. It is noisy, and that noise is part of the honest cost.
- **Status:** BLOCKED until paper trading produces fills.

## 5. Situation signals (recorded every cycle, `SITUATION` journal event)

The signals are listed in `src/jarvis/awareness.py`:
- FRED stress;
- breadth across the universe's stocks;
- hours to FOMC, CPI and jobs releases;
- BTC minus ETH 20-day return;
- each asset's regime (runtime `regime_model`, default `trend_vol`) and forecast volatility (computed every daily cycle, also with fixed sizing);
- the desk's drawdown, open positions and gross exposure.

They are recorded so that later phases can test them point-in-time. None of them changes a decision until it passes a test like the stress ablation above.
- **Known gap:** breadth over 27 assets is thin. The workflow's broader breadth universe (for example S&P 500 members) needs more data, and today's membership lists carry survivorship bias.

## Results — `fred` source, study version 1.0.0, code 529c572 (2026-10-19)

The full records are in `JARVIS_HOME/research/model_studies.jsonl`: development entries 1–3, holdout entries 4–6, one
hash chain. "Gain" means the baseline's loss minus the candidate's (positive = candidate better), averaged per date
within a group. *n* is the number of forecast origins.

### Volatility (primary h = 5; threshold 0.0167)

| | Stocks (NASDAQCOM, SP500, DJIA) gain / p | Crypto (BTC, ETH) gain / p | Passed |
|---|---|---|---|
| **Development** (1975–2023 / 2017–2023; n = 12,330 / 2,277) | | | |
| `ewma` | 0.055 / 1.5e-13 | 0.198 / 0.0005 | yes |
| `har` | 0.001 / 0.49 | 0.250 / 0.0044 | no |
| `garch` | 0.073 / 1.3e-9 | 0.272 / 0.0010 | **yes, winner** |
| **Holdout** (2024-01 to 2026-10; n = 697 / 1,018) | | | |
| `ewma` | 0.049 / 0.045 | 0.125 / 0.0043 | no |
| `har` | 0.082 / 0.032 | 0.215 / 0.021 | no |
| `garch` | 0.087 / 0.013 | 0.204 / 0.024 | no (crypto p above 0.0167) |

- **Decision:** `garch`, per the pre-registered rule, which chooses the winner on development data. It sets position size.
- In the holdout, GARCH had a lower QLIKE than the baseline on **all five** series. That is significant for stocks, but not quite for crypto, on about a third of the development sample.
- **Gap in this register:** it did not say what a holdout shortfall means. It is recorded here as "consistent in direction, not significant in crypto", not as a pass.
- **Secondary horizons:**
  - h = 1: all three candidates passed in development.
  - h = 21: none passed in development, because crypto p-values were 0.04–0.06.
- HAR's weakness on stocks probably comes from using squared daily returns in place of intraday realised variance; the original HAR uses intraday data.

### Regime (h = 21; threshold 0.025)

| | Stocks gain / p | Crypto gain / p | Passed |
|---|---|---|---|
| **Development** | | | |
| `trend_vol` vs `sma200` | −0.050 / 1.0 | −0.056 / 0.97 | no |
| `hmm2` vs `sma200` | 0.038 / 0.011 | 0.010 / 0.36 | no |
| `hmm2` vs `none` | 0.030 / 0.07 | −0.020 / 0.87 | no |
| `sma200` vs `none` | −0.008 / 0.70 | −0.030 / 0.93 | no |
| stress ablation (`trend_vol_stress` vs `trend_vol`) | −0.001 / 0.52 | 0.021 / 0.20 | no |
| **Holdout**: no candidate and no ablation passed; `sma200` vs `none`: stocks 0.076 / 0.014, crypto −0.055 / 0.99 | | | |

- **Decision:** winner `none`, and the stress signal is **dropped**. This is a negative result: under this test, no detector improved the forecast of the next month's return distribution, in stocks and crypto together.
- **Likely cause:** each label's mean and variance are estimated from about 1,000 overlapping 21-day targets, which is only about a dozen independent months per label. The estimation noise costs more than the labels add.
- The regime table nevertheless shows large differences in what followed each regime. Examples:
  - NASDAQ "down_calm": −9% a year;
  - NASDAQ "up_calm": +12% a year at 16% volatility.
- Any redesign (a shorter horizon or a longer estimation window) is a new study version, and a new trial.
- Labels are still recorded each cycle. Phase 7 tests directly whether choosing strategies by regime beats not choosing.

### Correlation risk (threshold 0.025; preliminary, five closely linked series)

| | Gain over `diagonal` / p (development, 74 periods) | Holdout (32 periods) |
|---|---|---|
| `sample` | 0.203 / 0.094 | 0.214 / 0.0054 |
| `shrunk` | 0.201 / 0.096 | 0.214 / 0.0054 |

- **Decision:** `diagonal` (development did not reach significance). The holdout favours a correlation-aware model, and the gain was about the same size in both periods.
- The universe `bars` study decides; it is BLOCKED on Alpaca keys.
- Mean shrinkage intensity: 0.24.
- Reported only: the long-only minimum-variance portfolio had realised volatility of 19.9% (sample/shrunk) and 21.0% (diagonal), against 37.2% for equal weight (development).

## Results — `bars` source (the 27-stock/ETF universe, Alpaca daily bars 2016–2026), run 2026-10-20

Registry entries 7–9 (development) and 10–12 (holdout), with the same version and rules as the `fred` study. This is
the run that decides for the traded assets. All series are stocks/ETFs: crypto bars on Alpaca start only in 2021.

| Model | Development (origins from 2020 because of the 1,000-return window) | Holdout 2024-01 to 2026-10 | Decision |
|---|---|---|---|
| Volatility, h = 5 | `garch` gain 0.034, p = 0.013; `ewma` 0.032, p = 0.003; `har` −0.098 (worse) | `garch` 0.078, p = 1.2e-6; `har` and `ewma` also pass | **GARCH: confirmed on both sources and both splits** |
| Regime | No candidate beats `sma200` or `none` (best p = 0.23); stress ablation −0.024 | Nothing passes (best `hmm2` vs `none`, p = 0.09); stress −0.041 | **None**, as with `fred` |
| Correlation | `sample` gain 1.015, `shrunk` 1.010, both p = 0.033 (threshold 0.025); 83 periods | Both about 0.415, p = 0.049–0.050; 33 periods | **`diagonal` by the rule.** Every run improved the forecast and roughly halved minimum-variance volatility (development 5.9% vs 9.2%; holdout 4.6% vs 7.0%), but none reached the pre-registered significance |

**The correlation result is an open owner decision.**
- Using the correlation model only to cap total risk (a safety limit that can block trades, never add them) is a different use from the forecasting test here.
- Adopting it would be a decision taken knowingly after seeing these results. It is recorded here, not applied silently.

### Transaction costs

BLOCKED: there are no paper fills yet. `cost-report` reports INSUFFICIENT_DATA until 50 fills exist.

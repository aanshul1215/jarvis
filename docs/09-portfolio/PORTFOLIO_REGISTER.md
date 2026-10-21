# Portfolio system register (pre-registration)

Written 2026-10-20, **before the portfolio system was run on real market data.** It implements the owner's
decisions of 2026-10-20:
- improve the existing system rather than start over;
- add proven strategy families, including pairs trading;
- make it regime- and situation-aware, with a big-picture layer after Aschenbrenner, *Situational Awareness*, 2024;
- let it choose and blend strategies by situation;
- maximise profit within a 25% worst-drawdown limit;
- allow short selling with tight caps;
- add 11 ETFs;
- test with a three-way split.

Code: `src/jarvis/portfolio/`. Runs are logged in `JARVIS_HOME/research/portfolio_studies.jsonl`. Evidence tags:
**FETCHED** (opened by a research agent; see `docs/01-research`) and **RECALLED** (from memory, not re-opened).

## Architecture

Every strategy ("sleeve") outputs target weights for every asset, every day. An allocator decides how much of each
sleeve to run in the current situation. A risk overlay sizes and caps the result, and an executor trades the
difference from current holdings. Weights decided after a close trade at the next open. Nothing in a decision uses
a later price: tests truncate the data and require identical past decisions.

## Universe

38 stocks and ETFs (2016 onward) plus BTC and ETH (Alpaca history from 2021), in fixed groups:
- **Equity indexes:** SPY, QQQ, IWM, DIA, EFA, EEM.
- **Sectors and themes:** XLF, XLK, XLE, XLV, XLY, XLP, XLI, XLU, XLB, SMH, VNQ.
- **Single stocks:** AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, JPM, XOM, UNH.
- **Bonds:** TLT, IEF, SHY, TIP, HYG, LQD.
- **Commodities:** GLD, SLV, DBC, USO, CPER.

**Known bias:** the single stocks were chosen in 2026, which flatters any strategy that holds them. The benchmarks
hold them too.

**Costs:**
- Trading costs per side: 5 bps for stocks and ETFs, 15 bps for CPER (thinly traded), 30 bps for crypto.
- Shorts pay a 1% a year borrow fee.
- Crypto is never shorted.

## Sleeves (all included; the allocator decides how much of each to run)

Each sleeve is scaled to 10% annual volatility on its own, with gross exposure capped at 2.

| Sleeve | Rule | Evidence |
|---|---|---|
| `trend_xasset` | Average sign of the 3-, 6- and 12-month returns; inverse-volatility weighted; long or short | Moskowitz, Ooi & Pedersen 2012 (FETCHED, S01); Hurst, Ooi & Pedersen, *A Century of Evidence on Trend-Following* (RECALLED) |
| `xs_momentum` | Stocks and equity ETFs: long the top fifth by 12-1 month momentum, short the bottom fifth | Jegadeesh & Titman 1993 (RECALLED) |
| `low_volatility` | Long the least volatile third of stocks and equity ETFs | Ang, Hodrick, Xing & Zhang 2006; Frazzini & Pedersen 2014 (RECALLED) |
| `pairs` | 20 economically linked pairs (listed in `sleeves.PAIRS`). 252-day hedge ratio; enter at a 2-standard-deviation spread with a 1–30 day half-life; exit at 0.5, stop at 4 or after 20 days; market-neutral | Gatev, Goetzmann & Rouwenhorst 2006, profits declining after the early 2000s (RECALLED) |
| `news_sentiment` | FinBERT headline sentiment z ≥ 2 from 3+ headlines; hold 5 days | Tetlock 2007 (RECALLED) |
| `theme_ai_power` | Hold SMH, NVDA, XLU, XLB, CPER in proportion to the four hyperscalers' capital-spending growth (full at ≥ 40%), only while the basket leads SPY over 6 months | Owner's thesis (Aschenbrenner 2024). Untested |
| `trend_sma200`, `meanrev_rsi2`, `volatility_breakout`, `breakout_volume`, `relative_strength`, `earnings_drift` | The earlier library (`docs/06-strategies`) as weight sleeves | See that register |

## Situational awareness

Twelve features, each standardised with its own past only.
- **Market state:**
  - S&P trend and volatility shift;
  - VIX level and term structure;
  - high-yield vs Treasury performance and the Baa spread change;
  - 10-year yield change;
  - breadth;
  - dispersion;
  - crypto trend.
- **Big picture:**
  - the AI/power basket's 6-month lead over SPY;
  - the hyperscalers' capital-spending growth, from SEC filings and dated when public.

## Allocator (blend methods: the logged development trials)

`equal`, `recent` (6-month return per unit of variance), `regime` (by plain-language regime), and `situational`
(a ridge regression per sleeve, with α = the number of samples, predicting the next month's return from the
features).
- All but `equal` keep 50% on equal shares and may hold cash.
- Monthly refits use only completed sleeve returns.
- Two years of history are needed first.

## Risk overlay

- Target 15% annual volatility.
- Caps:
  - gross exposure 1.0, so no leverage (*amended 2026-10-20, before any real-data run: it was 1.5, but the owner's paper policy caps holdings at the $10,000 allocation*);
  - 30% per asset;
  - 20% crypto;
  - 30% shorts.
- Drawdown control: full size below 10%, falling to a quarter of size at 20%.
- Live: the Governor's own limits (allocated capital $10,000; per-order and per-asset caps; daily loss stop).

## Testing protocol

| Split | Period | Rule |
|---|---|---|
| Development | Decisions from 2017-01-01 to 2021-12-31 (2016 is warm-up) | All 4 blend methods run as trials. **Chosen:** the highest Sharpe after costs whose worst drawdown is within 25%. Also reported: the deflated Sharpe ratio (Bailey & López de Prado 2014, RECALLED) across the trials, and results with doubled costs |
| Confirmation | 2022-01-01 to 2023-12-31 (includes the 2022 bear market) | Once, for the chosen configuration. **Passes if:** Sharpe ≥ SPY's, worst drawdown within 25%, and total return above T-bills |
| Holdout | 2024-01-01 onward | Once, after the confirmation, with the same pass rule |

- Benchmarks: SPY, the equal-weight universe and 60/40 (SPY/IEF), all with the same execution model.
- **Development may iterate:** any change to a sleeve, feature or rule is logged as a new version and counted in the deflated Sharpe.
- **Confirmation and holdout cannot be re-run** for a configuration once used.

**Honest expectation:**
- The universe's single stocks and the 2017–2021 bull market make SPY a strong benchmark.
- The most likely benefit is a smoother path (diversification, trend's crisis protection, risk control) rather than a large return edge.
- Paper trading then provides out-of-sample evidence with real fills.

## Amendments before the first real-data run (2026-10-20, after an independent code review)

None of these was informed by results: no real-data portfolio run had happened.

1. **Drawdown control** uses only the equity known at the decision. The previous decision's return ends at the next open, so it is excluded. (Review finding: the first version peeked one overnight move ahead.)
2. **Pairs:** after a stop (|z| > 4) or a time exit (20 days), the same divergence is not traded again until the spread returns inside 2 standard deviations or flips sign. A hedge-ratio filter of 0.2–5 applies, and the half-life uses the AR(1) slope.
3. **Earnings drift (weight sleeve):** a release counts if it became public after the previous session's close and by this session's close. Friday-evening and weekend releases therefore count on Monday. The original `earnings-drift@1.0.0` strategy keeps its registered 25-hour window.
4. **The earlier library's ATR stop-losses are not part of the weight sleeves.** Exits come from each rule's own signal and maximum holding period. The portfolio-level drawdown control replaces per-trade stops.
5. **Capital spending:** quarters are derived from year-to-date filings (most companies report cash-flow items year-to-date), counted from the date each filing became public.
6. **Missing prices:** a position with no price at the next open is kept, not closed early because of data that appears later.
7. **Development selection:**
   - If no blend method stays within the 25% drawdown limit, nothing is chosen.
   - The deflated Sharpe counts every development trial ever logged.
   - The development returns end on 2021-12-31.
   - The once-only rule for confirmation and holdout is keyed on the system design (version, assets, sleeves, features), not on the data's end date.
8. **Executor:**
   - It cancels its own unfilled orders before each cycle.
   - A close buys or sells back exactly the position.
   - A long-to-short flip takes two cycles.
   - Adding risk is sized at the limit price.
   - A refused submission is recorded as rejected.
   - Shorts are checked against the broker's shortable list.
   - Crypto trades only if enabled.
   - The total-holdings and buying-power caps are checked.
9. **Daily routine:** the full adjusted price history is re-downloaded, so dividends and splits re-adjust every earlier price consistently.

## Round 1 development result (v1.0.0, registry entry 1, run 2026-10-20)

Chosen: `regime` blending.

| Method | Return / yr | Sharpe | Worst drawdown |
|---|---|---|---|
| `regime` (chosen) | 9.9% | 1.18 | −11.9% |
| `situational` | 10.2% | 1.18 | −12.1% |
| `equal` | 8.3% | 1.05 | — |
| `recent` | 9.1% | 1.04 | — |
| SPY | 18.1% | 1.05 | −32.0% |
| Equal-weight universe | 19.7% | 1.32 | — |
| 60/40 | 12.5% | 1.24 | — |

- Deflated Sharpe probability: 0.99, against zero (not against SPY).
- **Problems found:**
  - turnover was about 52× a year, which cost roughly 3% a year;
  - four sleeves had negative or zero Sharpe: pairs −1.33, meanrev_rsi2 −0.41, breakout_volume −0.10, xs_momentum 0.07;
  - with no leverage, realised volatility was about 8%, against the 15% target.
- Confirmation and holdout were **not** run for v1.0.0.

## Round 2 (v1.1.0), registered 2026-10-20 before its first run (owner decisions: learning ranker, 1.5× leverage)

1. **Learning ranker** (`portfolio/ranker.py`):
   - **Inputs**, per asset, every week:
     - all 12 sleeves' views of the asset;
     - the asset's own state (1/3/6/12-month returns, 12-1 momentum, forecast volatility, distance from the 200-day average, news sentiment and count, an earnings release in the last week);
     - the 12 situation features;
     - the asset's group.
   - **Target:** the next week's open-to-open return over forecast volatility, minus the cross-sectional mean.
   - **Model:** gradient-boosted trees (depth 3, learning rate 0.05, 200 iterations, at least 200 samples per leaf, L2 = 1).
   - **Training:** refitted every 4 weeks on completed weeks only; 104 weeks of history needed first.
   - **Weights:** long the top fifth, short the bottom fifth (never crypto), score over volatility, risk-scaled to 10%.
2. **Sleeves blended:** `trend_xasset`, `low_volatility`, `news_sentiment`, `theme_ai_power`, `trend_sma200`, `volatility_breakout`, `relative_strength`, `earnings_drift`, plus `learning_ranker`. Pairs, meanrev_rsi2, breakout_volume and xs_momentum are dropped from the blend after round 1, but the ranker still sees their signals.
3. **Weekly rebalance** on the first session of each week, traded at the next open. Between rebuilds, positions are cut immediately only if the drawdown control tightens.
4. **Gross exposure up to 1.5×**, with margin interest at 7% a year on long exposure above capital. The paper policy's holdings cap is $15,000 on the $10,000 allocation.
5. **Methods (trials):** `equal`, `recent`, `regime`, `situational`, and `ranker_only` (the ranker alone through the overlay). Selection and the deflated Sharpe follow the round 1 rule, and the deflated Sharpe counts round 1's 4 trials too.

## Round 2 development result (v1.1.0, run 2026-10-20)

- **Chosen:** `situational`: 14.9% a year, Sharpe 1.21, worst drawdown −15.9%, turnover 26.6× a year; 13.3% a year with doubled costs.
- **The learning ranker failed:** 2.2% a year on its own. Its predictions carried almost no information (IC +0.017).
- **Deflated Sharpe probability:** 0.96 over 9 trials.
- **Diagnostic (development only), why it took less risk than targeted:**
  - Realised volatility was 12%, against the 15% target.
  - The 1.5× gross cap bound on 87–93% of weekly rebuilds; the blend needed a median 2.1× to reach the target.
  - Volatility forecasts were not the cause: the ex-ante volatility of the final weights was 11%.
  - Turnover was 100% on rebuild days, driven by the learning ranker (83× a year on its own), volatility breakout (42×), news (32×) and cross-asset trend (26×).
- Confirmation and holdout were **not** run for v1.1.0.

## Round 3 (v1.2.0), registered 2026-10-20 before its first run

Owner decisions 2026-10-20: the revised ranker plan (`RANKER_DESIGN.md`) is approved; 2× leverage.

1. **Momentum ranker** (`portfolio/ranker.py`) replaces the learning ranker and `relative_strength`.
   - **Validation, before use** (registered at commit 5be2e02 and run once): French 49 industries, 1927–2015. Mean monthly IC +0.068, t = 8.1, positive in all 9 sub-periods. **Passed.**
   - **Eligible names:** the 17 equity ETFs, plus a single stock only while it was a US top-10 company by market value at the previous year-end (RECALLED list in the code).
   - **Score:** the average cross-sectional rank of the 3-month, 6-month and 12-1 month returns.
   - **Decisions:** at each month start.
     - **Sell** when a holding falls below 9th place, stops being eligible, or its 12-1 return turns negative.
     - **Buy** from the top 4 (12-1 return positive) up to 4 names: at most 2 new names a month (a full rebuild when nothing is held), and at most 2 names from the big-tech cluster.
   - **Weights:** 1 / volatility, fixed at entry; then risk-scaled to 10% like every sleeve.
   - **Never uses** the entry price or unrealised P&L.
2. **Sleeves blended:** `trend_xasset`, `low_volatility`, `news_sentiment`, `theme_ai_power`, `trend_sma200`, `volatility_breakout`, `earnings_drift`, and `momentum_ranker`.
3. **Gross exposure up to 2.0×.** The other caps are unchanged.
4. **Margin interest:** the 3-month T-bill rate known that day plus 3% a year, which is what was payable at the time. A flat 7% throughout is reported as a sensitivity.
5. **No-trade band:** skip a change smaller than 1% of capital or 20% of the target position, whichever is larger. A full exit is always allowed. The research simulation and the executor use the same rule.
6. **Deflated Sharpe:** counts at least 25 trials, a floor covering every look at the data so far.
7. **Methods (trials):** `equal`, `recent`, `regime`, `situational`, and `ranker_only` (the momentum ranker alone, through the overlay). Selection is unchanged: the highest development Sharpe within the 25% drawdown limit.
8. **Executor:**
   - It sizes buys against the broker's buying power, so margin is allowed; before, it used the smaller of buying power and cash.
   - The paper policy's holdings cap becomes $20,000 on the $10,000 allocation.
9. **Next:** if development chooses a configuration, its confirmation (2022–2023) and then its holdout (2024+) run once each, straight after, with the registered pass rule.

## Round 3 results (v1.2.0, run 2026-10-20)

**Development (2017–2021).**
- **Chosen:** `equal`: 18.2% a year, Sharpe 1.23, volatility 14.5%, worst drawdown −18.5%, turnover 23.7× a year.
  - With doubled costs: 16.6% a year.
  - With 7% margin throughout: 16.2% a year.
- **Other methods:** `situational` 17.6% / 1.20; `regime` 17.0% / 1.17; `recent` 14.9% / 1.04; `ranker_only` 13.6% / 0.98.
- **Benchmarks:** SPY 18.1% / 1.05 / −32.0%; equal-weight universe 19.7% / 1.32 / −26.2%; 60/40 12.5% / 1.24 / −18.7%.
- **Deflated Sharpe probability:** 0.96 (25 trials).
- **The risk gap is closed:** 14.5% realised volatility against the 15% target.

**Confirmation (2022–2023, run once): FAILED.**
- **System:** −5.1% total, Sharpe −0.17, worst drawdown −18.0%; −7.6% with doubled costs.
- **Benchmarks:**
  - SPY: +2.3%, Sharpe 0.16, −26.3%;
  - equal-weight universe: +5.2%;
  - 60/40: −3.2%;
  - T-bills: +7.2%.
- **Failed checks:** Sharpe ≥ SPY's, and beating T-bills.
- **Holdout:** **not run.** A configuration that failed confirmation does not spend the untouched 2024+ period.

**Post-mortem (2022–2023, looked at after the confirmation, so these periods are no longer clean for later versions):**
- **By year:** 2022 −13.2%, 2023 +9.2%.
- **Sleeves alone (CAGR):**

  | Sleeve | CAGR |
  |---|---|
  | `momentum_ranker` | +5.7% (Sharpe 0.59: the only sleeve beating SPY) |
  | `trend_sma200` | +0.5% |
  | `volatility_breakout` | +0.5% |
  | `low_volatility` | −0.7% |
  | `earnings_drift` | −3.8% |
  | `theme_ai_power` | −4.8% |
  | `news_sentiment` | −6.3% |
  | `trend_xasset` | −6.8% |

- **Cross-asset trend:** its bond shorts earned about +7% in 2022, but equity-sector whipsaw lost about as much. The 2023 reversal then cost it again.
- **Drawdown control lock-out:** the portfolio was more than 10% below its peak on 93% of 2023's days. So it ran at about 0.93× gross instead of about 1.6× through the 2023 rebound.
- **Margin was not a cause:** about 0.3% a year.

## Round 4 (v1.3.0), registered 2026-10-20 before its first run

**Owner decision:** fix the flaws, then judge once on the untouched 2024+ period; no paper trading until then.

**Honesty note.** These changes were made **after** seeing round 3's 2022–2023 confirmation. That period is therefore no longer a clean test. The decisive test is the holdout (2024-01-01 onward, never looked at by any version), followed by live paper trading.

1. **Drawdown control.**
   - The brake measures drawdown from the highest equity of the last 126 decisions (about six months), not from the all-time peak.
   - Same shape as before: full size below 10%, falling to a quarter of size at 20%.
   - **Why:** a brake keyed to the all-time peak keeps a recovering portfolio small for as long as it stays below its old high. Round 3 ran at about half size through all of 2023.
   - **Unchanged:** the live Governor's 25% stop from the all-time peak (the owner's limit).
   - **Live desk:** it keeps its own equity per decision day for the same rule.
2. **Cross-asset trend uses asset-class instruments only:** equity indexes, bonds, commodities, and crypto (long only), as in Moskowitz, Ooi & Pedersen 2012. Sectors and single stocks are left to the momentum ranker. (Round 3's sector trend whipsawed.)
3. **The momentum ranker gets a fixed 25% of the invested blend in every method except `ranker_only`.** It is the only sleeve validated on independent long history (French 49 industries, 1927–2015). The other sleeves share the remaining 75% in the method's proportions.
4. **No sleeve is removed.** On pre-2022 evidence every sleeve had a positive development Sharpe; removing round 3's 2022–2023 losers would fit the confirmation period.
5. **Everything else as round 3:** the same methods and selection rule, and the deflated Sharpe counting at least 25 trials.
6. **Sequence:**
   - development;
   - then the confirmation, run once **for the record only**, because it is contaminated and not a gate;
   - then the holdout, run once, as the decisive test. Its pass rule is unchanged: Sharpe ≥ SPY's, worst drawdown within 25%, and more than T-bills.
   - Paper trading starts only if the holdout passes, or if the owner decides otherwise after seeing it.

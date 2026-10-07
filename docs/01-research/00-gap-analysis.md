# 00 - Gap analysis across research briefs 01-17

Date: 2026-10-01. Inputs: CONTEXT_current_jarvis_and_vision.md (section C binding: US resident, $1,000-$10,000 own money, near-zero monthly budget for data + LLM, solo developer, Claude agents), the three owner design documents (Architecture v1, v2, Workflow v3), and the 17 briefs in this folder. Where a brief's "Independent verification" section corrects its body, the correction is used.

---

## 1. Contradictions between briefs (and which side is better supported)

1. **Pattern-day-trader (PDT) rule.** The verification sections of 01, 04, 07, 15 and 16 say a sub-$25k margin account is limited to 3 day trades per 5 days. Briefs 05, 11, 12, 17 and the verification sections of 08, 09 and 10 say FINRA Notice 26-10 (SEC-approved 14 Apr 2026) removed the PDT rule from 4 Jun 2026, with brokers allowed to phase in until 20 Oct 2027, and that Alpaca has already put the change live. **Better supported: repealed.** FINRA 26-10 was fetched and re-fetched, and Alpaca's own blog and changelog say it is implemented. Two caveats remain: other brokers may keep the old rule until Oct 2027, and how Alpaca treats accounts under $2,000 is still unclear (see item 2).
2. **Day trading in an Alpaca account under $2,000.** Brief 05 (from Alpaca's blog) says these accounts can day trade with no count limit at 1x. The verification sections of 11 and 12 say this is not documented, and that the "$2,000" on the intraday-margin page is a generic Reg T reference. **Unresolved.** Brief 05 is better on the $2,000 margin/short minimum (Alpaca's margin docs, confirmed). The "no limit at 1x" claim should be treated as unverified until tested in the account. It barely matters if the design is swing-horizon.
3. **Cash account versus margin account.** The verification sections of 12 and 15 suggest "consider a cash account". The verification section of 17 says a margin account is not advisable at small capital. Brief 05 and its verification state that Alpaca offers no cash accounts (all accounts are margin; IRA cash accounts are planned). **Better supported: Alpaca is margin-only.** The control has to be a deterministic leverage cap of 1.0 and shorting switched off in the risk gate, not the account type.
4. **Coinbase Advanced entry-tier fees.** The four briefs give three different figures, all second-hand because the official page returned 403:
   - 0.50% / 0.90% (07 verification, 11), effective 2026-09-16 according to securities.io;
   - 0.60% / 1.20% (17);
   - 0.40% / 0.60% for new users (17 verification; 05 lists both ranges).

   **Somewhat better supported: 0.50% / 0.90%,** because it is a dated report of the September 2026 change cited by two briefs. Every reading is 2-4x Alpaca's 0.15% / 0.25%, so the decision (do not trade crypto on Coinbase at this size) does not depend on which is right. Read the actual tier from the logged-in account before any cost model is frozen.
5. **Adopting a trading engine versus building a thin one.** The body of brief 04 recommends adopting NautilusTrader, or LEAN as the fallback, and says "do not build". Brief 04's own verification, brief 14 and brief 03 point the other way:
   - Nautilus has no Alpaca adapter, and the adapter PR was closed for lack of maintainer capacity.
   - Nautilus 2.0 exists only as release candidates with breaking changes.
   - LEAN's CLI requires a paid QuantConnect tier.
   - At $1k-$10k a thin custom executor running on daily bars over Alpaca is defensible.

   **Better supported under the owner constraints: a thin custom executor** (a single process plus an explicit state machine), with 04's one-to-two-week spike kept as the way to confirm it. Nobody has run that spike.
6. **Where the control-plane state lives.** Briefs 03 and 17 call for a PostgreSQL state table or intent table, optionally with DBOS on Postgres. Brief 14 calls for SQLite in WAL mode with one writer, moving to Postgres only when a second writer appears. **Better supported: brief 14,** because there is one process on one host and DBOS uses SQLite by default. This is low-stakes: the intent-before-broker-call pattern from 17 works on either database.
7. **Docker Compose on the Windows laptop.** Brief 04 calls it "supported" because the engines ship Docker images. Brief 14 says to defer Docker on Windows: Docker Desktop needs 8 GB of RAM and WSL2 takes up to 50% of host memory. **Better supported: brief 14,** unless a containerised engine is adopted, which item 5 argues against.
8. **Minimum cacheable prompt prefix on Haiku 4.5.** Brief 03's verification says 4,096 tokens. Brief 13 states the same figure, but its verification calls it unverifiable. **Moderately supported: 4,096.** The consequence is that short Haiku extraction prompts get no cache discount, so cost estimates for Haiku should assume no caching.
9. **Monthly LLM cost.** The estimates differ because the workloads differ:
   - 03: about $135-260 a month for 50 candidates a day with 6 agents each;
   - 11: about $15-30 for 5 evaluations a day, about $1.50-3 for one daily batch;
   - 13: about $11 a month for a shortlist plus reviews, range $5-25, versus $98 to $57k for per-candidate designs;
   - 16: about $2-4 a month for 200 headlines a day on Haiku.

   These are consistent once the workload is fixed. All of them agree that LLM calls on every candidate are incompatible with the budget, and that a deterministic shortlist plus Batch API design costs single-digit to low-double-digit dollars a month.
10. **Whether LLM look-ahead bias can be removed.** Lopez-Lira, Tang and Zhu (cited in 01, 08 and 13) find that masking and date instructions fail. Glasserman and Lin (01, 13, 16) find anonymisation helps and that look-ahead was not an issue out of sample. He et al. (16) find the bias "modest" for next-day news. **Better supported for design: the cautious reading.** No brief shows a reliable fix. Only forward evidence collected after the model's training cutoff is admissible. Anonymisation can be run as an A/B arm, but it is not a cure.
11. **Whether the Strategy Lab is the best use of an LLM.** Briefs 01 and 02 call the offline Strategy Lab (Layer D) the best use of an LLM. Brief 08 and brief 02's verification cite Gençay (2026): with leakage-proof tools and deflation by the actual trial count, every LLM-discovered strategy was rejected. Brief 13 adds that an LLM's hypotheses are already mined from the history it was trained on. **Both hold:** it is the safest LLM role, but expect very low yield, and it is only valid with a trial registry, deflation and leakage-proof data.
12. **Using a different model as the critic.** Brief 02 recommends a different model family for the red-team critic (heterogeneity helps). Brief 02's verification notes this conflicts with the owner's Claude-only intent, and that the heterogeneity result was measured inside debate frameworks, not for a single critic call. **Treat as untested.**
13. **Survivorship-free equity data.** Brief 06 makes a survivorship-free universe (Norgate Platinum, $630 a year) a "hard precondition" for validating any equity model. Brief 06's verification says that is a 6-63% annual drag at $1k-$10k, and to buy only after a paper edge exists. Brief 09 recommends cross-sectional stock momentum, which needs exactly that data. **Not reconciled by any brief.** The way out: start with a fixed ETF universe plus BTC/ETH, where survivorship bias is minor, and defer single-stock cross-sectional strategies until the data purchase can be justified.
14. **Gradient boosting by default.** The body of brief 15 recommends LightGBM as the default model. Brief 15's verification says boosting lagged in the volatility study (Christensen et al.), so LightGBM is not supported for volatility: HAR or GJR-GARCH first. **Better supported: the verification** for volatility. Boosting remains the right default for return or outcome classification on tabular data.
15. **Sizing versus protective stops.** Brief 10 sizes so the loss at the stop is at most 0.25-0.5% of equity. At $1k-$10k that is $2.50-$50 at risk per trade, which usually means fractional positions. Briefs 13 and 17 note that Alpaca fractional orders are DAY-only, so no protective stop can rest at the broker overnight. **Unreconciled.** It needs a design decision: whole shares for anything held overnight, or explicit acceptance that the position depends on the local process staying up.

---

## 2. Decisions the redesign must make that no brief answers adequately

- **The owner's US state.** It decides whether Alpaca crypto is available (old lists exclude NY, possibly AZ), whether Binance.US is (licensed in 32 states), and whether Coinbase is usable. It is the first gate on the crypto sleeve. The state lists in 05, 11 and 14 are a year old or partial.
- **The owner's hardware spec.** With 8 GB of RAM, even the lean stack is constrained and Docker is not viable. No brief could size this.
- **After-tax comparison with buy-and-hold.** Several briefs say the benchmark is buy-and-hold after costs and tax, and that trend and swing gains are short-term (ordinary income) while buy-and-hold defers tax. **No brief computes the after-tax drag** of a vol-targeted trend or momentum sleeve against a static ETF+BTC allocation in a taxable account. Nor does any brief check whether a tax-advantaged account (an IRA at Alpaca or elsewhere) is available for automated trading. This decides whether JARVIS can beat its own benchmark at all.
- **Net-of-cost performance of the recommended first strategies.** No brief computes the expected turnover and net-of-fee result of:
  - vol-targeted crypto trend at Alpaca's 0.50% taker round trip (the Zarattini cost assumptions are unknown);
  - ETF trend with monthly rebalancing;
  - the opportunistic Form 4 overlay after costs.

  Post-2012 decay of the insider signal, post-2014 decay of Lazy Prices, post-May-2024 decay of LLM headline drift and post-2022 decay of crypto trend are all unverified.
- **Whether Alpaca's free plan includes the news API.** Brief 16's verification could not establish it. The whole Information Intelligence layer at $0 depends on this or on an alternative free feed with publish timestamps.
- **Promotion gates a low-turnover strategy can actually pass.** Brief 08 asks for about 300 independent trade clusters and DSR of at least 0.95. Brief 10 asks for a few hundred outcomes before calibration. A monthly ETF/BTC trend book generates tens of decisions a year, so these gates may never be passable from paper data. No brief designs a gate suited to slow strategies: one that relies on long deflated backtests, non-falsification in paper, then minimum-size live.
- **The evaluation horizon for LLM features versus model retirement.** Forward-only evidence for a Claude model starts after its cutoff (July 2026 for the 5.5 models). Models retire roughly yearly. Brief 02's verification says the ablation needs hundreds of scored decisions. No brief checks whether an LLM feature can ever gather enough post-cutoff evidence before its model is replaced, or what a "model-change re-validation" period should be.
- **Whether the design runs with the LLM off.** Brief 13's verification notes that a $0 budget may mean no API credit at all. The redesign must decide whether the core system has zero LLM dependency, with the LLM only an optional ablation arm. No brief specifies what is lost.
- **Using a Claude subscription for the offline Strategy Lab.** Brief 03's verification says plan users can run the Agent SDK, drawing on plan limits, but the credit change is "paused" and the source is a summary. The current terms need a first-hand read before the design relies on it.
- **Haiku 4.5 successor and cost.** Haiku 4.5's not-before retirement date is 2026-10-15 and no successor Haiku is listed. The cost plan may need to move to Sonnet 5.5 at roughly 2-2.5x per extraction.
- **Laptop or VPS, and the dead-man's switch.** There are no measured uptime figures. Free dead-man's-switch services, Windows auto-start (Task Scheduler or a service wrapper), and whether a US VPS IP causes any issue with Alpaca or Coinbase were not evaluated. The Oracle free tier carries an idle-reclaim risk.
- **Alpaca behaviours that only a test can settle:**
  - the response to a duplicate `client_order_id`;
  - whether the websocket replays missed events after a reconnect;
  - whether paper accounts enforce the new intraday-margin checks;
  - the typical spread on Alpaca's own crypto venue;
  - whether the cancel/replace race still occurs live;
  - the terms of the customer agreement (unreadable in every brief).
- **Numeric risk-gate parameters for $1k-$10k:** risk per trade, DD_max, daily loss, per-order notional caps. Briefs 10 and 12 give only engineering judgement. Minimum order sizes, fractional-share rules and penny-rounded fees interact with these and have not been worked through.
- **Crypto tax treatment.** Whether crypto wash-sale legislation (H.R. 9172) has been enacted, and the details of 1099-DA reporting, are unverified. Needs a tax professional.
- **What v1 ingestion code is worth salvaging.** No brief audited the v1 code itself. Brief 16 says rebuild, but nobody checked which ingestion functions (EDGAR, technicals) are reusable once the key is rotated.
- **Effective trial count N for correlated LLM-generated variants** (brief 08 open item). There is no agreed method, and the DSR/PBO formulas were recalled, not read from the papers.
- **Data licences for remote viewing.** Alpaca, Tiingo and Massive licences were not checked for a remotely viewed personal dashboard, as opposed to one viewed on the same machine.

---

## 3. Weak briefs

- **09 (where is the edge)** is the most decision-critical brief and among the most thinly sourced:
  - Many core numbers are search-snippet only: McLean-Pontiff, Novy-Marx-Velikov, Jensen-Kelly-Pedersen, Avramov et al., Huang et al., Moskowitz et al., Cookson et al., Ke-Kelly-Xiu, Wiecki et al. Its verification left most of them unverified.
  - The crypto-trend recommendation rests on one non-peer-reviewed working paper, read from the authors' own summary page, with cost assumptions not visible.
  - The planning range of Sharpe 0.3-0.7 is the author's judgement.
  - Its negative conclusions are well corroborated by other briefs. Its positive strategy list is not evidence-grade.
- **08 (backtest validity)**: the DSR, MinBTL, PBO/CSCV and CPCV formulas are recalled, because SSRN was blocked and the PDFs were unreadable. Every pass threshold is a design choice. The arithmetic was verified. The formulas must be checked against the papers before they are coded.
- **15 (statistical/ML models)**: mostly abstract-level reading. The AFML concepts and the Gu-Kelly-Xiu R-squared figures are recalled. The body's "LightGBM by default" was overturned for volatility. The RL survey was never opened. The HMM-leakage point is solid because the library docs were fetched.
- **17 (execution/positions)**: the exit-rule evidence comes from abstracts and CXO practitioner summaries, all on US equities at daily-to-monthly horizons, with nothing on crypto or intraday. Its Coinbase fee figure was wrong, and the Han-Zhou-Zhu stop level and figures were corrected. The broker-mechanics half is strong.
- **04 (engine build vs adopt)**: careful as a feature survey, but its recommendation ignores the budget and capital constraints (its own verification says so). It never ran the spike it recommends, and its primary pick lacks an adapter for the owner's likely broker.
- **16 (news intelligence)**: the Cohen-Malloy-Pomorski, Lazy Prices and Tetlock figures are snippet or recall. Free availability of Alpaca news is unconfirmed. Post-2024 decay is unknown. The Lopez-Lira-Tang and EDGAR facts are strong.
- **05 (brokers)**: about a third of the brief (the India section) does not apply to a US resident. The Coinbase and IBKR fees and IBKR's implementation of the PDT change are unverified. The Alpaca facts are strong.
- **Weak in part:**
  - 10: Harvey et al., Grossman-Zhou, Chopra-Ziemba and the meta-labelling evidence are snippet-level or simulation-based.
  - 07: the La Morgia precision/recall figures were not visible in the primary text.
  - 14: the Hetzner monthly prices are unverified, and the reliability argument rests on mechanisms rather than statistics.
- **Strongest:** 01, 02, 03, 11, 12, 13, 06. These are primary-source heavy and most claims were re-confirmed.

---

## 4. Top evidence-backed conclusions (stated for a US resident, $1k-$10k, near-$0 budget)

1. **No LLM trading agent has been shown to beat buy-and-hold net of costs** on a multi-year, multi-symbol sample after the model's training cutoff. Each test found the edge gone or statistically insignificant:
   - FINSABER: FinMem and FinAgent, 20 years, no significant alpha.
   - StockBench: differences within noise.
   - CLQT: agents do not cleanly beat the index net of costs.
   - A cost-inclusive re-test of TradingAgents: Sharpe 0.43 gross, 0.22 net.

   Keep LLMs out of LONG/FLAT selection and sizing. (01, 02, 08)
2. **Any LLM-in-the-loop backtest over data before the model's cutoff is contaminated.** Date instructions and masking do not reliably fix it. For Claude 5.5 models (cutoff June 2026), clean evidence exists only from July 2026 onward and must be gathered in forward shadow mode, restarting whenever the model ID changes. (01, 08, 13, 16)
3. **More agents, or bull/bear debate, do not reliably beat one well-prompted call or self-consistency.**
   - Multi-agent costs 3-15x the tokens.
   - It is worse on sequential tasks (-39% to -70%).
   - It fails 41-87% of the time, mostly for design and verification reasons.

   About 13 of the 18 v3 "agents" should be deterministic code or statistical models. The genuine LLM roles are news/filing extraction, offline research, an optional single red-team call, and narrative reporting. (02, 03)
4. **LLM-stated confidence is not a usable probability.** Verbal confidence clusters at 80-100%, and GPT-4's failure-prediction AUROC was about 0.63. A weighted average of distinct calibrated forecasts is itself uncalibrated (Ranjan-Gneiting). Use one outcome model trained on out-of-sample results. Data quality and execution are gates and costs, not confidences, and LLM confidence enters only as a feature with zero default weight. (10, 01, 02)
5. **Liquid US equities and ETFs are 10-40x cheaper to trade than crypto at the owner's size.**

   | Venue | Round-trip cost |
   |---|---|
   | Alpaca equities | about 0.03-0.10% |
   | Alpaca crypto (tier 1, 0.15% maker / 0.25% taker) | 0.50% as taker |
   | Kraken Pro | 1.6% |
   | Coinbase Advanced (second-hand) | about 1.8% |

   Percentage fees do not shrink at $1k-$10k, because 30-day volume never leaves tier 1. (11, 07, 09, 17)
6. **The owner's worked examples do not survive real costs.**
   - The "+$0.27 after costs" is essentially the gross figure; at Alpaca it is about $0.15 before spread.
   - Breaking even on the 2:1 payoff needs a 55% hit rate as an Alpaca taker, and is impossible at Kraken or Coinbase entry tiers.
   - Read as a calibrated probability, "72% confidence" implies about 72x Kelly leverage and +0.93% expected value per trade.
   - The $25 ETH position is below Kraken's 0.01 ETH minimum.

   (11, 10, 09, 17)
7. **Order-flow / L2 signals are not a retail alpha source.** Order-flow imbalance explains price moves at the same instant. Its forecasting power lasts about two price changes, and one-minute-ahead R-squared is negative. Alpaca equity data has no L2 at any tier, and historical crypto L2 costs at least $350 a month or months of self-recording. Keep only a deterministic liquidity and cost monitor, and drop intraday crypto. (07, 06, 09)
8. **Free data supports daily-to-monthly strategies only.**
   - Alpaca Basic: real-time IEX only (about 2.5% of volume), 30 websocket symbols, 200 calls a minute, SIP history older than 15 minutes back to about 2016.
   - The $99/month SIP plan is 12-120% a year of $1k-$10k capital.
   - Free sources with sound timestamps: EDGAR (keyless, under 1 s, 10 requests/s) and FRED/ALFRED vintages.

   (06, 05, 16)
9. **Fixed monthly costs dominate at this capital.** Keeping drag under 2% a year needs capital of at least 600x the monthly bill, so a $3-5/month LLM budget implies at least $2,000-3,000. Calling the LLM per candidate costs $100 to thousands a month. A deterministic shortlist plus Batch API design costs about $5-25 a month. The system must also run with the LLM switched off, and the console spend limit must be set. (11, 13, 03)
10. **At $1k-$10k the design is long/flat.**
    - Alpaca spot crypto cannot be shorted or margined.
    - Equity shorting needs at least $2,000 of equity and whole shares; fractional shares cannot be shorted.
    - The PDT rule is repealed (effective 2026-06-04, implemented at Alpaca), so PDT counting logic should go. Intraday-margin rejections must be handled instead, and the leverage cap fixed at 1.0.

    (05, 11, 12, 17)
11. **Published edges are small, and backtests barely predict live results.**
    - The average anomaly earns about 8 bps a month net in the post-2000s, before price impact.
    - Returns fall 26% out of sample and 58% after publication.
    - Across 888 Quantopian algorithms, backtest Sharpe explained less than 2.5% of the variance in out-of-sample Sharpe (R² < 0.025).

    Plan for a net Sharpe of 0.3-0.7 at best, and treat Sharpe above 3 or next-day accuracy above 55-60% as a leakage alarm. (09, 08, 15; partly snippet-grade, but consistent)
12. **Statistical power is the binding validation limit.**
    - A 3-month paper run has a Sharpe standard error of about 2.
    - A 55% win rate needs about 270 independent trades to confirm at 95%.
    - Pinning a "72%" bucket to plus or minus 5 points needs about 310 outcomes.
    - 1,000 skill-less variants tested on 2 years of data produce a best Sharpe of about 2.3 by chance.

    Paper trading is a plumbing and cost test, not proof. An append-only trial registry with deflation by trial count is mandatory. (08, 10; arithmetic re-verified)
13. **Alpaca paper trading overstates results.** It has no market impact, queue position, latency slippage, fees or dividends; there is no NBBO size check; partial fills are random (10%). Add pessimistic fills, set the paper balance to the real capital, and insert a micro-live stage to measure real slippage. (04, 05, 08, 17)
14. **The hard risk gate needs the erroneous-order family, not only financial limits.** That means per-order notional and quantity caps, price collars, duplicate detection with deterministic `client_order_id`, rate throttles, self-cross guards, broker reconciliation at start-up and on a timer, an independent kill switch, and a dead-man's switch. These come from the Knight and Citigroup post-mortems; Rule 15c3-5 and FINRA 15-09 serve as voluntary engineering models. (12, 17)
15. **Broker-side protection is limited.**
    - Alpaca crypto has no bracket or OCO orders, only stop-limit with GTC/IOC.
    - Fractional equity orders are DAY-only, so there is no resting overnight stop.
    - Equities have no stops in extended hours.

    Exits written in JARVIS fail if the host dies. Use whole shares where a resting stop is required, size unprotectable positions smaller, and reconcile before managing positions on restart. (13, 14, 17)
16. **Exits must be pre-registered per strategy.** Stops help momentum and trend at best, hurt mean reversion, and tight stops lose to costs in every cost-inclusive study. Trading costs argue for partial adjustment toward a new target, not full exits on signal wobble. The "confidence fell, exit" rule is untested and noisy. (17, 10)
17. **LLM reproducibility means record-and-replay.**
    - Sampling parameters return a 400 error on 4.7+ models.
    - Models retire with 60 days' notice.
    - Structured outputs are GA but can break on refusal or max_tokens, and do not enforce numeric minimum/maximum.

    Store the full request and response, model ID, prompt hash and usage. Validate ranges in Pydantic, and fail closed to FLAT. (03, 13)
18. **A lean single-process stack is enough, and safer.**
    - MinIO's community edition was archived in April 2026.
    - Feast is unnecessary (as-of joins in DuckDB or Polars do the same job) and would not have caught v1's label leak.
    - NATS core does not persist messages.
    - Windows forces update restarts and sleeps.

    Use SQLite WAL, Parquet, one asyncio process, Streamlit and email. Move 24/7 live trading to a $6-12/month VPS when needed. (14)
19. **Model choices that avoid the leaks, and drop what cannot be validated.**
    - The default hmmlearn and smoothed statsmodels regime outputs leak future data; use filtered probabilities refit walk-forward, or rule-based regimes.
    - For volatility, use HAR or asymmetric fat-tailed GARCH, as a sizing input.
    - Jump tests detect jumps; they do not forecast continuation.
    - Remove RL from the roadmap.
    - Nothing can be validated on v1's 123 rows.

    (15)
20. **Rebuild the news layer as a risk filter and an archive, not an alpha engine.**
    - LLM headline drift is small-cap, needs shorting, survives only at 5-10 bps costs, and has decayed (Sharpe 6.54 in 2021 Q4 down to 1.22 in 2024).
    - FinBERT tone is weak for return prediction.
    - Use EDGAR acceptance timestamps and 8-K items for gating, and opportunistic Form 4 buys as a slow overlay.
    - Sanitise all text: homoglyphs broke ticker mapping on 99.1% of manipulated headlines, and hidden HTML flipped sentiment on 65.6%.
    - Bound how far text can move position size.
    - Start archiving first-seen timestamps now.

    (16, 13, 09)

Also well supported, but not decision-driving: own-money-only trading does not trigger investment-adviser registration. Adding outside money, managing others' accounts, distributing signals or showing performance to prospects would change that, and data licences are individual-use. (12, 06)

---

## 5. Owner-document ideas: which survive and which do not

### Survive (supported as written, or with minor tightening)

- **"Never chase a return target; FLAT is a valid decision"; compounding capped by risk budgets; never increase size because a target was missed.** Every cost and edge brief supports this (09, 11).
- **"Agents may reason; deterministic rules hold the money; no LLM override."** Strongly supported (01, 02, 03, 12, 13).
- **v3 "Agents produce structured evidence; they do not directly send broker orders."** Supported; structured outputs are GA (03, 13).
- **Hard Risk Gate (Layer G) as a deterministic veto with a kill switch.** Supported. Add the erroneous-order controls, reconciliation and dead-man's switch (12, 17).
- **Capital Governor using volatility targeting, drawdown limits and optional fractional Kelly.** Supported with qualifications (10):
  - volatility targeting as a risk stabiliser, not a return source;
  - Kelly as a shrunk upper bound, switched on only after a few hundred outcomes;
  - risk of ruin explicitly defined.
- **v1 decision rule "upside x probability > loss + costs + risk penalty".** Right form. It needs a probability-weighted loss, real venue fee tables and a k-times-cost hurdle, becoming a Cost Gate (10, 11).
- **Strategy Lab: the LLM proposes, validation decides; ideas cannot go straight to capital.** Supported in direction (01, 02), but only with a trial registry, deflated Sharpe/PBO, leakage-proof data and low expected yield (08).
- **v3 step 1: freeze data contracts first, with event time versus ingestion time and replay IDs. Point-in-time features.** Strongly supported (06, 14, 16), extended to bitemporal `available_at` columns.
- **v3 step 3: the same code path for backtest and live.** Supported (04, 14).
- **v3 step 5 before step 6 (models and walk-forward evaluation before agents).** Supported. Move agents further still, after paper trading of the non-LLM pipeline (02).
- **Data Trust Gate / SAFE state on stale or untrusted data; cross-venue sanity checks.** Supported, since feeds drop messages (14, 07). Add reconciliation on start.
- **Idempotent order service.** Supported and essential (03, 12, 17).
- **Ledger / Layer I with model, feature and prompt versions, thesis, fills, exit reason and attribution.** Supported. Store full LLM requests and responses, the fee asset, wash-sale flags and holding period (03, 11, 13).
- **v1 research anchor that "paper does not simulate impact, queue position or latency slippage".** Supported, and understated (04, 05, 17).
- **v3 implementation note: "query the broker's current rules rather than assume them".** Strongly supported; the PDT rule changed in June 2026 (05, 12).
- **Paper -> shadow -> small live by predefined gates; staged capital increases; human approval for paper-to-live and for new strategies or models.** Supported (08, 12). Implement approvals as pending rows that expire to reject, and add a micro-live stage.
- **Volatility models (GARCH) in the model set.** Supported, as HAR or GJR/EGARCH with Student-t errors, used for sizing (15).
- **"XGBoost/LightGBM; DL only where justified"** for outcome models. Supported (15).
- **"RL later and sandboxed".** Supported; better still, removed (15).
- **Form 4 insider signal as a slow overlay (opportunistic trades only), and 13F as slow positioning context.** Supported (09, 16).
- **FRED/ALFRED vintages and SEC EDGAR as data sources.** Supported; free and point-in-time (06, 16).
- **Manipulation stance: "never claims a crime; integrity red flag; lower confidence or block"**, plus low-liquidity pump and burst detection and cross-venue divergence checks. Supported, as a defensive filter only (07).
- **"Small capital can be dominated by fees/spreads".** Supported and understated; it should become a quantitative gate (11).
- **De-duplication of news.** Supported; extend it to a scored novelty feature (16).
- **v3's LangAlpha caveat.** Verified accurate (01).
- **Daily summary, email alerts and a dashboard**, as personal owner outputs (Streamlit + email; narrative generated by a batch LLM job from the ledger). Supported (02, 14).

### Do not survive (contradicted, or impractical under the owner constraints)

- **All three worked examples ($100 BTC/ETH intraday order-flow trades, "+$0.27 after costs", "costs are small", confidence 72/82/79%).**
  - Costs are 33-113% of the expected upside.
  - The net figure is essentially the gross figure.
  - The confidence numbers imply absurd Kelly leverage.
  - The $25 ETH position is below Kraken's minimum.

  (09, 10, 11, 17)
- **Flow/Microstructure Agent as an alpha source; order-book imbalance in the Opportunity Scanner; order-flow models in the ensemble.**
  - Order-flow imbalance forecasts only seconds ahead, below retail fees.
  - There is no equity L2 data.
  - Crypto L2 history is unaffordable.

  Keep it only as a liquidity and cost monitor (07, 06).
- **Manipulation Surveillance detecting spoofing, layering, wash trades, momentum ignition and cancel-to-trade behaviour.** These are defined by intent and identity, and need participant-attributed data the public cannot access (07).
- **The 18-agent roster under a LangGraph LLM supervisor, with agents evaluating every candidate.** No evidence of benefit, 3-15x the tokens, and hundreds to thousands of dollars a month in calls versus a near-zero budget. Use a code state machine plus 3-5 LLM workflow steps off the order path (02, 03, 13).
- **Bull/Bear debate agents on candidates.** Same model, same evidence: the weakest debate configuration studied. The different-model heterogeneity fix is unavailable with Claude-only. At most, one optional red-team call, kept only if it passes an ablation test (02).
- **Confidence Calibrator combining Signal/Data/Model/Thesis/Execution into a calibrated "Overall" score.** No such pooled score can be calibrated (Ranjan-Gneiting), and data and execution are not outcome probabilities (10).
- **LLM "thesis confidence" as a calibrator input.** It is overconfident, varies from run to run, and cannot be calibrated before the cutoff. Default weight zero (01, 10).
- **Position Manager continuously recomputing confidence and exiting when it falls.** A threshold on a noisy score, with no evidence, higher turnover, and an LLM/API dependency in the exit path. Replace with pre-registered, per-strategy deterministic exits and broker-resting catastrophe stops (17, 13).
- **LONG/SHORT/FLAT across equities and crypto.** Not available at this capital: there is no crypto shorting at Alpaca, and equity shorting needs at least $2,000 and whole shares. The design is long/flat (05, 11, 17).
- **Multi-horizon scope (intraday to long-term) from day one, and an "always-on" scanner across equities and crypto.** Free data is IEX-only with a 30-symbol cap, and intraday trading is fee-negative. Start with daily-to-monthly strategies on a small ETF + BTC/ETH universe (06, 09, 11).
- **Live equity trades, quotes and L2 order books; v2 "Live trades/quotes/L2".** Unavailable or unaffordable (06).
- **Alpaca + Coinbase as a dual broker/feed stack, and a "second broker for redundancy".**
  - Coinbase entry-tier fees are about 3-4x Alpaca's.
  - Splitting volume keeps both accounts in the worst fee tier.
  - The Coinbase and Kraken public feeds remain useful as free data cross-checks.

  (11, 07)
- **"Wrap current JARVIS as the Information Intelligence service; do not restart".**
  - v1 has target leakage, a committed API key and zeroed SEC/social features.
  - Its dataset is 123 rows for one ticker.
  - The claimed Chroma/RAG, de-duplication and ticker-mapping features are not in the published Space.

  Rebuild; only the ideas survive (16, 13, context).
- **News-impact model and FinBERT-on-10-K as a return predictor; Reddit/Electrek social sentiment; event-study CAR as a feature.**
  - FinBERT is weak for return prediction.
  - Social sentiment is attention-driven and the main pump surface.
  - CAR joined to the filing date is direct leakage.

  (16, 09)
- **HMM regime model as presented, and "jump model says continuation is plausible".** Default library outputs leak future data, and jump tests detect jumps rather than predict them (15).
- **A many-model ensemble (jump, return distribution, HMM, GARCH, anomaly, relative value, news impact) built at once.** A multiple-testing and overfitting risk, and nothing can be validated on the existing data. Build sequentially behind baselines (15, 08).
- **TradingAgents cited as research evidence.** Its performance rests on a three-month, cost-free window. A cost-inclusive re-test gives Sharpe 0.22 net. Keep it as an engineering-pattern reference only (01, 02).
- **Local stack:**
  - Redis Streams/NATS bus, Redis hot state, PostgreSQL+TimescaleDB, Parquet+MinIO, MLflow server, Feast, OpenTelemetry+Prometheus+Grafana, FastAPI+React/Next.js, Kafka/Kubernetes/Redis cluster scale path.
  - Premature for one process. MinIO is archived. Feast would not have caught the v1 leak. NATS core loses messages. A full Compose stack would push a VPS to $24-48 a month.

  (14)
- **Docker Compose on a dedicated Windows laptop as the 24/7 live host.** Forced update restarts, sleep, and Docker needing a signed-in user. Use the laptop for research and paper trading, and a small VPS or a restart-tolerant design for live trading (14).
- **"Investors", "investor view", "hosted read-only UI".** Inconsistent with the own-money-only constraint, creates legal and data-licence exposure, and needs a separate React app for no user. Make it an owner dashboard (12, 06, 14).
- **"Compare predicted vs actual slippage in paper".** Paper cannot supply actual slippage; only micro-live fills can (05, 17).
- **v3 "human approval for a degraded-data override".** An override path on a hard control. Remove it (12).
- **"Every decision must be reconstructable" read as re-running the agent.** Only possible through record-and-replay (03, 13).
- **Kelly or confidence-scaled sizing from the start.** It needs a few hundred calibrated outcomes first. Use a fixed minimum risk unit during the bootstrap phase (10).
- **Trade emails and alerts quoting a bare confidence percentage.** Show base rates with n and an interval, and hide the number below about 100 resolved cases (08, 10).

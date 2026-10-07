# 08 - Backtest validity and promotion gates

Research date: 2026-10-01. Basis labels: FETCHED = opened in this session; SEARCH = seen only as a search-engine summary of the source in this session (not the full text); RECALLED = from memory, not re-opened. "Own arithmetic" = computed by me from a stated formula; reproducible, but not a quotation.

Access caveat (honest gap): SSRN returned HTTP 403 for every paper page, and the PDF copies I downloaded (AMS Notices, davidhbailey.com, Lo 2002, Gelman-Loken) could not be text-extracted in this environment (no PDF renderer, no Python). So for the López de Prado / Bailey papers I verified existence, authorship, venue and abstracts from fetched pages, but the formulas themselves are RECALLED and cross-checked against one fetched practitioner page and against my own arithmetic (the MinBTL formula reproduces the paper's well-known "5 years -> 45 trials" figure, which is a decent consistency check). Someone should re-verify the formulas against the PDFs before they are coded.

## 1. Questions asked

1. What are the original results on multiple testing / backtest overfitting (deflated Sharpe, PBO, CPCV, purging and embargo, walk-forward), and what did they actually show?
2. How long a track record, or how many trades, are needed to distinguish a given Sharpe ratio from zero? Worked numbers.
3. What is specific to an LLM "Strategy Lab" that proposes many hypotheses?
4. What concrete, pre-registered, numeric promotion gates should JARVIS use for backtest -> shadow -> paper -> small live?

## 2. Findings

### 2.1 Multiple testing and backtest overfitting

F1. Harvey, Liu, Zhu, "... and the Cross-Section of Expected Returns" (NBER WP 20592, Oct 2014; RFS 29(1), 2016). Catalogues 316 published/near-published factors and argues that, given the amount of data mining, a new factor should clear a t-ratio above 3.0 rather than 2.0, and that most claimed findings are likely false. It is a study of published cross-sectional equity factors, not of trading systems, and the 3.0 is a hurdle for the academic factor zoo as of 2012. For a private lab the hurdle depends on its own trial count. Source: https://www.nber.org/papers/w20592 (FETCHED abstract; "316 factors" and the p < 0.0027 equivalence SEARCH). Confidence: high.

F2. Bailey, Borwein, López de Prado, Zhu, "Pseudo-Mathematics and Financial Charlatanism" (Notices of the AMS, May 2014). Abstract: high simulated performance is easy to obtain after trying a relatively small number of configurations; the number of trials is usually not disclosed; under some conditions (memory in the series) overfit backtests give negative expected out-of-sample returns. Source: https://scholarworks.wmich.edu/math_pubs/40/ (FETCHED abstract). Confidence: high.
- Minimum Backtest Length (RECALLED formula): MinBTL (years) ~ [ (1-g) Zinv(1-1/N) + g Zinv(1-1/(N e)) ]^2 / E[max SR]^2, bounded above by 2 ln(N) / E[max SR]^2, with g = 0.5772 (Euler-Mascheroni) and N independent trials.
- The headline figure "with 5 years of data, no more than about 45 independent variations can be tried before a Sharpe of 1 is expected by chance" is SEARCH-confirmed, and my own arithmetic with the formula gives 4.99 years for N = 45. Confidence: high.

F3. Bailey and López de Prado, "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality" (Journal of Portfolio Management, 2014). Source: https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf (FETCHED, but only title/authors/venue/purpose were reliably extracted; treat the extracted example numbers as unverified). DSR is the Probabilistic Sharpe Ratio evaluated against a benchmark equal to the expected maximum Sharpe among N unskilled trials: SR0 = sqrt(Var of trial Sharpes) x [ (1-g) Zinv(1-1/N) + g Zinv(1-1/(N e)) ] (RECALLED). Inputs required: the number of (effectively independent) trials, the variance of Sharpe across trials, sample length, skewness, kurtosis. The method cannot be applied unless every trial is recorded. Confidence: high on concept, medium on exact formula text.

F4. Bailey and López de Prado, "The Sharpe Ratio Efficient Frontier" (Journal of Risk, 2012): Probabilistic Sharpe Ratio and Minimum Track Record Length. PSR(SR*) = Phi( (SR - SR*) sqrt(n-1) / sqrt(1 - skew x SR + ((kurt-1)/4) SR^2) ); MinTRL = 1 + [1 - skew x SR + ((kurt-1)/4) SR^2] x ( z_alpha / (SR - SR*) )^2, with SR per period (not annualised). Formula FETCHED from a practitioner cross-check, https://portfoliooptimizer.io/blog/the-probabilistic-sharpe-ratio-bias-adjustment-confidence-intervals-hypothesis-testing-and-minimum-track-record-length/ (it omits the leading "1 +", immaterial); original paper at SSRN 1821643 not opened (403). Confidence: high.

F5. Bailey, Borwein, López de Prado, Zhu, "The Probability of Backtest Overfitting" (Journal of Computational Finance, 2017; SSRN 2326253). RECALLED (PDF downloaded but unreadable here): combinatorially symmetric cross-validation (CSCV). Take the T x N matrix of per-period returns for all N configurations tried, cut it into S equal blocks (S = 16 gives 12,870 splits), use every half of the blocks as in-sample and the complement as out-of-sample, pick the in-sample best, record its out-of-sample relative rank. PBO = share of splits where the in-sample winner lands below the out-of-sample median. The paper does not prescribe a pass threshold; any threshold is a design choice. PBO needs the full matrix of all tried configurations, again a trial registry. Confidence: medium-high.

F6. Purging, embargo, CPCV: López de Prado, "Advances in Financial Machine Learning" (Wiley, 2018), ch. 7 and ch. 12. RECALLED (book; a search summary confirmed chapter attribution). Purging drops training samples whose label window overlaps the test window; embargo additionally drops a buffer after each test block because of serial correlation; CPCV with N groups and k test groups gives C(N,k) splits and (k/N) x C(N,k) full backtest paths (N = 6, k = 2: 15 splits, 5 paths), so one gets a distribution of out-of-sample Sharpe rather than a single path. Walk-forward is one historical path only, which makes it easy to overfit and uses data inefficiently, but it is the only scheme with strictly no future information in training. Recommendation: use both. Confidence: high on concept; I could not open an independent paper comparing CPCV against walk-forward (unverified).

F7. Lo, "The Statistics of Sharpe Ratios" (Financial Analysts Journal 58(4), 2002). Under IID returns the standard error of the Sharpe estimate is about sqrt((1 + SR^2/2)/T); sqrt-of-time annualisation is wrong when returns are serially correlated; hedge-fund annual Sharpe ratios can be overstated by up to about 65%. Source: https://rpc.cfainstitute.org/research/financial-analysts-journal/2002/the-statistics-of-sharpe-ratios (SEARCH for the 65% claim; formula RECALLED). Confidence: high.

F8. Empirical evidence that backtest Sharpe does not predict live results. Wiecki, Campbell, Lent, Stauth (Quantopian, 2016), "All that Glitters Is Not Gold": 888 algorithms, backtests from 2010, at least 6 months out-of-sample (mid-2015 to Feb 2016). Backtest Sharpe had R^2 < 0.025 against out-of-sample; the more backtests a user ran, the bigger the in-sample/out-of-sample gap. Caveat: a short, single out-of-sample window and a retail-quant population. Source: https://quantpedia.com/quantopians-academic-paper-about-in-vs-out-of-sample-performance-of-trading-alg/ (FETCHED summary; original SSRN not opened). Confidence: medium-high.

F9. McLean and Pontiff, "Does Academic Research Destroy Stock Return Predictability?" (Journal of Finance, 2016): 97 predictors; returns 26% lower out-of-sample and 58% lower post-publication. So even genuine, peer-reviewed effects should be haircut by a quarter to a half before costs. SEARCH. Confidence: high.

F10. Paper trading is not a market simulator. Alpaca's documentation says paper trading does not model market impact, information leakage, latency slippage, queue position for non-marketable limit orders, price improvement, regulatory fees or dividends; orders fill against NBBO, can fill for more than the real available liquidity, and partial fills are random 10% of the time. Source: https://docs.alpaca.markets/docs/paper-trading (FETCHED). Confidence: high. Consequence: paper P&L for any passive or order-flow strategy is biased upward and cannot validate execution-sensitive edges.

### 2.2 Minimum track record: worked numbers (own arithmetic from F4/F7)

With daily observations and roughly normal returns, MinTRL reduces to: years needed ~ (z / annual Sharpe)^2. This assumes the observed Sharpe equals the stated value.

| Annualised Sharpe | 95% one-sided (z = 1.645) | t = 3.0 hurdle (F1) | 80% power at 95% (z = 2.49) |
|---|---|---|---|
| 0.5 | 10.8 years | 36 years | 24.7 years |
| 1.0 | 2.7 years | 9 years | 6.2 years |
| 1.5 | 1.2 years | 4 years | 2.7 years |
| 2.0 | 0.68 years (~170 trading days) | 2.25 years | 1.5 years |
| 3.0 | 0.30 years (~76 days) | 1 year | 0.7 years |

Negative skew and fat tails lengthen these (for skew -1, kurtosis 6, Sharpe 2, the multiplier is about 1.15); positive autocorrelation lengthens them further (F7).

Read the other way: the standard error of an annualised Sharpe measured over T years is about 1/sqrt(T). A 3-month paper period has a standard error of about 2.0, so it can only distinguish a true Sharpe above roughly 3.3 from zero; 6 months, above 2.3; 12 months, above 1.65. A 3-month paper run cannot prove a Sharpe-1 strategy works. It can only fail to contradict the backtest and validate the plumbing and cost model.

Per-trade view (independent trades, symmetric 1:1 payoff, n = (z x sd / mean)^2):

| True win rate | Trades for 95% | Trades for t = 3 |
|---|---|---|
| 52% | ~1,690 | ~5,620 |
| 55% | ~270 | ~890 |
| 60% | ~65 | ~215 |

Trades overlapping in time or on correlated assets (BTC and ETH momentum on the same hour) are not independent; count clusters, not fills.

Selection inflation (expected best annualised Sharpe among N skill-less independent trials, from F3):

| Trials N | 1 year of data | 2 years | 5 years |
|---|---|---|---|
| 10 | 1.58 | 1.11 | 0.70 |
| 100 | 2.53 | 1.79 | 1.13 |
| 1,000 | 3.25 | 2.30 | 1.45 |

An LLM lab that tries 1,000 variants on two years of crypto data should expect its best pure-noise strategy to show a Sharpe around 2.3.

Calibration sample size: to pin down a "72% confidence" bucket to plus or minus 5 points at 95% needs about 310 resolved setups in that bucket (1.96^2 x 0.72 x 0.28 / 0.05^2).

### 2.3 Risks specific to an LLM Strategy Lab

F11. Memorisation / look-ahead. Lopez-Lira, Tang, Zhu, "The Memorization Problem: Can We Trust LLMs' Economic Forecasts?" (arXiv 2504.14765, Apr 2025, rev. Dec 2025): LLMs recall exact values of economic and market data from before their knowledge cutoff; instructions to respect a historical date do not stop this; masking fails because the models reconstruct entities and dates from context; no recall post-cutoff. Source: https://arxiv.org/abs/2504.14765 (FETCHED abstract). Confidence: high. Glasserman and Lin (arXiv 2309.17322, FETCHED abstract) is partly dissenting: on news headlines, anonymised headlines did better in-sample than originals, so a "distraction" effect was larger than look-ahead in their setting. Anonymisation is therefore worth testing but is contested as a cure.

F12. Search intensity. Gençay, "What survives honest evaluation? Leakage-safe, search-aware assessment of LLM-driven trading strategy discovery" (arXiv 2608.27734, Aug 2026, single-author preprint, not peer-reviewed): 453 US stocks point-in-time plus 39 ETFs, up to 100 LLM-generated candidates per run, five runs, two frontier models, costs including impact and borrow. A deliberately leaky oracle with Sharpe 35 passed conventional statistical tests (so deflation alone does not catch leakage); with look-ahead-proof tools plus deflation by actual trial count, passive benchmarks were certified and all LLM-discovered strategies were rejected. Source: https://arxiv.org/abs/2608.27734 (FETCHED abstract only). Confidence: medium.

F13. Ye et al., "The Alpha Illusion: Reported Alpha from LLM Trading Agents Should Not Be Treated as Deployment Evidence" (arXiv 2605.16895, May 2026, position paper): headline Sharpe from systems such as TradingAgents, FinMem, FinCon cannot be separated from temporal contamination, unmodelled frictions, short-window Sharpe uncertainty and narrative fitting; proposes six validity tests and recommends LLMs as auditable information interfaces upstream of independent calibration and execution. Source: https://arxiv.org/abs/2605.16895 (FETCHED abstract). Confidence: medium-high. Related: Jeon and Lee, "Can Blindfolded LLMs Still Trade?" (arXiv 2603.17692, FETCHED abstract) report regime-dependent performance when the window is extended.

F14. Garden of forking paths (Gelman and Loken, 2013): multiple comparisons arise even with one reported analysis when analysis choices are contingent on the data. PDF downloaded but unreadable here, so RECALLED. Confidence: high. LLM-specific forking paths that never show up as "backtests run": prompt wording, model version, temperature, which agent's opinion is used, feature choice, universe, bar size, stop/exit rule, confidence weights, the Position Manager's exit threshold, and the human (or agent) deciding to "look again" after a disappointing result. An LLM also proposes ideas from a literature it was trained on, so its hypotheses are pre-mined on the same history used to test them; a low internal trial count understates the true search.

## 3. What this means for the JARVIS design documents

- Architecture doc, Layer D "Strategy Lab" ("LLM proposes hypotheses; backtest, walk-forward, transaction-cost model, out-of-sample validation, paper trading"): direction supported, but the list omits the three things the literature says matter most: a complete trial registry, deflation by trial count (DSR/PBO), and leakage-proof tooling. As written it is a strategy-mining machine with a walk-forward stamp. Weakened.
- v3 build step 5 ("walk-forward evaluation; every model must have out-of-sample calibration") and the Confidence Calibrator ("walk-forward calibration; isotonic/Platt"): walk-forward alone is a single path (F6). The worked examples' "72% / 82% / 79% calibrated confidence" need about 300 resolved comparable setups per bucket; nothing in the current JARVIS (123 daily rows, one ticker, a leaked target) supports any calibrated number. Weakened.
- v3 build step 10 ("promote to small live only after predefined paper-trading gates"): principle supported, but no gate is defined, and the arithmetic in 2.2 shows a paper period of months cannot statistically establish an edge below Sharpe 2-3. The docs implicitly treat paper trading as the proof. Contradicted in emphasis: paper is an implementation and cost-fidelity test; the statistical burden must be carried by a long, deflated, leakage-free backtest plus continued live monitoring.
- Architecture doc's own research anchor ("paper ... does not fully simulate market impact, queue position or latency slippage"): supported by Alpaca's documentation (F10). But the BTC/ETH examples are order-flow/L2 intraday trades, precisely the class paper trading cannot validate.
- Specialist LLM agents (News/Event, Bull/Bear, Strategy Lab): any backtest that runs an LLM over dates before its training cutoff is contaminated (F11) and prompts do not fix it. LLM-in-the-loop components can be validated only forward in time (shadow), or by having the LLM emit deterministic code/features that are then backtested without the LLM. Not addressed in any of the three documents.
- Position Manager ("recalculates the thesis ... exits early when confidence falls"): each exit rule is another tunable path; it must be part of the pre-registered strategy definition and counted as trials.
- v1 JARVIS (Spearman 0.999, +61% in a month from a leaked feature): F12's "Sharpe-35 oracle passes conventional tests" is the same failure. A "too good to be true" tripwire belongs in the gates.
- "FLAT is valid", deterministic risk gate, versioned models/prompts in the ledger: supported; the ledger is the natural home for the trial registry.

## 4. Recommended changes (proposed gates)

The numeric thresholds below are my design proposals built from the formulas above. They are not taken from any paper; the literature gives methods, not pass marks. They should be frozen in a config file before the first strategy is tested, and changed only by an audited action.

Gate 0 - Pre-registration (before any backtest). A hypothesis card: economic rationale (who is on the other side and why they lose), universe, signal, exit rules, parameter grid (max 20 configurations per hypothesis), cost model, primary metric, kill criteria. Every backtest execution, including failed and abandoned ones, is auto-logged to an append-only trial registry by the backtest engine itself (the LLM cannot run a backtest outside it). Hypotheses are grouped into families; N for deflation is the family's cumulative count. Budget: for example at most 50 new configurations per quarter per family.

Gate 1 - Backtest -> shadow. All required:
- Point-in-time, survivorship-free data; same code path as live; no LLM calls on pre-cutoff dates.
- At least 300 independent trade clusters (so a 55% win rate is detectable at 95%), spanning at least 3 years for daily-or-slower strategies or at least 18 months and two volatility regimes for intraday crypto.
- Net of modelled costs; still positive expectancy at 2x costs.
- DSR at least 0.95 with N = registry count for the family (clustered to effective N), using measured skew and kurtosis.
- PBO (CSCV, S = 16) at most 0.20 across all configurations tried.
- CPCV (for example N = 10, k = 2, purged, embargo at least the label horizon): median path Sharpe above 0.5 net and at least 80% of paths positive.
- Walk-forward out-of-sample Sharpe at least 50% of in-sample; parameter neighbours within plus or minus 20% keep at least 70% of the Sharpe.
- A final holdout (most recent 20% of history) evaluated exactly once; failing it retires the hypothesis, with no re-tuning.
- Tripwire: backtest Sharpe above 3 on daily data, or accuracy above 60% on next-day direction, triggers a mandatory leakage audit rather than promotion.

Gate 2 - Shadow (signals only, live data) -> paper. At least 4 weeks and at least 50 signals; live-computed features and signals match a later replay of the same timestamps at 99% or better; zero unhandled data-trust incidents; quoted spread at signal time within 1.5x of the backtest cost assumption. For LLM-dependent signals shadow is the only clean evidence, so require at least 3 months and at least 100 signals.

Gate 3 - Paper -> small live. The later of 3 months and 100 trades. The test is non-falsification, not proof: realised Sharpe inside the backtest's 90% interval (roughly backtest Sharpe plus or minus 1.645/sqrt(T years)); max drawdown below the 95th percentile of bootstrapped backtest drawdowns; hit rate and average win/loss within 2 standard errors; zero risk-gate breaches; kill switch and reconciliation drills passed. Strategies relying on passive fills or queue position get no credit from paper (F10) and go to live at minimum size instead.

Gate 4 - Small live -> scale. Minimum order size and at most 1-5% of intended capital; the later of 3 months and 100 live trades; live slippage within 1.5x model; live-versus-shadow P&L tracking explained; then capital doubles per stage with the same checks. Standing demotion rules: drawdown above 1.5x backtest maximum, PSR(0) on the live record below 0.10 after 100 trades, or slippage above 2x model returns the strategy to shadow. Running PSR/MinTRL is reported on the dashboard so "not yet statistically distinguishable from zero" is visible to the owner and any investors.

Structural changes:
1. Add a "Research Integrity / Validation" service (deterministic, not an LLM) owning the trial registry, DSR/PBO/CPCV computation and the gate decisions; the Strategy Lab LLM may propose but cannot mark its own work.
2. Split LLM use: the LLM writes hypotheses and deterministic feature code (backtestable); LLM runtime judgement (news reading, bull/bear) is treated as forward-test-only.
3. Replace per-trade "confidence 72%" with bucketed empirical hit rates that display their sample size and interval; show no number below about 100 resolved cases.
4. Start with one or two economically motivated, low-turnover strategies with long histories instead of intraday order-flow on $100, where neither backtest data (L2 history) nor paper fills are trustworthy.

## 5. Open uncertainties

- Formulas for DSR, MinBTL, PBO/CSCV and CPCV are recalled, not read from the PDFs in this session (extraction failed, SSRN blocked). Re-verify before coding.
- The effective number of independent trials for correlated LLM variants has no agreed method; clustering trial returns (López de Prado's later work, recalled, unverified) is one option.
- PBO at most 0.20, DSR at least 0.95, 300 trades and the other thresholds are judgement calls; no source prescribes them.
- Whether anonymisation reduces LLM look-ahead is contested (F11 versus Glasserman-Lin).
- arXiv 2608.27734 and 2605.16895 are recent non-peer-reviewed preprints; I read abstracts only.
- I found no opened, peer-reviewed head-to-head of CPCV versus walk-forward.
- The Claude model version and cutoff the owner will use is unknown, so the clean forward-only window cannot be stated.
- White's Reality Check (2000), Hansen's SPA test (2005) and Harvey-Liu "Backtesting" (2015) are relevant alternatives but were not opened; recalled only.

## 6. Source list

- https://www.nber.org/papers/w20592 - Harvey, Liu, Zhu (FETCHED)
- https://scholarworks.wmich.edu/math_pubs/40/ - Bailey, Borwein, López de Prado, Zhu, Pseudo-Mathematics (FETCHED abstract); PDF https://www.ams.org/notices/201405/rnoti-p458.pdf (downloaded, unreadable)
- https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf - Deflated Sharpe Ratio (FETCHED, partial)
- https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf - Probability of Backtest Overfitting (downloaded, unreadable; RECALLED)
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1821643, 2460551, 2326253, 2249314 - SSRN pages (403, not opened)
- https://portfoliooptimizer.io/blog/the-probabilistic-sharpe-ratio-bias-adjustment-confidence-intervals-hypothesis-testing-and-minimum-track-record-length/ - MinTRL formula cross-check (FETCHED)
- https://rpc.cfainstitute.org/research/financial-analysts-journal/2002/the-statistics-of-sharpe-ratios - Lo 2002 (SEARCH)
- https://quantpedia.com/quantopians-academic-paper-about-in-vs-out-of-sample-performance-of-trading-alg/ - Wiecki et al. summary (FETCHED)
- McLean and Pontiff 2016, Journal of Finance (SEARCH; no primary page opened)
- https://docs.alpaca.markets/docs/paper-trading - Alpaca paper trading (FETCHED)
- https://arxiv.org/abs/2504.14765 - Lopez-Lira, Tang, Zhu (FETCHED)
- https://arxiv.org/abs/2309.17322 - Glasserman, Lin (FETCHED)
- https://arxiv.org/abs/2608.27734 - Gençay (FETCHED abstract)
- https://arxiv.org/abs/2605.16895 - Ye et al. (FETCHED abstract)
- https://arxiv.org/abs/2603.17692 - Jeon, Lee (FETCHED abstract)
- López de Prado, Advances in Financial Machine Learning, Wiley 2018, ch. 7, 11, 12 (RECALLED)
- Gelman and Loken, The garden of forking paths, 2013, https://sites.stat.columbia.edu/gelman/research/unpublished/p_hacking.pdf (downloaded, unreadable; RECALLED)

## Independent verification (2026-10-01)

Confirmed (opened or searched independently):
- HLZ (NBER w20592): t > 3.0 hurdle, "most claimed findings likely false"; it is an equity-factor study. https://www.nber.org/papers/w20592
- Gencay arXiv 2608.27734 (27 Aug 2026, single author): 453 stocks, 39 ETFs, up to 100 candidates, five runs, two models, Sharpe-35 leaky oracle survives DSR and PBO; all LLM strategies rejected. https://arxiv.org/abs/2608.27734
- Ye et al. arXiv 2605.16895 (16 May 2026): six validity tests, P1-P6 protocol. https://arxiv.org/abs/2605.16895
- Lopez-Lira, Tang, Zhu arXiv 2504.14765 (v1 Apr 2025, v2 Dec 2025). Note: it also says memorisation makes counterfactual forecasting skill non-identifiable. https://arxiv.org/abs/2504.14765
- Alpaca paper trading limits; also 10% random partial fills, NBBO matching; borrow fees not modelled. https://docs.alpaca.markets/docs/paper-trading
- McLean-Pontiff: 97 predictors, -26% out-of-sample, -58% post-publication. Note the paper reads 26% as an upper bound on data-mining decay and ~32% as the publication effect. https://ivey.uwo.ca/media/3775549/pontiff.pdf
- Quantopian: 888 algos, R^2 < 0.025. https://quantpedia.com/quantopians-academic-paper-about-in-vs-out-of-sample-performance-of-trading-alg/
- Own re-computation of MinBTL (N=45 -> ~5.0 yr), MinTRL tables, selection-inflation values, win-rate trade counts and the Sharpe standard-error figures: all arithmetic reproduces.

Corrected / sharpened:
- The "5 years -> 45 trials" figure means in-sample Sharpe about 1 with expected out-of-sample Sharpe zero; one secondary summary states ">1.5", so quote the formula, not the headline.
- Gencay is a preprint with abstract-only reading; do not cite it as settled. Its useful point (deflation alone passes a leaky oracle) is confirmed.
- Thresholds (DSR 0.95, PBO 0.20, 300 clusters) remain design choices, as the brief says.

Unverified: DSR/PBO/CPCV formulas (SSRN 403, PDFs unreadable), Lo 2002 "65%" claim, Lo SE formula, Gelman-Loken, AFML chapters, CPCV vs walk-forward comparisons.

Missed given owner constraints (US resident, $1k-$10k, near-zero budget):
- PDT rule is gone: SEC approved FINRA Rule 4210 changes 14 Apr 2026, effective 4 Jun 2026, brokers may take until 20 Oct 2027 to implement; margin accounts over $2,000 get broker-set intraday buying power. Day-trade gating for small accounts therefore depends on the specific broker. https://www.finra.org/sites/default/files/2026-04/Regulatory-Notice-26-10.pdf
- Statistical power at this scale: a $1k-$10k book on few low-turnover strategies cannot reach the 300-cluster / 3-year gates quickly; the gates are a filter, so expect most hypotheses to stay in shadow. Fees and spreads are a larger fraction of edge at small size.
- US tax friction (short-term gains, wash-sale rules on stocks, crypto taxed as property) is not in the cost model.

# 15 — Statistical and ML models for JARVIS

Research date: 2026-10-01. Basis tags: FETCHED = opened in this session (page, abstract or search-result abstract); RECALLED = from memory, not re-verified; UNVERIFIED = could not confirm. Where only an abstract was opened, that is stated.

## 1. Questions asked

The design documents (Architecture layer C "Specialist Intelligence"; v2 "Statistical + ML forecasters"; v3 "Model Ensemble: XGBoost/LightGBM; HMM; GARCH; anomaly models; DL only where justified", RL "later, sandboxed") propose a model ensemble. I asked:

1. Volatility: GARCH-family vs realised-volatility models (HAR) vs ML. Authoritative sources: the original papers and large comparison studies.
2. Regime HMMs: what do the standard libraries actually return (filtered vs smoothed), and how unstable is estimation? Sources: statsmodels and hmmlearn official docs; a peer-reviewed alternative (statistical jump models).
3. Jump detection: which tests, what data do they need? Sources: original papers and a Monte Carlo comparison.
4. Gradient boosting vs deep learning on tabular data, in general and in finance. Sources: large benchmark papers and the asset-pricing ML literature.
5. Reinforcement learning for trading: realistic assessment. Sources: FinRL repository, reproducibility and overfitting papers.
6. Build order and target definitions that prevent the leakage that invalidated JARVIS v1.

## 2. Findings

### 2.1 Volatility forecasting

**F1. GARCH(1,1) is hard to beat within the GARCH family on FX, but not on equities.** Hansen and Lunde (2005, J. Applied Econometrics 20(7)) compared 330 ARCH-type models out of sample on DM/USD and IBM returns using the SPA test and the reality check. No model beat GARCH(1,1) on the exchange rate; on IBM, GARCH(1,1) was clearly inferior to models with a leverage (asymmetry) term. Source: abstract via https://zendy.io/title/10.1002/jae.800 and CRAN replication vignette (search-result abstract). FETCHED (abstract only), confidence high.
Implication: if GARCH is used for equities, use an asymmetric variant (GJR/EGARCH) with fat-tailed errors, not plain GARCH(1,1).

**F2. HAR-RV is the standard realised-volatility benchmark.** Corsi (2009, J. Financial Econometrics 7(2)) proposes a regression of realised volatility on its daily, weekly and monthly averages; it reproduces long memory with a simple linear model and forecasts well. Source: https://papers.ssrn.com/abstract=1365738 (abstract via search). FETCHED (abstract only), confidence high.

**F3. Whether ML beats HAR depends on how carefully HAR is fitted and on what extra predictors exist.**
- Christensen, Siggaard and Veliyev (J. Financial Econometrics, 2022/2023; arXiv 2601.13014): 29 Dow Jones stocks, high-frequency data 2001-2017, horizons one day to one month. With only RV lags, neural nets gained roughly 5% over HAR and trees underperformed HAR; with a wider predictor set (implied vol, macro, etc.) neural nets cut MSE by roughly 10-15%, random forest about 10%, elastic net about 8%. Gains grow at longer horizons. Statistical-loss study; not a trading P&L study. Source: https://arxiv.org/html/2601.13014v1. FETCHED (machine summary of the full HTML), confidence medium-high on direction, medium on exact percentages.
- Audrino and Chassot, "HARd to Beat" (arXiv 2406.08041): about 1,445 US stocks, Jan 2016-Nov 2023, one-day-ahead RV, losses MSE/QLIKE/realised utility with and without costs. A HAR fitted with a long (about 630-day) rolling window and daily re-estimation consistently beat lasso, random forest, gradient-boosted trees and feed-forward nets when all use RV (and VIX). They argue earlier ML wins came from handicapped HAR baselines. Source: https://arxiv.org/abs/2406.08041 and https://arxiv.org/html/2406.08041v1. FETCHED, confidence medium-high (preprint; I did not confirm journal publication).

**F4. Tooling.** The Python `arch` package supports GARCH, EGARCH, FIGARCH, APARCH, HARCH volatility processes; HAR/HARX mean models; normal, Student-t, skew-t and GED errors. Source: https://arch.readthedocs.io/en/latest/univariate/introduction.html. FETCHED, confidence high. Current version number: unverified.

**F5. Practical caveat (my inference, not a cited finding).** HAR needs a realised-variance input built from intraday bars. On free data tiers this is feasible for crypto (free exchange minute bars) and for a small equity universe (free minute bars from the broker feed, possibly single-venue), but data depth and quality must be confirmed by the data-feed research stream. Where intraday data is absent, range-based estimators (Parkinson/Garman-Klass) on daily OHLC are the fallback. RECALLED, confidence medium.

### 2.2 Regime HMMs

**F6. Standard library outputs are look-ahead by default.** hmmlearn's `predict`, `decode`, `predict_proba` and `score_samples` all condition on the complete sequence (Viterbi "given all emissions", or forward-backward posteriors); the API documents no forward-only (filtered) method. Source: https://hmmlearn.readthedocs.io/en/latest/api.html. FETCHED, confidence high. statsmodels `MarkovRegression` separates `filter()` (Hamilton filter) from `smooth()` (Kim smoother, which uses the whole sample), but its official example notebook plots only `smoothed_marginal_probabilities`. Sources: https://www.statsmodels.org/stable/generated/statsmodels.tsa.regime_switching.markov_regression.MarkovRegression.html and https://www.statsmodels.org/stable/examples/notebooks/generated/markov_regression.html. FETCHED, confidence high.
Implication: a regime feature built by calling `model.predict(X)` on the full history and joining it back as a feature is the same class of defect as JARVIS v1's `return_pct_t1`. It makes regimes look clean and tradable in backtests. Only filtered probabilities P(state_t | data up to t), from a model whose parameters were also estimated only on data up to t, are legitimate.

**F7. Estimation is unstable.** hmmlearn's tutorial states EM generally gets stuck in local optima and recommends fitting from several initialisations and keeping the best score; it gives no guidance on choosing the number of states. statsmodels' example needs `search_reps=20` random starts for a 3-regime model. Sources: https://hmmlearn.readthedocs.io/en/latest/tutorial.html, statsmodels notebook above. FETCHED, confidence high. Additional known issues (label switching across refits, Gaussian emissions fitting "regimes" that are really just volatility clusters, rapid state flicker): RECALLED, confidence medium-high.

**F8. A more persistent alternative exists.** Shu, Yu and Mulvey (arXiv 2402.05272): a statistical jump model with an explicit penalty on state changes, tested on US, German and Japanese equity indices 1990-2023 with transaction costs and a trading delay, gave lower volatility and drawdown and higher Sharpe than an HMM-guided strategy and buy-and-hold. Source: https://arxiv.org/abs/2402.05272. FETCHED (abstract), confidence medium (authors' own back-test on three indices; a risk-reduction result, not alpha).

### 2.3 Jump detection

**F9.** Barndorff-Nielsen and Shephard (2006) test for jumps by comparing realised variance with bipower variation over a day; on FX data most detected jumps coincided with macro announcements. Source: https://users.ox.ac.uk/~ofrcinfo/pages_fineconpapers/2004fe01.htm (abstract via search). FETCHED (abstract only), confidence high.
**F10.** Lee and Mykland (2008, RFS 21(6)) test each intraday return against local bipower volatility, giving jump times and sizes; misclassification becomes negligible only with high-frequency returns; individual-stock jumps align with earnings and company news, index jumps with macro news. Source: https://galton.uchicago.edu/~mykland/paperlinks/LeeMykland-2535.pdf (abstract via search). FETCHED (abstract only), confidence high.
**F11.** Dumitru and Urga (2012, JBES 30(2)): Monte Carlo comparison of nine tests; the intraday ABD / Lee-Mykland procedures performed best provided volatility is not extreme; combining tests and sampling frequencies reduces spurious jumps. Source: https://openaccess.city.ac.uk/id/eprint/6962/. FETCHED, confidence high.
Implication: these tests **detect** jumps after they occur; they do not **forecast** them. The docs' "jump model says continuation is plausible" (BTC example) is a separate, unproven predictive claim that would need its own out-of-sample evidence. Jump tests also need intraday data and, without a diurnal-volatility adjustment, flag the open and close as jumps (RECALLED, medium).

### 2.4 Gradient boosting vs deep learning on tabular data

**F12. General tabular benchmarks.** Grinsztajn, Oyallon and Varoquaux (NeurIPS 2022; arXiv 2207.08815): 45 datasets, about 20,000 compute-hours of tuning per learner; tree ensembles stay ahead on medium-sized (about 10k-row) data; neural nets are hurt by uninformative features and irregular target functions. FETCHED, confidence high. Shwartz-Ziv and Armon (arXiv 2106.03253): XGBoost beat recently proposed deep tabular models, including on those models' own datasets, with less tuning; an ensemble of both beat either. FETCHED, confidence high.
**F13. The gap has narrowed since.** TabArena (arXiv 2506.16791, NeurIPS 2025 Datasets and Benchmarks): boosted trees remain strong contenders; deep methods catch up with large tuning budgets and ensembling; tabular foundation models do best on small datasets. FETCHED (abstract), confidence high. These benchmarks are i.i.d. tabular problems, not non-stationary low-signal financial series; transfer to finance is unverified.
**F14. Finance-specific.** Gu, Kelly and Xiu (RFS 2020): trees and neural nets are the best performers for monthly US stock returns, with the edge attributed to nonlinear interactions; dominant predictors are momentum, liquidity and volatility variants. Source: https://www.nber.org/papers/w25398 (abstract). FETCHED, confidence high. Detail from memory: about 30,000 stocks 1957-2016, roughly 900 predictors; best monthly out-of-sample R-squared about 0.4% (shallow nets) vs about 0.3% for trees; headline portfolio Sharpe ratios are gross of trading costs. RECALLED, confidence medium (I could not parse the PDF in this session).
**F15. The economic value shrinks sharply under realistic constraints.** Avramov, Cheng and Metzker (Management Science 69(5), 2023): deep-learning signals earn most of their profit in hard-to-arbitrage stocks (microcaps, distressed) and high-volatility periods; excluding these considerably attenuates profitability, and reasonable trading costs erode it further because of high turnover. Source: https://papers.ssrn.com/abstract=3450322 (abstract via search). FETCHED (abstract only), confidence high.
Bottom line: a predictive R-squared well under 1% per month is the state of the art for large cross-sections; a single-stock or small-universe daily model should expect less. Any JARVIS back-test showing rank correlations above roughly 0.1 or directional accuracy above roughly 55% should be treated as a leakage alarm, not a success (thresholds are my judgement).

### 2.5 Reinforcement learning

**F16.** FinRL's own README says the code is shared for academic purposes and is not a recommendation to trade real money; it now points users to FinRL-X / FinRL-Trading for deployment. About 16.5k stars. Source: https://github.com/AI4Finance-Foundation/FinRL. FETCHED, confidence high.
**F17.** Henderson et al. (AAAI 2018; arXiv 1709.06560): deep RL results vary heavily with seeds and hyperparameters, making reported gains hard to interpret, even in stationary simulators. FETCHED (abstract), confidence high.
**F18.** Gort et al. (arXiv 2209.05559), from the FinRL group: treats back-test overfitting of DRL crypto agents as a hypothesis test and rejects overfitted agents; the surviving agents beat benchmarks on 10 cryptocurrencies, but the test window is only 1 May-27 June 2022 (about two months). FETCHED (abstract), confidence high on facts. My reading: the proponents themselves treat overfitting as the central problem, and the supporting evidence is a two-month window.
**F19.** A critical survey (Millea, "Deep Reinforcement Learning for Trading — A Critical Survey", Data 6(11), 2021) and a review surfaced in search conclude most studies are proofs of concept in unrealistic settings without live testing. Source: https://www.mdpi.com/2306-5729/6/11/119 — the page returned 403; conclusions known only from search snippets. UNVERIFIED in detail, confidence low-medium.
Assessment: RL for directional trading needs a high-fidelity market simulator, far more data than one retail account generates, and has a reproducibility problem even in clean environments. No source I opened shows durable, cost-adjusted, live retail profitability. The one area where RL is plausibly appropriate (execution scheduling for large orders) is irrelevant at $1k-$10k.

### 2.6 Labels, validation and leakage

**F20.** Triple-barrier labelling (profit barrier, stop barrier, time barrier; label = first touched), meta-labelling, purging and embargo are from López de Prado, *Advances in Financial Machine Learning* (2018). Overlapping labels (an N-bar horizon sampled every bar) make adjacent samples share most of their outcome window, so naive K-fold leaks; purging drops training rows whose label window overlaps the test fold, embargo drops a buffer after it. I could not open the book or a primary page (Wikipedia page 404); description confirmed only through search-result summaries. Basis: RECALLED plus search snippet, confidence high on the concepts.
**F21.** Deflated Sharpe Ratio (Bailey and López de Prado, JPM 40(5), 2014) corrects a Sharpe ratio for the number of trials attempted and for non-normal returns. Source: https://papers.ssrn.com/abstract=2460551 (403 on direct fetch; abstract via search). FETCHED (abstract only), confidence high.
**F22.** Kapoor and Narayanan (Patterns, 2023): leakage found in 17 scientific fields affecting 294 papers; eight-type taxonomy; propose "model info sheets". Source: https://reproducible.cs.princeton.edu/ (via search abstract). FETCHED (abstract only), confidence high. JARVIS v1's defect is a textbook case in that taxonomy (a feature that is a proxy for the target).
**F23.** Volatility-scaled targets: Lim, Zohren and Roberts (arXiv 1904.04912; J. Financial Data Science 2019) embed learning in the volatility-scaling framework of time-series momentum on 88 futures; the Sharpe-optimised LSTM more than doubled the baseline gross of costs, but the edge survives only up to about 2-3 basis points of cost. FETCHED (abstract), confidence high. For retail crypto with taker fees an order of magnitude above that (fee level to be confirmed by the cost research stream), such strategies would not survive.

## 3. What this means for the JARVIS documents

- **"Volatility (GARCH/ML)" (Architecture layer C; v3 Model Ensemble): supported but mis-specified.** Volatility is the one quantity with strong, replicated predictability, and it feeds the Capital Governor's volatility targeting directly. But the evidence favours HAR on realised variance as the primary model, with asymmetric fat-tailed GARCH as the daily-data fallback. ML volatility models are optional and only pay off with richer predictors (F3).
- **"Regime model (HMM/ML)": weakened.** Legitimate only as filtered, walk-forward-refit probabilities; default library calls leak (F6) and estimation is unstable (F7). A transparent rule-based regime (trend sign plus volatility tercile) or a jump-penalised model (F8) should be the baseline an HMM must beat. Use regimes as a risk dial, not a return forecast.
- **"Jump/anomaly model ... continuation is plausible" (BTC example): contradicted as worded.** Jump tests detect; they do not predict continuation (F9-F11). Keep them as an event flag feeding the Data Trust and surveillance functions and as a feature.
- **"XGBoost/LightGBM; DL only where justified": supported** (F12-F15). On JARVIS-sized data (thousands to tens of thousands of rows) boosting is the right default. "Justified" should be defined in advance: DL must beat tuned boosting out of sample, net of costs, under purged validation.
- **"RL as a later sandboxed layer, not the first trading brain" (v2): supported; I would go further** and remove RL from the roadmap until a profitable supervised system and a validated simulator exist (F16-F19).
- **"Statistical continuation model = 76%; ML ensemble = 81%" and "calibrated confidence 72-82%" (all three worked examples): contradicted by base rates.** Published predictability (F14, F15, F23) implies calibrated directional probabilities for liquid assets sit near 50-55%. A properly calibrated JARVIS will rarely, if ever, emit 80%. The Confidence Calibrator should be expected to compress scores toward 50%, and the docs' example numbers should be rewritten.
- **"Return distribution" forecasts: partially supported.** Forecast the scale (volatility) well and treat the mean as near zero unless a signal earns otherwise; quantile-objective LightGBM or conformal intervals can give distributional output without a new model class (my recommendation; not separately sourced).
- **"Every model must have out-of-sample calibration and version IDs" (v3 step 5) and point-in-time features (Feast): supported**, but insufficient without purging/embargo for overlapping labels and without counting trials (F20, F21).
- **"News impact" model built on the existing 123-row TSLA dataset: not supportable.** No statistical model can be validated on 123 rows with 47 features.

## 4. Recommended changes

Build order (each stage gated on the previous one):

0. **Labelling and validation harness first, no model.** Label store with explicit `t_decision`, `t_label_start`, `t_label_end`; features must carry `t_available <= t_decision`. Walk-forward splits with purge equal to the label horizon plus an embargo. Automated leakage tests: (a) fail the build if any feature's absolute correlation with the target exceeds a threshold (v1's 0.999 would trip it); (b) shuffled-target run must score at chance; (c) feature-shift test (lag all features one extra bar; a collapse in performance signals look-ahead); (d) a trial counter feeding a deflated Sharpe.
1. **Naive baselines.** Buy-and-hold, zero forecast, 12-1 momentum, yesterday's volatility. Everything later must beat these net of costs.
2. **Volatility model.** HAR-RV (long window, daily re-fit) where intraday bars exist; GJR/EGARCH with Student-t otherwise. Evaluate with QLIKE. This is immediately useful for sizing even if no alpha is ever found.
3. **Simple regime indicator.** Rule-based first; filtered HMM or jump model only if it adds out-of-sample value to sizing.
4. **Jump/event flags.** Lee-Mykland-style test with intraday seasonality adjustment, used as a flag and feature.
5. **One LightGBM model on a pooled cross-section** (many symbols, not one), with a volatility-scaled forward return or triple-barrier label whose barriers are multiples of forecast volatility; sample weights by label uniqueness. Then, optionally, a meta-label model that decides whether to act on a simple primary rule.
6. **Calibration** (isotonic/Platt on purged out-of-fold predictions) and reliability curves.
7. **Deep learning** only if step 5 saturates and data volume supports it. **RL: not on the roadmap.**

Target definitions that avoid v1's leakage: the target is always computed from prices strictly after `t_decision` plus an execution delay (next bar open, not same bar close); no feature name or formula may reference a forward shift; targets are scaled by volatility estimated only from past data; overlapping labels are purged in validation; one final untouched hold-out period is reserved and used once.

## 5. Open uncertainties

- Gu-Kelly-Xiu exact figures (sample size, R-squared, whether any cost analysis is included) are recalled, not re-read; a machine summary of the PDF claimed costs are incorporated, which conflicts with my recollection. Needs a human read of the paper.
- Whether free data tiers give intraday bars of sufficient depth and quality for realised variance and jump tests on equities (belongs to the data-feed stream).
- HAR-vs-ML evidence is on US equities; I opened no equivalent large study for crypto.
- "HARd to Beat" is a preprint; publication status unverified.
- The statistical jump model result is from its authors on three indices; independent replication not checked.
- The critical RL survey could not be opened (403); its conclusions are second-hand.
- AFML (triple barrier, purged CV, CPCV, sample uniqueness) could not be opened; described from memory. Independent evidence that triple-barrier labels outperform simple fixed-horizon vol-scaled labels was not found and should not be assumed.
- Tabular foundation models (TabPFN-class) are untested on non-stationary financial data in anything I opened.

## 6. Source list

Opened in this session (page or abstract):
- https://arxiv.org/abs/2207.08815 — Grinsztajn et al., trees vs deep learning
- https://arxiv.org/abs/2106.03253 — Shwartz-Ziv and Armon
- https://arxiv.org/abs/2506.16791 — TabArena
- https://www.nber.org/papers/w25398 and https://ideas.repec.org/a/oup/rfinst/v33y2020i5p2223-2273..html — Gu, Kelly, Xiu (abstract)
- https://papers.ssrn.com/abstract=3450322 — Avramov, Cheng, Metzker (abstract via search)
- https://arxiv.org/html/2601.13014v1 — Christensen, Siggaard, Veliyev
- https://arxiv.org/abs/2406.08041 and https://arxiv.org/html/2406.08041v1 — Audrino and Chassot
- https://papers.ssrn.com/abstract=1365738 — Corsi HAR-RV (abstract via search)
- https://zendy.io/title/10.1002/jae.800 — Hansen and Lunde (abstract via search)
- https://arch.readthedocs.io/en/latest/univariate/introduction.html — arch package
- https://hmmlearn.readthedocs.io/en/latest/api.html and /tutorial.html — hmmlearn
- https://www.statsmodels.org/stable/generated/statsmodels.tsa.regime_switching.markov_regression.MarkovRegression.html and https://www.statsmodels.org/stable/examples/notebooks/generated/markov_regression.html — statsmodels
- https://arxiv.org/abs/2402.05272 — Shu, Yu, Mulvey statistical jump model
- https://users.ox.ac.uk/~ofrcinfo/pages_fineconpapers/2004fe01.htm — Barndorff-Nielsen and Shephard (abstract via search)
- https://galton.uchicago.edu/~mykland/paperlinks/LeeMykland-2535.pdf — Lee and Mykland (abstract via search)
- https://openaccess.city.ac.uk/id/eprint/6962/ — Dumitru and Urga
- https://github.com/AI4Finance-Foundation/FinRL — FinRL README
- https://arxiv.org/abs/1709.06560 — Henderson et al.
- https://arxiv.org/abs/2209.05559 — Gort et al.
- https://arxiv.org/abs/1904.04912 — Lim, Zohren, Roberts
- https://papers.ssrn.com/abstract=2460551 — Deflated Sharpe Ratio (abstract via search; direct fetch 403)
- https://reproducible.cs.princeton.edu/ — Kapoor and Narayanan (abstract via search)

Not opened (recalled or blocked): López de Prado, *Advances in Financial Machine Learning* (2018); https://www.mdpi.com/2306-5729/6/11/119 (403); Gu-Kelly-Xiu full text (PDF unreadable here).

## Independent verification (2026-10-01)

Checked by re-opening the primary arXiv/NBER/GitHub pages (abstract level unless stated).

Confirmed
- Audrino and Chassot (https://arxiv.org/abs/2406.08041): HAR with tuned rolling window beats ML on RV+VIX inputs; QLIKE/MSE/realised utility; still a preprint. Stock count on the page is 1,455 (brief says about 1,445; immaterial).
- Christensen et al. sample (https://arxiv.org/html/2601.13014v1): 29 DJIA stocks, 2001-01-29 to 2017-12-31, NN gains 3-5% MSE with RV lags only, elastic net 8.4%, RF 9.9%, NN 10-15% with extended predictors; published in J. Financial Econometrics (2022).
- Shu, Yu, Mulvey (https://arxiv.org/abs/2402.05272): US/Germany/Japan 1990-2023, out-of-sample, with costs and delay, beats HMM and buy-and-hold on vol, drawdown, Sharpe; accepted for journal publication.
- FinRL (https://github.com/AI4Finance-Foundation/FinRL): not financial advice / not a recommendation to trade real money; points to FinRL-X for production; 16.5k stars.
- Lim, Zohren, Roberts (https://arxiv.org/abs/1904.04912): 88 futures, more than 2x Sharpe before costs, advantage holds only up to 2-3 bp costs.
- Gort et al. (https://arxiv.org/abs/2209.05559): 10 cryptos, test window 2022-05-01 to 2022-06-27 only.
- Gu, Kelly, Xiu (https://www.nber.org/papers/w25398): trees and NNs best; momentum, liquidity, volatility dominant.

Corrected / weakened
- The abstract of Christensen et al. says ML "beats the HAR lineage" even with only RV lags, which is stronger than the brief's "trees underperformed" framing; the detailed result is NN-only (3-5%, 5-10% significance), and trees/boosting are mixed or worse. Gradient boosting specifically lagged in that study, so "LightGBM by default" is NOT supported for volatility; use HAR first, an NN or elastic net/RF only as an optional challenger.
- The NBER abstract of Gu-Kelly-Xiu says "large economic gains" and Sharpe "doubling"; the brief's R-squared figures (about 0.4% / 0.3%) are not on the page and stay RECALLED. Do not treat gross portfolio Sharpe as net of costs.
- Gort et al. is a two-month window containing two crypto crashes; it supports "overfitting detection helps", not "DRL is profitable". Brief's reading stands.

Unverifiable here
- Hansen-Lunde, Corsi, Barndorff-Nielsen/Shephard, Lee-Mykland, Dumitru-Urga, Avramov et al., Bailey-Lopez de Prado, Kapoor-Narayanan, AFML, Millea survey, hmmlearn/statsmodels doc claims: not re-opened in this pass.

Missed considerations (owner constraints, section C)
- Alpaca free-tier equity data is IEX-only and delayed/limited; realised-variance and jump tests on single-venue minute bars are noisy. At $1k-$10k, US pattern-day-trader rules (4+ day trades in 5 days on margin accounts under $25k) constrain intraday designs; a cash account or swing horizon avoids this.
- Near-zero budget favours daily-bar GJR-GARCH/HAR with range estimators and a rule-based regime; heavy ML and DL add compute and overfitting risk with little expected edge at this size.

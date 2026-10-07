# 10 — Calibration, confidence combination and position sizing

Research date: 2026-10-01. Labels: **FETCHED** = page opened this session (abstract page or HTML full text; stated which).
**RECALLED** = from memory, not opened. **DERIVED** = my own arithmetic, shown so it can be checked.
Several PDFs (Niculescu-Mizil & Caruana, MacLean-Thorp-Ziemba, Cederburg et al., DeMiguel et al.) downloaded but could not
be parsed in this environment; for those I rely on abstract pages only and say so.

## 1. Questions asked

1. How do Platt / isotonic / beta calibration and conformal prediction behave with little data and under drift?
2. Is there a principled way to merge five heterogeneous "confidences", or should one meta-model be trained on
   out-of-sample outcomes? Can LLM-stated confidence be trusted?
3. What does the literature say about Kelly under parameter uncertainty, fractional Kelly, volatility targeting and
   drawdown-based de-risking?
4. What concrete rule should replace the docs' confidence formula and sizing rule?

## 2. Findings

### 2.1 Calibration methods and data needs

| # | Finding | Source | Basis | Conf. |
|---|---|---|---|---|
| F1 | scikit-learn (v1.9.1 docs) states sigmoid/Platt suits small samples and symmetric distortion; isotonic is more general but "more prone to overfitting, especially on small datasets"; isotonic matches or beats sigmoid only with roughly >1,000 calibration samples. The calibrator must be fitted on data disjoint from the classifier's training data, otherwise it is biased toward 0/1. | https://scikit-learn.org/stable/modules/calibration.html | FETCHED | high |
| F2 | Niculescu-Mizil & Caruana (ICML 2005): boosted trees/stumps and SVMs show a sigmoid-shaped distortion (probabilities pushed away from 0 and 1); naive Bayes pushes toward 0/1; neural nets and bagged trees were well calibrated; after calibration boosted trees, random forests and SVMs gave the best probabilities. The paper quantifies data needs for Platt vs isotonic (I could only open the abstract; the ~1,000-case crossover is corroborated by F1, the detailed learning curves are RECALLED). | https://mlanthology.org/icml/2005/niculescumizil2005icml-predicting/ | FETCHED (abstract) | high / medium for the crossover detail |
| F3 | Beta calibration (Kull, Silva Filho, Flach, AISTATS 2017): logistic calibration assumes normal per-class scores and cannot represent the identity map, so it can make an already-calibrated model worse; the beta family fixes both and is as easy to fit as a logistic curve; evaluated on naive Bayes and AdaBoost. Three parameters (RECALLED; the abstract page did not state the count). | https://proceedings.mlr.press/v54/kull17a.html | FETCHED (abstract) | high |
| F4 | Kumar, Liang, Ma (NeurIPS 2019): scaling methods (Platt/temperature) are sample-efficient, O(1/eps^2), but their true calibration error cannot be verified and is typically under-reported; histogram binning is verifiable but needs O(B/eps^2); a scaling-then-binning calibrator needs O(1/eps^2 + B). | https://arxiv.org/abs/1909.10155 | FETCHED (abstract) | high |
| F5 | DERIVED: with n independent outcomes in one confidence bin, the standard error of the observed hit rate is about sqrt(0.25/n). To tell a true 55% bin from 50% at two standard errors needs n ≈ 400 **in that bin**; to resolve 52% vs 50% needs ≈ 2,500. Overlapping/serially correlated trades reduce effective n further. | own arithmetic | DERIVED | high |
| F6 | Guo et al. (ICML 2017): modern deep nets are poorly calibrated; one-parameter temperature scaling fixes most of it in-distribution. | https://arxiv.org/abs/1706.04599 | FETCHED (abstract) | high |

### 2.2 Calibration under non-stationarity

| # | Finding | Source | Basis | Conf. |
|---|---|---|---|---|
| F7 | Ovadia et al. (NeurIPS 2019), large benchmark on image/text/tabular-ad classification under shift: post-hoc calibration (temperature scaling) "falls short" as shift grows; methods that marginalise over models (deep ensembles) held up best. Not a finance study. | https://arxiv.org/abs/1906.02530 | FETCHED (abstract) | high |
| F8 | Adaptive Conformal Inference (Gibbs & Candès 2021): update alpha_{t+1} = alpha_t + gamma(alpha − err_t). Distribution-free guarantee that long-run average miscoverage is within (max{alpha_1, 1−alpha_1}+gamma)/(T·gamma) of target. Tested on stock volatility (GARCH(1,1), rolling 5-year window, four stocks chosen from twelve) where the non-adaptive method lost coverage around 2008. Caveats stated in the paper: the guarantee is a long-run frequency, not per-step or conditional coverage; sets can become infinite; quality depends on the score. | https://ar5iv.labs.arxiv.org/html/2106.00170 | FETCHED (full HTML) | high |
| F9 | Barber, Candès, Ramdas, Tibshirani ("Conformal prediction beyond exchangeability"): weighting recent calibration points gives a bounded coverage gap under drift; validated on electricity and election data, not on returns. | https://arxiv.org/abs/2202.13415 | FETCHED (abstract) | high |

Implication: no calibration method is "fit once". All assume the calibration sample resembles the future. Conformal
methods give honest *interval* coverage on average; they do not turn a weak classifier into a tradable probability.

### 2.3 Combining heterogeneous confidences; meta-labelling; LLM confidence

| # | Finding | Source | Basis | Conf. |
|---|---|---|---|---|
| F10 | Ranjan & Gneiting (JRSS-B 2010): any non-trivial weighted average of two or more distinct calibrated probability forecasts is necessarily **uncalibrated** and lacks sharpness. The fix is to recalibrate the pooled forecast on outcomes (beta-transformed linear pool). Demonstrated on simulations and precipitation forecasts. | https://ideas.repec.org/a/bla/jorssb/v72y2010i1p71-91.html | FETCHED (abstract) | high |
| F11 | Meta-labelling (López de Prado, *Advances in Financial Machine Learning*, 2018, ch. 3): a primary model picks the side; a secondary classifier, trained on realised outcomes of the primary signals, outputs P(primary is right), used to filter and size. | book | RECALLED | high (concept) |
| F12 | Meyer, Barziy, Joubert, "Meta-Labeling: Calibration and Position Sizing" (J. Financial Data Science): six sizing algorithms with calibrated and uncalibrated probabilities; fixed sizing functions improved significantly with calibration, sizing functions estimated from training data gained nothing significant. I saw only the abstract via search snippet; sample, period and cost treatment **unverified** (I recall the experiments being largely on simulated data — low confidence). | search snippet (Wikipedia "Meta-Labeling" result); Wikipedia page itself returned 404 on fetch | search-snippet only | medium |
| F13 | Xiong et al. (ICLR 2024), five LLMs incl. GPT-4 on QA/reasoning sets: verbalised confidence clusters in 80–100%, often multiples of 5; vanilla GPT-4 ECE ≈ 0.18, GPT-3.5 ≈ 0.38; failure-prediction AUROC 62.7% (GPT-4) and 55.1% (GPT-3.5), i.e. little better than chance; self-consistency sampling helped (GSM8K AUROC 54.8% → 92.7%) but no method was consistently best and all struggled on professional-knowledge tasks. | https://ar5iv.labs.arxiv.org/html/2306.13063 | FETCHED (full HTML) | high |
| F14 | Tian et al. (EMNLP 2023), ChatGPT/GPT-4/Claude on TriviaQA, SciQ, TruthfulQA: verbalised confidence was better calibrated than token probabilities (~50% relative ECE reduction). This is factual QA with ground truth, not market prediction. | https://arxiv.org/abs/2305.14975 | FETCHED (abstract) | high |
| F15 | ConfTuner (NeurIPS 2025) still describes LLM overconfidence as an open problem in 2025 and says prompt-based fixes have limited effectiveness; needs fine-tuning with a proper scoring rule. | https://arxiv.org/abs/2508.18847 | FETCHED (abstract) | high |
| F16 | Halawi et al. 2024: a retrieval-augmented LLM system approaches the human crowd on forecasting-platform questions. Abstract only; calibration details not verified. No paper I opened measures LLM-stated confidence on short-horizon asset returns. | https://arxiv.org/abs/2402.18563 | FETCHED (abstract) | medium |

Answer to Q2: there is no principled closed-form way to merge "signal", "data", "model", "thesis" and "execution"
confidence, because they are not probabilities of the same event (F10 shows even same-event calibrated forecasts cannot be
averaged). The defensible construction is a single supervised model of the trade outcome, trained and calibrated on
out-of-sample outcomes, with the five components as **inputs** or as hard gates. LLM-stated confidence is an untrusted
feature; it earns weight only if it adds out-of-sample skill.

### 2.4 Kelly, fractional Kelly, volatility targeting, drawdown control

| # | Finding | Source | Basis | Conf. |
|---|---|---|---|---|
| F17 | DERIVED (standard result, continuous approximation g(f)=mu·f − sigma^2·f^2/2): betting c × Kelly earns (2c − c^2) of the optimal growth. Half-Kelly → 75% of growth with half the volatility; 2× Kelly → zero growth; beyond 2× → negative. Over-betting is penalised far more than under-betting. Consistent with MacLean, Thorp & Ziemba, "Good and bad properties of the Kelly criterion" (search snippet; PDF unparsed). | https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf | DERIVED + snippet | high |
| F18 | Baker & McHale (Decision Analysis 2013): Kelly uses a point estimate of the win probability; under parameter uncertainty the bet should be **shrunk**; shrunken Kelly beat raw Kelly in simulation and on tennis betting data. | https://ideas.repec.org/a/inm/ordeca/v10y2013i3p189-199.html | FETCHED (abstract) | high |
| F19 | Metel (arXiv 1701.02814): estimation error causes over-betting; in simulated horse-race experiments an uncertainty-aware adjustment returned 18.48 vs 18.13 for raw Kelly, 13.27 for blanket half-Kelly and 27.46 with true probabilities. Simulated data only. Takeaway: shrink in proportion to how uncertain each estimate is, not by one global fraction — and most of the loss is from not knowing the probabilities at all. | https://ar5iv.labs.arxiv.org/html/1701.02814 | FETCHED (full HTML) | medium |
| F20 | Chopra & Ziemba (J. Portfolio Management 1993): errors in means are roughly ten times as damaging as errors in variances. | search snippet | snippet + RECALLED | medium |
| F21 | Busseti, Ryu, Boyd, "Risk-Constrained Kelly Gambling": constraint Prob(W_min < alpha) < beta is guaranteed by E[(r'b)^(−lambda)] ≤ 1 with lambda = log beta / log alpha; convex; in their experiments the bound was within ~30% of Monte-Carlo drawdown risk and RCK beat fractional Kelly at equal drawdown risk. Assumes the return distribution is known. | https://ar5iv.labs.arxiv.org/html/1603.06183 | FETCHED (full HTML) | high |
| F22 | Grossman & Zhou (Mathematical Finance 1993): under the constraint W_t ≥ alpha·M_t (M = running peak), the optimal CRRA policy invests in proportion to the surplus W_t − alpha·M_t. This is the theoretical basis for linear drawdown de-risking. | https://ideas.repec.org/a/bla/mathfi/v3y1993i3p241-276.html | search snippet of abstract | medium-high |
| F23 | Moreira & Muir (J. Finance 2017): scaling exposure by inverse realised variance produced large alphas and higher Sharpe for market, value, momentum, profitability, ROE, investment factors and currency carry. Monthly factor portfolios; abstract does not address trading costs. | https://www.nber.org/papers/w22208 | FETCHED (abstract) | high |
| F24 | Cederburg, O'Doherty, Wang, Yan (JFE 2020, 103 equity strategies): volatility-managed portfolios do **not** systematically beat unmanaged ones in direct comparison; the spanning-regression alphas are not implementable in real time; out-of-sample versions earn lower Sharpe/CER, due to structural instability. | https://experts.arizona.edu/en/publications/on-the-performance-of-volatility-managed-portfolios/ | FETCHED (abstract) | high |
| F25 | Harvey et al. (J. Portfolio Management 2018; 60+ assets, daily data from 1926): volatility targeting raises Sharpe only for risk assets (equity, credit); negligible Sharpe effect for bonds, currencies, commodities; but it reduces the likelihood of extreme returns across all asset classes. SSRN returned 403; from search snippet. | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3175538 | search snippet | medium |

Answer to Q3: volatility targeting is defensible as a **risk-stabilising** device (F25), not as a source of return
(F24). Full Kelly is indefensible when the edge is estimated; fractional Kelly is a crude but directionally correct
shrinkage (F17–F19); an explicit drawdown constraint (F21, F22) is better grounded than a "risk-of-ruin check" left
undefined.

## 3. What this means for the JARVIS design documents

- **v3 Confidence Calibrator ("Signal, Data, Model, Thesis and Execution confidence → calibrated Overall Confidence")** —
  *contradicted as specified*. The docs give no formula, and no averaging or product formula can be calibrated (F10).
  "Data confidence" and "execution confidence" are not probabilities of the trade outcome at all.
- **v3 "Walk-forward calibration; isotonic/Platt; reliability curves"** — *supported in principle*, weakened in practice:
  isotonic needs ~1,000+ independent outcomes (F1), reliability curves need hundreds per bin (F5). Today JARVIS has ~123
  daily rows for one ticker and zero validated out-of-sample trades. Calibration cannot exist before a trade/outcome
  history does.
- **v3 sentence "risk is sized from downside and liquidity, not confidence alone"** — *supported* (F17–F20).
- **Worked examples "confidence 72%" (v1 BTC) and "82%" (v2 ETH)** — *internally incoherent*. DERIVED: if 72% were a
  calibrated probability of +1.6% before −0.8%, Kelly is f* = p/L − q/W = 0.72/0.008 − 0.28/0.016 ≈ 72× leverage, and
  expected value is +0.93% per trade before costs — an edge no intraday momentum signal plausibly has. Either the number
  is not a probability, or the $25 position is absurd. Honest calibrated probabilities for short-horizon direction sit
  within a few points of the base rate, and the LLM habit of saying 70–90% (F13) is exactly the failure to avoid.
- **v1 decision rule "Expected upside × probability > expected loss + costs + risk penalty"** — *weakened*: the loss is
  not probability-weighted and "risk penalty" is undefined. Replace with the explicit expression in section 4.
- **Position Manager "confidence falls 72% → 54%, exit"** — *weakened*. Mid-trade probability is a different conditional
  event needing its own labelled data and calibration; a confidence-drop exit threshold is one more parameter to overfit.
  v3's own "deterministic exits" is the sound part.
- **Layer E Capital Governor (fractional Kelly, volatility targeting, risk-of-ruin)** — *supported with qualifications*:
  Kelly only as an upper bound with shrinkage; vol targeting for risk control only; risk-of-ruin must be defined.
- **Thesis / bull-bear agents producing confidence** — *weakened*: LLM verbal confidence is overconfident and poorly
  discriminating (F13, F15); QA evidence (F14) does not transfer to return prediction (no evidence found, F16).
- **Capital Governor "no LLM override"** — *supported*; nothing found argues for LLM involvement in sizing.

## 4. Recommended changes (concrete replacement)

**A. Split the five "confidences" by type.**
- Data → deterministic gate (pass/fail checks plus numeric quality features). Fail = no new risk. Not a probability.
- Execution → a cost estimate in basis points (spread + fees + modelled slippage) and a liquidity cap. Enters expected
  value as a cost, not as a confidence.
- Signal, Model, Thesis → inputs to one outcome model.

**B. One calibrated number with a defined event.**
p = P(trade reaches profit barrier before stop/time barrier, net of costs | features at decision time), from a single
meta-model (regularised logistic regression first; gradient boosting only once data allow) trained on walk-forward,
purged out-of-sample outcomes of the primary signals. Features: primary model scores, regime, volatility, spread,
data-quality metrics, and LLM agent structured outputs (including stated confidence) as ordinary features.
Calibration: Platt or beta by default; isotonic only above ~1,000 independent calibration outcomes; calibrator fitted
on a later, disjoint fold; refitted on a rolling window. Monitor Brier score/log-loss and reliability by bin with
binomial intervals; a pre-set degradation trips a de-risk state.

**C. Report uncertainty, not a bare percentage.** Display "similar setups won 54% (n = 212, 95% interval 47–61%)".
Size on the lower bound p_L (e.g. lower quartile of a Beta posterior or bootstrap), which is the Baker–McHale shrinkage
in operational form.

**D. Sizing rule (deterministic, in the Capital Governor).**
1. Edge = p_L·W − (1 − p_L)·L − cost. If Edge ≤ 0 → FLAT.
2. f_Kelly = p_L/L − (1 − p_L)/W (fraction of equity as position notional).
3. Position = min( lambda·f_Kelly with lambda ≤ 0.25; risk cap: loss at stop ≤ r% of equity (r ≈ 0.25–0.5 while
   unproven); volatility cap: target portfolio vol / forecast vol; liquidity and concentration caps ).
4. Drawdown throttle (Grossman–Zhou form): multiply by max(0, 1 − DD/DD_max); at DD_max, halt and require human reset.
5. Risk of ruin defined as Prob(equity falls below alpha before horizon), estimated by block-bootstrap of the realised
   trade ledger (or the Busseti–Ryu–Boyd bound); must be below a stated beta before any size increase.

**E. Bootstrap phase.** Until a strategy has a few hundred out-of-sample (paper) trades, no confidence-scaled sizing at
all: fixed minimum risk unit, and the "confidence" field shows "insufficient history". Kelly terms switch on only after
calibration is demonstrated.

**F. Intervals.** Use adaptive conformal inference around return/volatility forecasts to set stop distances and
"expected range" in alerts; state that coverage is a long-run average.

**G. Exits.** Keep exits rule-based and pre-declared at entry; any "re-scored confidence" exit must be validated as
its own model before use.

## 5. Open uncertainties

- No study opened here measures calibration drift speed for return classifiers; rolling-window length must be found
  empirically on JARVIS's own data.
- Meta-labelling evidence is thin and partly simulation-based; I could not open the JFDS papers. Its real out-of-sample
  value net of costs is unverified.
- No evidence found (for or against) on LLM-stated confidence for market outcomes with current Claude models.
- Thresholds proposed (lambda ≤ 0.25, r ≈ 0.25–0.5%, "few hundred trades") are conservative engineering judgements, not
  literature-derived optima.
- Harvey et al., MacLean-Thorp-Ziemba, Chopra-Ziemba, Grossman-Zhou details come from snippets/recall, not full text.
- Effective sample size with overlapping, correlated crypto/equity trades may be far below the trade count.

## 6. Source list

Fetched: scikit-learn calibration guide; mlanthology (Niculescu-Mizil & Caruana 2005, abstract); PMLR v54 kull17a
(abstract); arXiv 1909.10155, 1706.04599, 1906.02530, 2202.13415, 2305.14975, 2508.18847, 2402.18563 (abstracts);
ar5iv 2106.00170, 2306.13063, 1603.06183, 1701.02814 (full HTML); IDEAS/RePEc pages for Ranjan & Gneiting 2010 and
Baker & McHale 2013 (abstracts); NBER w22208 (abstract); University of Arizona experts page for Cederburg et al. 2020
(abstract).
Search-snippet only: Harvey et al. 2018 (SSRN 3175538, 403 on fetch); MacLean, Thorp & Ziemba; Chopra & Ziemba 1993;
Grossman & Zhou 1993; Meyer, Barziy & Joubert (JFDS).
Recalled, not opened: López de Prado, *Advances in Financial Machine Learning* (2018), ch. 3.

## Independent verification (2026-10-01)

Confirmed (source re-opened):
- F1 scikit-learn 1.9.1: isotonic performs as well as or better than sigmoid only with more than ~1000 samples. https://scikit-learn.org/stable/modules/calibration.html
- F10 Ranjan & Gneiting 2010: non-trivial linear pools of distinct calibrated forecasts are necessarily uncalibrated. https://ideas.repec.org/a/bla/jorssb/v72y2010i1p71-91.html
- F13 Xiong et al., ICLR 2024: verbalised confidence 80-100% in multiples of 5; GPT-4 AUROC 62.7%; GSM8K 54.8% -> 92.7% with sampling+consistency. https://ar5iv.labs.arxiv.org/html/2306.13063
- F24 Cederburg et al., JFE Oct 2020: vol-managed portfolios not implementable in real time, lower OOS Sharpe. https://experts.arizona.edu/en/publications/on-the-performance-of-volatility-managed-portfolios/
- F25 Harvey et al., JPM 45(1) 2018: Sharpe gain only for risk assets, tail-risk reduction across classes. https://quantpedia.com/the-impact-of-volatility-targeting-on-equities-bonds-commodities-and-currencies
- F18 Baker & McHale 2013: shrink Kelly bets under parameter uncertainty. https://ideas.repec.org/a/inm/ordeca/v10y2013i3p189-199.html
- F12 abstract text confirmed (calibration helps fixed sizing functions, not trained ones), via search; sample/costs still unverified.
- Own arithmetic (F5, F17, the 72x Kelly example, +0.93% EV) re-derived and correct.

Corrected / qualified:
- F13: the GPT-4 ECE of 18.0 is an average across eight datasets (not one task); the GPT-3.5 ECE 0.38 and AUROC 55.1 were not re-confirmed. GSM8K gain needed 5 sampled responses, i.e. more LLM cost, which matters at near-zero budget.
- F24 count: source says 103 strategies; brief's "103" matches, ensure the doc does not say 102.

Missed given section C (US resident, $1k-$10k, ~$0 budget):
- FINRA pattern day trader rule: SEC approved removal of the $25k minimum 2026-04-14; effective 2026-06-04 but brokers have until 2027-10-20 to implement, so the broker's own rules (and the old limit on small margin accounts) may still apply. Check the chosen broker. https://international.schwab.com/story/sec-approves-scrapping-25000-day-trader-minimum
- Sizing at $1k-$10k: a 0.25-0.5% risk cap is $2.50-$50 per trade, so fees, spread and fractional-share/min-order limits can dominate; Edge-after-cost test must use real fees.
- Few-hundred-trade calibration needs months of paper trading at low frequency; LLM-in-the-loop self-consistency sampling is unaffordable at ~$0, so use LLM output as a rare feature only.
- Tax: wash-sale and short-term gains treatment (not covered in brief).

Unverifiable here: Chopra & Ziemba 1993, Grossman & Zhou 1993 details, MacLean-Thorp-Ziemba, Lopez de Prado ch. 3 (recalled), Meyer et al. sample and costs.

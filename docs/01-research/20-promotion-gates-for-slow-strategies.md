# 20 - Promotion gates for slow (low-turnover) strategies

Date: 2026-10-01. Constraints: US resident, $1k-$10k own money, solo developer, near-zero budget. Test case: monthly-rebalanced ETF + BTC/ETH long/flat trend book (tens of decisions a year). FETCHED = I opened the document and read the page (PDFs were rendered to images and read); ESTIMATE = my arithmetic, assumptions stated.

## Questions
1. What are the exact DSR / MinBTL / PBO / multiple-testing formulas in the primary papers?
2. How is a slow strategy validated in practice, and what are paper/live trading actually good for?
3. How do we count effective independent trials when variants are correlated (including LLM-generated ones)?
4. What numeric gates (backtest -> shadow -> paper -> micro-live -> scaled live) and kill/demotion rules fit a slow strategy?

## Findings

### 1. Formulas, as printed (all FETCHED)
Notation: SR-hat = non-annualised Sharpe on the sampling frequency of T observations; g3, g4 = skewness, kurtosis (normal: 0, 3); Z = standard normal CDF; gamma = 0.5772 (Euler-Mascheroni).

- **Expected max Sharpe over N independent trials** (Bailey & Lopez de Prado, DSR paper, Eq. 1, p.7; derivation Eqs. 3-6, p.12):
  E[max SR_n] ~ E[SR_n] + sqrt(V[SR_n]) * ( (1-gamma) Z^-1[1 - 1/N] + gamma Z^-1[1 - (1/N) e^-1] ), for N >> 1.
  Code snippet (p.13) matches. The first version for annual units is Pseudo-Mathematics Prop. 2.1, Eq. 2.4, p.9; upper bound sqrt(2 ln N).
- **DSR** (Eq. 2, p.8): DSR = PSR(SR0) = Z[ (SR-hat - SR0) sqrt(T-1) / sqrt(1 - g3 SR-hat + ((g4-1)/4) SR-hat^2) ], with SR0 = sqrt(V[SR_n]) * ((1-gamma) Z^-1[1-1/N] + gamma Z^-1[1-(1/N)e^-1]). Pass at 5% means DSR > 0.95 (p.9). Worked example p.10: N=100, V=1/2, T=1250, g3=-3, g4=10, SR 2.5 annualised gives SR0=0.1132 (daily) and DSR=0.9004 < 0.95; with N=46 it is 0.9505.
  **Key point: T counts return observations (months), not trades.** A 30-year monthly backtest has T=360 whatever the trade count.
- **PSR / MinTRL** (Bailey & Lopez de Prado, Sharpe Ratio Efficient Frontier, Eq. 13, p.11): MinTRL = 1 + [1 - g3 SR-hat + ((g4-1)/4) SR-hat^2] (Z_alpha / (SR-hat - SR*))^2, in observations; the authors warn the moments need >30 observations to be valid.
- **MinBTL** (Pseudo-Mathematics, Theorem 3.1, Eq. 3.2, p.11): MinBTL ~ ( [(1-gamma)Z^-1[1-1/N] + gamma Z^-1[1-(1/N)e^-1]] / E[max_N] )^2 < 2 ln N / E[max_N]^2 years. Authors' example: 5 years of data allows no more than 45 independent configurations before an in-sample Sharpe of 1 is expected by chance (p.11-12). The authors call it "necessary, non-sufficient."
- **Lo's variance** (Pseudo-Mathematics Eq. 2.3, p.8): SR-hat ~ N( SR, (1 + SR^2/(2q)) / y ), y years, q periods per year.
- **PBO / CSCV** (Bailey, Borwein, Lopez de Prado, Zhu; Algorithm 2.3, pp.11-12): build T x N performance matrix M; split rows into S even blocks; form all C(S, S/2) combinations (S=16 gives 12,780); for each, pick the in-sample best n*, take its out-of-sample relative rank w = rank/(N+1), logit lambda = ln(w/(1-w)); PBO = phi = integral of f(lambda) from -inf to 0 (p.13). The paper suggests rejecting PBO > 0.05 (p.14). **Author limitations (Section 5, printed pp.23-24):** hidden trials bias PBO down; if all N strategies have high, similar Sharpe, PBO is high even though skill exists (4th limitation); CSCV must not be used as a search objective.
- **Harvey-Liu-Zhu** (NBER WP 20592, Oct 2014 version, not the RFS print): new factors need t > 3.0 (abstract). Bonferroni p_adj = min[M p, 1] (p.13); Holm rejects H(1)..H(k-1), k = first index with p(k) > alpha_w/(M+1-k) (p.14); BHY threshold (k alpha_d)/(M c(M)), c(M) = sum_{j=1..M} 1/j (Table 4, p.13). Implied annual Sharpe hurdle is t/sqrt(years) (ESTIMATE): 3.0 -> 0.67 at 20 years, 0.55 at 30.

Not opened: Harvey-Liu "Backtesting" (haircut Sharpe). I read preprint versions of the journal papers, so equation and page numbers may differ in print.

### 2. How slow strategies are validated
- **Century-scale, multi-asset evidence** (Hurst, Ooi, Pedersen, JPM Fall 2017, FETCHED): 67 markets, 1880-2016. Net of simulated costs and 2/20 fees Sharpe 0.76 (Exhibit 1). By decade the net-of-cost figure ranges 0.13 (1910s) to 1.70 (1970s), 0.61 (2000s), 0.41 (2010-16). Exhibit 2: 1-, 3-, 12-month signals each positive gross in every decade except 1-month in 2010-16 (0.06); lagging the signal one month degrades shorter signals. Exhibit 3: positive average return in each of 67 markets, mean gross Sharpe ~0.4. The authors treat pre-1985 data as out-of-sample versus Moskowitz et al. Caveat: futures portfolios, not a 10-ETF book. Lemperiere et al. (arXiv 1404.3274, abstract only) report t about 5 since 1960 and about 10 since 1800 and that short-term trends have decayed.
- **A single decade can be 0.13**, so a "bad 3 years" is uninformative about whether the edge exists.
- **Pre-registration protocol** (Arnott, Harvey, Markowitz, FETCHED): define sample ex ante (3a); keep track of everything tried and correlations (2a); document transformations such as vol scaling and require robustness to minor changes (3c); "iterated out of sample is not out of sample" (4b); no true out of sample exists except live trading (4a); refrain from tweaking a running model (5c); include trading costs in both samples (4c). Correlated markets are not independent out-of-sample tests (4a).
- **Parameter plateau**: no paper I opened gives a numeric plateau rule; Hurst Exhibit 2 and the AHM robustness point support requiring neighbours to work. The thresholds below are my design choices.

### 3. Effective independent trials
- Bailey & Lopez de Prado Appendix A.3 (Eqs. 7-9, p.14): N-hat = rho-hat + (1 - rho-hat) M, where rho-hat is the average off-diagonal correlation of M trial return series (rho->1 gives 1, rho->0 gives M). The paper itself says a PCA-style reduction can also be used.
- Lopez de Prado & Lewis (SSRN 3167017, FETCHED): ONC clusters trials by silhouette-scored k-means on a correlation-distance matrix (Sec. 8.1); K = number of clusters; cluster returns are minimum-variance aggregated and V[SR] is estimated across clusters, annualised to a common frequency (Sec. 8.2, p.12). Authors say constant-correlation assumptions bias N and that no exact independent count is feasible.
- Alternatives from genetics (poolr documentation, FETCHED): Li-Ji m = sum f(|lambda_i|), f(x) = I(x>=1) + (x - floor(x)); Galwey m = (sum sqrt(lambda_i))^2 / sum lambda_i; Nyholt m = 1 + (k-1)(1 - Var(lambda)/k).
- ESTIMATE, k variants, equicorrelation rho (eigenvalues 1+(k-1)rho once, 1-rho k-1 times):

| k | rho | Eq. 9 | Li-Ji | Galwey | Nyholt |
|---|---|---|---|---|---|
| 20 | 0.8 | 4.8 | 5.0 | 7.8 | 7.8 |
| 20 | 0.5 | 10.5 | 11.0 | 13.9 | 15.3 |
| 50 | 0.9 | 5.9 | 6.0 | 9.9 | 10.3 |
| 50 | 0.6 | 20.6 | 21.0 | 26.7 | 32.4 |

  Methods differ by up to 1.6x. DSR is insensitive: observed SR 0.6, 30 years monthly, trial-SR sd 0.15, g3=-0.5, g4=5 gives DSR 0.985 / 0.970 / 0.948 / 0.910 for N = 5 / 10 / 20 / 50 (ESTIMATE).
- Hidden trials are the real risk (PBO limitation, and DSR p.3). Rule: every LLM-proposed idea is backtested and logged, even if abandoned; text-different variants with identical signals have rho ~ 1 and add almost nothing.

### 4. Why paper/live cannot validate (ESTIMATE, Eq. 13, Lo, Normal returns, monthly)
- Years of data to reject SR=0 at 95% (MinTRL): true annual SR 0.3 -> 30; 0.5 -> 11; 0.7 -> 5.7; 1.0 -> 2.9. Add fat tails (g3=-0.72, g4=5.78, the paper's Brooks-Kat example) and it is 12.3 years at SR 0.5.
- Years to detect true SR 0.5 vs 0 with 80% power: (2.487/0.5)^2 = 24.7. At SR 0.3: 69.
- SE of annual SR (Lo, SR 0.5): 1.06 at 1 year, 0.61 at 3, 0.34 at 10.
- Monte Carlo, 12% vol, 40,000 paths: a true SR 0.5 strategy shows negative SR in 31% of 1-year and 19% of 3-year periods; a skill-less one shows SR >= 0.5 in 31% of 1-year and 19% of 3-year periods. **A 3-6 month paper run is therefore uninformative about alpha and informative about plumbing.**
- Min backtest length (Theorem 3.1) for a target in-sample max Sharpe of 0.5 by chance alone: N=5 -> 5.7 y; 10 -> 9.9; 20 -> 14.5; 50 -> 20.7; 100 -> 25.6 (ESTIMATE). BTC history is about 11-12 years (RECALLED, not checked), so crypto cannot pass a standalone gate; ETF proxies reach back 20-30+ years only with index/mutual-fund proxies (UNVERIFIED availability).

## What this decides for the JARVIS design

Replace "~300 independent trades + DSR >= 0.95 from paper" with evidence that the sample can actually supply: T return observations, number of independent episodes (bear markets, trend reversals), and cost realisation. Thresholds are design choices, justified by the arithmetic above, not published constants.

**G0 Pre-registration (before any backtest).** Frozen spec: hypothesis with economic rationale, universe, lookback grid (e.g. 4-6 values), vol target, rebalance rule, cost model, sample dates, primary metric = net-of-cost SR. Append-only trial registry; N_eff = max(ONC K, Galwey m) on the registered return series.

**G1 Backtest -> shadow** (all must hold):
1. Pooled multi-asset net SR measured on >= 20 years of monthly data (MinBTL for the registered N_eff must be <= available years at target 0.5); crypto sleeve capped at a small fixed weight and judged only inside the pooled book.
2. DSR >= 0.95 at registered N_eff and trial-SR sd >= 0.15 (floor); if the rule is a pre-registered published design with N_eff <= 5, accept >= 0.90. At 30 years that needs net SR about 0.55-0.6; at 20 years about 0.65 (ESTIMATE from the table). Honest ETF-trend SR may be 0.3-0.5: then the answer is "does not pass," which is a valid outcome.
3. Plateau: >= 80% of pre-registered neighbour cells have net SR >= 0.6 of the chosen cell and the chosen cell is not the grid maximum. Do not use PBO here: a true plateau gives high PBO by the authors' own 4th limitation.
4. Frozen-parameter holdout by asset class (tune on US equity/bond ETFs, test on gold, commodities, international, BTC): net SR > 0 in >= 70% of held-out assets (Hurst: all 67 positive, but cross-market correlation means this is weak evidence).
5. Positive net SR in >= 70% of non-overlapping 5-year windows; costs doubled keeps SR >= 0.75x.
6. Record the backtest's block-bootstrap max-drawdown distribution by horizon (used for kills).

**G2 Shadow (live data, no orders), >= 6 monthly rebalances.** Pass: 100% replay identity (rerunning stored point-in-time data reproduces every target weight), zero unhandled data gaps, >= 2 position changes observed. No performance test.

**G3 Paper (Alpaca paper), >= 3 rebalances overlapping shadow.** Pass: zero unreconciled position breaks, 3 failure drills passed (crash mid-rebalance, duplicate order id, stale feed), order lists equal shadow targets. Paper PnL is not evidence (no fees/impact per briefs 05/08).

**G4 Micro-live, 5-10% of intended capital (about $500-1,000), >= 6 months and >= 20 fills.** Gate on costs only: mean realised one-way cost <= 1.5x model. ESTIMATE: with per-fill sd 10 bps, n=20, SE is 2.2 bps, enough to see a 5 bps miss. Performance rule is non-contradiction: live drawdown below bootstrap p95 for the elapsed horizon.

**G5 Scaled live.** Steps 25% -> 50% -> 100%, >= 6 months each, no more than 2x per step, each requiring G4 conditions plus live-minus-replay tracking error inside the pre-set band and zero severity-1 incidents. Total time to full size >= 18 months. No step is justified by live Sharpe.

**Kill / demotion once live** (benchmark: MC at 12% vol, true SR 0.5 -> max drawdown p95/p99 of 18%/23% over 1 year, 28%/35% over 3, 33%/41% over 5; skill-less median 19% over 3 years; ESTIMATE). Rej-Seager-Bouchaud (FETCHED): 5% drawdown length about 2.14/SR^2 years and depth about 1.50/SR annual-vol units for a 10-year Brownian process; e.g. SR 0.5 gives 8.6 years and 3.0x annual vol. Their caveat: fat tails and autocorrelation make drawdowns longer.
- **Hard, immediate (no statistics):** unresolved reconciliation break, stale data, order-error rate, deployed-capital loss of 25% (owner-set lifetime stop).
- **Yellow (freeze scale-up, halve risk):** live drawdown > bootstrap p90 for the elapsed horizon (about 15% at 1 year, 24% at 3).
- **Red (back to shadow):** drawdown > bootstrap p99 (about 23% / 35%), or live-minus-replay tracking error beyond band two months running (this check has power: it is deterministic).
- **Do not kill on live Sharpe or underwater time** before about 10 years: a sequential test of SR 0.5 vs 0 at 5%/5% needs about 280 months expected (ESTIMATE: ln19 / (mu0^2/2), mu0 = 0.5/sqrt(12)); underwater p95 at 3 years is 2.9 of 3 years.

## Open uncertainties
- Equation numbers are from preprint versions (DSR July 2014; Pseudo-Mathematics April 2014; PBO Feb 2015 revision; HLZ NBER 2014). Published page numbers may differ.
- No paper opened supports the numeric plateau, 0.90 relaxation, 70% window and holdout thresholds; they are my choices and need a simulation on JARVIS's own data.
- Realistic net SR for a $1k-$10k ETF/BTC trend book is unknown (briefs: 0.3-0.7). G1.2 may fail for honest strategies.
- Gaussian MC understates tail risk; bootstrap on the actual backtest is needed.
- Quantopian R^2 < 0.025 (backtest vs live) carried from briefs 08/09, not reopened.
- BTC history length, ETF proxy availability, per-fill sd (10 bps) are assumptions.
- Faber, Moskowitz et al., Harvey-Liu 2015, Bailey-LdP drawdown/"triple penance" not opened.
- Hurst figures are gross of capital-size frictions and tax; after-tax drag unresolved (gap analysis).

## Source list
1. Bailey, Lopez de Prado, Deflated Sharpe Ratio (July 2014 preprint) - https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf - FETCHED
2. Bailey, Borwein, Lopez de Prado, Zhu, Pseudo-Mathematics (Apr 2014) - https://carmamaths.org/jon/backtest.pdf - FETCHED
3. Bailey et al., Probability of Backtest Overfitting (Feb 2015) - https://escholarship.org/content/qt4w1110bb/qt4w1110bb.pdf - FETCHED
4. Harvey, Liu, Zhu, NBER 20592 - https://www.nber.org/system/files/working_papers/w20592/w20592.pdf - FETCHED
5. Lopez de Prado, Lewis, False investment strategies / ONC - https://smallake.kr/wp-content/uploads/2020/04/SSRN-id3167017.pdf - FETCHED
6. Bailey, Lopez de Prado, Sharpe Ratio Efficient Frontier - https://www.davidhbailey.com/dhbpapers/sharpe-frontier.pdf - FETCHED
7. Arnott, Harvey, Markowitz, Backtesting Protocol - https://www.smallake.kr/wp-content/uploads/2023/04/SSRN-id3275654.pdf - FETCHED
8. Rej, Seager, Bouchaud, drawdowns - https://arxiv.org/pdf/1707.01457 - FETCHED
9. Hurst, Ooi, Pedersen, Century of Evidence (JPM 2017 reprint) - https://fairmodel.econ.yale.edu/ec439/hurst.pdf - FETCHED
10. Lemperiere et al., Two centuries of trend following - https://arxiv.org/abs/1404.3274 - FETCHED (abstract only)
11. poolr meff documentation (Li-Ji, Galwey, Nyholt formulas) - https://search.r-project.org/CRAN/refmans/poolr/html/meff.html - FETCHED

## Independent verification (2026-10-01)

Method: re-opened the cited PDFs (rendered Hurst exhibits as images), recomputed all arithmetic independently (own code), re-ran the drawdown Monte Carlo (12% vol, monthly Gaussian, 40,000 paths).

### Confirmed
- MinBTL example: 5 years allows 45 independent configs for E[max]=1 (Pseudo-Mathematics text; recomputed MinBTL(N=45)=4.998y). https://carmamaths.org/jon/backtest.pdf
- MinBTL table in section 4 (N=5/10/20/50/100 -> 5.7/9.9/14.5/20.7/25.6 y at target 0.5): reproduced exactly.
- DSR paper: N=46 gives 0.9505 (printed); N=100 example SR0=0.1132 reproduced; DSR about 0.900 by hand. https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf
- DSR sensitivity (SR 0.6, 30y monthly, trial sd 0.15, g3=-0.5, g4=5): N=5/10/20/50 -> 0.985/0.975(approx; brief says 0.970)/0.948/0.910 reproduced by hand to within rounding.
- MinTRL 30/11/5.7/2.9 years and the fat-tail 12.3 years, power 24.7 and 68.7 years, HLZ hurdle 0.67/0.55: reproduced.
- Hurst, Ooi, Pedersen Exhibit 1: full-sample Sharpe net of fees and costs 0.76; decades 0.13 (1910s), 1.70 (1970s), 0.61 (2000s), 0.41 (2010-16); 67 markets; average per-market Sharpe about 0.4. https://fairmodel.econ.yale.edu/ec439/hurst.pdf
- Rej-Seager-Bouchaud fits: length 2.14*SR^-2 years, depth 1.50*SR^-1 (10-year process, 5% level). https://arxiv.org/pdf/1707.01457
- PBO paper suggests rejecting PBO > 0.05. https://escholarship.org/content/qt4w1110bb/qt4w1110bb.pdf
- HLZ NBER 20592 (Oct 2014): t > 3.0 for new factors. https://www.nber.org/papers/w20592
- Drawdown MC reproduced: true SR 0.5 p95/p99 max DD 18%/23% (1y), 28%/34% (3y), 33%/41% (5y); p90 15%/24%; negative 1y/3y SR in 31%/19%; skill-less median 3y DD 19%; skill-less SR>=0.5 in 32%/20%.
- G4 cost SE: 10 bps/sqrt(20)=2.2 bps. Quantopian R^2 < 0.025 (Wiecki et al. 2016, SSRN 2745220, 888 algos) is real. https://quantpedia.com/quantopians-academic-paper-about-in-vs-out-of-sample-performance-of-trading-alg/

### Corrected / weakened (rely on these instead)
1. Hurst Sharpe 0.76 is NOT a benchmark for the JARVIS book. It is a long/SHORT, vol-targeted (10%), 67-market futures/cash-index portfolio with simulated institutional costs, including 2/20 fees. A long/flat 10-ETF + BTC/ETH book has no short leg and far fewer markets. Per-market average Sharpe is only about 0.4 gross, and the gross-of-cost 1-month signal fell to 0.06 in 2010-16 (all signals positive in every decade, so the brief's "except" wording is misleading; the lagged 1-month signal was negative in the 1880s). Plan on net SR 0.3-0.5 for the real book, as the brief already hints.
2. G1.2 SR thresholds depend strongly on N_eff and assumed trial-SR sd. Hand check with sd 0.15, g3=-0.5, g4=5: at 20 years, SR 0.65 gives DSR about 0.96 at N_eff=10 but only about 0.94 at N_eff=20 (fails 0.95); at 30 years SR 0.6 needs N_eff <= about 15. State the gate as a function of N_eff (about 0.55 at N_eff 5 / 30y; about 0.70 at N_eff 20 / 20y), not a single number.
3. "Do not kill on live Sharpe before about 10 years" is inconsistent with the brief's own SPRT figure of about 280 months (about 23 years; Wald expected sample under H1 is about 254-283 months). Rely on: live Sharpe is never a kill/promote signal inside any horizon an owner will tolerate (about 20+ years); use deterministic checks (tracking error vs replay, costs) and drawdown bands only.
4. The MC drawdown bands are Gaussian and slightly understate p95 for 3y (28% vs fat-tail reality); treat them as floors and replace with bootstrap on the actual backtest (as the brief already notes).
5. DSR 0.970 vs 0.975 for N=10 is a rounding-level difference; the ordering and conclusion (DSR is insensitive to N_eff) stand.

### Unverifiable here
- BTC/ETH history length "11-12 years" (RECALLED): not checked against a primary dataset. Common free daily series start about 2014 (BTC) and 2017 (ETH); either way crypto cannot pass a standalone 20-year gate.
- ETF-proxy availability for 20-30 years (UNVERIFIED in brief; still unverified).
- Harvey-Liu-Zhu Bonferroni/Holm/BHY formulas, Lopez de Prado-Lewis ONC details, poolr formulas, Arnott-Harvey-Markowitz item numbers, Lemperiere t-stats, DSR Eq./page numbers: not re-opened (PDF text extraction of figures/equations unreliable). Preprint-vs-print equation numbers still unchecked.
- Plateau (80%/0.6x), 70% holdout and window thresholds, 0.90 relaxation: design choices with no source; need simulation, as the brief states.

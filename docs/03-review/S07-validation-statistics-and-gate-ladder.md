# S07 Review: validation statistics and the gate ladder (G0-G5, L0)

Reviewer: S07-validation-statistics-and-gate-ladder. Date: 2026-10-02. Target: FINAL-design.md section 7 (gates), with touch points in sections 1, 4, 6, 11 and 14.

**Bottom line.** The gate set is honest but aimed at the wrong decision. The deflation machinery (DSR, MinBTL, PBO, ONC, Galwey) exists to police a search over many candidates. JARVIS launches one published, untuned rule with at most 6 registered cells. For that case the machinery collapses to almost nothing, and the one test that matters (G1b, satellite vs risk-matched null) cannot be powered by any sample the owner will ever have. The live ladder (G4 plus G5, at least 18 months after the first satellite fill) is justified by caution, not by statistical evidence. A leaner set keeps every protection that actually bites and removes roughly 6-10 dev-days and about 14 months of calendar. Statistics are not the main over-build; the executor phase P3 (43-53 dev-days) is, and other reviewers cover it.

## What the design gets right (with evidence)

1. **It counts trials and pre-registers.** Bailey & Lopez de Prado argue that the number of trials is the item most often missing from a backtest, and that a result without it is worthless. G0's frozen spec hash, trader-side registry and cap of 6 grid cells follow that rule. (DSR paper, FETCHED.) Arnott, Harvey and Markowitz give the same protocol: fix the sample ex ante, log everything tried, do not tweak a running model. (FETCHED via summary page; see unverified list.)
2. **It does not use a null that buy-and-hold passes.** My computation below confirms D4's point: an absolute test at N=1 passes plain equity exposure. The benchmark-relative framing (G1b against S0 and S0-RM) is the correct question.
3. **T counts months, not trades.** Section 7 and brief 20 use observations, not fills, in the Sharpe tests. That matches the DSR paper's variable definitions (FETCHED).
4. **It refuses live Sharpe and paper P&L as promotion evidence.** Brief 20's sequential-test arithmetic needs about 280 months to separate Sharpe 0.5 from 0. Rej, Seager and Bouchaud conclude that managers and investors underestimate how long and deep drawdowns can be at a given Sharpe (FETCHED, abstract). Wiecki et al. on 888 Quantopian algorithms found backtest metrics explained under 2.5% of out-of-sample Sharpe variance (FETCHED, secondary summary). So G4/G5 gate on costs, tracking error and drawdown bands, which is right.
5. **The cost test is sized correctly.** Per-fill sd 10 bps over n=20 fills gives SE 10/sqrt(20) = 2.2 bps (ESTIMATE; the sd is an assumption). The power depends on fill count, not elapsed months. This matters for P4 below.
6. **Holdout only where something is tuned.** Plain Faber has no parameter to tune, so a holdout would be theatre. The design says so.
7. **Formula unit tests reproduce published values.** My script reproduces brief 20's DSR examples (0.975, 0.945); the DSR paper text gives 0.9505 at N=46 and 0.90 at N=100 (FETCHED).
8. **"Fail is a valid outcome", plus a sunset rule.** Lempérière et al. report t about 5 since 1960 and about 10 since 1800 on pooled markets, with short trends decayed (FETCHED, abstract). That supports the premise, not an edge in a five-ETF taxable book, so a fail-capable gate is correct.

## What should improve

Computation used below (ESTIMATE, my script, Gaussian-moment DSR as printed in the DSR paper; trial-SR sd 0.15 annual, skew -0.5, kurtosis 5, as in brief 20):

| Years | Registered N | Net SR 0.3 | 0.4 | 0.5 | 0.6 | 0.7 |
|---|---|---|---|---|---|---|
| 20 | 1 (SR0=0) | 0.909 | 0.962 | 0.986 | 0.996 | 0.999 |
| 20 | 3 | 0.778 | 0.886 | 0.950 | 0.981 | 0.994 |
| 20 | 6 | 0.680 | 0.818 | 0.911 | 0.963 | 0.986 |
| 30 | 1 | 0.949 | 0.985 | 0.997 | 0.999 | 1.000 |
| 30 | 3 | 0.826 | 0.930 | 0.978 | 0.995 | 0.999 |
| 30 | 6 | 0.716 | 0.867 | 0.951 | 0.985 | 0.997 |

Reading: at N=1 an ordinary equity-like SR of 0.4 over 20 years already passes, so G1a cannot separate Faber from buy-and-hold. At N=6 the bar is SR about 0.55 (20 years) or 0.5 (30 years). The published rule's in-sample SR is likely above that, so G1a will probably pass on in-sample evidence and carry no information about the satellite's value. Both outcomes make G1a a non-discriminating gate.

Power of G1b (ESTIMATE): SE of an annual Sharpe difference is about sqrt(2(1-rho)/T years). With rho 0.7 / 0.8 / 0.9 and T=30, SE = 0.141 / 0.115 / 0.082. Detecting a true difference of 0.2 at 80% power, one-sided 5% needs T = 2(1-rho) x ((1.645+0.842)/0.2)^2 = 93 / 62 / 31 years. The design already concedes this ("cannot be powered").

### S07-P1 (must): Make G1b the single gating test; demote G1a to a reported statistic
- **Section 7, G1a and G1c.** Report PSR/DSR using N = the registered cell count (no ONC, no Galwey) as information. Remove the "20-year history, else cap at 25%" gating logic and the MinBTL-versus-years check as a pass condition.
- **Why.** The table above. DSR deflates for a search, and the DSR authors say multiple testing should be planned to avoid running unnecessarily large numbers of trials (FETCHED). Harvey, Liu and Zhu's t>3 hurdle is built for hundreds of tested factors (FETCHED, abstract). Plain Faber with 6 cells needs a Bonferroni-type z of only 2.39 (one-sided 5%/6; my arithmetic).
- **Cost.** $0. **Effort.** Saves about 3-5 dev-days in P2 (ESTIMATE, my judgment; P2 is 25-32 dev-days). **Risk.** Loses a cheap absolute sanity check; mitigated because the PSR is still printed and S0-RM already covers the absolute case. Respects all owner constraints.
- **Evidence.** DSR paper (FETCHED); HLZ NBER 20592 (FETCHED abstract); arithmetic above.

### S07-P2 (must): Reduce G1b to one pre-registered paired bootstrap with one gating criterion
- **Section 7, G1b.** Keep the paired block bootstrap on the combined, lot-level after-tax book. Gate only on current criterion (ii): median after-tax CAGR at least S0-RM's, at equal or lower p90 max drawdown. Keep (i) and (iii) as reported numbers.
- **Why.** Criterion (iii) uses the post-2013 slice, about 13 years. With an assumed tracking error of 6.5% a year (my assumption), the SE of the CAGR gap is 6.5/sqrt(13) = 1.8 points. If the true gap is 0 the chance of observing a gap no worse than -1.0 is Phi(0.56) = 71%; at the design's central -1.1 it is 48%; at -2.4 it is 22% (ESTIMATE). A gate that passes anywhere from 22% to 71% of the time depending on luck is a coin flip, not a control. Three stacked thresholds, all tagged DC, also invite hindsight tuning.
- **Pre-state the expected verdict.** The design's own arithmetic puts the taxable central effect at -1.1 to -1.4 points, so (ii) will often fail and retire S-A. Say so in section 1 and treat "retire" as the modal outcome, not a surprise.
- **Cost.** $0. **Effort.** Neutral to -1 dev-day. **Risk.** Fewer gates means the owner relies on one number; mitigated by reporting (i) and (iii).
- **Evidence.** Power arithmetic above; brief 20 sequential-test result; Wiecki et al. (FETCHED, secondary).

### S07-P3 (should): Defer ONC, Galwey and PBO; use a White-style bootstrap max-test for Lab families later
- **Section 7, G1c, G0 N_eff rule.** At launch use N = number of registered cells (conservative: correlated variants over-count). Do not build ONC, Galwey or PBO. When the first Strategy Lab family with more than 6 variants arrives, test the registered family against S0-RM with a White Reality Check bootstrap (maximum statistic over the registered trial matrix, resampling preserves cross-trial correlation), optionally Hansen's SPA refinement.
- **Why.** White's test is built for "does the best of the models I tried beat a benchmark", which is the Lab's exact question, and the bootstrap carries correlation, so no N_eff estimator is needed (White abstract, FETCHED). PBO's own authors note that if all candidates have high similar Sharpe the statistic is high even with skill, and brief 20 already says not to use PBO for plateaus; ONC's authors admit no exact independent count exists (both via brief 20, not reopened). Design G1c still lists PBO and ONC.
- **Cost.** $0. **Effort.** Saves about 3-4 dev-days now (ESTIMATE); adds about 1-2 later if the Lab is used. A Python SPA/RC implementation (the `arch` package) is RECALLED, not checked, including Windows install. **Risk.** The bootstrap max-test is weaker for tiny N; irrelevant at launch.
- **Evidence.** White 2000 (FETCHED, abstract); Hansen 2005 (RECALLED).

### S07-P4 (must): Shorten the satellite ladder and cap the satellite instead of scaling on evidence
- **Section 7, G4 and G5; sections 1 and 11 timeline.**
  - G4 passes after at least 3 satellite month-end decisions (including one entry or exit change), at least 20 fresh-quote fills counted from the first live S0 fill, the existing cost test, drawdown below p95, zero severity-1 incidents, and tracking error in band.
  - Delete G5's evidence-based 25 -> 50 -> 100% steps. Add `satellite_max` to `risk.yaml` (default 25%). Raising it is a risk-preference change: Red-Team note, owner approval, 72-hour cool-off. It is not a statistical promotion.
- **Why.** Every G5 step requires conditions that carry no information about edge: live Sharpe is never used and cannot be (about 280 months). The cost test's power comes from n=20 fills (SE 2.2 bps), not from six months. The 6-month duration is brief 20's choice, not a result from a paper (the design tags it DC). So 18 months of G5 is delay without evidence.
- **Ambiguity to fix.** `stage_fraction` 25 -> 50 -> 100% would end with S-A as the whole account. The design's own table puts that at -$110 to -$140 a year at $10,000. A satellite of 25% is $2,500 and, at -1.1 to -1.4 points, costs about $28-$35 a year (ESTIMATE: 2,500 x 0.011 to 0.014). The lifetime stop (25% of satellite) caps the loss at about $625 (ESTIMATE: 0.25 x 2,500).
- **Calendar.** Satellite at its cap about month 16-19 instead of 31-34 (ESTIMATE: G4 start month 13-16, plus 3).
- **Cost.** $0; no extra LLM load. **Effort.** Saves about 1-2 dev-days of step logic and approval flows plus 14 months of owner attention. **Risk.** Three months sees fewer regimes. Mitigation: loss bands, tracking-error trigger and lifetime stop all remain; none depended on the long ladder.
- **Evidence.** Brief 20 (cost SE, SPRT, Gaussian MC; verified there); Rej-Seager-Bouchaud (FETCHED); Wiecki et al. (FETCHED, secondary).

### S07-P5 (should): Shorten L0 and decouple "first live dollars" from the automation ladder
- **Section 7 L0, section 11 timeline.** Use two S0 tranches (25%, then 100% after one clean live reconcile) instead of 25/50/75/100 over three or more months. State that the ladder governs orders JARVIS places. The owner's own manual S0 holding in RECOMMEND mode is outside the ladder; the design already tracks manual trades through `external_trades` and `adopt`.
- **Why.** Order-error risk is bounded by the per-symbol cap (25% of equity), the entry-notional cap and the 2x modelled-notional cap, none of which scale with `deploy_fraction`. Market risk of the five-ETF mix is the owner's allocation choice, not a system defect. Worst-case slippage on a full turnover of $10,000 at the 10 bps absolute limit is $10 (ESTIMATE: 0.001 x 10,000).
- **Cost.** $0. **Effort.** Saves about 0.5 dev-day plus about 2 months. **Risk.** A first-live defect meets a larger notional; bounded by the caps above. Not investment advice: this is a control-design statement.
- **Evidence.** Design section 6 caps; brief 20 cost arithmetic; reasoning only (no paper tests ladder step counts, see unverified).

### S07-P6 (could): Calibrate the gate on placebos, not on formulas
- **Section 7, G1c null simulation.** Replace the open-ended null simulation with one fixed job: run the whole G1b pipeline on about 1,000 placebo strategies (same time-in-market as S-A, block-shuffled signal dates) and report the false-pass rate. Use it to set the single G1b threshold.
- **Why.** It tests the actual decision rule on the actual data in one afternoon of compute, rather than trusting formulas derived for iid or moment-corrected returns. AHM: simple, economically motivated rules; costs in-sample and out-of-sample (FETCHED, summary).
- **Cost.** $0 (local CPU, minutes). **Effort.** 1-2 dev-days, offset by P1 and P3. **Risk.** Placebo design can leak structure; Red-Team the spec.

### Net effect (ESTIMATE)
Dev-days: -6 to -10 (P1 3-5, P3 3-4, P4 1-2, P5 0.5, P6 +1-2). That is 4-7% of 134-182, so the validation layer was not the main over-build: P2 is 25-32 of 134-182 days (14-24%). Calendar: satellite at cap about month 16-19 instead of 31-34; L0 about 2 months earlier. Monthly cost: $0 (all code runs locally; the validation budget in section 3 is unchanged).

## What I could not verify

- **Hansen 2005, Harvey-Liu 2015, Lo 2002, PBO, Pseudo-Mathematics:** not opened this session (listing only, unreadable PDF, or failed fetch). Their content here comes from recall or brief 20.
- **Arnott-Harvey-Markowitz.** The fetch summary credited different authors for SSRN 3275654; I rely only on generic protocol items.
- **Faber's published SR and sample.** Not opened. I do not know whether Faber's in-sample SR clears 0.55; P1's claim that G1a "probably passes" is a judgment.
- **Tracking error 6.5%, rho 0.7-0.9, trial-SR sd 0.15** are my assumptions; replace with the P2 inventory's actual figures.
- **No source** tests a number of ladder steps or a 3- versus 6-month micro-live. P4 and P5 rest on arithmetic and on the absence of statistical information in live P&L, not on a paper.
- `arch` package availability and Windows behaviour (P3).

## References

1. Bailey, D.H. & Lopez de Prado, M. "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality", J. Portfolio Management, July 2014 preprint. https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf. Formula, N=46 -> 0.9505, N=100 -> 0.90, "plan the number of trials". **FETCHED** (text read).
2. Harvey, C.R., Liu, Y. & Zhu, H. "... and the Cross-Section of Expected Returns", NBER WP 20592 (2014); Rev. Financial Studies 2016. https://www.nber.org/papers/w20592. Hundreds of factors, t>3.0 hurdle. **FETCHED** (abstract page).
3. White, H. "A Reality Check for Data Snooping", Econometrica 68(5), 1097-1126, 2000. https://www.econometricsociety.org/publications/econometrica/2000/09/01/reality-check-data-snooping. Tests whether the best model from a search beats a benchmark. **FETCHED** (abstract page).
4. Arnott, R., Harvey, C.R. & Markowitz, H. "A Backtesting Protocol in the Era of Machine Learning", SSRN 3275654 (2018/19). https://www.smallake.kr/wp-content/uploads/2023/04/SSRN-id3275654.pdf. **FETCHED** (summary only; author attribution in the summary was inconsistent).
5. Rej, A., Seager, P. & Bouchaud, J.-P. "You are in a drawdown. When should you start worrying?" 2017. https://arxiv.org/abs/1707.01457. **FETCHED** (abstract).
6. Lempérière, Y., Deremble, C., Seager, P., Potters, M. & Bouchaud, J.-P. "Two centuries of trend following", 2014. https://arxiv.org/abs/1404.3274. t about 5 since 1960, about 10 since 1800 (pooled futures/spot data). **FETCHED** (abstract).
7. Wiecki, T., Campbell, A., Lent, J. & Stauth, J. "All that glitters is not gold: comparing backtest and out-of-sample performance on a large cohort of trading algorithms", 2016; 888 algorithms, R^2 < 0.025. Via https://quantpedia.com/quantopians-academic-paper-about-in-vs-out-of-sample-performance-of-trading-alg/. **FETCHED** (secondary summary).
8. Brief 20 of this project (with its independent verification): relays PBO, MinBTL, ONC, Lo variance, Hurst et al. Opened in that brief, not here: treat as **RECALLED** for this session.
9. Bailey, Borwein, Lopez de Prado & Zhu, "The Probability of Backtest Overfitting" (2017) and "Pseudo-Mathematics and Financial Charlatanism" (Notices AMS 2014). **RECALLED** (fetch unreadable).
10. Hansen, P.R. "A Test for Superior Predictive Ability", JBES 23, 365-380, 2005. **RECALLED**.
11. Harvey, C.R. & Liu, Y. "Backtesting", JPM 41(1), 13-28, 2015. **RECALLED** (PDF unreadable).
12. Lo, A.W. "The Statistics of Sharpe Ratios", FAJ 58(4), 2002. **RECALLED** (fetch failed).

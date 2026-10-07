# Critique: validation-leakage lens (2026-10-01)

Question: can each strategy and each model/LLM feature actually be validated with the data and time available? Evidence used: briefs 08, 15, 20, 13, plus 18, 16, 22, 02 where the proposals lean on them. "ESTIMATE" marks my own arithmetic from brief numbers; I invented no new facts.

## 0. Cross-cutting findings (they hit every proposal, so they are stated once)

**X1. The G1 gate tests the wrong null.** All five adopt brief 20's G1 (pooled 20-year DSR >= 0.95 at N_eff, plateau, asset holdout, 5-year windows, costs x2). DSR tests whether net Sharpe beats the expected best of N skill-less trials, which is an absolute test against zero. But the claim being made for Strategy A is relative: brief 18 says "roughly -1 to +1 point a year of CAGR versus holding the same assets, with about half the drawdown ... risk reduction, not alpha". Brief 18 also cites Huang-Li-Wang-Zhou: a trend strategy performs "virtually the same" as one based on the historical sample mean. So a long/flat book of positive-drift ETFs can pass an absolute-Sharpe gate simply by owning assets that went up, and buy-and-hold would pass it too. Conversely, brief 20 (verification item 2) says that at SR 0.3-0.5 the honest book will often fail the gate. Either way the gate says nothing about whether A adds value over S0. Only B writes a benchmark gate (after-tax CAGR within 1 point and max DD <= 0.7x S0); D says "after-tax comparison with S0" with no threshold; A, C and E have none. Even B's gate is a point estimate on one path whose drawdown benefit comes from about 2-3 episodes (2008, 2020, 2022), with no deflation. ESTIMATE of power: the standard error of a Sharpe difference between two assets-sets with correlation about 0.8 over 20 years is about sqrt(2*(1-0.8)/20) = 0.14, against a plausible true difference of 0.0-0.2. A paired excess-return test is underpowered too; the honest gate is "does the rule deliver its stated drawdown reduction in a block bootstrap on the difference, at no more than the stated CAGR cost", reported as a range, not a pass/fail on significance.

**X2. Hidden trials outside the registry.** Brief 20 and 08 say hidden trials are the real risk ("iterated out of sample is not out of sample"). Every proposal says the risk-gate and sizing numbers are "design choices ... simulated in G1" (B section 6; C section 6 "to be simulated in G1"; D section 6 "(DC) ... simulated on JARVIS data before they are frozen"; E section 6 "(J)"). These are: the 10% vol target, no-trade band (20%/25%/5 points), per-asset cap (25-30%), drawdown throttle (20-25%), catastrophe stop (15%, 3x ATR, -25%/-28%), collar widths. They are tuned or sanity-checked on the same 20-year history that then produces the DSR, but only the 4-6 value lookback grid enters N_eff. Stops are the worst case: brief 17 (via the proposals' own text) says exits must be backtested with entries, and each stop level is another cell. Nothing records them as trials.

**X3. "Pre-registration" is nominal for the two launch strategies.** Strategy A (Faber 10-month SMA) and Strategy B (Donchian 20/30/60/90) were chosen by the architects after reading in-sample results. Brief 18: "Skip the 5-10 day models. They give the best gross Sharpe but the highest cost" and the choice of 20-90 days is a subset of the paper's nine windows, selected after seeing costs. The paper (Zarattini et al.) is a working paper whose whole evidence is 2015-Mar 2025 daily data, the same data any G1 backtest will use; Faber's evidence is 1973-2012 and the 20-year G1 window (about 2006-2026) overlaps it. The true out-of-sample region is post-publication only (Faber: 2013 onward, about 13 years; Zarattini: Apr 2025 onward, about 17 months, brief 18 open uncertainties). No proposal reports the post-publication slice separately, and none counts the selection among the nine windows or among the universe tickers as trials (only C: "Choosing tickers is a registered trial"). The DSR relaxation to 0.90 "for a published rule with N_eff <= 5" is, per brief 20's own verification, a design choice with no source; it loosens the bar exactly for the strategies the architects prefer, and N_eff = 5 ignores the literature's own selection (trend rules are among the survivors of a large search).

**X4. LLM features cannot be validated on a monthly, 4-6 ETF book.** Every proposal gates LLM features behind "a pre-registered forward ablation on post-cutoff data" over "hundreds of scored decisions" (A section 7; C section 7; D section 7; E A2; B E1). But brief 18 gives about 3-4 round trips a year for the whole ETF book. ESTIMATE: each OFF/ON switch is a sell of the asset plus a buy of the T-bill ETF, so 3.5 round trips is about 14 fills a year, and 8-K or "fund event" flags for 5-6 index ETFs are a handful a year at most (index ETFs do not file 8-Ks). Brief 02 (verification item 7) and brief 13 (section 4.8) say the ablation must be scored on calibration over hundreds of candidate-level predictions, not on P&L, but there are no candidate-level predictions in this book. A (watchlist) produces "watch items, reported, never traded", so there is no outcome the ablation can attach to. Add model retirement: Haiku 4.5 is "not sooner than Oct 15, 2026" (brief 13, 22), the 5.5 models have about 3 clean months (cutoff June 2026, brief 13), and every model change restarts the clock. Conclusion, stated plainly: at launch the Reader/Extractor/Red-Team can pass only the extraction-accuracy gate (golden set), never a gate that earns weight over money. E says this ("Doubtful"); A, B, C, D write falsification criteria ("after 12 months ablations show no gain") that have no power in either direction.

**X5. Slow-strategy promotion arithmetic is not carried through.** G2-G5 copy brief 20, but:
- **G4 "at least 20 fills in 6 months"**: ESTIMATE about 14 fills a year (3.5 round trips x 4 fills), so about 7 fills in 6 months and about 17 months to reach 20. Every timeline (A: P5 "at least 6 months"; D: micro-live months 9-15; B: P4 months 7-12; E: shadow ends about April 2027) assumes 6 months suffices.
- **G4 cost gate for ETFs is below measurement noise**: brief 20 itself computes SE = 10 bps/sqrt(20) = 2.2 bps. For ETFs the model cost is "a few bps" (brief 18: about 2 bps a leg); 1.5x is a 1 bp margin, less than half the SE. The gate makes sense for crypto (25-50 bps), not for the ETF sleeve.
- **G2 dropped brief 20's ">= 2 position changes observed"**: replay identity across six months in which nothing changes passes trivially. All five omit it.
- **G1 "positive in >= 70% of non-overlapping 5-year windows"** on 20 years is 4 windows, so 3 of 4; the percentage is cosmetic.
- **G1 "costs doubled keeps >= 0.75x"** is vacuous for A (a few bps doubled is still a few bps).
- **G1 plateau "chosen cell is not the grid maximum"** is gameable by building the grid so Faber's 10 is mid-grid.
- **G1 "holdout by asset class"**: with a fixed published rule there is nothing tuned on US equity/bonds; all asset classes are known ex post (by the architects, and by Claude as the generator) to have worked; and brief 20's own cite (Arnott-Harvey-Markowitz 4a) says correlated markets are not independent OOS tests. Passing "SR > 0 in >= 70% of held-out assets" is nearly automatic for positive-drift assets.
- **T = 240 monthly observations** overstates information: DSR assumes about iid and the drawdown-avoidance claim rests on about 3 episodes. No proposal requires a minimum count of independent regime episodes (brief 20 section 4 lists this as the actual unit).

**X6. Crypto sleeve "judged only inside the pooled book" has no power over the sleeve.** Brief 20: crypto "cannot pass a standalone 20-year gate" (BTC about 2014, ETH about 2017, unverified). Brief 20's remedy (judge it inside the pooled book at a small fixed weight) means a 10-20% sleeve with true Sharpe of zero barely moves the pooled DSR, so the pooled pass certifies A, not B. All five repeat this; the damage differs by how soon the sleeve is live (A: launch at 10%; E: S3; B: conditional on three things; D: only after S-A G4 and a host move; C: deferred). Needed: an incremental test (book with vs without sleeve) with the post-Mar-2025 slice reported on its own, or an explicit label "unvalidated exploration sleeve, loss capped at X".

**X7. Replay identity is plumbing, not leak detection.** B says "the G2 replay-identity test proves" backtest and live share a code path. It proves determinism on stored data. If a vendor-adjusted series or a mis-dated `available_at` leaks the future, it leaks identically in replay. Brief 15 section 4 (step 0) lists the actual leak tests: correlation tripwire (v1's 0.999 would trip it), shuffled-target at chance, feature-shift test, trial counter. Brief 08 Gate 1: Sharpe > 3 or accuracy > 60% triggers a leakage audit. Only D has the equivalent mechanical tests.

**X8. Claude's own memory contaminates the research loop in a way "sealing" does not fix.** Brief 13/08 (Lopez-Lira-Tang-Zhu; F14): date instructions and masking do not reliably stop recall, and the LLM's hypotheses are "pre-mined" on the history used to test them. The Strategy Lab, Lab Lead, Backtest Engineer, Red-Team and Builder are all Claude models with a June 2026 cutoff (brief 13). Hiding the final years or holdout assets from the Lab's files (C) stops file access, not memory (the model knows 2008, 2020, 2022 and BTC's path). The only data clean of the generator's knowledge is July 2026 onward (about 3 months). Gençay (brief 08 F12, abstract only): only with look-ahead-proof tools plus deflation by actual trial count were LLM strategies rejected, and a Sharpe-35 leaky oracle passed deflation alone, so a mechanical leak test is mandatory, not an LLM reviewer.

## 1. Proposal A: vision-faithful

**Weak or meaningless gates and leakage paths**
- Section 7 "Extra gate for Claude-derived features ... pre-registered with/without ablation; zero weight until it passes": no decisions exist to ablate (X4). Section 13 risk 3 ("after 12 months ... ablations show no gain over the code-only arm") cannot be observed at monthly decision rates.
- Section 2 step 9 "Red-Team Reviewer ... one pre-mortem per position change (~5-15/month)" logged as would-veto/would-not "for ablation". The ~5-15 per month does not match brief 18's ~3-4 round trips a year for the whole book; at the real rate the veto-vs-outcome comparison has tens of observations a year and zero power. It will run forever as narrative. Same-family, same-evidence reviewer also fails to detect hidden trials (brief 02).
- Section 2 step 5(b) "anomaly watch ... watch items that are reported, never traded until a registered strategy covers them": this is an unregistered hypothesis generator reporting to a human who can trade manually. It is a forking path the registry never sees; A has no rule like D's "owner can veto, never add" (section 9).
- Section 4 "Strategy B ... Conditional on Alpaca crypto in Texas ... crypto judged only inside the pooled book" with section 6 "Crypto sleeve <= 10% at launch": X6 applies at full strength. A is the proposal that most plainly lets an unvalidatable sleeve reach live money.
- Section 3 Strategy Lab: "Forbidden: live config, keys, live branch"; logging "every variant" is by instruction and an owner-attended habit, not by a harness that is the only way to run a backtest (brief 08 Gate 0: "the LLM cannot run a backtest outside it").
- Section 7 G1 has no benchmark-relative test (X1) and the "(>= 0.90 for a published rule with N_eff <= 5)" relaxation (X3).
- Section 12 queue (Form 4 overlay, 10-K diff, headline score on "a 20-symbol watchlist ... plus owner single names such as v1's TSLA"): a watchlist that includes a name chosen with hindsight and today's survivors is the survivorship universe that brief 06/gap item 13 says defers single-stock work. Brief 16: post-publication decay of Form 4 and Lazy Prices is unverified, and opportunistic buy clusters on 20 names give a handful of events a year, nowhere near HLZ t > 3.
- No mechanical leakage tests, no Sharpe > 3 tripwire (X7).

**Handled well**
- Explicit fallback "Failing G1 is a valid result: JARVIS then holds the benchmark" and risk 2 ("an elaborate way to hold ETFs").
- Text archive starts in P1 (section 5) and bitemporal `available_at = max(published, first seen) + lag` with joins only `available_at <= decision_time`.
- Narrator numbers are checked by script against the ledger; LLM features have zero weight and "every model-ID change restarts the clock after a 2-4 week old/new shadow". The model-ID change procedure is the only one that names a shadow overlap.
- Sizing: no Kelly until 300 outcomes; no regime/HMM leakage (rule-based, or filtered walk-forward).

No fatal flaw. Largest serious: X6 plus unlogged watch-item channel plus unpowered agent gates presented as real gates.

## 2. Proposal B: evidence-minimal

**Weak or meaningless gates and leakage paths**
- Section 3/5 "E1 Event Sentry (DEFERRED)" and data table "Events (deferred)": nothing says the text archive starts now. Briefs 16 and 22 say first-seen archiving must start immediately because it is the only clean post-cutoff dataset; `first_seen_at` cannot be back-filled. Deferring until "capital >= $2,500" means the later forward test starts from zero. The other four archive from P1.
- Section 7 G1 benchmark gate "after-tax CAGR within 1 point of Strategy 0 and max drawdown at most 0.7x Strategy 0's" is the only benchmark-relative test in the set (credit), but it is a point estimate, not deflated, not bootstrapped, driven by 2-3 episodes, and set to pass brief 18's own expected result ("about half the drawdown"): circular. After-tax CAGR needs the unverified bracket assumption (brief 18, 19 ESTIMATE).
- Section 6 "values marked dagger are design choices ... All of them are simulated in G1": X2. Catastrophe stop "3x ATR(20)" is a free parameter.
- Section 3 R2 "Forbidden: ... leaving any trial unlogged" is an instruction to an LLM, not a harness control.
- Section 4 Strategy B: "goes live only if ... it passes G1 inside the pooled book": X6. It also adopts Donchian 20/30/60/90 chosen after reading results (X3).
- Section 7 G2/G4 same issues as X5: the timeline in section 11 (P4 months 7-12 for micro-live) ignores the fill count.
- Section 2 step 5 and 1: "G2 replay-identity test proves it" (X7).
- Validity of "Strategy 0 skips G1": acceptable (no alpha claim), but the static weights and universe are still choices; low risk.

**Handled well**
- Section 2 step 5: volatility starts as 60-day EWMA; HAR/GJR-GARCH is "adopted only if it lowers out-of-sample error". It is the only proposal that puts an acceptance test on the one statistical model in the system (brief 15 F3: HAR wins only when carefully fitted; HAR needs intraday RV, which free IEX minute bars supply poorly, brief 15 F5).
- No LLM touches a decision, so the LLM-validation problem (X4) is minimised, not solved: the honest approach for this data.
- Whole-share-only holdings and one pre-registered exit per strategy reduce free parameters.
- Section 13 risk 1 correctly concedes G1 failure falls back to S0.

No fatal flaw. Serious: no archive start; benchmark gate in-sample point estimate; X2, X5, X6.

## 3. Proposal C: agents as the quant team

**Weak or meaningless gates and leakage paths**
- Section 3 "Red-Team Reviewer ... Opus 5.5, fresh context ... checks for leakage, survivorship, costs, hidden trials, LLM-memory risk" as G-1 intake: an LLM judgement used as the leakage gate. Same model family as the Lab Lead (brief 02: no heterogeneity under Claude-only), non-reproducible (sampling parameters unavailable on 4.7+, brief 13), and it cannot see trials that were never logged. C has no mechanical future-poisoning, shuffled-target or feature-shift test (X7).
- Section 3 overfitting guardrails: "Holdout assets and the final years of data are not in the lab's directory": file-sealing does not stop model recall (X8). C's own risk 1 notes Claude knows 2008/2020/2022, yet the mitigation is the sealing. "Each hypothesis family gets at most 20 registered variants" per family: 10 families = 200 variants across the lab; family-level N_eff does not deflate across families (brief 08: N must be the cumulative count; brief 20: max(ONC K, Galwey m) on registered series).
- Section 7 LLM gate "Brier score over hundreds of candidate-level predictions": none exist (X4); the Reader's flags in an ETF universe have almost nothing to attach to. Section 13 risk 1's falsifier ("nothing passes G1 across at least 10 registered families") is expected under the null, so it cannot prove the lab wrong.
- Section 3 Post-Trade Reviewer produces "hypotheses tagged post-hoc" feeding the lab: good that they are tagged; but the registry must count them as trials, and nothing says so. P&L-driven hypothesis generation is the classic forking path.
- Nine agents each need owner attention; the lab loop relies on a weekly human who sees G1 results and unseals the holdout "once per spec": each unsealing is one OOS peek that is consumed, which is correct, but a failed spec rewritten and re-submitted is a new spec using the same holdout. Needs a rule: holdout is burned for the family, not the spec.
- G1 absolute-Sharpe null (X1); X3 for A; crypto deferred (good) but "B can never pass a standalone 20-year gate" is then silent on how it will ever be promoted (X6).

**Handled well (the strongest research-loop controls in the set)**
- Section 3: the harness is the only way to run a backtest and logs every run, abandoned ones included; Backtest Engineer "Forbidden: Any command except `jarvis-lab run <spec_id>`", enforced by permission hooks; registry in a separate `lab.sqlite`; holdout and final years withheld; family cap; N_eff from the registry; each idea must cite a published rationale; presumption that LLM ideas are mined from history (brief 13). This is the only proposal that implements brief 08 Gate 0 technically.
- Section 7 LLM gate adds a prompt-injection regression set (hidden text, homoglyphs, fake headlines; brief 13: 99.1% ticker-mapping failure, 65.6% sentiment flips) and a golden set dated after the cutoff.
- Reader isolated (no tools, NFKC, HTML stripped), text can never increase a position (brief 13).

No fatal flaw. Serious: LLM red team as the sole leakage gate; hidden recall not addressed; ablation unpowered; cross-family N.

## 4. Proposal D: failure-first

**Weak or meaningless gates and leakage paths**
- Section 7 G1: "after-tax comparison with S0" with no threshold and no test; same X1/X3. G1 uses the relaxed 0.90 for published rules.
- Section 6 catastrophe stops "about 3x the 20-day ATR for ETFs, and a -25% stop with a -28% limit for crypto (DC)" and "rebalance only on >5-point drift", the vol target, the 20-point per-ETF cap are DC parameters that are not in the registry grid (X2).
- Section 11 timeline "P5 (months 9-15) G4 micro-live" cannot meet "at least 20 fills" (X5). Section 12/13 "measured cost of controls (stop-outs vs no stop, override counterfactuals)" has a few events a year: no power.
- Section 3 Reader "log-only" and section 12 "Reader output given weight: A pre-registered forward ablation ... passes": X4. No scored decisions exist.
- Section 3 Strategy Lab: "spec plus a registry row for every variant", "Forbidden ... editing the registry": a rule, not a harness-only run path as in C.
- Section 2 step 9/F13: "Discretionary trades need expected move >= 3x round-trip cost": D has no discretionary strategy, so "expected move" has no producer; a number nobody validates would gate trades if one is ever added.
- GF failure drills (section 7) validate plumbing, not edge; fine as labelled, but they eat weeks 6-10 (D's own risk 2).

**Handled well (the only proposal with mechanical leakage defences)**
- Section 5: CI **future-poisoning test** (corrupt all data after T, assert every decision up to T is unchanged) catches any look-ahead in feature/signal code and as-of joins, the exact class of defect that sank v1 (`return_pct_t1`); alarm on Sharpe > 3 or accuracy > 60% (brief 08 Gate 1 tripwire; brief 15); "signals use bar t and act at t+1" stated as a backtest rule; as-of snapshot hashed.
- Section 4 plug-in contract: a strategy is a pure function of the snapshot with no I/O, no clock and no broker, so look-ahead has no channel except the snapshot.
- S0 always in shadow gives the paired benchmark series needed for X1.
- Section 9 owner veto only, never an addition, each veto logged with counterfactual P&L: closes the human-in-the-loop forking path.
- Crypto sleeve only after S-A passes G4 and the host moves: X6 handled by sequencing.
- Capital-scaled LLM spend cap (2% x capital/12): validation-wise honest about when LLM spend is justified.

No fatal flaw. Best in this lens. Serious: unpowered Reader gate, DC parameters as hidden trials, G4 timeline.

## 5. Proposal E: staged platform

**Weak or meaningless gates and leakage paths**
- Section 7 G1 has no benchmark-relative term at all (X1) and uses the 0.90 relaxation (X3).
- Section 7 agent ladder: A2 "pre-registered forward test on post-cutoff data only ... hundreds of scored decisions ... restarted at every model change"; then A3 "weight above 0, capped at +/-25% of a leg's size (J)". The cap is a free parameter, and per X4 no scored decisions exist. E concedes this in section 12 (S5 "Doubtful: the sample is too small per model generation"; S6 "Doubtful at monthly decision rates"; S7 "Never for monthly books"). Credit for honesty; but P4 still builds the Extractor golden set and A-ladder for a feature E itself expects never to earn weight, and the Extractor's launch use ("fund events (closure, merger, halt) for held symbols") has an expected event count near zero for 5 index ETFs.
- Section 3 Red-team Reviewer on a fixed Claude family: same as C (no heterogeneity); its `verdict_suggested` is another LLM gate.
- Section 3 Strategy Lab "Forbidden: deleting registry rows; re-running a holdout": instructions only, no harness-only runner.
- Section 6 daily-loss 4%, drawdown throttle 20%, min order $20, cash buffer 2%: (J) parameters untracked (X2). Section 6 sets Strategy A with "no intra-month stop, as published", which removes a free parameter (credit) but leaves most legs unprotected (not my lens).
- Section 7 G4 "5-10%, >= 6 months and 20 fills" and section 11 "shadow ends no earlier than about April 2027; full size at least 18 more months" understate fill-count time (X5).
- Crypto S3 "pooled G1 pass" (X6).
- No mechanical leak tests (X7).

**Handled well**
- Frozen `Evidence{... decision_weight (agents default 0), validation_status}` and typed `TargetBook`: weight is zero by contract; strategies take an `AsOfSnapshot`, the same leak-resistant interface as D.
- Point-in-time contract carries `event_time, vendor_time, available_at, ingest_time, replay_id`; "Backtest news uses available_at = created_at + conservative delay".
- Honest growth table: S5-S10 marked "Doubtful / Never" so the owner is not promised LLM validation that the data cannot deliver.
- Text archive begins at P1.

No fatal flaw. Serious: no benchmark-relative gate; A-ladder unreachable at monthly decision rates; hidden (J) parameters.

## 6. Scores (validation-leakage only)

| Proposal | Score | One-line reason |
|---|---|---|
| A-vision-faithful | 4 | Most LLM surface (6 agents, anomaly watch, red-team per change) with the least ability to validate any of it; crypto sleeve live on a powerless gate |
| B-evidence-minimal | 6 | Smallest leakage surface and an in-sample benchmark gate, but no archive from day one and instruction-only trial logging |
| C-agents-as-quant-team | 6.5 | Best technical control of the research-agent loop; weak on recall contamination and relies on an LLM as leakage gate |
| D-failure-first | 7.5 | Only proposal with mechanical leak tests, pure-function strategies, S0 shadow and veto-only owner |
| E-staged-platform | 6.5 | Honest about what cannot be validated; contracts leak-resistant; no benchmark gate, no leak tests |

## 7. Ideas worth grafting

- D: future-poisoning CI test; Sharpe > 3 / accuracy > 60% alarm; "signal on bar t, act at t+1" written into the backtest; hashed as-of snapshot; strategies as pure functions (D, E share the snapshot interface).
- D: S0 always running in shadow, which supplies the paired series for a proper benchmark-relative gate; owner may veto, never add, with each veto's counterfactual logged.
- C: harness-only backtest runner enforced by permission hooks, registry in a store the lab cannot edit, sealed holdout, variant caps, "post-hoc" tagging of P&L-derived hypotheses, injection regression set.
- B: benchmark-relative criteria in G1 (extend to a paired bootstrap on S0 difference); vol model "adopted only if it beats EWMA out of sample" (apply the same rule to every model); triple condition for crypto.
- E: zero-default `decision_weight` in a frozen Evidence contract and the explicit "Doubtful/Never" outlook for LLM features.
- A: new-versus-old model shadow overlap on each model-ID change; Narrator numbers validated by script with a template fallback (also in C, D, E).
- A, C, D, E: raw text archive with `first_seen_at` from P1.

## 8. Missing from all proposals

1. A benchmark-relative G1 with power stated (X1) instead of absolute DSR, plus a rule for what DSR/N_eff is computed on when the chosen strategy is a published rule.
2. A "parameters are trials" rule: freeze vol target, band, caps, stop levels and throttle before G1, or add them to the registry grid and N_eff (X2).
3. Report the post-publication slice (Faber 2013+, Zarattini Mar 2025+) and the post-June-2026 slice separately, with their (low) power stated (X3, X8).
4. Count independent regime episodes, not months; require a minimum and state that 20 years about 3 episodes (X5).
5. G4 must be re-specified for ETFs: fills accrue at about 14 a year, and a cost threshold of 1.5x a 2 bp model is under the measurement noise (brief 20: SE 2.2 bps at n=20); use a pooled cost test or an absolute-cost band, and set the timeline accordingly.
6. Restore "at least 2 position changes" in G2.
7. Model-retirement-proof LLM validation: archive raw text; when a model is swapped, re-run the successor over the archive from its own cutoff date, so the clock restarts at the successor's cutoff rather than at deployment. Define the consumer of the LLM feature first; for an ETF book there is none, so say the Extractor has nothing to validate until a single-stock sleeve exists.
8. A passive wide-universe event study (collect forward 8-K/news outcomes for hundreds of names as an evaluation label only, never a feature) is the only way to reach hundreds of scored events within months; none propose it, and it is only worthwhile if single-stock trading is a real goal.
9. Incremental test for the crypto sleeve (with vs without), and an explicit "unvalidated, loss-capped" label if it goes live (X6).
10. Deterministic leakage tests beyond poisoning: shuffled-label run, one-extra-bar feature lag, correlation tripwire (brief 15 section 4).
11. A rule that the Lab loop's holdout is burned per family, and that a rewrite after a failed G1 is a new trial in the same family.
12. Formula verification: brief 08/20 flag that DSR/PBO/MinBTL equations were partly recalled and thresholds are design choices needing simulation on JARVIS data; no proposal schedules that simulation before G1 is trusted (brief 20, open uncertainties).

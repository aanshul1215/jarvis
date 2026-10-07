# Critique, lens: quant-edge

Question: is there any honest reason to expect JARVIS to beat after-tax buy-and-hold? Checked against briefs 09, 18, 19 (and 20 for the gates).

## What the evidence base actually supports

1. Strategy A (monthly 10-month-SMA, long/flat) is priced by brief 18 at roughly -1 to +1 point of CAGR versus holding the same assets, before tax. Sources are Faber's self-reported figures and one unverified blog (brief 18, tag U). The only post-publication blog evidence in the brief is negative: 2014-2026 CAGR 8.4% vs SPY 13.6% (U, low confidence). Huang et al. find trend profit is "virtually the same" as a historical-mean strategy (briefs 09, 18). That is risk management, not forecasting.
2. Taxable-account hurdle (brief 19, ESTIMATE): +1.0 to +1.5 points a year at 8% gross, up to +2.6 in the top bracket, +2.5 to +2.9 for BTC-like 15% gross. The stylised model assumes 100% short-term realisation, so it is an upper bound for an ETF book that holds winners over a year (brief 18 puts the true gap at 0 to 0.9). It is close to realistic for a daily Donchian crypto sleeve. It also ignores the loss of qualified-dividend treatment on short-held ETFs and wash-sale disallowance (brief 19, open uncertainties).
3. Therefore in a taxable account the expected after-tax alpha of A is roughly -1 to -2.5 points. Only an IRA (brief 19, point 2) removes that, and Alpaca IRA fees, crypto support and the funding/lock-up terms are unverified.
4. Strategy B (BTC/ETH Donchian) has unknown net Sharpe (brief 18 verification: 0.3-0.8 is illustrative only). The source is one non-peer-reviewed working paper whose headline "net" results use 10 bps, versus Alpaca's 25-50 bps (brief 18). Plan range for any careful solo book: net Sharpe 0.3-0.7, with large decay (brief 09).
5. G1 in brief 20 uses net-of-cost Sharpe as the primary metric, tested against zero after deflation. It is not a test against the benchmark. Brief 20's own open item: "after-tax drag unresolved".

Honest headline for the owner: no proposal can honestly promise to beat after-tax buy-and-hold. Plausible deliverable is lower drawdown at about benchmark or slightly lower return, and in a taxable account the expected sign is negative. The proposals differ mainly in how plainly they say this and whether their gates can act on it.

## Defects shared by all five (judged below as "shared")

S1. G1 is a test against zero, not against the null. DSR >= 0.95 at N_eff tests whether the Sharpe differs from zero after deflation (brief 20, section 1). A plain long-only ETF portfolio over 20 years also clears that bar, and "positive in 70% of 5-year windows" and "positive net SR in 70% of held-out assets" are likewise passed by buy-and-hold. Passing G1 therefore says nothing about beating the benchmark. A, C and E copy brief 20 verbatim and have no benchmark or tax gate in G1. D says "after-tax comparison with S0" with no threshold. Only B states a numeric benchmark gate.

S2. Even a proper paired test cannot be powered. Edge of about +/-1 point against tracking error of several points is an information ratio of roughly +/-0.2. Brief 20 shows 25 years to detect SR 0.5 against 0 at 80% power, and 69 years at SR 0.3, and the difference test is harder. No proposal says that the beat-the-benchmark claim is unprovable by any available sample and that the decision must therefore be made on priors, cost, drawdown and tax dominance.

S3. The strategy that goes live is not the strategy with evidence. Faber's evidence is the plain, equal-weight 10-month SMA with no stops, no vol scaling, no bands and no drawdown throttle (brief 18). All five layer on a 10% vol target, no-trade bands, a drawdown throttle, T-bill sleeve, whole-share rounding and catastrophe stops, then use the "published rule, N_eff <= 5, DSR >= 0.90" relaxation (A, B, C, D, E). Brief 18 says vol targeting is contested out of sample (Cederburg: lower certainty-equivalent in 72 of 103 cases, secondary). With leverage capped at 1.0 it only de-risks, so it is a pure return drag in the calm regime and a sell-after-the-fall in the stress regime. No proposal runs an ablation of each overlay against the plain rule, or states the cumulative CAGR cost.

S4. No risk-matched null. Comparing a half-drawdown trend book to a full-risk buy-and-hold flatters trend. A 50/50 blend of the same buy-and-hold with T-bills also halves drawdown, in a taxable account with lower tax and no whipsaw. Only that comparison tells you whether trend adds anything beyond holding less risk.

S5. Post-publication window not examined separately. Faber's 2013 sample overlaps the proposed 20-year G1 window (about 2006-2026), so about 7 of 20 years are in-sample for the published rule. The only genuinely out-of-sample years (post-2013) are where the blog (U) shows lag. None of the five reports G1 on post-publication years alone or sets a prior from McLean-Pontiff decay (26% out of sample, 58% post-publication; brief 18).

S6. IRA lever under-specified. All five treat "move A into an IRA" as a later optimisation. It is the single largest improvement in after-tax expectancy (brief 19, point 2), but none states its binding constraints: $7,500 a year contribution cap (so a $10,000 book cannot fully move in year 1), lock-up to 59.5 for money the owner may need, fees unverified (a $10 fee is 1% of $1,000), and that crypto stays taxable. None makes "IRA yes/no" the first decision that fixes whether A is run for return at all.

S7. No lot-level after-tax simulation inside the backtester. The tax hurdle is a stylised brief number. The owner's real answer needs lot-level ST/LT, wash-sale and dividend-qualification handling run on the actual signal series, producing an after-tax CAGR gap against S0 before any engineering past the data layer.

S8. The agent ablation gates are almost certainly unpassable inside a model's lifetime, and the proposals mostly do not say so. A monthly book yields tens of decisions a year (briefs 00 gap analysis, 20); ablation needs hundreds of scored decisions after the model cutoff, restarted at every model-ID change (brief 22). Only E states the outlook ("Doubtful"). The honest default is that agents stay off the money permanently.

## Per-proposal attack

### A-vision-faithful (score 5.5)

- FATAL (lens): G1 section 7 has no benchmark or tax test. "G1 Backtest: >= 20 years pooled monthly; DSR >= 0.95 at N_eff (>= 0.90 for a published rule with N_eff <= 5); plateau; holdout by asset class; >= 70% positive 5-year windows; costs x2" can be passed by buy-and-hold. The benchmark appears in section 4 ("compared after cost and tax") and in the fallback sentence "Failing G1 is a valid result: JARVIS then holds the benchmark", but failing G1 is a Sharpe-vs-zero failure, not a benchmark failure. A strategy expected at -1 to -2.5 points after tax can be promoted and scaled to G5. Briefs 18, 19.
- Section 13 risk 2 repeats "A is about -1 to +1 point of CAGR" and never adds the 1.0 to 1.5 point tax hurdle (brief 19) or the contrary blog evidence.
- Opportunity Scanner "anomaly watch" (step 5b): price/volume z-scores, 8-K items, Form 4 clusters, news spikes over 20 symbols, "reported, never traded". Reported to the owner, they will be traded discretionarily; that is an unregistered strategy with no trial log, the multiple-testing problem of brief 09 ("scanning more of them continuously raises the multiple-testing burden rather than the edge"). No guard against owner trades on watch items (compare D).
- Step 10 "cost gate: expected gross move >= 3x measured round trip" has no input: SMA/Donchian rules produce no expected move. Either idle or arbitrary.
- Crypto sleeve B is registered in P2 with A, pooled in G1 ("crypto judged only inside the pooled book"). Pooling lets a sleeve with no standalone evidence (cannot pass standalone, brief 20) borrow the ETF sleeve's significance. Sleeve-level taxable hurdle is about 2.5-2.9 points of tax plus 0.7-1.2% cost (briefs 18, 19) against a net Sharpe that is "UNKNOWN".
- Red-Team "5-15 position changes a month" and ablation in P4: a 5-6 ETF monthly book does not produce that many independent decisions, and the ablation cannot complete before the model retires (S8).
- Strengths: states the null explicitly; "Failing G1 is a valid result"; agents zero-weight; the three biggest risks are honest; the benchmark computed after cost and tax in P1 (but not used as a gate).

### B-evidence-minimal (score 8.0)

- Strongest on the lens. Strategy 0 is first-class ("A static allocation of the same ETFs... If nothing passes G1, JARVIS runs Strategy 0, and that counts as a valid outcome"). It is the only proposal with a numeric benchmark gate in G1: "after-tax CAGR within 1 point of Strategy 0 and max drawdown at most 0.7x Strategy 0's".
- Serious: that gate lets the strategy trail by up to a point a year after tax, which is a drawdown-for-return bargain, not evidence of edge. It should be labelled as such. It is also not risk-matched (S4), and it has no tax model behind the after-tax figure (S7). Given briefs 18 and 19, A in a taxable account will usually fail this gate, which is the honest result, but the proposal does not say it expects that.
- Serious: "Exits: ... a whole-share GTC catastrophe stop at 3x ATR(20)". If ATR is on daily bars, that stop sits only a few percent below price for broad equity and bond ETFs (my arithmetic, not a brief figure), which is far from catastrophic for a strategy that trades monthly. Brief 17 finds stops help trend at best and tight stops lose to costs in every cost-inclusive study. It would sell whipsaw lows and wait until month-end to re-enter, creating short-term losses and wash sales in a taxable account (brief 19). It is a free parameter that the G1 grid ("at most 6 values") does not obviously cover.
- Serious: the whole-share rule at $1,000 ("rounding stays under 10% of each target weight", 4 ETFs at 30% caps) constrains the ETF choice to low-priced funds and adds tracking error against S0 that could exceed the 1-point edge being measured. Not tested in G1.
- Crypto B: "passes G1 inside the pooled book" (S1 pooling problem), but it is correctly conditional and the spot-ETF route is "preferred, if verified" (brief 21, unresearched) which would put crypto exposure at equity cost, possibly in an IRA. Good.
- S3 applies (vol-capped inverse-vol weights, bands, stops, DSR 0.90 relaxation).
- Build order is right: G1 verdict (P1) before runner (P2).

### C-agents-as-quant-team (score 5.5)

- FATAL (lens): the misstatement in risk 2: "Strategy A's honest expectation is about zero against after-tax buy-and-hold". Brief 18 says -1 to +1 before tax; brief 19 adds a 1.0-1.5 point taxable hurdle. After tax the expectation is negative in a taxable account. G1 contains no benchmark or tax criterion at all (S1); G-1 intake only checks a red-team report.
- Serious: the Strategy Lab is "central" (section 10), nine agents, weekly sessions. The evidence on LLM-discovered strategies is that, with leakage-proof tools and deflation by the actual trial count, every one was rejected (Gencay 2026, briefs 02, 08), and an LLM's hypotheses are mined from history it already saw (brief 13). The proposal acknowledges this in risk 1 but still builds the lab before any trade, the whole P2. Honest yield is near zero; the design's main investment is in the part with the weakest evidence.
- Serious: holdout sealing "the owner unseals them once per spec" burns the holdout on each spec; "iterated out of sample is not out of sample" (Arnott-Harvey-Markowitz, brief 20, section 2). No depletion accounting, so the holdout becomes in-sample after a few specs. Up to 20 variants per family also inflates N_eff and so raises the DSR bar, working against the lab's own throughput.
- Serious: owner-in-the-loop researcher degrees of freedom: the owner reads G1 reports and chooses the next hypothesis; the registry logs only the lab's runs.
- Credit: tax hurdle in the cost gate (step 11, brief 19), "B can never pass a standalone 20-year gate" (brief 20), "ideas the LLM came up with are presumed mined", and the failure branch "run on rules only" are honest.
- Reader ablation "Brier score over hundreds of candidate-level predictions" is unreachable on monthly decisions (S8) and the proposal does not say so.

### D-failure-first (score 7.5)

- Good: S0 is "always on, in shadow" with weekly NAV against after-tax S0 on the dashboard; "If nothing beats S0 through G1, JARVIS runs S0, which is a valid outcome"; the thesis states plainly "very little edge to find"; risk 1 says -1 to +1 "before the tax hurdle". Best sequencing for crypto: S-B only after Texas confirmed, host moved off the laptop and "S-A has passed G4", capped at 10% at launch. Owner-override accounting ("owner can veto a trade but never add one", counterfactual P&L logged, manual trade triggers SAFE) is the only handling of discretionary-trading leakage in any proposal. Future-poisoning CI test and the Sharpe > 3 alarm address leakage.
- Serious: G1 "after-tax comparison with S0" has no pass threshold and no tax model (S1, S7). It is a number to look at, not a gate.
- Serious: "Catastrophe stops: about 3x the 20-day ATR for ETFs, and a -25% stop with a -28% limit for crypto (DC)". Same objection as B for the ETF stop (brief 17); the crypto stop is plausible.
- Serious: P2 builds the executor and drills before P3 gives the strategy verdict. Acceptable since S0 also needs execution, but the 10-week plumbing effort is committed before the evidence on A is known. D's own risk 2 flags this.
- Does not mention the spot-ETF route for crypto (brief 21) or IRA funding constraints (S6).
- S3 applies (the vol target, throttle, bands, stops).

### E-staged-platform (score 7.0)

- Good: Strategy A "exits on the monthly SMA signal with no intra-month stop, as published", the only proposal that does not deviate from the published rule for exits. The growth table's "Honest outlook" column ("Doubtful", "Likely never", "Never for monthly books") is the plainest statement of agent and alpha limits in any proposal. Risk 2 quotes the "1-1.5 point tax hurdle" and says the honest answer may be buy-and-hold "with JARVIS as monitor and research lab". The benchmark is always-on shadow.
- Serious: G1 has no benchmark or tax criterion (S1); the benchmark is "compared after estimated tax" only in the strategy section. The after-tax comparison is therefore advisory.
- Serious: the IRA question (S4a) is placed at S4, after the Extractor and crypto, although the evidence (brief 19) makes it the first decision for whether A is worth running. "Evidence trigger, not capital" is right but the sequencing is late, and S6 constraints are omitted.
- Platform overbuild: five frozen contracts, empty slots and an S0-S10 ladder spend solo-developer weeks on capability the proposal itself rates "Likely never". This is its own risk 1. Singling out S4b ($31,500 Norgate) and S9/S10 as roadmap items outside the owner's $1,000-$10,000 range is noise rather than an alpha claim.
- A3 "weight above 0, capped at +/-25% of a leg's size" for a text feature is an unsupported number, but gated behind an ablation that the proposal itself calls doubtful.
- Sizing "sleeve weight x min(1, 10% vol target / forecast vol)" (S3).

## Ranking through this lens

B (8.0) > D (7.5) > E (7.0) > A (5.5) = C (5.5). A and C get the lowest scores because their promotion gates are blind to the benchmark and (A) because the scanner/evidence-card shape invites unregistered discretionary trading, (C) because the central investment is the lab that the evidence says will almost never produce a strategy, plus a misstatement of the after-tax expectation.

## Ideas worth grafting

- B: numeric benchmark gate in G1 (after-tax CAGR gap and drawdown ratio vs Strategy 0). Make it risk-matched and backed by a lot-level tax simulation, and state it as a drawdown-for-return trade, not as alpha.
- B/D/E: Strategy 0 as an always-on shadow and as the default that runs if nothing passes. D's weekly "NAV vs after-tax S0".
- B: put the G1 verdict before the runner (P1 before P2); A, C and E share this ordering.
- B: spot BTC/ETH ETFs as the preferred crypto route if verified; IRA check in P0.
- E: "no intra-month stop, as published" for A; the "Honest outlook" column; the idea that each unlock trigger is explicit and many are "never".
- D: crypto only after the ETF sleeve passes G4 and the host moves; 10% crypto cap at launch; owner veto-only with counterfactual logging; manual trade triggers SAFE; future-poisoning test; Sharpe > 3 alarm.
- C: tax hurdle in the cost gate; holdout sealing (add depletion accounting); cap variants per hypothesis family; "LLM-proposed ideas presumed mined".
- A: "failing G1 is a valid result: JARVIS then holds the benchmark".

## Missing from all five

1. A G1 criterion that tests excess return versus S0, after tax, risk-matched, with an explicit statement that it is underpowered and that the decision rests on dominance (cost, tax, drawdown) rather than a significance test.
2. A risk-matched null (buy-and-hold blended with T-bills to equal volatility or drawdown).
3. A lot-level after-tax backtest (ST/LT, wash sale, dividend qualification) run before the executor, producing the real tax gap for this owner's account type. Using this in place of brief 19's stylised table, which assumes 100% short-term realisation.
4. G1 reported on the post-publication window alone, and a prior set from brief 18's decay figures. A rule that A is not run for return if the post-2013 window trails S0 by more than the tax gap.
5. An overlay-ablation step: plain Faber rule versus each overlay (vol target, throttle, band, stop, whole-share rounding), with every overlay counted as a trial, and no use of the published-rule 0.90 relaxation once overlays are added.
6. A decision tree up front: IRA available and fee acceptable -> run A there for drawdown/discipline; taxable only -> run S0 plus monitoring, unless the after-tax simulation passes. Include the IRA cap ($7,500 a year), lock-up to 59.5 and cross-account wash-sale rule (Rev. Rul. 2008-5).
7. A plain statement to the owner of the expected value: the system's likely return versus holding is around zero or negative after tax; what is bought is drawdown control, discipline and a research record. The owner may reasonably prefer to hold S0 and keep JARVIS as a monitor.
8. The benchmark's own tax cost: a periodically rebalanced S0 in a taxable account realises gains (B's quarterly rebalance); a contribution-only rebalance is the fairer null.

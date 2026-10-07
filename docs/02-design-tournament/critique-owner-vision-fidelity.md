# Critique through one lens: owner-vision-fidelity

Critic: owner-vision-fidelity. Date 2026-10-01. I represent the owner, who asked for a complete end-to-end system that uses AI agents, scans for opportunities, explains every decision, and grows. Brief numbers are cited as in the proposals and 00/00b.

## Summary scores

| Proposal | Score | One-line verdict |
|---|---|---|
| A-vision-faithful | 8.0 | The only one whose pipeline, vocabulary and owner experience the owner would recognise. Deviations are individually justified. Some triggers are unreachable by its own strategies. |
| E-staged-platform | 7.0 | Honest destination-and-staircase framing and the best agent-weight ladder. At launch the owner gets a monthly ETF script and a narrator, and E admits most upper steps are "doubtful/never". |
| C-agents-as-quant-team | 6.5 | The strongest "AI agents" story and the best research guardrails. Drops the scanner and crypto, and most agents run only when the owner attends. |
| D-failure-first | 5.5 | Excellent safety, but it changes what JARVIS is from an opportunity-seeking agent to a ledger with an executor. The owner is treated as a failure source. |
| B-evidence-minimal | 3.5 | Hollowed out. No Claude agent runs in production, no scanner, no news layer, templated email. It is a rebalancer script. |

## What the owner would test any proposal against

From CONTEXT section B/C and v2 section 1 ("USER RECEIVES"): ranked opportunities, why each setup matters, confidence plus downside, action taken or rejected, alerts when the thesis changes, P&L after costs, post-trade explanation, and a goal planner that "rejects unrealistic targets". Add the v3 principles (never chase a target, FLAT valid, rules hold the money, paper to shadow to small live). Add "build on current JARVIS" (a chat assistant on TSLA) and "equities + crypto".

Three facts shared by all five proposals bound what is possible, and the owner should be told them once, plainly:
1. No LLM trading agent has beaten buy-and-hold net of costs after its cutoff (briefs 01, 02, 08). So every proposal keeps Claude off the order path. I do not penalise this. It is the honest limit.
2. At the bottom of the owner's range ($1,000), brief 11's 600x rule gives about $1.67 a month of LLM budget. Every proposal therefore collapses to a nightly Narrator plus owner-attended Claude Code sessions. Only D says this as a formula (`min($15, 2% x capital / 12)`). A, B, C and E state a flat cap ($15, $5, $10, $5) that is not scaled to capital.
3. Time to full size is about 2.5-3 years in every proposal (brief 20 gates). That is evidence-driven, not a fidelity defect.

---

## A-vision-faithful (8.0)

**Strengths**
- Keeps the owner's seven-state machine, the scanner (with a candidate/watch-item split), a team, a confidence concept, a position manager, a ledger, and equities plus crypto. The section 10 table gives a verdict and brief for every owner idea.
- Fidelity to the real v2 outputs: "FLAT/no change, and why" in the daily email, trade emails, a Goal Interpreter that returns a "config diff... explained back", and a planner that "rejects unrealistic targets by showing the backtest's bootstrap return and drawdown range (brief 20)". This is the only proposal that keeps the owner's optional return-goal field and handles it by honest display rather than deletion.
- "Anomaly watch ... 20-symbol watchlist (universe plus owner single names such as v1's TSLA)". It is the only proposal that carries the owner's own TSLA interest forward in any form, and the only one with a visible "opportunity" output (watch items) from day one.
- Evidence Card keeps the owner's five confidence components but shows them separately instead of pooling them (Ranjan-Gneiting, brief 10). A justified deviation that preserves the owner's explainability goal.
- A per-position-change Red-Team in shadow is the nearest honest realisation of Bull/Bear. The extra gate for Claude-derived features (golden set, forward-only evidence, ablation, clock restart) is correct (briefs 02, 22).
- Crypto sleeve kept at launch, capped, with a gap rule, and gated on Texas (brief 21).

**Serious flaws**
- "The roster keeps its names on the dashboard; thirteen members are honest code." Section 2 labels [D]/[S]/[C], which is good. But if the dashboard shows 19 named "agents" while 6 are Claude, it flatters the agent claim. The dashboard should carry the [code]/[stat]/[Claude] label too.
- Spend cap not scaled to capital: "dedicated `jarvis` workspace with a $15/month limit", but the same section says "below $2,400 only the Narrator runs (~$0.65)". At $1,000 a $15 cap is 18% a year of capital (brief 22, brief 11). The cap should be set to about 2% of capital (D's formula). Also unclear whether the Red-Team is on or off below $2,400: step 9 and P4 build it, but the cost rule implies only the Narrator runs.
- Unreachable growth triggers presented as live: "≥ 300 resolved outcomes: calibration curve shown; fractional Kelly cap allowed (brief 10)". A monthly ETF book yields tens of decisions a year (00 section 2, brief 20), so this never fires. B and E say so ("never for monthly books"). A's risk 3 admits the agents may never earn weight but does not say the Kelly trigger is likewise unreachable.
- Internal inconsistency: crypto "≤ 20% after G5; gap rule: a 30% overnight crypto gap must cost ≤ 3% of equity". 20% x 30% = 6%. C states the 6% bound honestly. A's 20% needs either a 10% cap forever or a restated gap rule.
- Largest scope of the five for a solo developer (16 flow steps, 6 agents, scanner plus anomaly watch, evidence card, red-team, lab, goal interpreter). A's own risk 1 flags this. The P0-P4 estimate of about 16 weeks is optimistic.
- Fractional lots accepted as unprotected with a diversified-ETF rationale. The drawdown throttle that is supposed to backstop this lives on the same host (brief 17/23: exits in JARVIS fail if the host dies).

**Fatal flaws:** none found under this lens.

**Missing relative to the owner's v2 "USER RECEIVES"**: the Evidence Card has no "expected range / downside in dollars at the stop". v3's trade email requires "expected range, downside". Easy and deterministic (see grafts).

## E-staged-platform (7.0)

**Strengths**
- Frames the owner's vision as the destination and the launch as step one, with five frozen interfaces (bitemporal record, strategy plug-in, evidence object, agent slot, default-deny gate). The evidence object ("agents default 0; producer; input_ids; validation_status") is the cleanest realisation of v3's "agents produce structured evidence; they do not directly send broker orders".
- The agent ladder A0 to A3 (schema valid on golden set, forward shadow at weight 0, pre-registered forward test on post-cutoff data, then weight capped at plus/minus 25% of a leg) is the best-specified route for Claude agents to earn influence.
- The Narrator report schema has `rejections[]` and `questions_for_owner[]`. It is the only proposal that makes "trades rejected and why" (a v3 daily-summary item) a typed output.
- The growth table (S1 to S10) is the most honest in the tournament: "Doubtful", "Never for monthly books", "Likely never". The owner learns exactly which of their dreams are unreachable at $1k-$10k and which trigger unlocks the reachable ones. Crypto is staged (S3, capital ≥ $3,600, Texas, pooled G1; spot-ETF route first).
- The extractor flags "fund events (closure, merger, halt) for held symbols". That is the only concrete "alert when something changes on a held position" in the tournament.

**Serious flaws**
- Section 13 risk 1 is correct and it is the fidelity problem: "Strategy A could run from a spreadsheet". At launch the owner receives a monthly ETF script, a Narrator and an approval CLI. The upper platform (S5 to S10) is, by E's own table, mostly "doubtful/never". Frozen contracts cost weeks (P0) for slots that may stay null. The platform framing is partly decorative.
- No scanner, no ranked opportunities, no watch items. "Opportunity Scanner -> Code: strategy plug-ins over a fixed universe" removes the owner's headline "scans for opportunities" behaviour. Strategy A has five sleeves, so there is nothing to rank.
- Strategy A "exits on the monthly SMA signal with no intra-month stop" and fractional legs are accepted as unprotected, "backed by diversification, the drawdown halt and the lifetime stop". Those are in-process controls and do not act if the host is down (briefs 13, 17, 23). Whole-share GTC stops would fit E's own contract.
- The Red-Team fires "a few times a year", so the owner's Bull/Bear "challenge before capital is used" is nearly absent at runtime.
- The Narrator-only runtime means "AI agents" at launch is one nightly summary. Honest but thin for "complete end-to-end system which uses AI agents".

**Fatal flaws:** none.

## C-agents-as-quant-team (6.5)

**Strengths**
- The best answer to "uses AI agents": nine named Claude roles with typed hand-offs, forbidden lists and costs, and the clearest statement of how they pay (API for unattended, plan for attended, per brief 22). The lethal-trifecta guardrails (brief 13), sealed holdout ("the owner unseals once per spec"), a 20-variant cap per family, and a harness that logs every run to the registry are the best overfitting defences of the five.
- Ledger Analyst Q&A ("why did we sell gold in March?") is the only proposal that preserves the conversational character of v1 JARVIS (a chat assistant). It also serves the owner's "explain every decision" far better than a nightly narrative.
- Incident Diagnostician and Post-Trade Reviewer map to v2's "post-trade explanation" and v1's "evaluation and learning" layer.

**Serious flaws**
- Scanner and crypto removed with no replacement. Mapping table: "Long/short, intraday, always-on scanner: DROPPED", "Crypto sleeve ... DEFERRED". There is no ranked-opportunity output, no watch list, no candidate concept. The agents work on the research timescale (hypotheses), not on JARVIS's live view of markets. The owner gets agents but no opportunities for them to look at.
- Five of nine agents (Lab Lead, Backtest Engineer, Red-Team, Ledger Analyst, Incident Diagnostician) run only in owner-attended Claude Code sessions "on his subscription". Weekly owner time is 60-90 minutes plus approvals (G0 freeze, holdout unseal, quarantine release, throttle re-arm...). For a solo developer this is a burden. C's own risk 3 notes the team "rests on owner time". If the owner lapses, the "agents" disappear and what remains is a Narrator. Compare this with the owner's "always-on" intent.
- "$0 on Pro" is repeated for most agents, but the brief 22/00 constraint is near-zero spend; whether the owner has a plan is not established. If not, brief 22's $13-21 a month research cost breaks the budget (C says to drop to monthly sessions).
- Heaviest ops overhead: separate Windows user `jarvis-trader`, hook-based deny rules, sealed holdout directories, `lab.sqlite` plus `jarvis.sqlite`, all on an 8 GB laptop where a Claude Code session is "~1 GB or more". It is defensible security, but it is a lot of build for a $1,000 account. P2 "Research Lab" comes before any execution core, so the owner has no running JARVIS for months.
- The Reader (the only agent touching untrusted text in production) starts at P5 / $3,000. Until then the "archive" is tier-0 code only.

**Fatal flaws:** none.

## D-failure-first (5.5)

**Strengths**
- The failure catalogue F1-F14 with a control for each is the best-engineered answer to "never lose money to a stupid bug". Spend cap `min($15, 2% x capital/12)` is the only capital-scaled LLM limit (brief 11/22). Future-poisoning CI test and hash-chained ledger make "every decision reconstructable" literally verifiable (v3 step 9).
- Honest growth table (Postgres/bus only on a second writer; shorting, margin, Kelly "not unlocked inside $10k").

**Serious flaws**
- Re-defines what JARVIS is: "a trading ledger with an executor attached. It is not a forecasting engine." The owner described an opportunity-seeking system with agents. D's mapping omits the Opportunity Scanner as a row, and "Scanner" appears only as "becomes code". There is no watch list or ranked opportunity. The result is "do the boring thing without ever doing something stupid" (section 1). That is legitimate, but it is a different product than the one the owner drew.
- Agents padded with dev tooling: "Change Reviewer: checks each diff... every deploy" and the Strategy Lab are Claude Code sessions, not JARVIS agents. Runtime agents are Reader (log-only), Narrator, Incident Analyst, Red-Team on promotions. Daily owner experience is "about 0 minutes: one ntfy status".
- Treats the owner as a failure mode (F11): "The owner can veto a trade but never add one", loosening limits "waits 72 hours", "a manual trade in the JARVIS account triggers SAFE". These are reasoned, but they override v3's "human approval for configurable exceptions" and v2's "user sets ... recommend / paper / act" permissions. They should be options the owner chooses, not hard rules, since it is the owner's own money (CONTEXT C).
- Crypto is pushed to month 15+ ("S-A has passed G4", host moved). Owner asked for equities + crypto; D is the slowest to deliver any crypto, though the justification (brief 23, 24/7 hosting, Texas unknown) is real.
- Time to something visible: P2 (weeks 6-10) is "a safe paper executor"; the first strategy verdict is week 12. Until P4 (months 3-9) the owner has no daily JARVIS experience.
- Whole-share-only holdings at $1,000: "use fewer and cheaper ETFs so that whole-share weights land within 5 points of target". With about $250 per sleeve, 5 points of weight is about $12-$50 per share, which excludes most liquid ETFs (ETF prices are not in the briefs, so this is my arithmetic and unverified). The $1,000 case may be mostly cash. A, C and E avoid this by accepting fractional lots.

**Fatal flaws:** none.

## B-evidence-minimal (3.5)

**Strengths**
- The leanest, lowest-risk, most-buildable design. Honest about evidence. "Strategy 0 is a valid outcome" is correct. Whole-share-only with GTC stops resolves gap item 15 cleanly in principle.

**Serious flaws (hollowing)**
- Zero Claude agents in production: "No Claude agent sits on the order path... Production runs with the LLM off, at $0" and E1 "DEFERRED". The "agents" are Builder (Claude Code), R1 and R2 (attended weekly/monthly). The owner asked for "a complete end-to-end system which uses AI agents" and for "the agents to be Claude agents". At runtime B has none, even though brief 22 prices a Narrator at about $0.65 a month and every other proposal includes one. B under-delivers what the evidence does allow.
- No scanner: "Opportunity Scanner -> Fixed-universe signals". No watch items, no opportunities, no "why this setup".
- Templated email "OK - no trades". This is the weakest answer to "explain every decision". Gate reason codes exist but nothing turns them into prose.
- News/SEC layer (the owner's "Information Intelligence", their strongest existing asset) deferred to a capital trigger, and "No v1 data or model is reused." No text archiving from day one, which A, C, D and E all do (it is the only clean post-cutoff dataset, briefs 16, 22). B's E1 would start with no history.
- Goal planner reduced to `owner_config.yaml` with "no return-target field". The owner's optional goal is deleted rather than answered.
- Whole-share-only at $1,000: "Share classes are chosen so that whole-share rounding stays under 10% of each target weight". At $1,000 with a 25-30% cap, about $250-$300 per slot, this needs share prices of roughly $25 or less (my arithmetic; ETF prices not in the briefs, unverified). At the bottom of the owner's range, B probably cannot satisfy its own rule and ends up in the T-bill ETF.
- Slowest to anything visible: Streamlit and R1 arrive in P3 (months 3-6). B's own risk 3 ("the owner disengages") is the predictable result.

**Fatal flaws:** none by the strict definition (it loses no money and breaks no hard constraint). Under this lens it comes closest to failing "complete end-to-end system which uses AI agents".

---

## Ideas worth grafting (ordered by value)

1. A: scanner split into candidate (registered strategies) and watch items (anomaly z-scores, 8-K items, Form 4 clusters, news-volume spikes), with watch items "reported, never traded". It is the only visible "opportunities" feed.
2. A: Evidence Card showing components separately, with the Red-Team flag at zero weight. Add dollars-at-stop and bootstrap range (see missing item 2).
3. E: Evidence object (agent default weight 0) plus the A0 to A3 agent ladder, with the golden set and a post-cutoff forward test. Merge with A's extra gate for Claude-derived features.
4. C: Ledger Analyst Q&A (read-only SQLite, SQL shown) as the interactive "JARVIS" the owner remembers.
5. C: sealed holdout, 20-variant cap per hypothesis family, harness logs every run, and the lethal-trifecta rules for the quarantined Reader.
6. D: capital-scaled LLM spend cap `min($15, 2% x capital / 12)`.
7. D: failure-drill gate GF plus the future-poisoning CI test. They make "every decision reconstructable" verifiable.
8. E: honest S-step growth table with outlook labels (reachable / doubtful / never).
9. E: Narrator output schema with `rejections[]`, `questions_for_owner[]`, and the extractor's held-symbol fund-event flags.
10. A: Goal Interpreter returning a config diff explained back, with the planner showing the bootstrap range instead of a return-target field. Reject B/D's deletion of the field.
11. A: TSLA/owner single names on the 20-symbol watchlist for archive and anomaly watch only.
12. D: owner veto without add (as an option), and tightening applied immediately with loosening delayed. Keep as owner-configurable, not forced.
13. B: Strategy 0 as an always-admissible outcome, and a benchmark gate (after-tax CAGR within 1 point and drawdown at most 0.7x). Needs a clearer statement that "within 1 point" means the strategy may trail by up to a point.

## Missing from all five proposals

1. **Compounding rule.** Workflow v3 section 2: "use current realized account equity as the base, but increase deployable capital gradually... Never increase size simply because a daily target was missed." No proposal states how realised gains change deployable capital relative to the G5 steps (25/50/100% of "intended capital"). Needs a stated rule (for example, deployable = min(equity, G5 ceiling) with ratcheted increases).
2. **"Expected range and downside" in every trade explanation.** v2/v3 require it. All five dropped the percentage but none substituted the deterministic version: dollars at risk to the stop, the bootstrap/backtest range for the strategy, and the cost estimate. This gives the owner the explainability without a fake confidence.
3. **Forward shadow outcomes for watch items.** The Claude agents can only earn weight with hundreds of post-cutoff outcomes (briefs 02, 22), and a monthly book gives tens. A cheap fix is to record every watch item and Reader event with a fixed forward-return label across a wider shadow universe (no capital). This builds the sample size the ablation needs inside one model generation, and is the real "learning loop". E calls its agent triggers "doubtful" without proposing this. A's anomaly watch is the seed.
4. **A conversational front end.** v1 was a Gradio chat. Only C offers Q&A, attended and not packaged as an owner-facing chat. Nobody specifies a Streamlit chat on the ledger, a spend-capped batch/answer path, or how it degrades with the LLM off.
5. **A v1 salvage audit.** 00 section 3 notes nobody checked which v1 ingestion code (EDGAR, technicals) is reusable once the key is rotated. Proposals say "rebuild; ideas survive" but only E says "some EDGAR code survive" and none schedules an audit. "Build on current JARVIS" is the owner's explicit instruction, so a short, documented salvage decision is owed.
4b. **A satellite lane for the owner's own ideas** (for example TSLA). All five defer single stocks until about $31,500 (Norgate). None offers a small, labelled, shadow-first discretionary or experimental sleeve with a hard cap, so the owner's own interest has no path other than the weekly lab.
6. **A month-one demo.** With 6-12 months before real money, B, C and D show the owner little before month 3-4. Only A (P1 daily data-health email and archive) and E (P1 market database) give early visible value. A short "shadow JARVIS" email (what it would do today and why) from P1 would protect the owner's engagement, and the disengagement risk named in B risk 3 and C risk 3.
7. **Owner permission model.** v2's three modes (recommend / paper / act inside pre-approved limits) are only partly mapped. A and E have approvals and G-steps, but nobody presents the owner's mode switch as a first-class setting with the audited transition rules.

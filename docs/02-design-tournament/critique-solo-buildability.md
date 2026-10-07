# Critique through one lens: solo-buildability

Critic: solo-buildability. Date 2026-10-01. Question: can one developer with AI coding help build and operate this on a Windows 11 laptop with 8 GB RAM? Briefs 14 and 04 are the main checks; others cited by number.

## 0. Method and assumptions (all effort numbers are ESTIMATES)

- No brief says how many hours a week the owner has. I use "dev-day" = about 6 productive hours with AI coding help. FT = 5 dev-days a week. A part-time owner at about 15 hours a week gets about 2.5 dev-days a week, so calendar time is 2x the FT figure. The proposals all read as full-time schedules.
- AI help shortens writing boilerplate. It does not shorten: broker probes on the paper account, calendar-bound gates, hand-labelling a golden set, verifying DSR/N_eff formulas against the papers (brief 08 says they were recalled, not read), or tuning against real Alpaca behaviour.
- RAM is not the binding constraint for any proposal. The trading job is a run-to-completion Python process (about 0.5 GB), backtests are 6 assets x 20 years of daily bars, and nothing needs Docker (brief 14 F10). The 8 GB limit bites only when several Claude Code sessions (about 1 GiB each, brief 03), Streamlit, a browser and Windows run at once. Only C plans a workload where this matters.
- All five proposals follow brief 14 on the stack (SQLite WAL, Parquet, DuckDB, Streamlit, no Docker, no bus). All five deviate from brief 14's "one long-running asyncio process" by using run-to-completion jobs (brief 23). This is a simplification: it removes websocket gap handling, heartbeat rows and in-process queues.
- All five resolve brief 04's build-versus-adopt question as "thin custom executor on daily bars over Alpaca". That matches the gap analysis (item 5). Brief 04 calls a custom event-driven backtester plus order state machine plus reconciliation "a multi-month project". The proposals avoid the backtester half by looping a pure `as_of_snapshot -> target weights` function over month-ends, which is small. They do not avoid the order-state-machine and reconciliation half, which I put at 20-30 dev-days. None runs brief 04's one-to-two-week spike; with a daily-bar executor it is no longer needed, but no proposal records that decision.

## 1. Effort per phase (proposal claim versus my estimate)

Total through "paper-ready" (G3 can start). FT weeks = dev-days / 5.

| Proposal | Claimed schedule to paper-ready | My dev-days | My FT weeks | At about 15 h/wk |
|---|---|---|---|---|
| A | P0-P4 about 17 wks | 125-175 | 25-35 | 12-16 months |
| B | P0-P2 8 wks (P3 months 3-6 is mostly calendar) | 72-105 | 15-21 | 7-10 months |
| C | P0-P2 about 10 wks, P3 "6+ months" | 115-165 | 23-33 | 11-16 months |
| D | P0-P3 12 wks, P4 months 3-9 | 105-160 | 21-32 | 10-15 months |
| E | P0-P4 14 wks | 90-140 | 18-28 | 9-13 months |

Per-phase detail (dev-days; claim in brackets):

- **A.** P0 8-12 [10]. P1 22-32 [15-20]. P2 22-32 [15-20]. P3 40-55 [20]. P4 30-45 [15, "3 wks overlapping P3"]. The P4 claim is the weakest: four agents, a ~300-item golden set, record-and-replay, a spend cap and a Lab routine in 3 weeks.
- **B.** P0 5-8 [5]. P1 25-35 [15]: ingest, bitemporal store, backtester, registry, G0/G1. P2 30-42 [20]: runner, reconciliation, gate, order service, ledger, kill switch, dead-man switch, email. P3 12-20 of work inside months 3-6.
- **C.** P0 8-12 [10]. P1 22-32 [15-20]. P2 35-50 [20]: harness, cost model, registry, holdout sealing, three agents and the permission hooks. P3 build 45-65 plus agents 4, 7, 9. P4 3-5.
- **D.** P0 5-8 [5]. P1 28-40 [20]. P2 40-60 [25]: order service, gate, reconciliation, kill switch, constraints adapter and 13 failure drills. P3 15-25 [overlapped]. P4 18-28.
- **E.** P0 8-12 [10]. P1 22-32 [15]. P2 18-28 [15]. P3 30-45 [20]. P4 14-22 [10].

Shared components (ESTIMATE, dev-days): bitemporal store and Alpaca/Tiingo ingest with as-of corporate actions 10-14; EDGAR/ALFRED/news archive 6-9; data trust gate 3-4; as-of backtest loop, benchmark and after-tax calc 8-12; registry plus DSR/N_eff/plateau/holdout/bootstrap bands 8-12; order service, intents, reconciliation, gate, kill, dead-man 20-30; ledger, tax lots, wash-sale flag, email 8-12; Streamlit 3-5; mock broker plus 3 drills 5-8 (13 drills 12-18); Narrator with number validator and record/replay 5-8; Extractor with sanitiser, golden set and injection set 12-20.

## 2. Is the first usable milestone close?

Three milestones, because "usable" differs:

- **M1: scheduled code emails the owner the benchmark and the month-end signal.** Shared minimal path is about 25-35 dev-days (about 5-7 FT weeks, month 3 at 15 h/wk).
  - D claims it at week 5 (P1, with S0 shadow). Realistic: weeks 7-9 FT.
  - A and C claim week 5-6. Realistic: weeks 8-10 FT.
  - E claims a database at week 5 and automated shadow at week 12. Realistic: weeks 16-22 FT.
  - B puts shadow only after the whole executor exists (P2, week 8). Realistic: weeks 12-18 FT.
- **M2: automated paper orders.** Realistic month 4-6 FT-equivalent for B and E, later for A, C and D.
- **M3: real money.** The gates, not the code, set this. G2 needs at least 6 monthly rebalances. G4 needs at least 6 months and at least 20 fills. G5 needs at least 18 more months (brief 20).
  - If shadow starts at month 3, G2 ends about month 9 and micro-live starts about month 9-10.
  - Brief 18's own cost arithmetic is 3.5 round trips a year at 1/5 NAV each way, so about 7 fills a year, or about 14 if the T-bill ETF swap is counted. Entry adds about 5. So "at least 20 fills" is about 12-30 months, not 6. Every proposal copies the 6-month figure.
  - Realistic first full-size capital is about month 40-55, not the 18-30 months in the proposals.

Verdict: M1 is close for D, A and C only if the owner works near full time. For a part-time owner it is month 3-4 at best. M3 is not close in any proposal.

## 3. What will be abandoned half-built

- **A:** the anomaly watch (watch items that "are reported, never traded", no consumer, nothing to validate), the Evidence Card (Model component hidden below about 100 outcomes, Thesis at zero weight, so two of five panels are empty for years: brief 10), the Integrity filter, the 20-symbol watchlist, the red-team shadow ablation, Filing Reader, and crypto sleeve B (a $50-$200 position at a 10-20% cap on a $500-$1,000 start, with a 24/7 schedule, a VM move and stop-limit handling).
- **B:** least at risk. Likely stalls: the Streamlit page, E1 (deferred anyway), and R2 because its yield is near zero (brief 08).
- **C:** most at risk. Lab Lead, Backtest Engineer and Red-Team need a harness, sealed holdouts and Claude Code hooks, all built before any trading code. Data-Quality Triage fires only on quarantined rows of a handful of ETF series. Incident Diagnostician and Post-Trade Reviewer cannot be tested until failures or about 20 fills exist. If A fails G1 (likely, section 4), the Lab was built for nothing.
- **D:** the 13-drill GF suite is likely to be cut to the cheap ones; Change Reviewer on every deploy, the "silence test", the override-counterfactual counter and the "first run after deploy is half size" rule (undefined for a monthly book) will decay.
- **E:** the five frozen contracts. The agent slot, the evidence object with `producer{kind...}` and S5-S10 hooks serve capabilities E itself rates "doubtful" or "never". E's own risk 1 says Strategy A "could run from a spreadsheet".

## 4. Cross-cutting problems found (apply to several or all proposals)

1. **G1 will probably fail, which makes the executor and S0 the real product.** Brief 20 plans Sharpe 0.3-0.5 and its own hand check needs about 0.65 at 20 years for DSR 0.96 at N_eff=10, failing at N_eff=20. All five say "hold S0 is a valid outcome". But A, C and E order the build G1-first and execution later. B and D alone say S0 needs only plumbing gates.
2. **S0 gate arithmetic.** B rebalances S0 quarterly but gates on at least 6 rebalances (G2), which is 18 months. Decision points should be monthly with a no-trade band so shadow counts.
3. **Shadow is gated behind the order service** (B P2, E P3, C P3). The 6-month calendar is the critical path, so the pure-function signal job should shadow immediately after the data spine (brief 14: same code path for backtest and live). D does this for S0 only.
4. **Whole-share rule at $1,000 (B, D).** B: 30% cap, $350 order cap, rounding under 10% of target. D: each ETF at most 30%. A slot of $200-300 with a 10% error limit needs an ETF share price of roughly $20-30; no brief shows ETFs meeting this across asset classes. Brief 21 says fractional orders are DAY-only. A, C and E accept unprotected fractional lots, which is far less code (no GTC re-arm state machine at launch).
5. **IEX-only quotes versus the price collar (all five).** The collar demands a quote at most 60 s old (0.5-1.5% bands) on a free feed that is about 2.5% of volume (brief 06). Thin ETFs may have no fresh IEX quote, so the gate may block orders on ordinary days. No proposal names a fallback reference price. This is a recurring tuning chore.
6. **Windows host (briefs 14, 23).** All rely on Task Scheduler with WakeToRun and StartWhenAvailable. Brief 23: Modern Standby limits wake behaviour, and DPAPI under "run whether logged on or not" is untested. For a monthly book a missed day is tolerable; for crypto it is not. D alone sequences crypto after a host move and G4.
7. **The AI coding agent runs as the owner's Windows user.** A DPAPI user-scope key (A, B, D, E) is readable by any Claude Code session as that user, and B's Builder rule "Seeing live keys" is unenforced. C's separate `jarvis-trader` user is the one real fix, but it adds a Task Scheduler stored-password setup that brief 23 lists as UNVERIFIED. A cheaper option: put the live key only on the VPS from G4.
8. **Maintenance load multiplies with each LLM component.** Every model change restarts the forward clock, needs old/new shadow and a golden-set rerun (brief 22). Haiku 4.5 has a not-before retirement of 2026-10-15 and no listed successor (brief 22, gap analysis). A has three production LLM jobs, C four, D two (Reader, Narrator), E two, B none at launch.
9. **Brief 04 spike.** None budgets it or records "skipped because daily-bar thin executor". Low cost to fix.
10. **Mock broker.** Brief 21 says duplicate-ID and replace-race behaviour needs tests, and some cases (broker 5xx, replace race, partial fill) cannot be forced on Alpaca paper. A fake Alpaca is a hidden 5-10 dev-day item in every plan; D's 13 drills make it mandatory.

## 5. Per-proposal attack

### A-vision-faithful (score 5)
- Serious: "(b) An anomaly watch ... produces watch items that are reported, never traded" (section 2, step 5) plus the five-component Evidence Card (step 8) are built features with no consumer; brief 10 says calibration needs a few hundred outcomes, which a monthly book never reaches.
- Serious: section 11 P4 "(3 wks, overlapping P3)" holds Narrator, News Analyst, Red-Team, Lab routine, "golden set; record/replay; $15 cap". A ~300-item golden set with deterministic answers dated after the cutoff (section 7) cannot be hand-built in 3 weeks (brief 22: 30-45 dev-days is my estimate).
- Serious: P2 "Register A and B" and the launch run schedule include a 00:05 UTC crypto run on a laptop that briefs 14 and 23 say should not host unattended crypto; sleeve B is 10% of equity at launch.
- Serious: 16-step flow with six Claude agents and thirteen code roles; the "roster keeps its names on the dashboard" is naming overhead.
- Strength: P0 lists concrete spikes (duplicate `client_order_id`, replay) and rotating the leaked key; explicit growth triggers; LLM off by default.
- Fatal flaws: none.

### B-evidence-minimal (score 8)
- Serious: P1 "weeks 2-4" cannot hold ingest, store, backtester, registry and G0/G1 (my estimate 25-35 dev-days versus 15).
- Serious: shadow starts only after P2 contains the full executor; shadow could start at the end of P1.
- Serious: "Positions are whole shares only" with a $350 order cap at $1,000 (section 6): feasible only with cheap ETFs no brief verifies; no stated fallback to fractional.
- Serious: S0 is rebalanced quarterly but "at least 6 rebalances" (G2) means 18 months.
- Moderate: R1 reads the ledger from a Claude Code session running as the owner; the "no key in any Claude context" rule is not enforced (DPAPI user scope).
- Strength: the smallest total build (72-105 dev-days). No production LLM at launch. One 13-step job. Approvals as expiring rows. Handles the daily job in two schedules. Every deferred item has a trigger. Only proposal where the order of work matches "S0 is the likely product".
- Fatal flaws: none.

### C-agents-as-quant-team (score 3.5)
- Serious: P2 "(4 weeks) Harness, cost model, registry, holdout sealing, agents 1, 3 and 5, and the permission hooks" — I estimate 35-50 dev-days. It is built before the execution core, so shadow starts last.
- Serious: nine agents. Weekly "60-90 minutes" Research Lab for the owner (section 9), plus review of red-team reports. The lab's expected yield is near zero (brief 02, Gençay), and brief 20 says B "can never pass a standalone 20-year gate".
- Serious: `jarvis-trader` separate Windows user with DPAPI and Task Scheduler: brief 23 lists "run whether user is logged on or not" as UNVERIFIED. This is a good control that is untested on this machine.
- Serious: section 8 plans Claude Code sessions "about 1 GB or more" next to Streamlit and a daily job on 8 GB; mitigated only by a "one session plus one subagent" rule.
- Moderate: Triage, Incident Diagnostician and Post-Trade Reviewer have nothing to run on until failures or fills exist, so they ship untested.
- Strength: harness-only backtests and logging every run to the registry (small and valuable); read-only Ledger Analyst Q&A; quarantined Reader design.
- Fatal flaws: none, but it is the least buildable.

### D-failure-first (score 6.5)
- Serious: P2 "(weeks 6-10)" must deliver order service, risk gate, reconciliation, kill switch, constraints adapter and "GF drills all pass" (13 drills). With a mock broker that is 40-60 dev-days versus 25. D's own risk 2 names this.
- Serious: whole shares only (section 6, "whole shares for overnight holdings") with ETFs ≤30% of the book at $1,000; see section 4 point 4.
- Serious: price collar ±1.5% against a quote ≤60 s old on IEX-only data (F1, F3); false skips are likely, and "any failure skips the run" means a missed rebalance.
- Moderate: the hash-chained ledger, "Change Reviewer on every deploy", 72-hour loosening, the "first run after a deploy at half size" rule (undefined for a monthly book), weekly silence test. Each is cheap; together they are ongoing owner chores.
- Strength: S0 shadow from P1; future-poisoning CI test (brief 14 section 2.5 recommends it); crypto deferred until the host moves and S-A passes G4; capital-scaled LLM cap min($15, 2% x capital/12); failure catalogue maps controls to failures; only two production LLM roles at launch.
- Fatal flaws: none.

### E-staged-platform (score 7)
- Serious: P0 freezes "five frozen contracts as Pydantic models with tests" before any code has used them (section 11); E's risk 1 admits contract churn. Of the five, only the bitemporal record and the strategy contract are needed at launch; the evidence object and agent slot serve S5-S10, rated "doubtful" or "never".
- Serious: P3 "(4 wks)" holds gate, order service, reconciliation, kill switch, dead-man switch, Task Scheduler jobs and template reports: 30-45 dev-days.
- Moderate: shadow is "started" only at P3 end (about week 12 claimed, about week 16-22 FT realistic).
- Strength: the leanest launch execution: Strategy A has no intra-month stop and fractional lots are accepted, so no GTC re-arm logic is needed at launch (this reduces build, though its money consequences belong to another lens); explicit S1-S10 triggers with honest "likely never" labels; Narrator with a templated fallback when the LLM is off; the `Strategy` pure-function protocol.
- Fatal flaws: none.

## 6. Ideas worth grafting

- B: smallest agent footprint (no production LLM at launch; R1/R2 as attended Claude Code sessions, not services). B's build order (S0 first, A earns its place).
- D: S0 shadow from P1; future-poisoning test; crypto after host move and G4; capital-scaled LLM cap formula; failure catalogue as a checklist, with the drill list cut to about 6 that a mock broker covers.
- E: only two frozen interfaces (bitemporal record, `Strategy -> TargetBook`); no intra-month stop at launch with fractional lots; templated report when LLM is off.
- C: the harness as the only way to run a backtest and write the registry (a function, not Claude Code hooks); Ledger Analyst as a read-only Claude Code command; separate Windows user for the live key only at G4 if the VPS is not used.
- A: the P0 spike list and the growth-trigger table; narrator-first ordering of agents.

## 7. Missing from all proposals

1. The owner's weekly hours and a project-level kill criterion (for example: if M2 is not reached by month 6, fall back to a script that emails the rebalance list and the owner places trades by hand).
2. A manual-execution bridge: emailing the signal at month 3 lets the owner trade by hand at micro size and collect real fills early, instead of waiting for the executor.
3. A mock Alpaca for failure drills and CI.
4. G4's "at least 20 fills" versus roughly 7-14 fills a year for a monthly ETF book (brief 18 cost arithmetic).
5. A reference-price fallback for the collar when IEX quotes are stale.
6. Recurring maintenance hours: Python lockfile and Windows Update, Alpaca API changes, and re-validating each LLM component on each model change (Haiku 4.5 retirement floor 2026-10-15).
7. Decoupling shadow from execution to start the 6-month calendar earlier.
8. Fixing S0's decision frequency so G2 counts are reachable.
9. Recording the decision not to run brief 04's spike.

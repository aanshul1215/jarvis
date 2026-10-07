# Panel position: solo-builder-pragmatist

Date 2026-10-02. Stance: I am the one building and running JARVIS alone, with AI coding help, on an 8 GB Windows laptop. I judge each change by build effort, 2 a.m. failure modes, and whether it gets a useful milestone inside about two months. All effort numbers are ESTIMATES (my judgement), not data.

## Verdict on the reviewer's concern

The concern holds. FINAL-design costs 134-182 dev-days to reach first live dollars at month 12-15 for a book whose live satellite is expected to lose $14-18 a year. The core S0 can be bought by hand in ten minutes a month. Most of the control surface (three Windows accounts, ACL matrix, emailed hashes, SAFE/risk-reducing class, mutation gate, XFER netting, G4/G5 ladders, API workspaces with a cap formula, sealed holdout) exists to protect an unattended executor that is not yet needed. The right shape for a solo builder is: attended first, unattended never until earned.

The single structural idea I back above all others: **no unattended order placement until adherence data says it is worth building.** At 2 a.m. nothing can lose money, because nothing trades unattended. Every failure then degrades to "email says what happened; next window retries".

## Proposed milestone ladder (my plan, ESTIMATE)

| Milestone | Content | Dev-days | Calendar at 2.5 d/wk |
|---|---|---|---|
| M0 | Revoke v1 key; Alpaca account and paper keys; 6 probes only: paper order round trip, fractional, activities endpoint or position-diff fallback, lot method, IBIT tradable, Alpaca IRA email sent; one scheduled-task wake test | 3-4 | wk 1-2 |
| M1 | One Python package, JSONL ledger, S0/S-A/S0-RM shadow targets, code-written monthly email | 8-10 | wk 3-5 |
| M2 | Scheduled Analyst memo (Desktop task) with code validator and template fallback; exception-only daily mail; two Healthchecks checks | 6-8 | wk 6-8 |
| M3 | RECOMMEND-live S0 with real money: orders emailed, owner places them, `jarvis adopt` imports fills; Behaviour Ledger v0; crisis letter | 5-7 | month 2-3 |
| M4 | P2-lite: Faber replication on ETF proxies, 21 offset dates, FIFO tax sim, decision memo for S-A; Mission Plan dial b | 12-16 | month 3-5 |
| M5 (optional) | Attended executor MVP (owner types key, runs one command), built only if adherence under 95% or owner wants it | 20-28 | month 5-8 |

Total to M3: about 22-29 dev-days, which fits the two-month goal. Total through M4: about 34-45. Compare 61-82 for the old design to the P2 verdict, with no live dollars.

Stop rules: if M3 is not done by month 3.5, the project stays an emailed shadow plan and the owner trades by hand. The old month-15 kill criterion is replaced by a month-4 checkpoint.

## Votes (abbreviated; full reasons in the structured output)

Accept: S01-P1, P2, P3, P4, P5, P8; S02-P1, P5, P6; S03-P1 (modified), P3, P4, P6; S04-P1 (mod), P2, P4, P5 (mod), P6, P7; S05-P1, P2, P4, P5; S06-P1, P2, P3, P4, P5, P7, P9, P11; S07-P1, P2, P3, P5; S08-P1, P4, P5; S09-P4, P5, P6, P8; S10-P1 (mod), P2 (mod), P5, P6, P7.

Modify: S01-P6, S01-P7, S02-P2, S02-P3, S02-P4, S03-P2, S03-P5, S03-P7, S03-P8, S04-P3, S05-P3, S05-P6, S05-P7, S05-P8, S06-P6, S06-P8, S06-P10, S07-P4, S08-P2, S08-P3, S09-P1, S09-P2, S09-P3, S09-P7, S09-P9, S10-P3, S10-P8.

Reject: S07-P6 (placebo null at launch), S10-P4 (ML proxy panel, moot while the ML lane is deferred).

## Conflicts and which proposal wins

1. S09-P9 (build executor right after P1a) vs S04-P6 (RECOMMEND-live first, gate executor on adherence). S04-P6 wins on ordering. S09-P9 supplies the executor spec when it is built (attended, key typed, minimum control set).
2. S09-P3 (git commits and typed dispatch as approvals) vs S04-P3 (emailed hash plus 24 h delay on vetoes). Mechanism: S09-P3 wins, but host-neutral (owner commit to prod config with an `effective_after` date). From S04-P3 keep the templated reason, counterfactual log and 24 h delay as a date check.
3. S09-P1 (GitHub Actions host) vs S06-P2 (Desktop scheduled tasks). The Analyst needs the laptop awake and the app open anyway, so a second host adds a second failure surface. Laptop Task Scheduler wins for v1; the entrypoint stays host-agnostic so a move costs about a day. Actions' hosted-runner clause (activity unrelated to the repo's software) is a further reason not to depend on it.
4. S02-P2 and S10-P3 (pre-register proxies so the 20-year gate applies; 1973 proxy ladder) vs S07-P1 and S01-P3 (G1a no longer gates). The gating rationale disappears, so keep only a small proxy table (GLD, EFA, FRED TB3MS with discount-basis fix) for the 2004+ replication; defer the 1973 ladder and its unread licences.
5. S06-P1 (delete eval workspace) vs S04-P5 (advice-leak set in the eval workspace at about $0.31). S06-P1 wins; run the advice-leak set as an attended plan session on any prompt or model change.
6. S05-P6 (code-only digest in P1b) vs S04-P7 and S06-P10 (demote the Reader). Digest is built after M3, default off, opt-in; no LLM Reader until the owner opens it in 6 of 8 weeks.
7. S01-P7 (defer ML lane) vs S10-P7 (time-box 5 days): both hold; deferred first, then time-boxed, using S10-P5's protocol (logistic first, expanding walk-forward).
8. S09-P2 (separate prod repo, passphrase SSH) vs attended execution: with the live key typed at run time and no stored live secret, the second repo is unneeded until unattended execution exists.
9. S08-P2 (crypto shadow with registered Donchian family) vs S01-P7, S05-P7 (fewer trials): take only the BTC 0/2.5/5% variants column, no registered family.

## Keep as is

- No Claude output in any order path; Claude authors, code decides, owner signs.
- S0 as the null and the product if S-A fails; plain untuned Faber; S0-RM as the risk-matched comparison (S0 with T-bill dial).
- A single small default-deny gate with a short list: per-symbol cap, limit-price formula, collar, $20 minimum, rate limit and HALT, broker-side no_shorting and margin 1.
- Deterministic client_order_id plus lookup-before-submit and intent persistence (needed the day an executor exists).
- Bitemporal `available_at` and the AsOfSnapshot idea, implemented minimally.
- Hash-chained append-only ledger, now as JSONL in a private git repo.
- Typed-field Analyst output with code number validation and template fallback.
- Mission Plan with dial b computed from dollar tolerance.
- Honest -$14 to -$18 framing and the "if S-A fails, benchmark is the product" outcome.
- The idea ledger as a document (not a dashboard feature), and the owner-ideas mapping.
- Attended Builder, Strategy Lab, Ledger Analyst; the quarantined Reader design (off by default).
- Kill switch concept: HALT flag file check (5 lines) plus the Alpaca app as last resort.

## Cut or simplify

- Three Windows accounts, ACL matrix, inbox/outbox, all JARVIS-* trader tasks (Kill, Flatten, Approve, CashEvent, Veto, RedTeam, HoldoutEval, Eval, Deploy), manifest hash, DPAPI probes, Modern Standby probes.
- Emailed 6-character hashes and rotating flatten codes.
- SAFE as a rich state, risk-reducing order class, same-run-funded T-bill rule, auto-clear logic and drills: SAFE becomes "no orders, email, exit".
- Mutation-score gate on the gate module: replace with a failure-catalogue test table plus crash drills.
- API workspaces, cap formula, tiers T0-T2, Batch jobs, per-role dollar budgets, nightly Narrator upgrade, eval workspace, Reader submit/collect jobs, golden set, unattended Incident Analyst tool loop.
- Sleeve tags, XFER netting, per-sleeve attribution, G4/G5 ladders, tracking-error band, ONC/Galwey/PBO, null simulation, sealed holdout, trader-side registry via tasks (use a repo file).
- Streamlit dashboard, ntfy, second-inbox hash anchor, Tiingo stored copy and second-vendor gate, 100-name watch universe, integrity flag and watch scan at launch, SHAP and ML-lane forecasts in the memo, 20 seeded Red-Team defects.

## Additions of my own

1. Milestone ladder with one-page definitions of done and stop rules (above). Anything not needed for the next milestone goes to BACKLOG.md.
2. "Attended before unattended" rule: no unattended order placement until M5 and a measured adherence reason; the live key is typed at run time and never stored.
3. A static weekly report page generated by code (markdown or one HTML file) replaces the Streamlit dashboard. No resident server on an 8 GB laptop.
4. Owner-attention budget: at most 15 minutes a week and 30 minutes on the decision day; the exception-only mail enforces it.
5. One Reviewer subagent on every Builder diff touching the gate, config or order path; its output is advisory, tests are the control. This is the most useful always-on Claude agent for a solo developer.
6. Plan-usage ledger: after each scheduled run, code records session usage if available; if the plan limit is hit, scheduled roles skip and templates ship, Builder has priority.
7. Archive v1's leaked TSLA model as a post-mortem in M1 (half a day): it teaches the leak tests and is the heritage item.
8. P0 probes cut to what changes a decision: paper round trip, fractional, activities endpoint, lot method, IBIT tradable, Alpaca IRA reply, one scheduled-task wake test.
9. Email Tiingo and Alpaca in week 1 with the licence and IRA questions; both answers have long latency and block M4 data choices.
10. Mission Plan stress loss uses worst historical peak-to-trough of the proxy series only (no bootstrap) with the 10-point hysteresis and band floor.

# Panel position: budget-and-simplicity-hawk

Date: 2026-10-02. Stance: near-zero metered spend, 8 GB RAM, one part-time developer, shortest path to a working system.
All dev-day figures below are ESTIMATES inherited from the design and the specialist reports; I did no new research.

## Test of the reviewer's concern

The concern holds. The current design spends 130-182 dev-days (section 11) to reach first live dollars at month 12-15, to run a satellite whose own arithmetic (section 1) is -$14 to -$18 a year, plus a $0.70-$2.02 a month LLM plumbing stack whose cap alone is 47-60% of that satellite loss. The main point: the thing that earns the owner money (holding a diversified ETF mix with a T-bill dial, in the right account) can be live by hand in month 1-2. Everything after that is optional and must justify itself against that baseline.

## Principle I applied

1. Live money first, by hand (RECOMMEND), because S0 is the product and the null, and needs no strategy gate.
2. Every build item must be paid for by a measured need (adherence, a real incident, a real loss), not by a hypothetical.
3. Claude agents run on the existing plan, attended or on Anthropic's own scheduler. No metered API, no keys on the Builder's machine.
4. No new paid service, no new account type, no second vendor, no dashboard server.

## Votes (all 76 proposals)

### S01
- S01-P1 ACCEPT. Biggest single cut: removes the satellite's XFER netting, per-sleeve attribution, combined-book wash-sale simulation and G4/G5. Default is S0 plus dial b; S-A in shadow; IRA-only live as option (b).
- S01-P2 ACCEPT. Text only, protects the owner from over-expecting.
- S01-P3 ACCEPT, with the scale fixed by S02-P2 (replication from roughly 2004 on real ETFs plus three proxies, not 1973). The verdict is a memo, not a trigger.
- S01-P4 ACCEPT. Half a day, prevents false sells.
- S01-P5 ACCEPT as a plain loop over the 21 offsets inside the replication. Report only, never a gate; cap at 1 dev-day.
- S01-P6 MODIFY. Keep "do not add Keller/dual momentum at launch" as a Lab backlog note. Drop the 6/9/12 vote shadow variant: it adds a trial and 1-2 days for a result nobody can validate.
- S01-P7 ACCEPT. ML lane deferred until after live S0 and spare plan capacity.
- S01-P8 ACCEPT as one template paragraph in the monthly email, only while S-A runs in shadow. No separate build.

### S02
- S02-P1 ACCEPT. Fix the tickers now; one ticker per slot; tax_character field and collectibles bucket kept minimal.
- S02-P2 MODIFY. Pre-register exactly three proxies (GLD for GLDM, EFA for VEA, FRED TB3MS/DTB3 for SGOV) and nothing else. With G1a report-only (S07-P1) the 20-year gate no longer gates, so this is just a one-line spec for the replication.
- S02-P3 REJECT the S0-2F column (second benchmark, more reporting). Keep only the zero-code wording: S0 is described as the like-for-like null, not as a recommended portfolio.
- S02-P4 MODIFY. Keep b = max(0, 1 - tolerance$ / (DD_stress x capital)), rounded up to 10 points, with the 10-point change rule and the small-account band floor. Use DD_stress = worst historical peak-to-trough of S0 on the proxy history; drop the bootstrap p95 term (no extra machinery).
- S02-P5 ACCEPT. Removes work and a sensitivity study.
- S02-P6 ACCEPT. Config change, zero cost.

### S03
- S03-P1 MODIFY. No TLH executor (agreed). Also no harvest_candidate simulator event and no pre-registered build trigger: value is about $3-10 a year at $5,000. Instead the monthly email shows one line "lots with unrealised loss at least 5% and $50" from a query. Revisit only if capital exceeds $5,000 in a taxable account.
- S03-P2 MODIFY. Accept the account-location priority as the pre-registered rule, but implement it as a static decision table in the Mission Plan document plus a check, not a code allocator. Cap effort at 0.5 day.
- S03-P3 ACCEPT. One config field and one tax-lot rule; reject K-1 funds.
- S03-P4 ACCEPT. FIFO as the only simulator mode; no HIFO or specific-lot branches.
- S03-P5 MODIFY. Replace the cross-account guard with a simple rule: no discretionary loss sale in taxable, ever, unless the owner does it by hand; read one external_trades CSV; same-underlying ETFs treated as identical. No pair-table approval workflow.
- S03-P6 ACCEPT. The contribution waterfall removes most S0 sells, so it simplifies the tax logic.
- S03-P7 ACCEPT. Same logic as S01-P1.
- S03-P8 MODIFY. Produce the question list as a half-page file. The paid consult is optional and only worth it above about $5,000 or before putting S-A in an IRA. Drop the three seeded tax defects (no seeded-defect bar, see S06-P9).

### S04
- S04-P1 MODIFY. Build only: plan-shadow NAV minus actual NAV, monthly adherence and override counts, money-weighted minus time-weighted return. Skip the 12-24 month baseline import and the per-cause attribution until there is data worth attributing. About 1 dev-day, not 2-3.
- S04-P2 ACCEPT. A quieter inbox is cheaper to build and to live with.
- S04-P3 MODIFY. Friction on vetoing an exit via a typed reason string and an effective_after 24-hour check (the same cheap mechanism as the cool-off), not the emailed-hash machinery that S09-P3 deletes.
- S04-P4 MODIFY. Crisis letter only (template, owner-written, returned by a loss-band check). Drop the pre-mortem at each G5 step since G5 is gone.
- S04-P5 MODIFY. Adopt the forbidden-behaviour list as prompt text plus schema/validator checks. Run the 30-prompt advice-leak set in an attended session on a model change at $0 plan usage, since the eval workspace is deleted (S06-P1). Cap at 1 dev-day.
- S04-P6 ACCEPT, with highest priority. RECOMMEND-live S0 from month 2-3; build an executor only if adherence over 6 months is below 95% or the owner wants it.
- S04-P7 ACCEPT the demotion. The owner Idea Journal is a "could": defer until the owner asks for it.

### S05
- S05-P1 MODIFY. Build the single-entry trial logger and use the raw count when the first Lab spec exists, not before. It is a 20-line wrapper; do not pre-build it.
- S05-P2 ACCEPT. Half-day CI test, built with the scaled-down harness.
- S05-P3 MODIFY. The one-way funnel is a prompt/skill template and a spec file hashed in git, not a trader-side registry. Keep negative results in the same file.
- S05-P4 ACCEPT. Zero effort.
- S05-P5 MODIFY. Accept the replication analyst task (plain Faber, planted random spec must fail, oracle must be blocked) as the first Lab job. Do not create a Spec Clerk step; it is a paragraph in the Lab template.
- S05-P6 MODIFY. Do not ship even the code-only digest at launch: no order consumer, and the archive plus scan is a large part of P1b. Defer the whole Reader and digest until the owner asks.
- S05-P7 ACCEPT. Lab capped at 4 sessions a year, maintenance mode if nothing clears.
- S05-P8 ACCEPT. Reviewer is an attended read-only subagent; no API Red-Team.

### S06
- S06-P1 ACCEPT. The strongest budget move: metered API spend goes to $0, and the cap/tier/batch/eval machinery is deleted.
- S06-P2 ACCEPT. Surfaces assigned: attended for Builder, Reviewer, Lab, Ledger and Incident; at most one Desktop scheduled task a week for the Analyst memo.
- S06-P3 ACCEPT. Incident Triage becomes attended with a code-built incident bundle.
- S06-P4 MODIFY. Go to five active roles (Builder, Reviewer, Strategy Lab, Analyst, Incident Triage). Reader stays defined but dormant.
- S06-P5 ACCEPT. Mechanical number check with at most 2 repair passes; template fallback.
- S06-P6 ACCEPT as one reusable permission recipe, tested once with Run now.
- S06-P7 ACCEPT. Plan-usage governance matters because the owner has already hit a limit; Builder has priority.
- S06-P8 REJECT for launch. Per-role memory files need a validator-failure log that does not exist yet; add after month 3 if failures repeat.
- S06-P9 MODIFY. Do not build a seeded-defect bar at all (not even 8). The Reviewer is advisory; track real catches in the weekly counters.
- S06-P10 ACCEPT. Declare A1 unreachable and drop the 300-item golden set (moot while the Reader is dormant).
- S06-P11 ACCEPT (must). Quarter-day cost, prevents a terms problem.

### S07
- S07-P1 ACCEPT. One gating test; G1a becomes a report.
- S07-P2 MODIFY. Gate only on criterion (ii), but with S-A in shadow this is a pre-registered decision memo, not a gate engine. State "retire S-A" as the modal verdict.
- S07-P3 ACCEPT. No ONC/Galwey/PBO at launch. Revisit White's Reality Check at the first family above 6 variants.
- S07-P4 MODIFY. Applies only if S-A goes live (IRA mode b). In that case, accept 3 decisions plus 20 fills and delete the G5 evidence ladder; satellite_max = 25%. Otherwise moot.
- S07-P5 MODIFY. Two tranches only if an executor exists. In RECOMMEND mode the owner's deposit schedule is the ladder.
- S07-P6 REJECT for now. A 1,000-placebo null simulation is for a decision rule that no longer gates anything. Build it with the first tuned Lab spec.

### S08
- S08-P1 ACCEPT. Delete the dead crypto branch and stop-lifecycle paragraph.
- S08-P2 MODIFY. No Coinbase ingest, no Donchian family. At most one static "S0 plus 5% BTC ETF" shadow column from Alpaca bars if IBIT is tradable (about 0.5 day, forward-only). Else defer.
- S08-P3 ACCEPT as a config row (permission default none) with no launch build. Implement only if the owner asks.
- S08-P4 MODIFY. One probe (GET asset for IBIT) in P0 and one question in the existing Alpaca email. No wash-sale mapping for BTC ETFs until they are held.
- S08-P5 ACCEPT. Zero work; no managed futures.

### S09
- S09-P1 MODIFY. Accept GitHub Actions in a private repo for work that needs no live key: monthly shadow run, weekly reconcile of paper, the emailed memo. Reject Actions as a host for live execution (see conflicts). Keep the laptop as dev box. Use the Actions run log for scheduled_for vs started_at; drop the 8-10-run probe to a quick 3-run check unless the owner wants the Actions-hosted path to become live.
- S09-P2 ACCEPT (must). Delete three Windows accounts, ACL matrix, inbox/outbox, Deploy task, manifest hash. Replace with: no live key on the Builder's machine; owner reads the diff and pushes.
- S09-P3 ACCEPT. Approvals become commits or typed inputs plus an effective_after date check.
- S09-P4 ACCEPT. SAFE collapses into "no orders, fail ping, next run re-reconciles"; HALT only for kill switch, lifetime stop (if a satellite is live) and rate breach.
- S09-P5 ACCEPT. Failure-catalogue tests and property tests; non-gating mutmut optional.
- S09-P6 ACCEPT. One heartbeat check is enough at launch; a second ("decision recorded by day 8") is fine and free.
- S09-P7 ACCEPT. Git as the ledger; I would also drop the custom prev-hash chain and rely on git history plus Alpaca confirmations (own addition).
- S09-P8 ACCEPT. Same as S06-P1/P3.
- S09-P9 MODIFY. Right shape (attended MVP, key typed at run time), wrong timing. It follows S04-P6: executor only if 6 months of RECOMMEND data justify it.

### S10
- S10-P1 MODIFY. Remove Tiingo from the daily pipeline entirely. If the one-time replication needs pre-2016 ETF data, use Tiingo only transiently (derived results stored, raw data not) or a source with permissive terms; keep a one-table docs/data_licences.md (0.25 day). Do not pay for Power ($360 a year).
- S10-P2 ACCEPT (must). The daily gate is Alpaca SIP vs Alpaca IEX close plus the 30% move and corporate-actions check; a missing bar means no risk-increasing order.
- S10-P3 MODIFY. Keep the real-ETF window and the three proxies from S02-P2. Reject the 1973 proxy ladder (Ken French, MSCI, Nareit, World Bank gold): about 3 dev-days, licences unread, and nothing gates on it. Later Lab task if the owner is curious.
- S10-P4 REJECT as a separate change. Only relevant when the ML lane exists; fold one sentence into the deferred spec.
- S10-P5 MODIFY. Accept the baselines and logistic-first protocol as text inside the deferred ML spec. No build now.
- S10-P6 ACCEPT. One honest paragraph; saves machinery.
- S10-P7 ACCEPT. 5-day time-box after live S0 and a spare plan budget; archive the leaked TSLA model as a post-mortem.
- S10-P8 MODIFY. One line in the deferred ML spec; no standalone work.

## KEEP as is

- No Claude output decides an order; Claude authors, code decides, owner signs.
- S0 as the null and the product; T-bill dial b from the owner's loss tolerance; plain Faber as the shadow satellite.
- Month-end signal, first-trading-day fill, marketable limit orders, no market orders, 25% per-symbol cap, collar, $20 minimum, 2% buffer.
- Broker-constraints adapter (no_shorting, margin multiplier) and deterministic client_order_id with lookup before submit, if an executor is built.
- Reconcile against the broker and the rule that an unexplained break blocks risk-increasing orders.
- No ETF stops, no LangGraph, no Docker, no Redis/Postgres, SQLite or flat files.
- Typed-field Narrator with a mechanical number check and a template fallback.
- Incident bundle idea (code builds evidence; cause_enum runbook step).
- First action: revoke the exposed OpenAI key; gitleaks pre-commit; legal perimeter (own money only).
- Honest labelling (DC/ESTIMATE/UNVERIFIED), the sunset rule, and the idea ledger as history, not a maintained build artifact.
- GF crash drills for the executor, scoped to the failure catalogue.

## CUT or simplify

- Three Windows accounts, ACL matrix, inbox/outbox, owner-startable trader tasks, JARVIS-Deploy, manifest hash, DPAPI probes.
- Emailed approval hashes and rotating flatten codes (replaced by git commits and typed inputs).
- Prepaid API workspaces, monthly cap formula, tiers T0-T2, batch jobs, eval workspace, per-role dollar budgets.
- Live S-A satellite, XFER netting, sleeve attribution, combined-book wash-sale simulation, G4/G5 ladders, tracking-error band.
- G1a gating, 20-year rule, 25% cap logic, ONC, Galwey, PBO, N_eff, 1,000-placebo null (until a tuned spec exists).
- Gating mutation score, 20 seeded defects, Red-Team API job and its catch-rate bar.
- Reader, Watchlist Digest, evening archive of EDGAR/Form 4/news, watch scan, integrity flag, regime label (no consumer), 300-item golden set.
- Tiingo in the daily gate; stored research copy.
- Shadow ML lane (until after live S0), SHAP stability rule.
- Streamlit dashboard; weekly "agent report card" reduced to a few counters in the memo.
- SAFE auto-clear, risk-reducing order class, same-run-funded T-bill rule.
- Mission Plan "probability of reaching the goal" bootstrap; nightly Narrator upgrade.
- Crypto stop lifecycle, Coinbase ingest, Donchian family.

## Conflicts between proposals, and who wins

1. Executor timing: S04-P6 (RECOMMEND first, executor gated on adherence) versus S09-P9 (build attended executor MVP right after P1a). S04-P6 wins on order. If the executor is built, use S09-P9's attended MVP shape (about 20-28 dev-days), not the 43-53 day P3.
2. Satellite funding: S01-P1/S03-P7 (S-A shadow unless an IRA) versus S07-P4 (shorten G4/G5). S01-P1 wins. S07-P4 applies only in IRA mode (b).
3. Digest: S05-P6 (code-only digest in P1b) versus S04-P7 (not default) and S06-P10. S04-P7 wins; no digest at launch.
4. History: S01-P3 (1973 replication) and S10-P3 (proxy ladder) versus S02-P2 (three proxies). S02-P2 wins.
5. Hosting: S09-P1 (Actions) versus S09-P2/S09-P9 and S06-P2 (Desktop tasks on laptop). Actions hosts only key-free work (shadow, memo); any live key stays off GitHub and off the Builder's machine, typed at an attended run. Desktop scheduled task is limited to the weekly Analyst memo.
6. Eval budget: S04-P5 (eval prompts cost $0.31 a run) versus S06-P1 (eval workspace deleted). S06-P1 wins; run the set in an attended session.
7. Veto/approval friction: S04-P3 (emailed hash) versus S09-P3 (no hashes). S09-P3 wins; use effective_after.
8. Red-Team: S05-P8 / S06-P4 (Reviewer) versus S06-P9 (8 seeded defects). Reviewer stays advisory; no seeded bar.
9. Tax: S03-P1 (harvest_candidate event) versus S01-P1 effort cuts. Drop the event; email line only.
10. Roster size: S06-P4 says six; I say five active plus a dormant Reader.

## Own additions the specialists missed

1. A scope lock with a clock. Target a complete v1 (RECOMMEND-live S0, monthly shadow memo, replication verdict, attended incident and ledger roles) in about 45-60 dev-days (ESTIMATE, my judgement from removing roughly 70-120 days of the design's 130-182), with S0 live by hand in month 1-2. Kill criterion: if live S0 by hand is not running at month 3, stop adding features.
2. Use GitHub Issues as the notification channel from Actions. The owner gets email and phone push from the GitHub app with no SMTP secret, no ntfy topic and no email account to wire; Healthchecks stays as the single dead-man check.
3. Drop the Streamlit dashboard (RAM and build). The weekly memo and one monthly static report are the dashboard.
4. Define agents as `.claude/agents/*.md` and skills files with a typed JSON output contract and a validator script. That is the whole "agent infrastructure"; no framework.
5. Keep the P0 probe list to five items that can actually kill the plan: Alpaca account type and fractional support for the six ETFs, activities/reconcile read, IBIT tradable, Actions schedule behaviour, plan-usage per scheduled run. Delete the other probes (DPAPI, Modern Standby, task ACLs, lot method beyond a note).
6. Plan-usage meter: record /usage after each scheduled run for the first four weeks; if the Analyst weekly run costs more than a small share of the weekly limit, shrink its inputs before adding any role.
7. Drop the custom hash chain; git history plus the broker's own confirmations are the audit trail.
8. Meaningfulness test for agents, so the system is not hollow: each retained agent must have (a) a typed output, (b) a mechanical verifier, (c) a visible weekly artifact. Analyst: the memo; Incident Triage: the incident file; Ledger Analyst: answers with SQL shown; Reviewer: a pre-mortem on each spec or gate diff; Strategy Lab: the replication report and trial file; Builder: the code. Five roles that each ship something visible beat eight roles that include theatre.

# S09 - Operations, security and hosting: is the design proportionate?

Reviewer: S09. Date: 2026-10-02. Constraints honoured: US/Texas, $1,000-$10,000 own money, near-zero metered spend, Windows 11 / 8 GB laptop, solo developer, Claude agents. Every proposal below costs $0 unless stated.

## Bottom line

The control *list* is right; the *machinery* is too heavy for a bot placing a handful of ETF orders a month. The satellite is expected to lose about $14-18 a year (FINAL-design section 1), so operations must be justified by loss prevention. The losses that matter are duplicate or oversized orders, an unnoticed outage and a leaked key. Three Windows accounts, emailed hashes, a 95% mutation gate and a three-state machine address them indirectly, at an estimated 13-24 dev-days (ESTIMATE, my judgement). A free GitHub Actions runner is a viable host, with caveats below.

## What the design gets right

1. **Default-deny, hard-reject gate in code the owner controls, with no overridable warnings (section 6).** The SEC's Knight order and press release list missing order-comparison checks, missing financial-risk safeguards, weak deployment procedure and no incident guidance as the gaps behind more than 4 million orders, 397 million shares and a loss above $460 million in about 45 minutes (SEC 2013-222, FETCHED). FINRA 15-09 asks for controls on anyone's ability to override (FETCHED via brief 12; page re-opened for kill switch, change management, testing, reconciliation).
2. **Reconcile-on-start and lookup-before-submit idempotency (section 2 steps 3, 4, 11).** FINRA 15-09 names reconciliation as the way to spot unintended results (FETCHED). Alpaca's order reference says `client_order_id` is at most 128 characters and is silent on duplicate behaviour (FETCHED), so a lookup, not the broker's rejection, must be the control, exactly as the design says.
3. **One-step kill switch.** 15-09 asks for the ability to disable an algorithm "with a minimal number of steps" (FETCHED).
4. **Dead-man alert off the host.** Alpaca's disclosures tell customers to set up monitoring for connectivity loss, power loss and crashes (FETCHED). Knight received 97 automated emails before the open and nobody acted (SEC 2013-222, FETCHED), so an alert must reach a human and stay rare. Healthchecks measures from `/start` and treats a missing success within grace as failure (FETCHED).
5. **No LLM in the order path, no ETF stops, no Docker, UNVERIFIED items probed first.** All shrink failure surface.
6. **Owner-startable trader tasks are feasible.** A task's DACL can grant execute permission to a user (Microsoft Learn, FETCHED). The question is whether they are worth building.

## Which controls prevent real losses (classification)

| Control in FINAL-design | Verdict | Why |
|---|---|---|
| Broker-side `no_shorting`, 1x margin, cash-bounded buying power | **Strongest, cheapest** | Alpaca rejects orders beyond buying power with 403 (FETCHED). A Knight-style runaway cannot exceed cash. Controls at the broker beat controls in code |
| Allow-list, notional caps, collar, per-run order cap | Keep | 15-09; Citigroup lesson (brief 12) |
| Deterministic ids, intents persisted first, lookup before submit | Keep | Duplicate-order family |
| Reconcile-on-start, foreign-order detection | Keep | Knight's missing control |
| HALT flag, workflow disable, Alpaca cancel-all | Keep, simplify | Few steps |
| Healthchecks dead-man; secret hygiene; hash-chained ledger | Keep | Cheap; v1 leaked a key; git can be the chain |
| Three accounts, ACL matrix, inbox/outbox, 9 trader tasks | **Disproportionate** | See P2 |
| Emailed approval hashes, rotating flatten code, 7-day expiry | **Disproportionate** | See P3 |
| SAFE state with risk-reducing class and auto-clear | Heavy | See P4 |
| Mutation score at least 95% on the gate | Heavy | See P5 |
| Manifest-hash HALT, `JARVIS-Deploy`, Claude Code blackout | Laptop artefacts | Vanish with a pinned-tag host |

## Is GitHub Actions a viable $0 host?

| Criterion | Laptop (design) | GitHub Actions, private repo, no card |
|---|---|---|
| Cost | $0 plus about $2.64 a month power (brief 23, ESTIMATE) | $0. Free plan has 2,000 private-repo minutes; with no payment method usage is blocked at the quota, so no surprise bill (FETCHED) |
| Minutes used | n/a | Design cadence 3 runs x 3 min x 22 days = 198 min (9.9%). Proposed 14 runs x 3 min = 42 min (2.1%). ESTIMATE; 3 min per run is assumed |
| Reliability | Unmeasured; Modern Standby, forced restarts (brief 23) | Docs: schedules "can be delayed" at high load, minimum 5 minutes, default branch only. Staff on a 2026 thread say runs may be dropped under high load; other 2026 reports show 8-14 hour delays on a new account (community threads, FETCHED, anecdotal) |
| Single instance | File lock to build | `concurrency` group; auto-disable hits only public repos (FETCHED) |
| Secrets | DPAPI, readable by anything running as that user (brief 23) | Encrypted repo secret; any user with write access can read it; third-party actions can leak it (GitHub hardening docs and CISA CVE-2025-30066, FETCHED) |
| Terms | Not applicable | Hosted-runner clause bars activity unrelated to producing, testing, deploying or publishing the repo's software, plus a "disproportionate burden" clause. A trading job is a **gray area** (GitHub terms, FETCHED) |
| Alpaca side | Own computer, per risk disclosure (brief 21) | Alpaca disclosure is risk language, not a ban; Alpaca publishes its own cloud-hosting tutorial (FETCHED) |
| Approval gates | Windows ACLs | **GitHub Free cannot use environments or required reviewers on private repos, and branch protection is not offered there either** (FETCHED) |

**Reliability arithmetic (ESTIMATE).** Assume a pessimistic 30% chance that a day's run is lost. The decision window is 5 trading days: 0.3^5 = 0.24% a month, so 1 - (1 - 0.0024)^12 = 2.9% a year of one missed month. That costs about $12.50 on a $1,250 satellite at an assumed 1% relative move, so the expected loss is 0.029 x $12.50 = $0.36 a year. Independence is assumed; outages correlate, so read it as order of magnitude. The design's catch-up rule already absorbs this.

**Verdict.** Viable for shadow and paper now, and for live later if a measured paper-phase log supports it. A terms or reliability failure costs a host move, not money: positions sit at the broker and the entrypoint is host-agnostic.

## What should improve

**S09-P1 (should). Make the job host-agnostic and run shadow and paper on GitHub Actions (section 8 "Host and process", section 11 P0-P3).** One entrypoint, reconcile-from-broker, state as append-only JSONL committed to a private data repo. Schedule off-peak minutes (not :00), only in the decision window plus one weekly reconcile, and log `scheduled_for` against `started_at`. P0-lite probe: 8-10 paper runs. Laptop stays dev box and attended fallback. Evidence: GitHub events, billing, concurrency docs; community threads (all FETCHED). Cost $0. Effort: saves 3.5-5.5 dev-days of DPAPI, Modern Standby, RAM and wake probes, adds 3-5, so about neutral (-1.5 to +2.5). Risk: gray terms and late runs; mitigated by the fallback and 5-day window.

**S09-P2 (must). Replace the three-account ACL model with "no live key where the Builder runs" (section 8 accounts, ACL matrix, inbox/outbox, `JARVIS-Deploy`, manifest).** Dev repo for Builder with a fine-grained token; separate prod repo holding the live secret, pushed only by the owner using a passphrase-protected SSH key. Release means the owner tags and pushes after reading the diff. Reasoning: the Builder writes the code that later runs with the key, so the OS boundary only protects against a session reading the key early, and owner diff review is the real control either way. Documents also show the standard-user `jarvis-trader` route needs the Logon-as-Batch privilege, which only Administrators and Backup Operators hold by default (Microsoft Learn, FETCHED); that edits a security policy and is not in the P0 probe list. Cost $0. Effort: saves 7-10, adds 1-2, net 5-9 dev-days. Risk: if the owner reuses one credential for both repos the boundary collapses; this is an owner rule, as the design already treats the inbox rule. Free-plan private repos cannot enforce reviewers, so it is a credential split, not a GitHub-enforced control.

**S09-P3 (must). Replace emailed-hash approvals with owner commits and `workflow_dispatch` inputs (sections 6, 8, 9).** Loosening, cash events, adopts, vetoes and halt-clear become owner-authored commits to prod config or typed dispatch inputs, audited by git and Actions. Keep the 72-hour cool-off as a date check on `effective_after`. Drop the rotating flatten code and 7-day expiry machinery. Evidence: 15-09 override control is met by the P2 credential split; Citigroup shows the danger is overridable soft warnings, not the lack of a second channel. Effort: saves 4-6, adds 1, net 3-5. Risk: an agent holding the owner's GitHub credential could approve; same owner rule as P2.

**S09-P4 (should). Collapse SAFE into "no-op and alert" (sections 6 states, 2 step 3).** Anomaly means place no orders, send `/fail`, exit; the next run re-reconciles, so recovery is automatic. Keep persistent HALT only for kill, lifetime stop and rate breach. Delete the risk-reducing class, same-run-funded T-bill rule and SAFE drills. Evidence: Knight lessons favour stop-and-cancel over clever recovery (brief 12, RECALLED mechanism). Effort saves 3-5, adds 0.5. Risk accepted: a sell signal can wait until the anomaly clears or the owner sells by hand; bounded by the 5-day window.

**S09-P5 (should). Swap the 95% mutation gate for a failure catalogue plus property tests plus one non-gating mutmut run (sections 3 roster row 1, 11 P3).** Catalogue: unit errors, duplicate ids, stale quotes, 100x notional, double submit, crash between intent and submit. Evidence: Yuan et al. (OSDI 2014) found over 30% of catastrophic failures preventable by simple error-handling tests (FETCHED); Google's mutation system needed diff scoping and arid-line filtering to be usable (Petrovic et al., FETCHED abstract). Equivalent-mutant triage on a hard 95% bar is open-ended solo work. Effort saves 2-4, adds 0.5-1. Risk: weaker adequacy evidence, offset by retained GF drills.

**S09-P6 (should). Right-size monitoring (section 8).** Two Healthchecks checks: a weekly heartbeat and "decision recorded by day 8"; email plus one phone push; about 2 alerts a month, each with a runbook line; status codes only. Effort 0.5 day. Evidence: Knight's 97 ignored emails.

**S09-P7 (could). Git as the ledger chain; drop `ledger_ro.sqlite`, outbox export, nightly backup and monthly anchor email (sections 2 step 17, 8).** SQLite becomes a cache rebuilt from JSONL; Alpaca's trade confirmations are an independent record. Saves 2-3, adds 1. Risk: one GitHub account controls ledger and workflow; a local clone detects history rewrites.

**S09-P8 (could, cross-domain with the LLM-cost reviewer). No Anthropic production key on the trading host in v1 (section 3).** The Incident Analyst writes a sanitised incident file; the owner triages in an attended Claude Code session on the plan; the Narrator stays templated or attended. Removes a secret, the capped workspace, O19 and the T0 spend of about $0.70 a month (design section 3). Saves 3-6 dev-days (my estimate). Risk: fewer unattended agent roles; the owner wants visible agents, so that reviewer should decide.

**S09-P9 (could). Build the attended executor MVP right after P1a, before the P2 verdict (section 11).** S0 live needs only GF + G3 + L0, not the S-A verdict. The MVP is the minimum control set below, about 20-28 dev-days (ESTIMATE). At 2.5 dev-days a week it finishes about month 4-5; three paper month-ends overlap, so L0 lands near month 6-7, not 12-15 (ESTIMATE). Live execution is attended first: the owner runs one command and types the live key, so no key sits at rest; unattended is a later wrapper. Caveat: S0 can be bought by hand in ten minutes, so the value is practice and fill data for G4. Risk: early live bugs, limited by the 25/50/75/100 tranches.

**Totals (ESTIMATE).** P2-P5 and P7 net 12.5-23.5 dev-days; P1 about 0; P8 3-6 more. That is roughly 16-30 of 134-182 dev-days (9-22%). It does not by itself fix the timeline; P9 does.

## Minimum control set (smallest that keeps all seven required controls)

1. Default-deny gate: 6-ticker allow-list, notional caps, collar, run-level order cap. 4-6 days.
2. Idempotent orders (`hash(decision_id, leg, attempt)`, intent persisted, lookup first) plus reconcile-on-start, fail closed. 8-10 days including brief 04's 5-day spike.
3. Kill switch: HALT variable or file, disable workflow, Alpaca cancel-all. 1 day.
4. Dead-man: two Healthchecks checks. 0.5-1 day.
5. Secret hygiene: revoke v1 key, paper/live split, live key in one place, gitleaks, SHA-pinned or no third-party actions, hashed lockfile, MFA on GitHub, Alpaca and email. 1-2 days.
6. Ledger: append-only JSONL with prev-hash, committed each run. 2-3 days.
Total about 17-23 dev-days, about 20-28 with the Actions wrapper (ESTIMATE), against P3's 43-53.

## What I could not verify

- Frequency of Actions delays and drops: only two community threads and a staff caveat. Measure in P1.
- Whether GitHub would treat a trading job as "unrelated" activity: no enforcement data.
- Alpaca duplicate `client_order_id` behaviour; the full Customer Agreement (not reopened).
- Logon-as-Batch for standard users: read from docs, not tested.
- Whether a fine-grained GitHub token can be scoped as P2 assumes: not opened.
- Helland (403) and Petrovic 2018 (snippet only); Knight order detail via summariser.
- All dev-day figures are my judgement; the design does not itemise.

## References

- SEC press release 2013-222 (Knight). https://www.sec.gov/newsroom/press-releases/2013-222 - FETCHED. SEC order 34-70694, https://www.sec.gov/files/litigation/admin/2013/34-70694.pdf - FETCHED via summariser.
- FINRA Notice 15-09. https://www.finra.org/rules-guidance/notices/15-09 - FETCHED.
- GitHub Docs (schedule event, secrets, security hardening, billing, limits, concurrency, environments, protected branches) under https://docs.github.com/en/actions - FETCHED. Terms for Additional Products, https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features - FETCHED.
- CISA, CVE-2025-30066. https://www.cisa.gov/news-events/alerts/2025/03/18/supply-chain-compromise-third-party-github-action-cve-2025-30066 - FETCHED.
- GitHub community threads 185355 and 201738 (2026). https://github.com/orgs/community/discussions/185355 - FETCHED, anecdotal.
- Alpaca disclosures, key-security article, order reference. https://alpaca.markets/disclosures , https://docs.alpaca.markets/reference/postorder - FETCHED.
- Healthchecks docs. https://healthchecks.io/docs/measuring_script_run_time/ - FETCHED.
- Microsoft Learn, Task Scheduler security contexts. https://learn.microsoft.com/en-us/windows/win32/taskschd/security-contexts-for-running-tasks - FETCHED.
- Yuan et al., "Simple Testing Can Prevent Most Critical Failures", OSDI 2014. https://www.usenix.org/conference/osdi14/technical-sessions/presentation/yuan - 198 failures, over 30% of catastrophic ones preventable. FETCHED (abstract page).
- Petrovic, Ivankovic, Fraser, Just, "Practical Mutation Testing at Scale", arXiv 2102.11378, 2021. https://arxiv.org/abs/2102.11378 - FETCHED (abstract).
- Petrovic and Ivankovic, "State of Mutation Testing at Google", ICSE-SEIP 2018 - RECALLED (search snippet).
- Helland, "Idempotence Is Not a Medical Condition", ACM Queue 2012 - RECALLED (403).
- Briefs 04, 12, 21, 23: secondary, earlier fetches by other authors.

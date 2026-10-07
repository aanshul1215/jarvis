# JARVIS Final Design (revision of Synthesis v1 after red team)

Chief architect, 2026-10-01. This document stands alone and replaces SYNTHESIS-v1.md.

**How to read the tags**
- Brief numbers refer to research/01-23. "00" is the gap analysis and "00b" is the gap-fill summary.
- **(DC)** marks a design choice. It does not come from the literature, and it must be simulated or probed before it is frozen.
- **ESTIMATE** marks arithmetic built on brief figures.
- **UNVERIFIED** marks a claim that no brief confirms, including general knowledge. Each one has a probe or an open item attached.
- **ILLUSTRATIVE** marks example numbers that are not data.

**Base: Proposal D (failure-first).** D had the highest mean score (7.28) and no fatal finding. It also led on the lenses where a mistake costs money: risk, security, validation and execution. Its two weak lenses were fidelity and buildability. This revision repairs both:
- The control semantics are now defined: the live-capital ladder, SAFE/HALT, retry, deposits, sleeves and the ACL model.
- The owner's ideas each have a row in an idea ledger (section 10).
- The Claude roles now carry real, visible, money-safe work.

---

## 1. Thesis

JARVIS has two parts.

1. **A deterministic trading desk.** A small long/flat monthly ETF book runs as a scheduled job behind a default-deny risk gate. A hash-chained ledger records every action.
2. **A Claude operations team.** Claude agents build the desk, watch it, triage its incidents, explain it, research for it and audit it.

**No Claude output decides an order.** The reasons:
- No study in the evidence base shows an LLM trading agent beating buy-and-hold net of costs over a multi-year, multi-symbol, post-cutoff sample (brief 01).
- The forward tests that exist are short and underpowered: StockBench 82 days, LiveTradeBench 50 days, mostly without costs. Alpha Arena is secondary-source only: two of six models finished up over about two and a half weeks (18 October to 3 November 2025).
- CLQT and AlphaForgeBench show run-to-run instability, and a "stating versus doing" gap, when LLMs make direct trade decisions (brief 01).
- This is an absence of shown edge, not proof that no edge exists. Even so, it gives no support for putting an LLM in the selection, sizing or exit path.
- The core must also run at $0 with the LLM switched off (brief 22).

### The number the owner must read first (all ESTIMATE)

**Inputs**

| Symbol | Meaning | Value | Source and grade |
|---|---|---|---|
| E | S-A's net CAGR minus holding the same ETFs, before tax | -1 to +1 point a year, central 0 | Brief 18, medium. Extrapolated from Faber's self-reported figures (his result tables were images, so no numbers were read) and one unverified blog. Huang-Li-Wang-Zhou found little evidence for time-series momentum asset by asset. |
| C | ETF trading cost | 0.03% a year (2 bps a leg) to 0.14% (10 bps a leg) | Brief 18. Subtracted explicitly; this may double-count up to 0.14 if E already includes cost. |
| H | Tax hurdle, taxable account | **Planning value 1.0-1.3 points** | Brief 19: cases A-C, 10 years, 100% short-term realisation, 8% gross. It rises to 1.26-1.51 at 20 years and 2.57 in the top bracket. |
| H′ | Tax hurdle, sensitivity | 0-0.9 points | Brief 18: trend exits realise many short-term losses, so the true gap lies between 0 and 0.9. |
| H(IRA) | Tax hurdle in an IRA | 0, less any IRA fee (unknown, O3) | Brief 19 |

**Arithmetic: D = E − C − H** (points a year, on the money S-A runs)

| Case | Central | Range |
|---|---|---|
| Taxable, planning hurdle (brief 19) | 0 − 0.1 − (1.0 to 1.3) = **−1.1 to −1.4** | −1 − 0.14 − 1.3 = **−2.4** up to +1 − 0.03 − 1.0 = **0.0** |
| Taxable, brief 18 sensitivity | 0 − 0.1 − (0 to 0.9) = −0.1 to −1.0 (midpoint about −0.5) | up to about +1.0 if the tax gap is 0 |
| IRA | **−0.1** before the IRA fee | −1.1 to +1.0 |

**Dollars a year**

| Basis | Taxable, central | Taxable, range | IRA, central |
|---|---|---|---|
| Whole account at $10,000, if S-A ran all of it | **−$110 to −$140** | −$240 to $0 (+$100 under brief 18's best case) | −$10 |
| Whole account at $1,000 | −$11 to −$14 | −$24 to $0 | −$1 |
| Satellite only, at G4 (12.5% of $10,000 = $1,250) | **−$14 to −$18** | −$30 to $0 | about −$1 |

Formula: dollars = D × capital × stage_fraction. Only the satellite carries D. The core S0 *is* the null, so it carries none.

**Fixed costs come on top.** At the lowest capital tier, the LLM add-on is about $0.70 a month (section 3), which is about 0.84% a year of $1,000 or 0.08% of $10,000. The cap limits it to at most 1% of capital a year.

**What JARVIS is expected to deliver** (expected, unverified; G1b decides):
- Drawdown control. Brief 18's "about half the drawdown" is an ESTIMATE of medium grade. The one blog figure is −20% versus −24% over 2014-2026, with a CAGR of 8.4% versus 13.6% (UNVERIFIED).
- Discipline, and a tamper-evident record.
- An AI team doing real work (section 3).

**If S-A cannot beat a risk-matched benchmark after tax, JARVIS runs the benchmark (S0, or S0 with a T-bill dial) and stays on as monitor, auditor, explainer and lab. That counts as a successful outcome.**

**Timeline** (ESTIMATE, assuming 15 hours a week; O2 is unknown and moves every date):

| Month | Milestone |
|---|---|
| About 2 | First shadow email and first Claude-written memo |
| About 6-8 | Strategy verdict (the P2 fork) |
| About 10-13 | Paper executor ready |
| About 12-15 | First live dollars (L0, the S0 core in tranches) |
| About 13-16 | Satellite micro-live (G4) starts |
| About 31-34 at the earliest | Satellite at full size |

---

## 2. End-to-end flow

Labels: `[CODE]` deterministic, `[STAT]` statistical, `[CLAUDE]` agent, `[OWNER]` human. Every job runs as the Windows user `jarvis-trader` from a tagged, read-only checkout at `C:\jarvis-prod` (section 8). The dashboard maps the steps onto the owner's v3 state names in a **state ribbon**:
- OBSERVE: steps 14-15
- INVESTIGATE: step 15 scoring
- VALIDATE: steps 5 and 10
- READY: steps 8-9
- EXECUTE: step 11
- MANAGE: steps 3-4 and 12
- SAFE/HALT: section 6
- LEARN: steps 17 and 20-25

### `JARVIS-Trade`: about 10:00 ET each trading day, with a retry at 11:00 that exits at once if no work is pending

Signals are computed on month-end data, and action happens on the following trading days.

1. [CODE] Take the lock and send the Healthchecks start ping. The `/start` and `/fail` semantics are recalled, not read (brief 23); P0 probes them.
   - Read the system state and the HALT flag file (section 6).
   - Verify `manifest.sha256`, which covers the gate module, `risk.yaml` and the lockfile. A mismatch means HALT.
2. [CODE] **Broker-constraints adapter.** Read account status, buying_power, `no_shorting`, the margin multiplier, the crypto flag and the fee tier. Anything unexpected means SAFE (brief 21).
3. [CODE] **Ingest account activities**, then reconcile each account. The activities feed covers fills, dividends, fees, splits and transfers. Endpoint and type codes are UNVERIFIED; the P0 probe settles them, and the fallback is a diff of positions and cash.
   - Expected differences: dividends, fees, partial fills, JARVIS's own fills, corporate actions in `corporate_actions`, and **owner cash events registered with `jarvis cash-event`** (section 9).
   - Cash tolerance is max($1, 0.1%) (DC). Anything unexplained means SAFE.
4. [CODE] **Adopt earlier intents.**
   - For every non-terminal intent from any earlier run, look up its `client_order_id` at the broker.
   - If the order is still working, cancel it and wait for a terminal state (up to 5 minutes, DC). Record any fills. If the order is not found, mark the intent `ABANDONED`.
   - An open broker order that matches no intent is foreign, which means SAFE.
5. [CODE] **Data-trust gate, per symbol** (DC thresholds).
   - The Alpaca and Tiingo month-end closes must agree within 0.5%, compared raw to raw.
   - A move over 30% with no matching `corporate_actions` row is quarantined.
   - A failing symbol gets no risk-increasing order. A signal-driven **sell is still allowed if both vendors' own series give the exit signal**, which follows the owner's "DATA-UNTRUSTED means no new trade."
   - There is no manual override (00: a degraded-data override is removed).
   - On failure, the Incident Analyst runs Data-Trust Triage (section 3).
6. [CODE] Freeze and hash the **AsOfSnapshot**: month-end as-of data with `available_at <= decision_time`.
   - `decision_id = hash(strategy_version, decision_date, snapshot_hash)`. It is stable across the 10:00 and 11:00 runs and across catch-up days.
7. [CODE] **Decision window.** Steps 8-11 run only on the first 5 trading days of the month (catch-up rule) or when a drill is armed. On other days the run ends after step 12.
   - "Done" means every sleeve is within its band, or every remaining delta is under $20.
   - If a symbol still fails the trust gate after day 5: alert, hold the position, log `MISSED_REBALANCE`, and wait for the next month (DC).
8. [CODE] Strategy plug-ins: `Strategy.target(AsOfSnapshot) -> TargetBook` for each sleeve. The live sleeves are the S0 core and the S-A satellite at `stage_fraction`. S0-RM and the ML lane run in shadow only.
9. [CODE] **Combine.**
   - Net the sleeve deltas per symbol, keeping each sleeve's share for attribution.
   - Cost gate: skip deltas under $20 or inside the band.
   - **Tax-lot check** for discretionary S0 band sales in a taxable account: defer a sale that would realise a short-term gain within 30 days of turning long-term (brief 19 item 5; window DC). S-A exits are never deferred.
   - **Wash-sale guard** across all of the owner's accounts (section 6).
   - Keep a 2% cash buffer. Sells go first.
10. [CODE] **Risk gate** (section 6). Every decision writes a reason code to `gate_log`.
11. [CODE] **Execute.**
    - Persist each intent with state `PLANNED`, then `SUBMITTED`, `WORKING`, and finally a terminal state: `FILLED`, `CANCELLED`, `REJECTED`, `EXPIRED` or `ABANDONED`.
    - `client_order_id = hash(decision_id, leg, attempt)`, at most 128 characters (brief 21). Before any submit, look up the id; that lookup, not the broker's rejection, is the idempotency control (brief 23).
    - Orders are marketable limits (section 6 formula) between 09:45 and 15:30 ET. Poll to a terminal state with a **15-minute timeout** (DC); then cancel, wait for a terminal state and record any partial fill. The remaining delta is picked up by the retry or by the next catch-up day.
    - Buys are sized from broker buying_power after the sells reach a terminal state.
    - `attempt` increments only after the earlier id is confirmed terminal.
12. [CODE] **Protection check.** No unexpected open orders remain; stop verification is added once a stop-bearing sleeve exists.
    - Append to the hash-chained `ledger` with sleeve tags.
    - A run that ends in RUN sends the success ping. A run that ends in SAFE or HALT sends the `/fail` ping, whose body is a status code only and never a balance.

### `JARVIS-Evening`: 19:00 ET

13. [CODE] Archive EDGAR 8-K items, Form 4 filings and Alpaca news headline *metadata*, each with `first_seen_at`.
14. [CODE] **Watch scan.** Price/volume z-scores, 8-K items, Form 4 buy clusters and news-volume spikes become `watch_items`, each with a pre-registered forward-outcome label.
    - **Integrity flag** (the owner's Manipulation agent, defensive only): price z > 3 and volume z > 3 with no 8-K or news on file marks a watch item "integrity risk; corroboration needed" (DC). It never claims misconduct (v2 wording; brief 07).
15. [CODE] **Cost monitor** (the owner's Flow agent, kept as a monitor; brief 07): per-fill slippage against the arrival quote, plus quote age. Score matured watch outcomes, and score the ML lane forward (section 4).
16. [CODE] Shadow NAV for S0, S0-RM and S-A.
    - Pre-tax from P1; the after-tax column is added at the end of P2.
    - Pessimistic fills apply **only in shadow NAV**, never in the broker-reconciled ledger.
17. [CODE] **Daily digest** by email (section 9). The ntfy message carries a status code only (brief 23: the topic name acts as the password).
    - Write `ledger_ro.sqlite` and an encrypted backup to the outbox (section 8).
    - On the first evening of each month, email the ledger head hash to the owner's second inbox, as the off-host anchor.

### Weekly and on events

18. [CLAUDE] **Narrator**: a weekly memo through Batch, plus synchronous notes on each trade and on each SAFE/HALT or gate transition.
19. [CLAUDE] **Incident Analyst**, a tool-using agent: runs on SAFE, HALT or a data-trust failure.
20. [CLAUDE] **Change-Watch Analyst**: runs when a watched vendor or model page changes its hash.
21. [CLAUDE] **Red-Team**: runs on any artifact the owner submits (spec, harness report, gate diff or loosening request).
22. [CLAUDE] **Reader**: a weekly batch, submitted Sunday and collected Monday, which builds the Watchlist Digest. It is enabled from capital tier T1.
23. [CLAUDE + OWNER] Attended Claude Code sessions: **Builder**, the monthly **Strategy Lab**, and **Ledger Analyst** (`/ask-ledger`).
24. [CODE] Agent report card, added to the weekly memo (section 3).
25. [OWNER] Quarterly Mission Plan review (section 9).

---

## 3. Agent roster: what "uses AI agents" honestly means here

**The split.** The evidence gives no support for Claude selecting, sizing or exiting trades (briefs 01, 02, 10). It does support Claude for:
- building software;
- extraction;
- narration;
- adversarial review of artifacts;
- bounded investigation;
- offline research (briefs 01-03).

So Claude gets every job on the second list. Each job has an input contract, a mechanical verifier, a budget and a list of forbidden actions.

**Honest census: 8 Claude roles.**
- **Agentic and attended (3):** Builder, Ledger Analyst, Strategy Lab. These are multi-step, tool-using Claude Code sessions that the owner runs.
- **Agentic and unattended (1):** Incident Analyst. It is tool-using, read-only, capped at 8 turns and $0.50.
- **Single-shot LLM workflow steps (4):** Narrator, Red-Team, Reader, Change-Watch Analyst.

Nothing agentic places an order. The one route by which Claude's creativity reaches money is this chain: Strategy Lab spec, then the deterministic harness, then Red-Team, then the owner's G0 freeze, then G1-G5. **Claude authors, code decides, and the owner signs.**

### Spend, models and capital tiers

- Production calls use an API key in a dedicated `jarvis` workspace. The Default Workspace cannot hold a limit (brief 22). A small prepaid balance is the real ceiling, because batches can overshoot.
- **Monthly cap: `min($15, 1% × capital / 12)`.** That is $0.83 at $1,000, $2.08 at $2,500, $4.17 at $5,000 and $8.33 at $10,000. When the cap is reached, the LLM is unavailable and trading is unaffected.
- **One pricing basis for every number in this section** (ESTIMATE, brief 22 prices, no caching assumed). Batch roles are priced at Sonnet 5.5 Batch, $1 in and $5 out per MTok, with tokens ×1.3 for the new tokenizer. Synchronous roles are priced at Sonnet 5.5, $2 in and $10 out. Haiku 4.5 is *not* the basis, because its retirement floor is 2026-10-15.
- Model IDs live in `config/models.yaml`, **with the mode per role** (sync or batch). There is a daily check that each model ID still exists, and a weekly hash of the deprecations page. An alert starts the 60-day procedure (brief 22).
- Every call is stored in `llm_calls`: full request, response, model, prompt hash, usage and `stop_reason`. A `refusal` or `max_tokens` stop produces null. Batch results are persisted on arrival, because retention is 29 days (briefs 13, 22).
- **Validation budget.** Golden-set, injection-set and model-change runs come from a separate `jarvis-eval` workspace with its own prepaid limit, outside the monthly cap. ESTIMATE about $2-6 per model change: Reader golden set about $1.1 if all 300 items are headline-sized, up to about $4.5 if all are brief 22-sized filing excerpts; injection set about $0.4; Narrator CI about $0.2. That happens roughly yearly (brief 22: about a 12-month model cadence). A trader task, `JARVIS-Eval`, runs it.
- **Plan cost.**
  - If the owner already pays for a Claude plan for other reasons, it is **sunk and excluded** from the sunset test, and the document says so.
  - If a plan is bought for JARVIS ($20 a month, brief 22), it counts in the sunset test and in the 600× rule. That rule needs $12,000 of capital, more than the owner's range, so a plan cannot be justified by JARVIS's trading alone. It is justified, if at all, as the cheapest way to *build* JARVIS (see O1).

**Per-role budget and priority** (ESTIMATE, per month)

| Priority | Role | Estimate | Basis | Mode |
|---|---|---|---|---|
| 1 | Incident Analyst reserve | $0.35 held first | One 8-turn incident: 8 × (13k × 1.3 = 16.9k tokens × $2/M + 0.8k × $10/M) = 8 × $0.042 ≈ $0.33 | sync |
| 2 | Narrator (weekly memo plus about 2 event notes) | $0.25 | Memo 15.6k in, 3k out at batch rates ≈ $0.031 × 4.33; notes ≈ $0.06 each | batch / sync |
| 3 | Change-Watch | ≤ $0.10 | About 6.5k in, 0.8k out ≈ $0.02 per change | sync |
| 4 | Red-Team | about $0.10 averaged; event-driven | About 39k in, 3k out ≈ $0.11 per review | sync; **borrows the unused incident reserve within the month** |
| 5 | Reader (Watchlist Digest) | $0.80 | About 217 headline-sized items a month × $0.0037 per item (brief 22's 2,100-token item at Sonnet batch with ×1.3). A brief 22 filing excerpt (9,500 tokens) costs about $0.015, so the item mix is capped in config to stay inside $0.80 | batch |
| 6 | Nightly Narrator upgrade | +$0.52 | 21 × $0.031 − weekly $0.13 | batch |

**Capital tiers.** Each threshold follows from the cap formula: capital = monthly total × 12 / 1%.

| Tier | Roles on | Monthly total | Capital needed |
|---|---|---|---|
| T0 | Incident, Narrator weekly, Change-Watch, Red-Team (from reserve) | $0.70 | ≥ $840, so the whole $1,000-$10,000 range qualifies |
| T1 | T0 plus Reader digest | $1.50 | ≥ $1,800, set at **$2,000** (DC rounding) |
| T2 | T1 plus nightly Narrator | $2.02 | ≥ $2,424, set at **$2,500** (DC rounding) |

**Fallback when the cap is exhausted** (pre-registered for each role):
- Narrator: the templated memo.
- Reader: the digest is skipped and the archive continues.
- Change-Watch: a raw-diff email.
- Red-Team: the review is queued, and nothing that needs it can proceed.
- Incident Analyst: the runbook step is chosen by code from `cause_enum` rules.

The dashboard shows the cap, spend per role and the active tier.

### Roster

| # | Agent | Kind | Real work | Trigger / identity | Input → output | Mechanical verifier | Forbidden |
|---|---|---|---|---|---|---|---|
| 1 | **Builder** | Agentic, attended | Writes all code, tests, the mock broker and the runbook | Owner's Claude Code sessions in `C:\dev\jarvis` (owner user) | Repo → commits | Gate property tests; **mutation testing on `jarvis/gate/`** (for example mutmut; ≥ 95% of non-equivalent mutants killed, DC set at P3); future-poisoning; replay identity; GF drills; owner-reviewed diffs for `jarvis/gate/` and `config/risk.yaml` | Any access to trader files (OS ACL, section 8); deploying (only the trader deploy task does that) |
| 2 | **Narrator** | Single-shot | Weekly memo; explains trades, rejections, gate moves, attribution and dollar downside; explains the Mission Plan; turns SHAP values from the ML lane into plain words | `jarvis-trader` task; batch weekly, sync for events | **Whitelisted typed fields only**: ledger numbers, enums, Reader `event_type` and `materiality`, code-built links → `Report{headline, actions[], rejections[], risk_state, vs_S0, vs_S0RM, attribution, questions_for_owner[]}` | Every number is checked against the ledger; the template is sent on failure; the injection set runs in the Narrator's CI as well | Raw text or spans; URLs or HTML other than code-built links; any recipient but the owner |
| 3 | **Ledger Analyst** | Agentic, attended | Conversational JARVIS ("why did we sell gold in March?"); the successor to v1's chat | `/ask-ledger` in the owner's Claude Code | `outbox\ledger_ro.sqlite` (read-only URI) → an answer plus its SQL | The SQL is shown; the connection is read-only | Writes; network; archive text |
| 4 | **Red-Team** | Single-shot | Pre-mortem on G0/G1 packages, promotions, loosening requests and gate diffs | Owner drops the artifact in `C:\jarvis-inbox`, then runs the trader task `JARVIS-RedTeam`; production key and Red-Team budget; fresh context | Spec, harness report or diff → `{failure_modes[], missing_evidence[], leakage_suspects[], kill_conditions[]}` in the outbox | **Must catch ≥ 12 of 20 seeded defects** (v1's four plus at least 16 synthetic; DC) before its notes may be cited for a promotion or a loosening. Cross-family heterogeneity is unavailable and untested (brief 02) | Approving; probabilities |
| 5 | **Strategy Lab** | Agentic, attended | Ideas → G0 specs; backtests through the harness; the Shadow ML lane | Monthly, owner's session, dev tree | Research copy → `StrategySpec` plus trial rows | `jarvis-lab run <spec_id>` logs to `lab.sqlite.trials` *and* appends spec and result hashes to the trader-side registry through the inbox; ≤ 20 variants per family; cumulative N_eff. The sealed holdout can be evaluated only through the trader task `JARVIS-HoldoutEval`, which returns metrics, never rows, and logs `holdout_burns` | Holdout rows (OS ACL); production paths (OS ACL); web |
| 6 | **Incident Analyst** | **Agentic, unattended** | Investigates SAFE, HALT and data-trust failures; drafts the incident report and the runbook step; **Data-Trust Triage** works out why vendors disagree (split, dividend, stale bar) and drafts a `corporate_actions` row | `jarvis-trader` task, sync API, ≤ 8 turns, ≤ $0.50 | Read-only tools: `query_ledger_ro` (SELECT only), `gate_log`, `intents_vs_activities`, `log_window` (redacted), `vendor_status_snapshot` (code-fetched, sanitised) → `{timeline, cause_enum, runbook_step_id, evidence_row_ids[], draft_corporate_action?}` | Must cite real row IDs. A draft corporate action is accepted only if code confirms it reconciles both vendors' raw series to within 0.5%, **and** the owner approves it with the approval hash | Write tools; clearing SAFE or HALT; keys; any order |
| 7 | **Reader** (quarantined) | Single-shot | Typed events from archived filings and headlines for the owner's watch list → the **weekly Watchlist Digest** (section 9) | Trader tasks `JARVIS-ReaderSubmit` (Sunday) and `JARVIS-ReaderCollect` (Monday, retried daily until collected and well inside 29 days); tier T1 and above | NFKC-normalised, HTML-stripped, length-capped, JSON-encoded text → `{event_type, materiality, novelty, instruction_like_text, span_start, span_end}` | Spans must be code-verified substrings or null; golden set; injection set in CI | Tools; network; ticker mapping (code maps the EDGAR CIK); free text; any effect on any order |
| 8 | **Change-Watch Analyst** | Single-shot | Says what changed on a vendor or model page (fractional rules, GTC, fees, PDT/intraday margin, crypto states, model retirement) and which config key or runbook step it touches | `jarvis-trader` task when a weekly page hash changes | Sanitised, length-capped text diff → `{page_id, summary≤300 chars, affected_config_keys[] (closed enum), runbook_step_ids[], severity}` | The keys must exist in the enum; the diff is treated as untrusted (injection set) | Changing config; tools |

**Agent report card** (in the weekly memo, computed by code). For each role:
- authority level;
- quality measure: Red-Team catch rate; Reader schema-valid rate and golden accuracy; Incident drafts accepted or rejected by the owner; Narrator validator failures; Change-Watch true or false alarms;
- spend against budget.

This makes "agents earn authority by evidence" visible.

### Reader ladder (revised)

- **A0, extraction quality.** At least 99% schema-valid, and accurate on a golden set of about 300 items, plus the injection set.
  - Labels are deterministic for `event_type` only: 8-K item numbers and Form 4 codes (brief 22).
  - `materiality`, `novelty` and `instruction_like_text`, and every headline field, need **hand-labelling**. Budget: the owner labels about 100 items, roughly 3-4 hours (DC).
  - Until that is done, A0 claims cover `event_type` only.
- **A1, forward shadow** at weight 0. The target is pre-registered: |5-day return of the stock minus the registered benchmark ETF| > 2 × trailing 60-day volatility × √5 (DC). This is scored with Brier against a pre-registered **code baseline**, a logistic regression on trailing volatility only.
  - **Power rule: at least 100 positive outcomes**, not 100 events (DC).
  - At about a 5-10% positive rate that means about 1,000-2,000 events. O16 counts positives over the first 60 days. If 100 positives would take more than 9 months, A1 is declared unreachable.
  - **Honest outlook: likely unreachable** within one model generation.
- **A2 as earlier written ("veto or reduce risk-increasing orders") is deleted.** No text event maps to a broad-ETF order, which is what critic D10 found. What remains is A2′: a Reader flag may add a caution line to the monthly email, with no effect on any order. Single-name use would need a single-name satellite, which is unreachable below the Norgate threshold (section 12).
- **There is no A3.** Text never raises a position, and never blocks an exit, a stop re-arm or the kill switch (brief 13).
- **On a model change**, the successor is re-run over archive text dated after *its* cutoff, and the forward clock restarts (brief 22).

### What happens to v3's 18 agents

| Becomes | Agents |
|---|---|
| Code | Orchestrator (code state machine; LangGraph dropped, see section 10), Goal Planner (Mission Plan), Scanner (watch scan), Data Trust, Market/Technical, Crypto (deferred), Strategy/Portfolio, Capital Governor, Execution, Position Manager, Ledger, **Flow → cost monitor (step 15)**, **Manipulation → integrity flag (step 14)** |
| Statistics | Volatility (EWMA; HAR or GJR only if it wins out of sample; brief 15); rule-based regime label (section 4); Shadow ML lane (one LightGBM at weight 0) |
| Claude | News/Fundamental → Reader plus Watchlist Digest; Bull/Bear → Red-Team; Ledger/Review → Narrator plus Ledger Analyst; incident handling → Incident Analyst; vendor and model watch → Change-Watch |

The dashboard labels every role [code], [stat] or [Claude].

---

## 4. Strategies, sleeves and universe at launch

**Universe.** Five liquid risk ETFs (US equity, developed ex-US, intermediate Treasuries, REITs, commodities/gold) plus one T-bill ETF.
- Tickers are fixed at G0, and choosing them counts as a registered trial.
- **Day 1 of P2 records each ETF's inception date** (O14).
- Fractional quantities are allowed.

**Strategies**

- **S0 core: the null, and live after L0.** The five risk ETFs at 20% each, **with no T-bill**.
  - It rebalances only by new contributions or by its band. The band is **relative ±20% of target weight**, so 16% to 24% of the core. The ceiling stays below the 25% per-symbol cap (DC; brief 18 uses a 20% band only for its crypto sleeve).
  - In a taxable account the null therefore rarely realises gains.
  - It has no drawdown stop, by design (DC): stopping a buy-and-hold at a drawdown is market timing, which is an unvalidated strategy in its own right. The owner's risk tolerance is handled by the dial.
- **S0(b) dial and S0-RM.** S0(b) is S0 with a fraction b held in the T-bill ETF.
  - **S0-RM** is S0(b*), with b* chosen so its backtest volatility matches S-A's. It is the risk-matched null: "half the drawdown" can also be bought simply by holding less risk.
  - The **owner's dial** b comes from the Mission Plan's risk tolerance (section 9). It is the product if S-A is retired.
- **S-A satellite: plain Faber 10-month SMA, as published.** Each of the five ETFs gets 20% of the satellite. At month-end each is either long or in the T-bill ETF. There is no intra-month stop. Expect about 3-4 round trips a year (brief 18).
  - Overlays (vol target at leverage 1.0, drawdown throttle, band width) are off at launch. Each one is a registered trial, adopted only if the ablation improves G1b.
- **Shadow ML lane (the owner's v1 heritage, at weight 0).**
  - One LightGBM classifier, which brief 15 names as the right default for tabular outcome classification. It predicts whether each ETF's next-month return beats the T-bill ETF.
  - Features come from the AsOfSnapshot only: 1/3/6/12-month returns, distance from the 10-month SMA, trailing 60-day volatility, the other ETFs' returns, and the FRED rate level.
  - Purged, embargoed walk-forward cross-validation; isotonic calibration on purged out-of-fold predictions; a reliability curve.
  - SHAP top-3 drivers go to the Narrator as typed numbers.
  - It is registered as family `ml-lgbm-v1`, scored forward from its registration date, and every refit counts as a trial. It reaches money only through G0-G1c-G1b (section 7).
  - Honest outlook: about 1,200-1,500 pooled monthly rows (5 ETFs × roughly 20-25 years × 12), which is small. Expect no edge. It must also pass the leak tests that v1 would have failed.
- **Regime label** (the owner's regime/cross-asset idea; brief 15). Per asset: above or below the 10-month SMA, crossed with the tercile of trailing 60-day volatility against its own history. It is shown on the dashboard and in the memo. It acts as a risk dial only through a registered spec. There is no HMM: default library outputs leak future data (brief 15).
- **Crypto:** deferred (section 12).

### Sleeves in the live book

- `orders`, `lots`, `ledger` and `attribution` carry a `sleeve` tag: `S0`, `SA`, `MANUAL` or `XFER`.
- **Sleeve NAV** is the sum of the sleeve's tagged lots at mark plus its tagged cash.
- Opposite sleeve deltas in one symbol are netted into one broker order. The internal share is recorded as an `XFER` book transfer at the fill price. It has no tax effect, because it is the same account.
- **Real broker tax lots may differ from sleeve lots.** Alpaca's lot method is unknown (O4); P0 logs it, and the tax simulator uses the broker's method.
- **Core-satellite.** `satellite_$ = stage_fraction × marked equity`. S0 holds everything else, so money S-A has not yet earned is never idle cash.
  - `stage_fraction` rises only through approved G5 steps. It is cut by the loss bands, never because a target was missed (v3 compounding rule).
- **Account layout constraint (decided in P0, from brief 19 and Rev. Rul. 2008-5).** Both sleeves sit in **one account of one type** by default. If the owner splits them (for example S0 taxable and S-A in an IRA), the sleeves must use **disjoint tickers**, and each account gets its own reconciliation.
  - Whether different-issuer ETFs on the same index are "substantially identical" is a question for the tax professional (O4).
- **The G1b lot-level tax simulation runs on the combined core-plus-satellite book**, not on each sleeve separately, so wash-sale interactions between sleeves are counted.

### Owner Idea Lane

Single-name ideas (v1's TSLA, Form 4 buy clusters, the owner's own picks) are tracked in shadow with forward outcomes and a Red-Team note. They are never traded directly.

**Promotion path:**
1. A watch pattern with at least N matured forward events (N fixed at registration, DC) beats a pre-registered null after deflation by the cumulative trial count (the section 7 DSR machinery). It then becomes a Strategy Lab spec.
2. The spec is Red-Teamed, and the owner freezes it at G0.
3. It enters shadow as a new Strategy plug-in, judged against S0 and S0-RM.
4. It goes live only through G1-G5.

**Honest limit, pre-registered.** Single-name trading is not reachable below the Norgate data threshold of $31,500 (section 12) unless the pattern can be expressed on the ETF set, for example as an insider-buying breadth overlay on the US equity ETF.

### Adding strategies

Spec → Red-Team → owner G0 freeze → G1-G5. Specs that originate with an LLM are tagged `llm_origin` and presumed mined from history the model has already seen. Only data from July 2026 onward is clean for them (briefs 13, 22).

---

## 5. Data plan

| Need | Source ($0) | Point-in-time handling |
|---|---|---|
| ETF daily bars | Alpaca Basic: SIP history older than 15 minutes, back to about 2016 (brief 06; 00 item 8) | Raw bars plus a `corporate_actions` table, adjusted as of the decision date (brief 06) |
| 20+ year history and cross-check | Tiingo Starter EOD. Pre-inception proxies UNVERIFIED (brief 20; O14) | Hashed research copy `research/YYYYMMDD/` |
| Collar reference | IEX quote no more than 60 s old, else the agreed prior close (raw) | Logged per order with quote age |
| Cash rate | FRED/ALFRED vintages, attributed in the dashboard footer | Vintages only |
| Filings, Form 4 | EDGAR with a declared User-Agent, at most 10 requests a second | Acceptance time |
| News | Alpaca news, probed at start-up and failing soft (brief 21). **Headline metadata only**, because the Benzinga terms are unread | `created_at`, `updated_at`, own `received_at` |
| Deferred, each with a stated reason | 13F (no consumer on an ETF book, and a 45-day lag per the owner's own document); macro and earnings calendars (no free source researched; would be a note, not a trade); on-chain data and Coinbase/Kraken public feeds (cross-checks, used only when crypto unlocks; 00 section 5); options (not researched) | n/a |

**Two frozen contracts:**
1. The bitemporal Record: `event_time, vendor_published_at, first_seen_at, available_at = max(vendor, first_seen) + lag, ingest_time, source, source_version, quality_flags, replay_id`.
2. The Strategy plug-in. `evidence` is a versioned table with `decision_weight DEFAULT 0`.

**Storage**
- Parquet plus DuckDB, including `archive/text/`.
- `jarvis.sqlite` (trader-owned, WAL, one writer) with these tables:
  - `runs, system_state, intents, orders, activities, cash_events, external_trades, ledger, lots, attribution, approvals, config_changes, vetoes, gate_log, evidence, llm_calls, agent_scores`
  - `watch_items, watch_outcomes, incidents, corporate_actions, g0_registry, holdout_burns`
  - Sleeve tags on `orders`, `lots`, `ledger` and `attribution`.
- `lab.sqlite` (owner-owned, dev tree) with `specs, trials`. It is advisory; the authoritative registry is trader-side (section 8).
- Backups: section 8.

**CI leak tests.** Future-poisoning; shuffled labels must score at chance; a one-extra-bar lag; a feature-target correlation tripwire (v1's 0.999 would trip it); and an alarm at Sharpe > 3 or next-period accuracy > 55-60%. That last band is judgement in both brief 08 (60%) and brief 15 (about 55%), so it is DC.

**Watch universe.**
- The owner's own list: TSLA, plus names the owner supplies. Costs are sized at about 20 names, an *assumption* taken from brief 22's workload.
- Plus about 100 liquid large caps, fixed on the registration date (DC).
- Scoring is forward-only, which avoids survivorship bias. None of these names is traded.

---

## 6. Risk gate, sizing, system states and exits

All values below are (DC) unless a brief is cited. They live in protected `config/risk.yaml`.

**Freeze order**
1. The *rules* (for example "yellow at bootstrap p90, red at p99") are frozen before G1 and counted as trials.
2. The *numeric bands* computed from G1's bootstrap are frozen after G1 and before the G2 count starts.

**Changing a value**
- Tightening applies immediately.
- Loosening needs a Red-Team note (from a Red-Team that has met its catch-rate bar) and owner approval. A **72-hour cool-off then runs from the approval**, and the change starts at the next session.
- Approval requests expire 7 days after issue, and expiry counts as rejection.

| Control | Setting |
|---|---|
| Broker side | `no_shorting=true`, `max_margin_multiplier=1` at Alpaca (brief 21) |
| Per-symbol | No order may take a position above 25% of equity (T-bill ETF exempt). Drift above 25% on an existing holding raises an alert only. Allow-list only |
| Entry order notional | No more than target weight + 5 points of equity; and no more than 2× the intent's modelled notional (erroneous-order family, brief 12) |
| Large trade (owner's v3 idea) | A risk-increasing order above 25% of equity needs an `approvals` row (default; the owner may tighten it). Normal operation never reaches this; it catches errors |
| Deployed cap (L0) | Deployed capital ≤ `deploy_fraction`, which steps 25 → 50 → 75 → 100% at monthly steps (section 7) |
| **Risk-reducing class** | Sells (never more than the broker-reported position) and T-bill buys funded in the same run. Exempt from the per-order caps and the deployed cap |
| Limit price | Buy: min(IEX ask × (1 + 10 bps), collar ceiling). Sell: max(IEX bid × (1 − 10 bps), collar floor). With no fresh quote: agreed prior close × (1 ± 50 bps). Raw prices throughout |
| Collar | ±1.0% against an IEX quote no more than 60 s old, else ±2.0% against the agreed prior close; T-bill ETF ±0.3%. Otherwise skip the order and catch up. **The P0 probe checks T-bill ETF distribution dates**: an ex-dividend drop near the start of the month could approach ±0.3% (general knowledge, UNVERIFIED) |
| Rate | At most 20 orders a run, 40 a day, 5 cancels a minute; a breach means HALT |
| Minimum order / cash buffer | $20 / 2% |
| Typed rejections | 403 self-cross, PDT and intraday-margin rejections are never retried (brief 21; agreement section 32) |
| Wash-sale guard | Across every account the owner registers, including `external_trades` from a manual monthly CSV import: (a) defer a *discretionary* taxable loss sale if the same or a mapped-equivalent ticker was bought in any account in the last 30 days; (b) in an IRA, block buys of a ticker within 30 days after a taxable loss sale of it, holding T-bill instead. The tax sim models both. Brokers report only same-account, same-CUSIP wash sales (brief 19) |
| Tax-lot check | Taxable S0 band sales that would realise a short-term gain within 30 days of turning long-term are deferred. S-A exits are never deferred |
| Loss states | **Day:** whole account down 5% means no risk-increasing orders that day. **Yellow:** live satellite drawdown above bootstrap p90 for the elapsed horizon freezes scale-up and halves `stage_fraction`. **Red:** above p99, **or live-minus-replay tracking error outside its band two months running** (band set at G2 from replay noise; brief 20), sends the satellite back to shadow. **Lifetime stop:** a 25% loss of deployed satellite capital (brief 20's owner lifetime stop) means HALT and S-A retired; re-entry only through a new G0 spec (DC) |

### System states

| State | Orders allowed | Entered on | Cleared by | End-of-run ping |
|---|---|---|---|---|
| **RUN** | All classes, within the gate | Default | n/a | success |
| **SAFE** | Risk-reducing class only: sells, same-run-funded T-bill buys, cancels of JARVIS's own orders, protective re-arm. No risk-increasing order | Unexplained reconcile break; foreign order; unexpected broker constraint; unregistered cash movement; day-loss rule. (A per-symbol trust failure blocks only that symbol and does not enter SAFE) | **Auto-clears after one clean reconcile run** in which the cause is gone, for example a registered cash event or an adopted manual trade (`jarvis adopt <activity_id>`, which needs the approval hash) | `/fail` with the status code |
| **HALT** | None, except `JARVIS-Flatten` run by the owner. Resting protective orders are left in place | Manifest mismatch; rate breach; lifetime stop; `JARVIS-Kill`; HALT flag file present | **Only by the owner**: `JARVIS-Approve` with a `halt-clear` request and the emailed hash; the reason is logged | `/fail` |

The flag file `C:\jarvis-inbox\HALT` is tighten-only: anyone, including an agent, can create it, and only the owner's approval clears HALT. Jobs check for it at start and before every submit.

### Exits

- S-A exits only on the month-end signal.
- **The ETF book has no resting stops.** S0, the alternative the owner would otherwise hold, has none, and the catch-up rule plus the dead-man alert cover a missed month-end. This removes, from phase 1:
  - the GTC re-arm state machine;
  - the stop/sell race;
  - the clash between stops and the self-cross rule;
  - the whole-share problem at $1,000 (briefs 17, 21).
- **Stop lifecycle**, written now for crypto or any later discrete trade:
  1. Size the stop to the filled quantity.
  2. On exit, cancel the stop, wait for a terminal state, then sell the quantity the broker reports.
  3. Re-arm with a new id before the 90-day GTC expiry.
  4. Protective orders form their own class, `PROT`, exempt from the in-house self-cross rule. Use OTO/OCO where Alpaca allows it (briefs 17, 21).

### Kill switch

- `JARVIS-Kill` is a trader-owned scheduled task that the owner user may start. It sets HALT and cancels **non-`PROT` orders only**.
- `JARVIS-Flatten` takes the rotating flatten code from the latest daily email. It closes all positions with `cancel_orders=true` in regular hours, and otherwise queues for 09:45, because out of hours only limit orders are accepted (brief 21).
- Both are reachable from the owner's standard account without switching user. That ability is UNVERIFIED (task ACL) and is a P0 probe; if it fails, the fallback is fast user switching to `jarvis-trader`.
- The Alpaca app or dashboard is the last resort. How its cancel-all treats resting stops is UNVERIFIED, and moot while the book has no stops.
- **No off-host watchdog can cancel orders**, because no read-only or scoped Alpaca key was found. An IP-allowlist field exists but is disabled (brief 23). This is accepted. The mitigation is the Healthchecks alert reaching the phone.

---

## 7. Validation and live-capital gates

**Sequence.**
- Satellite (S-A): G0 → G1 (a, b, c) → G2 (shadow) → GF (drills) → G3 (paper) → **L0 (first live dollars, S0 only)** → G4 (satellite micro-live) → G5 (scale).
- **If S-A is retired at the P2 fork**, the product (S0 or S0(b)) needs only **GF + G3 + L0**.

| Gate | Pass criteria |
|---|---|
| G0 | Frozen spec hash, registered trader-side through `JARVIS-Approve`. Grid of at most 6 cells. Overlays and risk rules registered as trials. N_eff = max(ONC K, Galwey m) over the cumulative registry (brief 20) |
| **G1a Absolute** | *Gating only if the pooled book history is at least 20 years*, measured from the latest inception among the five ETFs or verified proxies (O14). Otherwise it is reported but not gating, and S-A is **capped at `stage_fraction` 25% and labelled "unvalidated, loss-capped"** (DC). Criteria: (1) MinBTL for the registered N_eff, at target SR 0.5, ≤ available years (brief 20: N = 5/10/20 needs about 5.7/9.9/14.5 years). (2) DSR ≥ 0.95 at registered N_eff with a trial-SR sd floor of 0.15. **0.90 only for a pre-registered published design with N_eff ≤ 5** (brief 20; the 0.90 itself is an unsourced DC). The net-SR bar this implies, as a function of N_eff: about **0.55 at N_eff 5 over 30 years, about 0.70 at N_eff 20 over 20 years** (brief 20 verification). Brief 20 says an honest ETF-trend SR of 0.3-0.5 "does not pass", and that is a valid outcome. (3) Plateau: at least 80% of neighbour cells have net SR ≥ 0.6× the chosen cell, and the chosen cell is not the grid maximum (DC). (4) Positive net SR in at least 70% of non-overlapping 5-year windows (DC). (5) With costs doubled, SR stays ≥ 0.75× (DC). (6) Frozen-parameter holdout by asset class: **not applicable to plain Faber**, because no parameter is tuned (it is reported per asset as information). **Required for every Lab spec that tunes anything**: net SR > 0 in at least 70% of held-out assets (DC). (7) Record the block-bootstrap drawdown distribution by horizon |
| **G1b Benchmark** | Lot-level after-tax simulator (short and long term, wash sale, dividend qualification) on the **combined** book for the chosen account layout. Paired block bootstrap on monthly differences. S-A must show: (i) a median after-tax CAGR gap versus S0 of at least −1.0 point **and** a median, across paired bootstrap paths, of maxDD(S-A)/maxDD(S0) of at most 0.7 (DC); (ii) a median after-tax CAGR at least that of S0-RM at equal or lower p90 max drawdown; (iii) **on the pre-declared out-of-sample slice after 2013** (after Faber's 2013 update), an after-tax CAGR no more than 1.0 point below S0-RM's, with max drawdown no worse than S0-RM's (DC). Results are reported as a range and labelled "drawdown-for-return, not alpha". Power: the test cannot be powered (IR about ±0.2; Sharpe-difference SE about 0.14), so the report says the decision rests on dominance and priors |
| G1c | CI leak tests green. DSR, PSR/MinTRL, MinBTL and PBO implemented from the **preprint formulas read in brief 20** (equation and page numbers may differ in print). Unit tests reproduce brief 20's worked values: N = 46 gives DSR 0.9505; the N = 100 example gives SR0 = 0.1132; MinBTL(45) ≈ 5 years. ONC details and Harvey-Liu "Backtesting" are not re-verified. **Null simulation** of the false-pass rate on JARVIS's own data. For any spec that produces probabilities: a reliability curve and Brier score against the code baseline |
| **GF Drills** | Mock Alpaca (`tests/fake_alpaca.py`); its unverified behaviours are marked "assumed" and re-tested at the first live L0 rebalance. Drills: crash between intent and submit; crash between submit and poll; **10:00 run killed with a working DAY order, then the 11:00 retry adopts, cancels and recomputes**; duplicate id on restart; 5xx or timeout; partial fill plus an unfilled DAY order hitting the 15-minute timeout; stale data plus catch-up; **trust failure with both vendors signalling an exit (sell allowed) and with only one (blocked)**; foreign order → SAFE; **unregistered deposit → SAFE, registered → clean**; HALT flag file; `JARVIS-Kill` started from the owner user; restore from backup. On paper: kill switch, dead-man alert reaching the phone, a deliberate missed run |
| G2 Shadow | At least 6 monthly decisions; 100% replay identity; zero unhandled data gaps; **at least 2 position changes**. If 12 decisions pass without 2 changes, an injected-change shadow drill substitutes (DC). The tracking-error band for the red trigger is set here |
| G3 Paper | At least 3 monthly rebalances overlapping shadow; at most one may be a forced rebalance drill (an injected target change, DC). Paper balance = real capital. Order lists equal shadow targets. Zero unexplained breaks against the broker-reconciled ledger. The 3 failure drills of brief 20. Paper P&L is not evidence |
| **L0 First live dollars** | GF + G3 pass. The owner approves, and the live key is issued under DPAPI. **S0 is deployed in tranches**: `deploy_fraction` 25 → 50 → 75 → 100% at monthly decision points (DC; each step ≤ 2×). Undeployed capital is held in the T-bill ETF, which is exempt from the deployed cap. The owner is advised to fund in matching tranches through registered cash events. The first tranche is the micro-live stage. **The G4 fill count starts at the first live S0 fill**, and mock behaviours are re-tested here |
| **G4 Satellite micro-live** | Entry: G1 pass, G2 pass, and L0 active with at least one clean live rebalance. Satellite = 12.5% of capital, with a $200 floor (so 20% at $1,000). Exit (pass): (a) at least 6 months since the **satellite's** first live fill (brief 20's 6-month micro-live duration) **and** at least 20 fills with a fresh reference quote, counted from the first live S0 fill, S0 fills included (tranche buys alone supply about 20). (b) Cost test: fail if the mean realised one-way cost exceeds **1.5× the model** (2 bps a leg, brief 18) by more than one standard error, **or** exceeds 10 bps absolute (DC). The power assumption is a per-fill sd of 10 bps, so n = 20 gives SE 2.2 bps (brief 20); the ratio test is therefore noisy near the 2 bps model, and that is stated. Fills on a fallback reference (quote older than 60 s) are excluded and reported separately. (c) Live drawdown below the bootstrap p95 for the elapsed horizon (brief 20). (d) Zero severity-1 incidents (an unexplained break unresolved for more than one trading day; any order outside the gate reaching the broker; ledger-chain failure; DC). (e) Tracking error within band |
| G5 Scale | `stage_fraction` **25 → 50 → 100%**, which is brief 20's ladder, with at least 6 months per step and no more than 2× per step (12.5 → 25 is 2×). Each step needs the G4 conditions, tracking error within band and zero severity-1 incidents. **Never on live Sharpe** |

**Why G4 starts at 12.5%** rather than brief 20's 5-10%:
- At $1,000-$10,000, 5% of capital ($50-$500) cannot be split across five ETFs above the $20 minimum order at the low end.
- 12.5% keeps the scale-up ladder exactly on brief 20's 25 → 50 → 100 with 2× steps.

**Retirement.** Failing G1a (when it is gating) **or** G1b retires S-A; it is not tuned. A rewrite counts as a new trial in the same family. For Lab specs, a sealed time holdout is burned once per family: the most recent 5 years before the spec's G0 date, held under `jarvis-trader` (DC). The book then runs S0 or S0(b), with JARVIS as monitor.

**ML and LLM-origin specs** enter by the same G0 → G1c → G1a/G1b path. The refit schedule is fixed in the spec, and each refit counts as a trial. A G1c calibration check applies. No separate gate design exists, so the owner's ML and calibration ideas are tested by the same machinery as everything else.

**Sunset rule.** After 24 months of G4/G5, if the all-cost after-tax P&L trails the S0-RM shadow and shows no drawdown benefit, the satellite returns to S0 and LLM spend drops to tier T0. All-cost means LLM spend, data, and a plan *only if* it was bought for JARVIS.

---

## 8. Runtime, hosting, accounts, monitoring and secrets

**Host and process**
- The laptop runs Task Scheduler jobs with WakeToRun, StartWhenAvailable, RestartOnFailure and no AC sleep (brief 23).
- Python 3.12 virtual environment with a hash-pinned lockfile; no Docker (brief 14).
- RAM per run is **not measured**. P0 measures free RAM during a dry run while Claude Code is open.
- **Claude Code blackout** applies only on decision days (the first 5 trading days of the month), from 09:45 to 11:30 ET (08:45-10:30 Texas time), and whenever intents are non-terminal. A pre-run check emails the owner if a Claude Code process is running.

### Three Windows accounts

| Account | Purpose | Notes |
|---|---|---|
| `admin` | Setup only | Owner types this password at UAC prompts; never used for daily work |
| `owner` | Daily use; Claude Code; dev tree | **Standard user, never an administrator.** This prevents a Claude Code session from elevating past the ACLs |
| `jarvis-trader` | Runs every job | Holds the keys and the production data |

**ACL matrix** (R = read, W = write, X = start task, — = no access)

| Object | admin | owner | jarvis-trader |
|---|---|---|---|
| `C:\jarvis-prod` (tagged checkout, `config/risk.yaml`) | setup | — | R |
| `jarvis.sqlite`, archive, sealed holdout, trader-side registry | setup | — | RW |
| DPAPI secrets (Alpaca paper key; live key **from L0 only**; Anthropic production and eval keys) | — | — | RW (user scope) |
| `C:\jarvis-inbox` (requests, HALT flag, Red-Team artifacts) | setup | W | R |
| `C:\jarvis-outbox` (`ledger_ro.sqlite`, digest, Red-Team verdicts, incident drafts, encrypted backup) | setup | R | W |
| `C:\dev\jarvis`, `lab.sqlite`, research copy | — | RW | — |
| Scheduled tasks `JARVIS-Kill`, `-Flatten`, `-Approve`, `-CashEvent`, `-Veto`, `-RedTeam`, `-HoldoutEval`, `-Eval`, `-Deploy` | create | **X** (UNVERIFIED; P0 probe) | owner of each task |

**What the ACLs do and do not guarantee**
- An agent in the owner's session *can* create the HALT flag or start `JARVIS-Kill`. Both only tighten.
- It **cannot approve**, because every approve, flatten, cash-event, adopt and loosening request needs the 6-character hash or code that the trader task sends **only by email**. This holds only if no Claude session can read that inbox: the owner must not connect the approval inbox to Claude Code or any other agent (DC; a stated owner rule, not a technical control).
- Claude Code permission rules on `schtasks` and the inbox are a convenience. They are **not** counted as a control, because they live in the same trust domain as the Builder.
- **Hidden trials cannot be fully prevented on the owner's machine** (brief 20). The mitigations are:
  - the trader-side registry, appended on every `jarvis-lab run`;
  - the `llm_origin` tag;
  - the sealed holdout;
  - G0 registration only through `JARVIS-Approve`.
- The production `ANTHROPIC_API_KEY` is never set in the owner's environment; otherwise attended sessions would silently bill it (brief 22).

**Deploys.** Tag the release; the owner starts `JARVIS-Deploy`, which pulls the tag as `jarvis-trader` and refreshes the manifest; then the config-hash handshake. Never deploy while intents are non-terminal (brief 12).

**Fallback if the P0 probe fails** (DPAPI with "run whether logged on or not", and task ACLs, are both untested; brief 23):
- Move to a US VM (Google e2-micro at $0, or a $4-6 droplet; brief 23) only after Alpaca confirms in writing that a server is acceptable. Its disclosure says algorithms initially run "on your own computer ... and not a server" (brief 21).
- Otherwise use **attended-live mode**. The owner logs in as `jarvis-trader` for the decision-day runs; daily jobs run shadow-only; Healthchecks moves to a monthly schedule, so non-run days do not false-alarm.

**Approvals**
- `approvals` rows are approved through `JARVIS-Approve` with the emailed hash.
- Requests expire 7 days after issue.
- For loosening, the 72-hour cool-off runs from approval.

**Host move.** Use systemd `LoadCredentialEncrypted=` on the VM (brief 23). Cut over in this order: disable the laptop task, rotate the key, enable the VM. The two are never live at the same time.

**Monitoring**
- Healthchecks free tier with a cron schedule and 2-hour grace. It keeps only 100 log entries per check, and `/start` and `/fail` are recalled semantics; both are P0 probes.
- A monthly deliberate-skip silence test.
- The model-retirement tripwire.
- Weekly hashes of fragile vendor pages, which feed Change-Watch.
- **The off-host anchor is a monthly email of the ledger head hash to the owner's second inbox.** Storing the hash in the Healthchecks ping body is UNVERIFIED, and with 100 entries it would last only about 100 runs.
- ntfy carries a status code only, on a random topic name (brief 23).

**Backups.** A nightly encrypted backup goes to the outbox. The owner user copies it to the owner's own cloud drive (an assumption, O-item). The restore drill is part of GF.

**Hygiene and perimeter**
- **First action:** revoke the OpenAI key hard-coded at `jarvis_backend.py` line 597 (a commented line) at the provider; review its usage; make the Hugging Face Space private or delete it.
- Gitleaks pre-commit hook; BitLocker.
- **Legal perimeter** (brief 12, section 2.4): own money only. Five things end that status:
  1. outside money;
  2. pooling;
  3. authority over another person's account;
  4. selling or publishing signals;
  5. showing performance to prospects.

---

## 9. Owner experience

**Mission Plan** (the owner's Goal and Capital Planner and "simple plan"). It is made at onboarding and reviewed each quarter.
- **Inputs:**
  - capital;
  - risk tolerance, as the largest drawdown in dollars the owner would sit through;
  - an optional return goal;
  - time horizon;
  - whether the money may be needed before 59½;
  - IRA eligibility;
  - asset permissions (equities only; crypto is deferred);
  - permission mode.
- **Code computes:**
  - the account layout, from the O3 decision tree;
  - the dial b, so that S0(b)'s bootstrap p95 drawdown in dollars is no more than the stated tolerance;
  - the stage plan and timeline;
  - loss bands in dollars;
  - the G1 range;
  - the probability of reaching the goal, from the bootstrap;
  - fixed-cost drag (LLM tier) as a percentage of capital.
- **The Narrator only explains.** The owner signs through `JARVIS-Approve`.
- **The goal never changes risk** (v1, v3).

**Permission modes** (v2; every change is audited in `config_changes`)
- **RECOMMEND:** JARVIS emails orders; the owner places them by hand; fills are imported and adopted with `jarvis adopt`.
- **PAPER.**
- **ACT-WITHIN-LIMITS:**
  - An unregistered manual trade or cash movement puts JARVIS into SAFE until the owner adopts or registers it.
  - The owner may **veto** an intent (`JARVIS-Veto`), with counterfactual P&L logged in `vetoes`, but may not add one.
  - Deposits, withdrawals and IRA contributions are registered with **`jarvis cash-event`** (needs the hash; it checks the $7,500 yearly IRA cap from brief 19) and never trip SAFE. A registered deposit waits in cash, and is invested at the next decision window (first 5 trading days of the month) by the normal S0/S-A targets.
  - JARVIS does not support discretionary trading in its own account. Trades the owner makes elsewhere in the same ETF tickers go into `external_trades` by a manual monthly CSV import for the wash-sale guard. Whether a second Alpaca account is allowed was not researched.

**Rhythm**
- **Daily (0-1 minute): the deterministic digest. No LLM is involved.** It contains:
  - end state (RUN, SAFE or HALT) with the reason code;
  - counts: bars ingested, filings and headlines archived, watch items raised or scored;
  - orders considered, placed, rejected (with gate reason codes) and vetoed;
  - next decision date;
  - the **expected target-book diff** if month-end were today;
  - per-symbol data-trust status and quote age;
  - LLM spend against the cap and the active tier;
  - the rotating flatten code.
  - The owner acts only on SAFE or HALT, using the runbook and the Incident Analyst's draft.
- **Monthly from month 2: the "shadow JARVIS" email.** What S0, S0-RM and S-A would do and why; top watch items; archive counts; attribution. It doubles as the manual-execution bridge: if the executor is not finished by month 15, RECOMMEND becomes the permanent product.
- **Weekly (about 15 minutes): the Narrator memo.** It covers:
  - NAV against after-tax S0 and S0-RM;
  - **attribution**: market (S0 on all capital), satellite effect, cost, slippage against model, estimated tax, cash drag;
  - rejections with reasons;
  - the "cost of controls" and "cost of overrides" counters;
  - the risk-of-ruin line, as bootstrap P(drawdown above the owner's tolerance within 12 months);
  - the regime labels;
  - ML-lane forecasts with SHAP drivers (weight 0);
  - the **agent report card**;
  - LLM spend;
  - questions for the owner.
- **Weekly from tier T1: the Watchlist Digest** (Reader). For the owner's watch list it lists typed 8-K items and Form 4 buys, each with `event_type`, `materiality`, the integrity flag, the code-built EDGAR link, and a code-escaped excerpt of at most 200 characters (DC). **Excerpts never pass through the Narrator's prompt.** This is the owner's "ranked opportunities and why each matters", delivered without trading.
- **Monthly (optional, about 60 minutes):** a Lab session, `/ask-ledger`, an Idea Lane review.
- **Quarterly:** Mission Plan review.

**Each trade note** carries an **evidence panel whose components are never pooled into one score** (brief 10). This keeps the owner's confidence components apart:
- **Signal:** price distance from the 10-month SMA in %.
- **Data:** trust status and the cross-vendor spread in bps.
- **Execution:** modelled cost in bps, plus realised slippage once live.
- **Risk:** the position's 1-month p5 loss in dollars.
- **Model:** present only for an ML-lane spec, with calibration version and n.

Base rates appear only when n ≥ 100. There is no "Overall confidence", and no bare percentage.

**Dashboard** (Streamlit, owner only) shows:
- NAV, cash, positions by sleeve, realised and unrealised P&L, after-tax against S0/S0-RM;
- risk utilisation against the loss bands, `stage_fraction` and `deploy_fraction`;
- the state ribbon;
- the watch queue;
- the evidence panels;
- data health;
- the agent report card;
- LLM spend by role;
- the gate log;
- pending approvals.

### Worked example: one decision from goal to log (ILLUSTRATIVE market numbers)

**Setup.** $5,000, single taxable account, G4 stage: satellite 12.5% = $625, S0 core $4,375. (The 2% cash buffer, $100, is left out of the table for clarity.)

**Month-end signal.** Four ETFs close above their 10-month SMA. REITs close 2.3% below (illustrative).

**Targets**

| Holding | S0 core | S-A satellite | Combined target |
|---|---|---|---|
| US equity, ex-US, Treasuries, gold/commodities | $875 each | $125 each | $1,000 each |
| REITs | $875 | $0 | $875 |
| T-bill ETF | $0 | $125 | $125 |

**Combine.**
- The satellite held $125 of REITs last month, so the deltas are REIT −$125 and T-bill +$125.
- Core US equity has drifted to $925, which is 21.1% of the core. That is inside the 16-24% band, so there is no trade.
- Every other delta is under $20 and is skipped.

**Trust gate.** Alpaca and Tiingo REIT closes differ by 3 bps: pass.

**Risk gate.**
- The REIT sell is risk-reducing. The T-bill buy is funded in the same run, so it is risk-reducing too.
- Collar: IEX quote 12 s old; sell limit = bid × (1 − 10 bps), inside ±1.0%.
- `gate_log`: PASS/RISK_REDUCING.

**Execution.** Intents are written; the REIT sell fills; the T-bill buy is sized from buying_power and fills. Modelled cost is 2 bps × $250 ≈ $0.05 (brief 18).

**Ledger row.** Sleeve SA; `decision_id`; snapshot hash; reason `SIGNAL_EXIT`; the lot's realised short-term gain and estimated tax.

**Narrator note.** It explains the exit with the evidence panel. Signal: −2.3% from SMA. Data: 3 bps. Execution: 2 bps modelled. Risk: remaining book 1-month p5 −$290 (illustrative).

---

## 10. Idea ledger: one row per owner idea

Verdicts: **KEPT**, **CHANGED**, **DEFERRED** (with its condition), **DROPPED**.

| # | Owner idea (document) | Verdict | What JARVIS does instead, and why (brief) |
|---|---|---|---|
| 1 | Goal: continuously find opportunities in equities and crypto, act only when reward justifies risk, adapt, explain (v1) | CHANGED | Evening watch scan plus a monthly ETF book; crypto deferred. Free data supports daily-to-monthly horizons only (06, 09, 11) |
| 2 | OBSERVE-UNDERSTAND-FORECAST-DECIDE-EXECUTE-LEARN loop (v1) | KEPT | Mapped onto the job steps and the state ribbon (section 2) |
| 3 | Opportunity Scanner: price/volume, relative strength, patterns, news/SEC (v1 A, v3) | KEPT | Watch scan with forward-labelled items, never traded; a promotion path exists (section 4) (06, 16) |
| 4 | Scanner: order-book imbalance, order flow (v1 A, v2) | DROPPED | No equity L2 at any Alpaca tier; order-flow imbalance forecasts only seconds ahead (07, 06) |
| 5 | Scanner: crypto order book and on-chain (v1 A, v2) | DEFERRED | With crypto (section 12) |
| 6 | Shared market state, point-in-time, event vs ingest time (v1 B, v3 step 1) | KEPT | Bitemporal Record contract plus AsOfSnapshot (06, 14, 16) |
| 7 | Regime model, HMM/ML (v1 C, v2, v3) | CHANGED | Rule-based regime label (SMA state × volatility tercile). HMM deferred: default outputs leak (15) |
| 8 | Volatility, GARCH/ML (v1 C, v3) | CHANGED | EWMA; HAR or GJR only if it wins out of sample; sizing and display only (15) |
| 9 | Jump/anomaly model, "continuation is plausible" (v1 C) | CHANGED | The 30% move quarantine in the trust gate plus the watch-scan z-scores. Jump tests detect, they do not forecast (15) |
| 10 | Trend and mean-reversion models (v1 C) | CHANGED | Trend kept (S-A). Mean reversion DEFERRED to a Lab spec; no evidence-grade ETF monthly case (17, 18) |
| 11 | News-impact model, FinBERT tone, social sentiment, event-study CAR (v1, v3) | DROPPED | FinBERT weak for returns; social data is the main pump surface; CAR joined at filing date leaks; 123 rows (16, 15) |
| 12 | Relationship graph (v1 C, page 2) | DROPPED | No brief supports it, and the ETF book has no consumer |
| 13 | Statistical tests (v1 C) | KEPT | The G1 harness (08, 20) |
| 14 | XGBoost/LightGBM outcome models, walk-forward calibration (isotonic/Platt), SHAP (v1 heritage, v3) | CHANGED | **Shadow ML lane**: one LightGBM at weight 0 with purged CV, isotonic calibration and SHAP to the Narrator; only through G0-G1 (15) |
| 15 | Return-distribution, relative-value, reversal/continuation models (v3 ensemble) | DEFERRED | Lab specs one at a time behind baselines; a many-model ensemble is a multiple-testing risk (15, 08) |
| 16 | Strategy Lab: LLM proposes, validation decides (v1 D) | KEPT | Strategy Lab plus registry plus DSR plus Red-Team; low expected yield (01, 02, 08) |
| 17 | Capital Governor: vol targeting, drawdown limits, diversification (v1 E) | KEPT | Vol targeting as a registered overlay (off at launch); loss bands; five asset classes (10, 18, 20) |
| 18 | Fractional Kelly (v1 E) | DROPPED at this size | Needs a few hundred calibrated outcomes first; "never at this size" (10; section 12) |
| 19 | Risk-of-ruin check (v1 E) | KEPT | Bootstrap P(drawdown above tolerance within 12 months) in the weekly memo |
| 20 | LONG/SHORT/FLAT (v1 F, v3) | CHANGED | Long/flat. No crypto shorting at Alpaca; equity shorting needs $2,000 and whole shares (05, 21) |
| 21 | Thesis re-check, confidence-drop exits, trailing/time stops (v1 F, v3 Position Manager) | CHANGED | Pre-registered month-end exits. The confidence-exit rule is untested and noisy (17) |
| 22 | Hard risk gate, no LLM override, kill switch (v1 G, v3) | KEPT | Extended with the erroneous-order family, states table and owner-runnable kill (12, 17) |
| 23 | Execution engine, paper first, then controlled live (v1 H) | KEPT | GF → G3 → L0 → G4 (20) |
| 24 | Memory and audit: versions, snapshot, trace IDs, post-trade review, drift monitoring (v1 I) | KEPT | Hash-chained ledger, `llm_calls`, replay identity; drift = tracking error against replay (13, 20) |
| 25 | P&L attribution (v1 I, v3) | KEPT | Attribution table: market, satellite, cost, slippage, tax, cash |
| 26 | Professional trade log, 17 minimum fields (v1 p2) | KEPT | Mapping table below |
| 27 | Decision rule "upside × probability > loss + costs + risk penalty" (v1) | CHANGED | At strategy level it is **G1b** (benefit against S0/S0-RM after cost and tax). At order level it is the cost gate ($20, band), the tax-lot check and the wash-sale guard. A per-switch probability cannot be estimated for a published monthly rule (10, 11, 19) |
| 28 | "90% confidence is not a guarantee; recalculate" (v1) | KEPT in spirit | Uncombined evidence panel; no bare confidence (10) |
| 29 | Build on current JARVIS, wrap it as the Information layer (v1 p2, v2, v3) | CHANGED | Rebuild with a 2-day salvage audit (`docs/v1_salvage.md`): v1 has a target leak, a committed key and zeroed features (16, 13) |
| 30 | Live crypto feeds; Coinbase as second broker (v1, v3) | DEFERRED / DROPPED | Crypto deferred. A second broker is dropped: about 3-4× Alpaca's fees, and splitting volume keeps both in the worst tier (11). Public feeds are kept as future cross-checks |
| 31 | Equity trades, quotes, L2 (v1, v2) | DROPPED | IEX-only on the free tier; SIP costs $99/month (06) |
| 32 | Options later (v1) | DEFERRED | Not researched; Alpaca IRAs allow options, but no strategy needs them (21) |
| 33 | Macro real-time/vintage data (v1, v3) | KEPT in part | FRED/ALFRED vintages for the cash rate. A macro/earnings event calendar is DEFERRED until a free source is confirmed; it would raise a note only (06) |
| 34 | Form 4 insider signal as a slow overlay (v1) | CHANGED | Watch-only and forward-scored, with a promotion path; single-name trading is unreachable below $31,500 unless expressed on the ETF set (09, 16) |
| 35 | 13F long-horizon positioning (v1) | DEFERRED | No consumer on an ETF book; 45-day lag per the owner's own document |
| 36 | Point-in-time feature store (Feast), model registry (MLflow), traces (v1, v3) | CHANGED | As-of joins in DuckDB; `models.yaml` plus spec registry; ledger traces. Feast would not have caught v1's leak (14) |
| 37 | BTC $100 worked example, "+$0.27 after costs", 72% confidence (v1) | DROPPED | Costs are 33-113% of the upside; 72% implies absurd Kelly (09, 10, 11). Replaced by the $5,000 example (section 9) |
| 38 | Never manufacture trades; FLAT is valid; never chase a target (v1, v2, v3) | KEPT | The goal is displayed as a range and never changes risk (09, 11) |
| 39 | Agent teams: Plan & Discover, Understand, Challenge & Protect, Act & Learn (v2) | CHANGED | 8 Claude roles off the order path plus code and statistics (section 3) (02, 03) |
| 40 | User sets capital, risk tolerance, optional goal, horizon, permissions, mode (v2) | KEPT | Mission Plan inputs; tolerance sets the dial b |
| 41 | "A simple plan" the user receives; Goal Planner rejects unrealistic targets (v2, v3) | KEPT | Mission Plan, with code numbers and the Narrator explaining |
| 42 | Strategy Selector (v2) | DEFERRED | Until at least two strategies are live; a selector over one strategy is a forking path (08) |
| 43 | Data Steward / Data Trust agent, quorum (v2, v3) | KEPT as code | Two-vendor per-symbol gate plus Data-Trust Triage by the Incident Analyst (12, 14) |
| 44 | Market/Microstructure, Flow agent (v2, v3) | CHANGED | Cost monitor (step 15) feeding G4 (07) |
| 45 | Crypto/On-chain agent (v2, v3) | DEFERRED | With crypto |
| 46 | Fundamental/Macro agent (v3) | DEFERRED | No strategy consumer; brief 09 is thin on it |
| 47 | Statistical and ML forecasters (v2) | CHANGED | Shadow ML lane plus a volatility estimate |
| 48 | Bull/Bear researchers (v2, v3) | CHANGED | Artifact Red-Team with a catch-rate bar; same-model debate is the weakest configuration (02) |
| 49 | Manipulation surveillance: spoofing, layering, wash trades, momentum ignition (v2, v3) | DROPPED as written | Needs participant-attributed data the public cannot access (07) |
| 50 | Manipulation: pump and venue-divergence red flags, "never claims a crime" (v2, v3) | KEPT | Integrity flag on watch items; cross-vendor divergence = trust gate (07) |
| 51 | Portfolio/Risk agent, Capital Governor agent (v2, v3) | KEPT as code | Risk gate (12) |
| 52 | Execution agent, idempotent order service (v2, v3) | KEPT as code | Deterministic ids, lookup before submit, adopt-on-start (17, 21, 23) |
| 53 | Position monitor (v2) | KEPT as code | Reconcile, protection check, catch-up rule |
| 54 | Auditor/Learning agent; post-trade lesson; "what was right/wrong; needs review?" (v2) | CHANGED | Code attribution plus the Narrator's typed note plus an owner comment field; review flags from the loss bands and tracking error |
| 55 | LEARN; "adapts when the market changes" (v1) | CHANGED | **Adaptation = the monthly attended Lab plus pre-registered refits, each counted as a trial. No online learning, by design**: iterated out-of-sample is not out of sample (08, 20) |
| 56 | Confidence Calibrator: Signal/Data/Model/Thesis/Execution → calibrated Overall (v3) | CHANGED | Separate components, never pooled (a pooled score cannot be calibrated, per Ranjan-Gneiting). "Thesis" (LLM confidence) dropped (10, 01) |
| 57 | Named states OBSERVE/INVESTIGATE/VALIDATE/READY/EXECUTE/MANAGE/SAFE-LEARN (v3) | KEPT as display | State ribbon over job steps; SAFE/HALT system states defined (section 6) |
| 58 | Orchestrator on LangGraph (v3) | DROPPED | A code state machine plus SQLite intents and approvals gives checkpoints and human approval. An LLM supervisor adds 3-15× tokens and 41-87% failure modes (02, 03, 14) |
| 59 | Human approval for exceptions: large trade, new strategy, paper→live (v3) | KEPT | Large-trade threshold, G0 freeze, L0 approval |
| 60 | Human approval for a degraded-data override (v3) | DROPPED | An override on a hard control (12; 00) |
| 61 | Compounding from realised equity, capped by risk budgets (v3) | KEPT | `stage_fraction × marked equity`, G5 steps (20) |
| 62 | Local stack: Docker Compose, Redis/NATS, Postgres+Timescale, MinIO, Grafana, React (v3) | DROPPED | SQLite WAL, Parquet, Task Scheduler, Streamlit; 8 GB RAM; MinIO archived (14) |
| 63 | Build order, 10 steps (v3) | CHANGED | Data contracts first (kept); agents after paper of the non-LLM pipeline (02); section 11 |
| 64 | Dashboard panels: NAV, cash, positions, P&L, risk use, opportunity queue, confidence, strategy, model and data health (v3) | KEPT | Section 9 list; "overall confidence" replaced by evidence panels |
| 65 | Trade email: asset, side, fill, size, range, downside, reasons, risk approval, exit logic, ledger link (v3) | KEPT | Trade note with evidence panel and ledger link; long/flat only |
| 66 | Daily summary: scanned, rejected and why, taken, attribution, calibration changes, plan for next session (v3) | KEPT | Deterministic daily digest plus weekly attribution; "plan" = expected target-book diff |
| 67 | Investor view, hosted read-only UI (v3) | CHANGED | Owner-only, inside the legal perimeter and data licences (12, 21) |
| 68 | Query broker rules instead of assuming them (v3) | KEPT | Broker-constraints adapter plus Change-Watch (05, 21) |
| 69 | Permission modes: recommend / paper / act within limits (v2) | KEPT | Plus `cash-event`, `adopt`, `veto` (12) |
| 70 | RL as a later sandboxed layer (v2) | DROPPED | Removed until a profitable supervised system and a validated simulator exist (15) |
| 71 | Multi-horizon, intraday to long-term (v1, v3) | CHANGED | Monthly only; intraday is fee-negative and data-limited (06, 09, 11) |
| 72 | LangAlpha caveat (v3) | KEPT | Verified accurate (01) |

**Trade-log mapping** (v1's 17 fields)

| v1 field | JARVIS column |
|---|---|
| Trade ID | `intents.client_order_id` + `ledger.seq` |
| Asset | `orders.symbol` |
| Horizon | `spec.horizon` (monthly) |
| Event time | `intents.decision_time`, `orders.submitted_at`, `activities.filled_at` |
| Market-state snapshot | AsOfSnapshot hash plus stored snapshot |
| Strategy + version | `intents.strategy_id`, `spec_hash` |
| Features | Snapshot rows (close, SMA, distance, volatility) |
| Model probabilities + calibration | `evidence.prob`, `calibration_version` (ML lane only; null for rule strategies) |
| Expected return/risk | Spec bootstrap range plus 1-month p5 dollar loss |
| Position size | `intents.qty/notional`, `sleeve` |
| Risk checks | `gate_log` reason codes |
| Order/fill/slippage | `orders`, `activities`, `slippage_bps` against the arrival quote |
| Confidence changes | Evidence-panel values per run |
| Exit reason | `intents.reason_code` (SIGNAL_EXIT, BAND, CATCHUP, KILL, FLATTEN, VETO) |
| P&L | `lots` realised P&L plus after-tax estimate |
| Attribution | `attribution` table |
| Post-trade lesson | Narrator typed note plus `owner_comment` |

---

## 11. Build order

Effort is from critic solo's per-component estimates, plus the additions in this revision. Dev-days are about 6 hours. **Calendar assumes 2.5 dev-days a week (15 hours); O2 is unknown.**

| Phase | Work | Dev-days | Cumulative | Calendar (ESTIMATE) | Exit |
|---|---|---|---|---|---|
| P0 | Revoke v1 key; three Windows accounts; **probes**: DPAPI under "run whether logged on or not" and Modern Standby across 3 reboots; owner-user `schtasks /run` on trader tasks; free RAM during a dry run; Healthchecks `/start`, `/fail` and ping body; Alpaca duplicate id, activities endpoint and transfer type codes, lot method, `no_shorting` and multiplier config; T-bill ETF distribution dates. Account decision tree (O3) constrained to one account type or disjoint tickers. Capped `jarvis` and `jarvis-eval` workspaces; check the minimum prepaid purchase | 6-10 | 6-10 | Weeks 1-4 | Probe sheet closed |
| P1a | **Thin end-to-end slice**: Alpaca and Tiingo EOD for the 6 ETFs; S0/S-A/S0-RM shadow targets; templated email; **Narrator memo from shadow numbers** (first Claude agent in the loop) | about 12 | 18-22 | About month 2 | First shadow email and memo; **G2 calendar starts** |
| P1b | Bitemporal ingest, trust gate, archive, watch scan, integrity flag, CI leak tests, v1 audit, pre-tax shadow NAV | 18-28 | 36-50 | Months 4-5 | 20 clean runs |
| P2 | **Day 1: ETF inception inventory and the pre-committed G1a rule.** Lot-level tax sim (combined book); G1a/b/c; formula unit tests and null simulation; overlay ablation; harness, trader-side registry, `JARVIS-HoldoutEval` | 25-32 | 61-82 | Months 6-8 | **Verdict and fork**: if S-A fails, the product is S0/S0(b) plus monitoring, and P3 automates S0 or RECOMMEND continues (owner decides, O18). The after-tax shadow column is added |
| P3 | **First 5 dev-days are brief 04's spike**: order service plus mock broker skeleton plus the crash drills; if those cannot pass inside that box, re-open the adopt option (04). Then: gate, states, adopt-on-start, activities reconciliation, cash events, kill/flatten/approve tasks and ACLs, GF, tax lots, mutation testing | 43-53 | 104-135 | Months 10-13 | GF passes |
| P4 | G3 paper; Incident Analyst (tools, Data-Trust Triage); Change-Watch; Red-Team seeded evaluation; `/ask-ledger`; Streamlit; agent report card; Mission Plan | 18-27 (synthesis 15-22, plus 3-5 for the added agent tools, Change-Watch, report card and Mission Plan) | 122-162 | Months 11-15 | G2 and G3 pass |
| P5 | **L0** (S0 tranches) → G4; Reader A0 plus Watchlist Digest (at tier T1) | 12-20 | 134-182 | Months 12-22 | G4 |
| P6 | G5; Shadow ML lane (Lab sessions, any time after P2's harness); Reader A1 if the power check passes; crypto conditions | — | — | Month 19 onward | Per gate |

**Key dates** (ESTIMATE):
- Paper-ready (P0-P3): about 104-135 dev-days.
- L0: about month 12-15. G3 needs three paper rebalances after P3, of which at most one may be a forced drill, so about two months of month-ends.
- G4 start (satellite's first live fill): about month 13-16.
- G4 exit and the 25% step: about month 19-22.
- 50%: about month 25-28.
- **Satellite at 100%: about month 31-34 at the earliest.**

**Project kill criterion.** If P3 is not done by **month 15**, JARVIS stays in RECOMMEND mode. Month 15 sits two months past the upper estimate, so it does not trip on the estimate itself.

---

## 12. Growth path

**Rules**
- Any recurring cost C needs capital of at least 600 × C (brief 11).
- LLM spend follows the 1% cap and the tiers in section 3.

| Unlock | Trigger | Honest outlook |
|---|---|---|
| S-A in an IRA | Eligible; IRA fee no more than 0.25% a year of the balance (DC); money not needed before 59½; $7,500 a year contribution limit (brief 19); one account type, or disjoint tickers; G3/L0/G4 re-run for the new account | Reachable if eligible |
| Reader Watchlist Digest (T1) | Capital ≥ $2,000 (cap formula, ESTIMATE) | Reachable; owner-visible value |
| Nightly Narrator (T2) | Capital ≥ $2,500 (cap formula, ESTIMATE) | Reachable; low value |
| Reader A1 | A0 passed; at least 100 positive outcomes within 9 months (O16) | Likely unreachable |
| Strategy Selector | At least two strategies live | Distant |
| Crypto via spot BTC/ETH ETFs (Donchian ensemble) | Route and expense ratio verified (O6); S-A at G4; incremental with/without test; 10% cap; labelled "unvalidated, loss-capped" | Possible. In a taxable account the hurdle is about **2.5-2.9 points** of tax for a BTC-like 15% gross return (brief 19, cases B-C) plus a few bps of ETF cost; about 0 in an IRA if the ETFs are held there. **The Donchian evidence is one non-peer-reviewed working paper whose net results use only 10 bps costs** (brief 18) |
| Alpaca spot crypto | **Texas was absent from the last list seen** (28 jurisdictions, October 2025, search snippet, unconfirmed; brief 21); check at signup; VM confirmed in writing; ETF route unavailable; a 30% gap costs no more than 3% of equity | Doubtful |
| VM host | $4-6 a month needs $2,400-$3,600 (600×); Google e2-micro is $0 (brief 23) | Reachable if needed |
| Claude plan bought for JARVIS | $20 a month needs $12,000 (600×) | Not justified by trading; only as a build tool (O1) |
| Norgate single stocks ($52.50/month) | Capital of at least $31,500 | Never within $10,000 |
| SIP, intraday, shorting, Kelly | $59,400 or more; at least 300 outcomes | Never at this size |

---

## 13. Three biggest risks

1. **No edge, and the owner feels misled.**
   - *Signal:* G1a or G1b fails; the owner disengages; manual trades appear.
   - *Response:* this outcome is planned and stated in section 1, along with the timeline. S0/S0(b) runs live through L0. The agents' work stays visible through the Watchlist Digest, the report card, incident triage and the Lab. The Idea Lane has a written promotion path.
2. **Solo overload leads to bypassed gates.**
   - *Signal:* P3 not done by month 15; overrides in the approval log; vetoes clustering after losses.
   - *Response:* RECOMMEND becomes permanent. The 72-hour cool-off from approval, the SAFE-on-unregistered-activity rule and the emailed-hash approvals all hold.
3. **Security and liveness rest on untested Windows behaviour.** This covers DPAPI under Task Scheduler, task ACLs for a standard user, and Modern Standby.
   - *Signal:* a P0 probe fails, or more than 2 runs are missed in a month.
   - *Response:* attended-live mode on a monthly Healthchecks schedule, or a VM after written Alpaca confirmation.

---

## 14. Decision record

| # | Decision | Options (backers) | Critic / red-team findings | Choice and reason |
|---|---|---|---|---|
| D1 | Base | A-E | A and C quant-fatal; B fidelity 3.5; E overbuild | **D**: wins on the money-loss lenses; gaps grafted and now repaired |
| D2 | Claude's role | Reporting only (B); quant team (C); evidence slots (E) | B under-delivers; C's 9 agents include theatre; E's A3 lets text raise size; red team: the census was over-sold | **8 roles: 3 attended agentic, 1 unattended tool-using agent, 4 workflow steps.** The evidence gives no support for LLM selection or sizing and shows run-to-run instability (01). No A3 |
| D3 | S-A spec | Overlaid rule (all) | Overlays untested; 0.90 relaxation misused | **Plain Faber**; overlays registered as trials |
| D4 | G1 null and which gate decides | DSR vs 0 (A, C, E); report only (D); numeric gate (B) | Buy-and-hold passes DSR; no risk-matched null; red team: pass/fail undefined | **G1a (gating if ≥ 20 years) plus G1b against S0 and S0-RM; failing either retires S-A** |
| D5 | Account layout | Later (A, C, E); P0 (B, D) | Largest lever; cross-account wash sale (Rev. Rul. 2008-5) | **P0 tree; one account type or disjoint tickers; combined-book tax sim** |
| D6 | Idle capital | Unstated | Opportunity cost is the largest cost | **Core-satellite with sleeve tags** |
| D7 | ETF stops | Whole-share GTC (B, D); fractional unprotected (A, C, E) | Whole shares infeasible at $1,000; stop races | **No ETF stops**; catch-up plus dead-man |
| D8 | Kill | Cancel all | Strips protection; red team: owner cannot reach trader keys | **Cancel non-PROT through an owner-startable trader task; flatten with an emailed code; HALT flag file** |
| D9 | Crypto | Launch 10% (A); conditional (B, C, E); after G4 plus host move (D) | Taxable hurdle; TX absent from the last list | **D's sequencing, B's ETF route, incremental test** |
| D10 | Text | Nightly extraction (A, C, D, E); deferred (B) | No ETF consumer; Haiku retiring | **Archive from P1; Reader feeds the owner's Watchlist Digest from T1; A2 deleted** |
| D11 | Scanner | Dropped (B-E); watch items (A) | Dead-end lane | **Forward-labelled watch items plus a written promotion path** |
| D12 | Overrides | Forced (D); none | Fidelity wants options | **Permission modes; `cash-event`/`adopt`/`veto`; cool-off from approval** |
| D13 | Keys and isolation | Same user (A, B, D, E); separate user (C) | Red team: two users contradict the Lab, kill and approve workflows; admin can bypass | **Three accounts; owner is a standard user; inbox/outbox; trader tasks; ACL matrix** |
| D14 | LLM cap | Flat $5-15; 2% scaled (D) | A flat cap is 6-18% a year at $1,000; red team: the cap could not carry the roster | **1% scaled cap, per-role budgets, $0.35 incident reserve, capital tiers T0-T2 ($840 / $2,000 / $2,500), separate validation budget** |
| D15 | Build order | Executor first (D); G1 first | Agent loop visible too late | **Thin slice with a Narrator in P1a; verdict P2; executor P3 (P3 starts as brief 04's spike)** |
| D16 | Live ladder | 6 months / 20 fills / 1.5× | Circular S0-live definition; 20 → 50 broke the 2× rule | **L0 S0 tranches (25/50/75/100) → G4 at 12.5% (floor $200) → G5 25/50/100; ratio plus absolute cost test** |
| D17 | Model | Pin Haiku 4.5 | Retirement floor 2026-10-15 | **Model ID in config; Sonnet-class basis; per-role sync/batch mode; tripwire** |
| D18 | System states | Implicit | Red team: SAFE/HALT undefined | **RUN/SAFE/HALT table; SAFE auto-clears; HALT is owner-only; /fail ping** |
| D19 | Retry idempotency | Intents die with the run | Retry collides with its own working order | **Stable `decision_id`; persisted intent states; adopt, cancel, then recompute; 15-minute poll timeout** |
| D20 | Trust gate and exits | Block entry and exit | Contradicts "never block an exit" | **Block risk-increasing only; sells allowed when both vendors' series signal the exit; no manual override** |
| D21 | Owner's ideas | Partial mapping | About 17 of about 40 ideas mapped | **72-row idea ledger plus trade-log mapping** |

---

## 15. Open items only a test or the owner can settle

| # | Item | How to settle |
|---|---|---|
| O1 | **Does the owner already have a Claude plan?** Without one, Builder, Lab and `/ask-ledger` API costs are **unpriced**. Brief 22 prices only a weekly research session: $12.8/month on Sonnet, $21.3 on Opus, $41.6 heavy. Extrapolating its $2.96 central session unit to one session per dev-day over P0-P5 (about 134-182 dev-days, section 11) gives about $400-540 for the build (ESTIMATE; the one-session-per-dev-day assumption is mine, and build sessions may be heavier than brief 22's central session), against a Pro plan at about $20/month over a 15-22 month build, about $300-440. Whether Pro limits cover that usage was not researched | **Ask before P1.** If there is no plan, compare those two. Without a plan, the Ledger Analyst runs as a capped API Q&A script and the Lab is off at tier T0 unless funded from the validation budget |
| O2 | Weekly hours | Ask; re-plan section 11 |
| O3 | IRA eligibility, earned income, $7,500 cap, liquidity before 59½, Equity Trust fee, paper IRA; one account type or two | Owner, plus a written Alpaca reply, in P0 |
| O4 | Texas has no state income tax (general knowledge); brief 19's questions; Alpaca lot method and 1099; "substantially identical" for different-issuer ETFs | One paid consult before L0 |
| O5 | **Terms.** (a) The Consumer Terms clause barring reliance on the Services to buy or sell securities applies to plan-run Lab work. The wording is confirmed; the section number "3(9)" is unconfirmed (brief 22). (b) The Commercial Terms say "not for consumer use", so a personal API account is a gray area | Lawyer question. Default: no LLM output reaches orders without an owner G0 freeze |
| O6 | Spot BTC/ETH ETF route and cost; Alpaca crypto in Texas | Written Alpaca reply; fund documents |
| O7 | VM versus the "own computer" disclosure | Ask Alpaca in writing |
| O8 | Duplicate `client_order_id`; activities endpoint and transfer type codes; whether paper enforces the $2,000, 1× and crypto-state rules | `probes/*.py` in P0 |
| O9 | IEX quote freshness for the chosen ETFs | Log quote age over 20 sessions |
| O10 | Tiingo vs Alpaca EOD availability by 10:00 ET | Log over 20 sessions |
| O11 | Same-day reuse of sale proceeds below $2,000; fractional dust | Paper, then the first L0 rebalance |
| O12 | DPAPI under `jarvis-trader` with "run whether logged on or not"; Modern Standby wake; **standard-user start rights on trader tasks** | P0 probe across 3 reboots |
| O13 | News on the Basic plan; Benzinga terms | Start-up probe; read the terms before storing more than metadata |
| O14 | ETF inception dates and pre-inception proxies (is G1a gating?) | P2 day 1 inventory; the rule is pre-committed in section 7 |
| O15 | Formulas are implemented from the brief 20 preprints. **What remains is the null simulation**, plus ONC and Harvey-Liu "Backtesting", which are unchecked | P2 |
| O16 | Watch-universe *positive* rate (A1 power) | Count over the first 60 days; if 100 positives would take more than 9 months, declare A1 unreachable |
| O17 | Hugging Face Space visibility; v1 key usage | Owner checks the provider dashboard |
| O18 | Automate S0 if S-A fails G1? | Owner decides at the P2 fork |
| O19 | **Minimum prepaid API purchase and evaluation-tier limits** (UNVERIFIED, brief 22). A minimum purchase could equal many months of the $0.83 cap at $1,000 | Check in P0 before funding |
| O20 | Healthchecks ping-body storage; `/start` and `/fail` semantics | P0 probe; the monthly email anchor is used regardless |
| O21 | The owner's watch list (names beyond TSLA) and about 3-4 hours of hand-labelling for the Reader golden set | Owner, before P5 |
| O22 | The owner's second inbox (hash anchor) and cloud drive (backup target) | Owner, in P0 |
| O23 | RAM headroom with Claude Code open during a run | P0 measurement; the blackout rule may be relaxed if headroom is ample |

---

## 16. Red-team log

### Must-fix items

| # | Source | Must-fix item | Resolution |
|---|---|---|---|
| 1 | Evidence | Section 1 headline arithmetic inconsistent (−0.7 from an invented 0.65 hurdle; dollars did not match the range) | **Fixed.** Inputs and arithmetic are stated once (D = E − C − H). Planning hurdle 1.0-1.3 (brief 19) gives a taxable central of −1.1 to −1.4 and a range of −2.4 to 0.0. Brief 18's 0-0.9 is shown as a sensitivity (central about −0.5). IRA −0.1. Dollars are given for the whole account and for the satellite, with the formula. The block is labelled ESTIMATE (section 1) |
| 2 | Evidence | "No LLM trader has beaten buy-and-hold" and "evidence rules Claude out" overstate brief 01 | **Fixed.** Reworded to "no study shows ... over a multi-year, multi-symbol, post-cutoff sample", noting the short forward tests and that the evidence gives no support and shows instability (CLQT, AlphaForgeBench). Sections 1 and 3, D2 |
| 3 | Evidence | G5 20 → 50 breaks brief 20's 2× limit | **Fixed.** G4 = 12.5% (floor $200), then G5 = 25 → 50 → 100, all steps ≤ 2×. The deviation from brief 20's 5-10% G4 is stated with its reason (section 7). L0's S0 tranches 25/50/75/100 are also ≤ 2× |
| 4 | Buildability | S0 "always live" vs live key from G4: circular | **Fixed.** New gate **L0**: GF + G3, then the live key and S0 in monthly tranches. The first tranche is micro-live, and the G4 fill count starts at the first live S0 fill. The fork product uses GF + G3 + L0 only (section 7) |
| 5 | Buildability | 10:00/11:00 retry contradicts intent and SAFE rules; unstable `decision_id`; no poll timeout | **Fixed.** `decision_id = hash(strategy_version, decision_date, snapshot_hash)`; persisted intent states; adopt, cancel and await terminal at the start of every run; 15-minute poll timeout; a GF drill for a killed 10:00 run (sections 2 and 7) |
| 6 | Buildability | Deposits and withdrawals trip SAFE; no contribution flow | **Fixed.** `cash_events` and `jarvis cash-event` (hash-approved; checks the IRA cap); transfers matched in reconcile; unregistered transfers mean SAFE; GF drill. Activity type codes are UNVERIFIED and probed in P0 (sections 2, 8, 9) |
| 7 | Buildability | SAFE/HALT semantics undefined | **Fixed.** States table: allowed order classes, entry, clearing, ping. SAFE allows risk-reducing orders and auto-clears after a clean reconcile. HALT is cleared only by the owner. `/fail` on any non-RUN end (section 6) |
| 8 | Buildability | Two-user ACL model contradicts the Lab, kill and approve workflows; admin bypass | **Fixed.** Three accounts with the owner as a standard user. `lab.sqlite` and the research copy are in the dev tree; the sealed holdout is under the trader and evaluated by a trader task. Kill, flatten, approve, cash-event, veto and Red-Team are owner-startable trader tasks with an inbox/outbox; HALT flag is tighten-only; full ACL matrix. The deny hook is no longer claimed as a control (section 8). Task ACL behaviour is UNVERIFIED and probed in P0 |
| 9 | Buildability | G1a/G1b cannot pass or fail cleanly; holdout undefined; post-2013 limbo; DD statistic undefined | **Fixed.** Day-1 inventory with the rule pre-committed: G1a gates only with ≥ 20 years, otherwise S-A is capped at 25% (red team suggested 20%; 25% matches the G5 ladder). Failing G1a or G1b retires S-A. Holdout: not applicable to plain Faber (nothing tuned); defined for Lab specs. Post-2013 slice is pass criterion (iii). DD is the median paired-bootstrap ratio (section 7) |
| 10 | Buildability | Sleeves undefined in the live book; band and cap conflict; S0 vs T-bill ambiguous | **Fixed.** Sleeve tags on orders, lots, ledger and attribution; sleeve NAV; XFER netting. S0 = 5 risk ETFs at 20%, no T-bill. Band is relative ±20% (24% ceiling, below the 25% cap). Cap drift is alert-only. Combined-book tax sim. Lot method logged in P0 (sections 4 and 6) |
| 11 | Owner/agents | Owner ideas vanish without a row | **Fixed.** A 72-row idea ledger (one row per idea, each with a verdict, reason and brief) plus a 17-field trade-log mapping. Added: Shadow ML lane, regime label, risk-of-ruin line, Mission Plan, attribution, large-trade threshold, integrity flag, cost monitor, digest and dashboard fields, state ribbon, LangGraph rationale, adaptation statement (sections 2, 4, 9, 10) |
| 12 | Owner/agents | Agent census over-sold; production roles thin | **Fixed.** Honest census (3 attended agentic, 1 unattended agent, 4 workflow steps). The Incident Analyst is now a tool-using agent with Data-Trust Triage. Change-Watch Analyst added. Agent report card. The money route is stated (Lab → harness → Red-Team → G0 → G1-G5) (section 3) |
| 13 | Owner/agents | The $0.83 cap cannot carry the roster; no priority; plan cost ignored | **Fixed.** Per-role budget table with priorities, a $0.35 incident reserve (the red team suggested 40% of the cap; see the disagreements), capital tiers T0/T1/T2 derived from the cap formula, cap-exhausted fallbacks, a separate validation budget, and explicit plan treatment (sunk vs bought) (section 3) |
| 14 | Owner/agents | Reader has no consumer; A2 has no target | **Fixed.** The Reader feeds the weekly Watchlist Digest. Typed fields only reach the Narrator; excerpts are code-escaped and never in a prompt. A2 is deleted (A2′ is a caution line only). A1 is powered on positives. Enabled at T1 (section 3) |
| 15 | Owner/agents | Safety boundaries asserted, not mechanical (holdout seal, Red-Team identity, self-graded tests, plan fallback) | **Fixed.** Holdout under the trader with a metrics-only task and `holdout_burns`. Red-Team runs as the trader task on the production key with its own budget. Mutation testing (≥ 95%, DC) on `jarvis/gate/`. Plan-less fallback in O1. The limit on hidden trials is stated honestly (sections 3 and 8) |
| 16 | Owner/agents | Idea Lane is a dead end | **Fixed.** Written promotion path (deflated forward evidence → Lab spec → Red-Team → G0 → shadow → G1-G5), with the single-name limit pre-registered (Norgate $31,500; ETF-expressible only) (section 4) |

### Should-fix items

**Applied:**
- drawdown benefit marked "expected, unverified", with its grade;
- O15 corrected (formulas read from preprints; only the null simulation remains);
- G1a restored to brief 20: N_eff ≤ 5 relaxation, SR bar as a function of N_eff, windows test, cost-doubling test and holdout, all thresholds tagged DC; "3 bear episodes" dropped as unsourced;
- G4 ratio-plus-absolute cost test with its sd assumption, and fallback-reference fills excluded;
- Narrator and Reader thresholds recomputed on one basis;
- O1 marked unpriced, with an extrapolation;
- O5 and O19 added for API eligibility and the prepaid minimum;
- Healthchecks anchor marked UNVERIFIED and replaced by a monthly email;
- A0 hand-labelling budgeted;
- crypto ETF hurdle recomputed (2.5-2.9 plus bps) with the single-paper caveat;
- Texas wording corrected;
- cross-account wash-sale guard;
- "owner's 20 names" made an assumption;
- unsupported claims reworded or marked (scoped keys, Alpaca app cancel-all, confirmation inbox removed, activities endpoint, 0.5 GB removed, ntfy content-free);
- DC tags added, the brief 06 citation fixed, the tracking-error red trigger restored, P3 treated as brief 04's spike;
- P1 pre-tax shadow NAV;
- rules vs numeric bands freeze order;
- mock behaviours marked "assumed";
- A1 powered on positives, with a baseline;
- Red-Team catch-rate bar;
- Reader submit/collect jobs;
- G2/G3 stall rules;
- pessimism kept in shadow only;
- timeline re-derived, kill criterion moved to month 15;
- attended-live on a monthly schedule;
- backup target;
- discretionary account handled by CSV import;
- per-symbol trust gate with an end rule;
- limit price formula;
- the undefined "10-minute rule" deleted;
- "reached" defined;
- approval window fixed;
- blackout limited to decision days;
- one-account constraint;
- digest and evidence panel;
- worked example;
- sync vs batch per role;
- calibration check in G1c;
- `cash-event` command;
- timeline in the thesis;
- thin Narrator slice in P1a.

**Not applied as suggested** (see the disagreements below):
- the "owner-approved manual confirmation" path for trust-gate exits;
- the 40% incident reserve;
- the 20% short-history cap;
- the per-switch "expected benefit" form of the cost gate.

### Final-pass self-audit (corrections made after re-checking this document against the briefs)

- **Incident reserve arithmetic.** An earlier draft priced one 8-turn incident at $0.27 by omitting brief 22's ×1.3 tokenizer factor on input. Corrected to about $0.33, with the reserve set at $0.35. This moves T0 to $0.70 (capital ≥ $840), T1 to $1.50 (≥ $1,800, still set at $2,000) and T2 to $2.02 (≥ $2,424, set at $2,500). The section 1 fixed-cost line changes to about 0.84% a year at $1,000.
- **G4 clock.** The 6-month micro-live duration now runs from the satellite's first live fill, as brief 20 intends. The 20-fill count still starts at the first live S0 fill. Dates in sections 1 and 11 move by one month (full size about month 31-34).
- **Validation budget.** Filing-sized golden items cost about 4× headline items (brief 22 token sizes), so the per-model-change estimate is $2-6, not $2.
- **P4/P5 effort.** P4 is raised by 3-5 dev-days for the added agent work. P5 is restored to the synthesis figure (12-20) because an earlier draft had cut it without a reason.
- **Approval channel.** The emailed-hash control holds only if no agent can read the approval inbox. This is now stated as an owner rule.
- **Undeployed L0 capital** sits in the T-bill ETF. **Registered deposits** are invested at the next decision window.

### Disagreements with the red team (kept, with reasons)

1. **Trust-gate exits.** The red team proposed allowing sells on a trust failure "when broker quote and collar agree, or with an owner-approved manual confirmation." Accepted: sells are allowed. Not accepted: the manual-confirmation path, because it is an override on a hard control, which 00 and brief 12 say to remove. Not accepted: the quote-and-collar condition, because it checks the price level, not the *signal*. Instead, a sell is allowed when both vendors' own series give the exit signal.
2. **Incident reserve.** The red team suggested 40% of the cap. A fixed $0.35 (one full 8-turn incident, about $0.33) was chosen instead. At $1,000, 40% of the cap is about the same ($0.33), but at $2,000 and above 40% reserves several incidents' worth while crowding out the Reader tier.
3. **Short-history cap.** The red team suggested capping S-A at 20% when history is under 20 years. 25% was chosen so the cap coincides with the first G5 step and the ladder stays at ≤ 2×.
4. **Cost Gate wording.** The red team suggested an "expected benefit of a switch versus cost plus tax" test per order. For a published monthly rule there is no estimable per-switch benefit, so the owner's rule is implemented at strategy level (G1b) and at order level as the $20/band/tax-lot/wash-sale checks.
5. **Reader threshold.** The red team suggested $2,400 (brief 22's b1 under the 2% rule). Under this design's 1% cap and one Sonnet-class pricing basis, the arithmetic gives $1,800, rounded to $2,000. The nightly Narrator, which the red team also flagged, moves from $2,400 to $2,500 on the same basis.

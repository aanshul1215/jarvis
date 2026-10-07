# JARVIS Synthesis v1: the winning design

Chief architect, 2026-10-01. Brief numbers refer to research/01-23; "critic X" refers to the nine critiques in this folder. (DC) marks a design choice: these are not from the literature and must be simulated or probed before they are frozen. ESTIMATE marks arithmetic built on brief figures.

**Base: Proposal D (failure-first).** D has the highest mean score (7.28) and no fatal finding, and it leads on the lenses where a mistake costs money: risk, security, validation and execution. Its two weak lenses are fidelity (5.5) and buildability (6.5), and both are fixed below by grafting and cutting.

Why not the others:
- **A and C** each carry a quant-edge fatal finding (G1 is blind to the benchmark; C also misstates the after-tax expectation), and they rank lower on most other lenses.
- **B** ships no production Claude agent. The evidence does not force that, and the owner asked for agents.
- **E** contributes its honesty column and evidence weighting, but not its five frozen contracts.

## 1. Thesis

JARVIS has two parts.
- **A deterministic trading desk.** A small long/flat monthly ETF book, run by a scheduled job behind a default-deny risk gate, with a ledger that can prove every action.
- **A Claude operations team.** Agents build, watch, explain, research and audit the desk. **No Claude output reaches the order path.** No LLM trader has beaten buy-and-hold net of cost after its cutoff (brief 01), and the core must run at $0 with the LLM off (brief 22).

The owner must hear this before anything is built: **the expected after-tax result versus simply holding the same ETFs is about zero or negative.**
- Strategy A is priced at -1 to +1 point a year before tax (brief 18).
- The taxable hurdle is +1.0 to +1.3 points (brief 19).
- Central case: about -0.7 points a year taxable (range -2.4 to +0.9), about -0.1 in an IRA (critic economics, ESTIMATE). At $10,000 that is about -$74 to -$129 a year.

What JARVIS does deliver is drawdown control, discipline, a tamper-evident record, and an AI team doing real work: building the code, explaining decisions, answering ledger questions, catching defects, triaging incidents, and building a forward-scored research archive. **If Strategy A cannot beat a risk-matched benchmark after tax, JARVIS runs the benchmark (S0) and stays on as monitor, auditor and lab. That counts as a successful outcome.**

## 2. End-to-end flow

`[CODE]` deterministic, `[STAT]` statistical, `[CLAUDE]` agent, `[OWNER]` human. All jobs run as Windows user `jarvis-trader` from a tagged read-only checkout `C:\jarvis-prod` (section 8).

### `JARVIS-Trade` (about 10:00 ET each trading day, retry at 11:00; signal on bar t, act at t+1)

1. [CODE] Take a lock. Send the Healthchecks start ping. Verify `manifest.sha256` (gate module, `risk.yaml`, lockfile); a mismatch means HALT.
2. [CODE] **Broker-constraints adapter:** read account status, buying_power, `no_shorting`, margin multiplier, crypto flag and fee tier. Anything unexpected means SAFE (D; brief 21).
3. [CODE] Ingest **account activities** (fills, dividends, fees, splits) into `activities`, then reconcile.
   - Expected differences are matched: dividends, fees, partial fills, own stop fills, corporate actions. Cash tolerance is max($1, 0.1%).
   - Anything unexplained, including an order not in `intents`, means SAFE (critic risk M3, execution 5).
4. [CODE] **Data-trust gate:** Alpaca and Tiingo closes must agree within 0.5%; any move over 30% without a corporate action is quarantined.
   - On failure, no signal-driven order is placed (entry or exit).
   - Steps 1-3, 11 and 12 still run. There is no override.
5. [CODE] Freeze and hash the **AsOfSnapshot** (`available_at <= decision_time`).
6. [CODE] **Catch-up rule:** on each of the first 5 trading days of the month, re-evaluate the month-end signal on month-end as-of data until the target book is reached (critic risk M5).
7. [CODE] Strategy plug-ins: `Strategy.target(AsOfSnapshot) -> TargetBook` for the S0 core and the S-A satellite.
8. [CODE] Combine the targets.
   - Cost gate: skip changes under $20 or inside the no-trade band.
   - Keep a 2% cash buffer.
   - Sell first.
9. [CODE] **Risk gate** (section 6). A reason code is written to `gate_log`.
10. [CODE] Write `intents` with `client_order_id = hash(decision_id, leg, attempt)`, then submit and poll.
    - `attempt` increments only after a lookup confirms the prior id is terminal.
    - Orders are marketable limits, 09:45-15:30 ET, polled to a terminal state.
    - Buys are sized from broker buying_power after the sells finish.
    - Intents die with their run; a retry recomputes from scratch (critic risk M6).
11. [CODE] Protection check: no unexpected open orders. This becomes stop verification once crypto exists.
12. [CODE] Append to the hash-chained `ledger`. The success ping carries the head hash, which anchors it off-host.

### `JARVIS-Evening` (19:00 ET)

13. [CODE] Archive EDGAR 8-K items, Form 4 filings and Alpaca news headline metadata, each with `first_seen_at`.
14. [CODE] **Watch scan:** price/volume z-scores, 8-K items, Form 4 buy clusters and news-volume spikes become `watch_items`, each with a pre-registered forward-outcome label.
15. [CODE] Shadow NAV after modelled tax for S0, S0-RM and S-A. Score watch outcomes that have matured.
16. [CODE] Templated status by ntfy and email. Write `ledger_ro.sqlite` and an encrypted backup.

### Weekly and on events

17. [CLAUDE] Narrator: weekly memo, plus a note on each trade, SAFE/HALT or gate transition.
18. [CLAUDE] Incident Analyst on SAFE or HALT. Red-Team on specs, promotions, limit loosening and gate diffs.
19. [CLAUDE] Reader: batch extraction over the archive, only when a scoring run is due.
20. [CLAUDE + OWNER] Attended Claude Code sessions: Builder, monthly Strategy Lab, `/ask-ledger`.

## 3. Agent roster: resolving "uses AI agents"

**The split.** The evidence rules Claude *out* of selecting, sizing and exiting trades (briefs 01, 02, 10). It rules Claude *in* for building, extraction, narration, adversarial review of artifacts and offline research (briefs 01-03). Claude therefore gets every job on the second list, each with an input contract, a mechanical verifier and a cost.

**Spend and model handling.**
- Production calls use an API key in a dedicated `jarvis` workspace.
- Cap: **`min($15, 1% x capital / 12)`** until an LLM feature earns weight. That is $0.83/month at $1,000, $4.17 at $5,000 and $8.33 at $10,000. This is D's formula halved, because the expected edge is about zero.
- A small prepaid balance is the real ceiling. Hitting the cap means "LLM unavailable"; trading is unaffected.
- Model IDs live in `config/models.yaml`. No pin on Haiku 4.5 (retirement floor 2026-10-15); budget at Sonnet-class rates (brief 22).
- Every call is stored in `llm_calls` (request, response, model, prompt hash, usage, `stop_reason`). A `refusal` or `max_tokens` stop produces null. Batch results are persisted on arrival, since retention is 29 days (brief 13).

| # | Agent | Real work | Trigger / runs on | Input → output | Mechanical verifier | Forbidden | $/mo |
|---|---|---|---|---|---|---|---|
| 1 | **Builder** | Writes all code, tests, the mock broker and the runbook | Owner sessions; Claude Code on plan; dev tree `C:\dev\jarvis` | Repo → commits | Gate property tests, future-poisoning, replay identity, GF drills. Tests, not a second Claude (critic LLM-arch) | Reading `jarvis-trader` files (OS ACL); changing `jarvis/gate/` or `config/risk.yaml` without an owner-reviewed diff | Plan |
| 2 | **Narrator** | Weekly memo; explains trades, rejections and gate moves; dollar downside | Weekly batch plus events; API, Sonnet-class | Ledger numbers and enums → `Report{headline, actions[], rejections[], risk_state, vs_S0, vs_S0RM, questions_for_owner[]}` | Every number is checked against the ledger; template sent on failure | Raw text; URLs/HTML (plain text only); any recipient but the owner | ~$0.15 (E) |
| 3 | **Ledger Analyst** | Conversational JARVIS ("why did we sell gold in March?") | `/ask-ledger` in Claude Code | `ledger_ro.sqlite` (read-only URI) → answer with its SQL | SQL shown; read-only connection | Writes; network; archive text | Plan |
| 4 | **Red-Team** | Pre-mortem on G0/G1 packages, promotions, loosening and gate diffs | Event, a few a year; Sonnet-class, fresh context | Spec, harness report, diff → `{failure_modes[], missing_evidence[], leakage_suspects[], kill_conditions[]}` | Catch rate measured first on seeded defects (v1's four plus synthetic) | Approving; probabilities | <$0.50 |
| 5 | **Strategy Lab** | Ideas → G0 specs; backtests via the harness | Monthly, attended, plan | Research copy, holdout sealed → `StrategySpec` plus trial rows | `jarvis-lab run <spec_id>` is the only path and auto-logs to `lab.sqlite.trials`; ≤20 variants per family; cumulative N_eff (C) | Holdout; prod paths (PreToolUse deny hook); web | Plan |
| 6 | **Incident Analyst** | Incident draft plus runbook step | SAFE/HALT; one API call | Redacted log plus code-built enum broker snapshot → `{timeline, cause_enum, runbook_step_id, evidence_row_ids}` | Cites row IDs; the owner acts | Actions; clearing HALT; keys | <$0.50 |
| 7 | **Reader** (quarantined) | Typed events from archived filings and headlines, scored forward | Batch when an A0/A1 run is due; API, Sonnet-class | NFKC-normalised, HTML-stripped, length-capped, JSON-encoded text → `{event_type, materiality, novelty, instruction_like_text, span_start, span_end}` | Spans are code-verified substrings or null; golden set; injection set in CI | Tools; network; ticker mapping; free text; any effect on exits | ~$1 per 300 items (ESTIMATE, brief 22 per-item rate) |

### Agent ladder (E's structure with C's rule)

- **A0:** ≥99% schema-valid and accurate on a ~300-item golden set, plus the injection set. Labels are deterministic EDGAR metadata (8-K item numbers, Form 4 codes), so nothing needs hand-labelling (A).
- **A1:** forward shadow at weight 0, Brier-scored against a code-only baseline on watch-universe events. The pre-registered target is |5-day excess return| > 2 x trailing 60-day volatility x sqrt(5) (DC).
- **A2:** may veto or reduce *risk-increasing* orders only.
- **There is no A3.** Text never increases a position, and never blocks an exit, a stop re-arm or the kill switch (critic security; brief 13).
- **On a model change,** the successor is re-run over archive text dated after *its* cutoff (critic validation).
- **Honest outlook:** A2 is doubtful within one model generation, so agents stay off the money by default.

### What happens to v3's 18 agents

| Becomes | Agents |
|---|---|
| Code | Orchestrator, Goal Planner, Scanner, Data Trust, Market/Technical, Crypto, Strategy/Portfolio, Capital Governor, Execution, Position Manager, Ledger, Flow (as a cost monitor), Manipulation (as a pump/divergence filter) |
| Statistics | Volatility: EWMA, with HAR only if it wins out of sample (B) |
| Claude | News/Fundamental → Reader; Bull/Bear → Red-Team; Ledger/Review → Narrator plus Ledger Analyst |

The dashboard labels every role [code], [stat] or [Claude].

## 4. Strategies and universe at launch

**Universe:** five liquid ETFs (US equity, developed ex-US, intermediate Treasuries, REITs, commodities/gold) plus a T-bill ETF. Tickers are fixed at G0, and choosing them counts as a registered trial. Fractional lots are allowed.

- **S0 core (always live, always admissible):** equal weight, monthly decision points, 20% no-trade band. In a taxable account it rebalances by contributions or the band, so the null does not realise gains (critic quant 8). It needs plumbing gates only.
- **S0-RM (shadow):** S0 blended with T-bills to S-A's backtest volatility. This is the risk-matched null: "half the drawdown" can also be bought by holding less risk (critic quant S4).
- **S-A satellite: plain Faber 10-month SMA, as published.** Equal weight, month-end, long/flat, T-bill when off, **no intra-month stop**, about 3-4 round trips a year (brief 18; E).
  - Overlays (vol target at leverage 1.0, drawdown throttle, band width) are off at launch.
  - Each overlay is a registered trial, adopted only if the ablation improves G1b.
- **Crypto:** deferred (section 12).
- **Owner Idea Lane:** single-name ideas (for example v1's TSLA) are tracked in shadow with forward outcomes and a Red-Team note. JARVIS never trades them.

**Core-satellite** (critic economics). S0 holds all capital that S-A has not yet earned, so undeployed money is never idle cash. **Compounding** (v3 section 2): `satellite_$ = stage_fraction x marked equity`. `stage_fraction` rises only through approved G5 steps and is cut by the drawdown bands, never because a target was missed.

**Adding strategies:** spec → Red-Team → owner freezes G0 → G1-G5. LLM-originated specs are tagged `llm_origin` and presumed mined from history the model already saw. Only data from July 2026 onward is clean for them (brief 13; critic validation X8).

## 5. Data plan

| Need | Source ($0) | Point-in-time handling |
|---|---|---|
| ETF daily bars | Alpaca Basic, SIP history older than 15 minutes, back to about 2016 (21) | Raw bars plus a `corporate_actions` table, adjusted as of the decision date (06) |
| 20+ year history and cross-check | Tiingo Starter EOD; pre-inception proxies UNVERIFIED (20) | Hashed research copy `research/YYYYMMDD/` |
| Collar reference | IEX quote no more than 60 s old; fallback to the agreed prior close | Logged per order |
| Cash rate | FRED/ALFRED vintages (attribution in the dashboard footer) | Vintages only |
| Filings, Form 4 | EDGAR with a declared User-Agent, at most 10 requests/s | Acceptance time |
| News | Alpaca news, probed at start-up. **Headline metadata only**: Benzinga terms are unread (critic security) | `created_at`, `first_seen_at` |

**Two frozen contracts** (critic solo):
1. The bitemporal Record: `event_time, vendor_published_at, first_seen_at, available_at = max(vendor, first_seen) + lag, ingest_time, source, source_version, quality_flags, replay_id`.
2. The Strategy plug-in. `evidence` is a versioned table with `decision_weight DEFAULT 0`.

**Storage:**
- Parquet plus DuckDB, including `archive/text/`.
- `jarvis.sqlite` (WAL, one writer), with tables `runs, intents, orders, activities, ledger, lots, approvals, config_changes, vetoes, gate_log, evidence, llm_calls, watch_items, watch_outcomes, incidents`.
- `lab.sqlite`, with tables `specs, trials, holdout_burns`.
- Nightly encrypted backup.

**CI leak tests:** future-poisoning, shuffled-label at chance, one-extra-bar lag, a correlation tripwire, and an alarm at Sharpe > 3 or accuracy > 60% (D; brief 15).

**Watch universe:** the owner's 20 names plus about 100 liquid large caps, fixed on the registration date (DC). Scoring is forward-only, which avoids survivorship bias. These names are never traded.

## 6. Risk gate, sizing and exits

Values are (DC). They are frozen before G1 and counted as trials (critic validation X2), and kept in protected `config/risk.yaml`. **Tightening applies immediately. Loosening waits 72 hours, needs a Red-Team note and starts next session** (D).

| Control | Setting |
|---|---|
| Broker side | `no_shorting=true`, `max_margin_multiplier=1` at Alpaca (B; brief 21) |
| Per-symbol | No more than 25% of equity (T-bill ETF exempt); allow-list only |
| Entry order notional | No more than target weight + 5 points of equity |
| **Risk-reducing class** | Sells (never more than the broker-reported position) and T-bill buys funded in the same run. Exempt from the per-order caps and the 10-minute same-side rule (critic execution 6) |
| Collar | ±1.0% against an IEX quote no more than 60 s old, else ±2.0% against the agreed prior close; T-bill ETF ±0.3%. Otherwise skip the order and catch up |
| Rate | At most 20 orders a run, 40 a day, 5 cancels a minute; a breach means HALT |
| Minimum order / cash buffer | $20 / 2% (E) |
| Typed rejections | 403 self-cross, PDT and intraday-margin rejections are never retried (D; agreement s.32) |
| Loss states | Day down 5%: no new entries. Bootstrap p90: yellow (freeze scale-up, halve the satellite). p99: red (satellite back to shadow). A 25% loss of deployed satellite: HALT, and a fresh G1 is required (brief 20) |

**Exits.** S-A exits only on the month-end signal.

**No resting stops on the ETF book.** S0, the alternative the owner would otherwise hold, has none, and the catch-up rule plus the dead-man alert cover a missed month-end. This also removes, from phase 1:
- the GTC re-arm state machine;
- the stop/sell race;
- the conflict between protective stops and the self-cross rule;
- the problem of whole shares not fitting at $1,000 (critics risk, execution, solo).

**Stop lifecycle** (written now for crypto or any later discrete trade):
1. Size the stop to the filled quantity.
2. On exit: cancel the stop, wait for a terminal state, then sell a quantity taken from the broker's position.
3. Re-arm with a new id before the 90-day GTC expiry.
4. Protective orders form their own class, `PROT`, exempt from the in-house self-cross rule. Use OTO/OCO where Alpaca allows it (brief 17).

**Kill switch** (fixes a defect shared by all five proposals):
- `jarvis kill` sets HALT and cancels **non-`PROT` orders only**.
- `jarvis flatten --confirm` is separate: close-all with `cancel_orders=true` in regular hours, queued for 09:45 otherwise (equity market orders are rejected out of hours; brief 17).
- The Alpaca app is the fallback, but note that its cancel-all also removes stops.
- No off-host watchdog can cancel orders, because Alpaca keys cannot be scoped (brief 23). This is accepted. The mitigations are the phone alert, plus Alpaca trade confirmations sent to a separate inbox as an independent witness.

## 7. Validation and promotion gates

| Gate | Pass criteria |
|---|---|
| G0 | Frozen spec hash. Grid of at most 6 cells. Overlays and risk values registered as trials. N_eff = max(ONC K, Galwey m) over the cumulative registry |
| G1a Absolute | At least 20 years pooled. DSR ≥ 0.95 at N_eff; the 0.90 published-rule relaxation applies only with no overlays. Plateau test. At least 3 independent bear episodes, counted |
| **G1b Benchmark (decides)** | Lot-level after-tax simulator (ST/LT, wash sale, dividend qualification) for the chosen account type. Paired block bootstrap on monthly differences. S-A must show (i) a median after-tax CAGR gap vs S0 of at least -1.0 point **and** max drawdown no more than 0.7x S0's (B), and (ii) median after-tax CAGR at least that of S0-RM at equal or lower p90 drawdown. Reported as a range, labelled "drawdown-for-return, not alpha". The post-2013 slice is reported separately; if it trails S0-RM by more than the tax gap, S-A is not run for return. The test cannot be powered (IR about ±0.2; Sharpe-difference SE about 0.14, critic validation), so the report says the decision rests on dominance and priors |
| G1c | CI leak tests green. DSR/PBO formulas checked against the papers. Null simulation of the false-pass rate (briefs 08, 20) |
| **GF Drills** | Mock Alpaca (`tests/fake_alpaca.py`): crash between intent and submit, crash between submit and poll, duplicate id on restart, 5xx/timeout, partial fill plus unfilled DAY order, stale data plus catch-up, foreign order → SAFE, restore from backup. On paper: kill switch, dead-man alert reaching the phone, a deliberate missed run |
| G2 Shadow | At least 6 monthly decisions; 100% replay identity; **at least 2 position changes** (restored from brief 20) |
| G3 Paper | At least 3 rebalances; paper balance = real capital; pessimistic fills; zero *unexplained* breaks |
| G4 Micro-live | Satellite = max(20% of capital, $200), with the S0 core live. At least 6 months **and** at least 20 fills, S0 fills included; expect 12-18 months. ETF slippage against the arrival quote must average 10 bps per fill or less (DC). The 1.5x-model cost test applies to crypto only |
| G5 Scale | `stage_fraction` 20 → 50 → 100%, at least 6 months per step. Tracking error to replay in band; zero severity-1 incidents; never on live Sharpe |

**If G1b fails, S-A is retired, not tuned.** A rewrite counts as a new trial in the same family, and the holdout is burned per family (C, critic validation). The book then runs S0 or S0-RM as a "risk dial", with JARVIS as monitor.

**Sunset rule:** after 24 months of G4/G5, if the all-cost after-tax P&L (LLM, power and data included) trails the S0-RM shadow and shows no drawdown benefit, the satellite returns to S0 and LLM spend drops to the Narrator only.

## 8. Runtime, hosting, storage, monitoring, secrets

**Host and process**
- The laptop runs Task Scheduler jobs (WakeToRun, StartWhenAvailable, RestartOnFailure, no AC sleep).
- Python 3.12 venv with a hash-pinned lockfile; no Docker (brief 14).
- About 0.5 GB per run. No Claude Code sessions between 09:45 and 11:30 ET.

**Two Windows users** (C's control, made the default)
- `jarvis-trader` owns `C:\jarvis-prod`, both databases, the DPAPI secrets (Alpaca live key from G4 only; Anthropic production key) and the scheduled tasks.
- The owner's user, which runs Claude Code, has no ACL access to any of these.
- The production `ANTHROPIC_API_KEY` is never set in the owner's environment; otherwise attended sessions would silently bill it and drain the cap (brief 22).

**Deploys:** tag the release, pull it as `jarvis-trader`, refresh the manifest, then perform the config-hash handshake. Never deploy while orders are working (D; brief 12).

**Fallback if the P0 probe fails** (DPAPI with "run whether logged on or not" is untested, brief 23):
- move to a VM only after Alpaca confirms in writing that running on a server is acceptable;
- otherwise use **attended-live mode**, where the owner logs in as `jarvis-trader` for month-end runs. A monthly book makes this feasible.

**Approvals:** `jarvis approve <id>` runs only as `jarvis-trader` and needs the 6-character summary hash shown in the email, so agents cannot self-approve. Requests expire after 72 hours, which counts as a rejection.

**Host move:** use systemd `LoadCredentialEncrypted=` on the VM (brief 23). Cut over in order: disable the laptop task, rotate the key, then enable the VM; both are never live at once (critic risk M7).

**Monitoring:**
- Healthchecks with 2-hour grace;
- a monthly deliberate-skip silence test;
- a model-retirement tripwire (daily check that the model ID still exists; weekly hash of the deprecations page; an alert starts the 60-day procedure);
- weekly hashes of the fragile vendor pages (fractional DAY-only, GTC 90 days, fees, PDT).

**Hygiene and perimeter:**
- **First action:** revoke the OpenAI key hard-coded at `jarvis_backend.py` line 597 at the provider, review its usage, then make the Hugging Face Space private or delete it.
- Gitleaks pre-commit hook; BitLocker.
- **Legal perimeter** (brief 12 s4.3): own money only. Five things end that status: outside money, pooling, authority over another person's account, selling or publishing signals, and showing performance to prospects.

## 9. Owner experience

**Permission modes** (from v2; each change audited in `config_changes`):
- **RECOMMEND:** JARVIS emails orders; the owner places them by hand, and fills are imported as expected activity.
- **PAPER.**
- **ACT-WITHIN-LIMITS:** any manual trade puts JARVIS into SAFE. The owner may **veto** an intent (`jarvis veto`, with counterfactual P&L logged in `vetoes`) but not add one. Discretionary trading uses a separate account, which the wash-sale guard watches.

**Rhythm:**
- **Daily (about 0-1 minute):** templated status. Act only on SAFE or HALT, using the runbook and the Incident Analyst's draft.
- **Monthly from month one:** a **"shadow JARVIS" email** showing what S0 and S-A would do and why, the top watch items, and archive counts. This doubles as the manual-execution bridge: if the executor is not finished by month 12, RECOMMEND becomes the permanent product (critic solo).
- **Weekly (about 15 minutes):** the Narrator memo covers NAV against after-tax S0 and S0-RM, rejections with reasons, the "cost of controls" and "cost of overrides" counters, LLM spend against the cap, and questions for the owner.

**Each trade explanation** shows the strategy's bootstrap return/drawdown range, the position's 1-month p5 loss in dollars, the estimated cost and the gate reasons. There is no bare confidence percentage, and base rates are shown only when n is at least 100 (brief 10).

**The optional return goal is kept.** The planner answers it with the G1 bootstrap range and the probability of reaching the goal; the goal never changes risk (A).

**Monthly (optional, about 60 minutes):** a Lab session, `/ask-ledger` and an Idea Lane review.

## 10. Mapping to the owner's documents

| Owner idea | Verdict | Reason (brief) |
|---|---|---|
| Never chase a target; FLAT valid; rules hold the money | KEPT; the goal is displayed as a range | 01, 09, 11 |
| 18 agents, LangGraph | CHANGED: 7 Claude roles off the order path, plus a code state machine | 02, 03 |
| Opportunity Scanner | KEPT as candidates plus forward-scored watch items (never traded) | 06, 09, 16 |
| Bull/Bear | CHANGED: artifact Red-Team with a measured catch rate | 02 |
| Confidence calibrator | CHANGED: separate components and a deterministic dollar downside | 10 |
| Confidence-drop exits | CHANGED: pre-registered signal exits | 17 |
| Risk gate, kill switch, ledger, "reconstructable" | KEPT and extended (kill keeps protection; off-host hash anchor) | 12, 13, 17 |
| Paper → live, staged capital, compounding | KEPT as G0-G5 plus GF, core-satellite and `stage_fraction` | 20 |
| Data Trust / SAFE | KEPT; override DROPPED | 12 |
| Equities + crypto | Crypto DEFERRED behind conditions | 11, 21 |
| Shorting, intraday, L2, spoofing detection, RL | DROPPED | 05, 06, 07, 15 |
| Build on v1 | Rebuild, with a 2-day salvage audit (`docs/v1_salvage.md`); TSLA kept on watch and in the Idea Lane | 16 |
| v1 chat | KEPT as the Ledger Analyst | 03 |
| Docker/Redis/Postgres/Grafana/React | DROPPED: SQLite, Parquet, Task Scheduler, Streamlit | 14 |
| Investor view | Owner-only, inside the legal perimeter | 12 |
| v2 permission modes | KEPT: RECOMMEND / PAPER / ACT | 12 |

## 11. Build order

Effort is from critic solo's per-component estimates, in dev-days of about 6 hours. At about 15 hours a week, calendar time is roughly 2x.

| Phase | Work | Dev-days | Exit | Usable after |
|---|---|---|---|---|
| P0 (wks 1-2) | Revoke the v1 key; set up `jarvis-trader` and the DPAPI probe; account decision tree (O3); broker probes; Alpaca config; capped workspace; Healthchecks. Record that brief 04's spike is skipped (thin daily executor) | 6-10 | Probe sheet closed | Decisions |
| P1 | Bitemporal ingest, trust gate, archive, watch scan, S0/S0-RM/S-A shadow job, templated email, CI leak tests, v1 audit | 28-38 | 20 clean runs | Shadow email; **G2 calendar starts** |
| P2 | Lot-level tax sim, G1a/b/c, overlay ablation, formula verification, harness and registry | 25-32 | Verdict | **Fork:** if G1b fails, the product is S0/S0-RM plus monitoring, and P3 becomes optional automation of S0 (owner decides, O18) |
| P3 | Order service, gate, activity reconciliation, kill/flatten, mock broker, GF, tax lots | 40-50 | GF passes | Paper executor |
| P4 | G3; Narrator plus validator; Incident Analyst; Red-Team seeded evaluation; `/ask-ledger`; Streamlit | 15-22 | G2 and G3 pass | Full experience |
| P5 | G4; Reader A0 | 12-20 | G4 | Small real money |
| P6 | G5; Reader A1 if the power check passes; crypto conditions | — | Per gate | — |

Paper-ready takes about 115-150 dev-days. G4 likely starts in month 10-14, and full size comes after month 40 (critic solo). **Project kill criterion:** if P3 is not done by month 12, JARVIS stays in RECOMMEND mode.

## 12. Growth path

Rules: any recurring cost C needs capital of at least 600 x C (brief 11), and LLM spend stays at or below the 1% cap until a feature earns weight.

| Unlock | Trigger | Honest outlook |
|---|---|---|
| S-A in an IRA | Eligible; fee no more than 0.25%/yr of the balance (DC); money not needed before 59½; G3/G4 re-run for the new account | Reachable if eligible |
| Reader A1 | A0 passed; archive rate gives at least 300 scored events within 9 months | Doubtful |
| Reader A2 (veto/reduce entries) | A1 beats the code-only baseline before the model retires | Doubtful |
| Nightly Narrator | Capital of at least $2,400 | Reachable; low value |
| Crypto via spot BTC/ETH ETFs, Donchian | Route and expense ratio verified; S-A at G4; incremental with/without test; 10% cap; labelled "unvalidated, loss-capped" | Possible; doubtful to beat after-tax BTC hold in a taxable account (3.2-4.1 point hurdle) |
| Alpaca spot crypto | Texas and VM confirmed in writing; ETF route unavailable; a 30% gap costs no more than 3% of equity | Doubtful |
| Norgate single stocks ($52.50/month) | Capital of at least $31,500 | Never within $10k |
| SIP, intraday, shorting, Kelly | $59,400 or more; at least 300 outcomes | Never at this size |

## 13. Three biggest risks

1. **No edge, and the owner feels misled.** *Signal:* G1b fails. *Response:* the outcome was planned and stated in section 1. S0/S0-RM runs, and the agents continue building, monitoring and researching.
2. **Solo overload leads to bypassed gates.** *Signal:* P3 not done by month 12, overrides in the approval log, or vetoes clustering after losses. *Response:* RECOMMEND becomes permanent; the 72-hour loosening delay and SAFE-on-manual-trade rules hold.
3. **Security rests on untested Windows behaviour** (`jarvis-trader` with DPAPI and Task Scheduler; Modern Standby). *Signal:* the P0 probe fails, or more than 2 runs are missed in a month. *Response:* attended-live mode, or a VM after written Alpaca confirmation.

## 14. Decision record

| # | Decision | Options (backers) | Critic findings | Choice and reason |
|---|---|---|---|---|
| D1 | Base | A-E | A and C quant-fatal; B fidelity 3.5; E overbuild | **D**: wins on the money-loss lenses; its gaps can be grafted |
| D2 | Claude's role | Reporting only (B); quant team (C); evidence slots (E) | B under-delivers; C's 9 agents include theatre; E's A3 lets text raise size | **7 verified roles, no A3, Builder explicit** |
| D3 | S-A spec | Overlaid rule (all) | Overlays untested; 0.90 relaxation misused | **Plain Faber**; overlays registered as trials |
| D4 | G1 null | DSR vs 0 (A, C, E); report only (D); numeric gate (B) | Buy-and-hold passes DSR; no risk-matched null | **G1b**: after-tax, lot-level, against S0 and S0-RM, with power stated |
| D5 | Account type | Later (A, C, E); P0 (B, D) | Largest lever; cap and lock-up omitted | **P0 decision tree**; G3/G4 re-run per account |
| D6 | Idle capital | Unstated (all) | Opportunity cost is the largest cost | **Core-satellite** |
| D7 | ETF stops | Whole-share GTC (B, D); fractional unprotected (A, C, E) | Whole shares infeasible at $1k; 3x ATR is tight; stop races | **No ETF stops**, because S0 has none; add catch-up plus dead-man |
| D8 | Kill | Cancel all (all) | Strips protection | **Cancel non-PROT**; separate flatten that handles closed markets |
| D9 | Crypto | Launch 10% (A); conditional (B, C, E); after G4 plus host move (D) | Unvalidatable; taxable hurdle; Texas unknown | **D's sequencing, B's ETF route, incremental test** |
| D10 | Text | Nightly extraction (A, C, D, E); deferred, no archive (B) | No ETF consumer; Haiku retiring | **Archive from P1; extract only to score** |
| D11 | Scanner | Dropped (B-E); watch items (A) | Forking path | **Forward-labelled watch items**; veto-only owner; separate discretionary account |
| D12 | Overrides | Forced (D); none (others) | Fidelity wants options | **Permission modes**; the 72-hour loosening delay is fixed |
| D13 | Keys | Same user (A, B, D, E); separate user (C) | DPAPI is readable by Claude Code | **`jarvis-trader`**, with an attended-live fallback |
| D14 | LLM cap | Flat $5-15; 2% scaled (D) | Flat cap is 6-18%/yr at $1k | **1% scaled plus prepaid ceiling** |
| D15 | Order of build | Executor first (D); G1 first (others) | Shadow should start right after the data spine | **Shadow in P1, verdict in P2, executor in P3** |
| D16 | G4 | 6 months / 20 fills / 1.5x (all) | 12-30 months to 20 fills; cost test below noise | **Percentage of capital with a floor; S0 fills count; ETF bps test** |
| D17 | Model | Pin Haiku 4.5 (all) | Retirement floor 2026-10-15 | **Model ID in config, Sonnet-class budget, retirement tripwire** |

## 15. Open items only a test or the owner can settle

| # | Item | How to settle |
|---|---|---|
| O1 | Does the owner have a Claude plan? Without one, the plan-based roles cost about $13-50/month (brief 22) | Ask now. If no, compare a plan against API sessions for the build, and move the Lab to monthly API sessions |
| O2 | Weekly hours | Ask; re-plan section 11 |
| O3 | IRA eligibility, earned income, $7,500 cap, liquidity before 59½, Alpaca/Equity Trust fee, paper IRA | Owner, plus a written Alpaca reply, in P0 |
| O4 | Texas has no state income tax (general knowledge); brief 19's tax questions; Alpaca lot method and 1099 | One paid consult before G4 |
| O5 | Consumer Terms 3(9) for plan-run Lab work | Lawyer question. Default: no LLM output reaches orders without an owner G0 freeze |
| O6 | Spot BTC/ETH ETF route and cost; Alpaca crypto in Texas | Written Alpaca reply; fund documents |
| O7 | VM versus the "own computer" disclosure | Ask Alpaca in writing |
| O8 | Duplicate `client_order_id` behaviour; does paper enforce the $2,000, 1x and crypto-state rules? | `probes/*.py` in P0 |
| O9 | IEX quote freshness for the chosen ETFs | Log quote age over 20 sessions |
| O10 | Tiingo vs Alpaca EOD availability by 10:00 ET | Log over 20 sessions |
| O11 | Same-day reuse of sale proceeds below $2,000; fractional dust | Paper, then the first G4 rebalance |
| O12 | DPAPI under `jarvis-trader` with "run whether logged on or not"; Modern Standby wake | P0 probe across 3 reboots |
| O13 | News on Basic; Benzinga terms | Start-up probe; read the terms before storing more than metadata |
| O14 | Pre-inception ETF proxies for 20 years | P2 inventory; otherwise state the shorter window |
| O15 | DSR/PBO formulas were recalled, not read (brief 08) | Check against the papers; run a null simulation in P2 |
| O16 | Watch-universe event rate (A1 power) | Count over the first 60 days; if 300 events take more than 9 months, declare A1 unreachable |
| O17 | Hugging Face Space visibility; v1 key usage | Owner checks the provider dashboard |
| O18 | Automate S0 if S-A fails G1b? | Owner decides at the P2 fork |

# Proposal C: Agents as the quant team

Architect C, 2026-10-01. Binding constraints: US/Texas, $1,000-$10,000 own money, near-zero monthly budget, Windows 11 laptop with 8 GB RAM, solo developer, Claude agents. "Brief N" refers to the research folder.

## 1. Thesis

JARVIS is a deterministic daily trading job with a team of Claude agents around it. The agents work like a small quant team. They research and specify strategies, attack their own results, triage bad data, diagnose incidents, explain P&L and answer the owner's questions. No agent places, sizes or vetoes an order. The evidence supports this split. No LLM trading agent has beaten buy-and-hold net of costs after its training cutoff (briefs 01, 02), LLM confidence is not a usable probability (brief 10), and per-candidate LLM calls cost $100 to thousands a month (briefs 03, 13). LLMs are strong at reading, writing code, checking work and summarising, and all of that output can be checked by code or by the owner. So the agents get the knowledge work. The money path stays testable and keeps running with the LLM switched off (brief 22). The owner asked for "a complete end-to-end system which uses AI agents". He gets one, but the agents do the research, review and reporting. They do not make the trades. That is as far as the evidence goes.

## 2. End-to-end flow

Each step is labelled **[code]** (deterministic), **[model]** (statistical) or **[agent]** (Claude).

1. **[code]** Task Scheduler starts the run after the close: file lock, then a dead-man's-switch ping (Healthchecks.io) (brief 23).
2. **[code]** Reconcile with Alpaca, which is the source of truth, against the intent ledger. Any mismatch halts new entries and alerts the owner (briefs 12, 23).
3. **[code]** Ingest daily bars, an EOD cross-check, EDGAR, ALFRED and a news probe. Every row gets bitemporal timestamps (§5).
4. **[code]** Data Trust Gate: schema, staleness, gaps, corporate actions and two-source agreement. Failing rows are quarantined, and that instrument gets no new risk.
5. **[agent]** Data-Quality Triage diagnoses the quarantined rows after the run. Only the owner can release them.
6. **[code + model]** Features: 10-month SMA, 12-month return, realised volatility and a HAR volatility forecast (brief 15).
7. **[code]** Tier-0 event flags from EDGAR form types, 8-K item numbers and Form 4 codes (brief 16).
8. **[agent]** The Filing and News Reader writes typed events to an archive at zero weight (§7).
9. **[code]** Month-end signals from each live strategy's pre-registered rules.
10. **[model + code]** Sizing: volatility target with leverage capped at 1.0, then a drawdown throttle (§6).
11. **[code]** Cost gate: trade only if the expected benefit exceeds k times (fees + spread + tax hurdle), with a no-trade band (briefs 11, 19).
12. **[code]** Hard risk gate, including erroneous-order controls (§6, brief 12).
13. **[code]** Exceptions become pending approval rows that expire to *reject* (brief 03).
14. **[code]** Write the intent, look up its deterministic `client_order_id`, submit, poll to a final state, then re-arm the resting stops (briefs 21, 23).
15. **[code]** Append to the ledger, then send the success or failure heartbeat.
16. **[agent]** The Owner Reporter writes a nightly narrative from ledger rows. Code checks every number in it.
17. **[code → agent]** Monthly, code computes attribution, replay-vs-live tracking error and realised-vs-model cost. The Post-Trade Reviewer writes the memo.
18. **[agent]** A weekly Research Lab, attended by the owner, feeds the trial registry. It never touches production.
19. **[agent]** The Incident Diagnostician runs on any failure and proposes a cause and a runbook step. The owner acts.

## 3. Agent roster

**How agents run and pay.**
- **Production agents** (2, 4, 7, 8) use an API key and the Batch API in a dedicated `jarvis` workspace with a $10 spend limit (brief 22).
- **Research and ops agents** (1, 3, 5, 6, 9) run in Claude Code sessions the owner attends, on his subscription.
- **No unattended production job uses the subscription.** Plan policy is unstable, and the Consumer Terms bar relying on the service to trade securities (brief 22).

Costs are estimates based on brief 22.

| # | Agent | Trigger | Model | Input → output | Forbidden | $/mo |
|---|---|---|---|---|---|---|
| 1 | **Lab Lead** | Weekly, attended | Opus 5.5 | Owner-supplied papers and registry summaries → `HypothesisSpec` (rationale, universe, grid of ≤6 cells, costs, dates, metric) | Web tools, holdout data, editing harness/registry/costs, secrets | $0 on Pro (API: $13-21) |
| 2 | **Filing and News Reader** | Nightly batch, from P5 | Haiku 4.5, pinned in config | One sanitised item → `EventRecord` (enum type, entity, materiality, novelty, `instruction_like_text` flag, evidence span) | All tools, raw HTML, ticker mapping, any write except its own row | ~$4 at 20 symbols |
| 3 | **Backtest Engineer** | Subagent of 1 | Sonnet 5.5 | Spec → a pure signal function plus a `RunRequest` | Any command except `jarvis-lab run <spec_id>`, data files, tests | in session |
| 4 | **Owner Reporter** | Nightly batch | Sonnet 5.5, effort low | Ledger numbers and enums (no raw text) → `DailyReport` citing ledger row IDs | Numbers not in the ledger (code checks), any recipient but the owner | ~$0.65 |
| 5 | **Red-Team Reviewer** | Every G0/G1 package | Opus 5.5, fresh context | Spec, code, harness report, registry → `RedTeamReport` (checks for leakage, survivorship, costs, hidden trials, LLM-memory risk; verdict; blocking issues) | Running variants, approving promotion | in session |
| 6 | **Ledger Analyst** (Q&A) | On demand | Sonnet 5.5 | Read-only SQLite connection → answer with its SQL shown | Writes, raw text, network | $0 on Pro |
| 7 | **Data-Quality Triage** | On quarantine | Haiku 4.5 batch | Quarantined row, both sources, corporate actions → `TriageTicket` (cause enum, proposed fix) | Releasing or editing data | <$0.25 |
| 8 | **Post-Trade Reviewer** | Monthly | Sonnet 5.5 batch | Attribution tables computed by code → `ReviewMemo` (anomalies, lessons, hypotheses tagged "post-hoc") | Changing parameters | ~$0.10 |
| 9 | **Incident Diagnostician** | Failed run, reconciliation break, missed heartbeat | Sonnet 5.5 | Logs, redacted broker snapshot, runbook → `IncidentReport` (timeline, cause, runbook step) | Keys, carrying out the remediation, config edits | $0 on Pro |

**Spend.** About $1/month at launch, $5 with the Reader. Under brief 11's 2%-drag rule, $5/month needs at least $3,000 of capital, so the Reader stays off below that. Budget about 2.6x for a Haiku successor.

**Hand-offs.** Only typed artifacts (specs, run IDs, reports, tickets) pass through `lab.sqlite` and git, never free chat. Subagents get fresh context, split by context boundary, not persona (brief 02). Every API call is recorded for replay: request, response, model ID, prompt hash, usage (briefs 03, 13).

**Prompt-injection guardrails.** No agent combines private data, untrusted content and a way to send things out (the "lethal trifecta", brief 13).
- The Reader is the only agent that sees untrusted text. It has no tools. Its input is NFKC-normalised, HTML-stripped, length-capped and JSON-encoded. Its output is enumerated fields only.
- The Reporter sees only the Reader's enumerated fields.
- The Lab reads untrusted papers but has no secrets and no web or outbound tools.
- The live Alpaca key is DPAPI-encrypted under a separate Windows user, `jarvis-trader`. DPAPI protects only against *other* users, so the owner's Claude Code account must not share that user (brief 23).
- No score derived from text can increase a position (brief 13).

**Overfitting guardrails.**
- The harness is the only way to run a backtest, and it logs every run, abandoned ones included, to the registry. N_eff is computed from the registry (brief 20).
- Holdout assets and the final years of data are not in the lab's directory. The owner unseals them once per spec.
- Each hypothesis family gets at most 20 registered variants.
- Every idea must cite a published economic rationale. Ideas the LLM came up with are presumed mined from history it already saw, so expect a low hit rate (briefs 02, 13).

**What happens to the v3 agents** (briefs 02, 03). Their jobs are numeric, cost-sensitive or must be reproducible, and multi-agent designs cost 3-15x the tokens with no shown benefit. So:
- **Code or model:** Orchestrator, Goal/Capital Planner, Scanner, Data Trust, Market/Technical, Crypto, Flow (kept only as a cost monitor), Manipulation Surveillance (liquidity rules), Strategy/Portfolio, Capital Governor, Execution, Position Manager; Model Ensemble starts as one HAR model.
- **Dropped:** Confidence Calibrator.
- **Agents:** Bull/Bear → Red-Team Reviewer; News and Fundamental → Reader plus tier-0 code; Ledger/Review → database plus agents 4, 6, 8.

## 4. Strategies and universe at launch

**Benchmark (the null hypothesis).** A static buy-and-hold of the same ETFs, rebalanced periodically. All comparisons are after cost and after tax, in the same account type (briefs 18, 19).

**Strategy A (launch).** Month-end 10-month-SMA (or 12-month return sign) long/flat on 4-6 liquid ETFs (US equity, ex-US developed equity, intermediate Treasuries, real estate, commodities or gold), with a T-bill ETF when off. About 3-4 round trips a year at a few basis points. Honest expectation: CAGR within about ±1 point a year of buy-and-hold, with roughly half the drawdown; it reduces risk, it is not alpha (brief 18). Choosing tickers is a registered trial. If Alpaca IRA trustee fees are acceptable, run A there to remove tax drag (briefs 19, 21).

**Strategy C.** Volatility targeting is a sizing governor applied to A. It is not a source of alpha (brief 18).

**Strategy B (conditional).** A BTC/ETH Donchian ensemble (20-90 days), long/flat, capped at 20% of the book. Texas was absent from Alpaca's crypto state list, which is a year old and seen only as a snippet (brief 21); confirm at signup. Spot BTC/ETH ETFs are an unresearched alternative to verify first (00b). B can never pass a standalone 20-year gate (brief 20).

**Adding strategies later.** Lab spec → Red-Team review → owner freezes G0 → G1-G5. Queued first: an opportunistic Form 4 buying overlay and a 10-K year-over-year text diff as an avoid list (brief 16). Single-stock strategies wait for survivorship-free data (§12).

## 5. Data plan

**Sources, all free.**
- Alpaca Basic: SIP daily bars older than 15 minutes, back to 2016.
- Tiingo Starter: 30+ years of EOD data, used as a cross-check and for long-history proxies. Whether those proxies are available for every asset is unverified (brief 20).
- EDGAR: keyed on acceptance and `filed` times, limited to 10 requests/second.
- ALFRED vintages, using `output_type=4`.
- Alpaca/Benzinga news, behind a start-up probe, since free access is unconfirmed (briefs 06, 16, 21).

**Point-in-time rules.** Every row stores `event_time`, `vendor_time`, `first_seen_at` and `available_at` = max(vendor_time, first_seen_at) + lag, and features join only on `available_at <= decision_time`. Raw prices and corporate actions are stored and adjusted as of each date. Revisions are new rows. Event-study CAR is an evaluation label, never a feature. Text archiving starts on day one, because it is the only clean post-cutoff text dataset JARVIS will have (briefs 06, 16, 22).

**Storage.** Parquet queried with DuckDB; `jarvis.sqlite` (WAL, one writer) for intents, ledger, approvals and LLM call logs; `lab.sqlite` for the registry. No Feast, MinIO, Redis or Postgres (brief 14).

## 6. Risk gate, sizing and exits

The starting numbers below are design choices, to be simulated in G1 (briefs 10, 12, 20).

**Structure.** Long/flat, leverage capped at 1.0, no shorting, cash ≥ 0 after open orders, symbol allow-list.

**Sizing.**
- Equal risk weights, scaled to a 10% annual volatility target using HAR, with at most 100% invested.
- Rebalance a position only when it drifts more than 25% from its target weight.
- No Kelly or confidence-based sizing: a monthly book never gets the few hundred outcomes Kelly needs.
- Drawdown throttle: size × max(0, 1 − DD/20%), measured from the high-water mark. At 20% drawdown the system halts until the owner re-arms it.

**Order controls.**
- Notional per order at most min(35% of equity, $3,500), plus a quantity cap.
- Marketable limit orders within ±0.5% of a quote no older than 60 seconds.
- At most 12 orders per run and 20 per day.
- Duplicate guard on `client_order_id` and on any same symbol/side/size order within 10 minutes.
- Self-cross guard.
- Handlers for PDT and intraday-margin rejections, because Alpaca may keep the old rule for some accounts (brief 21).

**Exits (pre-registered, brief 17).**
- Strategy A exits on the month-end signal.
- Whole-share lots also carry a GTC catastrophe stop 15% below the month's reference price, re-armed on every run because GTC orders lapse after 90 days.
- Fractional lots cannot rest any stop, so the dashboard labels them unprotected. At $1,000 most of the book will be fractional; this is accepted for diversified ETFs and stated plainly.
- Strategy B, if enabled: GTC stop-limit orders. The 20% cap bounds the loss from a 30% gap at about 6% of equity (brief 23).

**Kill switch and kill bands.** The kill switch is a separate process: cancel all, block new; flattening is a separate command, tested weekly in paper. **Yellow** (drawdown above bootstrap p90, about 15% at one year): freeze scale-up, halve risk. **Red** (above p99, about 23%, or replay tracking error out of band two months running): back to shadow. **Lifetime stop:** 25% loss of deployed capital (brief 20).

**LLM influence: zero.** Once the ablation passes, a Reader flag may block or reduce an entry (for example after an 8-K item 4.02) but never add to one. Gate parameters live in versioned configuration: changes need the owner, take effect next session, and can only tighten during a session.

## 7. Validation and promotion gates

These follow brief 20's gates for slow strategies, with an agent intake step in front.

| Gate | What it requires |
|---|---|
| G-1 Intake | Lab spec, and a red-team report with no blocking issues |
| G0 Pre-register | Owner freezes the spec hash and opens a registry entry. N_eff = max(ONC K, Galwey m) |
| G1 Backtest | Run and reported by the harness (agents only read the report): pooled ≥20 years where proxies exist; DSR ≥0.95 at N_eff (≥0.90 for a published design with N_eff ≤5); plateau ≥80% of neighbours at ≥0.6x; held-out asset classes positive ≥70%; 5-year windows positive ≥70%; with costs doubled, Sharpe ≥0.75x |
| G2 Shadow | ≥6 rebalances with 100% replay identity |
| G3 Paper | ≥3 rebalances, no reconciliation breaks, 3 failure drills. Paper P&L is not evidence |
| G4 Micro-live | $500-1,000, ≥6 months, ≥20 fills, realised cost ≤1.5x the model |
| G5 Scale | 25% → 50% → 100%, each step ≥6 months. Live Sharpe is never used to promote or kill |

**LLM components have their own gate** (briefs 02, 13, 22):
- Accuracy on a golden set of about 300 items dated after the model's cutoff.
- A prompt-injection regression set: hidden text, homoglyphs, fake headlines.
- Forward shadow running only on post-cutoff data.
- An ablation scored by Brier score over hundreds of candidate-level predictions.
- The clock restarts whenever the model ID changes.

## 8. Runtime, hosting, storage, monitoring, secrets

**Host.** The laptop, under Task Scheduler (StartWhenAvailable, WakeToRun, RestartOnFailure; sleep disabled on AC). A main run plus a retry an hour later that exits at once if the day's intents are complete (brief 23). One Python 3.12 process per run, no Docker.

**Memory (estimates).** Daily job under 0.5 GB for a few minutes; Streamlit about 0.3 GB, started on demand; each Claude Code session about 1 GB or more (brief 03). Run at most one session plus one subagent, never during the run window.

**Fallback host.** The same script on a free GCP e2-micro (us-central1) with a systemd timer. Move there before any crypto position, or after two missed runs in a month (brief 23).

**Monitoring.** Healthchecks.io free tier (2-hour grace), alerts by email (Resend free tier) and ntfy or Telegram, Alpaca status-page subscription, config hash logged every run.

**Secrets.** Rotate the v1 key. Paper and live keys are separate, and the live key exists only under `jarvis-trader`. The Anthropic key is scoped to the capped workspace. Wallet transfers stay disabled. Add a gitleaks pre-commit hook and full-disk encryption. Claude Code permission rules plus a deny-by-default PreToolUse hook block the trading directories (brief 03).

**Monthly cost.** $0 for infrastructure and $1-5 for the API. Attended sessions are covered if the owner already pays for Pro.

## 9. Owner experience

**Daily (about 2 minutes).** One email: run status, positions, risk use, triage tickets, gap to benchmark. No bare "confidence %"; base rates appear with their n, and only once n ≥ 100 (brief 10).

**Monthly (about 20 minutes).** Clear approvals, read the review memo, check realised against model costs.

**Weekly (60-90 minutes).** One Research Lab session (supply papers, steer the Lab Lead, read the red-team report, decide on G0), plus questions to the Ledger Analyst, for example "why did we sell gold in March?"

**Approvals** (each expires to *reject*): G0 freeze, holdout unseal, every gate promotion and scale step, quarantine release, gate-parameter change, throttle re-arm, enabling the Reader. There is no override for degraded data (brief 12).

## 10. Mapping to the owner's documents

| Owner idea | Verdict | Reason (brief) |
|---|---|---|
| FLAT valid; no return target; staged capital | KEPT | Supported by every cost and edge brief (09, 11) |
| Agents reason, rules hold the money | KEPT, stricter | No LLM on the order path at all (01, 02, 13) |
| Strategy Lab: LLM proposes, validation decides | KEPT, central | Safest LLM role; yield is low, so a registry and DSR are mandatory (02, 08, 20) |
| Hard risk gate, kill switch | KEPT, extended | Adds erroneous-order controls, reconciliation and a dead-man's switch (12, 17) |
| Volatility targeting, drawdown limits | KEPT | As risk tools, not alpha (10, 18) |
| Data Trust Gate / SAFE state | KEPT | Triage agent added; override path removed (12, 14) |
| Freeze contracts first; same path for backtest and live; idempotent orders | KEPT | Adds bitemporal timestamps and record-and-replay (06, 13, 22) |
| Paper → shadow → live | CHANGED | Slow-strategy gates, plus micro-live to measure cost (20) |
| 18 agents under a LangGraph supervisor | CHANGED | 9 agents, all off the money path (02, 03) |
| Bull/Bear debate | CHANGED | One offline red-team reviewer (02) |
| News agent / FinBERT RAG | CHANGED | Quarantined Reader, zero weight, risk filter only (13, 16) |
| Position Manager exits on falling confidence | CHANGED | Pre-registered exits plus broker-resting stops (17) |
| Investor view | CHANGED | Owner-only, for licence and legal reasons (12, 21) |
| Confidence Calibrator | DROPPED | A pooled score cannot be calibrated (10) |
| L2 / order-flow alpha; manipulation forensics | DROPPED | Signals last seconds; no equity L2 data (06, 07) |
| Long/short, intraday, always-on scanner | DROPPED | Fees, free-data limits, no crypto shorting (05, 06, 11) |
| Wrap v1; social sentiment; CAR feature; RL | DROPPED | Leakage, pump risk, cannot be validated (15, 16) |
| Docker/Redis/Postgres/MinIO/Grafana stack | DROPPED | 8 GB of RAM; one process is safer (14) |
| Fractional Kelly | DEFERRED | Needs a few hundred outcomes (10) |
| Crypto sleeve; Coinbase second broker | DEFERRED | Texas eligibility unknown; fees 3-4x higher (11, 21) |
| Form 4/13F overlays; multi-model ensemble | DEFERRED | Lab queue, added in sequence behind baselines (15, 16) |

## 11. Build order

**P0: Hygiene and probes (2 weeks).**
- Rotate the leaked key; create `jarvis-trader` and the capped workspace; set up Healthchecks.
- Paper-account probes: news on Basic, duplicate `client_order_id`, Texas crypto eligibility, IRA fees.
- *Exit:* every probe answered.

**P1: Data spine (3-4 weeks).**
- Ingestion, the point-in-time store, the Trust Gate, the text archive, the benchmark, and the Ledger Analyst.
- *Exit:* 30 clean nightly runs and identical features on replay.
- *Usable:* a queryable archive and benchmark reports.

**P2: Research Lab (4 weeks).**
- Harness, cost model, registry, holdout sealing, agents 1, 3 and 5, and the permission hooks.
- *Exit:* Strategy A passes or honestly fails G0 and G1.
- *Usable:* the full research lab, with no trading.

**P3: Execution core and shadow (6+ months, set by G2's calendar).**
- Risk gate, intents, reconciliation, kill switch, runbook, and agents 4, 7 and 9.
- Paper (G3) runs alongside shadow.
- *Exit:* G2 and G3 pass, the drills pass, and brief 12's minimum control set is in place.
- *Usable:* daily reports and paper trading.

**P4: Micro-live (6+ months).**
- $500-1,000 of real money, and agent 8 starts.
- *Exit:* G4.

**P5: Scale.**
- G5 scaling steps.
- The Reader runs in forward shadow once capital reaches $3,000.
- Overlays from the lab queue.

## 12. Growth path

| Trigger | Unlock |
|---|---|
| Capital ≥ $3,000 | Reader nightly batch, about $4/month, under 2% drag (11, 22) |
| Capital ≥ $5,600 | Sonnet or successor extraction at about 2.6x the cost (22) |
| No Pro plan | Lab sessions move to monthly on the API at about $3-5 each; weekly would cost $13-21/month (22) |
| Crypto confirmed for Texas, or spot ETFs verified | Strategy B enters G0; move to the e2-micro first (23) |
| A single-stock strategy passes G1 on proxy data **and** capital ≥ $31,500 | Norgate Platinum at $630/year (06, 11) |
| Two missed runs in a month | e2-micro; a $4-6 VPS once capital is ≥ $3,000 (23) |
| A Reader flag passes the forward ablation | It may block or reduce entries, never increase them |
| A few hundred resolved outcomes in a faster strategy | Shrunk fractional Kelly, as an upper bound (10) |
| Never at this scale | $99 SIP data (needs about $59k of capital), L2, shorting by default |

## 13. Three biggest risks and what would prove this wrong

1. **The lab overfits or finds nothing.** Claude already knows how 2008, 2020 and 2022 turned out, and in Gençay's test every LLM-discovered strategy failed trial-count deflation (brief 02). *Proven wrong if* after 12 months and at least 10 registered families nothing passes G1, or the red-team never catches anything the harness missed. *Then* cut the lab to a quarterly literature review and run on rules only.
2. **There is no edge to manage.** Strategy A's honest expectation is about zero against after-tax buy-and-hold, and its Sharpe may miss the DSR bar (briefs 18, 20). *Proven wrong if* A fails G1 or trails the benchmark by more than its drawdown benefit is worth. *Then* JARVIS is a rebalancer plus reporting agents, and the owner should be told so plainly.
3. **The team rests on owner time, plan policy and model churn.** Nine agents need weekly attention, plan terms can change, and Haiku 4.5 may retire from 2026-10-15 (brief 22). *Proven wrong if* lab sessions lapse for over two months, or a model swap breaks the golden set unvalidated. *Then* the core keeps trading with the LLM off; P3 must demonstrate exactly that.

# Proposal D: Failure-first JARVIS

Architect D, 2026-10-01. Brief numbers refer to `research/01-23`. (DC) marks my own design choices, which are not from the literature and should be simulated on JARVIS data before they are frozen.

## 1. Thesis

JARVIS-D is a **trading ledger with an executor attached**. It is not a forecasting engine with a ledger attached.

A $1k-$10k account has very little edge to find. A long/flat ETF/BTC trend book should be planned at net Sharpe 0.3-0.5 (briefs 18, 20). No LLM trader has beaten buy-and-hold net of costs after its training cutoff (brief 01). Backtest Sharpe explains under 2.5% of live Sharpe (brief 08).

The ways to lose money, by contrast, are many and well documented: runaway orders and unit errors (brief 12), host death with no resting stop (brief 23), leakage and leaked keys (v1 had both), hidden trials (brief 20), LLM bills of up to 26% of capital a year (brief 22), and 1.0-1.5 points of tax drag (brief 19).

At this size, avoiding a 25% blow-up is worth more than any plausible alpha. So every component prevents a named failure (F1-F14, section 6), and strategies are pure-function plug-ins with no broker access. Claude agents read, write and review around the money path, never on it. The product does the boring thing (rebalancing a small trend book, or just holding the benchmark) without ever doing something stupid, and its ledger can prove it.

## 2. End-to-end flow

`[CODE]` = deterministic code, `[STAT]` = statistical model, `[CLAUDE]` = Claude agent, `[OWNER]` = human.

**Trading run** (Task Scheduler, about 10:00 ET each trading day, plus a retry at about 11:00 that exits at once if the day's intents are complete)
1. `[CODE]` Take a single-instance lock, ping the dead-man's switch, and log the code version and config hash.
2. `[CODE]` **Broker-constraints adapter:** read account status, buying power, shorting/crypto/margin flags and fee tier. Anything unexpected → SAFE, meaning no new risk (briefs 12, 21).
3. `[CODE]` **Reconcile** positions, orders and cash against the broker, which wins. An unknown order or position (a manual trade, for example) → SAFE plus an alert (briefs 17, 23).
4. `[CODE]` **Data-trust gate:** expected bars present and fresh; Alpaca and Tiingo closes within 0.5% (ETFs) or 1% (crypto); moves over 30% without a corporate action quarantined (DC). Any failure skips the run with a logged reason.
5. `[CODE]` Freeze and hash an **as-of snapshot**: only rows with `available_at ≤ decision_time`.
6. `[STAT]` Volatility per asset: 60-day realised to start, HAR/GJR-GARCH later (brief 15). Used only for sizing.
7. `[CODE]` **Strategy plug-ins** return target weights and pre-registered exits. They signal on the month-end close and execute the next session.
8. `[CODE]` **Event filter** over stored Reader extractions. It can only veto or reduce a trade, and at launch it only logs (briefs 13, 16).
9. `[CODE]` **Portfolio construction:** volatility target, leverage 1.0, whole shares for overnight holdings, a no-trade band, the **cost gate** (brief 11) and a **tax-lot check** (brief 19).
10. `[CODE]` **Risk gate** (section 6). Every check writes a reason code.
11. `[CODE]` Write **intent rows** with a deterministic `client_order_id` before any broker call. `[OWNER]` approval is needed only in pilot stages.
12. `[CODE]` **Order service:** look the order up by id before submitting, use marketable limit orders, poll to a terminal state, and never blind-retry a replace (briefs 21, 23).
13. `[CODE]` **Protection check:** every holding must have a broker-resting stop. Re-arm any that are missing or near the 90-day GTC expiry.
14. `[CODE]` Close the hash-chained ledger and ping success or failure.

**Evening run, weekly checks and event triggers**
15. `[CODE]` Archive news and EDGAR items with `first_seen_at` (brief 16).
16. `[CLAUDE]` Submit the Reader and Narrator batches. `[CODE]` validates the results before the digest is sent.
17. `[CODE]`/`[STAT]` Weekly: replay identity, realised against modelled cost, and drawdown against the bootstrap bands (brief 20).
18. `[CLAUDE]` Strategy Lab weekly. The Incident Analyst runs on any SAFE or HALT, the Red-Team on any promotion or loosening, and the Change Reviewer on every deploy.

## 3. Agent roster

All six agents are Claude and all sit **off the order path**. None holds broker keys or uses network tools on untrusted text. Every call is stored for record-and-replay: model ID, full request and response, prompt hash and usage (brief 22). Costs are estimates unless a brief is cited.

| Agent | Job | Trigger | Tier | Inputs → structured output | Forbidden | Est. $/mo |
|---|---|---|---|---|---|---|
| **Reader** (quarantined) | News, 8-K and Form 4 text → typed events | Nightly Batch | Haiku 4.5, pinned; successor at 2.6x (brief 22) | Sanitised text → `{event_type, entity_id, direction, materiality, novelty, injection_flag, evidence_span}` | Tools, network, ticker mapping, raising size | ~$1-2 (scaled from brief 22's $4 for 100 items) |
| **Narrator** | Daily and weekly digest | Nightly Batch | Sonnet 5.5, low effort | Ledger extract → markdown citing ledger-row IDs | Any number absent from the ledger (code checks; on failure, a template is sent) | ~$0.65 (brief 22) |
| **Red-Team** | Pre-mortem on a promotion, new spec or limit loosening | ~2-5 a month | Sonnet 5.5 | Spec, gate evidence → `{failure_modes, kill_conditions, missing_evidence}` | Approving; giving confidences; editing config | <$1 |
| **Incident Analyst** | Incident report draft | Any SAFE or HALT | Sonnet 5.5 | Redacted logs → `{timeline, cause, runbook_step, evidence_rows}` | Any action; clearing a HALT | <$1 |
| **Strategy Lab** | G0 specs plus sandbox backtests | Weekly, owner-attended Claude Code | Plan (Opus/Sonnet 5.5) | Research data copy → spec plus a registry row for **every** variant | Live keys or config; editing the registry | $0 extra on Pro; $12.8 on API (brief 22) |
| **Change Reviewer** | Checks each diff against the failure catalogue | Every deploy | Plan | Diff → checklist | Merging or deploying | $0 extra |

**API spend.** The cap is `min($15, 2% × capital / 12)` in a dedicated workspace, with a small prepaid balance as the real ceiling (briefs 11, 22). That gives $1.67 a month at $1,000 (Narrator only), $8.33 at $5,000, $15 at $10,000, and $3 during paper. Hitting the cap means "LLM unavailable". **Trading is unaffected, because the core needs no LLM.**

**The owner's 18 v3 agents** (brief 02):
- **Become code:** Orchestrator (a state machine), Goal Planner (a config validator that rejects return targets), Scanner, Data Trust, Market/Technical, Crypto, Strategy/Portfolio, Capital Governor, Execution, Position Manager, Ledger, plus Flow (a liquidity and cost monitor) and Manipulation (pump and divergence flags) (brief 07).
- **Become statistics:** Model Ensemble (volatility only at launch) and Calibrator (deferred).
- **Why:** these jobs are numeric, latency- or cost-sensitive, or must be reproducible. Multi-agent designs cost 3-15x the tokens and fail 41-87% of the time (brief 02).
- **Stay Claude roles:** News/Event and Fundamental become the Reader, Bull/Bear becomes the Red-Team, and Ledger narrative becomes the Narrator.
- **Added:** Incident Analyst and Change Reviewer, because deployment and incident handling are where Knight lost $460M (brief 12).

## 4. Strategies and universe at launch

- **S0, benchmark (always on, in shadow).** Buy-and-hold of the same ETFs plus BTC/ETH, rebalanced periodically and valued after tax in the same account type (briefs 18, 19). If nothing beats S0 through G1, **JARVIS runs S0**, which is a valid outcome.
- **S-A, ETF trend.** Month-end 10-month-SMA long/flat on 4-6 liquid ETFs (for example US equity, international equity, bonds, gold), with a T-bill ETF when off. About 3-4 round trips a year. Honest expectation: -1 to +1 point a year of CAGR with roughly half the drawdown (brief 18). At $1,000, use fewer and cheaper ETFs so that whole-share weights land within 5 points of target (DC).
- **S-B, BTC/ETH trend sleeve (CONDITIONAL).** A Donchian ensemble over 20-90 days, long/flat, with a 20% no-trade band and limit orders (brief 18). It starts only if Alpaca crypto is confirmed for Texas (brief 21), the host has moved off the laptop (brief 23), and S-A has passed G4. The sleeve is capped at 10% at launch and 20% at most. Its net Sharpe is unknown, and it cannot pass a standalone 20-year gate (brief 20).
- **Volatility targeting** is a risk governor, not a strategy (brief 18).

**Plug-in contract.** A strategy is a pure function `(as_of_snapshot) → {target_weights, exits, rationale_codes}` with a frozen spec hash. It has no I/O, no clock and no broker access. It enters only through G0-G5, with its exits backtested together with its entries (brief 17). Orders from strategies sharing a symbol are netted by the self-cross guard (brief 12).

## 5. Data plan

| Need | Source ($0) | Point-in-time handling |
|---|---|---|
| Daily bars, ETFs and crypto | Alpaca Basic: SIP history older than 15 minutes, back to about 2016 (briefs 06, 21) | Raw bars plus corporate actions; adjustments computed as-of (brief 06) |
| Long history for G1 | Tiingo Starter EOD, 30+ years (brief 06); ETF proxies UNVERIFIED (brief 20) | Frozen, hashed research copy |
| Cross-check | Tiingo; Coinbase and Kraken public feeds | Divergence → data-trust failure |
| Cash rate | FRED/ALFRED vintages (brief 06) | `output_type` vintages only |
| News | Alpaca news if a start-up probe succeeds, else none (brief 21) | `created_at`, `received_at`, our `first_seen_at` |
| Filings, Form 4 | EDGAR (keyless, 10 requests/s) | Acceptance timestamp |

Every row is **bitemporal** (`event_time`, `vendor_published_at`, `first_seen_at`, `available_at`), and joins are as-of only. Leakage defences:
- A CI **future-poisoning test** corrupts all data after T and asserts that every decision up to T is unchanged (DC).
- An alarm fires on Sharpe above 3 or accuracy above 60% (briefs 08, 09).
- Signals use bar *t* and act at *t+1*.

Storage is Parquet queried with DuckDB, plus SQLite in WAL mode with one writer, backed up nightly to a second encrypted location (brief 14). News archiving starts in Phase 1, because forward-recorded data is the only uncontaminated LLM evidence (briefs 01, 16).

## 6. Risk gate, sizing and exits

**Failure catalogue** (each failure maps to the controls that prevent it):

| # | Failure | Controls |
|---|---|---|
| F1 | Bad order (units, price) | Allow-list; per-order notional ≤ min(30% of equity, $4,000); quantity cap; price collar ±1.5% ETF / ±3% crypto against a reference ≤60 s old; marketable limits only, 09:45-15:30 ET (all DC) |
| F2 | Duplicate or runaway orders | Intent first; `client_order_id` = hash(decision, leg, attempt); lookup before resubmit; single-instance lock; ≤20 orders a run, ≤40 a day, ≤5 cancels a minute, turnover ≤100% of equity a run (DC); a breach → HALT |
| F3 | Stale or bad data | Data-trust gate → skip; collar is wider because quotes are IEX-only (brief 12) |
| F4 | Leakage | Bitemporal as-of joins; future-poisoning test |
| F5 | Overfitting | Trial registry, DSR at N_eff, plateau test (section 7) |
| F6 | Host death with open positions | Run-to-completion job; reconcile on start; no automatic flatten on restart (brief 17); whole-share GTC stops re-armed every run; crypto GTC stop-limit; off-host dead-man's switch |
| F7 | Runaway LLM spend | Capital-scaled cap; Batch only; core needs no LLM |
| F8 | Prompt injection | Quarantined Reader; sanitisation; text can only veto or reduce; injection test set in CI (brief 13) |
| F9 | Key theft | Section 8 |
| F10 | Tax surprise | ETF sleeve in an IRA if fundable (fee unconfirmed); lot ledger; cross-account wash-sale guard; after-tax benchmark; flag lots near one year (brief 19) |
| F11 | Owner override | Section 9 |
| F12 | Broker rule drift | Constraints adapter; typed, never-retried handlers for self-cross, PDT and margin rejections (briefs 12, 21) |
| F13 | Cost erosion | Discretionary trades need expected move ≥3× round-trip cost; rebalance only on >5-point drift or a signal flip (DC) |
| F14 | Self-manipulation | No opposite-side order while one is working; cross-strategy netting (brief 12) |

**Starting numbers for $1k-$10k:** leverage 1.0, no shorting, each ETF ≤30% of the book, crypto ≤10% (later 20%), and a 10% portfolio volatility target (DC). No Kelly or confidence sizing until a strategy has a few hundred outcomes, which a monthly book never reaches (brief 10).

**Catastrophe stops:** about 3× the 20-day ATR for ETFs, and a -25% stop with a -28% limit for crypto (DC). They insure against host death; they are not alpha (brief 17).

**Loss states:**
- A day down 5% → no new entries that day.
- Drawdown beyond the bootstrap p90 → yellow: freeze scale-up, halve risk.
- Beyond p99 → red: back to shadow.
- **25% lifetime loss on deployed capital → HALT**, and a restart needs a fresh G1 (brief 20).

**Kill switch:** `jarvis kill` sets HALT and cancels all orders (`DELETE /v2/orders`). Flattening is a separate step, `jarvis flatten --confirm`. The Alpaca app is the off-host fallback. The switch is drilled weekly in paper (brief 12).

## 7. Validation and promotion gates

Adapted from brief 20, with a failure-first gate added (**GF**):

| Gate | Pass criteria |
|---|---|
| G0 Pre-register | Frozen spec, cost model, lookback grid, registry row; N_eff = max(ONC K, Galwey m) |
| G1 Backtest | ≥20 years pooled; DSR ≥0.95 at N_eff (≥0.90 for a published rule with N_eff ≤5); plateau: ≥80% of neighbours reach ≥0.6× the chosen cell; positive in ≥70% of 5-year windows; doubled costs keep ≥0.75× SR; after-tax comparison with S0 |
| **GF Failure drills** (paper) | All pass: kill mid-order, duplicate id, network drop, stale feed, broker 5xx, partial fill, replace race, reconciliation mismatch, foreign manual order, clock skew, restore from backup, kill switch, dead-man alert reaching the phone |
| G2 Shadow | ≥6 monthly rebalances; 100% replay identity; no unhandled gaps. Not a performance test |
| G3 Paper | ≥3 rebalances overlapping G2; zero reconciliation breaks; pessimistic fills. Not evidence of edge (brief 08) |
| G4 Micro-live | $500-1,000; ≥6 months; ≥20 fills; realised cost ≤1.5× model; drawdown inside bootstrap p95 |
| G5 Scale | 25% → 50% → 100%, ≥6 months per step; tracking error against replay inside band; zero severity-1 incidents. Never justified by live Sharpe |

Each gate transition is a pending approval row carrying the Red-Team pre-mortem, and it expires to reject after 72 hours (DC). An LLM-derived feature gets weight only after a forward ablation on post-cutoff data. The clock restarts whenever the model ID changes (briefs 01, 22).

## 8. Runtime, hosting, storage, monitoring, secrets

- **Host:** the owner's Windows 11 laptop running Task Scheduler jobs (StartWhenAvailable, WakeToRun, RestartOnFailure, AC sleep off), not a daemon (brief 23). Python venv with a lockfile; no Docker (brief 14).
- **Memory:** an estimated 0.3-0.6 GB per run; Streamlit only on demand. Fits in 8 GB.
- **Move to a Google e2-micro VM** (us-central1, $0, systemd timer) **before the first crypto position, or after 2 missed runs in a month** (brief 23). Avoid Oracle (idle reclaim) and Hetzner US ($20.49).
- **Storage:** SQLite WAL (ledger and registry), Parquet and DuckDB (data), git (code and config). The ledger is append-only and each row stores the hash of the previous row, so any edit is detectable (DC).
- **Monitoring:**
  - Healthchecks.io free tier: a daily cron check with a 2-hour grace, plus a separate "stops verified" check.
  - Alerts go out through ntfy or Telegram, and by email (brief 23).
  - Alpaca status-page subscription and a JSON log.
  - A weekly "silence test" that deliberately skips a ping.
- **Secrets:** **first, rotate the v1 key committed in source.** Paper and live keys are separate. The live key sits in a DPAPI user-scope file on one host only, and only from G4. Wallet whitelisting stays off, because a leaked key can add whitelist entries (brief 23). Other measures: a capped Anthropic workspace key, pre-commit secret scanning, no keys in prompts or logs, and BitLocker (brief 13).
- **Deploys:** tagged versions with a config-hash handshake. No deploy while orders are working. The first run after a deploy is at half size. No dead code and no reused flags (brief 12).

## 9. Owner experience

- **Daily (about 0 minutes):** one ntfy status (OK, SKIPPED with a reason, or SAFE/HALT) and the Narrator digest by email. The owner acts only on SAFE or HALT, using the one-page runbook and the Incident Analyst's draft.
- **Weekly (about 20 minutes):** review the Streamlit page: NAV against after-tax S0, risk use, data health, realised against modelled cost, drawdown band, LLM spend and the "cost of overrides" counter. Then run the paper kill-switch drill, and optionally a Strategy Lab session.
- **Monthly:** read the rebalance report. **Quarterly:** review the limits (brief 12).

**Approvals** go through a local CLI with typed confirmation, and they expire to reject. They are needed for each gate transition, a new strategy, loosening any limit, clearing a HALT, moving the host, and the first 3 live rebalances (where the order list is shown first).

**Override controls (F11):**
- Tightening a limit applies at once. **Loosening waits 72 hours, needs a Red-Team note, and starts next session** (DC).
- The owner can veto a trade but never add one. Each veto is logged with its counterfactual P&L.
- A manual trade in the JARVIS account triggers SAFE. Discretionary trading belongs in a separate account, which the wash-sale guard watches.
- The config schema has no return-target field.

## 10. Mapping to the owner's documents

| Owner idea | Status | Reason | Brief |
|---|---|---|---|
| Never chase a target; FLAT is valid | KEPT | Edges are small; enforced in the config schema | 09, 11 |
| Deterministic risk gate, no LLM override | KEPT, extended | Erroneous-order family, reconciliation, dead-man's switch added | 12 |
| Idempotent execution | KEPT, specified | Intent-first, lookup-before-resubmit, poll | 17, 21, 23 |
| Ledger / Layer I | KEPT, promoted to the core product | Plus LLM record-and-replay, tax lots, hash chain | 13, 19, 22 |
| Data contracts first; point-in-time; same code path for backtest and live | KEPT | Bitemporal data, future-poisoning test, replay identity as gate G2 | 06, 14, 20 |
| Paper → shadow → live | CHANGED | G0-G5 plus GF; paper is a plumbing test | 08, 20 |
| Data-trust gate / SAFE state | KEPT | The degraded-data override is DROPPED | 12 |
| 18 agents under a LangGraph supervisor | CHANGED | Code state machine plus 6 Claude roles off the order path | 02, 03 |
| Bull/Bear debate | CHANGED | A single Red-Team call on promotions only | 02 |
| 5-part Confidence Calibrator | DROPPED; outcome model and Kelly DEFERRED | A pooled score cannot be calibrated; data and execution become gates and costs; an outcome model needs a few hundred outcomes | 10 |
| Confidence-drop exits | CHANGED | Pre-registered exits plus broker-resting stops | 17 |
| LONG/SHORT/FLAT | CHANGED | Long/flat: no crypto shorts; equity shorts need $2,000 and whole shares | 05, 11 |
| Intraday, order-flow and L2 alpha | DROPPED | Fees exceed any edge; no equity L2 | 06, 07 |
| Spoofing and wash-trade surveillance | DROPPED | Needs participant data; self-manipulation guard ADDED | 07, 12 |
| Coinbase or a second broker | DROPPED | 3-4x the fees; public feeds kept as a cross-check | 11 |
| Crypto sleeve | DEFERRED | Needs Texas availability, a host move, and S-A at G4 | 21, 23 |
| Model ensemble (HMM, jump, ...); RL | DEFERRED; RL DROPPED | Default outputs leak; volatility model only | 15 |
| News/SEC intelligence layer | CHANGED | Rebuilt from scratch as a risk filter and archive; weight zero. Social sentiment and CAR are dropped (pump surface; leakage) | 16 |
| Wrap v1 | DROPPED | Leakage, leaked key, 123 rows; only the ideas survive | 16, context |
| Docker, Redis, Postgres, Kafka, Grafana | CHANGED | SQLite, Parquet, Task Scheduler; explicit upgrade triggers | 14, 23 |
| Investor view | CHANGED | Owner-only dashboard; legal perimeter | 12 |
| Form 4 overlay, Lazy Prices | DEFERRED | Post-publication decay unverified; slow | 09, 16 |
| Strategy Lab (LLM proposes) | KEPT | Trial registry mandatory; expect low yield | 08, 20 |
| Worked examples ($100, +$0.27) | DROPPED | Costs are 33-113% of the upside | 11 |
| Alerts, daily summary | KEPT | Narrator with a numeric validator | 14, 22 |

## 11. Build order

| Phase | Content | Exit criteria | Usable after |
|---|---|---|---|
| P0 (week 1) | Rotate the v1 key; secret scanning; confirm Texas crypto, the IRA fee and news access; read the customer agreement | Checklist closed | Open questions answered |
| P1 (weeks 2-5) | Ledger, bitemporal ingestion, data-trust gate, news archive, S0 shadow, Healthchecks | 20 clean scheduled runs; future-poisoning test green | Data-health and benchmark dashboard |
| P2 (weeks 6-10) | Order service, risk gate, reconciliation, kill switch, constraints adapter on paper | **GF drills all pass** | A safe paper executor |
| P3 (weeks 8-12, overlapping) | S-A through G0/G1 | Passes, or "hold S0" is declared | A validated strategy, or an honest null |
| P4 (months 3-9) | G2 shadow plus G3 paper; Narrator, then Reader (log-only); Incident Analyst | Replay identity; zero breaks | The full daily owner experience |
| P5 (months 9-15) | G4 micro-live on S-A | Costs ≤1.5× model | Real money, small |
| P6 (month 15+) | G5 scaling; e2-micro host; S-B crypto if conditions hold; weekly Strategy Lab | Per G5 | Full system |

## 12. Growth path

| Unlock | Trigger |
|---|---|
| Reader on more symbols (b1 tier, about $4 a month) | Capital ≥ $2,400 (600× rule) (briefs 11, 22) |
| Sonnet-tier extraction (b2) | Capital ≥ $5,600 **and** a golden-set check passed |
| Reader output given weight | A pre-registered forward ablation on post-cutoff data passes |
| $5 VPS instead of e2-micro | Capital ≥ $3,000, or e2-micro is unreliable |
| Norgate data ($630 a year) for single stocks | Capital ≥ about $31,500 (600× $52.50), or a paper edge needs it (brief 06) |
| SIP real-time ($99 a month) | Capital ≥ about $59,400; daily strategies do not need it |
| Second strategy live | The first has completed G4 |
| Postgres, bus, Grafana | A second concurrent writer or process (brief 14) |
| Shorting, margin, Kelly | Not unlocked inside $10k |

## 13. Three biggest risks of this proposal

1. **There may be no edge to protect.** S-A's honest expectation is -1 to +1 point a year against holding the same assets, before the tax hurdle (briefs 18, 19). *What proves it:* S-A fails G1 against an after-tax S0. JARVIS then runs S0 as a disciplined, audited rebalancer. That is still useful, and the owner should know it is a likely outcome.
2. **The controls may cost more than they save.** False skips could miss a rebalance, IEX-only prices could trip collars, and stops could sell at the bottom of a gap. A solo developer could also burn 10 weeks on plumbing, then bypass it. *What proves it:* during G2-G4, the measured cost of controls (skipped-rebalance tracking error, stop-outs compared with no stop, override counterfactuals) exceeds an agreed share of S0's return. P2 still unfinished at week 12 is another sign.
3. **It under-delivers the owner's "AI agents" vision.** Claude never decides, so the owner may bolt on an LLM trader outside the gates. *What proves the design too cautious:* a pre-registered forward ablation on post-cutoff data shows an LLM signal improving after-cost results. That signal would then enter through G0-G5 like any other plug-in.

# Proposal B: Evidence-minimal JARVIS

Architect B. Written 2026-10-01. Brief numbers refer to `research/01-23`; "gap" refers to `00-gap-analysis.md`.

## 1. Thesis

JARVIS-B is a once-a-day, run-to-completion Python job on the owner's laptop. It holds a long/flat, volatility-capped trend book of 4-6 liquid ETFs, plus a small conditional BTC/ETH trend sleeve. Every order passes a deterministic risk gate, is protected by stops resting at the broker, and is written to an auditable ledger. The benchmark is a static rebalanced allocation of the same assets after cost and tax.

Claude agents build the code, audit and explain each week, and generate hypotheses offline into a registered trial log. They never choose, size or exit a position. Production runs with the LLM off, at $0.

The evidence leaves little room for anything bigger:
- No LLM trading agent has beaten buy-and-hold net of costs after its training cutoff (brief 01).
- Multi-agent debate does not beat one call (brief 02).
- Free data supports only daily-to-monthly horizons (brief 06).
- Intraday trading is fee-negative at $1k-$10k (briefs 07, 11).
- Fixed costs above capital/600 a month consume the edge (brief 11).
- Neither paper nor live Sharpe can validate anything within a horizon the owner would tolerate (brief 20).

The honest goal is risk reduction at roughly benchmark returns (brief 18), from a system that cannot blow up and that grows only by passing gates. A system this small is also one a solo developer can get right.

## 2. End-to-end flow

Each step is labelled **[CODE]** (deterministic code), **[STAT]** (statistical model) or **[CLAUDE]** (Claude agent). Steps 1-13 make up the job. Task Scheduler runs it at 10:15 ET (execution, when orders are pending) and at 16:45 ET (data, signals, report), each with a retry an hour later (brief 23).

1. **[CODE]** Take the single-instance lock and send a Healthchecks.io start ping (brief 23).
2. **[CODE]** Reconcile against Alpaca REST; the broker is the source of truth. Any mismatch sets HALT (exits only) and sends an alert (briefs 12, 21).
3. **[CODE]** Ingest Alpaca and Tiingo daily bars (plus Coinbase/Kraken public data for crypto). Store raw bars with corporate actions and `event_time` / `vendor_time` / `ingest_time` (brief 06).
4. **[CODE]** Data trust gate. Bars must be fresh, the two sources must agree on the close within 1%, and there must be no missing session or halt. On failure the state becomes DATA-UNTRUSTED: no new risk, while exits and stop re-arming continue. There is no override (gap section 5).
5. **[STAT]** Volatility forecast: a 60-day EWMA of realised volatility. HAR or GJR-GARCH is a registered upgrade, adopted only if it lowers out-of-sample error (brief 15). It is used for sizing only.
6. **[CODE]** Signals.
   - A: at month-end, is the close above its 10-month SMA?
   - B: the daily 20/30/60/90-day Donchian state (brief 18).
7. **[CODE]** Target weights. Apply volatility and sleeve caps and the leverage cap of 1.0. Round to whole shares, put the residual in a T-bill ETF, and apply a 20% no-trade band (brief 18).
8. **[CODE]** Cost gate. Drop any trade whose expected spread and fees are too large relative to the weight change (briefs 10, 11).
9. **[CODE]** Hard risk gate (section 6). It is default-deny and every outcome gets a reason code (brief 12).
10. **[CODE + owner]** In early live stages, risk-increasing orders wait for approval, as pending rows that expire to *reject*. Risk-reducing orders never wait.
11. **[CODE]** Execute.
    - Write the intent row, then submit a marketable limit order with a deterministic `client_order_id`.
    - After a timeout, look the order up by its ID before any resubmit.
    - Poll to a terminal state, then re-arm the GTC catastrophe stops (brief 21).
12. **[CODE]** Ledger row (decision, data hash, config hash, fill, cost against the model, tax lot, wash-sale flag; brief 19) and a templated status email.
13. **[CODE]** Healthchecks success or fail ping; release the lock.
14. **[CLAUDE]** Weekly review, owner-attended (R1).
15. **[CLAUDE]** Monthly research session (R2). Its output goes into the trial registry, and the gates in section 7 decide.
16. **[CLAUDE, deferred]** Nightly event extraction (E1): shadow only, zero weight.

## 3. Agent roster

**No Claude agent sits on the order path.** Claude does engineering, audit, explanation and research, the roles where evidence shows LLM value (gap conclusion 3). Every call is recorded for replay: model ID, full request and response, prompt hash and usage (brief 13). Because the core has no LLM dependency, a lapsed plan or an API outage does not affect the money.

| Agent | Job | Trigger | Model tier | Inputs | Structured output | Forbidden | Est. monthly cost |
|---|---|---|---|---|---|---|---|
| **B0 Builder** | Writes and tests code; runs failure drills; keeps the runbook | Owner-started Claude Code sessions | Opus/Sonnet 5.5 on the owner's plan | Repo, tests, paper logs | Commits, green tests, drill report | Seeing live keys; deploying with open positions; editing `risk_config` without an owner-signed commit | $0 extra on an existing Pro plan; otherwise ~$20 (Pro) or ~$3 per session on the API (brief 22) |
| **R1 Weekly Reviewer** | Audits the week: reconciliation breaks, data-trust trips, cost against the model, drawdown bands, replay identity, missed runs. Explains P&L against the benchmark | Weekly, owner-attended, read-only database access | Sonnet 5.5 (plan) | Ledger, run log, gate log, registry | `weekly_review.json` (incidents, cost_ratio, band_status, approvals, questions) plus a one-pager | Recommending trades or sizes; writing anywhere except `reviews`. It is an auditor, not an adviser (Consumer Terms, brief 22) | $0 on plan; ~$12.8 on the API (brief 22) |
| **R2 Strategy-Lab Researcher** | Drafts G0 specs and backtest code; one red-team pass on its own spec; logs **every** variant | Monthly, owner-attended | Opus 5.5 (plan) | Notes, registry, backtester | `g0_spec.yaml` plus registry rows | Touching live config; leaving any trial unlogged. Expected yield is very low (brief 08) | $0 on plan; ~$3 per session on the API |
| **E1 Event Sentry** (DEFERRED) | Extracts event type and severity from fund/issuer 8-Ks and crypto venue/regulatory news | Nightly Batch API, after the capital trigger | Haiku 4.5, then its successor (~2.6x) | EDGAR items; Alpaca news (probed at start-up) | `{symbol, event_type, severity 0-3, evidence_quote, source_id}`, Pydantic-validated, fails closed | Any effect on orders before it passes a forward test. After that it may only *tighten* risk | ~$4 (brief 22, b1); ~$10 on a successor |

**What happens to the owner's 18 v3 agents.** They become deterministic code or simple statistics. Code is cheaper, testable and replayable, and no evidence shows an LLM adds value in these roles (briefs 02, 03, 10, 15).

| v3 agent | Becomes | Why |
|---|---|---|
| Orchestrator | Job script with an explicit state machine | One process (briefs 02, 23) |
| Goal & Capital Planner | `owner_config.yaml` plus a printout of the benchmark's expected range; no return-target field | Brief 18 |
| Opportunity Scanner | Fixed-universe signals | 30-symbol free data (brief 06) |
| Data Trust | Code gate | Brief 14 |
| Market/Technical | Signal code | Closed-form rules |
| Flow/Microstructure | **Dropped** as alpha; a spread check remains | Brief 07 |
| News & Event | EDGAR item watcher (code); E1 **deferred** | Brief 16 |
| Fundamental/Macro | **Deferred** | No launch use |
| Crypto | Sleeve B code | Brief 18 |
| Manipulation Surveillance | **Dropped**; liquid-only allow-list | Brief 07 |
| Bull/Bear | **Dropped**; one red-team pass inside R2 | Brief 02 |
| Model Ensemble | One volatility model | Brief 15 |
| Confidence Calibrator | **Dropped**; base rates with n | Brief 10 |
| Strategy/Portfolio | Weight combiner (code) | Deterministic |
| Capital Governor | Code (kept) | Brief 12 |
| Execution | Idempotent order service (kept) | Brief 21 |
| Position Manager | Pre-registered exits plus broker stops | Brief 17 |
| Ledger/Review | SQLite ledger plus Claude R1 | The one review role where an LLM clearly helps |

## 4. Strategies and universe at launch

- **Strategy 0, the benchmark (always admissible).** A static allocation of the same ETFs, rebalanced quarterly. It claims no alpha, so it needs only the plumbing gates (G2-G4). If nothing passes G1, JARVIS runs Strategy 0, and that counts as a valid outcome.
- **Strategy A, ETF trend.** Faber 10-month SMA, long/flat, at month-end. Each asset is ON (volatility-capped) or OFF (into the T-bill ETF), with about 3-4 round trips a year (brief 18).
  - Universe: US equities, developed ex-US equities, Treasuries, REITs, gold or commodities, plus a T-bill ETF.
  - Four assets at $1,000; up to six at $10,000.
  - Share classes are chosen so that whole-share rounding stays under 10% of each target weight.
  - Expectation: -1 to +1 point a year of CAGR against Strategy 0, with about half the drawdown. The evidence is contested: Huang et al. (brief 18).
- **Strategy B, crypto trend (CONDITIONAL).** A BTC/ETH Donchian 20/30/60/90 ensemble, long/flat, daily close, limit orders, sleeve capped at 20%. Cost is about 0.7-1.2% a year (brief 18, verified). Net Sharpe is unknown, because the evidence is one working paper. It goes live only if all three hold:
  - Texas eligibility is confirmed (brief 21).
  - It passes G1 inside the pooled book (brief 20).
  - An execution route is chosen. Preferred, if verified: spot BTC/ETH ETFs, which trade at equity cost, take whole-share GTC stops and are IRA-eligible (brief 21, unresearched). Fallback: Alpaca spot on a Linux host.
- **Volatility targeting** is a sizing governor on A and B, not a strategy (brief 18).

**Adding strategies.** The only route is a G0 spec in the append-only registry, written by R2 or the owner. The backtester computes N_eff across all registered trials (brief 20), and the spec then climbs G1 to G5.

## 5. Data plan

| Need | Source ($0 each) | Point-in-time handling |
|---|---|---|
| ETF bars, live | Alpaca Basic (IEX real-time; SIP history older than 15 minutes, from about 2016) | Raw bars plus a corporate-action table, adjusted as of the decision date. Never train on a re-downloaded adjusted series (brief 06) |
| 20+ year history | Tiingo Starter EOD (30+ years) | Same rule. Index proxies from before ETF inception are unverified (brief 20) and flagged in every G1 report |
| Second source | Tiingo against Alpaca closes | IEX against SIP is not a valid pair (brief 06) |
| Crypto | Alpaca bars; Coinbase/Kraken public data as a check | Fixed UTC daily cut |
| Cash rate | FRED T-bill series | ALFRED vintages if macro is ever used |
| Events (deferred) | EDGAR acceptance times and 8-K items; Alpaca news | Use only rows with `ingest_time` at or before the decision time (brief 16) |

Storage:
- Parquet by `source/symbol/year`, under 1 GB.
- SQLite in WAL mode with one writer for state, intents, ledger, registry, approvals and LLM records (brief 14).
- A nightly copy of both to a second disk.

Backtest and live call the **same** functions on the same as-of data; the G2 replay-identity test proves it. No v1 data or model is reused, because of v1's leakage and its 123 rows. The leaked key is rotated first.

## 6. Risk gate, sizing and exits

Values marked † are design choices, not evidence. All of them are simulated in G1 and changed only by an owner-signed config commit that takes effect next session (brief 12).

| Control | $1,000 | $10,000 |
|---|---|---|
| Account | Leverage 1.0; `no_shorting` at the broker and in the gate | same |
| Allow-list | 4 ETFs + T-bill ETF | 6 ETFs + T-bill ETF (+ BTC/ETH if B passes) |
| Max weight per asset | 30%† | 25%† |
| Crypto sleeve | Off | ≤20% (brief 18) |
| Portfolio volatility target | 10% a year ex ante†; weight = min(cap, risk share / forecast vol) | same |
| Per-order notional cap | $350† | min(30% of equity, $3,000)† |
| Daily traded notional | ≤100% of equity on rebalance days, ≤25% otherwise† | same |
| Order rates | ≤20 orders a day, ≤5 cancels a minute, ≤12 open† | same |
| Price collar | Within 0.5% (ETF) or 1.5% (crypto) of a quote no older than 60 s; otherwise block† | same |
| Duplicates | `client_order_id` = hash(decision, leg, attempt); same symbol and side within 10 minutes blocked; no self-cross | same |
| Intraday | Down >5% since the prior close → reduce-only† | same |
| Drawdown bands | Yellow at bootstrap p90 (about 15% at 1 year): freeze scale-ups, halve risk. Red at p99 (about 23%): reduce-only, back to shadow (brief 20) | same |
| Lifetime stop | 25% loss of deployed capital: flatten, halt, manual re-arm (brief 20) | same |

**Sizing** uses fixed volatility-capped weights. There is no confidence or Kelly scaling, because a monthly book never collects the few hundred calibrated outcomes that requires (brief 10). Positions are whole shares only, so every overnight position can carry a resting stop (resolving gap contradiction 15).

**Exits** are pre-registered and included in the backtest. There is no "confidence fell" exit (brief 17).
- A: the month-end signal flip, or a whole-share GTC catastrophe stop at 3x ATR(20)†, re-armed each run before the 90-day expiry (brief 21).
- B: the Donchian midpoint ratchet, plus a GTC stop-limit (brief 23).

**Around the gate:**
- `jarvis kill` is a separate script that cancels everything and blocks new orders; flattening is a separate command; it is drilled weekly in paper.
- A Healthchecks dead-man's switch with a 2-hour grace period alerts by email and ntfy.
- Exits within 30 days of the one-year mark are flagged; a cross-account wash-sale guard runs (brief 19).

## 7. Validation and promotion gates

These follow brief 20, because count-based paper gates cannot be passed by a monthly book.

- **G0 Pre-register.** A frozen spec with a grid of at most 6 values. Every trial goes in the append-only registry.
- **G1 Backtest.** All must hold:
  - net Sharpe measured on at least 20 years of pooled monthly data;
  - DSR ≥0.95 at the registered N_eff (0.90 for a published design with N_eff ≤5);
  - a plateau: at least 80% of neighbouring cells reach ≥0.6x the chosen cell, and the chosen cell is not the grid maximum;
  - the asset-class holdout positive in at least 70% of assets;
  - positive in at least 70% of 5-year windows;
  - with costs doubled, Sharpe at least 0.75x;
  - plus a benchmark gate added by this proposal: after-tax CAGR within 1 point of Strategy 0 *and* max drawdown at most 0.7x Strategy 0's.

  A failure is logged and the book stays on Strategy 0.
- **G2 Shadow.** At least 6 rebalances, 100% replay identity, no unhandled gaps.
- **G3 Paper.** At least 3 rebalances overlapping shadow, with the paper balance equal to the real capital. Zero unreconciled breaks. Three drills passed: crash mid-rebalance, duplicate ID, stale feed. Paper P&L is not evidence (brief 05).
- **G4 Micro-live.** $500-1,000 for at least 6 months and at least 20 fills. Realised cost at most 1.5x the model; drawdown inside the p95 band.
- **G5 Scale.** 25% → 50% → 100%, at least 6 months per step, each approved by the owner. Live Sharpe is never the reason for a step.

Strategy 0 skips G1. E1 needs its own forward test on post-cutoff data, restarted whenever the model changes (brief 22).

## 8. Runtime, hosting, storage, monitoring, secrets

- **Runtime.** Python 3.12, one run-to-completion process, peak RAM under about 500 MB. There is no Docker, Redis, Postgres, MLflow or LangGraph: none of them prevents a failure this system can have (brief 14). Streamlit runs only when the owner opens it.
- **Host.** The laptop under Task Scheduler (WakeToRun, StartWhenAvailable, RestartOnFailure, no sleep on AC power). It costs about $2.64 a month in power (brief 23). The job moves to a $0 GCP e2-micro (or a $4-6 VPS) before the first 24/7 crypto position, or after 2 missed runs in a month.
- **Monitoring.** Healthchecks, a JSON-lines run log, a gate log with reason codes, and the daily email.
- **Secrets.** DPAPI user-scope. Separate paper and live keys, with the live key on one host only. No key in the repo or in any Claude context. Transfers are disabled at the broker where possible (brief 12).
- **Monthly cost:** $0 for data and LLM.

## 9. Owner experience

- **Daily (0-2 minutes).** One email: "OK - no trades", or a short trade summary with cost against the model. A phone alert comes only on a missed run, HALT, a data-trust trip or a band breach.
- **Weekly (about 30 minutes).** Run the R1 session, read the one-pager, and clear approvals (`jarvis approve <id>` or Streamlit).
- **Monthly.** The rebalance email, and an optional R2 session.
- **Approvals.** Each is an expiring pending row:
  - stage promotions, scale steps and new strategies;
  - `risk_config` changes;
  - re-arming after a halt;
  - risk-increasing orders in the first 3 live rebalances.
- **No bare "confidence %"** is shown. Base rates carry n and an interval, and are hidden below about 100 cases (brief 10).

## 10. Mapping to the owner's documents

| Owner idea | Verdict | Reason (brief) |
|---|---|---|
| Never chase a target; FLAT is valid; rules hold the money | KEPT | 01, 09, 11 |
| Hard Risk Gate plus kill switch | KEPT + erroneous-order controls, reconciliation, dead-man's switch | 12 |
| Volatility targeting and drawdown limits | KEPT as volatility caps and bootstrap bands | 10, 20 |
| Fractional Kelly / confidence sizing | DEFERRED; the monthly book never reaches the sample size | 10 |
| "upside x p > loss + cost + penalty" | CHANGED to a cost gate plus fixed weights | 10, 11 |
| Strategy Lab, with validation deciding | KEPT as R2 plus registry and DSR | 08, 20 |
| Data contracts, event vs ingest time, one code path | KEPT | 06, 14 |
| Data Trust / SAFE state | KEPT; degraded-data override DROPPED | 12 |
| Paper → shadow → live, idempotent execution | KEPT + micro-live and slow-strategy gates | 20, 21 |
| Ledger with versions and attribution | KEPT + tax lots + LLM record-and-replay | 13, 19 |
| 18 agents under LangGraph | CHANGED to code + 2 attended Claude roles + 1 deferred | 02, 03, 13 |
| Bull/Bear debate; overall confidence calibrator | DROPPED | 02, 10 |
| "Confidence fell → exit" | CHANGED to pre-registered exits plus broker stops | 17 |
| Order-flow/L2 alpha; intraday BTC/ETH examples | DROPPED | 07, 09, 11 |
| Manipulation surveillance | DROPPED; liquid allow-list | 07 |
| LONG/SHORT, multi-horizon, always-on scanner | CHANGED to long/flat, ETF monthly + conditional crypto daily | 05, 06, 18 |
| Model ensemble (HMM, jump, …); RL | One volatility model; the rest DEFERRED; RL DROPPED | 15 |
| News/SEC/FinBERT layer; Form 4/13F | DEFERRED (E1 as a risk filter; Form 4 at the data trigger); v1 rebuilt, not wrapped | 09, 16 |
| Coinbase second broker | DROPPED (fees 2-4x); public data kept as a check | 11 |
| Docker/Redis/Postgres/MinIO/Feast/Grafana/React; always-on laptop | CHANGED to SQLite + Parquet + Streamlit and a scheduled job | 14, 23 |
| "Investor" dashboard | CHANGED to owner-only | 06, 12 |
| Daily summary, alerts, approvals | KEPT (templated; approvals expire) | 08, 14 |

## 11. Build order

| Phase | Work | Exit criterion | Usable afterwards |
|---|---|---|---|
| P0 (week 1) | Rotate the leaked key. Alpaca paper account. Confirm Texas crypto eligibility, IRA eligibility (brief 19) and API behaviour (brief 21). Healthchecks | Accounts verified; secrets in DPAPI | Nothing yet |
| P1 (weeks 2-4) | Ingest, store, backtester, registry; G0/G1 for Strategies 0 and A | G1 verdict recorded | An honest research tool |
| P2 (weeks 5-8) | Runner, reconciliation, gate, order service, ledger, kill and dead-man switches, email | Shadow running, 100% replay | Automated "what I would do" reports |
| P3 (months 3-6) | Paper alongside shadow; drills; R1; Streamlit | G2 + G3 | A full system on paper |
| P4 (months 7-12) | Micro-live | G4 | Real money at minimum size |
| P5 (months 13-30+) | Scale steps; B track if its conditions are met | G5 per step | Full intended capital |

## 12. Growth path

The rule: recurring spend is allowed only when **capital ≥ 600x the monthly cost** (brief 11).

| Trigger | Unlocks |
|---|---|
| Capital ≥ $2,500 | E1 in shadow, Haiku-tier batch (~$4 a month), in a dedicated workspace with a $5 limit (brief 22) |
| Capital ≥ $5,600 | E1 on a Sonnet-tier successor (~$9.4 a month) |
| E1 passes its forward test | E1 may block entries on severe events |
| 2 missed runs in a month, or B on spot crypto | $0-6 Linux host |
| IRA eligible and fee confirmed | Sleeve A moves into the IRA, removing the ~1-1.5 point tax hurdle (brief 19) |
| Capital ≥ ~$31,500 (Norgate $630 a year ≤2%) | Single-stock momentum and the Form 4 overlay become eligible for G0 (briefs 06, 09) |
| Never at this scale | SIP real-time data, L2, intraday trading, shorting |

## 13. Three biggest risks, and what would prove this proposal wrong

1. **There may be no edge to manage.** A may add nothing over Strategy 0 after tax (Huang et al., brief 18), and B rests on one working paper. JARVIS would then be a well-engineered rebalancer. *Proof against this proposal:* a richer design produces a strategy that passes G1 at a comparable N_eff, which this design could never have found. A simply failing G1 does not count, because the proposal falls back to Strategy 0.
2. **Operational fragility.** It runs on a single laptop. Several broker behaviours are untested: the duplicate-ID response, GTC stop expiry, whole-share rounding at $1,000 and Texas crypto availability (brief 21). *Proof:* more than 2 missed runs a month, any break in G3, or realised cost above 1.5x the model in G4. Any of these forces the VPS move or an execution redesign.
3. **The AI is under-used and the owner disengages.** Claude stays off the money, and full size takes 18-30 months. If LLM text features do carry forward value, this design leaves it on the table, and a bored owner may bypass the gates. *Proof:* E1's forward test clears its threshold by a wide margin, or the approval log shows overridden gates or skipped reviews. Either means the agents need more responsibility, or the owner needs more visibility.

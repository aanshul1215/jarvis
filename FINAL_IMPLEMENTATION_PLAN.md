# JARVIS AI | Final Implementation Plan

**Version:** 2.0 | **Prepared:** 15 October 2026 | **Repository:** `https://github.com/aanshul1215/jarvis` | **Base:** `branch-1` (`0da7e0858a170cb1fac37bdffed95d984bea694f`, verify before editing) | **New delivery branch:** `branch-3` (create from the current `branch-1`; not yet present at last check)

**Document type:** Canonical engineering and research handoff for the owner, technical teammate, and Codex. **Status:** Proposed implementation plan, not running software or approved live-trading authority.

> **Operating principle:** Research deeply, recognize quickly, trade only validated setups, enforce risk in code, and learn from both trades and missed opportunities. JARVIS is intended to become a disciplined, automated *personal* trading desk—not an unregulated hedge fund, not a guaranteed-profit system, and not 18 LLMs deliberating on each order.

## 0. Read this first: what is already true

**Branch protocol.** `branch-1` is the October 8 autonomous design baseline; `main` is historical and must not be silently merged into this work. `branch-3` is the new *documentation and execution-planning branch*, created FROM `branch-1` after verifying latest remote state. Never imply a branch or commit exists until Git confirms it. Preserve old decisions and supersede them explicitly in this final plan. First Codex pass adds documentation ONLY. Human-approved implementation PRs follow later.

**Five October 15 owner refinements (now mandatory design inputs):** (1) Alpaca **Basic/free first** with attribution for feed entitlements, coverage, delays, local inference and broker execution, then a measurable upgrade assessment; (2) lightweight **local CSV, Parquet, JSON and append-only JSONL**, with optional Excel reports and rigorous schemas; (3) **Bayesian evidence updating** and a tail-aware trading utility objective—not raw classification accuracy—with strong out-of-sample and latency evaluation; (4) **AI-generated implementation code with enforceable engineering controls**, a root `EXECUTION.md` task register and root `LOG.md` audit trail; (5) comprehensive **user-input, paper account, key setup, and broker/crypto eligibility checklists**. See sections 4A, 5A, 6A, 9A and 10A. The file-based storage decision in section 5 supersedes the attached draft's database proposal for V1.


The `branch-1` repository remains a **design and research repository**. Its October 8 revision restores **18 logical responsibilities**, not 18 deployed autonomous agents. The current execution engine, broker adapter, automated research laboratory, model registry, and proposed trading-desk UI have not been implemented. `legacy-v1/` contains a TSLA reference prototype and known data leakage; it is **not** a production starting point. The older `ARCHITECTURE.md` describes a historical manual/monthly proposal; `AUTONOMOUS_ARCHITECTURE.md` and `docs/04-autonomous-design/` are the active design direction. Do not delete or silently rewrite the evidence trail.

**Non-negotiable decisions**

1. **Paper-first and no live-by-default.** No real-money connection, trade permission, live secret, or live endpoint in the development environment. Each transition to live needs explicit owner approval and objective readiness evidence.
2. **Owner-only, long/flat initially.** Liquid US equities and, *only if eligibility is verified*, spot BTC/ETH. No options, leverage, short selling, broad altcoins, or high-frequency execution at initial launch.
3. **Two clock speeds.** A lean, priority-protected live decision path and a separate scheduled/low-priority research path. Collect data continually where permitted; do not run historical backtests on every market tick.
4. **One operating architecture, separate asset-class pipelines.** Equity and crypto features, clocks, data quality, venue rules, models, and strategy evaluations remain distinct. One cross-asset portfolio view and Governor enforce shared risk limits.
5. **Both discovered and conventional opportunities.** Detect interpretable patterns (opening gaps, candlesticks, volume, breakout/continuation, event response), statistical/ML relationships, and unusual events. New discoveries enter a hypothesis register, **not** live execution.
6. **No generative text in the live authorization path.** LLMs can help research, summarize, argue bull/bear cases, draft tests, and propose hypotheses. Only versioned, approved strategies plus deterministic capital/risk/execution code may order.
7. **Observe failures and nontrades.** Store every candidate, supporting evidence, contradictions, `FLAT`/rejection reason, model decision, order/fill, and later hypothetical or realized outcome. Keep hypothetical P&L separate from actual P&L.
8. **Stable, auditable, reversible software.** Persist decisions before broker submission; use client-generated idempotency IDs; reconcile broker truth on startup and after activity; rollback models and suspend strategy families without changing account records.
9. **Lean first.** The repository assumes a Windows 11 laptop with approximately 8 GB RAM and near-zero metered spend; confirm the teammate's actual OS, memory, storage, and network access. Do not introduce Kubernetes, Kafka, GPU inference, or multiple databases without measurement.
10. **Outcomes matter more than complexity.** Predictive metrics, net-of-cost strategy results, drawdowns, calibration, latency, and operational correctness count; the number of agents, hypotheses, or executed trades does not.

### What success looks like

A reproducible, telemetry-instrumented paper trading system that can (a) collect and replay point-in-time market data, (b) detect and rank candidate opportunities without inventing tradable edges, (c) test new hypotheses without look-ahead, (d) execute selected *approved* strategies automatically within an owner-signed risk envelope, (e) recover from outages without duplicate orders, and (f) explain every execution and no-trade in a lightweight desk UI. **Profitability is a separate empirical hypothesis, not a project acceptance criterion that can be guaranteed.**

---

## 1. Product charter and system boundaries

**Owner goal.** An autonomous, opportunity-seeking, risk-averse trading desk for the owner's own capital, starting from a small account (repository reference: approximately $1,000–$10,000), with future scalability. Scan intelligently rather than chase a daily return target. First test horizons: **hours to days**; shorter trading is a later evidence- and infrastructure-dependent research question.

**Live decision chain (trading path is independent of heavy training):**

`Market/broker/event feeds → Data Trust → incremental feature snapshots → cheap universe scan → candidate shortlist → approved strategy evaluation → portfolio comparison → deterministic Governor → durable order intent → broker adapter/reconciliation → managed exit → decision ledger`.

**Independent research chain:**

`Historical + new point-in-time data → pattern/hypothesis discovery → candidate strategy specification → leakage-resistant backtest → out-of-sample tests → shadow/paper observation → independent review → versioned approved registry`.

**Background information chain:**

`SEC filings / permitted news / macro / optional social → deduplicate → identify entity → timestamp first availability → classify/summarize → quality check → publish optional features`. This lane must *never* block a price-only strategy or a protective position-management decision.

**Recommended initial modes:** `OFF`, `OBSERVE`, `SHADOW`, `PAPER`, `SAFE`, `HALT`; `LIVE` is present as a disabled configuration state only until a separate owner-approved launch. `SAFE` prevents new risk, permits only explicitly tested and broker-reconciled risk-reduction behavior, and requires reconciliation before resuming. `HALT` requires owner intervention. A power loss means software-based stops cannot be assumed to operate while offline.

### Scope boundaries for the first implementation

**In scope:** equities scanner; BTC/ETH data lane with trading disabled pending eligibility; selected transparent pattern detectors; baseline strategies; backtest/replay; separate validation; paper broker integration; portfolio Governor; operating ledger; basic read-only UI; monitoring and recovery; strategy/hypothesis registry.

**Later, only after evidence:** cross-asset ML selection, larger market universe, deeper news/event intelligence, automated strategy research at scale, more crypto assets/venues, premium SIP data, hosted uptime, order-book research, advanced portfolios. **Never assume** complex models add an edge.

**Out of scope for v1:** production hedge fund operations, client accounts, discretionary external money management, broker-dealer activities, guaranteed income, autonomous modification of hard risk limits, a self-modifying order path, LLM-generated direct orders, HFT, or automated live capital increases.

---

## 2. Access, accounts, data rights, and prerequisite checklist (Phase A0)

**Use Alpaca's Trading API for an individual account—not its Broker API designed for brokerage/platform partners.** One Alpaca Trading API account may cover equities and supported spot crypto, but **crypto enablement is not automatic**. The account, Texas eligibility, available instruments, actual exchange/venue, supported order types, fees, and quote access must be checked via current documentation and a read-only account/capability probe. A second crypto broker is **not initially required**; add one only if there is a verified unmet need and a separate approved integration review.

| Requirement | Exact owner/teammate action | Evidence to record | Release consequence |
|---|---|---|---|
| Alpaca account | Owner creates/controls account; complete identity, residency, tax and account requirements; verify Trading API support. | Non-sensitive pass/fail; no account ID in Git. | Without an eligible account, use local mock/paper only. |
| Paper credentials | Owner provisions **paper-specific** key/secret; teammate configures OS secure store outside repo. | Auth + read-only `get_account`, fake-paper-only order exercise. | Paper mode default; never silently switch endpoints. |
| Live credentials | **Do not provision to Codex or teammate during initial work.** Owner alone retains credentials. | Separate owner-held launch checklist, not a repository secret. | `LIVE=false` until explicit approval. |
| Equity data | Check Alpaca Basic entitlements, IEX real-time vs delayed consolidated SIP, historical bar coverage, corporate actions, rate/connection limits. | Feed and freshness probe plus sample bar/quote. | Do not build an opening-second consolidated-volume strategy on IEX-only data. |
| Crypto | Check account/region permissions including Texas, BTC/USD and ETH/USD tradability, venue (`us` vs applicable `us-1`), market data, decimals, min size, fees, overnight execution and allowed order types. | Explicit *read-only* per-symbol capability matrix. | Crypto execution disabled until all relevant checks pass. |
| Fees and frictions | Verify current spread, maker/taker fees, min order, slippage estimates, equity regulatory fees where applicable, and tax/account constraints. | Dated cost-model assumptions by asset/venue. | No promotion without cost model; don't hardcode stale fee tables. |
| News/filings/macro | Official SEC submissions/XBRL, FRED if useful, permitted RSS/news; assess coverage, latency, attribution, retention and redistribution rights. | Source register: licence, timestamp semantics, rate limit, fallback. | Missing optional source does not block unrelated strategies. |
| Hardware/OS | Verify Windows/macOS, Python version, RAM, free disk, power/sleep behavior, clock sync, network stability, restart policy. | Local environment and liveness checklist (redacted). | Limit compute and data volume; do not claim 24/7 operation on a laptop. |
| Security | Revoke legacy exposed search/OpenAI keys if still valid; `.gitignore`, secret scanner, dependency pinning, OS key store, no chat paste. | Secret-scan clean; rotation checklist. | Block integration work until cleared. |
| Financial/rule scope | Verify own-account setup, applicable broker restrictions, settlement/cash limitations, day-trading/margin rules, tax treatment, and market-data licensing with current sources. | Dated rule and account-type register; unresolved items marked OPEN. | Never assume a past research brief remains legally current. |

**Provider claims from the supplied plan (not independently account-verified in this documentation pass; re-check before implementation):**

- Alpaca distinguishes paper (`https://paper-api.alpaca.markets`) and live (`https://api.alpaca.markets`) endpoints, with separate credentials. **Paper/live selection must not be toggled by a casual environment typo.** Source: https://docs.alpaca.markets/us/v1.1/docs/authentication-1
- The free/basic equity plan's real-time feed is IEX-only; Alpaca documents `iex`, `sip`, and `delayed_sip` streams with entitlement checks. Record actual feed/latency in every event. Source: https://docs.alpaca.markets/us/docs/about-market-data-api ; https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data
- Alpaca's crypto market-data documentation describes distinct location/venue feeds such as `us` and `us-1`. **Texas and account-level crypto trading eligibility remain unverified** until the account capabilities and current supported-regions policy have been checked; verify execution venue as well as data venue. Source: https://docs.alpaca.markets/us/docs/real-time-crypto-pricing-data
- Alpaca supports spot crypto 24/7; order types/fees differ from equities, including crypto maker/taker charges; no crypto shorting/margin in the referenced spot documentation. Check current order specifications and fee posting behavior. Source: https://docs.alpaca.markets/us/docs/crypto-trading ; https://docs.alpaca.markets/us/docs/crypto-orders
- SEC EDGAR submissions and XBRL APIs supply machine-readable filings and company facts. Preserve filing first-availability times and subsequent revisions. Source: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- Paper execution does **not** replicate latency slippage, market impact, queue position, or live conditions. A paper success is a software-readiness milestone, not evidence of net live alpha. Source: https://docs.alpaca.markets/us/v1.4.2/docs/paper-trading

**Phase A0 deliverable:** `docs/05-final-implementation/PROBE_REGISTER.md` with columns `dependency / required for / probe procedure / observed evidence / checked_at / pass-fail-open / fallback / owner`. No fabricated account probes or hardcoded capabilities.

---

## 3. Trading desk organization: preserve all 18 responsibilities

The five desk groups below are *coordination areas*. The **18 numbered responsibilities** correspond to the current `branch-1` decision record. They need not each be a standalone LLM, process, or paid API request. Build deterministic functions for speed-critical mathematics and money-critical actions; consider LLM tools for **offline** reasoning and interpretation.

| # | Responsibility / desk home | Inputs → outputs | Proposed implementation | Execution frequency / authority |
|---|---|---|---|---|
| 01 | **Orchestrator / Supervisor** — Operations | Schedules, states, pending work → durable work routing | Python state machine, bounded queues | Continuous; no discretionary order power |
| 02 | **Goal & Capital Planner** — Risk | Owner constraints, equity/cash → signed risk envelope | Deterministic policy + portfolio math | On approved policy change |
| 03 | **Opportunity Scanner** — Intelligence | Cheap market features → expiring candidates | Fast vectorized rules and ranker | Per completed bar / approved event |
| 04 | **Data Trust Agent** — Intelligence | Raw source events → clean/quarantined records | Typed schemas, integrity/time checks | At ingestion; can block unsafe data |
| 05 | **Market / Technical Agent** — Intelligence | Price/volume → trends, gaps, candles, volatility | Python incremental feature engine | Per relevant bar |
| 06 | **Flow / Microstructure Agent** — Intelligence | Quotes/spreads/venue liquidity → execution estimates | Spread and venue checks; L2 optional | At candidate and order time |
| 07 | **News & Event Agent** — Intelligence | News, SEC, RSS → typed event features | Background parser, optional LLM, source links | Asynchronous, not blocking live queue |
| 08 | **Fundamental / Macro Agent** — Intelligence | SEC/XBRL, FRED → company/macro features | Point-in-time data adapters and models | Filing or scheduled update |
| 09 | **Crypto Agent** — Intelligence | BTC/ETH venue/bars/spread → crypto state | Separate asset-class rules and adapter | 24/7 while connected |
| 10 | **Manipulation Surveillance Agent** — Intelligence/Risk | Anomalies, stale/cross-source inconsistencies → quality flags | Detection/quarantine; no unsupported legal accusations | At ingest/candidate evaluation |
| 11 | **Bull / Bear Agents** — Research | Evidence + candidate → strongest case and countercase | Optional research-time LLM with citations; machine-checkable output | Background review, not per-order vote |
| 12 | **Model Ensemble** — Quant Lab | Approved feature snapshot → versioned forecasts | Statistical/ML predictors and baselines | Pretrained inference on live path |
| 13 | **Confidence Calibrator** — Model Validation | Forecasts + labeled outcomes → reliability report | Calibration metrics; abstain when unproven | Training/evaluation; lightweight live lookup |
| 14 | **Strategy / Portfolio Agent** — Trading | Candidates, model signals, positions → intent or FLAT | Approved strategy selector + exposure allocator | Only for actionable candidates |
| 15 | **Capital Governor / Risk Agent** — Risk | Intent + broker truth + signed policy → ALLOW/BLOCK/SAFE | Deterministic fail-closed gate; reason codes | Every order and meaningful state change |
| 16 | **Execution Agent** — Trading | Allowed intent → order/fill/reconciliation | Broker adapter, stable client order ID | During authorized paper/live sessions |
| 17 | **Position Manager** — Trading | Positions, fill state, approved exits → actions | Broker-truth state machine + risk controls | Stream and scheduled checks |
| 18 | **Ledger / Review Agent** — Operations/Validation | Decisions, fills, outcomes → attribution/audit/experiments | Append-only JSONL journal + generated CSV reports | Continuous write, periodic evaluation |

**Additional capability, not a nineteenth live AI agent:** **Model Evaluation & Benchmarking Layer** sits within roles 12, 13 and 18, supported by research workflows. It evaluates predictive accuracy, calibration, after-cost strategy performance, statistical robustness, drift, and challenger eligibility.

### Human collaboration and permissions

| Human / tool role | Accountable for | May do | Must not do |
|---|---|---|---|
| **Owner (product/risk approver)** | Desired universe, risk envelope, architecture acceptance, live switch, capital | Approve strategy family, exceptions within policy, releases | Delegate live key custody to Codex; skip gates |
| **Technical teammate (implementation lead)** | Build, tests, CI, documentation, operating drills | Implement on feature branches; run mocks and paper with authorized credentials | Push unreviewed code to `main`; introduce secrets |
| **Codex (development assistant)** | Repo mapping, tickets, code/tests/doc drafts | Read repo, propose scoped diffs, run local tests | Place real orders; invent probe results; rewrite evidence history |
| **Independent reviewer (can be owner + separate review pass)** | Model validity, risk controls, security | Challenge leakage, benchmarking, execution semantics | Treat one good backtest as validation |

Assign a named human to each GitHub issue before development. Never make an AI agent the legal/accountable owner of a real brokerage account.

---

## 4. Architecture: separate the time-critical path from research

```text
             MARKET DATA + BROKER UPDATES + PERMITTED EVENTS
                               |
                     DATA TRUST / TIME STAMPS
                               |
             +-----------------+-----------------+
             |                                   |
       FAST TRADING LANE                   RESEARCH LANE
       bounded; prioritized                scheduled/isolated
             |                                   |
   rolling feature snapshots               Parquet historical archive
             |                                   |
   cheap scan -> shortlist                  discovery -> hypothesis registry
             |                                   |
   approved models and strategy             leakage-safe replay/backtest
             |                                   |
   portfolio allocator -> GOVERNOR          benchmark -> shadow/paper
             |                                   |
   durable intent -> paper broker           challenger evaluation
             |                                   |
   monitor/exit/reconcile                   owner-approved promotion
             |                                   |
             +---------- DECISION LEDGER --------+
                               |
                       MODEL/STRATEGY REGISTRY
                               |
                        READ-ONLY DESK UI
```

**Latency contract.** Strategies must declare their `signal_horizon`, `max_feature_age`, `max_candidate_age`, `required_sources`, and `max_decision_latency`. Measure end-to-end `first_available_at → identified_at → evaluated_at → approved_at → submitted_at → filled_at`; record p50/p95 and missed/expired counts. Establish p95 targets **after** a benchmark of the proposed hardware/data feed. No strategy whose edge disappears before a realistic end-to-end decision is suitable for the initial engine.

**Scheduling contract.** Highest priority: reconciliation, kill/SAFE conditions, existing position protection. Next: actionable candidates and broker order state. Next: ingestion and storage. Lowest: historical simulation and heavy LLM work. Historical training never locks the order path; if compute pressure rises, pause research. Crypto observation can remain active during equity-off-hours; a laptop cannot guarantee 24/7 exits while asleep.

**Reliability contract.** One locked journal writer with durable append and validated checkpoints; bounded in-memory queues, backpressure, deduplication, reconnect and gap-fill, restart from the last valid event, separate market/text workers. On reconnect, reconcile broker state **before** any new order. Expired opportunity does not become a catch-up trade.

---

## 4A. Data-tier, latency, and missed-opportunity attribution (NEW, release-critical)

**Requirement:** Distinguish whether JARVIS was (i) wrong about direction/edge, (ii) too slow internally, (iii) blocked or degraded by feed/access entitlement, (iv) delayed by broker submission or actual fill, or (v) correctly refused on risk grounds. A correctly predicted direction can still lose money because entry was late or spreads were wide. These causes are separate and must never be mislabeled as model failure.

### 4A.1 Provider profiles and free-tier-first policy

At launch choose Alpaca **Trading API Basic (free)** with paper account. The official October 2026 market-data plan lists **real-time IEX-only equities**, **30 simultaneous stock WebSocket symbol subscriptions**, **200 historical market-data calls/min**, and **historical SIP restricted for the most recent 15 minutes**. It lists **Algo Trader Plus** as the paid upgrade providing SIP real-time market-wide US equity coverage, higher request allowances and unlimited stock stream symbols; current listed price **$99/month**, subject to recheck before purchase. This does **not** mean all IEX messages arrive 15 minutes late; it is a *coverage/entitlement* difference, and restricted consolidated historical recency is a distinct issue. Alpaca paper trading is simulated and does **not** model market impact, queue position or latency-driven price slippage. Do not treat any stated plan or price as guaranteed for the user's account. Sources: https://docs.alpaca.markets/us/docs/about-market-data-api ; https://docs.alpaca.markets/us/docs/market-data-faq ; https://docs.alpaca.markets/us/v1.4.2/docs/paper-trading .

**Practical consequence:** A broad hourly universe scan of up to 200 names is *not* the same thing as subscribing to 200 live symbols. With Basic, use permitted batch/delayed bars for broad discovery, then an entitlement-aware priority watchlist of no more than the verified streaming cap for IEX. Opening-second, consolidated-volume, and sub-minute SIP-dependent strategies must remain inactive until suitable data access and measured infrastructure exist. Record which feed (`iex`, `sip`, venue/location), subscription plan, requested vs granted symbols, provider entitlement, freshness and coverage each strategy actually used. A 403 entitlement denial, 429 rate limit, 406 streaming connection limit, and a late broker fill are **different diagnostic events**.

For BTC/ETH, Alpaca's crypto Trading API/data pathways can potentially serve both assets, subject to the owner's account, Texas/region permissions, supported pairs, fees, order types and the actual execution/data venue. Crypto data locations such as `us` and `us-1` are not interchangeable. Check them using current asset and data APIs; do not presume equity paid data changes crypto venue quality. Crypto trading and market data must be independently probed. Sources: https://docs.alpaca.markets/us/docs/crypto-trading ; https://docs.alpaca.markets/us/docs/crypto-fees ; https://docs.alpaca.markets/us/docs/real-time-crypto-pricing-data .

### 4A.2 Timestamp contract (UTC, nanosecond or millisecond precision where supported)

Every candidate/order must carry **timestamp provenance**, not merely one `timestamp` column. Minimum fields:

| Time field | Meaning |
|---|---|
| `exchange_event_at` | Exchange/venue's timestamp for trade/bar/event, when provided |
| `provider_publish_at` | Provider publish time if exposed; nullable, never invented |
| `local_received_at` | First local receipt on the relevant interface |
| `usable_at` | When input was lawful, available, validated and usable for strategy |
| `feature_ready_at` | Point-in-time feature snapshot completed |
| `candidate_detected_at` | Scanner recorded signal |
| `inference_started_at` / `inference_ended_at` | Model-inference interval |
| `risk_decided_at` | Governor decision completed |
| `order_intent_persisted_at` | Durable intent committed before broker submission |
| `order_submitted_at` | Client sent request, from monotonic span correlation |
| `broker_ack_at` | Broker acknowledged request; persist request ID if returned |
| `first_fill_at` / `last_fill_at` | Actual fill timestamps, or null for non-fills |
| `candidate_expires_at` | Latest valid entry opportunity, fixed by strategy spec |

Network/host clock skew and clock precision must be measured; provider timestamps can be missing or inconsistent. Preserve raw reported timestamps, local clock offset, monotonic durations, and `UNKNOWN` for unavailable steps. Don't derive precise network latency from unsynchronized clocks.

### 4A.3 Trace every opportunity and diagnose bottlenecks

Associate `correlation_id`, `candidate_id`, `strategy_version`, `model_version`, `policy_version`, `provider_profile_id`, `feed`, `venue`, `market_data_entitlement`, `source_sequence`, `process_host`, `process_build_sha`, and API request ID with each span. Core observed spans: `ingest_lag`, `feature_lag`, `scan_lag`, `inference_latency_ms`, `risk_latency_ms`, `queue_wait_ms`, `submit_ack_ms`, `ack_first_fill_ms`, `total_actionable_latency_ms`, `quote_age_ms`, `missed_message_count`, `rate_limit_count` and `stream_disconnect_count`.

Classification requires **evidence**. Valid reason codes include `ENTITLEMENT_DENIED`, `FEED_COVERAGE_LIMIT`, `HISTORICAL_RECENCY_RESTRICTION`, `STREAM_CAPACITY`, `RATE_LIMIT_429`, `DISCONNECTED`, `STALE_DATA`, `CLOCK_SKEW`, `LOCAL_QUEUE_BACKLOG`, `FEATURE_COMPUTE_DELAY`, `MODEL_INFERENCE_DELAY`, `GOVERNOR_DELAY`, `BROKER_ACK_DELAY`, `PARTIAL_FILL`, `SPREAD_SLIPPAGE`, `SIGNAL_EXPIRED`, `RISK_BLOCKED`, `MODEL_MISFORECAST`, `MARKET_MOVED`, `UNDETERMINED`. Multiple labels may coexist, but do not double-count attributable cost.

An SLO panel monitors p50/p95/p99 of phase durations, quote age by feed, queue depth, dropped/late events, expired candidates, successful vs failed submissions, cost of delay with uncertainty, and evidence that paper assumptions differ from live fills. Set hard performance budgets **only after benchmarking the actual computer and data tier**; reject strategies whose opportunity lifetime cannot tolerate measured delays. Instrument from A1, exercise mock delay injection before A3, and do not wait until the first live order to add telemetry. Telemetry itself must stay bounded and non-blocking where safe: correlation IDs and risk-critical decision records are durable, while noncritical high-volume spans use batched/async export, bounded queues and explicit drop counters; an observability outage must never silently hide a failed risk check.

### 4A.4 Return capture and counterfactual integrity

Maintain **realized return**, **valid contemporaneous executable reference return**, and **hypothetical counterfactual return** as different fields. A model predicting a 10% move is not entitled to claim it "missed 7%" merely because it ultimately earned 3%. To estimate missed capture, freeze the candidate at its *first genuinely observable/usable time*, define strategy sizing/exit, infer executable entry from contemporaneous bid/ask/available liquidity and costs, then compare with filled P&L using a common exit assumption. If no bid/ask, depth, or fill-quality evidence exists, label the difference **estimated/unknown**, not measured loss from Alpaca Basic. Never use tomorrow's high or perfect entry as the reference.

**Illustrative display only:** candidate reference gross return `+6.0%`; executed gross return `+3.9%`; *estimated entry-timing shortfall* `2.1 percentage points` before matched fee differences. Even then, the root cause remains `UNDETERMINED` until a specific local delay, feed entitlement restriction, market move, or broker event is verified. Counterfactual ranges/uncertainty and available quote coverage appear next to the estimate. Return percentages are NOT direct additive performance attribution when position sizes, holding periods, or exits differ.

Recommended opportunity outcome fields: `candidate_id`, `first_actionable_at`, `reference_price_type`, `reference_ask_bid`, `estimated_executable_size`, `actual_fill_vwap`, `exit_policy_hash`, `actual_realized_net_pnl`, `reference_hypothetical_net_pnl`, `missed_capture_pp_estimate`, `assumptions`, `confidence_interval_or_bounds`, `evidence_level` (`MEASURED`, `ESTIMATED`, `UNKNOWN`), `cause_code`, `cause_evidence_uri`, `counterfactual_version`. Hypothetical statistics must never be combined with live account profit and loss.

### 4A.5 How a paid data upgrade is evaluated

Log free-tier observed restrictions and candidate misses from day one. **You cannot empirically know what the paid SIP stream would have provided in real time without actually observing a lawful comparable SIP feed.** Therefore Basic-only periods can show verified access limits and *estimated opportunity costs*, not precise paid-tier opportunity capture. On a later authorized upgrade, run a **paired shadow comparison** of Basic/IEX versus paid/SIP on the same symbols, time windows, strategy code and clocks; compare observation availability, candidate timing, model/strategy decisions, order constraints and after-cost reference fills. Use uncertainty intervals, retain no-SIP-control caveats, and evaluate whether *measured net incremental benefit* plausibly exceeds the subscription, engineering, and operational costs. Never purchase or activate paid entitlements automatically.

**Example UI explanation:** `NVDA | signal usable 10:03:00 | identified 10:03:00.120 | policy approved 10:03:00.145 | order sent 10:03:00.170 | filled 10:03:01.400 | source IEX Basic | reference fill unavailable | cause: cannot quantify paid-feed counterfactual`. When evidenced: `SEC filing event parsed 10:01:30 but local text backlog delayed feature 84 s; candidate expired; classified LOCAL_QUEUE_BACKLOG (measured), not model error.`

## 5. Data system, schemas, and storage

### 5.1 Recommended storage stack

| Store | Format / mechanism | What goes there | Why |
|---|---|---|---|
| Historical market store | Partitioned **Parquet** | Equity/crypto bars, normalized market events, dated features | Compressed, reproducible batch research |
| Operational source of truth | **Append-only JSONL** journal, one locked writer | Candidates, evidence IDs, broker observations, risk decisions, order intents, fills, outcomes and health events | Replayable chronological audit; no in-place trade edits |
| Experiment registry | Versioned JSON metadata + CSV result index | Every hypothesis/test, data hashes, results, negative findings | Multiple-testing accountability |
| Artifact registry | Immutable filesystem files with SHA-256 | Model weights, preprocessing pipeline, specs, promotion receipts | Exact reproducibility and rollback |
| News/event store | JSONL event metadata + permitted local documents | Source URLs, published/first-seen times, dedup/event tags | Relevance and licensing control |
| Human reports | Atomic CSV snapshots; optional XLSX exports | Opportunities, trades, model comparisons, latency and research | Excel-readable views derived from the journal |
| Backups | Encrypted, restore-tested external copy | Journal, Parquet, registries, artifacts, metadata and configuration | Operational recovery |

**V1 excludes SQLite, PostgreSQL, MongoDB, Redis, cloud databases and database servers.** Put the local persistence boundary behind `StorageAdapter`; future database integration may be evaluated after measured scaling pressure without rewriting strategies, agents, Governor or evaluation code. See [LOCAL_STORAGE_AND_SCHEMAS.md](docs/05-final-implementation/LOCAL_STORAGE_AND_SCHEMAS.md) for directory layout, column contracts, atomicity, crash recovery and acceptance evidence.

**Do not commit** market bulk data, secrets, private account statements, model dumps with private information, live trade ledgers, or backups to the public Git repository. Check provider rights before retaining/repackaging article content. Avoid raw tick/order-book capture initially; bar storage is manageable, while depth/tick feeds create much greater I/O and retention complexity. Record disk usage and retention policy rather than guessing storage sizes.

### 5.2 Contract-first typed records

Create versioned Pydantic/dataclass models and schema tests for:

- `Asset` / `Venue` / `UniverseMembership`: canonical symbol, asset class, exchange/calendar, tradability as known at each time; delisting and symbol changes.
- `AssetEvent`: `event_at`, `first_available_at`, `ingested_at`, `source`, `venue`, `event_type`, payload hash, data-quality status.
- `FeatureSnapshot`: asset, horizon, as-of/available/expiry times, feature version, raw event IDs, `MISSING` and quality flags.
- `Candidate`: detection time, scanner version, hypothesis/trigger ID, expiry, applicable universe and evidence snapshot.
- `Hypothesis` and `Experiment`: claimed relationship, economic rationale, search space, trial count, split plan, outcome horizon, run hash and negative results.
- `StrategySpec`: strategy family, asset class, required features, entry/exit logic, holding period, cost model, signal horizon, no-trade criteria, version and approval status.
- `ModelCard` / `EvaluationReport`: training cutoff, feature schema, data snapshot, code digest, metrics, benchmark, probability calibration and drift thresholds.
- `StrategyIntent` / `RiskDecision`: candidate, approved spec version, position target, expected net edge and downside, policy version, `ALLOW/BLOCK/SAFE` reasons, validity window.
- `OrderIntent` / `BrokerEvent` / `Fill` / `PositionSnapshot`: stable idempotency ID, broker IDs, status, partial fills, fees (including late-posted crypto fees), reconciliation and current position.
- `Outcome` / `MissedOpportunityOutcome` / `PromotionDecision`: realized vs **hypothetical** result, horizon, counterfactual assumptions, attribution, reviewer, rollback target.
- `SystemEvent`: data outage, retry, queue lag, SAFE/HALT, startup reconciliation, UI information timestamp.

**Timestamp rule:** UTC everywhere internally; display exchange-local time only in UI. Preserve both event time and when JARVIS first could have known an item. Revisions and late bars create *new versions*, not retroactively prescient snapshots. No future data, leaked target label, survivorship-only universe, or adjusted historical price without explicit adjustment protocol.

### 5.3 Two market lanes, one portfolio

**Equity lane:** scheduled liquid universe refresh (initial design upper bound: **200 equities**); hourly broad screening and a maximum **10 deep candidates**; daily bars for context. Build a much smaller smoke-test universe first. Equity calendars, market hours, corporate actions, consolidated/IEX feed differences, earnings/SEC, sector relative strength, market-spread checks.

**Crypto lane:** start with `BTC/USD` and `ETH/USD` market data; hourly or 15-minute *completed bar* features only if data rights/support and backtests justify them. Asset class has 24/7 clock, venue-specific liquidity, fees, min quantities, corporate-action inapplicability, and exchange/feed-location matching. Trading disabled until account and jurisdiction probe passes.

**Shared portfolio:** actual broker cash, positions, pending orders, correlations, concentration, combined equity+crypto exposure, total risk budget and available buying power. Signals may conflict; a portfolio allocator compares expected net edge and incremental risk, may choose multiple opportunities or `FLAT`.

---

## 5A. Local files and Excel-ready management workbooks (NEW)

**Design choice:** use an append-only JSONL **operational journal** as the replay source for decisions, risk, orders and fills; Parquet for numerical histories and features; JSON for configuration, manifests and versioned registries; native model artifacts with hashes; and atomic **CSV/Excel-openable reports** for inspection. CSV reports and optional XLSX workbooks are generated views, not order authority. Excel can be used to inspect copies; an edited report never changes journal history. See the detailed [storage contract](docs/05-final-implementation/LOCAL_STORAGE_AND_SCHEMAS.md).

### 5A.1 Required local table / export contracts

These are **CSV projection names**, not operational authorities. Any "append" rule in the table applies to the underlying JSONL event or immutable research record; CSV files are regenerated atomically from those sources.

| Table / export | Primary key | Essential columns and relationships | Append/revision rule |
|---|---|---|---|
| `provider_profiles.csv` | profile_id+version | plan, equity feed, crypto location, key alias (not secret), symbol and request limits, permission result, probe datetime | versioned changes |
| `market_events.csv` | event_id | asset, exchange/source event times, local receipt, feed, quality, adjusted version | append, linked corrections |
| `feature_snapshots.csv` | snapshot_id | asset/horizon, available_at, expires_at, features_ref, missingness, raw event IDs, transform hash | immutable snapshots |
| `candidates.csv` | candidate_id | strategy scope, detected/expires, direction hypothesis, discovery features and reason, status | append events + current view |
| `decision_trace.csv` | decision_id | candidate/model/spec/policy versions, times, allow/block reason, latency per stage, evidence hashes | append-only |
| `trade_journal.csv` | trade_id | intent/broker ids, paper/live, symbol, venue, quantity, expected/slippage fees, entry/exit, realized and unrealized P&L | broker reconciled, correction events |
| `fills.csv` | fill_id | broker fill time, quantity, price, fees, liquidity/order refs, ingest time, late-fee adjustments | immutable fills + adjustments |
| `opportunity_attribution.csv` | candidate_id+evaluation_version | executable reference, actual result, estimated capture gap, cause, evidence type, assumptions | versioned evaluations |
| `model_registry.csv` | model_id+version | asset class, family, trained cutoff, feature hash, artifact SHA, training code SHA, approved state | immutable per version |
| `model_benchmarks.csv` | evaluation_id | holdout window, metric name/value/unit, uncertainty, baseline, net costs, sample, trials, method | append-only |
| `experiments.csv` | experiment_id | hypothesis, pre-register time, exact data/code snapshots, splits, tried variants, result and rejection | append-only |
| `system_health.csv` | event_id | data gaps, latency histograms, missed messages, rate limits, disk, CPU, source health | append; aggregate reports |
| `promotion_decisions.csv` | decision_id | champion/challenger, evidence IDs, owner/reviewer, scope, rollback, result | append-only |

CSV header templates supplied in `docs/05-final-implementation/templates/` contain **no account records and no invented production performance**. The detailed storage contract defines schemas, keys, nulls, units, UTC times and event-to-export lineage. CSV reports are regenerated from validated journal events and immutable research records, written to a temporary file and atomically renamed. Each export manifest records row count, time window, schema version, generating commit, file hash and redaction level. Excel formatting and charts are optional offline exports.

### 5A.2 Lifecycle and preservation

The local setup should define `JARVIS_HOME` **outside Git**, disk budget, retention and legal rights, encryption-at-rest where appropriate, encrypted backups, checksum validation, and a **restore drill**. The journal has one lock-owning writer; readers use complete validated records or published snapshots. Append, flush and sync critical intents before broker submission. Detect and repair an incomplete final journal line under a tested protocol; quarantine corruption in the middle. Parquet partitions and JSON manifests use temporary files, fsync and atomic same-volume replacement. Store arrival/revision and feed/location provenance beside bars. Use schema-version adapters; backtests pin exact immutable data snapshots, never an edited workbook.

The user should be able to open a read-only report workbook containing tabs: `Overview`, `Opportunities`, `Trades`, `Model Scorecard`, `Strategy Scorecard`, `Latency & Access`, `Experiments`, `Risk & Exceptions`, `Audit`, `Definitions`. Each has explicit definitions, filters, units and last refreshed time. Never treat Excel as a live shared transaction ledger.

## 6. Pattern discovery and model research: how JARVIS becomes smarter

### 6.1 Support three routes to an opportunity

**Route A — explicit pattern detectors:** candlestick sequences (including morning star), open-vs-previous-close gaps, trend/continuation, opening ranges where feed latency permits, volume anomalies, support/resistance, volatility expansion, sector-relative strength. Detect the pattern deterministically; **do not assume the pattern is profitable**.

**Route B — trained statistical/ML signals:** simple linear/logistic baselines, regularized regression, tree ensembles (e.g. XGBoost when justified), calibration, regime labels, anomaly scores. Compare against price-only or no-model baselines and decide separately for equities/crypto.

**Route C — research-generated hypotheses:** systematic feature combinations, decision-tree rule extraction, controlled clustering, anomaly follow-up, event/news linkage, and optional LLM reasoning from *source-cited, permitted* evidence. Every proposal has an economic hypothesis and explicit test plan. A newly discovered relationship stays **research-only** until admitted to the approved strategy registry.

### 6.2 The research loop (not on the critical trading path)

1. Define the prediction target **before** fitting: directional move, net return distribution, volatility, event reaction, or probability of reaching a target before a stop, always with an exact horizon.
2. Assemble point-in-time training data and dated feature provenance. Record asset survivorship, cost assumptions, missingness, source licenses, and universe selection.
3. Reserve a truly untouched chronological test period; within the development portion, use expanding/rolling walk-forward, purge overlapping labels and add an embargo when needed.
4. Search a **bounded** hypothesis space; record every tested idea, including failed ideas and all hyperparameter trials. Prevent unbounded pattern mining from inventing alpha.
5. Convert candidate patterns into frozen executable `StrategySpec` records: precise detection, entry, position sizing proposal, exit/time-stop, expiry, fee model, slippage assumptions, vetoes and constraints.
6. Backtest through the same feature/decision interfaces intended for paper/live. Simulate delayed availability, quote/slippage, spreads, order rejection, partial fills, corporate actions and survivorship.
7. Compare against buy-and-hold, matched-risk exposure, simple price-only baseline, previous champion, and an always-FLAT/no-trade reference. Include chance/selection-bias checks appropriate to number of trials.
8. Run the final untouched evaluation **once per frozen candidate**; do not repeatedly tune to the holdout. Label inconclusive low-sample results honestly.
9. Shadow trade forward on fresh data; paper execute only after engineering checks; compare expected vs observed fills and signal expiry.
10. Submit a reviewable promotion report. No newly discovered strategy can autonomously loosen the Governor, access unknown assets, or reach LIVE without owner-approved family permission.

**Illustrative discovery:** a model notices that certain completed opening-gap + relative-volume + sector-strength combinations correlate with follow-through. Research checks how many trials were attempted, whether SIP/IEX limitations allow the signal to be known in time, and whether costs leave an edge. If positive on frozen out-of-sample periods, register as a candidate strategy; *do not* have a live LLM improvise the entry.

### 6.3 Intelligent strategy selection without latency explosion

- The fast scanner only computes inexpensive features for the universe; it does **not** load every model for every tick.
- An expiring `Candidate` routes to a small set of *eligible* strategies by asset class, horizon, source freshness and environment.
- Predictive models are pretrained and loaded; inference is cheap compared with training. Required missing/stale inputs return `FLAT` for that strategy, never fabricated values.
- A simple transparent selector (best validated net expected utility with uncertainty penalty) is the **initial baseline**. A learned meta-selector is a **challenger**, not a default dependency.
- Compare opportunities in portfolio context: transaction costs, incremental correlation/concentration, downside, holding period, competing orders, and risk budget.
- A model's raw `probability` is not a universal confidence; calibrate each target/horizon separately, and prefer abstention when empirical support is weak.
- All signals have a `valid_until` time; opportunities missed due to compute/data latency are logged, not chased.

### 6.4 Training versus evaluation (including backpropagation)

**Backpropagation** is an optimization method for neural-network training, not a standalone model-performance test. JARVIS should implement a framework that can train linear models, boosted trees, and optionally neural networks, but evaluate **all of them** using comparable out-of-sample, cost-aware metrics. Do not add deep learning merely because it sounds advanced.

**Predictive tests:** log loss, Brier score and reliability diagrams for probabilities; MAE/MSE if predicting returns; directional accuracy conditional on class balance; feature stability; regime-conditional errors. **Strategy tests:** after-cost return, expected trade value, distribution of losses, drawdown, turnover, Sharpe/Sortino with caveats, exposure/time-in-market, capacity and slippage sensitivity. **Operating tests:** detection delay, inference latency, order reject/duplicate rate, reconciliation drift, and test coverage. Report uncertainty and sample size.

### 6.5 Model Evaluation & Benchmarking Layer

This is an explicit cross-cutting capability under existing responsibilities **12, 13 and 18**, not an excuse to introduce an LLM at every order.

- **Registry:** versioned model + preprocessing + feature schema + train cutoff + training data digest + benchmark and evaluation receipt.
- **Champion/challenger:** freeze challenger and compare forward (replay + fresh shadow). Expose reviewer-approved promotions only; preserve rollback point.
- **Drift:** monitor data quality, feature distribution changes, prediction calibration, outcome error, after-cost net performance, and execution degradation. Monitor statistically—not on one loss.
- **Learning rate:** store every outcome as evidence; retrain on a schedule or after sufficient new labels; test on held-out forward data; never change the live weights per tick.
- **Multiple testing:** track number of patterns, thresholds and training runs explored; reserve untouched data; use selection-bias-aware diagnostics (e.g. deflated Sharpe/false-discovery controls if justified).
- **Attribution:** separate detection error, forecast error, strategy-selection error, sizing/risk decision, transaction costs, unavailable information, and luck. Rejected candidates get simulated *counterfactuals* clearly labeled as such.

---

## 6A. Bayesian inference, objective alignment and model-challenge protocol (NEW)

**Owner's concern is correct:** 90% directional accuracy can be financially disastrous if the 10% wrong predictions lose much more than the winners earn. The precise concepts are **objective/reward misspecification (metric misalignment)**, **cost-sensitive decision-making**, **asymmetric payoffs**, **tail risk**, **expected utility** and **poor probability calibration**. In deep reinforcement learning an incorrectly designed reward can create *reward hacking*; that term is narrower than a conventional supervised predictor optimizing accuracy while the trading desk actually needs net, risk-controlled returns. Never conflate a high win rate with a high expected return.

### 6A.1 Two distinct objectives

A prediction model minimizes a scientifically appropriate prediction loss (e.g. log loss / Brier for probabilities, pinball loss for return quantiles, proper scoring rules for full distributions). A **separate policy/strategy evaluator** maximizes evidence-backed, after-cost *portfolio utility* subject to independent hard constraints. Suggested research objective (NOT a preset live policy):

`ExpectedUtility = E[net portfolio P&L] - lambda_tail * ExpectedShortfall(alpha) - lambda_turnover * transaction_costs - lambda_latency * actionable_delay_cost - lambda_concentration * risk_penalty`

`lambda_*`, horizon and `alpha` are unknown design choices, to be stress-tested/preregistered and approved by the owner. Always record the unit and accounting window. **Expected Shortfall** (CVaR) explicitly measures the severity of bad tail outcomes; maximize net utility with hard limits rather than maximizing win rate. Benchmark against price-only buy/hold, a simple rule-based strategy, cash/FLAT and current champion using identical capital and risk assumptions.

### 6A.2 Bayesian learning as an optional, testable model—not a magic optimizer

Use Bayesian inference to represent uncertainty about signal quality and regime dependence. Example starting point: an interpretable Beta-Binomial posterior for *success frequency* by setup and evidence quality, updated only after matured independent outcomes. **Do not size trades using win probability alone**; success/failure magnitude and dependency matter. More appropriate follow-on research includes hierarchical Bayesian models across related symbols/strategy families, robust Student-t or mixture return distributions for heavy tails, regime-specific posteriors, and posterior predictive checks. Use partially pooled priors to avoid confident estimates from tiny samples. Update research beliefs as new data arrives; any production model version is immutable until normal evaluation/promotion. Avoid double-counting overlapping positions, near-identical patterns and repeatedly re-labeled events as independent evidence.

**Challenge protocol before promoting a model:** Is the apparent relationship leakage? How many hypotheses were tried? Is the expected return positive after realistic costs? Is it sensitive to open/close timestamp definition or feed venue? Does a simpler baseline do as well? What happens with spreads doubled, delays introduced, heavy-tail stress, market-regime shift, missing news, and no trade? What is the credible/confidence interval around performance? Can the prediction be calibrated? Is the strategy still viable at observed p95/p99 actionable latency? Can a model be retrained and rolled back reproducibly?

### 6A.3 Training, evaluation and promotion

Backpropagation/gradient descent are **training mechanics** for neural models, not evidence of trading quality. The validation stack is: (1) point-in-time dataset QA; (2) chronological train/validation/unseen test or purged/embargoed walk-forward when overlapping labels could leak; (3) prediction metrics and calibration; (4) realistic execution-aware, after-fee portfolio backtest; (5) benchmark and multiplicity-adjusted evidence with experiment budget; (6) latency-stress replay and provider-profile robustness; (7) shadow observations on new market data; (8) paper execution/reconciliation; (9) human-approved promotion within owner policy. Failure at any stage means reject, revise or remain in shadow, **not** secretly broaden model scope.

### 6A.4 Mandatory scorecards by model, strategy and desk

**Model scorecard:** data coverage, baseline, log loss/Brier/MAE or horizon-appropriate proper metric, calibration reliability, uncertainty, distribution tail fit, feature drift, inference p50/p95/p99, data version and last training cutoff. **Strategy scorecard:** expected and realized net P&L, payoff ratio, average win/loss, profit factor, win rate (context only), drawdown, Expected Shortfall, exposures, turnover, capacity/liquidity, benchmark delta, slippage and fees, omitted-candidate count, number of trials and uncertainty. **Desk scorecard:** true broker portfolio P&L, policy incidents, client-order dedup, downtime, freshness, missed/expired opportunities, data-tier access limits, local computation vs broker latency and evidence-qualified capture shortfall. The desk may be correctly modelled but execution-limited, correctly executed but model-wrong, or appropriately in FLAT.

**Performance example:** 90 winning trades averaging +0.2% and 10 losing trades averaging -3.0% yields `(90 × 0.2 + 10 × -3.0) / 100 = -0.12%` mean trade return *before costs*. This is why directional accuracy (90%) is not the trading objective. Drawdown clustering can make portfolio outcomes worse still.

### 6A.5 Counterfactual evaluation has its own uncertainty budget

For every strategy comparison use the *same* information eligibility, fill simulation rules, capital, fees, exit logic and market exposure. Distinguish `prediction_miss`, `selection_miss`, `risk_block`, `data_miss`, `timing_miss`, and `execution_shortfall` where observational evidence supports it. Counterfactuals involving unavailable paid feeds, perfect unseen prices or incompatible positions must remain marked **unknown or estimated** and must not enter realized return or verified alpha. Pre-register thresholds to prevent choosing model variants solely from attractive outcomes.

## 7. Autonomous trading, Governor, and execution

**No single LLM authorizes an order.** The Governor is a small deterministic decision service reading *current broker truth* and a signed, versioned owner policy. An LLM may give structured reasons in research; it may not bypass risk vetoes.

### 7.1 Owner-signed policy: mandatory fields

Tradable symbols/classes, allowed strategy families and versions, mode (`PAPER` initially), gross/net exposure, per-position cap, sector/asset-class limits, daily and total drawdown/loss-stop behavior, cash reserve, liquidity/spread and slippage ceilings, max stale data age, maximum simultaneous orders, large-order approval threshold, holiday/market-hours restrictions, crypto venue allowance, post-outage recovery policy, kill switch, permitted risk-reducing behavior, and revocation/rollback process. **No numerical live limits should be invented by Codex; all are owner inputs with safe paper-only defaults.**

### 7.2 Intent and order lifecycle

1. Strategy returns typed `StrategyIntent` or `FLAT` with evidence snapshot, eligible horizon, thesis, expected after-cost distribution and frozen exit contract.
2. Portfolio allocator compares all current intents against actual holdings, pending orders and available cash; may rank, size down, combine, or choose none.
3. Governor evaluates all policy, freshness, market-hours, volatility/spread and account-capability checks; writes `ALLOW/BLOCK/SAFE` with exact reason codes.
4. Persist `OrderIntent` and unique stable client order ID **before submission**. Pass via broker adapter; reconnect or timeout means *query by ID before retrying*.
5. Consume broker order updates and reconcile fills, fees, positions and cash. Partial fill, cancel-replace, stale quotes, split/dividend, crypto fee posted later, and unknown external orders must all be handled.
6. Position Manager applies tested exits/time stops, checks signal expiry and portfolio conditions, and records *actual* execution quality.
7. On reboot/sleep/outage: reconcile actual broker positions/orders; expire outdated candidates; enter SAFE on unexplained state; never create an order merely because the missed signal had been positive.

### 7.3 No-regret safety drills before paper autonomy

Kill switch blocks new risk; delayed/stale quotes; market halt; spread widens; unknown symbol; duplicate client ID; post-submit timeout; partial fills and late fill; failed cancel; deposit/withdrawal; data-source disagreement; sleeping laptop; broker order made outside JARVIS; loss cap breached; revised bar after decision; market calendar/DST; crypto venue access removed; fee posted after fill; backup/restore mismatch. Each drill must produce deterministic final state and an audit trail.

**Do not claim paper/live 1:1 execution.** Real-money launch requires a separate limited pilot decision, measured operational reliability, and source/venue eligibility. No automated rollout from passing unit tests.

---

## 8. Lightweight UI concept: the JARVIS Trading Desk

**Goal:** an attractive, understandable local overview that communicates *what each desk is doing* without becoming another high-cost compute system. The UI is an **observability layer**, not an agent and not the decision engine. Its indicators must reflect actual event/heartbeat data, never invented activity.

### 8.1 Single-screen layout

```text
┌────────────────────────────────── JARVIS TRADING DESK ──────────────────────────────────┐
│  MODE: PAPER     Broker: Connected     Data age: 00:15     System: HEALTHY      HALT*   │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  MARKET INTELLIGENCE     →   QUANT RESEARCH    →    MODEL VALIDATION                    │
│  [● Scanner] [● Trust]       [● Discovery]        [● Evaluation] [● Challenger]          │
│         ↘                     ↗                         ↘                               │
│                 [○ Opportunity Queue: NVDA | BTC | AAPL]                                │
│                                    ↓                                                    │
│       [● Portfolio] → [● Governor] → [● Execution] → [● Position Manager]               │
│                                         ↓                                               │
│                                  [● Decision Ledger]                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  Cash | Exposure | Realized/Unrealized P&L | Drawdown | Strategy versions | Feed lag     │
│  RECENT DECISIONS: 10:01 NVDA Candidate → Risk BLOCK: spread; 10:04 BTC → PAPER FILL    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
*HALT is an authenticated, audited owner action outside read-only dashboard controls in v1.
```

### 8.2 Desk visual and icons

- Each desk/role is a **tiny icon**: simple circle/blip, minimal line-art laptop operator, or square node; use consistent labels and tooltips. Show all 18 logical responsibilities in a collapsible “Who does what?” panel; display 5 desk groups on the main canvas.
- A **brief moving dot along an SVG line** represents an actual `EventID` traversing Intelligence → Candidate → Strategy → Governor → Execution. No constant decorative activity and no full-screen 3D animation. Hover/click displays timestamp, status and event link, **not** secrets or raw account IDs.
- Status vocabulary: `idle`, `collecting`, `evaluating`, `approved`, `blocked`, `paper-filled`, `degraded`, `offline`; color *plus text/icon* for accessibility. Respect reduced-motion preference.
- Small timeline explains why a candidate was chosen/rejected: `source → feature → strategy/version → net expected edge estimate → risk decision → order/fill`.
- Separate tabs: **Desk**, **Opportunities**, **Positions**, **Research Lab**, **Model Benchmarks**, **System Health**, **Audit**. Start with the Desk/Health/Decisions MVP; additional tabs can follow.
- Research pane visibly separates `HYPOTHESIS`, `BACKTEST`, `SHADOW`, `PAPER`, `APPROVED`, `RETIRED`; never show trial results as actual profits.

### 8.3 Implementation choice and boundaries

Recommend **FastAPI + server-sent events (SSE) or controlled polling + a minimal HTML/CSS/vanilla JS/SVG page** served on `127.0.0.1`. Read published, validated journal projections and cached CSV/JSON aggregates; the UI never takes the writer lock. No React/Next.js/animations library unless prototyping proves it is essential. No subscriptions or model calls from the UI itself. No broker credentials in the DOM or browser storage. If authenticated controls are introduced later, isolate them behind audited server-side commands and owner permission; leave first release view-only. The UI should remain functional when no paper broker is connected (display `DISCONNECTED` honestly).

**UI performance tests:** idle CPU/RAM, update rate and payload size, network disconnect/refresh, 1,000-event rendering, accessibility and reduced-motion, actual-vs-demo data label, and confirmation that UI outage never affects the execution service.

---

## 8A. Trading Desk UI: lightweight, explainable and truthful (NEW)

**Design objective:** one calm, locally served, low-CPU visual trading desk; small SVG/CSS characters or circular icons for *roles* (not fictional sentient processes), subtle event "blips" moving across the screen **only when a real logged event with ID is replayed or received**. Distinguish MOCK/SHADOW/PAPER/LIVE with a persistent unmissable text label, but do not create colorful attention badges for every status. Use reduced-motion preference, keyboard access, tooltips and plain text ledger timeline; no canvas game loop or per-tick whole-page redraw. Render event flow at bounded frame rate only on recent updates, update static numbers less frequently, pause animation in background tab, serve on `localhost` behind simple session protections. Read-only by default; a requested kill/SAFE control must be a separate authenticated, confirmation-protected command handled by policy code, not HTML magic.

Suggested view: top `Mode | Equity feed IEX Basic | Crypto venue | Last trustworthy data | End-to-end p95 latency | Broker reconcile | Kill state`; center **five desk areas** (Market Intelligence, Research, Model Validation, Trading & Execution, Risk & Governance) with expandable map of **all 18 original roles** and small animated dots carrying `event_id` links; right side **Opportunity Timeline** (`DETECTED -> EVALUATED -> APPROVED/BLOCKED -> SUBMITTED -> FILLED/EXPIRED`); bottom **Model vs Strategy vs Desk Performance**, attribution with `MEASURED/ESTIMATED/UNKNOWN` marker, `Tier/access limitation`, `Recent errors`, and a no-trade explanation. UI uses pre-aggregated file snapshots, never reads credentials, never polls broker for display unnecessarily, never blocks order execution.

User-facing example: `TSLA | pattern recognized | model version xgb-eq-004 | rejected: market quote stale (provider IEX Basic) | model forecast not yet scored as wrong | hypothetical return unknown`. Icon click reveals UTC timing trace and strategy version. Show missing data and unsupported access as **unknown**, not silent zero. First UI iteration may be a Python-served static HTML+SVG/CSS dashboard; choose more complex frontend only if measured need justifies it.

## 9. Delivery sequence, tickets, and hard acceptance gates

Use existing roadmap **A0–A5** as the canonical phase sequence; the tasks below expand it. Complete **one small verified deliverable per PR**, not one giant Codex execution. Every ticket contains `Purpose / Owner / Files affected / Dependencies / Test or evidence / Done condition / Rollback`.

### PHASE A0 — Repository verification and dependency/security probes

**Who:** Technical teammate + owner; Codex drafts scoped documentation and code later, with human verification.

**Execute:**

1. After Codex has created the reviewed documentation branch, clone `branch-3`; verify it descends from `branch-1`, confirm HEAD, compare with `main`, inspect original v1/v2/v3, `AUTONOMOUS_ARCHITECTURE.md`, `DECISIONS.md`, `ROADMAP.md`, `CONTRIBUTING.md`, and legacy leakage notes. Produce `REPO_CURRENT_STATE.md` listing built vs proposed features. Do **not** assume 18 deployed agents.
2. Preserve historical architecture and research; use `FINAL_IMPLEMENTATION_PLAN.md` and `docs/05-final-implementation/` for the final plan, dependency/decision register, setup and acceptance matrix. Check that Codex appended the documentation-stage entry to `docs/LOG.md` without rewriting history.
3. Run read-only repository and dependency inventory; identify tracked secret patterns, existing credentials, unmaintained packages, notebooks and architecture/code divergence. **Never print/reveal secret values.** Owner rotates any still-valid compromised secrets.
4. Set development environments and mode policy; secure local env/key-store, `.gitignore`, secret scanner, Python toolchain, git hooks, CI smoke tests. Confirm actual OS/hardware.
5. Build evidence-based Alpaca/equity/crypto/source/terms probe register from section 2. Prefer mock interfaces before any credentialed call. Probe with paper *read-only* access when owner authorizes.
6. Freeze first-version product constraints (asset universe, time horizon, owner risks, data sources, cost limits, offline behavior) in an unsigned `OWNER_DECISIONS_REQUIRED.md`; obtain a separately recorded approval before live.

**Done when:** Architecture difference report accepted; no unexplained tracked secrets; secure paper-only config exists; each dependency marked `PASS / FAIL / OPEN / FALLBACK`; *no* live order path enabled.

### PHASE A1 — Typed contracts, local storage, latency tracing, and deterministic replay

**Who:** Data/Platform owner + independent reviewer.

**Execute:**

1. Scaffold `src/jarvis/` modules, package/test configuration, typed data records, locked append-only JSONL journal, `StorageAdapter`, Parquet partitions, atomic CSV reports, JSON model/spec registry and local configuration.
2. Implement mock data/broker adapters first; market backfill adapters for a **small** equity universe and BTC/ETH test data; UTC normalization and venue/calendar maps.
3. Ingest raw bars/events with `event_at`, `available_at`, `ingested_at`, source/venue/version. Deduplicate; quarantine wrong symbol, outlier, missing bar, late event, and revised observations.
4. Implement `FeatureSnapshot` from rolling windows and *historically available* information only. Use the same feature calculation code in historical replay and live updates.
5. Write deterministic `replay(date/time, universe, version)` with stored evidence hashes; restore from a backup into an isolated test environment.
6. Add a deliberately leaked TSLA fixture and a planted future-data oracle; tests must fail if either influences a valid decision.

**Done when:** Replaying a date reproduces the same snapshots/IDs; late revisions don't rewrite earlier available knowledge; backup restores; leakage fixtures are blocked; schema and contract tests pass. Crash injection leaves no ambiguous journal event, duplicate order or unreconciled broker position; reports open in Excel and research load cannot delay the time-critical path. These are future tests, **not passed tests**.

### PHASE A2 — Market intelligence, provider entitlement diagnostics, scanning, and fast path

**Who:** Market Data/Scanner owner.

**Execute:**

1. Implement equity and crypto adapters separately. Stream if entitled; otherwise scheduled completed-bar polling. Handle reconnects, backfill gaps, rate limits, feed source and quality explicitly.
2. Incrementally calculate reliable base features: returns, rolling volatility, relative volume, gap, trend/sector-relative strength and **candle pattern definitions with exact completed-bar semantics**.
3. Build cheap broad scanner: initially a handful of test assets; graduate toward current plan's 200 equity symbols hourly, <=10 deep active candidates; record reasons for filtered/no-trade candidates.
4. Build background SEC/news/event queue; deduplicate by source/document hash, map ticker/entity, track first available, classify with a deterministic baseline before optional LLM enrichment. No private/social scraping or rehosting without rights.
5. Build candidate expiry and prioritization; emit `Candidate` with enough evidence to replay its exact creation. Use `FLAT`/quarantine for missing required features.
6. Benchmark end-to-end scanner/feature latency on actual hardware; implement backpressure and queue separation. Don't chase opportunities which expired while the machine slept.

**Done when:** Fresh completed bars generate correct incremental features and auditable candidates; 1,000 synthetic events don't delay critical position-monitor tasks; duplicated articles and stale features do not create duplicate candidates; measured latency and backlog are reported.

### PHASE A3 — First strategies, portfolio Governor, paper broker, latency fault injection, and desk UI MVP

**Who:** Strategy + Trading Systems owners; separate risk reviewer.

**Execute:**

1. Register **few transparent baselines** as research candidates, not predetermined edges: opening gap/volume filter, simple trend/momentum, event-response or price-only comparison, always-FLAT. Test equities/crypto separately.
2. Implement frozen `StrategySpec`, `StrategyIntent`, and strategy selector with explicit abstention; reject unsupported data or unsupported asset class.
3. Implement policy-driven portfolio allocator and Governor; owner can edit only through audited configuration. Use fake risk-envelope values in tests; no invented live defaults.
4. Implement mock broker → Alpaca paper adapter; durable order intent/idempotency, status/partial fills/cancels, account/position reconciliation and restart safety. Place **paper** orders automatically only after mock drills pass.
5. Implement Position Manager with predefined exit contracts, timeouts, portfolio limits and alerts; no late-candidate chase.
6. Create basic **local read-only Trading Desk UI** from section 8 showing actual data/health, roles, event movement, candidate audit trail, risk decisions and mock/paper fills; add reduced-motion switch.
7. Implement startup/readiness script and documented `OFF → OBSERVE → SHADOW → PAPER` operator flow; keep `LIVE` configuration inaccessible.

**Done when:** End-to-end `new bar → candidate → strategy/FLAT → risk decision → intent → mock/paper fill → position → outcome` is reproducible, automatic without manual order entry, and safe under restart, duplicate, reject, partial fill, and outage drills. UI is demonstrably not connected to order-authority endpoints.

### PHASE A4 — Strategy discovery, Bayesian challengers, and model evaluation laboratory

**Who:** Quant/ML + independent validation reviewer.

**Execute:**

1. Build `HypothesisRegistry` logging proposed pattern, discovery data, trial count, rationale, objective and exact expected holding horizon. Seed known patterns (morning star, gaps, volume) plus bounded automated tree-rule combinations/anomaly follow-ups.
2. Establish equity and crypto model pipelines with a simple **price-only benchmark** first, then controlled regressions/trees. Neural networks and backpropagation only when they beat simple baselines out of sample *and* fit hardware budget.
3. Build strict time-series train/development/holdout splits, purging/embargo for overlapping targets where needed, transaction-cost and execution-delay sensitivity, universe and corporate-action handling, and negative controls.
4. Build predictive metrics, reliability plots, calibration, strategy P&L/drawdowns, benchmark comparison, drift, sample sizes, and multiple-testing ledger. Negative results are permanent records.
5. Implement champion/challenger states (`DRAFT`, `BACKTESTED`, `SHADOW`, `PAPER`, `APPROVED`, `SUSPENDED`, `RETIRED`) and promotion report requiring owner/reviewer approval for new live families.
6. Monitor executed **and rejected** candidates; produce simulated counterfactuals separately labeled, using conservative fill assumptions. Attribute discovery, forecast, selection, risk, execution and regime errors.
7. Schedule heavy research off the critical path, cap CPU/memory, and test that paper trade/position latency is unaffected while research runs.

**Done when:** A planted look-ahead strategy cannot pass; random/shuffled strategy cannot be promoted; challenger can be shadowed and rolled back; trial count is visible; no research run can change production model automatically without a versioned gate.

### PHASE A5 — Controlled live-readiness review (NOT automatic launch)

**Who:** Owner, teammate, independent risk reviewer.

**Execute:**

1. Verify the account/venue/source/right-to-store matrix again immediately before any live candidate release.
2. Run meaningful forward paper evidence, operating failure drills, full reconciliation, cash/fees/quote checks, and strategy benchmarks. Define minimum duration/observations **before looking at results**; inconclusive evidence means do not launch.
3. Sign owner risk envelope and strategy-family permissions; freeze rollback, alerts, capital cap, loss cap, kill procedure and abnormal-event playbook. Include permissions for crypto only if validated separately.
4. Test model/strategy promotion, kill/HALT, restoration and software rollback. Review independent security and code audit.
5. Only then consider a **separate, explicit, minimal-capital live pilot**; keep paper mode as the shipped state of this project and do not write live keys into code or docs.

**Done when:** A signed readiness report exists with measurable evidence and explicit residual risks. If any gate fails, remain SHADOW/PAPER/SAFE. No tool, teammate, model or CI workflow may enable live mode silently.

### Build graph and minimum PR sequence

`A0 repo audit → A0 probes/security → A1 schemas/DB → A1 replay/fixtures → A2 market adapters → A2 features/scanner → A3 strategy specs/selector → A3 Governor → A3 mock broker/reconcile → A3 paper adapter → A3 UI MVP → A4 discovery/testing → A4 evaluation/challenger → A5 readiness review`.

A specific task can parallelize when contracts are frozen, e.g. UI mocks and model-research notebooks, but **never merge an untested interface contract into the trading path**.

---

## 9A. AI-generated code execution standard, roles and logs (NEW)

**AI agents may generate all initial code**, but correctness, security, evidence and production authorization remain the **named human team's responsibility**. Distinguish *AI coding assistants used during development* from *runtime market agents*. Development agents can be assigned parallel scoped roles—**Architect/Planner**, **Implementation Coder**, **Test/QA Author**, **Quant/Leakage Reviewer**, **Broker/Risk/Security Reviewer**, **Documentation/Release Reviewer**—without creating six new trading-time LLM calls. The reviewer should not simply approve the coding agent's own explanation; inspect diffs, write adversarial tests and independently replay outputs.

### 9A.1 Mandatory root files

- `EXECUTION.md` = actionable **living execution register**. For each task: ID, phase, goal, exact path/interface, prerequisites, owner, AI role, priority, status (`PLANNED`, `READY`, `IN_PROGRESS`, `BLOCKED`, `TESTING`, `REVIEW`, `DONE`), inputs, intended outputs, acceptance test, result links, commit/PR refs, risk/revert, next action. Maintain one unambiguous `NEXT SAFE TASK`; never invent completed work.
- `LOG.md` = **append-only engineering log**. Each dated record includes scope, author/agent + model/tool/version when known, prompt/spec ID or sanitized summary (never secrets), repo base SHA and output SHA, files changed, dependencies and version lock, test names/results, measured performance and failures, model/data hashes, human reviewer/signoff, conflict/decision rationale, rollback reference. Distinguish `PROPOSED`, `GENERATED`, `TESTED`, `REVIEWED`, `MERGED`, and `DEPLOYED` stages. Preserve `docs/LOG.md` as an independent high-level history; root LOG is fine-grained build evidence.
- `MODEL_REGISTRY` and `EXPERIMENTS` = persisted machine-readable metadata, not arbitrary ChatGPT claims. Every trained model and research experiment gets exact source-code commit, dataset manifest/snapshot hash, feature pipeline version, dependency lock, random seed, specification, outcomes and status. Promotion receipts reference evidence and rollback hashes.

### 9A.2 Codex execution cycle for each atomic issue

`READ ACTUAL REPO -> DECLARE SPEC/CONTRACT -> WRITE TESTS & FIXTURES -> GENERATE SMALLEST CODE CHANGE -> RUN OFFLINE MOCKS -> TEST EDGES/FAILURES -> QUANT AND SECURITY REVIEW -> BENCHMARK LATENCY -> UPDATE EXECUTION.md + LOG.md -> HUMAN APPROVAL -> COMMIT/PUSH/PR -> NEXT ISSUE`.

Require `pytest`, formatter/linter, Python type checks for money-critical modules, dependency lock and vulnerability checks, secret/PII scans, deterministic seeds, reproducible model/data manifests, and a clean diff. Add tests for look-ahead, time zones, NaN/infinity, split-adjustments, position mismatch, duplicate orders, reconnect gaps, rate-limit backoff, provider entitlement denial and delayed fills. Use a fake broker with network blocked in unit tests; no live secrets in CI. Prevent any automated assistant from editing production risk policy, changing `LIVE=false`, relaxing gates, subscribing to paid services, or placing live orders. A code generation loop may auto-iterate in sandbox until tests pass, but **cannot declare its own risk code approved**.

### 9A.3 Independent quantitative and operational challenge

The quant reviewer checks label construction, walk-forward methodology, multiple-testing count, payoff tail, regime shifts, latency attribution confounding and benchmark parity. Security/risk reviewer checks broker idempotency, policy fail-closed, secret handling, atomic ledger writes and offline/recovery; operations reviewer reproduces installation from zero, runs fault-injection and checks docs. AI-generated performance reports must include exact test command and data snapshot. No 'best version' claim without a controlled comparison on previously held-out evidence; record rejected versions and benchmark deltas, not just winners.

## 10. Definition of done, operating scorecards, and test suite

**Engineering acceptance:** type checking/formatting/CI green; reproducible environment; replay tests pass; no secrets; broker-state invariants; mock outage/duplicate/fill drills; paper and research isolated; UI accessible/read-only; issue and design log updated. Unit tests alone are insufficient: run integration tests with mock broker and fault injections.

**Research acceptance:** declared hypothesis, versioned data and code, train/validation/test separation, as-of data, explicit search-space and trial counts, independent comparison to costs and benchmarks, distribution of outcomes, calibration if probabilities, stress and time sensitivity, negative results stored, reviewer decision. Positive backtest alone **never** grants trading approval.

**Risk acceptance:** no unauthorized symbol/strategy, no trade without fresh applicable data and broker reconciliation, exposure/loss limits default deny, owner kill works, no duplicate submissions, stale-candidate expiry, risk-reducing behavior tested separately.

**Live-path performance scorecard (measured; not assumed):** feed age by source; queue backlog; p50/p95 candidate and order decision time; expired/missed candidate count; model inference duration; duplicate or unknown broker orders; paper-to-estimated-live cost gap; CPU/RAM/disk; uptime/restarts. Predeclare target metrics for each approved strategy according to its time horizon.

**Model scorecard:** data coverage, predictive error/calibration, benchmark-relative after-cost results, sample size and uncertainty, maximum drawdown and tail outcomes, regime performance, turnover, slippage sensitivity, complexity/maintenance, model drift, and verified rollback. Keep trading P&L separate from model prediction metrics.

**Adversarial acceptance scenarios:** future timestamp and post-event document; target-leaking TSLA fixture; shuffled labels; duplicate article and stale news score; fake positive candlestick due to revised bar; IEX vs SIP mismatch; gaps/out-of-order events; false broker success followed by timeout; partial fill; unknown external position; fee arriving next day; crypto venue unavailable; laptop sleep; DST and holidays; backup restore; overloaded research job; UI freeze; kill in flight. Every scenario must have a named expected safe outcome.

---

## 10A. Owner inputs, setup wizard and verification probes (NEW)

**Codex/team must not ask the owner to paste brokerage API keys into chat, commit, screenshots or prompt files.** Supply an interactive local setup checklist/config wizard only after the documentation pass and only with explicit paper scope. The initial document package includes names and schemas—not secrets.

| Input / required human decision | Example input name | Who supplies it | Safe default and validation |
|---|---|---|---|
| Alpaca **paper** key ID and secret | OS credential aliases `alpaca_paper_key_id` / `alpaca_paper_secret` | Account owner, locally | No credentials => MOCK/OBSERVE only; no echo/log |
| Paper account domain / API profile | `broker_mode: paper`; endpoint `https://paper-api.alpaca.markets` | Developer with owner review | Hard-coded allowlist; `api.alpaca.markets` blocked in v1 |
| Market data feed | `equity_feed: iex`, `equity_data_plan: basic`, optional historical `sip` if delayed permissible | Team from measured entitlement probe | Denied/unknown => fail closed on source-dependent strategy |
| Crypto observation/trading | `crypto_data_location`, `crypto_trading_enabled: false` | Owner after account/region/assets check | Data-only or disabled until positive probe |
| Capital and market universe | `paper_starting_equity`, `eligible_equity_symbols`, `eligible_crypto_pairs` | Owner | Match realistic intended capital; no $100k default assumption |
| Risk envelope | max position %, per-asset/cross-asset exposure, daily loss cap, volatility limits, max spread and quote age, owner large-order threshold | Owner signs document | Unknown thresholds => no autonomous orders |
| Strategy timing envelope | `max_feature_age_ms`, `max_candidate_age_ms`, `max_decision_latency_ms`, `entry_window` per strategy | Quant/team after data benchmark | Missing => strategy stays SHADOW |
| Data storage and machine | `JARVIS_HOME`, disk quota, Windows/macOS choice, 8GB assumption or actual specs, time sync, sleep behavior | Developer / owner | Local-only, encrypted backup, forbid live if uptime unknown |
| Research scope | asset classes, backtest periods, features, statistical objective, trial budget, compute windows | Owner/team | Research off live critical path, no unbounded exploration |
| Optional information/model APIs | SEC user agent/contact, FRED or other approved key, optional Grok/Claude provider via OS secret store | Owner optionally | No optional key => source disabled, price-only lane continues |
| Review & notifications | human risk approver, PR reviewer, optional alert channel | Team | Review required for risk/live changes; local read-only UI otherwise |
| Later live account | separate live brokerage credentials, owner consent and account access | Owner ONLY after A5 | Never in Codex, dev CI, branch, sample config or first-pass implementation |

The future setup wizard should output a **redacted capability report** (`PASS`, `FAIL`, `UNVERIFIED`) for stock data plans, WebSocket capacity, response status, time-sync, paper trading access, instrument tradability, feed-location mismatch, current fees, maker/taker, order types, min increments, API rate limits, OS uptime, disk encryption/backup, and latency baseline. Store only key aliases and probe results, not credentials or full identifying account data. The separate [USER_SETUP_AND_REQUIREMENTS.md](docs/05-final-implementation/USER_SETUP_AND_REQUIREMENTS.md) starts the human checklist; a runnable wizard is a later implementation task.

**Future stage-zero readiness target:** after implementation, the user should be able to install a pinned Python environment, run an offline mock demonstration, inspect CSV templates and a dashboard demo, then (with paper credentials configured locally) perform read-only brokerage and market-feed probes. None of these runnable facilities exists in this documentation branch. Trading remains disabled until the Governor, reconciliation and paper tests pass. Before paid subscription, request explicit cost approval, log current pricing/entitlements and conduct the planned paired comparison.

## 11. Proposed repository layout (additive, first pass is documentation only)

```text
jarvis/
  README.md                           # current status, links to plan
  FINAL_IMPLEMENTATION_PLAN.md       # canonical final build plan for branch-3
  EXECUTION.md                       # actionable phase/ticket register, next action + evidence
  LOG.md                             # append-only engineering, AI generation and validation log
  AUTONOMOUS_ARCHITECTURE.md         # preserved branch-1 proposed architecture
  docs/
    00-original-vision/              # preserve
    01-research/                     # preserve
    02-design-tournament/            # preserve
    03-review/                       # preserve
    04-autonomous-design/            # preserve
    05-final-implementation/
      PROBE_REGISTER.md
      OWNER_DECISIONS_REQUIRED.md
      RUNBOOK_INCIDENTS_AND_RECOVERY.md
      LOCAL_STORAGE_AND_SCHEMAS.md
      USER_SETUP_AND_REQUIREMENTS.md
      PHASE_ACCEPTANCE_AND_OWNER_MATRIX.md
      templates/*.csv               # HEADERS ONLY; no sensitive records
    LOG.md                           # existing high-level project history (append only)
  legacy-v1/                         # reference only, do not execute live
  # Later implementation PRs only (not first Codex documentation pass):
  src/jarvis/{core,data,features,discovery,research,models,validation,
              strategies,portfolio,risk,brokers,positions,ledger,ui}/
  tests/{unit,integration,replay,fault,performance,security}/
  config/example.paper.yaml         # no credentials, only when implementation starts
  .github/workflows/                # offline/mock tests; no live secrets
  .gitignore                         # future local data/models/logs/credentials excluded
```

Local runtime data stays **outside the public repository**. Suggested local-only root `JARVIS_HOME` contains separate equity/crypto Parquet history, feature partitions, an append-only JSONL journal, JSON registries/manifests, native model artifacts, CSV reports and encrypted backups; see the [storage contract](docs/05-final-implementation/LOCAL_STORAGE_AND_SCHEMAS.md). A path may differ by OS; configurability matters more than this example naming.

## 12. How Codex should create branch-3 and prepare your teammate's handoff

### 12.1 Non-negotiable sequence: verify -> branch -> document -> test -> push

1. Work from a genuine Git clone, not a downloaded ZIP posing as a git checkout. Confirm `git rev-parse --show-toplevel`, `git remote -v`, `git status --porcelain`, `git branch --show-current` and `git log -1 --oneline`. If workspace is wrong or dirty, STOP before edits.
2. `git fetch origin --prune`; verify the current upstream `origin/branch-1` and compare with the documented baseline. Review any changes since plan preparation and record unresolved conflicts. Never overwrite a teammate's work.
3. Check `git branch -a` and remote refs for `branch-3`. **If it does not exist**, create `branch-3` from `origin/branch-1` in a clean worktree. **If it exists**, inspect its parent/history and diff; do not re-create, reset, rebase, or force-push it without review.
4. Read `README.md`, `AUTONOMOUS_ARCHITECTURE.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `docs/04-autonomous-design/{DECISIONS,DIAGRAMS,ROADMAP}.md`, `docs/00-original-vision/v3-workflow.md`, `docs/LOG.md`, the research/review docs and `legacy-v1/` caveats. Do not treat design prose as implemented agents.
5. Use this file as `FINAL_IMPLEMENTATION_PLAN.md`; create the supporting storage, probe, owner-input, setup, runbook and acceptance documents under `docs/05-final-implementation/`, plus root `EXECUTION.md` and root `LOG.md`. Add links and correct status to `README.md`, append one dated entry to existing `docs/LOG.md`. No broker integrations or agent code in this FIRST PASS.
6. Run doc link/reference checks, CSV-schema/header checks, `git diff --check`, git secret scan, and inspect complete diff. Log every executed check, command, result, and limitation. Commit the documentation to `branch-3`, push without force, and provide exact commit SHA. If remote push is blocked, provide the staged diff and commands, not a claim of success.
7. Teammate clones `branch-3`, reproduces environment and checklists, assigns named human owners, and only then begins A0/A1 in small reviewable implementation changes. Changes that alter broker operations, risk, promotion, or data access always receive human review and explicit signoff.

Example commands for a clean clone (run only after inspecting the actual environment):

```bash
git clone https://github.com/aanshul1215/jarvis.git
cd jarvis
git fetch origin --prune
git status --porcelain
# verify branch-3 does not already exist
# git branch -a
# if ABSENT and branch-1 is appropriate base:
git switch -c branch-3 origin/branch-1
# Open THIS directory in Codex; import documentation overlay, inspect all diffs.
# git diff --check
# git add FINAL_IMPLEMENTATION_PLAN.md EXECUTION.md LOG.md docs/05-final-implementation README.md docs/LOG.md
# git commit -m "docs: add final implementation plan and engineering handoff"
# git push -u origin branch-3
```

**Do not run the optional commands blindly.** `branch-3` may have appeared since this document was prepared. `branch-1` may also have moved. If either fact changes, report before any write. The repository's `CONTRIBUTING.md` currently prefers topic branches and PR review against `main`; the owner's specific request here is to establish `branch-3` as a new documentation baseline. This does **not** authorize merging the branch or changing `main`; follow repository permissions and request review before implementation merges.

### 12.2 Human and AI development workflow

The technical teammate is accountable for architecture, code review, tests, security, and integration; the owner approves risk envelope and live enablement. Codex can generate scoped code/tests/docs automatically, but generated code is **untrusted until reviewed and verified**. Treat generated diffs as proposals, not production authority.

For every ticket: (a) inspect actual code and cite interfaces, (b) write an explicit specification and failing tests, (c) generate smallest code patch, (d) run tests with mocks/offline where possible, (e) adversarial code review using a separate pass/agent, (f) run static checks, dependency/secret scans, (g) update `EXECUTION.md` and root `LOG.md` with evidence, (h) human review, (i) commit with traceable version IDs and rollback strategy. No AI-driven runtime code self-rewrites or live strategy promotions without designated gates.

### 12.3 What Codex must report at end of its first task

(A) the verified repository and branch state; (B) exact files added or changed; (C) doc consistency issues and provider facts that need probing; (D) secret-scan and documentation test results; (E) resulting commit SHA/push status or clear blocker; (F) next **single smallest** A0 issue, with human owner TBD and acceptance test. **STOP** after docs push; do not silently implement the trading engine.

## 13. Open decisions requiring explicit owner/team review

1. Confirm development OS/hardware and the laptop's real uptime; whether 24/7 crypto trading is in scope or only observation/paper at first.
2. Confirm broker ownership/account type and paper account setup; verify crypto eligibility and venue *for that account* and Texas at the time of integration.
3. Sign initial **paper-only** financial envelope and realistic paper balance. The initial account must not accidentally simulate $100k if intended real capital is far smaller.
4. Select first **equity data granularity** consistent with entitlement: daily/delayed full-market vs real-time IEX. Do not promise minute-by-minute consolidated opening setup detection without SIP rights.
5. Set initial universe/liquidity filters and event horizons; explicitly define which candidate classes are too short-lived for the measured infrastructure.
6. Approve model/pattern discovery experiment budgets, compute windows and maximum trial search scope; forbid unbounded backtest mining.
7. Choose **which human** reviews model promotion and owner-facing risk-policy changes; record paper vs live rights separately.
8. Decide acceptable local UI exposure (localhost only recommended), user alerts, and what data may be shown on screen/shared screenshots.
9. Decide data retention, encrypted backup location, recovery requirements, and licensing terms for stored news/social content.
10. Define *pre-registered*, strategy-specific success/failure metrics, minimum evidence sample, and the criteria to stop/pause work when no edge is found.

Until resolved, implement **safe defaults**: mock/observe/paper, `FLAT` for unsupported features, no live mode, no unknown-asset trades, and no claim of continuous uptime.

---

## 14. References and verification ledger

### Internal repository primary sources (review before coding)

- `https://github.com/aanshul1215/jarvis/tree/branch-1` — branch currently documenting the autonomous proposal.
- `AUTONOMOUS_ARCHITECTURE.md` — current scope, clock design, typed interfaces, fail-safe operating boundaries.
- `docs/04-autonomous-design/DECISIONS.md` — exact mapping for all 18 original responsibilities.
- `docs/04-autonomous-design/DIAGRAMS.md` — current data and candidate flow.
- `docs/04-autonomous-design/ROADMAP.md` — A0–A5 gates and failure catalog.
- `docs/00-original-vision/v3-workflow.md` — original 18-role A-to-Z operating loop.
- `docs/LOG.md`, `CONTRIBUTING.md`, `legacy-v1/` — chronology, merge rules, invalidated legacy assumptions.

### External primary documentation (re-check access and policy at execution)

- Alpaca Trading API and official Python SDK: https://docs.alpaca.markets/us/docs/sdks-and-tools
- Paper/live authentication: https://docs.alpaca.markets/us/v1.1/docs/authentication-1
- Market data subscriptions/IEX/SIP: https://docs.alpaca.markets/us/docs/about-market-data-api
- Stock market data feeds: https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data
- General streaming connection limits: https://docs.alpaca.markets/us/docs/streaming-market-data
- Crypto feed locations and channels: https://docs.alpaca.markets/us/docs/real-time-crypto-pricing-data
- Crypto trading, fees and restrictions: https://docs.alpaca.markets/us/docs/crypto-trading
- Crypto order parameters: https://docs.alpaca.markets/us/docs/crypto-orders
- Alpaca order updates: https://docs.alpaca.markets/us/docs/working-with-orders
- Alpaca paper/live simulation limits: https://docs.alpaca.markets/us/v1.4.2/docs/paper-trading
- SEC EDGAR submissions/XBRL APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces

**Research honesty:** Some earlier repository briefs reflect the best information available when written; price plans, exchange venues, market access, and regulations can change. The probe register—not a remembered claim—determines integration readiness. If a documented venue or rule differs from the live account probe, mark the integration `OPEN` and do not trade that asset class until resolved.

**Final implementation principle:** Commit and review documentation first; implement A0–A5 incrementally with human-owned gates. A professional trading desk is measured by reproducibility, risk discipline, execution reliability and evidence—not by the number of agents.

## 15. Phased execution ownership and expanded acceptance gates (branch-3 addendum)

**Delivery principle:** No monolithic implementation. Each phase has an accountable human owner (name TBD), Codex may draft work, an independent reviewer inspects trading-critical changes, and source-controlled evidence is required for completion. The following augments A0–A5 above; any apparent conflict resolves in favor of stricter data integrity, owner authorization and fail-closed behavior.

| Phase | Lead human role | Required output | Critical acceptance gate | Status at plan publication |
|---|---|---|---|---|
| A0: current-state and access | Owner + implementation lead | repo inventory, hardware profile, paper key alias, provider/crypto feasibility matrix, secure env/backup plan, risks and signed paper envelope | source and account probes PASS or explicit disabled fallback; zero exposed credentials; all owner-required fields resolved before orders | NOT STARTED |
| A1: data and trace | Data engineer/teammate | timestamped schemas, locked JSONL journal, Parquet versioned bars, CSV export manifest, source-quality checks, ingest-to-fill spans, replay fixtures | no future-leak; exact replay; restart and restore; simulated tier 403/429; safe journal reads under concurrent append | NOT STARTED |
| A2: detection and fast path | Quant/teammate | Basic IEX/delayed SIP-aware scanner, bounded stream subscriptions, separate crypto lane, feature freshness, real candidate IDs, queue priority and telemetry | scanner respects measured account/feed capacity; source outage gives FLAT; no research pause stalls risk/order path; meaningful p95 benchmarks on local hardware | NOT STARTED |
| A3: mock/paper automation and UI | Execution/risk lead | validated baseline strategies, deterministic policy, durable intents, mock and PAPER-only adapters, position monitor, icon desk, opportunity capture audit | zero duplicate orders in fault suite, stale candidate never sent, paper vs live separated, telemetry shows exact stage root cause and unknown when unverified | NOT STARTED |
| A4: independent research lab | Quant validation lead | preregistered hypotheses, backtests, model registry, calibration, Bayesian challengers, tail-aware and latency-aware scorecards, shadow champion–challenger and trial register | planted leakage detected; noise strategy not promoted; held-out benchmark advantage with uncertainty; rollback reproducible | NOT STARTED |
| A5: owner readiness review | Owner + independent reviewer | end-to-end paper history, failed/slow order cases, incident plan, broker capability/fee probe, explicit policy and any data-upgrade evaluation | paper operational gates and measured trading edge separately reviewed; live permission remains OFF unless owner signs; no implied launch date | NOT STARTED |

**Ticket sequence to create in GitHub (one PR each, unless cohesive tiny substeps):** A0-01 repo and data leakage audit; A0-02 source/license/crypto/entitlement probe; A0-03 user config/credentials wizard; A1-01 typed event+time schema; A1-02 file journal/StorageAdapter/CSV exports; A1-03 Parquet and replay; A1-04 end-to-end timestamp tracing; A1-05 backup/restore; A2-01 equity feed/stream limits; A2-02 crypto observation lane; A2-03 incremental feature engine; A2-04 scanners and candidate expiration; A2-05 async news/SEC; A3-01 frozen strategy specs; A3-02 deterministic Governor and policy tests; A3-03 mock broker recovery; A3-04 PAPER adapter; A3-05 position lifecycle; A3-06 UI blips and ledger drilldown; A3-07 latency injector and paper limitation diagnostics; A4-01 hypothesis and experiment registry; A4-02 point-in-time walk-forward engine; A4-03 ML/proper-loss/calibration; A4-04 Bayesian research challenger; A4-05 tail-aware objective and baseline benchmark; A4-06 champion–challenger and human signoff; A5-01 owner acceptance packet. Dependencies must be written into `EXECUTION.md` and issues; never parallelize work that shares unfinished data contracts.

**End-to-end adversarial cases to certify:** (a) market event received late but inference fast -> label provider/local receive, not predictive failure; (b) valid event but model stalls -> label inference; (c) IEX setup differs from SIP -> label coverage mismatch, not definitely missed profit; (d) 429 -> backoff, no stale order; (e) delayed broker ack -> lookup by client order ID before retry; (f) fill differs from quote -> report execution, not algorithm latency; (g) candidate expires while research is busy -> research preempted or strategy FLAT; (h) 90% wins with rare tail wipeouts -> reject on Expected Shortfall/utility; (i) impressive strategy after 10,000 searches -> adjusted skepticism and untouched final test; (j) auto-generated code changes risk cap -> CI/human review blocks; (k) local CSV edit -> never changes ledger; (l) crypto source location differs from execution venue -> block strategy; (m) UI shows a blip only if actual persisted event ID exists; (n) provider upgrade comparison without comparable paid feed -> `UNKNOWN` counterfactual.

## 16. Requirement traceability: every owner request mapped to a deliverable

| Owner request | Blueprint section / output | Acceptance evidence |
|---|---|---|
| Free Alpaca first, paid later | 2, 4A, 10A and provider probe | measured entitlement, coverage/stream tests and no unauthorized subscription |
| Explain missed 2% despite good signal | 4A and attribution CSV | event traces and evidence-quality marked reference-vs-realized analysis |
| Excel/Parquet local storage | 5, 5A | CSV/Parquet schemas, JSONL replay, atomicity/recovery tests, optional workbook export and restore |
| Bayesian inference | 6A | preregistered challenger and posterior predictive/benchmark result |
| Tail risk / wrong objective | 6A | payoff asymmetry and Expected Shortfall tests; not win-rate-only |
| Model shouldn't be late | 4A, 6A, 9, 15 | p50/p95/p99 budgets and latency-stress backtest |
| All code AI-generated, reliable | 9A, 12 | `EXECUTION.md`, `LOG.md`, independent review, pinned deps and CI evidence |
| User-input keys and setup | 2, 10A | redacted paper-only capability report and safe credential store |
| All original 18 desk roles | 3 | 18-role map preserved, runtime vs logical functions differentiated |
| Self-discovered patterns and strategies | 6, 6A, A4 | hypothesis register, unseen tests, shadow/paper and promotion gates |
| Equity + crypto distinct modeling | 5.3 | independent clocks/data/models and one shared risk view |
| Readable innovative desk UI | 8, 8A | true event-linked icons/blips, low CPU, accessible read-only replay |
| Teammate can clone `branch-3` | 11, 12, 15 | verified branch/commit, repo links, working owner tickets and reproducible setup |

## 17. Supplied source notes requiring re-verification

The supplied October 15 plan listed these links and tier figures; this documentation pass did **not** independently verify current pricing, limits, or account-specific rights. A0 must recheck them and record dated evidence in the probe register. **Alpaca Trading API** (individual) differs from its **Broker API** (platform partners). Source-plan figures to probe: Basic free; Algo Trader Plus listed $99/month; Basic IEX real-time equities, SIP historical latest 15 minutes restricted, 30 concurrent stock streams, 200 historical data requests/min. https://docs.alpaca.markets/us/docs/about-market-data-api . Feed distinction: https://docs.alpaca.markets/us/docs/market-data-faq . Paper/live credentials and domains: https://docs.alpaca.markets/us/docs/authentication . Paper simulation limits: https://docs.alpaca.markets/us/v1.4.2/docs/paper-trading . Crypto eligibility, orders, account settings and 24/7: https://docs.alpaca.markets/us/docs/crypto-trading . Crypto venue-specific data: https://docs.alpaca.markets/us/docs/real-time-crypto-pricing-data . Crypto spot fee schedules: https://docs.alpaca.markets/us/docs/crypto-fees . Broker support trace IDs: https://docs.alpaca.markets/us/docs/getting-started-with-trading-api .

**Version status:** `FINAL IMPLEMENTATION PLAN` describes approved *design direction*, not deployed software, confirmed profitability, opened brokerage accounts, accessible subscription tiers or signed real-money authority. Keep all `OPEN` evidence explicit until implementation confirms it.

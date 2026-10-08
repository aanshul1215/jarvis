# JARVIS autonomous architecture — proposed revision

**Status:** design proposal, 2026-10-08. No components described here have been implemented in this repository. This document expresses the owner's revised goal and supersedes the runtime and product scope of the [October 2 monthly recommendation proposal](ARCHITECTURE.md). That earlier proposal remains available for its research, rejected alternatives, and risk analysis. The [original v1/v2/v3 vision](docs/00-original-vision/) remains the source of the workflow below.

JARVIS is a local, owner-only system for finding and managing opportunities in liquid US equities and spot BTC/ETH. It should automatically collect evidence, choose among approved strategies, place and manage permitted orders, record every decision, and improve through controlled evaluation. **Neither Claude nor Codex participates in the live decision or order path.** They may help develop, test, and review the software. A profitable or steady return is a goal to test, not a property the architecture can guarantee.

## 1. Invariants and operating envelope

1. Preserve **OBSERVE → INVESTIGATE → VALIDATE → READY → EXECUTE → MANAGE → SAFE/LEARN**, corresponding to the original **Observe → Understand → Forecast → Decide → Execute → Learn** workflow. Preserve all 18 original responsibilities, though they need not be 18 LLM processes (section 8).
2. The first trading horizon is **hours to days**. Equity and crypto have different market clocks. Scanning and approved execution are automatic whenever the Windows laptop is awake and connected; a missed short-lived opportunity is never traded after restart merely to catch up.
3. The owner approves the live operating envelope: account, tradable universe, strategy families, maximum exposures and losses, large-order threshold, and paper-to-live switch. Inside it, the system can select a strategy, submit an order, and manage an exit without approval for each trade. New strategy families, risk-limit loosening, and a degraded-data exception require explicit owner action. An exception cannot override an unknown broker position, an untrusted execution price, or a hard loss limit.
4. Code, not generative text, is the final authority for risk, order sizing, broker operations, and state transitions. A summary or sentiment score is evidence for a strategy, never an order by itself. **FLAT/no trade is a valid result.**
5. Keep metered data and model spend near zero, use the existing Windows 11 laptop with 8 GB RAM, and trade only the owner's own capital. These constraints rule out a promise of uninterrupted 24/7 coverage or sub-minute, full-market execution. Revisit them if measured opportunities require faster data or higher uptime.
6. Paper mode is the default. No live credentials or account identifiers belong in this code repository or in any Claude/Codex context. Revoke keys exposed in legacy notebooks or exports before connecting accounts.

## 2. Responsibilities and data flow

The [architecture and decision diagrams](docs/04-autonomous-design/DIAGRAMS.md) render on GitHub. One small local process can run the scheduler, collectors, scanner, decision engine, and broker adapter with bounded background workers. SQLite supplies durable queues and transactional state; Parquet stores larger historical series. No Redis, LangGraph, Docker, PostgreSQL, or always-on LLM is required for the first version.

| Responsibility | Input → output | Decision boundary |
|---|---|---|
| Market and account collection | Broker account, quotes, bars, corporate actions, crypto venue data → timestamped raw events | A feed outage or unmapped asset is recorded; it cannot silently become a valid feature. |
| Information Intelligence | Permitted filings, news, RSS, and social items → deduplicated, asset-mapped events; local summary, sentiment, novelty, event type | Runs independently and asynchronously. It cannot submit orders. Its own logic is retained from the TSLA work, but its old data and models are not trusted as live predictors. No purchased news/sentiment API is required by design. |
| Feature and market state | Raw events → versioned `FeatureSnapshot` for each asset and horizon | Every feature records source, event time, first-known time, calculation time, validity horizon, and quality. Historical replay may use only features known at that decision time. |
| Opportunity scanner | Cheap broad features → ranked `Candidate` records | A candidate triggers deeper analysis; it is not a trade. |
| Forecast and strategy selector | Candidate + eligible feature snapshot + registered strategy versions → `StrategyIntent` or FLAT | Selection only among owner-approved families and predeclared conditions. Component confidence remains uncombined until outcome calibration supports a probability. |
| Capital governor and hard risk gate | Intent + broker truth + owner risk policy → `ALLOW`, `BLOCK`, or `SAFE` with reason codes | Deterministic; cannot be relaxed by a model, summary, or agent. |
| Executor and position manager | Approved intent → broker order, fills, monitoring, predefined exit | Persist intent before sending. Use a stable client order ID; lookup and reconcile before retry. Changes in position follow the strategy's frozen exit contract. |
| Ledger and learning evaluator | Candidates, rejections, intents, fills, later outcomes → attribution, challenger evaluations, reports | New model versions are tested in replay and shadow before bounded promotion. A single loss never rewrites the live strategy. |

### Core records

All records carry a unique ID, UTC timestamps, schema version, source or producer version, and correlation ID. The minimum typed interfaces are:

| Record | Required content |
|---|---|
| `AssetEvent` | Asset/entity ID, asset class, event type, source ID, source document or market-data reference, `event_at`, `first_available_at`, `ingested_at`, quality status, payload hash. |
| `FeatureSnapshot` | Asset, horizon, feature-set and model versions, value or `MISSING`, source-event IDs, `available_at`, `expires_at`, quality flags, snapshot hash. |
| `Candidate` | Asset, detected-at time, scanner version, trigger and supporting feature IDs, candidate expiry. Retain rejected and expired candidates. |
| `StrategyIntent` | Candidate ID, approved strategy/version, LONG/SHORT/FLAT direction, desired target, prediction horizon, estimated costs, entry and exit conditions, evidence snapshot hash. SHORT is represented for the original workflow but blocked in the initial live envelope. |
| `RiskDecision` | Intent ID, broker-state hash, policy version, allowed quantity or zero, checks and reason codes, time validity. |
| `OrderIntent` and `Fill` | Stable client order ID, request/response, status changes, partial fills, fees, slippage, reconciliation result. |
| `Outcome` and `ModelEvaluation` | Strategy horizon, realized and benchmark results after costs, attribution category, evaluated data window, trial count, promotion/rollback decision. |

## 3. Different clocks for equities, crypto, and text

These are **initial design cadences**, not claims that a particular signal is profitable. A strategy must declare its own required feature freshness. Backtests and paper runs may cause a cadence to be changed through a versioned strategy update.

| Lane | Collection and decision cadence | First-version treatment |
|---|---|---|
| US equities | Cheap scan of up to **200 liquid, tradable equities** hourly during regular market hours, refreshed weekly by trailing liquidity. Use completed, full-market bars older than the free plan's 15-minute restriction for signal calculation; daily bars for longer context. Deep-analyse at most **10 active candidates**. | Decisions are hours-to-days, not opening-second reactions. At order time, obtain a current permitted quote, apply a price collar and reject if price quality is insufficient. Alpaca Basic's live equity feed is IEX only; it is not a full-market real-time feed. [Alpaca plans](https://docs.alpaca.markets/us/docs/about-market-data-api). |
| Spot BTC/ETH | Collect permitted live trades/quotes and minute bars while online; aggregate into 15-minute and hourly features. Evaluate first-version strategy entries **hourly**. Observe fills and predefined exits continuously while online. | Venue, spread, fee, and liquidity features are separate from equities. Historical and live feed location must match the account's execution venue. Crypto is live-disabled until Texas/account eligibility and exact costs are verified. [Alpaca crypto data](https://docs.alpaca.markets/us/docs/real-time-crypto-pricing-data). |
| Company filings and news | Detect new permitted items for held, watched, or shortlisted equities; priority-process them on arrival. Poll official filing metadata on a bounded schedule; preserve the published and first-seen times. | Summarize once per unique item; classify event, novelty, entity and sentiment. A strategy requiring that event waits for the finished, verified feature. SEC submissions and XBRL are available through official APIs. [SEC API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces). |
| Crypto news/social | Collect only from an approved source with known access and retention rights; form hourly attention, sentiment, novelty, and manipulation-quality aggregates. | No minute-by-minute LLM summaries or social-only orders. If no lawful, reliable source exists, the feature is `MISSING` and text-dependent strategies stay in shadow. |
| Portfolio and broker | Broker order updates as they arrive; account and open-order reconciliation on startup, after each execution, and periodically while online. | Broker positions, cash, fills, and working orders outrank local estimates. Every restart reconciles before a new order. |

The background text queue is separate from the market/order queue and has a fixed CPU and memory budget. Cheap source filtering and deduplication precede model inference. Summaries for held assets and active candidates have priority. A strategy that does not require text may proceed without it; a strategy that does require text may not substitute an old or unverified score. No pipeline scans every article about all 200 symbols with a large model each hour.

## 4. From evidence to an order

Example only: a new filing for a fictional company becomes an `AssetEvent`; local logic extracts `guidance_raised`, with a source reference and `first_available_at`. This feature alone creates no buy. The scanner later sees an eligible price/volume pattern and creates a `Candidate`. A registered, previously tested post-filing strategy reads a snapshot containing only then-available data and either emits an intent with an exit contract or returns FLAT. The gate checks actual holdings, cash, data age, spread, cost, policy and loss limits. Only an allowed intent becomes an order. The broker result and eventual strategy-horizon outcome are linked back to the candidate. The same record also explains **why a candidate was rejected**.

The strategy's estimated edge must be measured out of sample and after expected spread, fees, slippage, and taxes where relevant. Summary tone, confidence language, SHAP values, and a strong backtest do not independently authorize a trade. The old TSLA prototype's next-day-return feature leakage is a planted regression case for the replay tests.

## 5. Local state, audit, and recovery

| Store | Contents and rule |
|---|---|
| SQLite (WAL, one writer) | Asset/event index, dedup keys, feature metadata, candidates, strategy registry, owner policy, order intents, broker events, fills, reconciliation, outcomes, model evaluations, durable work queues. Append-only decision events retain previous versions rather than overwriting them. |
| Parquet | Historical market bars and derived numerical features, partitioned by asset class, asset, and date. Provenance and source licences remain in SQLite. |
| Model registry on disk | Immutable artifact, training cutoff, input schema/hash, software version, evaluation report, status (`challenger`, `shadow`, `pilot`, `champion`, `retired`). |
| Local reports and backups | Read-only owner dashboard/report; daily encrypted backup and tested restore. Store no API keys in backup manifests or Git. Git stores code, specs, decisions and test fixtures, **not** the live account ledger. |

On an ordinary restart: lock the runner; load last durable intents; query broker positions, cash and open/recent orders; adopt known fills; resolve or flag unknown activity; check data gaps and feature expiry; then resume new scanning. Expired candidates remain in the audit trail but are never submitted. If the laptop slept through a crypto move, the system does not invent a fill or chase that old event. An unresolved difference enters `SAFE` (no new risk), alerts the owner, and continues data collection. `HALT` requires an owner-recorded clearance. A current broker-side protective order, where supported, is a separate capability to verify; a laptop-only exit cannot protect a position while the laptop is off.

## 6. Learning and autonomous strategy choice

The live selector can automatically choose among **approved** strategies. Learning is a slower champion–challenger process: completed outcomes and rejected/missed candidates feed attribution; a challenger is retrained using only past-available features; replay is walk-forward with costs, corp-action handling, and a raw trial registry; the challenger then runs in shadow. A candidate enters pilot live exposure only after its **pre-registered, strategy-specific** evidence gate passes. A pilot cannot loosen the owner policy, add assets, or increase the approved family exposure. Drift, reconciliation errors, or a frozen loss condition immediately roll it back to the last champion or FLAT. A wholly new strategy family needs the owner's signed approval before live eligibility, as in the original v3 workflow.

Do not interpret each winning or losing trade as a training label for every component. Attribute prediction error, strategy-selection error, sizing error, execution cost, data error, and unforeseeable outcome separately. For low-frequency strategies, insufficient independent observations mean `INCONCLUSIVE` and continued shadow operation. The acceptance target is a reproducible improvement over a declared baseline after costs and within drawdown limits, not a guaranteed or constant return.

## 7. Safety and deployment gates

- **Before any paper orders:** data-source licences and terms checked; point-in-time replay green; test oracle and shuffled-label leak fixtures blocked; data-quality quarantine and entity mapping tests green; no credentials in tracked files; stop/kill path demonstrated.
- **Before automatic paper execution:** mock-broker crash/retry drills, duplicate IDs, partial fills, rejects, late fills, foreign orders, deposits, cash/fees, splits, data outages, and laptop restart all reconcile or enter SAFE. Store both a selected order and a rejected candidate with exact evidence and reason codes.
- **Before live:** owner records the risk envelope and explicitly enables live mode; live account's equity and crypto capabilities, order types, fees, and Texas eligibility are probed; a measured paper run is operationally clean; a reviewed pilot size and rollback rule are frozen. Paper fills cannot prove live costs: the broker's simulator omits market impact, latency slippage and queue position. [Alpaca paper limits](https://docs.alpaca.markets/us/v1.4.2/docs/paper-trading).
- **While live:** unexpected broker activity, untrusted prices, stale mandatory inputs, lost reconciliation, policy mismatch, repeated order failures, or an exhausted loss limit prevents new risk and alerts the owner. Risk-reducing action may occur only through a separately tested, broker-reconciled path. Every model promotion and policy change is versioned and reversible.

The [roadmap](docs/04-autonomous-design/ROADMAP.md) orders the work by demonstrable exit tests. The [decision record](docs/04-autonomous-design/DECISIONS.md) explains exactly how this owner-directed revision differs from the October 2 proposal without rewriting its historical evidence.

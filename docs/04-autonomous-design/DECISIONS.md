# Owner-directed architecture revision — decision record

**Date:** 2026-10-08. **Status:** proposal for review, not a deployed system. This record explains changes to the [October 2 architecture](../../ARCHITECTURE.md). It preserves that document and the [v1/v2/v3 owner vision](../00-original-vision/) as historical sources. The owner stated that the product should automatically discover and act on opportunities in equities and crypto, run locally, learn from recorded outcomes, and retain JARVIS's information-analysis foundation. The previous monthly, manually entered ETF order list does not meet that goal.

## Decisions and rationale

| Topic | Revised direction | What remains constrained |
|---|---|---|
| Product loop | Restore Observe/Understand/Forecast/Decide/Execute/Learn and the v3 operational states. Run decisions at hours-to-days horizons rather than only at the first five trading days of a month. | No guarantee of constant returns; no sub-minute full-market strategy on free data. |
| Autonomy | Automatic selection, sizing, execution and exits within an owner-signed envelope. New strategy families and paper-to-live still need owner approval. | Deterministic risk gate and broker reconciliation retain veto power; no Claude/Codex live order authority. |
| Assets | Cheap broad scan of liquid US equities, deep shortlist, direct spot BTC/ETH if account eligible. Long/flat at first; interface can represent SHORT for future eligibility. | No broad altcoin, options, leverage or short-selling at launch. Texas crypto access must be probed. |
| TSLA heritage | Retain local collection, news summarization, social and SEC feature engineering, forecasting and explanation as distinct functions. Rebuild with point-in-time data and independent evaluation. | Old XGBoost results are invalidated by target leakage; old prompts, data and SHAP outputs are not live trading evidence. |
| Data clocks | Equity delayed consolidated bars for hour-scale signals; live crypto data aggregated from minute bars; background text/event processing only for held or shortlisted assets. | Text never blocks a price-only trade. Free equity real-time feed is IEX only; laptop downtime loses short-lived opportunities. |
| Learning | Local candidate/trade/outcome ledger; automatic retraining and champion–challenger comparison; bounded promotion inside an approved strategy family, with rollback. | One trade does not prove or disprove a model. Insufficient evidence remains inconclusive/shadow. |
| Storage/runtime | SQLite operational state and audit, Parquet history, immutable model artifacts, encrypted local backup. One lean local service with bounded workers. | No need for the v3 Redis/Postgres/Docker/LangGraph stack on an 8 GB laptop. Reliable 24/7 operation would require a later hosting decision. |

**Evidence tension:** The October 2 review concluded that free data and this account size favoured daily-to-monthly decisions. The owner's hours-to-days target is therefore an experiment, not an established edge. Phase A3 must compare each shorter-horizon strategy with a price-only baseline after spread, fees, slippage, downtime and applicable taxes. If it fails, the system stays paper/shadow or FLAT; the cadence does not justify live trading by itself.

## All 18 v3 responsibilities remain accounted for

An entry below describes a **logical function**, not necessarily an LLM agent or an independent process. This keeps the original workflow without making every function a text-generating runtime agent.

| Original v3 role | Revised owner of the function |
|---|---|
| 1. Orchestrator / Supervisor | Local state machine, scheduler and durable queues. |
| 2. Goal & Capital Planner | Owner risk envelope and deterministic capital allocator. |
| 3. Opportunity Scanner | Broad cheap scan and ranked candidate shortlist. |
| 4. Data Trust Agent | Typed source validation, as-of snapshots and quarantine. |
| 5. Market / Technical Agent | Price, volume, trend and volatility feature lane. |
| 6. Flow / Microstructure Agent | Venue liquidity, spread and execution-cost lane; depth only where available and measured. |
| 7. News & Event Agent | Asynchronous local summaries, event types, relevance, novelty and sentiment features. |
| 8. Fundamental / Macro Agent | SEC/XBRL and macro feature lane, active only for strategies that consume it. |
| 9. Crypto Agent | BTC/ETH venue state, liquidity, cost and crypto-specific events. |
| 10. Manipulation Surveillance Agent | Data-integrity/anomaly quarantine; no unsupported claim of detecting unlawful conduct. |
| 11. Bull / Bear Agents | Independent research challenge and automated counter-evidence checks, never a live vote over an order. |
| 12. Model Ensemble | Versioned strategy-specific statistical models and price-only baselines. |
| 13. Confidence Calibrator | Outcome-based component calibration; no overall probability until enough evidence exists. |
| 14. Strategy / Portfolio Agent | Registered strategy selector and target/FLAT combiner. |
| 15. Capital Governor / Risk Agent | Deterministic, default-deny policy and kill/SAFE states. |
| 16. Execution Agent | Durable, idempotent broker adapter with fill and cancel state. |
| 17. Position Manager | Broker-reconciled monitoring and predefined exits. |
| 18. Ledger / Review Agent | SQLite audit, outcome attribution, challenger evaluation and owner report. |

## Explicitly unresolved dependencies

The owner must supply a risk envelope before live mode. Account-level crypto availability in Texas, source licences, quote quality, expected costs, and laptop uptime require probes. The plan is designed to remain paper/shadow or FLAT when any necessary dependency fails. Numeric strategy-promotion criteria belong in a signed, pre-registered strategy specification before its results are inspected; none should be retrofitted to an attractive backtest.

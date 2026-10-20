# JARVIS execution register

## Phase 1 foundation fixes — 2026-10-19

Branch `phase1/foundation-fixes` from `feature/jarvis-v1-implementation` (`3de6c82`). Plan: [Final workflow](https://github.com/aanshul1215/jarvis/blob/main/Final%20workflow(feedback%20requierd).md), Phase 1.

| Fix | Status | Evidence |
|---|---|---|
| Windows crash writing Parquet (`fsync` on a read-only handle) | TESTED LOCALLY (Windows) | Baseline on Windows 11: 11 failed / 9 passed. After: 31 passed. |
| Second writer on Windows raised `PermissionError` instead of `StorageError` | TESTED LOCALLY | `test_second_writer_gets_a_clear_error` |
| Exit order ID reused across identical trades (no sell placed, fake outcome) | TESTED LOCALLY | `test_second_identical_trade_places_a_new_exit`, `test_repeated_exit_call_does_not_duplicate_the_outcome` |
| Any open order froze every asset; no cancel path | TESTED LOCALLY | `test_expired_entry_order_is_cancelled_and_frees_the_desk`, `test_open_order_holds_only_its_own_asset` |
| Vendor-amended bar sent the desk to SAFE | TESTED LOCALLY | `test_vendor_bar_revision_is_stored_not_safe`; revision history kept, `load_bars(as_of=...)` |
| Daily-loss and drawdown limits never evaluated | TESTED LOCALLY (mock + fake client) | `test_daily_loss_limit_blocks_new_risk`, `test_drawdown_from_stored_peak_blocks_new_risk`, `test_alpaca_state_reports_daily_pnl_and_normalises_crypto_symbols` |
| Crypto fee taken from the received coin broke reconciliation | TESTED WITH MOCK — ACCOUNT BEHAVIOUR UNVERIFIED | `test_crypto_fee_shortfall_is_recorded_but_a_real_mismatch_is_still_safe`; confirm fee posting on the first paper fill |
| Crypto position symbol format (`BTCUSD` vs `BTC/USD`) | DEFENSIVE — ACCOUNT FORMAT UNVERIFIED | `test_symbol_normalisation`; confirm in the Phase 0 probe |
| CI on Windows and Linux | PASSING | 8/8 checks green on the first run (2026-10-19) |
| 24-hour mock paper soak (Phase 1 exit test) | PASSED (MOCK) | `jarvis soak --hours 24 --poll-seconds 60 --seed 7`: 1,440/1,440 cycles, never stopped, 0 cycle errors, 0 overdue orders, 14,645 journal events re-verified; 858 s wall time. Seed 7 produced only one trade, so path coverage relies on `tests/test_soak.py` (seed 11: cancel, partial fill, late fill, fee adjustment, bar revisions, session skips). |
| Defects found by the soak | FIXED | Sell quantity rounded up past the position (now rounded down to 8 decimals; under-$1 leftovers treated as flat); decision time taken before the quote was fetched; no outcome for partially filled entries. |

## Phase 2 data layer — 2026-10-19

| Item | Status | Evidence |
|---|---|---|
| Multiple datasets per asset (`1Day-raw`, `1Day-adjusted`, `1Hour-raw`, live `bars`) and generic hash-checked tables | TESTED LOCALLY | `tests/test_phase2_data.py` |
| FRED market-stress series (VIX, 3-month VIX, 10y, 2y, 10y-2y, 3-month bill, Baa credit spread) with publication-time availability and revisions | TESTED LOCALLY + LIVE DOWNLOAD | Live run 2026-10-19: ~84,000 observations, re-run adds 0; point-in-time check on 2020-03-16 returned Friday's VIX close 57.83 and Thursday's 10y yield |
| Excluded series | DECIDED | High-yield spread (FRED keeps ~3 years only); NFCI and STLFSI4 (revised after publication; need vintages) |
| Alpaca history back-fill (SIP, raw and adjusted, deterministic availability) | TESTED WITH FAKE CLIENT — NEEDS PAPER KEYS | Rebuild from scratch gives byte-identical files; `jarvis backfill` fails closed without keys |
| Data-quality checks (duplicates, gaps, spikes, stale prices, zero volume) | TESTED LOCALLY | `jarvis data-check` |
| Proposed starting universe (27 stocks/ETFs + BTC/ETH) | PROPOSED — OWNER TO CONFIRM | `config/universe.example.json` |
| SEC EDGAR filings, earnings releases and fundamentals | TESTED LOCALLY + LIVE RUN | Live 2026-10-19 (AAPL, MSFT, SPY): ~2,200 filings, 87 earnings releases timed from index pages, ~3,100 fundamental values; re-run costs 3 requests per company. The submissions JSON `acceptanceDateTime` was found to be unreliable (8 h off for AAPL earnings 8-Ks), so earnings use the index-page "Accepted" time |
| Event calendars (FOMC decisions, CPI and jobs releases) | TESTED LOCALLY + LIVE RUN | Live build: 381 events 2016–2027 (8 FOMC, 12 CPI, 12 jobs per year); 2020 emergency meetings stored as unscheduled, the cancelled 17–18 March 2020 meeting never counts as upcoming |
| Breadth universe, news/social collectors | NOT STARTED | Collectors need source decisions (Reddit app credentials; Alpaca news once keys exist) |

## Phase 3 evaluation harness — 2026-10-19

| Item | Status | Evidence |
|---|---|---|
| Same code path: real PaperDesk, engine, strategies and Governor replayed on stored history | TESTED LOCALLY (SYNTHETIC DATA) | `replay.py` (ReplayClock, ReplayData, ReplayBroker), `harness.py` |
| Point-in-time guard: every replay read refuses bars not yet available; violations abort the evaluation | TESTED | `test_a_data_bug_that_leaks_the_future_aborts_the_evaluation`, `test_replay_fills_at_the_next_open_with_costs_and_honours_limits` |
| Fills at the next bar's open, limit orders honoured, costs per side (equity 5 bps; crypto 25 bps fee + 5 bps spread), doubled-cost stress run | TESTED | as above |
| Benchmarks: equal-weight buy-and-hold, equal-weight monthly rebalance (with costs), cash at the 3-month T-bill rate (FRED) | TESTED | harness runs |
| Metrics: total return, CAGR, volatility, Sharpe, Sortino, max drawdown, 5% expected shortfall, turnover, exposure, beta/alpha to benchmark, trade stats | TESTED | `metrics.py` |
| Gate: leak alarms, â‰¥30 trades, block-bootstrap significance vs benchmark with Bonferroni correction across registered trials, â‰¥60% of years beating the benchmark, positive with doubled costs | TESTED | random entry fails (two seeds; second seed faces a stricter bar) |
| Future-poisoning leak test (signals and order inputs before a cut-off must not change when later bars are scrambled) | TESTED | Planted v1-style leak (Sharpe â‰ˆ 2.2, below the statistical alarm) flagged; honest run of the same strategy passes |
| Append-only, hash-chained experiment registry; holdout usable once per strategy configuration | TESTED | `test_holdout_may_be_evaluated_once` |
| Performance | MEASURED | 6-month replay 20.2 s → 0.7 s after removing a per-cycle journal re-read; full evaluation of 2.3 years × 4 stocks (base, doubled costs, benchmarks, 8 poisoning cut-offs) ≈ 20–35 s |
| Real-data evaluation | BLOCKED — NEEDS ALPACA PAPER KEYS | `jarvis backtest --universe ... --strategy ...` runs once `backfill` has data |

## Phase 7 strategy selector — 2026-10-20

| Item | Status | Evidence |
|---|---|---|
| Selector hooks in the real order path: per-strategy size multipliers (capped at the owner's per-order limit, rounded down) and a per-entry filter, both journaled | TESTED | `test_engine_applies_multipliers_and_the_filter_to_new_entries` |
| Sleeves (each strategy alone) with trade records: entry features, exit decision time, return net of fees | TESTED | `test_trade_records_charge_only_fees_on_top_of_fill_prices` |
| Allocators: equal weight, regime lookup, contextual Thompson-sampling bandit; schedules see only earlier days | TESTED | Planted-structure and noise tests; scrambling the future leaves earlier allocations unchanged |
| Meta-label filter (yearly logistic regression, 7-day purge) | TESTED | Learns a planted feature; ignores trades that exit after the cut-off |
| Chain of stages through combined replays, with a gate (significance, smaller drawdown, double costs); holdout only confirms development's choice, once, and is claimed before it runs | TESTED (synthetic) | On a random-walk market every stage fails and equal weight is kept |
| Pre-registration | WRITTEN before any real run | `docs/08-selector/SELECTOR_REGISTER.md` |
| Phase 7 exit test (beats the equal-weight blend on unseen periods, after costs, with smaller drawdowns) | BLOCKED — NEEDS ALPACA BACK-FILL | `jarvis selector-study --universe …` |
| Independent code review | DONE — 2 definite bugs fixed (spread counted twice in trade labels; holdout re-ran the whole selection) plus timing, rounding and bookkeeping fixes | LOG 2026-10-20 |

## Phase 5 situational-awareness models — 2026-10-19

| Item | Status | Evidence |
|---|---|---|
| Volatility forecasters (rolling-20 baseline, EWMA, HAR, GARCH) with month-start walk-forward refits; live forecast identical to the study | TESTED | Recovers a simulated GARCH process; future-scrambling and live-parity tests for every model |
| Volatility study on real data (FRED stocks 1975–2023, crypto 2017–2023) | **PASSED — GARCH wins** (development); holdout consistent on all 5 series, significant for stocks only | `docs/07-awareness/MODEL_REGISTER.md` Results |
| Volatility sets position size (1% daily risk at base, capped at 1.5× and at the owner's per-order limit; baseline used until GARCH has 1,000 returns) | TESTED | Replay sizing test with future-poisoning check |
| Regime detectors (sma200, trend×vol, filtered HMM) and FRED stress ablation | TESTED; **real-data result negative**: no detector beat "no regime"; stress signal dropped | Register Results; regime labels still recorded |
| Correlation model (diagonal, sample, Ledoit–Wolf constant correlation) | TESTED; preliminary FRED result: not significant in development (p 0.09), significant in holdout (p 0.005) | The universe study decides; BLOCKED — NEEDS ALPACA KEYS |
| Transaction-cost model and realised shortfall | BUILT; BLOCKED — NEEDS PAPER FILLS | `cost-report` |
| Situation snapshot every cycle (stress, breadth, events, crypto, per-asset regime and volatility, desk state) | TESTED | `test_situation_snapshot_combines_stress_breadth_events_and_desk_state` |
| Independent code review | DONE — 6 definite bugs fixed before any real-data run | LOG 2026-10-19 |
| Phase 5 exit test ("each model beats its baseline on unseen data, or it is dropped") | Volatility: kept (GARCH). Regime: dropped. Correlation: pending universe data. Costs: pending fills | |

## Phase 4 strategy library — 2026-10-19

| Item | Status | Evidence |
|---|---|---|
| Long-horizon features (returns to 252 bars, 12-1 momentum, 50/200-bar averages, RSI(2)/RSI(14), Bollinger z, ATR, volatility ratio, 20-bar breakdown, distance from 1-year high) | TESTED | Hand-checked on a known series (ret_252, mom_12_1, sma_200, RSI, ATR) |
| Strategy interface: entry score with cross-asset context; strategy-owned exits; ATR stop-loss; maximum holding period; one position per asset | TESTED | `test_engine_applies_the_owning_strategys_stop_loss_and_signal_exit` |
| Paper loop in two passes (gather, then decide on one consistent point-in-time view of all assets) | TESTED | full suite |
| Point-in-time earnings calendar for event strategies (harness and paper command) | TESTED | `test_earnings_calendar_is_point_in_time` |
| Five strategies pre-registered before any real-data run: trend-sma200, meanrev-rsi2, volatility-breakout, relative-strength, earnings-drift (plus the breakout baseline and random control) | REGISTERED — NOT YET EVALUATED ON REAL DATA | `docs/06-strategies/STRATEGY_REGISTER.md`; unit tests per rule; every strategy trades in a synthetic replay and passes the future-poisoning test |
| Phase 4 exit test (each strategy has an out-of-sample daily return series) | BLOCKED — NEEDS ALPACA PAPER KEYS | The development runs (2016-03-01 to 2023-12-31) are pre-registered; results will be appended to the register |

## Implementation dependency map — 2026-10-18

**Development branch:** `feature/jarvis-v1-implementation`, based on `origin/branch-3` at `438c778f45d679fe000720a7741b8ae743dc4bfe`. Working tree was clean at branch creation. Historical research and `legacy-v1/` remain references; no autonomous runtime existed at the baseline.

```text
typed contracts and configuration
  -> local JSONL/Parquet StorageAdapter + replay/recovery
  -> equity/crypto bars + point-in-time features + candidates
  -> approved strategy selector -> deterministic Governor
  -> durable intent -> MockBroker -> reconciliation/position manager
  -> outcome/latency journal -> CSV reports -> read-only dashboard
  -> offline backtest/model lab -> challenger registry
  -> read-only Alpaca probes -> paper adapter (requires owner inputs)
```

The runtime priority is broker reconciliation and protection, then timely market decisions, then ingestion, then bounded research. The Alpaca connector must never enable a live endpoint. Research cannot promote an unapproved strategy or change a risk limit.

| Milestone | Current status | Dependencies | Acceptance evidence |
|---|---|---|---|
| V1-01 Offline vertical slice | TESTED LOCALLY | Typed contracts and local files | Fixture → features → candidate → approved strategy/FLAT → Governor → mock fill/exit → journal → dashboard; six focused tests passed on 2026-10-18. Remaining release review: independent audit and clean clone. |
| V1-02 Market/research | PARTIAL — TESTED WITH SYNTHETIC FIXTURES | V1-01 | Equity/crypto feature Parquet, expanding walk-forward evaluation, holdout, model registry and hypothetical backtest reports; broader data feeds and drift controls pending. |
| V1-03 Alpaca paper adapter | PARTIAL — MOCK CYCLE TESTED, ACCOUNT UNVERIFIED | V1-01 plus read-only account/entitlement probes | Guarded multiasset paper cycle and SDK request contract implemented; 18 local tests pass. Owner configuration, actual account lifecycle, feed entitlement, and independent review remain open. |
| V1-04 Release review | NOT STARTED | V1-01–03 | Clean clone, full tests, security scan, independent review, no critical failures. |

**Current release blocker:** no owner-signed paper risk envelope, local paper credentials, or account-capability evidence is available in this task. Mock tests cannot count as Alpaca paper verification. The implementation branch will not be merged into `branch-3` while these gates are open.

**2026-10-18 implementation check:** `.venv/bin/python -m pytest -q` passed 20 tests; `train --fixture` and `backtest --fixture` completed for AAPL and BTC/USD using synthetic data only. Models remain `RESEARCH`; those synthetic metrics do not establish predictive performance. `paper --dry-run` is read-only; paper orders require private owner policy/runtime files, valid credentials, and the explicit `--enable-orders` flag. Both paper commands failed closed locally because owner configuration was absent. An event-driven local information summarizer now records explicitly unvalidated asset features outside the fast path. The package built in the existing virtual environment with the bundled build backend. A fresh-clone installation and account-connected paper behavior are NOT VERIFIED.

**Current state (2026-10-15): documentation only.** No A0–A5 implementation or acceptance test has passed. [FINAL_IMPLEMENTATION_PLAN.md](FINAL_IMPLEMENTATION_PLAN.md) is the proposed blueprint; [local storage contract](docs/05-final-implementation/LOCAL_STORAGE_AND_SCHEMAS.md) is the V1 storage decision.

| Ticket | Status | Dependency | Next evidence |
|---|---|---|---|
| A0-01 Repository and leakage audit | **NEXT — NOT STARTED** | Human owner: TBD | Read-only inventory of tracked files, existing code vs proposals, and secret-pattern findings **without printing values**; owner records rotation status for exposed legacy keys. |
| A0-02 Source, licence, crypto and entitlement probes | NOT STARTED | A0-01 | Redacted [probe register](docs/05-final-implementation/PROBE_REGISTER.md); no unverified account capability called PASS. |
| A0-03 Owner paper setup and risk inputs | NOT STARTED | A0-01 | Completed [setup checklist](docs/05-final-implementation/USER_SETUP_AND_REQUIREMENTS.md) and owner decisions; no keys in Git/chat. |
| A1-01 Typed event and time schema | NOT STARTED | A0 outputs | Schema fixtures and point-in-time tests. |
| A1-02 File `StorageAdapter`, journal and CSV projections | NOT STARTED | A1-01 | Atomic append, crash/replay, idempotency and report tests in [storage acceptance](docs/05-final-implementation/LOCAL_STORAGE_AND_SCHEMAS.md). |
| A1-03 Parquet and replay | NOT STARTED | A1-01/02 | Reproducible features and immutable partition hashes. |
| A2–A5 | NOT STARTED | Prior phase gates | See [phase acceptance](docs/05-final-implementation/PHASE_ACCEPTANCE_AND_OWNER_MATRIX.md). |

Each future ticket must record purpose, named human owner, files, dependencies, verification command and result, rollback, reviewer and commit. Do not mark a gate passed from a plan or a mock result alone. Research jobs cannot block the time-critical decision or reconciliation path.

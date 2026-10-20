# JARVIS execution register

## Phase 1 foundation fixes â€” 2026-10-19

Branch `phase1/foundation-fixes` from `feature/jarvis-v1-implementation` (`3de6c82`). Plan: [Final workflow](https://github.com/aanshul1215/jarvis/blob/main/Final%20workflow(feedback%20requierd).md), Phase 1.

| Fix | Status | Evidence |
|---|---|---|
| Windows crash writing Parquet (`fsync` on a read-only handle) | TESTED LOCALLY (Windows) | Baseline on Windows 11: 11 failed / 9 passed. After: 31 passed. |
| Second writer on Windows raised `PermissionError` instead of `StorageError` | TESTED LOCALLY | `test_second_writer_gets_a_clear_error` |
| Exit order ID reused across identical trades (no sell placed, fake outcome) | TESTED LOCALLY | `test_second_identical_trade_places_a_new_exit`, `test_repeated_exit_call_does_not_duplicate_the_outcome` |
| Any open order froze every asset; no cancel path | TESTED LOCALLY | `test_expired_entry_order_is_cancelled_and_frees_the_desk`, `test_open_order_holds_only_its_own_asset` |
| Vendor-amended bar sent the desk to SAFE | TESTED LOCALLY | `test_vendor_bar_revision_is_stored_not_safe`; revision history kept, `load_bars(as_of=...)` |
| Daily-loss and drawdown limits never evaluated | TESTED LOCALLY (mock + fake client) | `test_daily_loss_limit_blocks_new_risk`, `test_drawdown_from_stored_peak_blocks_new_risk`, `test_alpaca_state_reports_daily_pnl_and_normalises_crypto_symbols` |
| Crypto fee taken from the received coin broke reconciliation | TESTED WITH MOCK â€” ACCOUNT BEHAVIOUR UNVERIFIED | `test_crypto_fee_shortfall_is_recorded_but_a_real_mismatch_is_still_safe`; confirm fee posting on the first paper fill |
| Crypto position symbol format (`BTCUSD` vs `BTC/USD`) | DEFENSIVE â€” ACCOUNT FORMAT UNVERIFIED | `test_symbol_normalisation`; confirm in the Phase 0 probe |
| CI on Windows and Linux | PASSING | 8/8 checks green on the first run (2026-10-19) |
| 24-hour mock paper soak (Phase 1 exit test) | PASSED (MOCK) | `jarvis soak --hours 24 --poll-seconds 60 --seed 7`: 1,440/1,440 cycles, never stopped, 0 cycle errors, 0 overdue orders, 14,645 journal events re-verified; 858 s wall time. Seed 7 produced only one trade, so path coverage relies on `tests/test_soak.py` (seed 11: cancel, partial fill, late fill, fee adjustment, bar revisions, session skips). |
| Defects found by the soak | FIXED | Sell quantity rounded up past the position (now rounded down to 8 decimals; under-$1 leftovers treated as flat); decision time taken before the quote was fetched; no outcome for partially filled entries. |

## Phase 2 data layer â€” 2026-10-19

| Item | Status | Evidence |
|---|---|---|
| Multiple datasets per asset (`1Day-raw`, `1Day-adjusted`, `1Hour-raw`, live `bars`) and generic hash-checked tables | TESTED LOCALLY | `tests/test_phase2_data.py` |
| FRED market-stress series (VIX, 3-month VIX, 10y, 2y, 10y-2y, 3-month bill, Baa credit spread) with publication-time availability and revisions | TESTED LOCALLY + LIVE DOWNLOAD | Live run 2026-10-19: ~84,000 observations, re-run adds 0; point-in-time check on 2020-03-16 returned Friday's VIX close 57.83 and Thursday's 10y yield |
| Excluded series | DECIDED | High-yield spread (FRED keeps ~3 years only); NFCI and STLFSI4 (revised after publication; need vintages) |
| Alpaca history back-fill (SIP, raw and adjusted, deterministic availability) | TESTED WITH FAKE CLIENT â€” NEEDS PAPER KEYS | Rebuild from scratch gives byte-identical files; `jarvis backfill` fails closed without keys |
| Data-quality checks (duplicates, gaps, spikes, stale prices, zero volume) | TESTED LOCALLY | `jarvis data-check` |
| Proposed starting universe (27 stocks/ETFs + BTC/ETH) | PROPOSED â€” OWNER TO CONFIRM | `config/universe.example.json` |
| SEC EDGAR filings, event calendars, breadth universe, news/social collectors | NOT STARTED | EDGAR needs a contact for its required User-Agent; collectors need source decisions |

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

# JARVIS execution register

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

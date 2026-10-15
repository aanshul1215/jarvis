# JARVIS execution register

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

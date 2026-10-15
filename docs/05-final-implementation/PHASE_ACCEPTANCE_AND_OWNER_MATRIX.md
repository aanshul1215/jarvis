# A0–A5 ownership and acceptance

**All phases are NOT STARTED.** Owners are roles until humans are named. The [final plan](../../FINAL_IMPLEMENTATION_PLAN.md) expands each phase; the [storage contract](LOCAL_STORAGE_AND_SCHEMAS.md) gives file-specific tests.

| Phase | Accountable human | Required evidence before exit |
|---|---|---|
| A0 | Owner + implementation lead (TBD) | Repository/leakage inventory, key rotation decision, account/data rights and owner policy inputs recorded without secrets. |
| A1 | Data/platform lead + independent reviewer (TBD) | CSV/Parquet/JSONL schemas; exact save/load and feature replay; model lineage; atomic/crash recovery; broker reconciliation design and isolated restore. |
| A2 | Market data lead (TBD) | Separate equity/crypto data quality, bounded text backlog, rejected candidate retention, measured latency/access traces, research isolation. |
| A3 | Execution and risk leads (TBD) | Mock then paper end-to-end run; default-deny Governor; no duplicate order under timeout/restart; broker state reconciliation; Excel-readable report. |
| A4 | Quant lead + independent validator (TBD) | Pre-registered trials, leakage controls, after-cost benchmark, calibration/tail risk, champion/challenger and reproducible rollback. |
| A5 | Owner + independent reviewer (TBD) | Paper operational record, live account/crypto eligibility, cost and incident evidence, signed risk envelope; no automatic live launch. |

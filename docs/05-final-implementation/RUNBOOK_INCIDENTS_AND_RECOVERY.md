# Incident and recovery runbook — implementation target

This is a planned procedure, not a tested operating runbook.

1. On unknown broker state, file corruption, failed journal sync, stale required data or hard limit breach, enter SAFE: block new risk and record/alert. A separately tested risk-reducing path may remain available.
2. Stop the writer, preserve journal and partial files, and copy evidence to quarantine. Do not hand-edit the active JSONL or CSV projection.
3. Check file hashes, sequence gaps, last complete JSONL record and published Parquet/JSON manifests. Rebuild projections from validated source records. Quarantine mid-file corruption; do not silently skip it.
4. Query broker positions, cash, open/recent orders and fills. Match stable client IDs and broker IDs. Unknown activity remains SAFE; never retry a timed-out order before lookup.
5. Restore encrypted backup to an isolated directory if necessary, verify hashes and replay, then reconcile broker truth again. Expired opportunities remain recorded but cannot be submitted.
6. Record cause, timestamps, owner clearance and regression test. HALT re-arm requires explicit owner action.

A1/A3 must fault-test this procedure before automatic paper orders; A5 reviews it again for any live pilot.

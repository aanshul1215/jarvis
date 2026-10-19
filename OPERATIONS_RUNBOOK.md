# JARVIS operations runbook

## Current modes

`demo` is synthetic SHADOW mode with a mock broker. `backtest --fixture` and `train --fixture` use synthetic historical fixtures and cannot authorize orders. `alpaca-check` and `paper --dry-run` are read-only. An Alpaca paper cycle exists behind a private owner policy, exact strategy-version allowlist, broker and quote checks, and the explicit `--enable-orders` CLI flag. Account-connected behavior is unverified in this development environment. There is no live broker mode.

## Startup and recovery

1. Run `python -m jarvis doctor` and inspect FAIL/UNVERIFIED results.
2. Keep `JARVIS_HOME` outside Git with access limited to the operator.
3. Stop the writer before backup. The writer lock rejects a second writer.
4. At restart, verify the journal hash chain. A trailing incomplete JSONL line is quarantined; corruption within completed lines stops startup.
5. Reconcile open orders and positions with broker truth before decisions resume. Unknown orders or position mismatches enter SAFE.
6. Never blindly retry an uncertain submission. Query by stable client order ID first.

The operator may run `paper --once --enable-orders` for one paper cycle or `paper --loop --enable-orders` for periodic cycles only after account and risk review. `--loop` uses the private poll interval (minimum 60 seconds). Equities are skipped while Alpaca's market clock is closed; eligible crypto continues on its own clock. Entry requests use a buy limit at the verified ask; time exits use market sells. Existing open orders hold further decisions pending reconciliation. Missing or stale bars, stale quotes, unavailable asset permissions, or unknown broker state prevent new orders. Stop with Ctrl-C. Reconcile the account before resuming.

For the offline mock path, run `python -m jarvis demo` and inspect the journal and dashboard trace. `tests/test_vertical.py` exercises a timeout after broker acceptance, duplicate suppression, restart mismatch, and partial tail recovery. These tests do not establish account-connected behavior.

## Data and model controls

Market and feature Parquet files have SHA-256 manifests. The operational JSONL journal has a hash chain, monotonic sequence, and unique event IDs. CSV reports are projections; the journal is the source for decision replay. Model experiment JSON and model files live under `JARVIS_HOME`. No challenger is promoted by the training command. Restore backups to a new path, verify file hashes, then reconcile the broker before any execution.

`python -m jarvis --home "$JARVIS_HOME" review` projects completed outcomes and rejected reasons into local JSON/CSV. Bayesian win estimates are descriptive and separated by MOCK/PAPER evidence. Fees and slippage remain unverified, and this review never alters approvals or risk limits.

## Incident response

On data corruption, unknown broker state, stale quotes, missing policy, or unclear account capability, halt order submission and preserve the runtime directory for investigation. Do not edit the journal manually. Broker positions and orders take priority over locally inferred state. The dashboard is read-only and cannot override the Governor.

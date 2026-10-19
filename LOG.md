# Engineering execution log

## 2026-10-18 — Implementation baseline and dependency map

- Branch: `feature/jarvis-v1-implementation`, created from clean `origin/branch-3` (`438c778f45d679fe000720a7741b8ae743dc4bfe`) after `git fetch origin --prune`. No runtime code existed beyond the invalidated `legacy-v1/` TSLA reference.
- Inspected the attached implementation prompt and current final plan. The branch-3 file-based V1 storage decision governs implementation. Existing 18 roles are logical responsibilities, not deployed agents.
- Dependency map and milestone gates recorded in `EXECUTION.md`. Python 3.9.6 is installed system-wide; the bundled Python 3.12.14 is available for development. No pytest, pyarrow, alpaca-py, scikit-learn, or FastAPI was preinstalled in the system interpreter. Account-connected paper verification is pending owner-controlled inputs.
- Next: implement and test V1-01 offline vertical slice. No order has been sent.

## 2026-10-18 — V1-01 offline vertical slice

- Added typed multiasset bars/features/candidates/intents/risk/events, local JSONL hash-chain and Parquet bar adapter, baseline scanner/strategy, deterministic Governor, mock broker, paper-only Alpaca boundary, offline fixture for AAPL and BTC/USD, read-only local desk view, CLI demo and focused tests.
- Executed `PYTHONPATH=src .venv/bin/python -m jarvis demo`: synthetic AAPL and BTC/USD candidates processed through mock decisions; no external order or market call. Executed `.venv/bin/python -m pytest -q tests/test_vertical.py`: **6 passed**. Results are local mock/fixture evidence only.
- Known gaps: research/backtest/train commands, owner-approved paper execution workflow, feature Parquet partitions, full 18-role function map, clean-clone installation and account-connected Alpaca tests are still outstanding. Paper order endpoint remains disabled; no live endpoint is present.

Append dated entries with branch, commit, commands actually run, evidence, failures and next ticket. This file tracks implementation and verification. [docs/LOG.md](docs/LOG.md) remains the project decision chronology.

## 2026-10-15 — Documentation preparation

- Base verified: `origin/branch-1` at `0da7e0858a170cb1fac37bdffed95d984bea694f`; `branch-3` absent when inspected. Created local `branch-3` from that base.
- Imported the supplied Markdown plan as a source document, then revised its SQLite statements to the owner's file-based V1 decision. The supplied text and DOCX are planning references, not evidence of installed functionality.
- Storage, broker, model, and phase tests remain **NOT RUN / NOT IMPLEMENTED**. Documentation-only checks run before staging: `git diff --check` passed; 14 Markdown files had zero broken local links; 13 CSV templates each had exactly one header row with required common columns and no duplicate names; a filename-only scan for common credential patterns found no matching new/edited files. These checks do not prove storage behavior or comprehensive secret absence.
- Open implementation facts: account permissions, Texas crypto eligibility/venue, current data-tier limits and fees, real laptop latency, owner risk envelope and backup path. Next ticket: A0-01 in `EXECUTION.md`.

## 2026-10-18 — V1-02 synthetic research increment

- Branch: `feature/jarvis-v1-implementation`. Added local feature Parquet persistence, deterministic equity/crypto research fixtures, chronological train/validation/holdout evaluation, constant and logistic baselines, transaction-cost-aware hypothetical metrics, model artifacts, experiment JSON, and CSV reports. Model approval remains `RESEARCH` with no automatic promotion.
- Added strict private owner policy loader, a read-only `paper --dry-run` setup gate, `.env.example`, and clone/setup/operations documentation. No Alpaca order was sent.
- Commands: `.venv/bin/python -m pytest -q` passed 10 tests before the final policy test addition; `PYTHONPATH=src .venv/bin/python -m jarvis --home /tmp/jarvis-research-check train --fixture` completed for AAPL and BTC/USD. Final test count and commit reference to be updated after the full verification run.
- Remaining: live market-data ingestion and entitlements, account-connected paper lifecycle, position monitor, fuller research safeguards, setup health probes, independent review, clean-clone install, and release decision. Synthetic fixture metrics are not evidence of real returns.

## 2026-10-18 — Safety and verification increment

- Added read-only Alpaca equity/crypto bar and quote boundary, with explicit feed and request-duration diagnostics, plus an independent fake-client contract test. PAPER decisions require an explicit fresh quote and remain disabled in the CLI.
- Added broker-value-based portfolio exposure checks; unknown position values fail closed. Added time-based position monitoring from the recorded order contract and a local post-trade review projection. Review separates MOCK from PAPER and never changes approvals.
- Commands: `.venv/bin/python -m pytest -q` **13 passed, 1 third-party deprecation warning**; `PYTHONPATH=src .venv/bin/python -m jarvis demo` worked with AAPL and BTC/USD mock fills/exits; `backtest --fixture` and `train --fixture` worked on synthetic data; `paper --dry-run` returned exit 2 and `owner_policy: FAIL` because no private policy exists. `compileall` and `git diff --check` passed.
- Attempted `.venv/bin/python -m pip install -e '.[dev]' --no-deps --no-build-isolation`: **FAILED** because `setuptools.build_meta` is not installed in the current virtual environment. Clean-clone installation remains NOT RUN. No Alpaca account call or order was made.
- Commit reference pending. Remaining critical gates: owner paper policy, valid paper credentials, account/feed/asset probes, account-connected lifecycle, independent review, and clean installation.

## 2026-10-18 — Guarded paper cycle and order recovery

- Added private per-asset paper sizing and exact strategy-version configuration, a bounded equity/crypto paper cycle, equity market-clock check, stale bar/quote blocks, buy limit orders, open-order hold, and `paper --once/--loop --enable-orders` commands. These are opt-in and use Alpaca's paper client only. No external paper order was submitted.
- Reconciliation now polls known unsettled orders and records fill/status updates before position comparison. A durable intent with no broker record enters SAFE. Added mock tests for paper cycling, stale data, buy limit order construction, and partial-fill restart recovery.
- Commands: `.venv/bin/python -m pytest -q` **18 passed, 1 third-party deprecation warning**; `compileall` and `git diff --check` passed. The order-capable command and read-only dry-run both returned exit 2 with owner policy missing. A filename-only secret-pattern scan of new source, tests and setup docs returned no matches.
- Initial editable install without build isolation failed because `.venv` lacked setuptools. Retried using the bundled Python runtime's setuptools on `PYTHONPATH`; the local editable wheel built and installed. This does not establish a fresh-clone installation.
- Account-connected paper verification, private owner values, independent review, clean-clone install, and release approval remain open. No merge into `branch-3` while these gates are open.

## 2026-10-18 — Responsibility map and local information path

- Published the feature tree to GitHub branch `feature/jarvis-v1-implementation` through the connected GitHub API after the Git CLI push failed for missing HTTPS credentials. The remote commit `1e6b51a8bd01474f3a4afb9dec083ef75afad8ff` has the exact local Git tree `6b70fd252b602a2a064c88f2ad9393aaaf6459d1`; `branch-3` and `main` were not changed.
- Added typed purpose/input/output/evidence definitions for all 18 logical responsibilities. The dashboard now derives recorded state from actual event types and shows partial/unavailable status explicitly.
- Added a separate local information-ingestion command using a dated JSON document, deterministic extractive summary, unvalidated lexical counts, raw/feature JSON storage, and one `INFO_FEATURE` event per source document. It is scoped to a named asset and has no trade authority. The bundled sample is fictional.
- Commands: `.venv/bin/python -m pytest -q` **20 passed, 1 third-party deprecation warning**; `info-ingest --file info.example.json` completed on the fictional BTC/USD sample; `git diff --check` passed. No external source or broker order was contacted for this increment.
- Remaining: SEC/news collectors and licensing, validated event models, account-connected paper/stream tests, full strategy discovery and model controls, and release gates. Commit and remote publication of this increment pending.

## 2026-10-18 — Research validation increment

- Added expanding walk-forward folds with one observation embargo, holdout probability-calibration bins, immutable artifact conflict detection, and a versioned local model registry. The registry records both constant and logistic models as `RESEARCH`; no training result can promote itself.
- Commands: `.venv/bin/python -m pytest -q` **20 passed**; `train --fixture` completed for AAPL and BTC/USD and wrote the registry. The output is synthetic and does not establish real predictive performance. Account and release gates remain open.

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

## 2026-10-19 — Phase 1 foundation fixes

- Branch `phase1/foundation-fixes`, based on `origin/feature/jarvis-v1-implementation` at `3de6c82`. Generated by Claude (Claude Code, `claude-opus-5-5`) at the owner's request; teammate review pending. Plan reference: Phase 1 of `Final workflow(feedback requierd).md` on `main`.
- Fixed: Windows `fsync` on a read-only handle (every Parquet write failed on Windows); Windows second-writer `PermissionError`; exit client order ID reused across identical trades (no sell placed, duplicate `TRADE_OUTCOME`); any open order holding every asset with no cancel path (expired entry orders are now cancelled and only that asset waits); vendor bar amendments raising `StorageError` and SAFE (now stored as revisions; `load_bars(as_of=..., all_revisions=...)`); daily-loss and drawdown limits never evaluated (Alpaca `equity - last_equity`, stored equity high-water mark); crypto fee taken from the received coin breaking reconciliation (recorded as `POSITION_ADJUSTMENT` up to 0.4% of quantity bought); defensive `BTCUSD` → `BTC/USD` symbol normalisation. `ORDER_INTENT` now records `asset_class` and `expires_at`.
- Commands (Windows 11, Python 3.13, fresh venv, `pip install -e ".[dev]"`): baseline `pytest -q` on the unmodified branch **11 failed, 9 passed**; after the fixes **31 passed, 1 third-party deprecation warning**; `python -m jarvis demo` completed with AAPL and BTC/USD mock fills. Added `.github/workflows/tests.yml` (Windows and Ubuntu, Python 3.12 and 3.13).
- Changed test: `test_bar_reingestion_preserves_first_availability` now expects a revision instead of `StorageError`, matching the new behaviour.
- Not verified: account-connected Alpaca behaviour, crypto fee posting and position symbol format (both need the Phase 0 paper probe), first CI run, the 24-hour mock soak required by the Phase 1 exit test. No broker or market-data call was made.

## 2026-10-19 — Phase 1 exit test and Phase 2 data layer (part 1)

- Branch `phase1/foundation-fixes` (no pull requests, at the owner's request; PR #1 closed). Generated by Claude (Claude Code, `claude-opus-5-5`).
- Phase 1: added `jarvis soak` (simulated clock, synthetic bars with breakouts and vendor amendments, mock broker with unfilled/partial/late fills, session hours, crypto fees in coin). The soak found three defects, all fixed: sell quantity rounded up past the position; decision time taken before the quote was fetched (quotes looked like they came from the future); no outcome for partially filled entries. The journal writer now serves an in-memory copy instead of re-parsing the file on every read.
- Phase 1 exit test: `jarvis soak --hours 24 --poll-seconds 60 --seed 7` passed — 1,440/1,440 cycles, never stopped, 0 cycle errors, 0 overdue entry orders, 14,645 journal events re-verified from disk, 858 s wall time. Mock evidence only. CI: 8/8 green.
- Phase 2: multi-dataset bar storage and generic hash-checked tables; FRED loader (live download verified, ~84,000 observations; Python's default User-Agent is required — FRED reset connections for a custom label); publication-time availability (VIX same day 22:00 UTC; Treasury and Moody's series next business day 22:00 UTC); revisions kept; high-yield spread, NFCI and STLFSI4 excluded with reasons; Alpaca history back-fill (SIP, raw and adjusted) tested with a fake client including a byte-identical rebuild; data-quality checks; proposed universe; CLI `macro-update`, `backfill`, `data-check`.
- Commands: `pytest -q` **40 passed** on Windows (Python 3.13). No broker or Alpaca market-data call was made; the only live call was the public FRED CSV download.
- Needs from the owner: Alpaca paper keys (history back-fill and probes), a contact name/email for the SEC User-Agent, universe confirmation, news/social source decisions.

## 2026-10-19 — Phase 2 data layer part 2: SEC EDGAR and event calendars

- SEC contact: the owner's name and email, supplied via `JARVIS_SEC_USER_AGENT` and kept out of Git (the repository is public).
- `edgar.py`: ticker map, filings (8-K, 10-Q, 10-K, Form 4) back to 2016 including older submission pages, earnings releases (8-K item 2.02) and fundamentals (revenue, net income, diluted EPS, assets, liabilities, equity, operating cash flow, shares outstanding) with period length so quarterly and year-to-date values cannot be mixed. Finding: the submissions JSON `acceptanceDateTime` is unreliable — for Apple's earnings 8-Ks it was 8 hours ahead of the official "Accepted" time on the filing index page (16:30 New York), while a Form 4 was correct UTC. Earnings releases therefore use the index-page time; other filings are treated as known at the end of the filing day. Requests are spaced 0.15 s apart (SEC limit is 10/s); resolved index pages are never re-fetched.
- `calendars.py`: FOMC decisions (current and historical Fed pages; 14:00 New York on the last meeting day), CPI and Employment Situation releases (BLS archive links and schedule pages; 08:30 New York). Emergency meetings (2 and 15 March 2020) stored as `FOMC_UNSCHEDULED`, known only from the end of that day; the cancelled 17–18 March 2020 meeting is kept but never counts as upcoming. Assumed availability of scheduled events: 1 July (Fed) and 1 October (BLS) of the prior year.
- Live runs 2026-10-19: AAPL/MSFT/SPY EDGAR load as recorded in `EXECUTION.md`; calendar build 381 events 2016–2027. `tzdata` pinned for New York time on Windows.
- Commands: `pytest -q` **45 passed** on Windows. New CLI: `edgar-update`, `calendar-update`.

## 2026-10-19 — Phase 3 evaluation harness

- Journal index (`JournalIndex`) replaces full-journal scans in the decision path; backtest storage mode (no per-event fsync, index-only memory). Strategy plug-in interface (`Strategy.entry_score`); `random-entry` research control. Daily bars use real session times (09:30–16:00 New York) so a daily decision fills at the next open; runner settings per timeframe (`1Hour`, `1Day`).
- `replay.py`: point-in-time ReplayData with a hard look-ahead guard on every read; ReplayBroker filling at the next bar open with spread/fees and limit-order semantics. `harness.py`: replays through the real PaperDesk/engine/Governor, benchmarks, metrics, gate, future-poisoning leak test, hash-chained experiment registry with a once-only holdout. `metrics.py`: return/risk metrics and a circular block bootstrap.
- Findings while building: (1) the paper loop rebuilt the review report every cycle, re-reading the whole journal — now only when a new outcome exists, never in replays (replay 29× faster); (2) the planted leak earned Sharpe ≈ 2.2, below the statistical alarm, and leaked through the quote (execution input) rather than the signal — the future-poisoning test now compares both signals and order inputs and catches it.
- Exit tests (synthetic random-walk market, 4 stocks, 2016–2018): random entry fails the gate for two seeds; planted leak flagged structurally while the honest run passes the poisoning test; a look-ahead data bug aborts the evaluation; holdout refused on second use. `pytest -q` **50 passed** on Windows.
- Not yet run on real market data (needs Alpaca paper keys for `backfill`). Synthetic results are not market evidence.

## 2026-10-19 — Phase 4 strategy library (pre-registered)

- Features: long-horizon set added without changing existing feature names; daily lookback raised to ~400 calendar days (equities) / 300 (crypto). Hand-checked against a known series.
- Strategy interface: `entry_score(snapshot, context)`, `exit_reason(...)`, `stop_loss_atr`; `DecisionContext` (all assets' snapshots at one moment, earnings releases known at that moment). Engine monitor applies maximum holding time, then (from the first new bar) the stop-loss, then the owning strategy's exit. Runner gathers data for every asset first, then decides; one position per asset (no adding by a second strategy). Snapshots computed once per asset per cycle and reused.
- Strategies (`library_specs`, all RESEARCH): trend-sma200, meanrev-rsi2, volatility-breakout, relative-strength (top 3 enter, outside top 5 exits, needs ≥6 assets), earnings-drift (8-K 2.02 release during the latest bar, >2% reaction on ≥1.5× volume, 20-bar hold). Pre-registered with evidence tags and an evaluation plan in `docs/06-strategies/STRATEGY_REGISTER.md` before any real-data run.
- Tests: 12 new; the integration tests were strengthened after the first version passed trivially (4 synthetic stocks were too few for relative strength to rank, and random release dates rarely triggered the drift rule) — now every strategy must trade in the replay and pass the future-poisoning test. `pytest -q` **62 passed** on Windows (3 min 50 s).
- Not run on real market data: blocked on Alpaca paper keys for `backfill`.

## 2026-10-19 — Phase 5 situational-awareness models (pre-registered)

- New modules:
  - `volatility.py`: rolling-20 baseline; EWMA 0.94; HAR (levels, OLS per horizon); GARCH(1,1) MLE. Rolling 1,000-return window, refit at each month start.
  - `regime.py`: none/sma200 references; trend×volatility; two-state Gaussian HMM (EM fit, forward filter only); FRED stress ablation.
  - `riskmodel.py`: diagonal baseline; sample covariance; Ledoit–Wolf constant-correlation shrinkage; portfolio volatility and a crowding ratio.
  - `costs.py`: spread + fee + square-root impact model; realised shortfall from the journal.
  - `awareness.py`: per-cycle `SITUATION` snapshot (stress, breadth, event calendar, crypto, per-asset regime and volatility, desk state).
  - `studies.py` + `model-study` / `cost-report` commands; FRED long-history price series for the studies (kept out of Git: copyrighted).
- Integration:
  - Volatility sizing in the runner and backtests (`sizing="volatility"`), capped at the owner's per-order limit, with quantities rounded down.
  - Strategy register amended (before any real run) to use it.
- Pre-registration: `docs/07-awareness/MODEL_REGISTER.md`, committed before any model touched real data. Reference checks were made by a research agent, with FETCHED/RECALLED tags.
- An independent review agent checked look-ahead (future-scaling tests on every model), forecast parity between study and live code, and the Ledoit–Wolf formula against the authors' covCor.m (exact match). It found:
  1. Live volatility sizing would go SAFE: the bar request limit exceeded 1,000, and Alpaca returns the oldest bars first. Fixed: the whole window is fetched and the newest bars kept.
  2. Pass-2 awareness code ran outside the SAFE error handling. Fixed.
  3. Live paper did not record `SITUATION`. Fixed.
  4. Scaled orders could exceed the owner cap and be blocked. Fixed: capped.
  5. The Diebold–Mariano test was liberal: by simulation, 7–16% false alarms at 5%. Changed to an Andrews bandwidth (≥2h), which simulated at 5–8%, with pooling per asset group.
  6. Cost shortfall was measured from the ask, not the mid. Fixed.
  7. Minor issues fixed as well: hmm2 now has a live path and a parity test; deterministic HMM fits; NaN guard; the holdout requires a recorded development run; stress flags are revision-aware.
- Also repaired 13 mis-encoded lines in EXECUTION.md, which came from an earlier commit.
- Real-data studies (FRED source, code 529c572; development, then holdout once):
  - Volatility: GARCH passes and is the winner. EWMA also passes; HAR fails on stocks. In the holdout, GARCH was better on all five series, but significant only for stocks.
  - Regime: no detector beats "no regime". The stress signal is dropped. This negative result is recorded.
  - Correlation: not significant in development, significant in holdout; it waits for the universe data.
- After the study, a recorded fallback was added: the baseline sizes orders until GARCH has 1,000 returns. It applies to strategy sizing only. Backtest CLI defaults are now `--sizing volatility --volatility-model garch`.
- The registry append now takes an exclusive lock: parallel study runs could otherwise fork the hash chain. A test was added.

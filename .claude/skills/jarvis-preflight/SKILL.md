---
name: jarvis-preflight
description: >-
  Check that Jarvis is safe to run before trusting it or after changing its code. Covers tests, golden-day
  replays (would the desks still make exactly the recorded decisions?), data freshness, the scheduled daily
  routine, credentials present (names only), package pins and repository hygiene, with PASS / WARN / FAIL for
  each. Use after any change to desk, executor, risk or research code, before committing, after a failed daily
  run, or when the owner asks "is everything working", "health check" or "preflight".
---

# jarvis-preflight

Run from the repository root. `JARVIS_HOME` is the data home (`$data` in the local `run-daily.ps1`):

```powershell
.venv\Scripts\python.exe -m jarvis --home $env:JARVIS_HOME <command>
```

**Read-only, apart from the test run (which writes only to temporary folders).** This skill never:
- runs `--enable-orders`;
- records a golden day unless the owner asks;
- prints the value of an environment variable;
- changes Windows security settings.

## Checks

1. **Tests:** `$env:JARVIS_HOME=<home>; .venv\Scripts\python.exe -m pytest -q`.
   - PASS if everything passes. Report the skip count.
   - With `JARVIS_HOME` set, `tests/test_golden_days.py` also replays the owner's real recordings.
2. **Golden days:** `golden` replays every recording in `<JARVIS_HOME>\golden\`.
   - PASS means today's code and desk settings make exactly the recorded decisions.
   - A FAIL after a code change means the desks would now trade differently. List the first differences and say which change caused them.
   - If the change is intended and the owner agrees, retire the old recording: rename the folder `<day>.retired`, which the replay ignores. Then record a new one during market hours. Recording is read-only on the desk's paper account:

     ```powershell
     .venv\Scripts\python.exe -m jarvis --home $env:JARVIS_HOME golden --record --desk sector --universe "$env:JARVIS_HOME\config\universe.json"
     .venv\Scripts\python.exe -m jarvis --home $env:JARVIS_HOME golden --record --desk stockbook --universe "$env:JARVIS_HOME\config\universe.json"
     ```
   - No recordings: WARN, and suggest recording one.
3. **Doctor:** `doctor`. PASS if nothing is FAIL.
4. **Data freshness:** the newest stock-book bar should be the last completed session (WARN if older):

   ```powershell
   .venv\Scripts\python.exe -c "import pandas as pd; print(pd.read_parquet(r'<JARVIS_HOME>\shortterm\live_daily_adjusted.parquet', columns=['timestamp']).timestamp.max())"
   ```

   Then run `desk-status` and check that each desk's `decision_row_date` matches.
5. **Scheduled routine:** `Get-ScheduledTaskInfo -TaskName "JARVIS daily"`.
   - `LastTaskResult` of `0` is PASS.
   - `3221225786` (0xC000013A) means terminated (shutdown, sleep, logoff or a closed console): WARN.
   - Read today's `<JARVIS_HOME>\logs\daily-<yyyy-MM-dd>.log`. Without a `=== finished` line the run stopped part-way and the desks may not have traded.
6. **Credentials present, by name only.** Print SET or MISSING, never a value:

   ```powershell
   foreach ($n in "ALPACA_PAPER_KEY_ID","ALPACA_PAPER_SECRET_KEY","ALPACA_SECTOR_KEY_ID","ALPACA_SECTOR_SECRET_KEY","ALPACA_STOCKBOOK_KEY_ID","ALPACA_STOCKBOOK_SECRET_KEY","JARVIS_SEC_USER_AGENT") { "{0}: {1}" -f $n, $(if ([Environment]::GetEnvironmentVariable($n, "User")) {"SET"} else {"MISSING"}) }
   ```
7. **Package pins:** `pyarrow` must be `24.0.0`. Windows Smart App Control blocks the newer DLLs; never upgrade it.

   ```powershell
   .venv\Scripts\python.exe -c "import pyarrow; print(pyarrow.__version__)"
   ```
8. **Repository hygiene:** the repository is public.
   - Run `git status --short` and `git diff --cached --name-only`. Nothing under `jarvis-data`, and no data files (`*.parquet`, `*.jsonl`) or model weights, should be staged.
   - Search the staged diff for anything key-like (`PK[A-Z0-9]{16,}`, `SECRET`) or an e-mail address. Any hit is a FAIL: unstage it and tell the owner.

## Report

Give one table (check, result, one-line reason), then what needs doing, most urgent first. Never say "all good" when a check was skipped; say which and why.

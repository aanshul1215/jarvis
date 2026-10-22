---
name: jarvis-status
description: >-
  Report how the Jarvis paper desks are doing, read-only. Covers each desk's equity against the $10,000 it
  started with and against SPY, the latest cycle (orders placed, orders skipped and why, halts), whether
  today's scheduled run finished, and anything that needs the owner. Use when the owner asks "how are the desks
  doing", "status", "how much did we make", "did today's run work", "performance", or at the start of a
  session about the live desks.
---

# jarvis-status

**Read-only.** This skill never:
- places, cancels or changes an order;
- runs a command with `--enable-orders`;
- prints a key;
- edits anything under the desks' homes.

`JARVIS_HOME` is the data home (`$data` in the local `run-daily.ps1`). Run the commands from the repository root:

```powershell
.venv\Scripts\python.exe -m jarvis --home $env:JARVIS_HOME <command>
```

If `JARVIS_HOME` is not set, take the `$data` path from `run-daily.ps1`.

## Steps

1. **`desk-status`:** reads each desk's own journal, with no broker call. It reports:
   - status (`RUNNING`, `HALTED`, `NO_CYCLE_YET`) and the time of the last cycle;
   - capital;
   - orders and skip reasons in the last cycle;
   - order fills so far;
   - whether the first build is complete;
   - the owner policy version.
2. **`desk --desk sector --check`** and **`desk --desk stockbook --check`:** each paper account's equity, cash, positions and open orders. These are read-only connections.
3. **`performance`:** refreshes `<JARVIS_HOME>\reports\performance.html` (both desks against SPY bought at the desks' first order) and prints the figures.
4. **Today's routine:**
   - Run `Get-ScheduledTaskInfo -TaskName "JARVIS daily"` and read `LastRunTime`, `LastTaskResult` and `NextRunTime`. A `LastTaskResult` of `0` means success. `3221225786` (0xC000013A) means the process was terminated (shutdown, sleep, logoff or a closed console).
   - Read the step lines of `<JARVIS_HOME>\logs\daily-<yyyy-MM-dd>.log`: the lines starting with `---`, `===` and `!!!`.
   - A log without a `=== finished` line means the run stopped part-way and the desks may not have traded. Say so.

## How to report (plain language, this order)

1. **Each desk:** equity; the gain or loss in dollars and percent since its $10,000; SPY over the same period.
2. **Today's run:** whether it ran and finished. If a desk did not trade, say why.
3. **Last cycle:** orders placed, and orders skipped grouped by reason, each with its meaning:

   | Reason | Meaning |
   |---|---|
   | `WIDE_SPREAD` | the free IEX quote was wider than the policy limit; retried next run |
   | `STALE_OR_FUTURE_QUOTE` | the quote was too old (or ahead of the clock) |
   | `NO_QUOTE:<error>` | no quote could be fetched |
   | `MARKET_CLOSED` | the run happened outside market hours |
   | `LOSS_STOP_ACTIVE` | the daily-loss or drawdown stop is on; only risk-reducing orders are allowed |
   | `BUYING_POWER`, `PORTFOLIO_CAP`, `SHORT_CAP` | a capital or exposure limit stopped the order |
   | `NOT_SHORTABLE` | the broker will not lend the stock |
   | `BELOW_ONE_DOLLAR`, `BELOW_ONE_UNIT` | the order was too small to place |

4. **Anything that needs the owner:**
   - a `HALTED` desk, or SAFE mode;
   - a failed or partial run;
   - positions the desk did not place. Manual trades must be recorded as a `POSITION_ADJUSTMENT`; see `docs/11-desks/PAPER_DESKS.md`. Remind the owner not to trade the desk accounts by hand.

## Rules

- Every number comes from the commands' output. Never estimate or round a loss into a gain.
- Days or a few weeks of returns are mostly noise. Never extrapolate a week to a month or a year. Say how many trading days the figures cover.
- The desks are paper accounts. Nothing here is investment advice.

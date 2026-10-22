# Round 7 paper desks (owner decision 2026-10-21)

**Owner decision:** paper-trade two candidates with $10,000 each, on separate Alpaca paper accounts ("Stock book" and "Sector rotation"), so each one's balance is its own performance. The original $100,000 paper account is not used by either desk.

| | Sector rotation | Stock book |
|---|---|---|
| Design | `sector-rotation-1.5.0` (docs/09-portfolio/ROUND6_DESIGN.md) | `enhanced-index-2.0.0` (docs/10-shortterm/ENHANCED_INDEX_V2_STUDY.md), passed development, confirmation and holdout |
| Decisions | First session of each month (the trend switch, plus the top 3 of 12 sector ETFs; otherwise SHY) | First session of each week for stocks; month start for the 20% bonds/commodities sleeve |
| Holdings | 3 ETFs (or SHY) | About 300 stocks in fractional shares + 3 sleeve ETFs |
| No-trade band | max(1% of capital, 20% of target) | max(0.1% of capital, 25% of target) |
| Strategy id | `sector_rotation` | `stock_book` |
| Desk home | `JARVIS_HOME/desks/sector` | `JARVIS_HOME/desks/stockbook` |
| Keys (user environment variables) | `ALPACA_SECTOR_KEY_ID` / `ALPACA_SECTOR_SECRET_KEY` | `ALPACA_STOCKBOOK_KEY_ID` / `ALPACA_STOCKBOOK_SECRET_KEY` |

## Desk policies (owner-signed values carried over from the main owner policy)

**Both desks:**
- paper only;
- allocated capital $10,000, with holdings capped at $10,000 (no leverage);
- no shorting and no crypto;
- daily loss stop $300; drawdown stop 25% from the all-time peak;
- quotes must have a spread of at most 50 bps and be at most 60 seconds old.

**Sector desk:** at most $4,000 per order and per asset. Assets: the 12 sector ETFs and SHY.

**Stock desk:** at most $1,500 per order and per asset; spread limit **2%** (owner decision 2026-10-21: the free IEX quotes show spreads far wider than the real market's on many large stocks; buys still carry a limit price). Assets: the 9 sleeve ETFs, SHY, and the rule `shortterm_top300` (any stock in the current month's point-in-time top-300 list).

## How a cycle works

Each desk has its own journal, so reconciliation sees only its own account. The weekday cycle:
1. reconcile with the broker;
2. cancel the desk's own unfilled orders;
3. compute targets with the research code;
4. on a decision day (or on the first run of an empty desk), trade the differences above the no-trade band: sells first, then marketable limit buys at the ask + 0.2%. Each order is checked against the desk policy and journaled before it is sent.

**What the desks do not have:** a drawdown brake, volatility targeting or leverage. These are round 5's guards against repeating rounds 2–4. The Governor's stops still apply.

## Daily routine (weekdays, 9:00 Texas = 10:00 New York)

1. `macro-update` (T-bill rate);
2. `backfill --timeframes 1Day` (ETF prices);
3. `shortterm-update` (completed sessions only; the stock universe at month start; SIC codes; about 15 months of daily bars);
4. `desk --desk sector --enable-orders`;
5. `desk --desk stockbook --enable-orders`.

**Read-only commands:**
- `desk --desk <name>` without `--enable-orders` previews the targets;
- `desk --desk <name> --check` reports the account's equity and positions. It never prints keys.

## Manual trades in a desk account

**Don't trade a desk's account by hand.** Each desk's journal must explain every position. A manual order makes the next cycle stop with "unknown or mismatched broker position" (SAFE), and the paper results stop matching the strategy.

**If a manual trade happens:**
1. Record it in that desk's journal as a `POSITION_ADJUSTMENT` with the signed quantity and the reason `OWNER_MANUAL_SALE` or `OWNER_MANUAL_BUY`.
2. To return to the strategy's targets at once, remove `config/desk-build-complete.json` so the next cycle rebuilds.

**First case** (2026-10-21): the owner sold 5 SMH from the sector account by hand. It was recorded on 2026-10-22, and SMH was bought back (6 shares) the same morning.

## Golden days and operating skills (2026-10-22)

**Golden days** (`src/jarvis/golden.py`) are regression tests built from real desk decisions.

`jarvis golden --record --desk <desk> --universe <universe.json>` runs during market hours, read-only on the desk's paper account. It writes `JARVIS_HOME/golden/<desk>/<day>/`, containing:
- every stored bar and macro table the target builder read;
- the stock book's input files;
- the desk's policy, capital baseline and high-water mark;
- the broker state;
- every quote and shortable answer the planner received;
- the resulting target weights and the full-rebalance plan.

Each recording is replayed once as soon as it is written. If it doesn't reproduce itself, the folder is renamed `<day>.failed`.

`jarvis golden` replays every recording with the current code and settings. It fails on any difference: a code change that would make a desk trade differently is caught before it reaches the desk. `tests/test_golden_days.py` does the same when `JARVIS_HOME` is set. If a change is intended, retire the recording by renaming it `<day>.retired`, then record a new one.

Recordings contain exchange and FRED data, so they stay local and never go into the repository.

- **First recordings (2026-10-22, about 15:30 ET):**
  - sector: 3 target ETFs, already held, so no orders;
  - stock book: 303 targets, 9 orders, 101 skipped.

**`jarvis desk-status`** gives a read-only summary of each desk from its own journal: the last cycle, skip reasons, fills, build state and policy version.

**Claude Code skills** (`.claude/skills/`) cover operations and research only. They never place orders.
- `jarvis-status`: desks against SPY, today's run, and anything that needs the owner.
- `jarvis-preflight`: tests, golden days, data freshness, the scheduler, credentials (names only), the pyarrow pin and repository hygiene.
- `jarvis-study`: the pre-registered study protocol, with a template and a red-team checklist.

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

**Stock desk:** at most $1,500 per order and per asset. Assets: the 9 sleeve ETFs, SHY, and the rule `shortterm_top300` (any stock in the current month's point-in-time top-300 list).

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

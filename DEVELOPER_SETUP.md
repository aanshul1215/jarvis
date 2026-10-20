# Developer setup and configuration

Use Python 3.11+ and install `pip install -e '.[dev]'` in a virtual environment. Dependencies are pinned in `pyproject.toml`. Run `python -m pytest -q` and `python -m jarvis doctor`. No database server or hosted model is required.

Set `JARVIS_HOME` to a writable absolute directory outside this checkout. `.env.example` lists supported variable names; it is a template and is not loaded automatically. Export paper credentials in your local shell or private secret manager as `ALPACA_PAPER_KEY_ID` and `ALPACA_PAPER_SECRET_KEY`. Never place actual keys in tracked files. `python -m jarvis alpaca-check` performs read-only account and basic asset probes; a PASS requires an actual account response. `python -m jarvis paper --dry-run` also checks the local owner policy and does not send an order.

An owner policy is a private JSON file at `$JARVIS_HOME/config/owner-policy.json`. The owner must choose its values. Schema example, **disabled and with placeholder limits**:

```json
{
  "version": "owner-v1",
  "approved_assets": ["AAPL", "BTC/USD"],
  "approved_strategies": ["breakout-volume"],
  "max_order_notional": 1,
  "max_asset_notional": 1,
  "max_portfolio_notional": 1,
  "max_daily_loss": 1,
  "max_drawdown": 0.01,
  "max_spread_bps": 1,
  "max_quote_age_seconds": 1,
  "paper_enabled": false,
  "crypto_enabled": false,
  "owner_approved": false
}
```

These numbers are placeholders, not suggested trading limits. The loader rejects missing or extra fields and paper mode remains disabled unless the owner explicitly enables it. The baseline strategy has MOCK approval only; research results do not auto-promote it. Existing branch-3 [FINAL_IMPLEMENTATION_PLAN.md](FINAL_IMPLEMENTATION_PLAN.md) remains the architecture contract.

The private `$JARVIS_HOME/config/paper-runtime.json` must also identify exact strategy versions and the owner's intended order notional for each asset. A disabled example is in [paper-runtime.example.json](paper-runtime.example.json). The `order_notional` value is a target for one paper entry, bounded again by the Governor. US equity size is rounded down to whole shares; crypto size is rounded to eight decimal places. Only the exact `strategy-id@version` named in this private file may be promoted to PAPER for that process; research output alone cannot change it.

`python -m jarvis --home "$JARVIS_HOME" paper --dry-run` checks the private configuration and read-only account access. `paper --once --enable-orders` and `paper --loop --enable-orders` are explicit operator actions that can submit **paper** orders after all configuration and broker checks succeed. Do not run either order-capable command until owner risk values, account capabilities, feed latency, and strategy evaluation have been reviewed. The implementation has no live trading switch. Equity cycles check Alpaca's market clock; crypto cycles run on their own 24/7 clock. Research is a separate process.

Local storage uses Parquet for bars/features, append-only hash-chained JSONL for operational events, JSON for experiment metadata, CSV for Excel-readable results, and native model artifacts. Only load model artifacts generated in a trusted local environment; Python model serialization can execute code when loaded. Keep `JARVIS_HOME` and backups private.

`train --fixture` runs expanding chronological validation folds and an untouched holdout for a constant baseline and logistic challenger. It stores calibration bins, downside measures, model hashes, and an immutable `model-registry.json` under the local runtime. Every entry stays in `RESEARCH`; this command never approves a model or strategy.

The information path accepts dated local JSON documents using the [example schema](info.example.json). `info-ingest --file PATH` persists the original text and a short, deterministic extractive summary under `JARVIS_HOME/information/`, with an `INFO_FEATURE` journal event. Documents are scoped to one asset and processed when supplied, so the trading cycle does not scrape or summarize the whole universe. Lexical sentiment is unvalidated and has no trading authority. News/SEC collectors, source licensing checks, and real event impact models remain future work.

## Data commands (Phase 2)

All write under `JARVIS_HOME` and record a journal event. None places an order.

| Command | Needs | What it does |
|---|---|---|
| `jarvis macro-update` | nothing | FRED market-stress series (VIX, 3-month VIX, Treasury yields, T-bill, Baa credit spread) with publication-time availability |
| `jarvis calendar-update` | nothing | FOMC decisions and CPI/jobs release dates 2016 onward, plus the published schedule ahead |
| `jarvis edgar-update --universe FILE` | `JARVIS_SEC_USER_AGENT` | SEC filings, earnings-release times and fundamentals for the universe's stocks |
| `jarvis backfill --universe FILE [--start 2016-01-01]` | Alpaca paper keys | Daily and hourly bars (raw and adjusted) into point-in-time datasets |
| `jarvis data-check --universe FILE` | stored data | Duplicate, gap, spike, stale-price and zero-volume report |
| `jarvis soak [--hours 24]` | nothing | Accelerated mock paper run of the full loop (Phase 1 exit test) |

`config/universe.example.json` is a proposed starting universe; copy it to `JARVIS_HOME/config/universe.json` and edit.

# 00b - Summary of gap-fill briefs 18-23 (verified corrections applied), 2026-10-01

Read together with 00-gap-analysis.md. Full briefs: 18-...md to 23-...md in this folder.
Owner facts added since the gap analysis: **Texas**, **Windows 11 laptop with 8 GB RAM**.

## 18 - First strategies, primary evidence (reliability: medium)
- The null hypothesis is a static ETF + BTC/ETH buy-and-hold with periodic rebalancing. Every strategy is judged
  net of cost and after tax against it.
- Strategy A: month-end 10-month-SMA (or 12-month return sign) long/flat on 4-6 liquid ETFs, cash/T-bill ETF when
  off. About 3-4 round trips a year, cost a few bps. Honest expectation: roughly -1 to +1 point a year of CAGR versus
  holding the same assets, with about half the drawdown. It sells risk reduction, not alpha.
- Strategy B (small sleeve, 20-25% cap): BTC/ETH Donchian trend ensemble with 20-90 day lookbacks, long/flat,
  leverage 1.0, daily-close signals, 20% no-trade band, limit orders. Cost about 0.7-1.2% a year before spread at
  Alpaca. Net Sharpe is UNKNOWN (0.3-0.8 is illustrative only; source is a non-peer-reviewed working paper). Likely
  lags BTC buy-and-hold in bull runs; its value is avoiding >80% drawdowns.
- Strategy C: volatility targeting is a sizing/risk governor, not alpha (out-of-sample Sharpe gain not reliable).
- Confirmed: McLean-Pontiff 26% out-of-sample / 58% post-publication decay; Chen-Velikov 4-8 bps/month net average
  anomaly; Quantopian backtest Sharpe R^2 < 0.025 vs live. These are haircut heuristics, not measurements for trend.

## 19 - After-tax and account type (medium)
- Benchmark must be after-tax buy-and-hold in the same account type. Tax hurdle for a strategy realising gains
  short-term: about +1.0 to +1.5 percentage points a year at 8% gross for 22-24% brackets (ESTIMATE).
- Alpaca offers IRAs with API trading for equities/ETFs (no crypto, 1x, no shorting) - fee schedule unverified.
  Running the ETF sleeve in an IRA removes the tax drag; limits: about $7,500/yr contribution, lock-up to 59.5.
- Alpaca crypto round trip is 0.30% (maker) to 0.50% (taker). Crypto wash-sale legislation status is unverified.
- Ledger needs lot ID, acquisition date, account type, wash-sale flag; cross-account wash-sale guard.
- Not tax advice; list of questions for a professional is in the brief.

## 20 - Promotion gates for slow strategies (medium)
- Paper-trade counts cannot validate a monthly strategy. Evidence must come from long (>=20 year) pooled
  multi-asset backtests of a pre-registered spec, with an append-only trial registry and deflated Sharpe by
  effective trial count; plateau/robustness tests instead of PBO for near-identical variants.
- Gates: G0 pre-register -> G1 backtest (deflated Sharpe, plateau, holdout by asset, 5-year windows, costs x2)
  -> G2 shadow >= 6 rebalances (replay identity, no performance test) -> G3 paper >= 3 rebalances (reconciliation
  and failure drills; paper P&L is not evidence) -> G4 micro-live at 5-10% of capital, >= 6 months, >= 20 fills,
  gate on realised cost <= 1.5x model -> G5 scale 25% -> 50% -> 100%, >= 6 months per step.
- Live Sharpe is unusable for kill/promote decisions on any realistic horizon. Use replay tracking error, realised
  costs and bootstrap drawdown bands (yellow at p90, red at p99), plus an owner lifetime stop.
- Plan on net Sharpe 0.3-0.5 for a long/flat ETF/BTC trend book. Numeric thresholds are design choices to be
  simulated on JARVIS's own data.

## 21 - Alpaca specifics (medium)
- Basic (free) plan: IEX-only real-time, 30 streamed symbols, 200 REST calls/min. News API on Basic is documented
  but must be probed at start-up (fail soft); EDGAR is the non-vendor fallback.
- Crypto: state list is about a year old and unverified for Texas - confirm at signup; treat the crypto sleeve as
  CONDITIONAL. Limit orders GTC/IOC; exits are stop-limit only; no brackets.
- Design option not researched by any brief (verify before relying on it): spot Bitcoin/Ether ETFs trade as
  ordinary equities, which would give crypto exposure at equity costs, inside an IRA, with resting stops.
- No PDT counters, but keep handlers for intraday-margin / PDT rejections; leverage cap 1.0; no shorting.
- Fractional orders are DAY-only: overnight stop protection needs whole shares with a GTC stop (auto-cancels at 90
  days; re-arm each run).
- Order service: deterministic client_order_id, but look up by id before any resubmit; reconcile via REST after
  every reconnect; never blind-retry a replace. Duplicate-id behaviour and websocket replay need a paper test.
- Terms are compatible with personal own-money automated trading and an owner-only dashboard.

## 22 - Claude usage and cost plan (high)
- Core JARVIS must run with the LLM fully off ($0). LLM is an optional add-on behind a hard spend cap.
- Production LLM calls: API key + Batch API in a dedicated workspace with a self-set monthly limit (~$15).
  Nightly batch extraction on Haiku 4.5 for ~20 symbols plus a daily narrative is about $4/month (ESTIMATE);
  adding a weekly API research session raises it to roughly $20-35/month.
- Do not make the production pipeline depend on a Pro/Max subscription login (policy unstable, shared limits,
  consumer terms mention securities trading). Use the subscription for owner-attended Claude Code sessions:
  building JARVIS and the weekly research/Strategy-Lab session.
- Record-and-replay store and a golden-set comparison harness before any LLM feature goes live. LLM-derived
  features stay at zero weight until they pass pre-registered forward tests; every model change restarts the clock.
- Haiku 4.5 may be retired soon; keep model ID in config and budget ~2.6x for a successor.

## 23 - Hosting and liveness (medium)
- Design a run-to-completion scheduled job, not a daemon: lock -> heartbeat -> reconcile with broker (broker is
  source of truth) -> calendar and data-freshness checks -> signals -> risk gate -> write intent rows before any
  broker call -> submit -> poll to terminal state -> verify resting stops -> heartbeat success/fail.
  SQLite WAL, one writer.
- Default host: the owner's Windows laptop under Task Scheduler (wake-to-run, retry run an hour later). Fallback /
  upgrade: the same script on a free or $4-6/month US Linux VM (avoid Oracle free tier: idle reclaim). Move before
  the first 24/7 crypto position or after 2 missed runs in a month.
- Off-host dead-man's switch (Healthchecks.io free tier) alerting to email/Telegram/ntfy.
- Protection rests at the broker: whole-share GTC stops for equities; GTC stop-limit for crypto with a sleeve cap
  that bounds gap risk.
- Secrets: DPAPI user-scope file on Windows; separate paper and live keys; live key on one host only.

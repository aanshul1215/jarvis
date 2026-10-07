# Proposal A: Vision-faithful JARVIS

Architect A, 2026-10-01. Evidence: briefs 01-23, 00, 00b. ESTIMATE = arithmetic from briefs; "design choice" = not a published constant.

## 1. Thesis

JARVIS stays the system the owner drew: the seven-state machine (OBSERVE to SAFE/LEARN), the opportunity scanner, a specialist team, a confidence concept, a capital governor with a hard veto, a position manager, a professional ledger, and both equities and crypto. Each part is rebuilt at the resolution the evidence supports. The scanner is scheduled, not always-on (briefs 06, 23). Numeric specialists become code and statistics; text-reading specialists become Claude agents (brief 02). "Confidence" becomes an evidence card of base rates with sample sizes, not a pooled percentage (brief 10). The position manager runs pre-registered exits with stops resting at the broker (briefs 17, 23). The book is long/flat on daily-to-monthly horizons (briefs 05, 11). This philosophy is right because the owner's documents already contain the principles the evidence rewards (deterministic rules hold the money, FLAT is valid, never chase a target, paper before live). What the evidence rejects is the design's resolution (intraday order flow, debate on every candidate, a pooled 72%), not its shape. Keeping the shape means later capital and data fill slots that already exist instead of forcing a rewrite. The plain limit: no evidence shows Claude agents picking trades profitably (briefs 01, 02), so the agents here are real but sit off the order path, with zero weight on money decisions until they pass forward ablation tests.

## 2. End-to-end flow

[D] = deterministic code, [S] = statistical model, [C] = Claude agent.

1. **Goal & Capital Planner** [D; optional C front end]. Owner's capital, risk tolerance, optional goal and permissions (recommend / paper / live) become a typed, versioned config. Unrealistic targets are rejected by showing the backtest's bootstrap return and drawdown range (brief 20).
2. **Ingest** [D]. Daily bars, corporate actions, EDGAR, FRED/ALFRED, Alpaca news; every row carries `source_published_at`, `first_seen_at`, `available_at` (briefs 06, 16).
3. **Data Trust Gate** [D]. Schema, staleness, gaps, duplicates; Alpaca vs Tiingo EOD and vs Coinbase/Kraken public prices. Failure sets system state SAFE (no new risk; exits allowed), with no override path (briefs 07, 12, 14).
4. **Market State** [D + S]. Trend signals (10-month SMA, 12-month sign, Donchian), HAR or GJR-GARCH volatility forecast for sizing, rule-based regime label; any HMM uses filtered probabilities refit walk-forward (brief 15).
5. **Opportunity Scanner: OBSERVE to INVESTIGATE** [D]. Evenings for equities, 00:05 UTC for crypto. (a) Evaluates every *registered* strategy; a change in target position is a **candidate**. (b) An *anomaly watch* (price/volume z-scores, 8-K items, Form 4 buy clusters, news-volume spikes) over a 20-symbol watchlist produces **watch items** that are reported, never traded until a registered strategy covers them (brief 16).
6. **News & Event Analyst** [C, nightly batch]. Text becomes structured events feeding the archive and deterministic blackouts (earnings date, 8-K items); never a return signal at launch (briefs 16, 22).
7. **Integrity Risk Filter** [D]. Crypto pump-burst detector, venue hygiene, cross-venue check; may block or downsize, never create (brief 07).
8. **VALIDATE: Evidence Card** [S + D]. Five components shown separately, never pooled (brief 10): Signal (strategy base rate with n and interval), Data (gate result), Model (calibration status; number hidden below ~100 resolved outcomes), Thesis (red-team flags, zero weight), Execution (estimated cost vs hurdle).
9. **Red-Team Reviewer** [C, batch]. One pre-mortem per position change, logged as "would veto / would not" for ablation and shown to the owner; no authority (brief 02).
10. **Strategy / Portfolio: READY** [D]. Target weights from registered rules; cost gate: expected gross move ≥ 3× measured round trip, holding period ≥ 1 day (briefs 07, 11); 20% no-trade band (brief 18).
11. **Capital Governor + Hard Risk Gate** [D]. Sizing (section 6) and erroneous-order controls, default-deny; writes an **intent row before any broker call** (briefs 12, 17, 23).
12. **EXECUTE** [D]. Idempotent service: deterministic `client_order_id`, lookup before resubmit, limit orders, poll to terminal state, REST reconcile after reconnect (brief 21).
13. **MANAGE: Position Manager** [D]. Pre-registered exits; broker-resting stops re-armed each run; reconcile on start (briefs 17, 23).
14. **SAFE / LEARN: Ledger** [D]. Decision, evidence card, config hash, model/prompt IDs, full LLM request/response, fills, cost vs model, lot ID, holding period, wash-sale flag (briefs 13, 19, 22).
15. **Narrator & Reviewer** [C, nightly batch]. Daily summary, trade emails, weekly review, from ledger rows only (brief 02).
16. **Strategy Lab** [C, weekly, owner-attended]. Hypotheses into pre-registration; all logged in the append-only trial registry; G0-G5 decide (briefs 08, 20).

## 3. Agent roster

All agents emit Pydantic-validated structured output (ranges included), fail closed to "no information", and are recorded for replay (briefs 13, 22). Production calls use an API key and the Batch API in a dedicated `jarvis` workspace with a $15/month limit; model IDs live in config, with 2.6× budgeted for a Haiku 4.5 successor (retirement floor 2026-10-15; brief 22).

| Agent | Job | Trigger / frequency | Model tier | Inputs | Structured output | Forbidden | Est. $/month |
|---|---|---|---|---|---|---|---|
| **News & Event Analyst** (v3 #7) | Sanitised headlines and 8-K/10-Q excerpts → events | Nightly batch, novel items only (dedup by hashing first) | Haiku 4.5 batch | ~100 items + ~3 filings a night, homoglyph/hidden-HTML stripped (brief 16) | `{event_type, entity, direction, materiality, is_new, evidence_span, version}` | Any order/size influence; config edits; weight > 0 before forward tests | ~$3.40 (brief 22 b1, ESTIMATE); ~$9 on a Sonnet-class successor |
| **Filing Reader** (v3 #8, text half) | Year-over-year 10-K/10-Q risk-factor diff → avoid/flag list | New filing on a watchlist name (few a month) | Haiku 4.5 batch | EDGAR text keyed on acceptance time | `{changed_sections[], new_risks[], severity, evidence_span}` | Same | Included above |
| **Red-Team Reviewer** (v3 #11) | Pre-mortem: falsifiable reasons the candidate is wrong | Each position change (~5-15/month) | Sonnet 5.5 batch, `effort: low` | Evidence card, events, spec | `{concerns[], would_veto, falsifiers[]}` | Blocking or sizing (shadow until ablation); stating probabilities | <$0.50 (ESTIMATE) |
| **Narrator / Reviewer** (v3 #18) | Daily summary, trade emails, weekly review | Nightly batch + weekly | Sonnet 5.5 batch | Ledger rows only | Markdown citing ledger/event IDs | Writing ledger/config; any figure not matching the ledger (checked by script) | ~$0.65 (brief 22) |
| **Strategy Lab Researcher** (v1 Layer D) | Hypotheses, pre-registration specs, backtest code | Weekly owner-attended Claude Code session | Owner's plan model | Notes, registry, results | G0 file + registry entry | Live config, keys, live branch or account | $0 extra on Pro; ~$13 on API (brief 22) |
| **Goal Interpreter** (v3 #2 front end) | Free-text goal → typed config proposal, explained back | On demand in Claude Code | Plan model | Owner text, config | Config diff | Applying the diff | $0 |

**Total API about $4.50/month (ESTIMATE), about $10 with a pricier Haiku successor, under a $15 hard cap.** At $1,000 that is a ~5% annual drag (brief 22), so below $2,400 only the Narrator runs (~$0.65); the extractor starts at ≥ $2,400 (brief 11's 2% rule). The core runs with every agent off (brief 22).

**v3 agents that become code or models** (briefs 02, 07): Orchestrator (code state machine; termination/repetition are the top multi-agent failure modes), Goal Planner core, Scanner, Data Trust, Market/Technical, Crypto, Strategy/Portfolio, Capital Governor, Execution, Position Manager and Ledger store are **code**: they must be reproducible, and an LLM adds cost and nondeterminism. Model Ensemble and Confidence Calibrator are **statistical**. Flow/Microstructure becomes a deterministic **Liquidity & Cost Monitor** and Manipulation Surveillance an **Integrity Risk Filter** (order flow does not forecast at retail fees; spoofing detection needs identity data). Bull + Bear collapse into one Red-Team call (same-model debate is the weakest configuration studied). The roster keeps its names on the dashboard; thirteen members are honest code.

## 4. Strategies and universe at launch

**Benchmark (null):** static ETF + BTC/ETH buy-and-hold, rebalanced periodically, compared after cost and tax in the same account type (briefs 18, 19).

**Universe:** 5-6 liquid ETFs (US equity, international equity, bonds, gold/commodities, real estate) plus a T-bill ETF as cash, and BTC/ETH; tickers fixed at G0. A 20-symbol *watchlist* (universe plus owner single names such as v1's TSLA) is used only for archiving and anomaly watch.

- **Strategy A, ETF trend.** Month-end: hold each ETF above its 10-month SMA (or with positive 12-month return), else T-bills. ~3-4 round trips a year, a few bps of cost. Honest expectation: about −1 to +1 point of CAGR vs holding the same assets, with about half the drawdown; risk reduction, not alpha (brief 18).
- **Strategy B, crypto trend.** 20/30/60/90-day Donchian ensemble on BTC/ETH, long/flat, leverage 1.0, daily close, 20% no-trade band, limit orders; ~0.7-1.2%/yr cost before spread. Net Sharpe **unknown** (one non-peer-reviewed paper; brief 18). **Conditional on Alpaca crypto in Texas** (brief 21); otherwise spot BTC/ETH ETFs at equity cost, an option that must be verified first (brief 21).
- **C, volatility targeting:** a sizing governor on A and B, not a strategy (brief 18).

**Adding strategies later:** only via Strategy Lab → G0 → trial registry → G1-G5. Queued, in order of fit (brief 16): an opportunistic Form 4 buy-cluster overlay once ≥ 12 months of archive exist; a 10-K text-diff avoid list; a Claude headline score after ≥ 6-12 months of shadow. Single-stock momentum waits for survivorship-free data (section 12).

## 5. Data plan

| Source | Use | Cost | Point-in-time handling |
|---|---|---|---|
| Alpaca Basic | Daily bars (SIP history older than 15 min), IEX real-time quotes for collars, news (probe at start-up, fail soft) | $0 | Store raw bars plus a corporate-action table and adjust as of the decision date. Never train on a re-downloaded adjusted series (brief 06) |
| Tiingo Starter | 30-year EOD cross-check and long history | $0 | Reconciliation pair for the Data Trust Gate |
| Coinbase / Kraken public | Crypto price sanity checks | $0 | Data only; not used as brokers (brief 11) |
| SEC EDGAR | 8-K items, Form 4, 10-K/10-Q, XBRL `companyfacts` keyed on `filed` | $0 | Acceptance timestamp is `available_at` (brief 16) |
| FRED/ALFRED | Macro context, rates | $0 | Vintages only (brief 06) |

Event rows are bitemporal and append-only (`available_at` = max(published, first seen) + safety lag); joins only on `available_at <= decision_time` (brief 16). Text archiving starts in phase 1: it is the only clean post-cutoff dataset JARVIS will ever have (briefs 16, 22). No social sentiment or event-study CAR features (brief 16). 20-year ETF proxy history and crypto history before ~2014 are unverified (brief 20).

**Storage:** SQLite WAL, one writer (control plane, ledger, events, trial registry); Parquet + DuckDB (bars, features); a few GB locally with a nightly encrypted off-machine copy (brief 14).

## 6. Risk gate, sizing and exits

**Capital Governor** (starting values are design choices in versioned config; changes need the owner, apply next session, and only tighten intraday; brief 12).

| Rule | Value at launch | Basis |
|---|---|---|
| Leverage | ≤ 1.0, no shorting, symbol allow-list | Alpaca is margin-only; long/flat (briefs 00, 05) |
| Crypto sleeve | ≤ 10% of equity at launch, ≤ 20% after G5; gap rule: a 30% overnight crypto gap must cost ≤ 3% of equity | briefs 18, 23 |
| Per-symbol | ≤ 25% of equity (T-bill ETF exempt) | brief 12 |
| Per-order notional | ≤ min(30% equity, $3,000) absolute | brief 12 |
| Price collar | Limit within 1% (ETF) / 2% (crypto) of a quote < 60 s old; no market orders | brief 12 |
| Rate / duplicates | ≤ 20 orders/day; deterministic `client_order_id`; no opposite-side order while one is working | briefs 12, 21 |
| Daily / weekly loss | −3% / −6% of equity → reduce-only until owner re-arm | brief 12 (values are design choices) |
| Drawdown throttle | size × max(0, 1 − DD/25%); 25% loss of deployed capital = lifetime stop, halt | briefs 10, 20 |
| Kelly | Off until ≥ 300 resolved outcomes, then ≤ 0.25× and only as an upper bound | brief 10 |

**Sizing:** equal-weight slots per sleeve, shrunk (never levered) when forecast vol exceeds a ~10% book target (design choice), then clipped by the gate.

**Exits (pre-registered per strategy, not a "confidence drop"; brief 17):**
- **A:** month-end signal flip only, partial adjustment inside the band. Whole-share slots get a GTC catastrophe stop at about −15% (design choice), re-armed each run because GTC expires at 90 days. Fractional slots are DAY-only, so they are explicitly accepted as unprotected inside a diversified ETF book (briefs 21, 23). This settles gap-analysis item 15.
- **B:** close below the ratcheting channel-midpoint stop, mirrored by a GTC stop-limit at the broker (brief 23).
- **System:** SAFE, a reconciliation break or a stale feed blocks entries but never forces exits. The kill switch is a separate one-command process (cancel all, block new; flattening is a separate choice). An off-host dead-man's switch alerts on a missed run (briefs 12, 23).

## 7. Validation and promotion gates

Brief 20's gates as written, since paper P&L cannot validate a monthly strategy:

- **G0 Pre-register:** hypothesis, universe, 4-6 value lookback grid, cost model, dates; registry entry; N_eff computed.
- **G1 Backtest:** ≥ 20 years pooled monthly; DSR ≥ 0.95 at N_eff (≥ 0.90 for a published rule with N_eff ≤ 5); plateau; holdout by asset class; ≥ 70% positive 5-year windows; costs ×2 keeps SR ≥ 0.75×; crypto judged only inside the pooled book. **Failing G1 is a valid result: JARVIS then holds the benchmark.**
- **G2 Shadow:** ≥ 6 rebalances, 100% replay identity.
- **G3 Paper:** ≥ 3 rebalances, zero reconciliation breaks, three failure drills (crash mid-rebalance, duplicate order ID, stale feed); paper balance = real capital.
- **G4 Micro-live:** $500-1,000, ≥ 6 months, ≥ 20 fills, realised cost ≤ 1.5× model.
- **G5 Scale:** 25% → 50% → 100%, ≥ 6 months each; yellow at bootstrap p90 drawdown, red at p99, plus replay tracking error. Live Sharpe never kills or promotes.

**Extra gate for Claude-derived features** (briefs 02, 22): a ~300-item golden set with deterministic answers; forward-only evidence after the model cutoff; a pre-registered with/without ablation; zero weight until it passes; every model-ID change restarts the clock after a 2-4 week old/new shadow.

## 8. Runtime, hosting, storage, monitoring, secrets

- **Shape:** one Python package of run-to-completion jobs; no daemons, no Docker (brief 14). Each run: lock → heartbeat → reconcile with broker → calendar/freshness → signals → gate → intent rows → submit → poll → verify stops → heartbeat (brief 23). Working set well under 1 GB of the 8 GB.
- **Schedule** (Task Scheduler, WakeToRun, StartWhenAvailable, retry after 1 h): 16:45 ET equity scan + LLM batch submit; 09:45 ET next session equity orders; 00:05 UTC crypto run; 07:00 local batch collection + email.
- **Hosting:** laptop for build, paper and ETF live; the same script moves to a free GCP e2-micro or $4-6 VM **before the first live crypto position or after 2 missed runs in a month** (brief 23).
- **Monitoring:** Healthchecks.io free dead-man's switch → email/ntfy; health lines in the daily email; Streamlit dashboard launched on demand, not resident.
- **Secrets:** rotate the leaked v1 key first; DPAPI user-scope store; separate paper/live keys; live key on one host; keys never visible to any prompt; withdrawals disabled (briefs 12, 23).
- **Cost:** $0 infrastructure, ~$2.64 power (brief 23), $0-4.50 LLM.

## 9. Owner experience

- **Daily (2 minutes):** one email with NAV, positions, actions or "FLAT/no change, and why", data and reconciliation health, watch items, red-team notes and LLM spend. Confidence reads "Strategy A base rate: x of n months, interval [a, b]", never a bare percentage (brief 10).
- **Weekly (~60 minutes):** read the Narrator's review; run the Strategy Lab session; kill-switch drill while in paper (brief 12).
- **Monthly:** rebalance summary; clear pending approvals.
- **Approvals** are pending rows that expire to *reject* (brief 00): paper → micro-live, each G5 step, any new strategy or model, any order above 30% of equity, any config change. No override exists for degraded data or the gate (brief 12). The dashboard is owner-only; there is no "investor view" (briefs 06, 12).

## 10. Mapping to the owner's documents

| Owner idea | Verdict | Reason | Brief |
|---|---|---|---|
| Never chase targets; FLAT valid; agents reason, rules hold the money | KEPT | Supported by every cost, edge and agent brief | 01, 02, 09, 11 |
| 7-state machine OBSERVE→SAFE/LEARN | KEPT, as code | Predefined paths beat LLM supervisors | 02 |
| Always-on scanner | CHANGED → scheduled scan + anomaly watch | Free data is IEX/30 symbols; intraday is fee-negative | 06, 09, 11 |
| 18-agent team under LangGraph | CHANGED → 6 Claude agents + 13 code/stat roles | 3-15× tokens, no measured benefit | 02, 03, 13 |
| Bull/Bear debate | CHANGED → one Red-Team call, shadow | Same-model debate is the weakest configuration | 02 |
| Overall calibrated confidence | CHANGED → Evidence Card (base rate, n, interval; components not pooled) | Pooled forecasts cannot be calibrated; LLM confidence is unusable | 10 |
| Position Manager exits on a confidence fall | CHANGED → pre-registered exits + resting stops | Untested, noisy, adds an API dependency | 17, 23 |
| Hard Risk Gate / Capital Governor | KEPT, expanded with erroneous-order family, reconciliation, dead-man's switch | Knight/Citi lessons | 12, 17 |
| v1 decision rule EV > loss + cost + penalty | KEPT as a Cost Gate (3× cost hurdle) | Right form, made explicit | 10, 07 |
| Ledger / audit (Layer I) | KEPT, plus full LLM record/replay and tax lots | Reproducibility | 13, 19, 22 |
| Strategy Lab | KEPT with trial registry and deflation | Safest LLM role, low yield | 01, 08, 20 |
| Equities + crypto | KEPT; crypto CONDITIONAL on Texas availability, capped sleeve | 10-40× cost gap; state unverified | 11, 21 |
| LONG/SHORT/FLAT | CHANGED → long/flat | No crypto shorts; equity shorts need $2k + whole shares | 05, 17 |
| Data Trust Gate / SAFE; degraded-data override | Gate KEPT; override DROPPED | Hard controls take no overrides | 12, 14 |
| Point-in-time features; freeze contracts first; same path backtest/live | KEPT, made bitemporal | Strongly supported | 04, 06, 14, 16 |
| Paper → shadow → live by gates | KEPT, re-specified as G0-G5 with micro-live | Paper can't validate slow strategies | 20 |
| Flow/Microstructure alpha, L2 order books | DROPPED as alpha; kept as Liquidity & Cost Monitor | OFI horizon is seconds; no equity L2 | 07, 06 |
| Spoofing/layering/wash detection | DROPPED; pump-burst + venue hygiene kept | Needs identity data | 07 |
| HMM/GARCH/jump/anomaly ensemble at once | CHANGED → vol model for sizing, rule regime; others DEFERRED | Leakage and multiple testing | 15 |
| RL layer | DROPPED | Cannot be validated | 15 |
| Wrap v1 as Information Intelligence | CHANGED → rebuild; v1 ideas reused | Leakage, zeroed features, 123 rows | 16 |
| FinBERT/social sentiment/CAR as predictors | DROPPED (FinBERT only as a coarse filter) | Weak, pump surface, leakage | 16 |
| Form 4 / 13F | DEFERRED (Form 4 overlay after archive) | Supported only as a slow overlay | 16, 09 |
| Docker Compose, Redis, Postgres, Kafka, MinIO, Grafana, React | DROPPED → SQLite/Parquet/Streamlit | 8 GB RAM; MinIO archived | 14 |
| Alpaca + Coinbase dual broker | CHANGED → Alpaca only; Coinbase/Kraken as data | Fees 3-4× | 11 |
| Investor view / hosted UI | CHANGED → owner dashboard | Own money only; licences | 12, 06 |
| $100 BTC/ETH intraday examples | DROPPED | Costs exceed edge; Kelly absurdity | 09, 10, 11 |
| Kelly sizing | DEFERRED (≥ 300 outcomes) | Needs calibrated outcomes | 10 |

## 11. Build order

| Phase | Work | Exit criterion | Usable after |
|---|---|---|---|
| P0 (2 wks) | Rotate leaked key; freeze data contracts and schema; trial registry; Alpaca paper; confirm Texas crypto; spikes on duplicate `client_order_id` and websocket replay | Contracts frozen; spikes logged | Clean foundation only |
| P1 (3-4 wks) | Ingest + Data Trust Gate + text archive (EDGAR, news `first_seen_at`); benchmark computed after cost and tax | 30 days of clean runs; Healthchecks green | Daily data-health email; archive accumulating |
| P2 (3-4 wks) | Register A and B; backtest harness on the shared code path; G1 | G1 pass/fail recorded honestly | Research verdict; benchmark portfolio |
| P3 (4 wks + calendar) | Gate, execution service, Position Manager, ledger, kill switch; G2 shadow then G3 paper | Replay identity; drills passed | Full non-LLM JARVIS running in paper |
| P4 (3 wks, overlapping P3) | Agents in order: Narrator → News Analyst (archive-only) → Red-Team (shadow) → Strategy Lab routine; golden set; record/replay; $15 cap | Schema-valid ≥ 99% on golden set; spend under cap | The agent team operating, off the order path |
| P5 (≥ 6 months) | G4 micro-live $500-1,000 | ≥ 20 fills, cost ≤ 1.5× model, no severity-1 incidents | Real-money JARVIS at minimum size |
| P6 (≥ 18 months) | G5 scale steps | Bands held each step | Full intended capital |

Agents follow a working non-LLM paper pipeline, giving an ablation baseline (brief 02). Shadow plus paper takes ~6 calendar months because the strategies are monthly.

## 12. Growth path (explicit triggers)

- **Capital ≥ $2,400:** nightly News Analyst batch on (b1 drag < 2%/yr); **≥ $5,600:** Sonnet-class extraction (briefs 11, 22).
- **First live crypto position or 2 missed runs a month:** move jobs to the VM (brief 23).
- **Archive ≥ 12 months:** Form 4 overlay enters G0. **Headline-score shadow passes ablation:** it may enter one model as a feature (brief 16).
- **≥ 300 resolved outcomes:** calibration curve shown; fractional Kelly cap allowed (brief 10).
- **Capital ≈ $31,500 and a paper-stage edge:** Norgate survivorship-free data ($630/yr at 2% drag) unlocks single-stock momentum and a wider Filing Reader universe (brief 06; ESTIMATE).
- **Equity ≥ $2,000 and a G1-passed strategy needing shorts:** whole-share shorting enabled in the gate (brief 05).
- **IRA confirmed with acceptable fees:** move sleeve A there (brief 19, unverified).
- **Budget ≥ ~$25/month:** Strategy Lab as an API routine; second red-team sample tested (brief 22).
- **Never at this size:** SIP/L2 feeds, intraday strategies, RL.

## 13. Three biggest risks of this proposal

1. **Keeping the vocabulary invites rebuilding the expensive version.** Roster names, scanner and evidence card could pull a solo developer back toward per-candidate LLM calls and a big stack. *Proved wrong if:* LLM spend exceeds $15/month, any LLM call enters the order path, or P3 is not done within 4 months.
2. **The strategies add nothing over the benchmark after tax.** A is about −1 to +1 point of CAGR, B's net Sharpe is unknown, and G1 may fail (briefs 18, 20); JARVIS could be an elaborate way to hold ETFs. *Proved wrong if:* G1 fails for both, or the drawdown benefit does not appear in the first live stress episode. The honest fallback is to run the benchmark with JARVIS as its risk and audit layer.
3. **The Claude agents never earn weight.** Forward evidence accrues slowly and models retire about every 12 months, restarting the clock (briefs 00, 22), so the "AI agent" part may stay narrative and risk-flagging. *Proved wrong if:* after 12 months the red-team and news ablations show no gain over the code-only arm; then the agents remain reporters and researchers, and the claim that they improve decisions is dropped.

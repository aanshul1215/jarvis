# 04 - Trading engine: build vs adopt

Research date: 2026-10-01. Every finding is tagged FETCHED (opened in this session) or RECALLED (from memory, not re-checked), with a confidence level. Pages were read through a summarising fetch tool, so exact wording and fine numeric detail should be re-checked before anything is frozen into a design decision.

## 1. Questions asked

1. Should JARVIS build its own event bus + backtester + execution engine (as v3 build steps 1, 3 and 8 imply), or adopt an existing open-source engine?
2. Which candidates genuinely give "the same code path for backtest, paper and live" for equities AND crypto?
3. For each of NautilusTrader, QuantConnect LEAN, freqtrade, Hummingbot, vectorbt, backtrader, zipline-reloaded, Microsoft Qlib, FinRL: maintenance status today, licence, asset classes, adapters (Alpaca / Coinbase / IBKR / Binance), parity, fill and slippage modelling, Windows/Docker, learning curve.

Authoritative sources chosen before searching: each project's GitHub repository and GitHub REST API (status, licence, release dates), each project's official documentation (adapters, fill model, platform support), QuantConnect docs (CLI terms), Alpaca docs (paper-trading limits). No blogs or comparison articles were used.

## 2. Findings

### 2.1 Summary table

| Engine | Maintained (Oct 2026) | Licence | Equities | Crypto | Alpaca | Coinbase | IBKR | Binance | One code path backtest/paper/live |
|---|---|---|---|---|---|---|---|---|---|
| NautilusTrader | Yes, very active (2.0.0rc5 on 2026-09-15) | LGPL-3.0 | Yes, via IBKR only | Yes | **No** (open RFC) | Yes (Advanced Trade) | Yes | Yes | Yes (backtest / sandbox / live share one kernel) |
| QuantConnect LEAN | Yes (pushed 2026-09-30) | Apache-2.0 | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| freqtrade | Yes (2026.9 on 2026-09-29) | GPL (v3 recalled) | No | Yes | No | No | No | Yes | Yes, crypto only |
| Hummingbot | Yes (v2.17.0 on 2026-09-22) | Apache-2.0 | No | Yes | No | Yes | No | Yes | Partial (market-making focus; backtesting docs not verified) |
| vectorbt (OSS) | Yes (v1.1.1 on 2026-09-26) | Apache-2.0 + Commons Clause | Research only | Research only | - | - | - | - | No (no execution layer) |
| backtrader | **No** (last commit 2023-04-19) | GPL-3.0 | Yes | Via third-party | Third-party | No | Yes (legacy IbPy) | Third-party | Nominally yes, but abandoned |
| zipline-reloaded | Slow (3.1.1 in July 2025) | Apache-2.0 | Yes | No | No | No | No | No | No (backtest only) |
| Microsoft Qlib | Commits yes (pushed 2026-09-22); last tagged release shown is v0.9.0, Dec 2022 | MIT | Yes (US/China) | No | No | No | No | No | No (no broker layer) |
| FinRL | Commits yes; classic repo self-described as educational; last release 0.3.5, June 2022 | MIT | Yes | Yes | Basic | No | No | Data only | No |

### 2.2 NautilusTrader

- Licence LGPL-3.0; 29.5k stars; supports Linux x86_64/ARM64, macOS ARM64 and Windows x86_64; Python 3.12-3.14; Docker images published at ghcr.io. README warns that the project is still under active development and that breaking changes can occur between releases. Source: https://github.com/nautechsystems/nautilus_trader - FETCHED - high.
- Release cadence: 1.230.0 Beta (2026-06-29), 1.231.0 Beta (2026-08-02), then 2.0.0rc3/rc4/rc5 (2026-08-20, 09-02, 09-15). The rc5 notes list numerous breaking changes (renamed data variants, changed constructors, stricter reduce-only handling). It is in the middle of a major-version transition. Source: https://github.com/nautechsystems/nautilus_trader/releases - FETCHED - high.
- Integrations listed as stable: Binance, Bybit, Coinbase, Kraken, OKX, BitMEX, Deribit, dYdX, Hyperliquid, Interactive Brokers, Databento, Tardis, Betfair, Polymarket and others. **Alpaca is not listed.** Source: https://nautilustrader.io/docs/latest/integrations/ - FETCHED - high.
- Alpaca status: issue #3374 "[RFC] Alpaca Markets Integration" is open (created 2026-01-01); an implementation PR #3375 is closed; an older request #1781 (2024) is closed. I could not see maintainer comments, so whether the PR was rejected or superseded is **unverified**. Source: GitHub search API for "alpaca" in the repo - FETCHED - medium.
- Coinbase adapter targets the Advanced Trade API (spot, perpetuals, dated futures), L2 market-by-price book over WebSocket, MARKET/LIMIT/STOP_LIMIT orders only; the Coinbase sandbox is described as a static mock; one product family per execution client. Source: https://nautilustrader.io/docs/latest/integrations/coinbase/ - FETCHED - high.
- IBKR adapter needs TWS or IB Gateway running (a dockerised gateway is supported), covers equities/options/futures/FX, paper trading via the paper gateway port. Source: https://nautilustrader.io/docs/latest/integrations/interactive_brokers/ - FETCHED - high.
- Architecture: one `NautilusKernel` shared by three environments - Backtest (historical data, simulated venue), Sandbox (live data, simulated venue), Live (live data, real venue with paper or real account). Single-threaded core with its own MessageBus (pub/sub, request/response); Redis is an optional backing for cache and message-bus streaming. Crash-only design intended for an external supervisor. Only one node per process. Source: https://nautilustrader.io/docs/latest/concepts/architecture and the installation page - FETCHED - high.
- Parity caveat stated by the project itself: live execution introduces venue, transport, timing and reconciliation behaviour a simulation may not reproduce. Source: README - FETCHED - high.
- Fill modelling: with L2/L3 data market orders walk the book; with L1 data, market orders fill at the quote and any residual one tick worse; limit-order queue handling tracks available size, not true order priority, with an optional `queue_position` flag and a probabilistic `prob_fill_on_limit`; fill models are seedable. Market impact was not described on the pages opened. A latency model exists in my recollection, but I did not open that page (RECALLED, medium). Source: https://nautilustrader.io/docs/latest/concepts/backtesting/fill-prices-and-matching - FETCHED - medium.
- Windows: officially "Windows Server 2022 and later (x86_64)". Windows 11 desktop is not explicitly named on the page as summarised; treat native Windows as second-class and run in a Linux container. Source: installation docs - FETCHED - medium.
- Learning curve: steep (strongly typed domain model, Rust/Cython core, config objects, Parquet data catalog). This is my judgement - RECALLED - medium.

### 2.3 QuantConnect LEAN

- Apache-2.0; 21.8k stars; pushed 2026-09-30; not archived; C# engine with Python and C# algorithm APIs; Docker images; `lean live` runs live trading locally in Docker. Sources: https://github.com/QuantConnect/Lean and https://api.github.com/repos/QuantConnect/Lean - FETCHED - high.
- Local brokerages via LEAN CLI include Alpaca (US equities, options, crypto), Coinbase, Interactive Brokers, Binance, Kraken, plus Schwab, TradeStation, Tastytrade, Bybit and more. This is the only candidate that covers both brokers named in the JARVIS documents. Source: https://www.quantconnect.com/docs/v2/lean-cli/live-trading/brokerages - FETCHED - high.
- **Cost catch:** the CLI documentation says you must be a member of an organisation on a paid tier to use the CLI. Exact tier prices did not render on the pricing page; **prices are unverified**. Source: https://www.quantconnect.com/docs/v2/lean-cli/key-concepts/getting-started - FETCHED - high (requirement), unverified (price).
- The Apache-2.0 engine can be compiled and run without the CLI, and brokerage plugins live in separate open repositories - RECALLED - medium. Running it that way means hand-configuring a .NET engine and supplying your own data in LEAN's format, which is real work.
- Reality modelling is the richest of the group: pluggable fill, slippage, fee, brokerage, buying-power, settlement, short-availability, margin-interest models; the docs warn that defaults assume highly liquid assets. Source: https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/key-concepts - FETCHED - high.
- Learning curve: moderate-to-steep; the algorithm is a class inside LEAN's lifecycle, Python runs embedded in a .NET process, and local data access leans on paid QuantConnect datasets (QCC tokens). Source for data purchases: https://www.quantconnect.com/pricing - FETCHED - medium.

### 2.4 freqtrade

- Very active (monthly releases, 2026.9 on 2026-09-29), 55k stars, Docker recommended. Crypto only: Binance, Bybit, Kraken, OKX, Gate, Bitget, Hyperliquid etc. **Coinbase is not in the supported list, and there is no equities support.** Sources: https://github.com/freqtrade/freqtrade and /releases - FETCHED - high. Licence GPLv3 - page said "GPL", version RECALLED - medium.
- Same strategy class runs in backtest, dry-run and live. Backtesting is candle-based and assumes no slippage; the docs state backtesting never replaces dry-run and describe known ordering differences (stoploss vs ROI). Source: https://www.freqtrade.io/en/stable/backtesting/ - FETCHED - high.

### 2.5 Hummingbot

- Apache-2.0, 20.3k stars, v2.17.0 on 2026-09-22, Docker Compose install, 40+ crypto venues including Coinbase Advanced Trade and Binance; no equities brokers. Built around market making and arbitrage, which is the wrong shape for a directional, multi-horizon signal system. Sources: https://github.com/hummingbot/hummingbot and GitHub API releases - FETCHED - high. The backtesting documentation page returned 404, so the quality of its backtester is **unverified**.

### 2.6 vectorbt

- Open-source edition is Apache-2.0 with Commons Clause (cannot be sold as a product); v1.0.0 (2026-04-22) added a Rust backend, v1.1.1 on 2026-09-26. It is the community edition of the paid vectorbt PRO. No broker or execution layer. Sources: https://github.com/polakowo/vectorbt and GitHub API - FETCHED - high.
- Role: fast vectorised research and parameter sweeps, not an engine.

### 2.7 backtrader

- GPL-3.0, 23.4k stars, last commits 2023-04-16 to 2023-04-19; live integrations are IB via the obsolete IbPy, Oanda and Visual Chart. Effectively unmaintained. Sources: https://github.com/mementum/backtrader and /commits/master - FETCHED - high. **Do not adopt.**

### 2.8 zipline-reloaded

- Apache-2.0, 1.9k stars, releases 3.0.4 (May 2024), 3.1 (Sep 2024), 3.1.1 (July 2025). US-equity daily/minute backtesting with a Pipeline factor API. No live trading in the maintained fork - RECALLED - medium (the README's "live-trading engine" phrase describes Quantopian's historical use). Sources: GitHub repo and releases API - FETCHED - high for dates.

### 2.9 Microsoft Qlib

- MIT, 49k stars, repo pushed 2026-09-22, 483 open issues; the release shown on the repo page is v0.9.0 dated December 2022 (I did not confirm whether newer tags exist on PyPI - unverified). Equity research platform (US and China data, daily and 1-minute). Backtest uses configured costs, a deal price and limit thresholds; documentation mentions no broker connection. Sources: https://github.com/microsoft/qlib, GitHub API, https://qlib.readthedocs.io/en/latest/component/strategy.html - FETCHED - high.
- Role: a research/ML workflow pattern (which is how the JARVIS documents cite it), not an execution engine.

### 2.10 FinRL

- MIT, 16.5k stars, last tagged release 0.3.5 (June 2022) though commits continue. The README itself calls this repository the original educational and research framework and points to FinRL-X / FinRL-Trading for a production-oriented stack. Source: https://github.com/AI4Finance-Foundation/FinRL - FETCHED - high.
- FinRL-X (Apache-2.0, 3.8k stars, 322 commits) supports Alpaca only and claims deployment consistency through a weight-vector interface; young and equities-centred. Source: https://github.com/AI4Finance-Foundation/FinRL-Trading - FETCHED - medium.

### 2.11 Paper trading is not a fill model

- Alpaca's paper environment does not simulate market impact, information leakage, latency slippage, queue position for non-marketable limits, price improvement, regulatory fees or dividends; it does cover crypto and randomly partial-fills about 10% of the time. Source: https://docs.alpaca.markets/docs/paper-trading - FETCHED - high. The JARVIS Architecture document already acknowledges this, correctly.

## 3. What this means for the JARVIS design documents

1. **v3 build step 3 ("prove that the same data path works for backtest and live") is supported as a requirement, but the documents imply building it from Redis Streams/NATS plus custom services.** That is the most expensive and bug-prone part of the whole system for a solo developer, and two maintained engines already provide it (NautilusTrader, LEAN). Building a deterministic event-driven backtester with order state machines, reconciliation and realistic matching is a multi-month project in its own right. The "build" option is weakened.
2. **Only two of nine candidates meet the equities + crypto + parity requirement.** freqtrade and Hummingbot are crypto-only; vectorbt, zipline-reloaded, Qlib and FinRL have no production execution; backtrader is dead.
3. **The documents' broker choice (Alpaca + Coinbase) conflicts with the technically strongest Python-native engine.** NautilusTrader has no Alpaca adapter. With NautilusTrader, equities go through IBKR, or someone writes and maintains an Alpaca adapter. LEAN supports both Alpaca and Coinbase, but its convenient local path requires a paid QuantConnect tier.
4. **"Event bus: Redis Streams or NATS" (v3 section 3) partly duplicates what an adopted engine supplies.** Nautilus has an internal MessageBus with optional Redis streaming. A separate bus is still reasonable between the slow LLM agents and the kernel, but not inside the trading core.
5. **Execution Agent and Position Manager (v3) should not be LLM agents.** In either engine these are deterministic strategy/exec-algorithm components inside the kernel. This supports the documents' own principle ("deterministic routing for money-critical steps") and sharpens it: Claude agents sit outside the kernel and hand over structured, validated signals.
6. **Flow/Microstructure Agent and the $100 BTC/ETH order-flow examples.** Nautilus can replay L2 data and walk the book, but queue priority is approximated and market impact was not shown as modelled; freqtrade assumes zero slippage; Alpaca paper ignores latency and queue position. No candidate will validate a +$0.27 intraday order-flow edge to the precision the worked examples imply. Those examples are weakened as evidence of anything.
7. **The citation of Qlib and FinRL as "research patterns" is fair; neither should be mistaken for an execution engine.** FinRL's own README demotes the classic repo to educational use.
8. **"Docker Compose on a dedicated laptop" is supported** - every viable candidate ships Docker images, and running in Linux containers sidesteps the weaker native-Windows story.

## 4. Recommended changes

**Recommendation: HYBRID - adopt an engine for the deterministic core, build only the JARVIS-specific layers around it.**

1. Do not build a custom event bus, backtester, order manager or simulated exchange. Build only: data-trust gate, feature/signal services, the Claude agent layer, confidence calibration, ledger, dashboard, and a thin "signal intake" component inside the engine.
2. Primary candidate: **NautilusTrader** as the kernel (backtest -> sandbox -> live with one strategy class; Coinbase Advanced Trade and IBKR adapters marked stable; Python-native so it sits beside the ML stack; LGPL is unproblematic for private use). Conditions: pin an exact version, expect breaking changes during the 2.0 transition, run in a Linux container.
3. Fallback candidate: **LEAN**, chosen if the owner insists on Alpaca for equities or cannot open an IBKR account in their jurisdiction. Budget for the paid QuantConnect tier (price to be confirmed) or accept the effort of running the bare engine.
4. Before committing, run a time-boxed spike (about one to two weeks): implement one trivial strategy (for example a daily moving-average cross on one ETF and BTC-USD) in both engines, run backtest then paper, and compare fills. Decide on evidence, not on this report alone.
5. Revisit the broker line in the stack: replace "Alpaca + Coinbase" with "broker chosen after the engine spike and after jurisdiction is known"; IBKR is the equities path under Nautilus.
6. Keep vectorbt (or plain pandas/polars) for fast research screening only; any strategy that will touch capital must be re-run in the adopted event-driven engine before promotion. Mind the Commons Clause if JARVIS is ever sold.
7. Drop backtrader, zipline-reloaded and classic FinRL from consideration. Keep Qlib only as a reference for the research workflow.
8. Rewrite v3 step 3 as: "Stand up the adopted engine; load historical data into its catalog; prove one strategy runs unchanged in backtest, sandbox/paper and live-small." Rewrite step 8 to add a three-way reconciliation (backtest fill vs paper fill vs live fill) as a promotion gate.
9. Architecture boundary: Claude agents publish typed signals (schema-validated, timestamped, with expiry) to a queue; an Actor inside the kernel consumes them; sizing, risk gate and order handling stay inside deterministic kernel code. The same recorded signal stream must be replayable in backtest, otherwise the parity claim does not hold for the agent layer.
10. Scale back the microstructure ambitions until L2 history is available and a fill model has been checked against real small-size fills.

## 5. Open uncertainties

- Owner's jurisdiction is unknown; it decides whether Alpaca, Coinbase Advanced Trade or IBKR are even available. This could flip the engine choice.
- Why Nautilus PR #3375 (Alpaca adapter) was closed, and whether maintainers intend to accept an Alpaca integration - unverified.
- QuantConnect paid-tier prices and whether local live trading needs additional per-brokerage or node fees - unverified (pricing page did not render numbers).
- Whether NautilusTrader 2.0 goes final soon and how painful the 1.x -> 2.0 migration is; whether Windows 11 desktop is supported natively.
- Nautilus latency and market-impact modelling: not confirmed from the pages opened.
- Hummingbot's backtester quality and zipline-reloaded's lack of live trading are not confirmed from primary pages.
- Qlib: whether releases newer than v0.9.0 exist on PyPI.
- How to replay LLM agent outputs deterministically in backtest (LLM outputs are not point-in-time reproducible and carry look-ahead risk from training data). This is a design problem no engine solves; it belongs to another research topic but directly limits the parity claim.
- Release years reported by the page-summarising tool were wrong on first pass for two projects and corrected through the GitHub API; freqtrade and Nautilus release dates were read from the releases page only.

## 6. Source list (all FETCHED 2026-10-01 unless noted)

- https://github.com/nautechsystems/nautilus_trader
- https://github.com/nautechsystems/nautilus_trader/releases
- https://nautilustrader.io/docs/latest/integrations/
- https://nautilustrader.io/docs/latest/integrations/coinbase/
- https://nautilustrader.io/docs/latest/integrations/interactive_brokers/
- https://nautilustrader.io/docs/latest/concepts/architecture
- https://nautilustrader.io/docs/latest/concepts/backtesting and /fill-prices-and-matching
- https://nautilustrader.io/docs/latest/getting_started/installation
- https://api.github.com/search/issues?q=alpaca+repo:nautechsystems/nautilus_trader
- https://github.com/nautechsystems/nautilus_trader/issues/3374 (body only; comments not visible)
- https://github.com/QuantConnect/Lean ; https://api.github.com/repos/QuantConnect/Lean
- https://www.quantconnect.com/docs/v2/lean-cli/live-trading/brokerages
- https://www.quantconnect.com/docs/v2/lean-cli/key-concepts/getting-started
- https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/key-concepts
- https://www.quantconnect.com/pricing ; https://www.quantconnect.com/docs/v2/cloud-platform/organizations/tier-features (no prices rendered)
- https://github.com/freqtrade/freqtrade ; /releases ; https://www.freqtrade.io/en/stable/backtesting/
- https://github.com/hummingbot/hummingbot ; https://api.github.com/repos/hummingbot/hummingbot/releases
- https://github.com/polakowo/vectorbt ; https://api.github.com/repos/polakowo/vectorbt/releases
- https://github.com/mementum/backtrader ; /commits/master
- https://github.com/stefan-jansen/zipline-reloaded ; https://api.github.com/repos/stefan-jansen/zipline-reloaded/releases ; https://zipline.ml4trading.io/
- https://github.com/microsoft/qlib ; https://api.github.com/repos/microsoft/qlib ; https://qlib.readthedocs.io/en/latest/component/strategy.html
- https://github.com/AI4Finance-Foundation/FinRL ; https://api.github.com/repos/AI4Finance-Foundation/FinRL ; https://github.com/AI4Finance-Foundation/FinRL-Trading
- https://docs.alpaca.markets/docs/paper-trading
- Failed to open (404): https://hummingbot.org/strategies/v2-strategies/backtesting/ ; https://nautilustrader.io/docs/latest/concepts/backtesting/fill_models/


## Independent verification (2026-10-01)

Confirmed (re-fetched):
- NautilusTrader latest release v2.0.0rc5, 2026-09-15, prerelease; wheels for Windows/Linux/macOS, Python 3.12-3.14. https://api.github.com/repos/nautechsystems/nautilus_trader/releases
- NautilusTrader integration list has no Alpaca; Coinbase, Binance, Interactive Brokers, Kraken, etc. all marked stable. https://nautilustrader.io/docs/latest/integrations/
- Nautilus Windows support is officially "Windows Server 2022 and later" x86_64 only. https://nautilustrader.io/docs/latest/getting_started/installation
- LEAN: Apache-2.0, 21,835 stars, pushed 2026-09-30, not archived. https://api.github.com/repos/QuantConnect/Lean
- LEAN CLI: "you must be a member in an organization on a paid tier". https://www.quantconnect.com/docs/v2/lean-cli/key-concepts/getting-started
- freqtrade official exchange list excludes Coinbase. https://www.freqtrade.io/en/stable/exchanges/
- Alpaca paper trading omits market impact, latency slippage, queue position, fees; supports crypto; 10% partial fills. https://docs.alpaca.markets/docs/paper-trading

Corrected / sharpened:
- Nautilus Alpaca PR #3375 was closed unmerged because maintainers said they lack capacity to assess or support the integration (not superseded). Treat a first-party Alpaca adapter as unlikely; any Alpaca path means self-maintaining an adapter. https://github.com/nautechsystems/nautilus_trader/pull/3375
- The "jurisdiction unknown" uncertainty is resolved: owner is a US resident (context section C). Alpaca (US), Coinbase and IBKR are all available to US residents, so the fallback trigger "cannot open IBKR" does not apply. But the real constraint is budget (~$0/month).
- LEAN fallback is NOT free: the Free plan excludes local coding/CLI (Researcher tier and up includes it). Prices still unverified. Under a near-zero budget, LEAN via CLI is effectively ruled out; the bare engine route costs development time instead.
- freqtrade: for US users Binance.com API access is region-restricted; freqtrade docs point to Binance US. "Binance" in the table is not usable as-is for this owner. Same caution applies to Nautilus's Binance adapter (binance.com vs Binance.US).
- Latest-release rows should say "2.0.0rc5 pre-release", i.e. there is no stable 2.0 yet; pinning a 1.23x beta or an rc are the only options.

Missed considerations (owner constraints):
- $1,000-$10,000 capital: fixed per-trade costs, spreads and the 10% partial-fill / no-slippage paper gaps dominate; a heavyweight engine plus 3-way reconciliation is over-engineered relative to capital. A thin custom daily-bar executor over Alpaca (free paper + commission-free US equities/crypto) may be the cheaper, defensible option; the "do not build" conclusion should be reconsidered at this scale.
- US pattern day trader rule (margin accounts under $25k) limits intraday equity strategies; cash-account settlement also applies. Not mentioned in the brief.
- Market data: free tiers (Alpaca IEX feed, Coinbase public) are limited; Nautilus/LEAN data catalogs and Databento/Tardis are paid. Near-zero budget means daily/minute bars only, which also undermines the L2 microstructure discussion.
- Taxes (US wash-sale on equities, crypto taxable events) affect turnover design.

Unverifiable in this pass: QuantConnect tier prices; Nautilus latency/market-impact models; Hummingbot backtester; zipline-reloaded live-trading absence; Qlib releases after v0.9.0; Nautilus 2.0 final date; Nautilus on Windows 11 desktop.

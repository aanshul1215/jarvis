# 01 - LLM trading agents: what is actually measured

Research date: 2026-10-01. Basis tags: FETCHED = opened in this session; RECALLED = from memory, not re-checked; UNVERIFIED = could not open an authoritative source. Note: pages were read through a fetch-and-summarise tool, so individual table cells should be re-checked against the PDF before being quoted in a design document.

## 1. Questions asked

Facts needed and the authoritative source chosen for each:

| Fact needed | Authoritative source |
|---|---|
| Architecture, claims and evaluation design of each system | The original arXiv paper (full HTML), not the abstract |
| Repo status today, disclaimers | The GitHub README itself |
| Owner's LangAlpha claim | Chen-zexi/LangAlpha README |
| Whether results survive longer periods / more symbols / costs | Independent re-test papers (FINSABER, KDD 2026) |
| Memorisation / look-ahead contamination | Lopez-Lira et al.; Glasserman & Lin; Profit Mirage; KTD-Fin |
| Forward / live results 2025-2026 | StockBench, LiveTradeBench, AI-Trader, Agent Market Arena, CLQT, Alpha Arena |

## 2. Findings

### 2.1 The systems: what each claims and how it was tested

**TradingAgents (Tauric Research)** - arXiv 2412.20138 (v7, Jun 2025), FETCHED, high confidence.
- Architecture: four analysts (fundamental, sentiment, news, technical) -> bull/bear researcher debate -> trader -> risk team -> portfolio manager; LangGraph.
- Evaluation: 1 Jan - 29 Mar 2024, roughly 60 trading days, a handful of mega-cap tech stocks (AAPL, GOOGL, AMZN reported in the main table). Backbones o1-preview / gpt-4o / gpt-4o-mini. Baselines: buy-and-hold, MACD, KDJ+RSI, ZMR, SMA. No ML baseline.
- Reported: cumulative return 23-27% in three months, Sharpe 5.6-8.2, max drawdown 0.9-2.1%.
- The authors themselves footnote that the Sharpe exceeds their expected empirical range and attribute it to few pullbacks in the window; the test was kept to three months because each decision costs about 11 LLM calls and 20+ tool calls.
- Transaction costs/slippage: not stated. Ablations: none found. The whole test window lies inside the training data of the models used (medium confidence on the exact cutoffs; RECALLED).
- Repo (https://github.com/TauricResearch/TradingAgents, FETCHED, high): about 109k stars, Apache-2.0, v0.5.2 released Sept 2026, actively maintained, supports Claude. README states it is for research, that performance varies with model, temperature, period and data, that two runs of the same ticker/date can differ, and that it is not trading advice. It now has a markdown decision-memory log, SQLite checkpoint/resume and a backtest runner. It publishes no updated performance claim.

**FinMem** - arXiv 2311.13743, FETCHED, high.
- Single agent with profiling, layered (short/mid/long) memory and decision module.
- Test: 6 Oct 2022 - 10 Apr 2023 (about six months), five stocks (TSLA, NFLX, AMZN, MSFT, COIN), GPT-4-Turbo. Baselines: buy-and-hold, three DRL agents, two LLM agents. Costs not mentioned. Headline: TSLA +61.8% versus buy-and-hold -18.6%.
- Repo (pipiku915/FinMem-LLM-StockTrading, FETCHED): about 960 stars, MIT; README does not explain how to obtain the dataset or reproduce the paper numbers. Last commit date not visible (unverified).

**FinAgent** - arXiv 2402.18485 (KDD 2024, venue RECALLED), FETCHED for content, high.
- Multimodal (news, prices, K-line chart images), dual-level reflection, memory retrieval, tool-augmented.
- Test: 1 Jun 2023 - 1 Jan 2024 (about seven months; the tool reported "398 trading days", which is not consistent with those dates - treat as unverified), five US stocks plus ETH. Claims 36% average profit improvement and 92.27% ARR on TSLA. Commission said to be incorporated but no rate given. Authors admit single-asset only and that the stock-specific tools made crypto 21% worse.
- Repo DVampire/FinAgent: 75 stars, 7 commits, MIT - effectively a code drop, not a maintained project (FETCHED, medium).

**FinCon** - arXiv 2407.06567 (NeurIPS 2024), FETCHED, high.
- Manager-analyst hierarchy, CVaR-triggered within-episode risk control, "conceptual verbal reinforcement" (belief updates between episodes).
- Test: 5 Oct 2022 - 10 Jun 2023 (eight months), eight single stocks and two three-stock portfolios chosen from a 42-stock pool by news availability; GPT-4-Turbo. Costs not mentioned. Reported 82.9% on TSLA; portfolio Sharpe 3.27. Own ablations: removing CVaR control or belief updates hurts.
- Repo The-FinAI/FinCon: 67 stars, 11 commits; README apologises that the full code is still not released because of commercial API dependencies (FETCHED, high). So the headline results are not independently reproducible.

**FinRobot (AI4Finance)** - arXiv 2405.14767 and repo, FETCHED, high.
- A four-layer platform for equity-research report generation (valuation, bull/bear synthesis). The paper reports no trading performance at all. The README now stresses that all numbers come from deterministic Python operators and the LLM only narrates; "not ... recommendations for live trading". About 8.1k stars, Apache-2.0.

**virattt/ai-hedge-fund** - repo, FETCHED, high.
- About 63.8k stars, MIT. Persona-style "investor agents" plus risk and portfolio managers. README: educational only, "the system does not actually make any trades", no performance claims. Notable: its backtester now withholds tickers and calendar dates (periods shown as t-0, t-1) to reduce look-ahead - the maintainers themselves treat memorisation as a real problem.

**LangAlpha** - see 2.2.

Pattern across the papers: 3-8 month windows, 3-8 hand-picked large-cap or high-news names, test windows inside the LLM's training data, costs absent or unspecified, no confidence intervals, no multiple-run variance.

### 2.2 Verification of the owner's LangAlpha claim

VERIFIED (FETCHED, high). https://github.com/Chen-zexi/LangAlpha carries a notice that the repository is early work and no longer considered best practice as of 26 March 2026, pointing to https://github.com/ginlix-ai/LangAlpha. The old README also confirms 2-6 minutes per query and 30k-100k+ tokens (max observed 490k+), supervisor plus researcher/market/browser/coder/analyst/reporter agents, MongoDB, US equities only, no live execution. The v3 doc's description is accurate.

What the v3 doc misses: the successor (ginlix-ai/LangAlpha, about 1.8k stars, Apache-2.0, FETCHED) abandoned the fixed role-pipeline the owner is borrowing. It is now a Claude/LangChain ReAct agent with parallel sub-agents that write and run Python in a sandbox ("programmatic tool calling") instead of pushing raw data through the context window, with PostgreSQL checkpointing, Redis, reusable research "skills" and source-provenance tracking. It remains explicitly research-only. The pattern the owner cites as "useful reference ideas" is the one its own authors moved away from.

### 2.3 Independent re-tests and contamination evidence

**FINSABER** - Li, Kim, Cucuringu, Ma, arXiv 2505.07078, KDD 2026 Datasets & Benchmarks (oral). FETCHED, high.
- Re-ran FinMem and FinAgent (GPT-4o / 4o-mini) over 2004-2024 on 60-90+ symbols chosen by unbiased rules, with costs of $0.0049/share (min $0.99/order), against 13 baselines including buy-and-hold, rule-based, ARIMA, XGBoost and RL.
- On the composite universes buy-and-hold Sharpe was 0.32-0.70; FinMem -0.25 to 0.03; FinAgent 0.09-0.24. By regime: FinAgent Sharpe 0.12 in bull markets and -0.38 in bear; FinMem -0.19 and -0.97. Simple ATR-band and ARIMA strategies were positive in every regime.
- Conclusion: the published edge disappears with longer periods and wider universes; the agents are too cautious in bull markets and too aggressive in bear markets.
- Caveats: TradingAgents and FinCon were NOT re-tested (FinCon closed-source); and the 2004-2024 window is itself inside the LLM's training data, so contamination should have helped the agents - they still lost.

**Memorisation** - Lopez-Lira, Tang, Zhu, arXiv 2504.14765. FETCHED (abstract), high. LLMs recall exact economic and market values from before their cutoff; telling the model to respect a historical date does not stop it; masking fails because models reconstruct the entity and date from context. Their conclusion: LLM forecasts for periods inside the training window cannot be trusted as evidence of skill.

**Glasserman & Lin**, arXiv 2309.17322. FETCHED (abstract), high. Headline-sentiment strategy with and without company names. In-sample, anonymised headlines did better (a "distraction" effect larger than look-ahead); out-of-sample, look-ahead was not an issue. Anonymisation is suggested for cleaner backtests. Note the tension with Lopez-Lira et al. on whether masking is sufficient - masking helps but is not a guarantee.

**Profit Mirage** - Li et al., arXiv 2510.07920. FETCHED (abstract only), medium. Reports that backtested returns of LLM agents collapse once the test moves past the model's knowledge window. Numbers not extracted; the paper also promotes its own method, so treat its positive claims with caution.

**KTD-Fin** - Zhu et al., arXiv 2605.28359 (May 2026). FETCHED (abstract), medium. Ten frontier LLM agents on CSI300, 2024-2026, with identifiers and dates masked; returns are mostly explained by passive market and style exposure, with little evidence of persistent stock-selection alpha. Chinese A-shares, so transfer to US equities/crypto is an inference.

**Survey** - Nguyen & Pham, arXiv 2603.27539 (Mar 2026, preprint, not peer-reviewed as far as I can tell). FETCHED, medium. Of 14 systems reviewed, 2 model transaction costs, none report confidence intervals, none meet all five of their minimum evaluation standards. Their "coordination matters more than model size" claim is explicitly labelled a hypothesis resting on the original authors' own ablations.

### 2.4 Forward / live benchmarks 2025-2026

- **StockBench** (arXiv 2510.02209), FETCHED, high. Mar-Jun 2025 (82 trading days, after model cutoffs), top-20 Dow stocks, $100k, no costs or slippage. Model returns ranged -2.8% to +2.4% against +0.4% for equal-weight buy-and-hold: differences that small over 82 days are noise. All agents underperformed the passive baseline in the down-market window.
- **LiveTradeBench** (arXiv 2511.03628), FETCHED (abstract), medium. 21 LLMs, 50 live days, US stocks and Polymarket. General benchmark (LMArena) rank does not predict trading outcome.
- **AI-Trader** (HKUDS, arXiv 2512.10971), FETCHED (abstract), medium. Live benchmark on US stocks, A-shares, crypto; most agents had poor returns and weak risk management.
- **Agent Market Arena** (arXiv 2510.11695, WWW 2026 per the FinCon README), FETCHED, medium. Aug-Sep 2025, four assets (TSLA, BMRN, BTC, ETH), simulated fills, no cost model, no significance tests. Finding: agent framework design changes behaviour more than the LLM backbone. A single-agent-with-memory baseline was among the best on TSLA. (One table row returned by the fetch was internally inconsistent; do not quote its numbers.)
- **CLQT** (arXiv 2606.29771, v3 Sept 2026), FETCHED (abstract), medium. Real broker paper-trading with costs and a hard time gate: agents beat defensive baselines but do not cleanly beat the index net of costs, and their actual allocations diverge from their own stated analysis (the "stating versus doing" gap, +0.23 live).
- **AlphaForgeBench** (arXiv 2602.18481; several authors overlap with FinAgent), FETCHED (abstract), medium. LLMs making direct discrete trade decisions show extreme run-to-run variance and irrational action flipping even at deterministic decoding; using the LLM to write factor/strategy code that is then executed deterministically removes that instability.
- **Alpha Arena (nof1)**: official pages returned 404/403; UNVERIFIED from a primary source. Secondary news only (low confidence): Season 1, 18 Oct - 3 Nov 2025, six models with $10k real money each on Hyperliquid perpetuals; two finished up (about +22% and +5%) and four lost 42-59%. A later US-stock season reportedly had one model profitable. Two-to-three-week single runs have no statistical power either way.

**What survives out-of-sample:** No study I could open shows an LLM trading agent beating buy-and-hold net of costs over a multi-year, multi-symbol, post-cutoff sample. Forward tests show roughly index-like results with high variance between runs and models. What does replicate: (a) LLMs extract useful structured information from text (news/filing ablations in StockBench degrade when removed); (b) framework design and risk control matter more than which frontier model is used; (c) LLM discretionary decisions are unstable.

## 3. What this means for the JARVIS design documents

**Supported**
- v2/v3 principle "agents may reason; deterministic rules hold the money" and v3's "agents produce structured evidence; they do not directly send broker orders". FinRobot's README, AlphaForgeBench and CLQT all point the same way.
- v1 Layer D (Strategy Lab: LLM proposes hypotheses, backtest/walk-forward/paper validation decides). This is the LLM-as-researcher pattern that the evidence favours.
- v1 Layer G / v3 Capital Governor as a non-LLM veto. AI-Trader and FinCon's ablation identify risk control as the differentiator.
- v3 statement about LangAlpha's notice: verified verbatim in substance.
- v3 build order putting models and walk-forward evaluation (step 5) before LangGraph agents (step 6).

**Weakened**
- v2 "Research patterns folded into the design: TradingAgents ..." and v3 research basis [2]. TradingAgents is a legitimate source of organisational patterns, but its performance evidence is one three-month bull window with no costs and a Sharpe its own authors flag. It cannot be cited as evidence that an analyst/debate/trader pipeline makes money.
- Bull/Bear Agents (v2 "Challenge & Protect", v3 agent table). No independent ablation shows debate adds return; the evidence is the original authors' own. It adds latency and token cost on every candidate. Defensible only as a cheap, offline thesis-stress step on a small number of longer-horizon candidates, with its value measured.
- The 18-agent roster (v3). AMA and the survey suggest design matters, but not that more agents are better; a single agent with memory was competitive. FINSABER explicitly warns against "scaling framework complexity".
- v3 "Thesis confidence" from LLM agents feeding the Confidence Calibrator. CLQT's stating-versus-doing gap and AlphaForgeBench's run-to-run variance mean LLM-stated confidence is not a stable input. It must be treated as a feature to be calibrated on forward data, with a default weight of zero until it earns one.
- v3 "borrow from LangAlpha: supervisor + planner, specialist roles". The authors deprecated that design in favour of code-executing agents with sandboxes and provenance.

**Contradicted**
- Any use of LLM agents in the intraday decision path of the worked examples (v1 BTC, v2 ETH, v3 crypto breakout: order-flow signals, 50-minute to 3-hour holds). Agent pipelines take minutes and many calls per decision (TradingAgents about 11 LLM + 20 tool calls; old LangAlpha 2-6 minutes). No published LLM agent has been validated at intraday frequency. Those examples can only be driven by the deterministic/ML path.
- Any plan to validate LLM-agent components by backtesting over history the model was trained on. Lopez-Lira et al. show date instructions and masking do not prevent recall. For Claude agents, only data after the model's training cutoff (i.e. forward shadow/paper trading) counts as evidence.

## 4. Recommended changes

1. Re-scope LLM agents to three jobs: (a) text-to-structured-feature extraction (news, filings, events) with timestamps and provenance; (b) offline research - proposing hypotheses and writing strategy/factor code that a deterministic backtester judges; (c) explanation, ledger narrative and reporting. Remove LLMs from LONG/SHORT/FLAT selection and from sizing until forward evidence says otherwise.
2. Add an explicit "LLM evidence policy" to the docs: no LLM-in-the-loop backtest result over pre-cutoff data is admissible; record model ID and cutoff date with every LLM output; re-validation is required when the model version changes.
3. Make the bull/bear debate and each specialist LLM agent an ablatable switch. During shadow mode, log decisions with and without each one and keep only those with measurable incremental value net of token cost.
4. Collapse the roster. Start with the deterministic pipeline plus at most three LLM roles (information extraction, research/strategy lab, reviewer/reporter). Add roles only on evidence.
5. Run every LLM judgment N times (or at temperature 0 with a fixed prompt hash) and log dispersion; treat high dispersion as low thesis confidence.
6. Include LLM API cost and decision latency in every P&L and backtest report, as FINSABER and the survey recommend. With a $100 account these costs alone exceed any plausible profit.
7. Benchmark against buy-and-hold and two or three trivial rule strategies on the same universe, always; require multi-regime coverage including a drawdown period before any promotion gate.
8. Borrow engineering, not results: TradingAgents' checkpoint/resume and decision log with realised-outcome feedback; ai-hedge-fund's ticker/date masking in backtests; ginlix LangAlpha's sandboxed code execution and source provenance; FinRobot's rule that numbers come from code and the LLM only narrates; FinCon's idea of a risk trigger (CVaR breach) that forces a review - implemented deterministically.
9. Replace research-basis item [2] with FINSABER, Lopez-Lira et al. and StockBench as the honest evidence base, and keep TradingAgents as a pattern reference only.

Theatre (drop or demote): persona agents imitating famous investors; multi-round debates on every candidate; "risky/neutral/safe" LLM risk debaters in place of numeric limits; LLM-stated percentage confidence; headline Sharpe figures from sub-one-year single-stock tests.

## 5. Open uncertainties

- No independent long-horizon re-test of TradingAgents or FinCon exists that I could find; absence of confirmation, not disproof.
- Alpha Arena results are from secondary reports only.
- Several 2026 papers were read at abstract level (KTD-Fin, CLQT, AlphaForgeBench, Profit Mirage, LiveTradeBench, AI-Trader); numeric details need a full read before being quoted.
- The crypto intraday setting is barely covered by the literature (FinAgent ETH daily; AMA BTC/ETH daily for two months). Nothing here says order-flow ML models fail or succeed - that is a separate topic.
- Whether text-derived LLM features add alpha net of costs for a retail account is plausible but not established by the sources opened here.
- Last-commit dates for FinMem, FinAgent, FinCon and ai-hedge-fund repos were not visible in the fetched pages.
- The 2603.27539 survey is a non-peer-reviewed preprint; its cost-drag estimates are approximations.

## 6. Source list (all FETCHED this session unless noted)

- https://arxiv.org/html/2412.20138v7 - TradingAgents paper
- https://github.com/TauricResearch/TradingAgents
- https://arxiv.org/html/2311.13743 - FinMem; https://github.com/pipiku915/FinMem-LLM-StockTrading
- https://arxiv.org/html/2402.18485 - FinAgent; https://github.com/DVampire/FinAgent
- https://arxiv.org/html/2407.06567 - FinCon; https://github.com/The-FinAI/FinCon
- https://arxiv.org/abs/2405.14767 - FinRobot; https://github.com/AI4Finance-Foundation/FinRobot
- https://github.com/virattt/ai-hedge-fund
- https://github.com/Chen-zexi/LangAlpha ; https://github.com/ginlix-ai/LangAlpha
- https://arxiv.org/html/2505.07078 - FINSABER
- https://arxiv.org/abs/2504.14765 - Memorization Problem
- https://arxiv.org/abs/2309.17322 - Glasserman & Lin
- https://arxiv.org/abs/2510.07920 - Profit Mirage
- https://arxiv.org/abs/2605.28359 - KTD-Fin
- https://arxiv.org/html/2603.27539v1 - evaluation survey
- https://arxiv.org/html/2510.02209 - StockBench
- https://arxiv.org/abs/2511.03628 - LiveTradeBench
- https://arxiv.org/abs/2512.10971 - AI-Trader
- https://arxiv.org/html/2510.11695 - Agent Market Arena
- https://arxiv.org/abs/2606.29771 - CLQT
- https://arxiv.org/abs/2602.18481 - AlphaForgeBench
- Alpha Arena: https://nof1.ai (no detail on page), https://alphaarena.ai (403); secondary only: https://forklog.com/en/four-out-of-six-ai-models-suffer-losses-in-trading-tournament/amp (search snippet, not opened) - UNVERIFIED


## Independent verification (2026-10-01)

Method: re-opened primary sources for the decision-driving claims (scoped to limit usage).

Confirmed
- FINSABER (KDD 2026 D&B oral; 2004-2024; 63-91 symbols in composite setups, abstract says 100+; cost $0.0049/share, min $0.99/order; Sharpe B&H 0.315/0.384/0.703, FinMem -0.253/0.025/-0.228, FinAgent 0.094/0.104/0.241; TradingAgents not tested): https://arxiv.org/html/2505.07078
- TradingAgents repo: 109.4k stars, Apache-2.0, v0.5.2 (2026-09), Claude supported, not-advice disclaimer: https://github.com/TauricResearch/TradingAgents
- LangAlpha deprecation notice dated 26 Mar 2026 pointing to ginlix-ai/LangAlpha: https://github.com/Chen-zexi/LangAlpha
- FinCon repo 67 stars, 11 commits, full code unreleased due to commercial APIs: https://github.com/The-FinAI/FinCon
- Memorization paper (masking and date instructions fail): https://arxiv.org/abs/2504.14765
- StockBench: 3 Mar-30 Jun 2025, 82 days, Dow top-20, $100k, no costs: https://arxiv.org/html/2510.02209
- CLQT (v3 12 Sep 2026): cost-aware, agents do not cleanly beat index, stating-vs-doing gap +0.30 backtest / +0.23 live: https://arxiv.org/abs/2606.29771
- Alpha Arena S1 (secondary sources, now consistent): 6 models, $10k each, Hyperliquid perps; Qwen3 Max $12,231, DeepSeek $10,489, Claude Sonnet 4.5 $5,799, Gemini $5,445, Grok $4,208, GPT-5 $4,126 (so two up, four down 42-59%): https://www.scmp.com/tech/tech-trends/article/3329784/deepseek-outperforms-ai-rivals-real-money-real-market-crypto-showdown

Corrected / weakened
- StockBench return range: a re-fetch gave best model +1.9% (Kimi-K2) and worst -2.8%, buy-and-hold +0.4% (max DD -15.2%); the brief's "+2.4%" was not reproduced. Conclusion (differences are noise) unchanged. Note "all agents underperformed" is too strong: some beat B&H on return.
- Alpha Arena is no longer purely UNVERIFIED: figures above are consistent across several outlets, though still no primary page was opened. Alpha Arena trades US-inaccessible venue (Hyperliquid perps); not a template for a US resident.
- FINSABER costs ($0.0049/share) reflect Moomoo; commission-free brokers (e.g. Alpaca) differ, so cost drag for the owner is spread/slippage plus LLM API cost, not commission.

Not verified (unchanged)
- Profit Mirage, KTD-Fin, LiveTradeBench, AI-Trader, AlphaForgeBench, survey 2603.27539 numbers (abstract level in original; not re-opened here). TradingAgents paper table values and Sharpe footnote not re-opened.

Missed considerations for the owner (US, $1k-$10k, ~$0 budget)
- Pattern Day Trader rule: margin accounts under $25k are limited to 3 day trades per 5 business days (FINRA rule status may be changing in 2026; check current rule). Intraday equity design is infeasible on a small margin account; cash accounts face settlement limits.
- Crypto intraday: retail US fees (Coinbase-type taker fees of tens of bps) can exceed edge on 50-minute to 3-hour holds; Hyperliquid and many perp venues are not available to US persons.
- US tax: short-term gains taxed as ordinary income; wash-sale rules for equities; per-trade record keeping.
- Free data tiers have rate limits, delayed or no order-flow/L2 data; the order-flow-based worked examples likely cannot be fed at zero cost.
- At $1k-$10k and near-zero API budget, LLM cost per decision (~11+ calls for TradingAgents-style) must be budgeted explicitly; prefer batch/cached extraction and the Claude cheapest tier.

# 02 — Multi-agent vs single-agent: does an 18-agent design with bull/bear debate and a supervisor improve decisions?

Research date: 2026-10-01. Every finding is tagged FETCHED (opened in this session) or RECALLED (from memory, not re-opened), with a confidence level.

## Short answer

The evidence does not support the idea that more LLM agents, or LLM-vs-LLM debate, reliably produce better decisions. The controlled literature says: (a) most of the measured benefit of "debate" is plain ensembling/voting; (b) multi-agent systems cost roughly 3-15x the tokens of a single agent; (c) they help on breadth-first, parallelisable, read-heavy research and hurt on sequential, state-dependent tasks; (d) they fail often, mostly for system-design and verification reasons. The published trading multi-agent results (TradingAgents) rest on a three-month, cost-free backtest with no ablation of the debate, and an independent 20-year re-test of comparable LLM trading agents found the advantage disappears.

For JARVIS specifically: of the 18 "agents" in the v3 table, about 13 should be ordinary deterministic code or statistical models (the v3 "Suggested stack" column already says so for most of them), 3-4 have a genuine LLM role, and none of the money-path steps should be an LLM. The right framing is "a deterministic pipeline with a few LLM workflow steps", not "18 agents under a supervisor".

## Questions asked

1. When does multi-agent debate improve accuracy, when does it not, and what does it cost?
2. What are the documented failure modes of multi-agent LLM systems?
3. What do Anthropic and other labs say about workflows vs agents vs multi-agent?
4. Which of the 18 v3 agents genuinely need an LLM?

Authoritative source types chosen before searching: the primary arXiv papers (opened in HTML, not just abstracts, where numbers mattered); Anthropic's own engineering posts; the TradingAgents paper and repository (because the JARVIS docs cite it as a research basis); an independent benchmark paper testing LLM trading agents over long periods.

## Findings

### 1. Multi-agent debate

**F1. The original debate result is real but small-scale and on an old model.** Du et al. 2023 used gpt-3.5-turbo-0301, 3 agents, 2 rounds. Debate vs single agent: arithmetic 81.8 vs 67.0; GSM8K 85.0 vs 77.0; MMLU 71.1 vs 63.9; biographies 73.8 vs 66.0. Majority vote alone got GSM8K to 81.0, i.e. about half the gain is ensembling. The authors note the method is more expensive and that debates often converge on a single answer that is confidently wrong.
Source: https://arxiv.org/abs/2305.14325 (table read via https://ar5iv.labs.arxiv.org/html/2305.14325) — FETCHED — high.

**F2. Debate does not reliably beat simpler baselines.** Smit et al. ("Should we be going MAD?") benchmarked debate protocols on 7 datasets (3 medical, 4 reasoning) with GPT-3.5 and concluded debate systems do not reliably outperform self-consistency and ensembling, and are more sensitive to hyperparameters. One knob (how much agents are told to agree) moved Multi-Persona by about 15 points on one subset — which is evidence of fragility as much as of promise.
Source: https://arxiv.org/abs/2311.17371 and https://arxiv.org/html/2311.17371 — FETCHED — high.

**F3. A strong single prompt matches discussion.** Wang et al. (2024) found a single agent with a strong prompt (with demonstrations) reaches almost the same performance as the best multi-agent discussion approach; discussion only helped when the prompt had no demonstrations.
Source: https://arxiv.org/abs/2402.18272 — FETCHED (abstract page only) — medium-high.

**F4. Large systematic re-evaluation: debate is overvalued.** Zhang et al. (2025) evaluated 5 debate methods on 9 benchmarks with 4 models and found debate often fails to beat chain-of-thought and self-consistency while using significantly more inference compute. Their one positive finding: mixing different underlying models (heterogeneity) consistently helps. I could not extract exact win/loss rates or token multipliers from the page.
Source: https://arxiv.org/abs/2502.08788 — FETCHED (abstract-level detail only) — high for the conclusion, numbers unverified.

**F5. Voting, not debating, does the work.** Choi et al.? (authors not verified by me) "Debate or Vote" (NeurIPS 2025) separated majority voting from inter-agent debate across 7 benchmarks with 5 agents and small open models (Qwen2.5-7B/32B, Llama3.1-8B). Voting alone accounted for most of the gain (e.g. Qwen2.5-7B average 0.769 for voting vs 0.738 for 2-round decentralised debate). They prove that under their model the belief in the correct answer is a martingale across rounds: debate by itself does not raise expected correctness. Caveat: small models, closed-form QA tasks.
Source: https://arxiv.org/html/2508.17536v2 — FETCHED — high for what was measured; author names unverified.

**F6. Where debate does help: information asymmetry with a judge.** Khan et al. (2024): when two "expert" models that can see a text argue for opposing answers and a non-expert judge that cannot see the text decides, judge accuracy rises (non-expert models 76% vs 48% baseline; humans 88% vs 60%). This is a different setup from bull/bear in JARVIS: the debaters hold information the judge lacks, and there is a ground-truth answer.
Source: https://arxiv.org/abs/2402.06782 — FETCHED (abstract page) — high.

**Implication of F1-F6.** Two same-model agents given the same evidence and assigned "bull" and "bear" personas is close to the weakest configuration in this literature: no information asymmetry, no model heterogeneity, no verifiable ground truth at decision time. Expect it to produce fluent, balanced-sounding text whose marginal predictive value is unproven. No paper I opened measures adversarial debate on out-of-sample financial forecasting with costs.

### 2. Failure taxonomies

**F7. MAST (Cemri et al., 2025).** 1,600+ annotated traces across 7 multi-agent frameworks (coding, maths, general tasks), inter-annotator kappa 0.88. 14 failure modes in 3 categories: system design issues about 44% (step repetition 15.7%, unaware of termination conditions 12.4%, disobeying task spec 11.8%); inter-agent misalignment about 32% (reasoning-action mismatch 13.2%, task derailment 7.4%, failing to ask for clarification 6.8%); task verification about 24% (incorrect verification 9.1%, incomplete verification 8.2%, premature termination 6.2%). Reported failure rates of 41% to 86.7% across the 7 systems. Prompt/role fixes gave ChatDev only +9.4% and adding a verification step +15.6% — helpful but not a cure. The authors state gains over single-agent or best-of-N baselines are often minimal.
Source: https://arxiv.org/abs/2503.13657 and https://arxiv.org/html/2503.13657 — FETCHED — high (percentages as extracted by the fetch tool from the HTML version; versions of the paper differ slightly).

**F8. Google/MIT "Towards a Science of Scaling Agent Systems" (Kim et al., Dec 2025).** 260 configurations, 6 agentic benchmarks, 5 architectures (single, independent, centralised, decentralised, hybrid), 3 model families. Mean effect of multi-agent vs single-agent across all configurations: -0.3% (95% CI -58.7% to +77.2%) — i.e. zero on average with huge variance. Sequential planning (PlanCraft): every multi-agent variant was worse, -39% to -70%. Decomposable financial analysis (Finance-Agent, an analyst-style document/quant reasoning benchmark, not trading): centralised multi-agent +80.8% (0.349 to 0.631). Error amplification: independent agents 17.2x, centralised 4.4x. Token/turn overhead: +58% (independent) to +515% (hybrid). Coordination gains shrink once a single agent already exceeds about 45% on the task; tool-heavy tasks are penalised more.
Source: https://arxiv.org/abs/2512.08296 and https://arxiv.org/html/2512.08296 — FETCHED — high for the numbers as reported; it is a preprint.

### 3. Lab guidance

**F9. Anthropic, "Building effective agents" (Dec 2024).** Distinguishes workflows (LLMs and tools orchestrated through predefined code paths) from agents (the LLM directs its own process). Advice: find the simplest solution; a single well-prompted LLM call with retrieval is usually enough; agentic systems trade latency and cost for task performance and risk compounding errors; workflows give predictability for well-defined tasks. Patterns: prompt chaining, routing, parallelisation (sectioning/voting), orchestrator-workers, evaluator-optimizer.
Source: https://www.anthropic.com/engineering/building-effective-agents — FETCHED — high.

**F10. Anthropic, "How we built our multi-agent research system" (2025).** Agents use about 4x the tokens of chat; multi-agent about 15x. Their multi-agent research system beat single-agent Opus 4 by 90.2% on an internal research eval; token usage alone explained 80% of variance on BrowseComp. They state multi-agent suits heavy parallelisation, information exceeding one context window, and many complex tools — and is a poor fit when agents must share the same context or have many inter-dependencies, including most coding tasks.
Source: https://www.anthropic.com/engineering/multi-agent-research-system — FETCHED — high (internal eval, not independently reproduced).

**F11. Anthropic, "Building multi-agent systems: when and how to use them" (23 Jan 2026).** Three justified cases: context protection, parallelisation, specialisation (e.g. an agent struggling with 20+ tools). Multi-agent typically costs 3-10x the tokens. Decompose by context boundaries, not by role or problem type; role-style sequential hand-offs add coordination overhead and lose fidelity at each hand-off.
Source: https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them — FETCHED — high.

**F12. Cognition, "Don't build multi-agents" (Walden Yan, 12 Jun 2025).** Argues parallel sub-agents are fragile because they lack shared context and make conflicting implicit decisions; recommends a single-threaded agent with full trace sharing. Practitioner opinion, not data.
Source: https://cognition.com/blog/dont-build-multi-agents — FETCHED — high that this is what it says; medium as evidence.

**F13. OpenAI, "A practical guide to building agents".** Recalled advice: maximise a single agent first; split only when prompt logic becomes unmanageable or tools overlap/overload. The PDF downloaded but could not be parsed in this session, so this is not verified.
Source: https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf — RECALLED / UNVERIFIED — medium.

### 4. Evidence from trading-specific multi-agent systems

**F14. TradingAgents paper — what it actually measured.** Backtest 1 Jan to 29 Mar 2024 (three months) on a handful of mega-cap tech tickers (AAPL, GOOGL, AMZN reported in the main table). Baselines: buy-and-hold and four rule-based indicators. Reported cumulative returns 23-27% and Sharpe ratios 5.6-8.2. No transaction-cost or slippage modelling described. No ablation isolating the bull/bear debate. LLMs: gpt-4o/4o-mini and o1-preview. The authors themselves flag the Sharpe ratios as exceeding normal empirical ranges and attribute them to the short window. This is not evidence that a multi-agent debate adds alpha.
Source: https://arxiv.org/html/2412.20138 — FETCHED — high.

**F15. TradingAgents repository today.** About 109k stars, v0.5.2 (Sep 2026), supports Anthropic models. README says it is designed for research, is not trading advice, and that two runs on the same ticker and date can differ. Popularity is not validation.
Source: https://github.com/TauricResearch/TradingAgents — FETCHED — high (star count as rendered by the fetch tool).

**F16. Independent long-horizon test (FINSABER, Li et al., 2025).** Re-tested open-source LLM trading agents (FinMem, FinAgent — not TradingAgents itself) over 2004-2024, 63-91 symbols, with commissions, against rule-based, ML and RL baselines. Reported LLM advantages deteriorated: FinMem negative alpha, FinAgent positive but statistically insignificant; buy-and-hold Sharpe 0.55-0.70 was consistently top-tier; LLM agents were too conservative in bull markets and lost heavily in bear markets.
Source: https://arxiv.org/abs/2505.07078 and https://arxiv.org/html/2505.07078v5 — FETCHED — high.

## What this means for the JARVIS design documents

**Supported**
- v2/v3 principle "agents may reason; hard risk, permission, data-integrity and order-validation rules are deterministic and cannot be overridden by an LLM" — strongly supported by F7-F9 (compounding errors, verification failures).
- v3 build step 6: "agents produce structured evidence; they do not directly send broker orders" — supported.
- v3 "Orchestrator: deterministic routing for money-critical steps" — supported; F8 shows centralised verification cuts error amplification (17.2x to 4.4x) and F9 favours predefined code paths.
- v3's own honesty about LangAlpha being a slow, high-token report generator, not a live architecture — consistent with F10/F11.
- v1 Layer D (LLM proposes hypotheses; backtest/validation decides) — this is the best LLM use in all three documents: offline, breadth-first, verifiable.

**Weakened**
- The headline framing of "18 agents". Reading the v3 "Suggested stack" column, only Bull/Bear is specified as an LLM; News is FinBERT/RAG; the supervisor is LangGraph. The other ~14 are already Python, statistics or services. Calling them agents invites building each as an LLM tool-loop, which F7-F11 say is costlier and less reliable. The document is better than its own vocabulary.
- "TradingAgents" as a research basis (v2 and v3 ref [2]). It supports the engineering pattern (structured outputs, decision logs) only. Its performance claims are a three-month, cost-free, un-ablated backtest (F14), and comparable agents failed a 20-year test (F16).
- "Bull/Bear agents ... expose weak assumptions rather than vote blindly" (v3). Same model, same evidence, assigned sides: per F2-F5 this is unlikely to beat one strong structured critique call, and per F1 can converge confidently on a wrong answer. Not contradicted outright (no finance-specific test exists), but unsupported.
- "Thesis confidence" as an input to the Confidence Calibrator (v3 section 2). If it derives from LLM debate output, it is an uncalibrated, non-deterministic number (F15: runs differ) entering a calibrated score. It needs its own out-of-sample evidence before it gets any weight.
- LangGraph "supervisor + specialist research workflows" as the "agent brain" on the live intraday path. F8 (-39% to -70% on sequential tasks), F10 (poor fit for real-time coordination) and the 4-15x token cost argue against any LLM supervisor in the tick-to-order loop. The worked examples are $100 accounts earning $0.27 per trade; any per-trade LLM debate costs a meaningful fraction of, or more than, that gain (cost figure depends on current model pricing — not checked here).

**Contradicted**
- Nothing in the docs is flatly contradicted, because the docs never claim a measured benefit from the agent count. The implicit claim "several small brains instead of one blind model" (v1 Layer C) is about statistical models, where ensembling is well-founded; it should not be read across to LLM agents.

## Reasoned classification of the 18 v3 agents

| # | v3 agent | Classification | Reason |
|---|---|---|---|
| 1 | Orchestrator / Supervisor | Deterministic state machine (code). No LLM. | The state machine OBSERVE..LEARN is fixed and known; F9: predefined code paths for well-defined tasks; F7: termination/step-repetition failures are the top MAS failure modes. |
| 2 | Goal & Capital Planner | Deterministic rules + optimiser. Optional LLM only to parse the user's free-text goal into a typed config and to explain the plan back. | Arithmetic and constraints; an LLM adds only a natural-language front end. |
| 3 | Opportunity Scanner | Deterministic/statistical. | Streaming screens over numeric features; latency- and cost-sensitive; runs continuously. |
| 4 | Data Trust | Deterministic (schemas, quorum, staleness checks). | Must be reproducible and testable; an LLM cannot be the integrity gate. |
| 5 | Market / Technical | Deterministic feature computation. | Pure numerics. LLMs reading indicator values add noise, not information. |
| 6 | Flow / Microstructure | Deterministic streaming features + stat models. | Sub-second numeric data; LLM latency and cost disqualify it. |
| 7 | News & Event | **LLM justified** (as a workflow step, not an autonomous agent). | Unstructured text to structured fields: event type, entity, novelty, relevance, direction. Fixed-schema extraction, cacheable, evaluable against labelled history. Dedup itself is embeddings/hashing, not LLM. |
| 8 | Fundamental / Macro | Hybrid. XBRL/FRED numbers and valuation are code; **LLM justified** for reading filings/transcripts (risk-factor changes, guidance) on a slow, offline cadence. | Matches the breadth-first, read-heavy profile where F8/F10 show gains (Finance-Agent +80.8% is exactly document analysis). This is also the one place a parallel sub-agent pattern is defensible. |
| 9 | Crypto | Deterministic. | Venue liquidity, cross-venue gaps, volatility are numeric. |
| 10 | Manipulation Surveillance | Rules + anomaly models. LLM only possibly for classifying social-media pump text (which is really part of #7). | Order-book pattern detection is statistical; must be fast and auditable. |
| 11 | Bull / Bear | **LLM, but redesign.** Replace two-agent debate with a single structured "pre-mortem / red-team" call (or N independent samples aggregated), preferably using a different model from the one that wrote the thesis; treat output as a checklist of falsifiable conditions, not a confidence number, until proven otherwise. | F2-F5: voting/self-consistency captures most of the gain; heterogeneity is the only robust improver; F6 shows debate helps under information asymmetry, which this is not. |
| 12 | Model Ensemble | Statistical/ML. | By definition. |
| 13 | Confidence Calibrator | Statistical (isotonic/Platt, reliability curves). | Calibration is a statistical procedure over out-of-sample outcomes. |
| 14 | Strategy / Portfolio | Deterministic decision engine + optimiser. | Expected value after costs is arithmetic; the LLM must not pick LONG/SHORT/FLAT. |
| 15 | Capital Governor / Risk | Deterministic. | The docs already say so; keep it. |
| 16 | Execution | Deterministic idempotent service. | Order safety. |
| 17 | Position Manager | Deterministic exits on streaming state. | v3 already says "deterministic exits". |
| 18 | Ledger / Review | Ledger is a database. **LLM justified** for the narrative layer: trade emails, daily summary, post-trade review drafts — reading from the ledger, never writing decisions. | Summarisation of structured records is a low-risk, high-value LLM use; attribution numbers themselves are computed in code. |

Plus one LLM role the v3 table omits but v1 has (Layer D, Strategy Lab): **offline research/hypothesis generation**, where a true agentic or even multi-agent loop is appropriate because it is breadth-first, not time-critical, and every output is checked by a backtest.

Net: roughly 13 of 18 are code/statistics; LLM roles are News/Event extraction, Fundamental document reading, a red-team critique, narrative reporting, and offline research. All are off the order path.

## Recommended changes

1. Rename the architecture: "deterministic pipeline of services + a small number of LLM workflow steps". Reserve the word "agent" for components where an LLM chooses its own next action; today that is at most the offline Strategy Lab and filing research.
2. Remove the LLM from the supervisor role. Implement the v3 state machine as code. LangGraph is acceptable as a workflow engine for the LLM steps but is not needed as the system's brain.
3. Replace Bull/Bear debate with a single structured red-team step; if multiple opinions are wanted, use independent samples and aggregate (vote), and use a different model family or at least a different model tier for the critic.
4. Make every LLM output a typed, versioned feature (schema-validated, timestamped, prompt/model version recorded) that enters the statistical models and calibrator like any other feature. It gets weight only if it improves out-of-sample calibration in walk-forward tests.
5. Add an explicit ablation gate to the build order: before any LLM step goes live, run the pipeline with and without it over the same paper/shadow period and keep it only if the after-cost metric improves. Apply the same test to "LLM thesis confidence".
6. Keep LLM calls off the intraday latency path. Run them on events (new filing, new headline cluster) and cache results; the scanner and position manager consume cached structured outputs.
7. Set a per-day LLM budget and log token cost per candidate and per trade in the ledger, so cost-per-decision is visible next to expected edge.
8. Downgrade TradingAgents in the "Research basis" to "engineering pattern reference; performance claims not relied upon", and add FINSABER-style long-horizon, cost-inclusive evaluation as the standard for any LLM-derived signal.
9. Build order change: move v3 step 6 ("Add LangGraph Orchestrator and specialist agents") after step 8 (paper trading of the non-LLM pipeline), so there is a working baseline to ablate against.

## Open uncertainties

- No study I found tests bull/bear-style debate on out-of-sample financial forecasting with costs and a proper ablation. The recommendation against it rests on general-reasoning benchmarks plus the absence of positive finance evidence, not on a direct negative result.
- Most debate studies used older or small models (GPT-3.5, 7-32B open models). Whether findings hold for current frontier Claude models is not established; F8's "capability saturation" result suggests stronger single agents make coordination less, not more, valuable, but that is one preprint.
- F8 and F10 both show large multi-agent gains on parallel research tasks; the boundary between "decomposable analysis" and "sequential decision" in JARVIS's fundamental-research path would need to be tested empirically.
- Exact per-trade LLM cost was not computed (needs current Claude pricing and a token estimate; another topic owner should check live pricing).
- OpenAI's guide was not verifiable in this session (PDF unparseable).
- Zhang et al. (F4) exact win/loss and token multipliers were not extracted; "Debate or Vote" author list not verified.
- MAST percentages vary slightly between paper versions; category shares quoted are from the HTML version fetched today.
- TradingAgents has had many releases since the paper; I did not check whether later versions published longer, cost-inclusive backtests.

## Source list

Fetched this session:
- https://arxiv.org/abs/2305.14325 and https://ar5iv.labs.arxiv.org/html/2305.14325 — Du et al., multi-agent debate
- https://arxiv.org/abs/2311.17371 and https://arxiv.org/html/2311.17371 — Smit et al., "Should we be going MAD?"
- https://arxiv.org/abs/2402.18272 — Wang et al., "Rethinking the Bounds of LLM Reasoning"
- https://arxiv.org/abs/2502.08788 — Zhang et al., "Stop Overvaluing Multi-Agent Debate"
- https://arxiv.org/html/2508.17536v2 — "Debate or Vote" (NeurIPS 2025)
- https://arxiv.org/abs/2402.06782 — Khan et al., debate with persuasive LLMs
- https://arxiv.org/abs/2503.13657 and https://arxiv.org/html/2503.13657 — Cemri et al., MAST
- https://arxiv.org/abs/2512.08296 and https://arxiv.org/html/2512.08296 — Kim et al., scaling agent systems
- https://www.anthropic.com/engineering/building-effective-agents
- https://www.anthropic.com/engineering/multi-agent-research-system
- https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them
- https://cognition.com/blog/dont-build-multi-agents
- https://arxiv.org/html/2412.20138 — TradingAgents paper
- https://github.com/TauricResearch/TradingAgents
- https://arxiv.org/abs/2505.07078 and https://arxiv.org/html/2505.07078v5 — FINSABER

Not verified (recalled only):
- https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf

Note on method: page contents were read through a fetch tool that summarises pages with a small model; numbers quoted were taken from the HTML full-text versions where available, but a human spot-check of the key tables (MAST percentages, Kim et al. overhead figures, TradingAgents Table) is advisable before they are cited in a final design document.

## Independent verification (2026-10-01)

Done by a separate fact-checking agent that re-opened the sources. Same limitation as the brief: pages were read through a fetch tool that summarises with a small model, so the numbers below are "re-extracted and consistent across two independent fetches", not human-checked against the PDFs.

Overall: the brief's direction holds. Thirteen claims were checked; nine are confirmed as stated, three need correction (one number is wrong, one is cherry-picked, one is misquoted), and one could not be verified. Newer evidence found today strengthens the brief's main conclusion about trading agents rather than weakening it.

### Confirmed

- **F14 TradingAgents paper.** Backtest 1 Jan to 29 Mar 2024; AAPL 26.62% / Sharpe 8.21, GOOGL 24.36% / 6.39, AMZN 23.21% / 5.60; baselines are buy-and-hold, MACD, KDJ+RSI, ZMR, SMA; no cost model; no debate ablation; the authors say the Sharpe exceeds their expected range. https://arxiv.org/html/2412.20138
- **F8 Kim et al.** 260 configurations, 6 benchmarks, 5 architectures; mean effect -0.3% (95% CI -58.7% to +77.2%); PlanCraft -39.1% to -70.0%; Finance-Agent centralised +80.8% (0.349 to 0.631); error amplification 17.2x independent vs 4.4x centralised; token overhead 58% / 263% / 285% / 515%; the 45% threshold. Current version is v3, 8 Apr 2026; still a preprint. https://arxiv.org/html/2512.08296
- **F7 MAST.** 1,642 traces, 7 frameworks, kappa 0.88, 14 modes in 3 categories (43.9% / 32.35% / 23.75%), every per-mode percentage quoted in the brief, 41% to 86.7% failure rates, ChatDev +9.4% and +15.6%. Version v3, 26 Oct 2025. https://arxiv.org/html/2503.13657
- **F10 Anthropic research system.** "about 4x" and "about 15x" tokens; 90.2% (Opus 4 lead with Sonnet 4 subagents vs single Opus 4, internal eval); token usage alone explains 80% of BrowseComp variance (three factors explain 95%); poor fit for shared-context and highly inter-dependent work. https://www.anthropic.com/engineering/multi-agent-research-system
- **F9 Building effective agents.** Published 19 Dec 2024; definitions, "simplest solution" advice and the five patterns are as stated. https://www.anthropic.com/engineering/building-effective-agents
- **F5 Debate or Vote.** Authors are Hyeong Kyu Choi, Xiaojin Zhu, Sharon Li (UW-Madison), NeurIPS 2025; 7 benchmarks, 5 agents; Qwen2.5-7B average 76.91% voting vs 73.77% decentralised debate (single agent 72.05%); martingale result as stated. The "?" on the author name can be removed. https://arxiv.org/html/2508.17536v2 and https://neurips.cc/virtual/2025/poster/116557
- **F4 Zhang et al.** 5 debate methods, 9 benchmarks, 4 models; often fails to beat CoT and self-consistency at higher compute; heterogeneity helps. Abstract-level only, as the brief says. https://arxiv.org/abs/2502.08788
- **F6 Khan et al.** 76% vs 48% (models), 88% vs 60% (humans). https://arxiv.org/abs/2402.06782
- **F3 Wang et al.** and **F15 TradingAgents repo** (109.4k stars, v0.5.2 Sep 2026, Anthropic supported, research-only and non-determinism disclaimers; README also says backtest results are not guaranteed to match any published figure). https://arxiv.org/abs/2402.18272 and https://github.com/TauricResearch/TradingAgents

### Corrected

- **F16 FINSABER, buy-and-hold Sharpe "0.55-0.70".** That range does not appear in the paper. Buy-and-hold Sharpe over 2004-2024 on the four selected stocks is 0.46 to 0.63 (MSFT 0.461, AMZN 0.551, NFLX 0.622, TSLA 0.630); in the composite, bias-mitigated setup it is 0.315 to 0.703 depending on the selection rule. Use: "buy-and-hold Sharpe roughly 0.3 to 0.7 and it beat both LLM agents in the composite setup (FinMem -0.29 to 0.03, FinAgent -0.08 to 0.24)".
- **F16, "FinAgent positive but statistically insignificant".** Only half right. FinAgent alpha is +6.57% (p = 0.345) under momentum selection and -0.20% (p = 0.368) under volatility selection; FinMem is -1.34% and -1.04%. All p-values exceed 0.34. Use: "neither agent produces statistically significant alpha".
- **F16, "lost heavily in bear markets".** The paper's wording is "too conservative in bull markets and too aggressive in bear markets" (bull Sharpe: FinAgent 0.12, FinMem -0.19, buy-and-hold 0.61; bear: -0.38, -0.97, -0.28). Backbones were GPT-4o / GPT-4o-mini, so this is not a test of current frontier models. Now published at KDD '26. https://arxiv.org/html/2505.07078v5
- **F1, "about half the gain is ensembling".** True for GSM8K only (77.0 single, 81.0 majority, 85.0 debate). On arithmetic in the same table, majority voting gave 69.0 against 67.0 single and 81.8 debate, i.e. voting captured almost none of the gain. The paper reports no majority row for MMLU or biographies. The "voting does the work" conclusion should rest on F4 and F5, not on Du et al. https://ar5iv.labs.arxiv.org/html/2305.14325
- **F11, "an agent struggling with 20+ tools".** The post says "15-20+ tools". The 3-10x token figure, the 23 Jan 2026 date and the three justified cases are correct. https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them
- **F2 framing (minor).** Smit et al. conclude the underperformance comes mainly from hyperparameter sensitivity and that tuned debate (agreement modulation, about +15% for Multi-Persona on the USMLE subset) can match or exceed Medprompt. The brief's "does not reliably outperform" is accurate, but the paper is less negative than the brief implies. https://arxiv.org/html/2311.17371

### Could not verify

- **F13 OpenAI practical guide.** The PDF downloads but cannot be parsed here either. Do not cite it; nothing in the design depends on it.
- **F4 exact win/loss rates and token multipliers** (abstract only).
- **Which systems sit at the 41% and 86.7% ends of the MAST range**, and with which models.
- **Miyazaki et al. details** (see below): only the abstract was readable.

### What the brief missed

1. **A direct, cost-inclusive re-test of TradingAgents now exists.** "The Alpha Illusion" (Ye et al., May 2026 preprint) reproduced TradingAgents for Jan 2025 to Jan 2026 on five equities: portfolio Sharpe 0.43 gross, 0.22 after commission, spread, token cost and market impact. It also cites temporal-contamination results ("Profit Mirage", Li et al. 2025): FinMem's return falls about 72% and QuantAgent's Sharpe about 51% once the test window passes the model's training cutoff. This closes the brief's open uncertainty on later TradingAgents evidence, in the brief's favour. https://arxiv.org/html/2605.16895
2. **Training-data leakage is a separate failure the brief never names.** Any backtest of an LLM step on dates before the model's training cutoff is contaminated. The ablation gate in recommendation 5 must therefore run forward in paper/shadow mode, or only on dates after the cutoff of the exact model used. Historical walk-forward tests of LLM features are not valid evidence.
3. **Search-intensity bias in the offline Strategy Lab.** Gençay (Aug 2026 preprint) tested LLM-discovered strategies on 453 US stocks and 39 ETFs with costs and trial-count deflation: every LLM-discovered strategy was rejected while passive benchmarks passed. The brief calls Layer D "the best LLM use"; it remains the safest, but its outputs need a deflated-Sharpe / multiple-testing correction, not just "a backtest decides". https://arxiv.org/abs/2608.27734
4. **A counter-example exists.** Miyazaki, Kawahara, Roberts, Zohren (Feb 2026) report that a multi-agent trading system with fine-grained task decomposition significantly improves risk-adjusted returns over coarse-grained designs. Period, costs and ablations were not readable, so its weight is unknown, but the brief's "no finance-specific evidence" statement should become "little and unverified". https://arxiv.org/abs/2602.23330
5. **Live Claude pricing (the brief left this open).** Per million tokens, input / output: Haiku 4.5 $1 / $5; Sonnet 5 and 5.5 $2 / $10; Opus 5 $5 / $25; Opus 5.5 $4 / $20; Fable 5.1 $10 / $50. Batch API is 50% off; cache reads are 0.1x input (less on the newest models). Models from 4.7 onward use a tokenizer producing about 30% more tokens. Illustrative arithmetic (my assumption of 20k input + 3k output tokens for one small debate-and-judge exchange): about $0.035 on Haiku 4.5, $0.07 on Sonnet 5, $0.175 on Opus 5. Against the documents' $0.27 gain on a $100 trade, that is 13% to 65% of the gain, per candidate evaluated, not per trade taken. At the owner's $1,000 to $10,000 the same call is 0.1% to 6% of a proportionally scaled gain, so the cost objection is strong at $100 and much weaker at $10,000; the "close to zero" monthly budget is the binding constraint. https://platform.claude.com/docs/en/about-claude/pricing
6. **The heterogeneity advice conflicts with owner constraints.** The owner wants Claude agents. A different Claude tier is not a different model family, and F4's heterogeneity result was measured inside debate frameworks, not for a single critic call. Treat "use a different model for the critic" as untested, not as an evidence-backed recommendation.
7. **Statistical power of the ablation gate.** With a small account and few trades, a with/without comparison over one paper period will not detect a realistic effect. The gate should be scored on calibration of many candidate-level predictions (Brier score / log loss over hundreds of decisions), not on realised P&L.
8. **F8's +80.8% is a relative gain from a low base** (0.349 to 0.631) at about 3.9x the tokens, on Finance-Agent, with models of that study. It supports parallel document research for agent #8, but the same paper says gains turn negative once a single agent passes about 45%, and current models may already be past that on filing analysis.
9. **F10's 90.2% used Opus 4 and Sonnet 4**, both now retired on the first-party API. The pattern guidance stands; the number should not be quoted as current.

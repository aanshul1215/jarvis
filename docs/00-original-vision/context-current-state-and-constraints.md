# JARVIS — shared context for all agents (written 2026-10-01)

## A. What exists today (JARVIS v1, Hugging Face Space, built July 2025)

A Gradio chatbot for ONE stock (TSLA), daily bars, frozen data 2025-01-02..2025-07-01 (~123 rows).
- Data pipeline (Colab, not in repo): price + summarised news with sentiment/decay; 1,324 Reddit/Electrek posts with
  engagement-weighted sentiment; SEC 10-K/10-Q rows with FinBERT tone + Loughran-McDonald ratios + event-study CAR;
  technicals (RV20, RSI-14, MACD, SMA/EMA, Bollinger z, ATR-14), VIX/QQQ/NVDA returns, day-of-week dummies.
- Three XGBoost models on the same 47 features: next-day return regressor, up/down classifier, big-move classifier.
  SHAP explanations and 21-day backtest equity curves saved.
- Assistant: keyword intent matching -> gathers the feature row + runs models -> fills a prompt template ->
  gpt-3.5-turbo narrates bullets. No trading, no execution, no live data.
- Known defects: (1) target leakage — feature `return_pct_t1` IS the next-day return, so test metrics
  (Spearman 0.999, accuracy 1.0, +61% in one month) are meaningless; (2) SHAP drivers never reach the LLM;
  (3) SEC/social values reach the LLM as zero due to column-name mismatches; (4) several intents are placeholders;
  (5) an API key was committed in source; (6) one global session shared by all users.
- Honest salvage value: the *ideas* (news/SEC/social ingestion, FinBERT sentiment, event-study features, technical
  features, SHAP explanation, LLM narration) and some ingestion code. No validated predictive model exists.
- Note: the owner's design documents describe the "current foundation" as also having Parquet + Chroma RAG memory,
  duplicate removal, ticker mapping, macro collection. That is NOT in the published Space; treat it as unverified.

## B. What the owner wants to build ("JARVIS Ultimate Financial Agent")

Three design documents (full text in this same folder):
- JARVIS_Ultimate_Financial_Agent_Architecture.txt  (v1: 9 layers A–I, decision rule, BTC worked example)
- JARVIS_Ultimate_Financial_Agent_v2.txt            (v2: agent teams, operating states, protections, ETH example)
- JARVIS_Ultimate_Financial_Agent_Workflow_v3.txt   (v3: 18 agents, state machine, local stack, 10-step build order)

Essence: an always-on, local-first (Docker Compose on a dedicated laptop), end-to-end autonomous system for
equities + crypto, long/short/flat, multi-horizon (intraday to long-term). Pipeline:
user goal & capital -> goal/capital planner -> always-on opportunity scanner -> data trust gate -> market state
engine -> specialist agents (technical, flow/microstructure, news/event, fundamental/macro, crypto, manipulation
surveillance, bull/bear) -> stat/ML model ensemble (jump, return distribution, volatility, regime HMM, GARCH,
anomaly, relative value, news impact) -> confidence calibrator (signal/data/model/thesis/execution -> overall)
-> strategy/portfolio decision -> deterministic hard capital governor & risk gate (no LLM override) -> execution
(paper first, then small live) -> live position manager that recomputes thesis/confidence and exits early ->
professional trade ledger -> evaluation & learning -> dashboard / email alerts / daily summary for "investors".

Stated principles: never chase a return target; FLAT is valid; agents reason but deterministic rules hold the
money; build on current JARVIS as the "Information Intelligence" layer; paper -> shadow -> small live by gates.
Proposed stack: LangGraph, Redis Streams/NATS, Redis, PostgreSQL+TimescaleDB, Parquet+MinIO, XGBoost/LightGBM/
PyTorch, MLflow, FastAPI + React/Next.js, Grafana, OpenTelemetry+Prometheus, Alpaca + Coinbase feeds.
Worked examples use a $100 account trading BTC/ETH intraday on order-flow signals, netting +$0.27.

## C. Owner constraints (answered by the owner on 2026-10-01 — treat as binding)
- Country of residence: United States.
- Live capital after paper trading: $1,000 to $10,000.
- Whose money: only the owner's own. No outside investors (the "investor view" is a personal dashboard).
- Monthly budget for data feeds + LLM API calls: close to zero (free data tiers, very sparing LLM use).
- US state: Texas. Hardware: Windows 11 laptop with 8 GB RAM (Docker Desktop is not viable; stack must be very lean).
- Team size: solo developer + AI agents.
- The owner is open to changing the design where evidence justifies it, but changes must be well-reasoned.
- The owner intends the agents to be Claude agents.

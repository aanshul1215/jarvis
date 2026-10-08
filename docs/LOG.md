# Project log

One dated entry per meaningful step. Newest at the bottom. Append; do not rewrite earlier entries.

## 2025-07-30 — JARVIS v1 (legacy)

- TSLA-only prototype published as a Hugging Face Space (Gradio chatbot; three XGBoost models; gpt-3.5-turbo narration).
- Later found: target leakage (`return_pct_t1` is the next-day return), SHAP drivers never reach the LLM, SEC/social
  features reach the LLM as zero, placeholder intents, a committed API key, one global session. See
  `docs/00-original-vision/context-current-state-and-constraints.md`.

## 2026-10-01 — Redesign started

- Owner's three design documents (v1 architecture, v2 revised architecture, v3 workflow) read and summarised.
- Owner constraints recorded: US (Texas), $1,000–$10,000 own money, near-zero monthly budget, Windows 11 / 8 GB RAM,
  Claude agents.
- Stage 1: 17 research briefs written against primary sources and independently fact-checked; 6 gap-fill briefs
  added; gap analysis written (`docs/01-research/`).
- Key findings: no evidence of an LLM-trader edge net of costs; intraday, order-flow and crypto-on-exchange
  strategies uneconomic at this capital; pattern-day-trader rule repealed June 2026; free data supports
  daily-to-monthly horizons only; a 14-service infrastructure stack is premature for one process.
- Stage 2: five competing architectures (vision-faithful, evidence-minimal, agents-as-quant-team, failure-first,
  staged platform), nine critics, synthesis on the failure-first proposal, red-team, final revision
  (`docs/02-design-tournament/FINAL-design.md`).

## 2026-10-02 — Paper-grounded review and final architecture

- Ten specialist reviews against research papers; 76 change proposals; four-seat panel vote; chief-architect
  rewrite; two verification passes; all eleven must-fix findings applied (`docs/03-review/`).
- Result: `ARCHITECTURE.md`. Metered spend $0; v1 build about 37–49 dev-days; real money following the plan by
  hand at about month 2.5–4; trend strategy in shadow only; eight Claude agent definitions in six roles.
- Not approved by the owner yet. Open warnings listed in `README.md`.

## 2026-10-07 — Repository created

- GitHub repository `jarvis` created; vision documents, research, design tournament, review and redacted legacy v1
  code committed. Collaboration workflow in `CONTRIBUTING.md`.
- Next: discussion of the open warnings; then milestone M0.

## 2026-10-08 — Owner-directed autonomous design proposal

- Owner clarified the product goal: retain the original Observe/Understand/Forecast/Decide/Execute/Learn workflow
  and JARVIS's local news, social and SEC information features while scaling from TSLA to liquid equities and spot
  BTC/ETH. Claude and Codex are development tools, not live trading decision makers.
- Chose hours-to-days opportunities, a broad cheap scan with a deep shortlist, near-zero metered spend, bounded
  automatic model promotion, and local Windows operation with explicit recovery after missed uptime.
- Added `AUTONOMOUS_ARCHITECTURE.md` and `docs/04-autonomous-design/` for the new proposal, diagrams, role mapping,
  decisions and milestone gates. The October 2 `ARCHITECTURE.md` remains as historical evidence. No autonomous
  trading implementation or live account connection has been created.

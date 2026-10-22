---
name: jarvis-study
description: >-
  Run a Jarvis research study the way every study here is run. The rules are written down before any result;
  development, confirmation and holdout periods are each used once; costs are realistic; an adversarial red
  team reviews it; and the write-up in docs/ records the result whether it passes or fails. Use when the
  owner asks to test, research, backtest, replicate or evaluate a strategy, signal, model, paper or GitHub
  repository ("does X work", "test this idea", "replicate this paper", "will this repo help us").
argument-hint: "[the idea, paper or repository to test]"
---

# jarvis-study

A backtest is only evidence if its rules were fixed before its result was seen. Everything below protects that. The owner's goal is at least +15% a month, which needs an after-cost Sharpe of roughly 2.1 or more plus leverage. Judge every result against that honestly, and never round a failure up.

## Non-negotiable rules

- **Pre-register first.** Write `pre_registration.txt` (use `pre_registration_template.md` in this folder) before computing any return, and record its SHA-256.
  - After that, keep an append-only `deviations.txt`, each entry timestamped and written before seeing the affected result.
  - A change of rule after a result is a new trial, not a fix.
- **Splits, each used once.** Equities: development 2016-02-01 → 2021-12-31; confirmation 2022–2023; holdout 2024 → the latest data.
  - Run the holdout once, and only for designs that passed development and confirmation.
  - For a published strategy, its sample overlap is a replication; only the post-publication period is out of sample.
  - Load data with the date filter applied, and assert it.
- **Count every trial,** including earlier studies of the same family (see `docs/10-shortterm/`, `docs/12-options/`, `docs/13-aggressive/`). Report the deflated Sharpe and month-clustered t-statistics.
- **Realistic costs:** a base case, double the base, and zero.
  - Auction orders (market-on-open/close) cost far less than crossing the spread.
  - Stop-triggered fills slip.
  - Small or volatile stocks cost more.
- **No survivorship or look-ahead:**
  - Use point-in-time universes (`shortterm/universe_top300.json`, `universe_top1500.json`).
  - `KNOWN_FAILURES` are valued at zero after their last listed day.
  - Signals use only what was available at decision time.
- **Leak alarm:** an annualised Sharpe above 3, or a win rate above 75% over 30+ trades, is treated as a bug until proven otherwise.
- **Data:**
  - Alpaca API data is allowed: throttle to ≤150 requests a minute, pause 08:55–09:40 US Central on weekdays, take keys from the environment and never print them.
  - Any other download (models, datasets, papers as files) needs the owner's explicit approval, with name, source, size and licence.
  - Market data and FRED price series stay local, never in the public repository.

## Steps

1. **Frame:**
   - the owner's question, in their words;
   - the hypothesis and why it could work (who loses money to it, and why it has not been competed away);
   - the evidence (mark anything not verified as RECALLED);
   - what result would falsify it;
   - prior tests of the same idea in `docs/` and memory.
2. **Design:** universe, signal, timing (when the decision is made and how the order executes), sizing, costs, metrics, and the decision rule. Fill in the template.
3. **Run it as a separate background agent.** Give the agent the full rules:
   - work in `%TEMP%\claude\<study>\`; do not modify the repo;
   - use the venv python `.venv\Scripts\python.exe`;
   - no pip installs;
   - do not kill other Python processes, and keep threads ≤ 3;
   - no downloads beyond what is approved;
   - sanity checks: a hand-traced example, an independent re-implementation of the core, and a look-ahead truncation test.

   Never predict or report its results before it finishes.
4. **Red team:** a second agent attacks the result using `red_team_checklist.md`. Its corrections are recorded even when they reverse the conclusion.
5. **Write-up:** `docs/<NN-area>/<NAME>_STUDY.md`, containing:
   - the owner request;
   - the evidence;
   - the registered design;
   - results (CAGR, Sharpe above T-bills and max drawdown for each period, plus the cost cases);
   - the decision by the rule;
   - caveats and red-team findings;
   - a plain-English summary.

   Commit it with the result in the message. The repository is public: no secrets, no data files.
6. **Tell the owner,** in plain language:
   - the one number that matters;
   - what it means for the +15%-a-month goal;
   - what next.

   A passing study earns a paper desk only after the owner decides. Live money only with the owner.

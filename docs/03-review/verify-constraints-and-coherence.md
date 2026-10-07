# Verifier: constraints and coherence (JARVIS-final-architecture.md)

Scope: binding owner constraints (near-zero metered budget, 8 GB RAM, Texas, $1k-$10k, solo, Claude agents) and internal coherence.

## Constraint check

- **Metered budget.** Lines sum to $0.00 of metered spend. No API key, Alpaca/FRED/EDGAR/Healthchecks/GitHub private repo are free tiers. PASS, with two blemishes:
  - The table lists "Laptop power $2.64" but the total says $0.00. Mark the row "$0 incremental" or delete it.
  - Unpriced items sit outside the $0 claim: the Alpaca IRA fee ("a $10 fee is 1% of $1,000") and an optional tax consult. The doc says the consult is "required before any live taxable S-A", but taxable S-A is never allowed (section 6). That sentence is stale.
- **8 GB RAM.** No resident service, flat files, DuckDB read-only. PASS. But the Narrator needs Claude Desktop open and the laptop awake every Sunday 17:00. That is a resident process, contrary to "no RAM is held between runs". O3 measures it, which is the right fix.
- **Texas.** No state-specific logic beyond the no-income-tax note (flagged medium confidence) and crypto (off). PASS.
- **$1k-$10k.** Sizing, $20 minimum and band floor are workable. At $1,000 a 25% S-A satellite is $250 and an IRA fee could erase it; the doc already says so. PASS.
- **Solo.** Owner must read gate, order and config diffs written by the Builder. Acceptable, but see should-fix 5.
- **Claude agents.** All eight definitions are `.claude/agents` files, no API. PASS.
- **Agent table vs workflow.** Every agent named in sections 3 and 5 (Builder, Reviewer, Lab incl. Spec Clerk and Replication Analyst, Narrator, Ledger Analyst, Change-Watch, Incident Triage, Reader) is in the table, and the table has nothing the workflow omits. Counts (6 roles / 8 definitions) reconcile. Build-phase gap: no milestone creates the Builder or Reader definition, and `jarvis whatif` (which the Ledger Analyst needs) is in no milestone (see must-fix 4).
- **Arithmetic.** M0-M4 effort 3-4 + 8-10 + 6-8 + 7-10 + 12-16 = 36-48; with M5 56-76. Timeline vs hours agrees. Stated dollar effects (-$14 to -$18; fees $0.88-$8.80; dial b = 0.40 example) are right.

## Must fix

1. **Harness-trust gate is not passable as written, and M4 depends on it.**
   - The Replication Analyst must reproduce Faber's text claims and Antonacci's medians (section 5d, section 8). Those are 1973+ long-history results.
   - Section 9 and D6 delete the 1973 proxy ladder, and the harness only has 2004+ (or 2016+ if no pre-2016 source). "Within tolerance" has no numbers.
   - Smallest fix: restrict replication to claims checkable on the ETF-era window (turnover about 70%, 3-4 round trips a year, sign of the drawdown change). Write numeric tolerances. Optionally add Ken French or Shiller free monthly data for the long-history check. Drop the Antonacci-median claim from the gate otherwise.
2. **"Agents may create HALT" contradicts "no agent writes outside agent-out/<agent>/".** Section 5f vs section 4 shared rules. Either an agent can write outside its folder or it cannot.
   - Smallest fix: an agent writes `agent-out/<agent>/REQUEST_HALT`; the daily code job promotes it to HALT and emails. Or delete "agents may create HALT".
3. **Dividend and interest cash would trip SAFE every month.**
   - Reconcile treats any unregistered cash as a SAFE cause (flow a step 3, step 10, section 7). SGOV pays monthly, VTI/VEA/IEF/VNQ pay dividends, and the broker CSV shows them as cash.
   - Smallest fix: reconcile classifies broker activity types DIV/INT/FEE as expected non-owner cash. Only deposits and withdrawals need `jarvis cash-event`. Dividends feed the contribution waterfall as new cash. Add this to the M3 exit test.
4. **Phase prerequisites run backwards in M1-M2.**
   - M1 ships S0-RM shadow and M2 memos report `vs_S0RM`, but S0-RM's b* is "fitted once in M4" from S-A's backtest volatility.
   - The M2 memo schema carries `behaviour{}`, `rejections[]`, `risk_state`, which are built in M3. `jarvis whatif` for `/whatif` is in no milestone.
   - M2's exit test ("2 memos validated") would pass on empty fields, and then the schema, validator and advice-leak set are reworked in M3.
   - Smallest fix: use a placeholder b* (equal to S0(b)'s b, labelled) until M4. Mark the M2 memo fields optional with explicit "not yet available" values. Move `/whatif` and `jarvis whatif` to M3 or M4, or add them to M2's task list.
5. **`llm_origin` rule is self-contradictory.** The Lab table says the Lab must never mark an `llm_origin` spec live-eligible. Flow (d) step 5 gives an `llm_origin` spec a path to live money ("≥12 monthly forward decisions plus the owner's G0 before any live money").
   - Smallest fix: pick one. Recommended: an `llm_origin` spec can reach shadow only. Live eligibility requires the owner to re-register it as an owner-origin spec after the forward period.
6. **First-real-money path rests on an unprobed order mechanism.** M3 (first live dollars) has the owner place orders "in the Alpaca app", yet:
   - The order email lists "dollar amount" plus "limit price". To my knowledge Alpaca fractional dollar-notional orders are market-only and limit orders need quantity. The M0 fractional probe does not test notional with limit.
   - M0 has no probe that a manual order-entry UI (and cancel-all/close for the kill path) exists for the live account.
   - Quotes: the limit is computed from an IEX quote at `jarvis month` time and "no older than 60 s", but the owner places orders later.
   - Smallest fix: add M0 probes (manual entry UI on live account; notional+limit; fractional limit by quantity). Print quantity-based limits with an instruction to re-run if more than 15 minutes pass. If no UI exists, a read-only key is not available either, so the "no live key anywhere" rule needs a stated exception.
7. **S-A memo gate tests the wrong quantity for the only live path.** S-A may go live only in a tax-deferred account (section 6), but the M4 memo and the Sunset rule gate on after-tax CAGR (section 8). In an IRA there is no tax drag.
   - Smallest fix: gate on the metric that matches the account where it would run. Pre-tax for the IRA branch (report after-tax for information). Apply the same to Sunset.

## Should fix

1. **G4 (S-A live) cannot be measured without the optional executor.** It needs "mean one-way cost ≤10 bps" and fresh-quote fills, but `jarvis.costs` exists only from M5 and hand-placed orders record no arrival quote. Fix: store the quote used in the order email and compute slippage in `jarvis adopt`, or state that S-A live requires M5.
2. **Wash-sale rule only looks backward.** Monthly contributions buy the most underweight ETF, which can repurchase a just-sold-at-loss ticker within 30 days after the sale. Fix: after any taxable loss sale, the combiner blocks buying that or any mapped ticker for 31 days; count DRIP and contribution buys in the lookback.
3. **LLM-to-order inventory is incomplete.** The doc says no LLM output decides an order, which holds for runtime output. The channels that do reach orders are:
   - Builder-authored code and config;
   - `draft_corporate_action` (Incident Triage), which feeds the price series and the SMA signal. It is checked only by a 0.5% reconciliation fit plus an owner commit, and its inputs include untrusted vendor text;
   - Lab specs.
   Fix: list these in section 4 as the only LLM-to-order paths, with controls. Require the corporate action to match a second independent source (the vendor corporate-actions feed) as well as the fit.
4. **Narrator `actions[]` and `questions_for_owner[]` are free text next to the order list.** Fix: `actions[]` is code-rendered enum ids; the denylist applies to the questions only. Pin the Narrator model id in the task, and rerun the advice-leak set when the pin changes (a "Sonnet-class" alias can move silently).
5. **Control enforcement is by convention.**
   - "Reviewer automatically on risky diffs" has no trigger, and the Builder can skip it. Fix: `jarvis release` refuses unless a Reviewer file whose hash matches the diff exists.
   - A loosening commit with `effective_after` in the past defeats the 72 h rule unless code detects loosening. Fix: `jarvis release` diffs `risk.yaml` against the prior release and sets `effective_after` itself.
   - The Reviewer "sanity bar" has no action on failure. Fix: if fewer than 4 of 8 seeded defects are caught, the Reviewer becomes a checklist the owner uses.
6. **Plan-usage assumptions are not tied to a baseline.**
   - The plan tier is unknown, and the owner has already hit a limit.
   - The 36-48 dev-day calendar assumes zero limit stalls.
   - The Narrator estimate (about 70k input a month) ignores fixed session overhead and up to 3 passes a week; expect several times higher.
   - The degrade rule drops the Reader, then the Narrator, but the Builder is the consumer that trips the limit.
   - Fix: record the tier in M0; add a 1.3-1.5x calendar buffer to the stop-rule dates or count calendar stalls in the stop rule; judge by the measured `ops/plan_usage.csv` before M3.
7. **M3 is overloaded for the first-money milestone** (7-10 days: month, combine, gate, adopt, cash-event, wash-sale, Behaviour Ledger, Healthchecks B, incident bundle plus Triage, page-hash plus Change-Watch), against a hard stop at month 3.5. Fix: move Incident Triage and Change-Watch to after the first real month-end. Also state how the first deployment of cash into an empty account is run, and that the first real month-end is a calendar event that can add up to a month of wait.
8. **Month-4 adherence trigger is statistically empty.** By month 4 there are 1-2 decisions of about 6 orders each, so "adherence below 95%" is hit by a single deviation. Fix: trigger on "any costly deviation or owner choice", with the percentage reported only from 4 or more decisions.
9. **Pre-2016 ETF-era data source is open (O6) and has no fallback.** Alpaca history starts about 2016. Fix: pre-state that if no source is licensed by M4 day 2, the memo is declared inconclusive and S-A stays shadow.
10. **Missing failure behaviours.**
    - Flow (a) steps 5-6 and flow (b) step 4: uncaught code error means `/fail` ping, incident bundle, and no partial order list.
    - Flow (b): a total Alpaca or FRED outage is not described.
    - Flow (a) step 3: the owner must first download the activity CSV, which is not shown as an owner action.
    - Flow (b) step 1: HALT should not stop data ingest and shadow NAV; check HALT only before the recommend/order steps.
    - Healthchecks B cannot express "trading day 8"; use a calendar-day schedule with grace.
11. **Meaningfulness test cannot be passed by event-driven agents.** "Ships nothing for two months is reviewed for removal" applies to Incident Triage and Change-Watch, which run a few times a year. Fix: exempt event-driven agents; their test is "no unhandled trigger".
12. **Anthropic terms provisions 7 and 9 have no stop path.** O4 is read by the owner but if provision 9 reads as barring reliance for trading decisions, or provision 7 bars the scheduler, only the Narrator has a fallback. Fix: add a one-line decision rule to M0: provision 9 unclear means Builder keeps to code-writing and owner decides; provision 7 barred means Narrator attended.

## Verdict
The architecture fits the binding constraints on budget, hardware, Texas, size, team and agent type, and the agent roster is consistent between table and workflow. It has seven real defects that must be fixed before build: an unpassable replication gate, an HALT/permission contradiction, a monthly false-SAFE from dividends, inverted M1-M2 prerequisites, a self-contradicting `llm_origin` rule, an unprobed hand-order mechanism at the first-money step, and a memo gate that tests after-tax for an IRA-only path.

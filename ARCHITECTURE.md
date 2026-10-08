# JARVIS: Final Architecture

> **Historical proposal (2026-10-02).** The owner subsequently clarified that JARVIS should restore its information-analysis foundation and autonomously scan, select, execute and learn across equities and spot crypto. The [autonomous architecture proposal](AUTONOMOUS_ARCHITECTURE.md) is now the current design direction. This document is preserved for its evidence, review history and earlier decisions; its monthly manual-order workflow is not the current product target.

Chief architect, final revision after two verification passes, 2026-10-02. This document stands alone and replaces `FINAL-design.md` wherever the two disagree. Section 17 lists each verification must-fix and how it was resolved.

**How to read the labels**
- **ESTIMATE**: arithmetic or judgement, not a measurement.
- **DC** (design choice): a setting picked by judgement, not taken from a paper. **"DC, motivated by X"** means a source points in that direction but does not establish the specific setting.
- **UNVERIFIED**: no source has confirmed it. Each one has a probe or an open item in section 15.
- **ILLUSTRATIVE**: example numbers, not data.
- **Read-depth tags** (section 16): **FETCHED-full** (the text was read), **FETCHED-abstract**, **FETCHED-summariser** (a tool's summary of the page was read), **SECONDARY** (a report about the source was read), **SNIPPET** (search result only), **RECALLED** (memory only).
- "Brief NN" means research brief NN in `research/`. "S01-S10" are the ten specialist reviews in `review/`.
- Nothing here is investment, tax or legal advice. JARVIS computes what the owner's own pre-written rules imply. The owner decides.

---

## 1. Summary

**What JARVIS is.** JARVIS is a personal investing co-pilot for one person in Texas with $1,000-$10,000 of their own money. It has three parts.

1. **A small, boring, deterministic money engine (code).** Once a month it computes the owner's target portfolio: five low-cost ETFs plus a T-bill ETF "dial" for risk. It checks every proposed order against hard limits and tells the owner exactly which orders to place. At launch the owner places them by hand. A code-driven executor is an optional later step.
2. **A team of Claude agents that do real, checked work around the money but never touch it.** One agent builds the software and another reviews it. Others write the weekly memo, answer questions about the ledger, triage incidents, watch vendor and terms pages, and run a research lab that tests strategy ideas honestly. Every agent produces typed output that code checks. Every agent has a template or code-only fallback, so the money engine runs the same with all agents switched off.
3. **A tamper-evident record.** An append-only ledger in a private git repository records every decision, deviation and fill.

**The rule that never bends.** No runtime Claude output decides, sizes or times an order. Claude authors, code decides, and the owner signs. The three channels through which Claude-written material can still reach an order (code, corporate-action drafts, Lab specs) are listed with their controls in section 4.0. The reasons:
- **No evidence of an LLM edge.** The studies in the evidence base show no reliable after-cost win for an LLM trader over buy-and-hold. They are weak evidence either way: FINSABER is long but pre-cutoff, so models may have memorised the period (Lopez-Lira, Tang and Zhu 2025); StockBench covers 82 days, and some agents did beat buy-and-hold on raw return; CLQT was read at abstract level only (brief 01). This is absence of evidence, not proof of impossibility. It is still enough to keep Claude off the order path.
- **LLM advice is biased.** Studies of LLMs as investment advisers find biased recommendations and agreement with the user (S04: Winder et al. 2025, Lee et al. 2025, Zhi et al. 2025, Sharma et al. 2024). These studies used older models; how large the effect is for current Claude is unknown.
- **Terms.** Anthropic's Consumer Terms provision 9 appears to bar relying on the Services to buy or sell securities. S06 read it through a summariser, so the owner confirms it in M0 (O4).

**The honest expectation** (ESTIMATE; sources in sections 2 and 6)
- **The core (S0)** earns roughly what its five ETFs earn, minus about 0.088% a year in fund fees (S02). The dial trades some expected return for a smaller worst-case loss, sized from the dollar loss the owner says they can sit through.
- **The trend strategy (S-A, plain Faber 10-month moving average)** is expected to change pre-tax return by about 0 ± 1 point a year against holding the same ETFs (brief 18). Published histories show large drawdown cuts, from different rules and periods:
  - Faber's text reports his five-asset SMA10 book's maximum drawdown falling from 46% to under 10%, about 0.2 of buy-and-hold (broad commodities included).
  - Antonacci reports a median of 0.4 of buy-and-hold drawdown for 12-month absolute momentum (S01).
  - JARVIS's own ETF-era check tests only the direction of the change (section 8).
- **In a taxable account S-A costs money after tax.** The design-assumption central case is −1.1 to −1.4 points a year, about −$14 to −$18 a year on a 12.5% sleeve of $10,000. The range is −2.4 to 0.0 points (−$30 to $0). The figure is sensitive to the short-term-gain share (Alpaca's FIFO lot method may lower it, S03-P4) and to the trend hurdle (brief 18's 0-0.9 point hurdle gives a central case near −0.5). Across the whole range the sign is unfavourable or zero, so S-A never runs live in a taxable account.
- **No sample the owner will ever have can settle whether S-A works.** Detecting an information ratio around 0.2 takes tens to about 200 years, depending on correlation and statistical power (S01: 96 years at 95% confidence and about 50% power, about 196 at 80%; S07: 31-93 years at 80% power for a Sharpe difference at correlations 0.9-0.7).
- **So S-A runs in shadow.** "Retire S-A" is the most likely verdict of its decision memo. S-A can go live only inside a tax-deferred account, and only if the memo, gated on **pre-tax** results for that account, does not fail it.
- **Where the value is most likely to come from:**
  - keeping the owner on the plan (behaviour);
  - putting the right assets in the right account type (tax location);
  - avoiding tax mistakes (gold's 28% collectibles rate, wash sales across accounts);
  - a record the owner trusts;
  - agents that save the owner time.
- **The behaviour gap is two different published numbers.** Morningstar's dollar-weighted gap is about 1.2 points a year (7.0% vs 8.2%, ten years to December 2024; SNIPPET). Vanguard's estimate of about 1.5 points is the value of adviser behavioural coaching, a different quantity, via a secondary source. Both come from vendors with an interest in the result. JARVIS measures the owner's own gap directly rather than assuming either number.
- **"JARVIS runs the benchmark and monitors it" counts as success.** The owner charter says so in writing.

**Is this over-built for the money at stake?** The reviewer's concern was tested. It held for the previous design: three Windows accounts, emailed approval hashes, a 95% mutation-score gate, 134-182 dev-days and first live dollars at month 12-15, all built around a satellite whose sign after tax is unfavourable. This version removes all of that. It keeps one Windows account, approvals as owner commits, failure-catalogue tests, about 37-49 dev-days for v1 (unvalidated planning estimate), and real money placed by hand at about month 2.5-4. What remains is sized to a $1,000-$10,000 account: the smallest gate that blocks fat-finger and unit errors, $0 metered spend, and stop rules that end feature work if milestones slip.

**Monthly cost.** Metered spend is **$0.00 a month**. No Anthropic API key exists anywhere in the system. Every Claude agent runs on the owner's existing Claude subscription, which is a sunk cost. Data comes from free tiers: Alpaca Basic, FRED and SEC EDGAR. Monitoring uses the Healthchecks free tier and a free private GitHub repository.
- The real scarce resource is **plan usage**. The owner has already hit the session limit once, so section 10 sets rules for it.
- The ETFs' own expense ratios (about $0.88-$8.80 a year on $1,000-$10,000) are a holding cost, not a JARVIS cost.
- Costs outside the $0 claim, both optional: an Alpaca IRA fee (unknown; M0 question O7) and a tax-professional consult.

**Timeline** (unvalidated planning estimate at 15 hours a week, with a 1.3-1.5× calendar allowance for plan-limit stalls):
- First shadow email: about week 5-8.
- Real money following the JARVIS plan, placed by hand: **about month 2.5-4**. This includes waiting for the first real month-end after the M3 code is done.
- S-A decision memo and calibrated risk dial: about month 4-6.
- Optional attended executor: built about months 5-9, live after paper tests at about month 10-11.

The previous design reached first live dollars at month 12-15 and needed 134-182 dev-days. This one completes v1 in about **37-49 dev-days**, plus an optional 20-28 for the executor. The dates are not the commitment. **The stop rules in section 11 are the commitment.**

---

## 2. What the previous design got right, and what this version improves

| # | Item | Verdict | Evidence | Effect on cost / build time |
|---|---|---|---|---|
| 1 | No runtime Claude output decides, sizes or times an order | **Kept** | Brief 01 (FINSABER pre-cutoff, StockBench 82 days, CLQT abstract only: no reliable after-cost win, weak evidence either way); S04 (Winder, Lee, Zhi, Sharma; older models); Gencay 2026 abstract (every LLM-found strategy rejected under honest evaluation) | None |
| 2 | S0 (equal-weight five ETFs) as the null and the product; plain untuned Faber; risk-matched null S0-RM | **Kept** | DeMiguel et al. 2009: optimised weights did not beat 1/N out of sample. Their datasets are equity-style, so this supports "do not optimise weights", not "20% in each of five asset classes is a good portfolio". Huang et al. 2020; Zakamulin 2018 | None |
| 3 | Monthly, long/flat, marketable limit orders, no ETF stops | **Kept** | Briefs 06, 09, 11, 17, 21; Alpaca order docs (S02) | None |
| 4 | Default-deny gate with error-order controls, deterministic order ids, lookup before submit, reconcile with broker | **Kept, smallest form** | SEC Knight order 2013-222; FINRA 15-09 (S09) | Needed only when code places orders (M5) |
| 5 | Point-in-time data (`available_at`), as-of snapshots, leak tests | **Kept, plus a planted look-ahead oracle** | Zakamulin 2018 (look-ahead created moving-average "alpha"); Gencay 2026 (a Sharpe-35 oracle passed deflation; caught only structurally) | +0.5 dev-day |
| 6 | Typed agent output, code validator, template fallback | **Kept** | Huang et al. ICLR 2024 (no reliable self-correction without external feedback); Reflexion; Anthropic "Building effective agents" | None |
| 7 | Tax-lot deferral; wash-sale rule across all accounts | **Kept, simplified to one two-way rule** | Wash sale: IRS Pub. 550; Rev. Rul. 2008-5. Deferral: DC, motivated by Odean 1998 (investors realise gains too early) | About 1 dev-day |
| 8 | Tighten at once, loosen slowly (72-hour cool-off) | **Kept, now enforced by code** | DC, motivated by Thaler-Benartzi 2004 (pre-commitment for savings; not technical lock-in) and FINRA 15-09 (controls and kill switch, never delayed). Neither source supports 72 h specifically | Saves 3-5 dev-days (no emailed hashes) |
| 9 | Dead-man alert off the laptop; revoke v1's leaked key; own-money legal perimeter | **Kept** | Knight's 97 ignored automated emails; brief 12 | None |
| 10 | No LangGraph, Docker, Redis or Postgres | **Kept** | Briefs 02, 03, 14; Anthropic (agents about 4× and multi-agent about 15× chat tokens); MAST 14-mode failure taxonomy | None |
| 11 | Live 12.5% S-A satellite with G4/G5 ladder, sleeve tags, netting | **Improved: S-A in shadow; live only in an IRA** | S01, S07 (tens to about 200 years to detect an information ratio near 0.2); S03 (taxable central case −$14 to −$18 a year; range −$30 to $0) | Saves about 12-25 dev-days |
| 12 | Stacked G1a/G1b/G1c gates (ONC, Galwey, PBO, 20-year rule) | **Improved: one pre-registered decision memo, gating only on G1b(ii), pre-tax for the IRA path** | S07 DSR table (buy-and-hold passes G1a); Bailey-López de Prado DSR paper; White 2000 | Saves about 6-9 dev-days |
| 13 | Prepaid API workspace, cap formula, tiers T0-T2, batch jobs, eval workspace | **Improved: all agents on the subscription; $0 metered** | S06 (the T0 cap of $8.40 a year is 47-60% of S-A's central-case taxable cost); Consumer Terms (summariser-read; O4) | −$0.70 to −$2.02 a month; net −6 to −9 dev-days |
| 14 | Unattended tool-using Incident Analyst on the key-holding account | **Improved: attended `/incident` over a code-built bundle** | tau-bench (pass^8 under 25%; a 2024 gpt-4o-era retail result, so dated and direction only); Anthropic's human-checkpoint advice | Removes the only LLM near broker keys |
| 15 | Three Windows accounts, ACL matrix, inbox/outbox, emailed approval hashes | **Improved: no live key where the Builder runs; approvals are owner commits; code sets `effective_after`** | S09; Microsoft Learn (Logon-as-Batch needs an admin policy change) | Saves about 8-14 dev-days |
| 16 | Rich SAFE state with a risk-reducing order class and auto-clear | **Improved: SAFE = place no orders, alert, exit** | Knight lessons (stop, do not improvise) | Saves 3-5 dev-days |
| 17 | 95% mutation-score gate | **Improved: failure-catalogue tests, property tests, crash drills** | Yuan et al. OSDI 2014: the majority of catastrophic failures were preventable by simple testing of error-handling code (over 30% by their static checker); Petrovic et al. | Saves 2-4 dev-days |
| 18 | First live dollars only after a 43-53 dev-day executor (month 12-15) | **Improved: RECOMMEND-live S0 by hand at about month 2.5-4; executor optional** | Bhattacharya et al. 2012 (advice often not followed, so measure adherence); Barber-Odean 2000 | Moves live money about 9-10 months earlier |
| 19 | Tiingo stored research copy and mandatory second vendor | **Improved: Alpaca-only daily gate; Tiingo at most transient** | Tiingo ToS 1.6 (free plans: in-memory only; summariser-read) (S10) | Saves 1-2 dev-days; avoids a licence breach |
| 20 | ETF tickers left open; "commodities/gold" with no tax class | **Improved: tickers fixed; `tax_character` field; gold flagged as a 28% collectible** | S02; IRS Chief Counsel memo pmta01809 (basis for treating physical-metal ETF holders as owning collectibles; non-precedential); IRS Topic 409 (the 28% rate only) | +0.5 dev-day |
| 21 | Risk dial from a bootstrap p95 | **Improved: stress-loss formula, rounded up, with hysteresis** | S02 | About 0 |
| 22 | Behaviour value claimed but never measured | **Improved: Behaviour Ledger (adherence, deviations, plan-minus-actual)** | Barber-Odean; Bhattacharya; Morningstar gap (SNIPPET) | +1-2 dev-days |
| 23 | Daily digest email | **Improved: exception-only daily mail** | DC, motivated by D'Acunto et al. 2019 and Sicherman et al. 2016 (indirect: robo-advice adoption; attention and logins) | −0.5 dev-day |
| 24 | "Agents never advise" asserted | **Improved: tested advice-leak set plus code denylist** | Winder; Lee; Zhi; Sharma (S04; older models) | +1 dev-day |
| 25 | Reader at tier T1 with a 300-item golden set | **Improved: dormant; code-only digest first, opt-in** | Lopez-Lira and Tang v6 (Oct 2025): subperiod Sharpe 6.54 falling to 1.22 in the latest period; profitable at 5-10 bps round trip, not at 20 bps. Kim-Muhn-Nikolaev paper temporarily withdrawn pending review | Saves 6-10 dev-days |
| 26 | Shadow ML lane in P2 | **Improved: deferred, 5-day time-box with Welch-Goyal baselines** | Welch-Goyal 2008; Goyal-Welch-Zafirov 2024; Gu-Kelly-Xiu 2020 (ML gains came from millions of stock-months); S10 AUC arithmetic (about 20 years to judge forward) | Saves 6-10 dev-days now |
| 27 | Crypto unlock as a 10% Donchian sleeve | **Improved: static BTC-ETF ≤5%, default off** | S08 (Zarattini et al.: a single non-peer-reviewed working paper; IBIT about 2.7 years of history) | About 0 |
| 28 | Lab trial count by N_eff estimators | **Improved: raw count from one entry point; one-way funnel; replication first** | Gencay 2026; Beel et al. 2025 (42% of AI Scientist runs failed on code errors) | +1-3 dev-days |
| 29 | Orders from 09:45 / 10:00 ET | **Improved: from 10:30 ET** | DC, motivated by Dimensional (spreads widest near the open; European data, indirect) | 0 |
| 30 | Hash chain, SQLite read-only copy, backups, anchor email | **Improved: JSONL ledger with prev-hash in a private git repo** | S09 | Saves 1-2 dev-days |
| 31 | Streamlit dashboard | **Improved: static weekly HTML report generated by code** | 8 GB RAM constraint (brief 14) | Saves build effort and RAM |
| 32 | Rebalance band | **Kept and frozen; contribution waterfall added** | Vanguard (Jaconetti et al., SNIPPET); Daryanani 2008; Berkin-Ye 2003 | About 0 |

---

## 3. Architecture

Each component is marked **[code]** (deterministic Python), **[stat]** (a statistical model or computation), **[Claude]** (an agent) or **[owner]**.

```mermaid
flowchart TB
  subgraph SRC["Free data sources"]
    ALP["Alpaca Basic: daily bars, corporate actions, IEX quotes"]
    FRED["FRED: T-bill rate (TB3MS)"]
    BRK["Alpaca account: activity CSV (owner download) or read-only GET"]
  end
  subgraph ENGINE["Money engine (runs with every agent off)"]
    ING["Ingest + data-trust gate [code]"]
    SNAP["AsOfSnapshot, hashed [code]"]
    STRAT["Strategies: S0(b) live, S0-RM and S-A shadow [code]"]
    COMB["Combine: band, contribution waterfall, tax-lot and two-way wash-sale rules [code]"]
    GATE["Risk gate, default-deny [code]"]
    OUT["Order list: quantity + limit + quote time (RECOMMEND), or attended executor from M5 [code]"]
    REC["Reconcile (DIV/INT/FEE classified) and adopt fills [code]"]
  end
  LEDGER[("Ledger: JSONL with prev-hash, private git repo")]
  STATS["Shadow NAV, after-tax estimator, Behaviour Ledger, PSR/DSR, bootstrap [stat]"]
  FACTS["Weekly facts.json and static report page [code]"]
  VAL["Validator: numbers, schema, enums, denylist [code]"]
  HC["Healthchecks dead-man [external]"]
  OWNER(["Owner"])
  subgraph AGENTS["Claude agents (subscription only, never on the runtime order path)"]
    NAR["Narrator [Claude, scheduled weekly]"]
    LA["Ledger Analyst /ask-ledger /whatif [Claude, attended]"]
    IT["Incident Triage /incident [Claude, attended]"]
    CW["Change-Watch /changewatch [Claude, attended]"]
    REV["Reviewer [Claude, attended subagent]"]
    LAB["Strategy Lab: Spec Clerk, Replication Analyst [Claude, attended]"]
    BLD["Builder [Claude, attended]"]
    RDR["Reader [Claude, dormant / opt-in]"]
  end
  ALP --> ING
  FRED --> ING
  ING --> SNAP --> STRAT --> COMB --> GATE --> OUT --> OWNER
  BRK --> REC --> LEDGER
  OWNER -->|"places orders by hand"| BRK
  GATE --> LEDGER
  LEDGER --> STATS --> FACTS
  FACTS --> NAR --> VAL --> OWNER
  LEDGER --> LA
  ING -->|"anomaly: bundle"| IT
  ING --> HC --> OWNER
  BLD -->|"diffs"| REV
  LAB --> REV
  REV --> OWNER
  AGENTS -.->|"agent-out/*/REQUEST_HALT, promoted by code"| GATE
  OWNER -->|"signed commits: config, releases, G0 freezes"| ENGINE
```

**Data flow in words**
- **Code pulls free data.** The daily check (18:00 Central, after the close) pulls bars for the six ETFs from Alpaca using the paper key's market-data access (UNVERIFIED; M0 probe) and the T-bill rate from FRED.
- **The trust gate checks each symbol.** Checks: SIP close vs IEX-derived close, stale bars, a move over 30% with no matching corporate action, and a missing bar. A failing symbol gets no risk-increasing order.
- **Code freezes and hashes the AsOfSnapshot.** It contains only month-end data whose `available_at` is at or before decision time.
- **Strategy plug-ins compute target books.** Each plug-in maps `target(AsOfSnapshot) → TargetBook`. Only S0(b) is live. S0-RM and S-A run in shadow.
- **The combiner turns targets into orders.** It applies the band, the contribution waterfall, the tax-lot deferral and the two-way wash-sale rule.
- **The gate approves or rejects each order** and writes a reason code.
- **Delivery.** In RECOMMEND mode, code emails an order list with share quantities, limit prices and the quote time, and the owner places the orders. Fills come back through `jarvis adopt`, which reads the broker activity CSV the owner downloads (or uses read-only GET calls).
- **Reconcile knows the broker's routine cash.** Dividends, interest and fees (activity types DIV, INT, FEE and similar; exact CSV labels confirmed in M0) are expected non-owner cash and feed the contribution waterfall. Only owner deposits and withdrawals need `jarvis cash-event`.
- **Statistics** produce the shadow NAVs, the coarse after-tax estimate and the Behaviour Ledger.
- **Agents read only typed files that code produced.** Agents write only into `agent-out/<agent>/`. Code validates everything an agent writes before the owner sees it. An agent that sees danger writes `agent-out/<agent>/REQUEST_HALT`; code promotes it to the real HALT flag and emails the owner (section 5f).

**Where the statistics live.** These are the only statistical models at launch. The M5 and growth items are not built now.

| Model | Used for | Type |
|---|---|---|
| 10-month SMA signal (S-A) | Shadow target book | Rule [code] |
| S0-RM dial b* (T-bill share matching S-A's backtest volatility) | Risk-matched comparison | [stat]. Labelled placeholder (b* = S0(b)'s b) from M1; fitted once in M4 |
| Paired block bootstrap of monthly differences | G1b(ii) in the decision memo | [stat] |
| PSR/DSR with raw trial count | Reported in the memo, not gating | [stat] |
| Coarse FIFO-aware after-tax estimator | Shadow after-tax column, with a 0-100% short-term-share range | [stat] |
| Stress-loss dial b | Mission Plan | [stat] |
| Behaviour P&L: plan-shadow NAV minus actual NAV; money-weighted minus time-weighted return | Weekly memo | [stat] |
| Slippage vs printed quote | Cost check for hand-placed fills (G4) | [stat], in `jarvis adopt` from M3 |

---

## 4. The agents of JARVIS

**Census.** There are six roles with eight named agent definitions. Each is a `.claude/agents/<name>.md` subagent file (the Builder's is the project `CLAUDE.md` plus `builder.md`), with a skill file and a JSON output schema in `schemas/`. The Strategy Lab is one definition with two modes (Spec Clerk, Replication Analyst).
- **Scheduled:** Narrator only, plus the Reader if the owner switches it on.
- **Attended:** everything else.
- **Dormant:** Reader.

No API calls exist. No framework is used. Narrator, Ledger Analyst and Change-Watch are three modes of one "Analyst" role (S06-P4), each with its own tools.

**Why the subscription and not the API**
- The metered stack cost more than the spend it governed (S06).
- **Unattended route: S06 interpretation, unconfirmed.** S06 inferred, from a summariser read of Consumer Terms provision 7 and the Claude Code legal page, that unattended subscription use is acceptable only through Anthropic's own Desktop scheduler. S06 itself left open whether `claude -p` or a setup token counts as "explicit permission". The owner reads provisions 7 and 9 in M0 (O4). "At most weekly" is a design invariant (DC), not a term.
- **Decision rule after the M0 read:**
  - If provision 7 bars the scheduler, the Narrator becomes an attended weekly command, or the template memo ships alone.
  - If provision 9 reads as barring use in connection with trading decisions, or stays unclear, agents keep to code-writing and code review (Builder, Reviewer). The memo becomes template-only, and the owner decides everything else.
- Agent SDK programs, `claude -p` cron wrappers and `/loop` (its recurring tasks expire after 7 days) are never used on the subscription login.

**Rules shared by every agent (the "never-do" list, S04-P5).** No agent may:
1. give a buy, sell, hold or timing view, or say whether to override the plan;
2. give a price forecast, target or bare probability;
3. agree with the owner's stated market belief, or reassure in its own words after a loss;
4. present a causal story for a price move as fact;
5. choose or recommend tickers, or change risk because of the owner's mood;
6. present shadow or backtest results as predictions;
7. use urgency or fear-of-missing-out language.

**Enforcement**
- The rules are in every prompt.
- The validator's denylist rejects imperative buy/sell wording, bare percentages framed as probabilities, and price targets.
- A 30-prompt **advice-leak set** runs in an attended session after any prompt change and whenever the model used by a scheduled task changes. The red-line subset must pass 100%. Passing 30 of 30 bounds the failure rate only to about 10% (rule of three), so it is a smoke test, not proof.
- No agent holds a broker key, the owner's GitHub credential or a mail credential.
- No agent writes outside `agent-out/<agent>/`. Writes to `.claude/**` are denied. The one way an agent can stop trading is a `REQUEST_HALT` file inside its own folder, which code promotes (section 5f). That only ever tightens.

### 4.0 The only paths from Claude-written material to an order

Runtime agent output never reaches an order. Three channels of Claude-written material do reach orders, and each has its own control.

| Channel | How it reaches an order | Controls |
|---|---|---|
| **Builder-authored code and config** | Code computes every order | Failure-catalogue and property tests; `jarvis release` refuses without a Reviewer note whose hash matches the diff of `jarvis/gate/`, `jarvis/orders/` or `config/`; the owner reads those diffs; code detects any loosening of `risk.yaml` and sets a 72-hour `effective_after` itself |
| **`draft_corporate_action` (Incident Triage)** | A corporate-action row changes the adjusted price series and so the SMA signal and trust state | Code accepts it only if (a) it reconciles the price series within 0.5%, (b) the vendor corporate-actions feed lists the same action, and (c) the owner commits it. Until the vendor lists it, the symbol stays untrusted for buys, which is the safe direction (section 14, V3) |
| **Lab specs** | A frozen spec can become a strategy | `llm_origin` specs reach **shadow only**. Live eligibility needs the owner to re-register the idea as an owner-origin spec after ≥12 forward decisions, with a new G0 (counted as a new trial). S-A itself can go live only in an IRA under section 8 |

### 4.1 The agent table

| Agent | Purpose | When | How it runs, and why | Tools and permissions | Inputs | Structured output | How the output is checked | Must never | Monthly cost |
|---|---|---|---|---|---|---|---|---|---|
| **Builder** | Writes all code, tests, schemas, prompts and runbooks | Owner's work sessions, about 2.5 dev-days a week | Attended Claude Code session. Building needs judgement and back-and-forth | Full dev tools in `C:\dev\jarvis` only. No live key exists on disk. Paper key only | Repo, `BACKLOG.md`, milestone definition of done | Commits and PRs, plus `docs/` | Failure-catalogue tests; property tests on the gate; leak tests plus planted oracle; crash drills (M5). `jarvis release` refuses a release touching gate, order path or config without a matching Reviewer note. The owner reads those diffs | Touch `C:\jarvis-prod`; hold or ask for the live key; push releases; edit `config/risk.yaml` without the owner's commit | $0 metered. The largest plan-usage consumer |
| **Reviewer** | Advisory pre-mortem on diffs, Lab specs, loosening requests and decision memos | On every release candidate that touches `jarvis/gate/`, `jarvis/orders/` or `config/` (enforced by `jarvis release`); on each Lab spec; on each loosening | Attended subagent with a fresh context. Same-model debate is weak (brief 02), so it is fed code diagnostics, not opinions | Read, Grep only. No Bash, no web | The artifact plus code diagnostics: leak tests, cost ×2, offsets, plateau | `{diff_hash, failure_modes[], missing_evidence[], leakage_suspects[], kill_conditions[], cites_diagnostics[]}` | Schema check. Every finding must cite a file and line or a diagnostic id. `diff_hash` must match the release diff. **Sanity bar: 5 of 8 seeded defects** (v1's four known, two tax, two gate); the interval is wide and the bar is advisory. If it catches fewer than 4 of 8, the Reviewer is replaced by an owner checklist built from the same 8 defects | Approve anything. Give probabilities. Its note is never required for a tightening | $0. Small plan usage |
| **Strategy Lab**: modes *Spec Clerk*, *Replication Analyst* | Turns ideas into pre-registered specs; runs the harness; writes replication and null-result reports | M4 replication, then at most monthly; maintenance mode once 50 trials are logged with nothing clearing | Attended session. Research needs iteration, but no price rows ever enter its context | Dev tree and `lab/`. Runs only `jarvis-lab run <spec_id>`. No web, no ledger writes | Pre-registration form (mechanism, cited source, sign, universe, ≤6 cells, kill condition) | `lab/specs/<id>.yaml` (hashed into `lab/registry.jsonl` before any run); result JSON ≤1.5k tokens | One entry point logs a trial row for every run; the raw count N feeds DSR. A planted random spec must fail; the oracle must be blocked. The Reviewer critiques. The owner's G0 freeze is a signed commit | Tune inside a family after seeing results (a rewrite is a new family). Read holdout or price rows. Mark an `llm_origin` spec live-eligible (they reach shadow only; section 4.0) | $0. Episodic plan usage |
| **Narrator** (Analyst, memo mode) | Weekly memo: NAV vs S0 and S0-RM, Behaviour Ledger, gate rejections, S-A shadow line, "what the agents did", questions for the owner | Desktop scheduled task, Sunday 17:00 Central; laptop awake, app open | Scheduled Claude Code task (route per the S06 interpretation above; owner confirms in M0). Model id and effort pinned in the task if the M0 probe shows pinning works; otherwise code records the model each run uses and a change triggers the advice-leak rerun | Read `reports/weekly/<date>/facts.json` only. Write `agent-out/narrator/` only. Bash allowed for exactly `jarvis validate-memo`. No web | Typed facts from code: numbers, enums, reason codes. Fields not yet built carry `not_yet_available` | `Report{headline, action_ids[] (closed enum, rendered to text by code), rejections[], risk_state, vs_S0, vs_S0RM, behaviour{adherence, deviations, plan_minus_actual}, agent_desk[], questions_for_owner[] (≤3, ≤200 chars each)}` | Inside the task: up to 2 repair passes against `jarvis validate-memo`. Then the 19:30 code job re-validates independently: every number must match the ledger, `action_ids` must be in the enum, and the denylist applies to all free text. **On failure, the template memo is sent** | Write the order email (that is 100% code). Read raw text, URLs or other folders. Use any recipient but the owner | $0 metered. Plan usage: at least about 68k input tokens a month (memo payload only, 15.6k × 4.33; a lower bound, since harness overhead and repair passes are unmeasured; measured in M2) |
| **Ledger Analyst** (Analyst, ask mode) | Conversational JARVIS: "why did we sell X?" (`/ask-ledger`, from M2); "what if I had held through March?" (`/whatif`, from M3b) | On demand | Attended. Interactive by nature | DuckDB **read-only** over the ledger JSONL; runs `jarvis whatif` functions. No writes, no web | Ledger, shadow NAVs, dial settings | Answer plus the SQL or `whatif` call used, and the numbers it returned | The SQL is shown. Every number comes from a query or a code counterfactual, never from the model | Invent a counterfactual. Advise an override (never-do list) | $0. On demand |
| **Change-Watch** (Analyst, watch mode) | Says what changed on watched vendor or terms pages and which config key or runbook step it touches | When the weekly code page-hash job emails "pages changed" | Attended `/changewatch`. Pages are untrusted text, so a human is present | Read the sanitised, length-capped diff file only. Write `agent-out/changewatch/` (may include `REQUEST_HALT`) | Diff file | `{page_id, summary≤300 chars, affected_config_keys[] (closed enum), runbook_step_ids[], severity}` | Keys must exist in the enum; schema check | Change config. Follow instructions found in page text | $0. A few runs a year |
| **Incident Triage** | Explains a SAFE or HALT event and drafts the runbook step and any `corporate_actions` row | When an exception email says "run /incident <id>" | Attended. A monthly book loses nothing by waiting for the owner, and this removes the only tool-using LLM from any key-holding context (S06-P3) | Read `incidents/<id>/bundle.json` only. Write `agent-out/incident/` (may include `REQUEST_HALT`) | Code-built bundle: ledger rows, gate log, redacted log window, vendor snapshot, code-computed `cause_enum` and runbook step | `{timeline, cause_enum, runbook_step_id, evidence_row_ids[], draft_corporate_action?}` | Row ids must exist. A draft corporate action needs the three checks in section 4.0 | Clear SAFE or HALT. Touch keys. Place or suggest orders | $0. A few runs a year |
| **Reader** (dormant) | Typed events from SEC filings for the owner's watch list, to enrich an opt-in digest | Off at launch. Weekly Desktop task only if the owner enables it (section 12) | Scheduled. Quarantined, because filing text is untrusted | Read one sanitised file; write one output file. No Bash, no web | NFKC-normalised, HTML-stripped, length-capped text | `{event_type, materiality, novelty, instruction_like_text, span_start, span_end}` | Schema check. Spans must be code-verified substrings or null. 30-item spot check at enablement. `event_type` comes from 8-K item codes by code | Map tickers. Affect any order. Write free text | $0. About 0.46-0.59M input tokens a month if enabled (S05/S06 ESTIMATE) |

**Meaningfulness test** (budget hawk's addition, adopted)

| Agent | Kind | Visible artifact | Test |
|---|---|---|---|
| Builder | Routine | Code | Ships each milestone |
| Reviewer | Routine | A pre-mortem on each risky diff | One per gated release |
| Lab | Routine (from M4) | Replication report and trial file | Something every month it runs |
| Narrator | Scheduled | Weekly memo | Valid memo most weeks (template rate reported) |
| Ledger Analyst | On demand | Answers with the SQL shown | Used at least once a month, or reviewed |
| Incident Triage | Event-driven | Incident file | **No unhandled trigger** |
| Change-Watch | Event-driven | Typed change note | **No unhandled trigger** |

A routine or scheduled agent that ships nothing for two months is reviewed for removal. Event-driven agents are exempt from the two-month rule; they fail the test only if a trigger goes unhandled.

**Agent memory.** There are no per-role memory files at launch. A `memory/<agent>.md` file, appended **by code** from validator failures and owner accept/reject decisions only, is added for an agent once the same validator failure recurs three times, or at the month-4 checkpoint (S06-P8, decision D20).

### 4.2 Non-LLM modules that replace the owner's remaining agents

| Module | Type | Replaces (owner's agent) | What it does |
|---|---|---|---|
| `jarvis.run` state machine | code | Orchestrator / Supervisor | Lock → reconcile → HALT check → trust gate → snapshot → targets → gate → deliver → ledger → ping |
| `jarvis.mission` | code + stat | Goal & Capital Planner | Dial b from dollar tolerance; account-location table; goal shown as a range; rejects goal-driven risk |
| `jarvis.data.trust` | code | Data Trust / Data Steward | Per-symbol checks; blocks risk-increasing orders only |
| `jarvis.strategies` | code | Strategy / Portfolio, Market / Technical | S0(b), S0-RM, S-A plug-ins |
| `jarvis.gate` | code | Capital Governor / Risk | Default-deny limits (section 7) |
| `jarvis.orders` (from M5) | code | Execution | Idempotent ids, lookup before submit, attended only |
| `jarvis.reconcile` | code | Position Manager / Monitor | Broker is the source of truth; classifies activity types; adopt; detects foreign orders |
| `jarvis.ledger` + `jarvis.behaviour` | code + stat | Ledger / Review, Auditor | Append-only record; Behaviour P&L; attribution |
| `jarvis.costs` | code | Flow / Microstructure | From M3: slippage of each hand fill vs the quote printed on the order list. From M5: vs arrival quote, plus quote age |
| `jarvis.report` | code | Dashboard / daily summary | Exception mail, monthly order email, static weekly page |

### 4.3 How the owner's 18 v3 agents map

| v3 agent | Becomes | Why |
|---|---|---|
| 1 Orchestrator / Supervisor | Code state machine | An LLM supervisor multiplies tokens (Anthropic: about 4× for agents, about 15× for multi-agent systems) and adds failure modes (MAST's 14-mode taxonomy; the 41-87% benchmark failure rates quoted for open-source frameworks are unconfirmed) |
| 2 Goal & Capital Planner | Code (Mission Plan) + Narrator explains | Kept in spirit; code computes, Claude explains |
| 3 Opportunity Scanner | Deferred (Watchlist Digest, opt-in) | No consumer on an ETF book; single names unreachable below the $31,500 Norgate threshold (brief 06) |
| 4 Data Trust Agent | Code + Incident Triage | Checks are deterministic; Claude explains failures |
| 5 Market / Technical | Code (SMA signal) | One published rule |
| 6 Flow / Microstructure | Code cost check (M3 hand fills; M5 executor) | Order flow forecasts only seconds ahead; no equity L2 (brief 07) |
| 7 News & Event | Reader (dormant) | Text alpha is short-lived, small-cap and decaying (Lopez-Lira and Tang v6) |
| 8 Fundamental / Macro | Dropped for now | No strategy consumer |
| 9 Crypto | Deferred: static BTC-ETF ≤5%, default off | Alpaca spot crypto unconfirmed for Texas; taxable hurdle (S08) |
| 10 Manipulation Surveillance | Dropped as written; 30% move quarantine kept | Spoofing detection needs participant data (brief 07) |
| 11 Bull / Bear | Reviewer | Same-model debate is the weakest configuration (brief 02) |
| 12 Model Ensemble | Deferred ML lane (5-day time-box) | About 1,300 rows; Welch-Goyal prior of no skill |
| 13 Confidence Calibrator | Dropped; uncombined evidence panel | A pooled score needs its own calibration data, which JARVIS lacks: a linear pool of calibrated forecasts is itself uncalibrated and must be recalibrated on outcomes (Ranjan-Gneiting 2010, brief 10) |
| 14 Strategy / Portfolio | Code plug-ins | Deterministic |
| 15 Capital Governor / Risk | Code gate | "No LLM override" (owner's own principle) |
| 16 Execution | Owner by hand, then optional attended code (M5) | Behaviour first; the executor must earn its build |
| 17 Position Manager | Code reconcile and month-end rule | Confidence-drop exits untested and noisy (brief 17) |
| 18 Ledger / Review | Code ledger + Narrator + Ledger Analyst | Records by code, explanations by Claude |

---

## 5. Detailed runtime workflow

Times are US Eastern (ET) unless stated; Texas is Central (ET minus 1 hour). In every flow, any agent failure means the template or the code-only path runs instead. In every code flow, **an uncaught exception means**: Healthchecks `/fail` ping, an incident bundle with the traceback, exit, and **no partial order list** (the order list is written atomically, only after every step has succeeded).

### (a) Monthly decision and order run (RECOMMEND mode, from M3)

| # | Actor | Input | Action | Output | On failure |
|---|---|---|---|---|---|
| 1 | Code (daily job, last trading day) | Month-end closes | Normal daily check (flow b); flags "decision window opens next trading day" | Ledger row | As flow b |
| 2 | Owner | Exception email "decision day" | Downloads the Alpaca activity CSV into `C:\jarvis-data\inbox\` (or, only if M0 found no CSV export, types the live key for read-only GET calls in a terminal with no Claude session) | CSV file | No CSV → `jarvis month` stops with "download activities first" |
| 3 | Owner | — | Runs `jarvis month` in a plain terminal from 10:30 ET (09:30 Central) on any of the first 5 trading days. No Claude session is needed | — | Not run by trading day 5 → code logs `MISSED_REBALANCE`; the laptop emails on day 6; Healthchecks check B is the off-laptop backstop |
| 4 | Code | Activity CSV | Reconcile positions and cash. DIV, INT, FEE and tax-withholding types are expected non-owner cash and become contribution-waterfall cash. Deposits, withdrawals and journals must match a registered `jarvis cash-event`. Any activity type not on the known list → SAFE | Reconcile record | Unexplained break, unregistered deposit or withdrawal, or unknown type → SAFE: no order list, incident bundle, exit |
| 5 | Code | HALT flag, `agent-out/*/REQUEST_HALT` | Promote any agent halt request to HALT and email; if HALT is set, stop here (data and shadow NAVs are unaffected) | — | HALT → "halted" email with the reason, exit |
| 6 | Code | Bars, FRED | Trust gate per symbol; freeze and hash the AsOfSnapshot; `decision_id = hash(strategy_version, date, snapshot_hash)` | Snapshot | Failing symbol: no buy for it, sells still listed. Alpaca unreachable after one retry → no order list today; try again another window day |
| 7 | Code / stat | Snapshot, `mission_plan.yaml` | Targets for S0(b) (live), S0-RM and S-A (shadow) | Target books | Uncaught exception rule |
| 8 | Code | Targets, holdings, cash | Combine: new cash (deposits, dividends, interest) to the most underweight eligible ETF first; sell only on a band breach that cash cannot fix; defer short-term-gain or collectibles-rate sales within 30 days of turning long-term; wash-sale rule both ways (section 7); deltas under $20 skipped; 2% cash buffer | Proposed orders | Uncaught exception rule |
| 9 | Code | Proposed orders, `risk.yaml` | Risk gate (section 7); reason code per order to `gate_log` | Approved list | A rejected order is listed as rejected, with its reason |
| 10 | Code | Approved list, fresh IEX quotes | Order email and terminal print: ticker, side, **share quantity** (fractional where the M0 probe allows fractional limit orders), **limit price** (marketable, 10 bps), dollar estimate, **quote time and "valid until" (quote time + 15 minutes)**, tax-lot note. Plus one line listing lots with unrealised loss ≥5% and ≥$50 (information only) | Email | Mail fails → terminal print and a file in `reports/` |
| 11 | Owner | Order list | Places the orders in the Alpaca web dashboard or app (M0 probe P4) before "valid until". After that, runs `jarvis month --requote`, which reprices limits from fresh quotes without changing targets or `decision_id`. Any order not placed needs a templated reason ("rule I am departing from / what I expect") | Orders at broker | No manual order entry for the live account → see section 9, key exception |
| 12 | Owner + code (`jarvis adopt`, same or next day) | Fresh activity CSV | Imports fills; matches them to the list; records deviations (skipped, changed, extra); computes slippage vs the printed quote | Fills, Behaviour Ledger rows, cost rows | Unmatched activity → SAFE until adopted or registered |
| 13 | Code | Ledger | Commit and push to the private `jarvis-ledger` repo; Healthchecks check B "decision recorded" ping | Git commit | Push failure → retry next run; the local clone keeps the record |

**First deployment into an empty account.** The owner deposits and registers it with `jarvis cash-event`. At the next decision window, `jarvis month` runs the same flow; with no holdings, the contribution waterfall turns the cash into buy orders toward target. The Mission Plan may stage the first deployment over up to three windows (`first_deploy_windows: 1-3`, the owner's choice, DC). The first real month-end is a calendar event: once the M3 code is done, up to a month can pass before it arrives (section 11 uses that wait for M3b).

**From M5 (attended executor):** steps 10-12 become `jarvis execute`.
- The owner types the live key in a terminal with no Claude session open.
- Code prints the order list, and the owner types a confirmation for the first six live months.
- Each intent is persisted, the order id is looked up, then the order is submitted and polled until it reaches a terminal state (15-minute timeout).
- A retry at 11:30 ET adopts or cancels anything left working.

### (b) Daily check (unattended code, 18:00 Central on trading days, laptop)

| # | Actor | Action | Output | On failure |
|---|---|---|---|---|
| 1 | Code | Take a lock; Healthchecks `/start`; promote any `agent-out/*/REQUEST_HALT` to HALT and email. **HALT does not stop this job**: data and shadow NAVs keep running; HALT blocks only order steps | — | Lock held → exit quietly |
| 2 | Code | Pull bars (raw and adjusted) and corporate actions for the 6 ETFs; pull FRED | Parquet in `C:\jarvis-data\bars` | Missing bar → symbol untrusted. Alpaca down after one retry 30 minutes later → all symbols untrusted today, no shadow update, `/fail` with `DATA_OUTAGE`; email from the second consecutive day. FRED down → last value with a stale flag (it feeds no order) |
| 3 | Code | Trust gate: SIP vs IEX-derived close within 0.5%; stale bar; >30% move with no corporate action | `trust.jsonl` | Fail → exception email only if the state changed |
| 4 | Stat | Shadow NAV for S0, S0(b), S0-RM, S-A; expected target diff if month-end were today; drawdown vs crisis-letter thresholds | Ledger rows | Threshold crossed → code emails the owner's own crisis letter. Uncaught exception rule |
| 5 | Code | Commit and push the ledger; Healthchecks success ping (check A) | — | Laptop asleep: StartWhenAvailable runs it later; check A alerts after 8 days of silence |
| 6 | Code | **Mail only on exceptions:** state change, trust failure, decision day, missed rebalance, crisis letter, incident, HALT reminder (weekly while HALT stands) | Email | — |

### (c) Weekly agent cycle

| # | When | Actor | Action | Output | On failure |
|---|---|---|---|---|---|
| 1 | Sun 16:00 Central | Code | `git pull` the ledger; build `facts.json` with typed fields only (numbers, enums, reason codes, Behaviour Ledger, agent counters); fields not yet built are `not_yet_available`; page-hash check of the watched pages (from M3b) | `reports/weekly/<date>/facts.json` | Pull fails → stale-data flag in the facts |
| 2 | Sun 17:00 | **Narrator** (Desktop scheduled task) | Writes the memo JSON; runs `jarvis validate-memo`; up to 2 repair passes | `agent-out/narrator/<date>.json` | Plan limit hit, laptop asleep, or still failing → no file |
| 3 | Sun 19:30 | Code | Re-validates independently; renders `action_ids` to fixed text; renders the static report page and email; appends the "agent desk" block (runs, validator passes, template rate, Reviewer findings, incidents triaged) | Weekly email and `reports/weekly/<date>.html` | No valid file → **template memo** with the same numbers |
| 4 | Sun 19:30 | Code | If any page hash changed: email "run /changewatch" | Email | — |
| 5 | Any time that week | Owner + **Change-Watch** / **Ledger Analyst** | Optional attended runs | Typed notes, answers | — |
| 6 | Weeks 1-4 after M2 | Owner | Records plan usage of the scheduled run (and of Builder sessions) in `ops/plan_usage.csv` | Usage log | If one Narrator run takes a visible share of the weekly limit, shrink `facts.json` before adding any agent |

### (d) Research / Strategy Lab cycle (attended, monthly at most)

| # | Actor | Input | Action | Output | On failure |
|---|---|---|---|---|---|
| 1 | Owner + **Lab: Spec Clerk** | An idea | Fill in the pre-registration form: mechanism, cited source, sign, universe, ≤6 cells, kill condition. `llm_origin` is tagged if Claude proposed it | `lab/specs/<id>.yaml`, hash appended to `lab/registry.jsonl` | Missing a cited source → rejected at the form |
| 2 | Code (`jarvis-lab run`) | Spec | Harness: total-return monthly series on the ETF-era window, one-bar lag, costs, 21 rebalance offsets, coarse after-tax estimate, pre-tax and after-tax columns, S0-RM comparison; logs a trial row (an `llm_origin` run counts ×2) | Result JSON ≤1.5k tokens | Series without declared `available_at` → refused (oracle guard) |
| 3 | **Reviewer** (fresh context) | Result plus diagnostics | Pre-mortem citing diagnostics | Review JSON | — |
| 4 | Owner | All of the above | Accept to shadow (G0 freeze as a signed commit) or reject. **Negative results stay in the registry** | Registry entry | — |
| 5 | Code | Frozen spec | Forward shadow scoring. An `llm_origin` spec stays in shadow. To become live-eligible, the owner re-registers it as an owner-origin spec after ≥12 forward decisions, with a new G0 that counts as a new trial | Shadow NAV | — |
| — | Rule | Registry | At N = 50 trials with nothing clearing → maintenance mode (replication, null reports only) | — | — |

**The first Lab jobs (M4), in order:**
1. Replication Analyst: reproduce plain Faber on the ETF-era window against the claims that window can check, with the numeric tolerances in section 8 (turnover, round trips, direction of the drawdown change). Antonacci's long-history medians are not a gate.
2. A planted random spec, which must fail.
3. The look-ahead oracle, which must be blocked.
4. The v1 TSLA leak post-mortem, done in M1 as the teaching case.

### (e) Incident handling

| # | Actor | Action | Output | On failure |
|---|---|---|---|---|
| 1 | Code | Detects the cause: reconcile break, foreign order, unregistered deposit or withdrawal, unknown activity type, broker constraint changed (`no_shorting`, margin multiplier), rate breach, trust failure, uncaught exception, promoted `REQUEST_HALT` | `cause_enum` | — |
| 2 | Code | Enters SAFE (no orders, `/fail`, exit) or HALT (rate breach, kill, S-A lifetime stop, promoted agent request). Writes `incidents/<id>/bundle.json` with redacted logs and the code-chosen runbook step | Bundle | — |
| 3 | Code | Exception email: status code, runbook step, "run /incident <id>". No balances in the ping | Email | Healthchecks alerts independently |
| 4 | Owner + **Incident Triage** (from M3b) | Attended analysis | `agent-out/incident/<id>.json` | Agent unavailable or not yet built → the runbook step from step 2 stands alone |
| 5 | Code | Validates that the cited row ids exist; checks any draft corporate action (section 4.0) | Pass/fail | — |
| 6 | Owner | Fixes the cause: registers a cash event, adopts a trade, commits a corporate-action row, or clears HALT by commit with a written reason | Commit | — |
| 7 | Code | Next run re-reconciles; SAFE clears itself when the cause is gone | RUN | — |

### (f) Owner approvals and overrides

All approvals are owner-authored commits to `config/` or typed confirmations at the terminal. `jarvis release`:
- prints the diff of gate, order-path and `risk.yaml` files with the Reviewer note;
- **refuses** if those files changed and no Reviewer note's `diff_hash` matches the diff;
- compares `risk.yaml` with the previous release using a per-key direction map (which way is "looser"), and for any loosening **sets `effective_after` to release time + 72 hours itself**, ignoring any value in the commit.

The run refuses any config whose `effective_after` is in the future.

| Action | Mechanism | Delay | Notes |
|---|---|---|---|
| Tighten a limit, raise b, create the HALT file | Commit or `New-Item HALT` | Immediate | Only the owner and code write HALT. An agent writes `agent-out/<agent>/REQUEST_HALT`; code promotes it at the next daily or monthly run and emails the owner. A false request costs at most a delayed rebalance |
| Kill / flatten | HALT file plus the Alpaca dashboard or app (cancel all / close) | Immediate, one step | Never delayed (FINRA 15-09). Cancel-all and close exist on the live account (M0 probe P4) |
| Loosen a limit, lower b (more risk), raise `satellite_max` | Commit with templated reason; Reviewer note advisory | `effective_after` = +72 h, set by code | Residual: a loosening can pass without independent review |
| Deviate from a RECOMMEND order | Templated reason in `jarvis adopt` | None (the owner's money) | Counted in the Behaviour Ledger |
| Veto an S-A exit (IRA branch only) | Commit with reason; counterfactual logged | +24 h | — |
| Deposit / withdrawal | `jarvis cash-event` (commit) | Next decision window | Unregistered → SAFE. Dividends and interest need nothing |
| Adopt a manual trade | `jarvis adopt <activity_id>` | Immediate | — |
| Clear HALT | Commit with reason | Next run | Owner only |
| G0 freeze, release, executor go-live | Signed commit plus typed confirmation | — | One three-question pre-mortem (Klein 2007) at executor go-live and at any S-A IRA unlock |

---

## 6. Strategies, universe, benchmark and account layout at launch

**Universe.** Fees and inceptions come from S02 and are mostly from search summaries; each must be re-checked on the issuer page in M0.

| Slot | Trade ticker | Expense ratio | Research proxy before inception | `tax_character` |
|---|---|---|---|---|
| US equity | VTI | 0.03% | none needed (2001) | qualified-dividend equity |
| Developed ex-US | VEA | 0.03% | EFA (2001-08-14, FETCHED-full) | equity |
| Intermediate Treasuries | IEF | 0.15% | none needed (2002) | ordinary interest |
| REITs | VNQ | 0.13% | none needed (2004) | mostly ordinary |
| Gold | GLDM | 0.10% | GLD (2004-11-18), minus 0.30 point a year | **collectible, up to 28% long-term**. Basis: IRS Chief Counsel memo pmta01809 (non-precedential) plus sponsor FAQs; Topic 409 gives the 28% rate |
| T-bill dial | SGOV | 0.09% | FRED TB3MS converted from discount basis (3.72% → 3.81%) | ordinary interest |

- **Gold, not Faber's broad commodities, is a deviation from the published rule.** It is registered as one trial. Gold is a diversification prior, not an evidenced return source (Erb-Harvey 2013).
- **No K-1 funds** in a taxable account. **No managed-futures ETF**: it duplicates S-A's bet at 8-9× the fee.

**Strategies**
- **S0(b), live.** Five risk ETFs at 20% each of the risk sleeve, plus a share b in SGOV.
  - Equal weight is a null, not an optimised or market portfolio. The global market portfolio is far from equal-weight (Doeswijk et al. 2014), and DeMiguel et al. support "do not optimise", not this particular mix.
  - Band: ±20% relative, with a floor of ±3 points of account equity. Frozen; not tuned.
  - Rebalancing comes from contributions (including dividends and interest) first, and band sales only when needed.
  - No drawdown stop: stopping buy-and-hold is market timing.
- **Dial b (S02-P4, DC).** b = max(0, 1 − T / (DD_stress × C)), where T is the dollar tolerance and C is capital.
  - Round b up to the next 10 points. Change it only at a decision window, and only by ≥10 points.
  - Until M4, DD_stress = 50%. This conservative placeholder sits near the roughly 46% five-asset buy-and-hold drawdown in Faber's text.
  - In M4 it becomes the worst peak-to-trough of S0 on the 2004+ proxy history, which includes 2007-2009. If only 2016+ history is available, the 50% placeholder stays.
  - ILLUSTRATIVE: C = $5,000, T = $1,500 gives b = 1 − 1,500/2,500 = 0.40, so 40% SGOV.
- **S0-RM (shadow).** S0 with the b* that matches S-A's backtest volatility. It is the risk-matched null: "less drawdown" can also be bought by simply holding less risk. Until M4 it runs with a labelled placeholder b* equal to S0(b)'s b, and memos show "S0-RM: not yet fitted".
- **S-A (shadow): plain Faber.** Each of the five ETFs is held while its month-end total-return price is above its 10-month SMA, otherwise SGOV.
  - The mechanism prior is time-series momentum, documented mostly on futures (Moskowitz, Ooi, Pedersen 2012; Hurst, Ooi, Pedersen), so transfer to these ETFs is indirect.
  - Conventions frozen at G0: total-return series adjusted as of decision date, the last 10 month-end closes, decision at month-end, fill on the first trading day from 10:30 ET (S01-P4).
  - All 21 rebalance-day offsets are reported (S01-P5; Newfound 2013 on rebalance-timing luck).
  - Shown in the weekly memo as one line, pre-tax and after-tax, with the pre-registered sentence "many exits will look wrong in hindsight".
- **S-A live is allowed only if all of these hold:**
  1. a tax-deferred account exists and its fee is acceptable;
  2. the M4 memo does not fail G1b(ii), gated on **pre-tax** results (the IRA has no tax drag);
  3. it stays at or below `satellite_max` = 25% of total JARVIS capital;
  4. the short G4 in section 8 passes.

**Benchmarks shown to the owner.** S0 is the like-for-like null, not a recommended portfolio. S0-RM is the risk-matched null. A two-fund 60/40 reference (S0-2F) appears only in the quarterly Mission Plan stress table, with no gate.

**Account layout (owner decision, not advice).** v1 runs one account. A static location table sits in the Mission Plan:
1. If an IRA is eligible and its fee is acceptable, it holds the most heavily taxed holdings first (IEF, SGOV, VNQ), in line with the bonds-in-tax-deferred result (Dammon, Spatt, Zhang 2004). S-A goes there first only if it is ever unlocked.
2. Taxable holds the rest, as S0 only, with no harvesting.

**Value of location** (ESTIMATE, ILLUSTRATIVE yields, S03):
- About **$17-44 a year at $10,000 for the core alone**.
- Plus about $13-16 a year **only if S-A goes live in the IRA**, which is not the modal outcome.
- **Capacity.** The $7,500 yearly IRA contribution limit means at most $7,500 of a $10,000 account can sit in an IRA in year one, less if the owner already contributed.
- If two accounts are ever used, they hold disjoint tickers (Rev. Rul. 2008-5). G3 is re-run for any IRA.

**Crypto.** Alpaca spot crypto is unconfirmed for Texas (SNIPPET only; recheck at signup), so it is off. The Mission Plan permission `crypto: none | shadow | capped-ETF` defaults to `none` (section 12).

---

## 7. Risk gate, limits and system states

All values live in `config/risk.yaml`. Unless a source is given, they are DC.

| Control | Starting value |
|---|---|
| Broker side | `no_shorting = true`; margin multiplier 1 (brief 21). Alpaca rejects orders beyond buying power |
| Allow-list | VTI, VEA, IEF, VNQ, GLDM, SGOV (IBIT only if `capped-ETF` is ever enabled) |
| Per-symbol cap | No order may take a holding above 25% of equity (SGOV exempt). Drift above it → alert only |
| Entry notional | ≤ target weight + 5 points of equity, and ≤ 2× the modelled notional |
| Order type and window | Marketable limit only, never market. **Quantity-based** (fractional shares if the M0 probe allows fractional limit orders; otherwise whole shares with the remainder left in SGOV and the tracking error shown). 10:30-15:30 ET; retry 11:30 |
| Limit price | Buy: min(IEX ask × 1.001, collar ceiling). Sell: max(IEX bid × 0.999, collar floor). No fresh quote: prior close × (1 ± 0.005) |
| Collar and quote age | ±1.0% vs an IEX quote no older than 60 s at print time, else ±2.0% vs prior close. SGOV ±0.3% (check distribution dates in M0). A hand order list is valid for 15 minutes after its quote time; after that, `jarvis month --requote` |
| Rate | ≤20 orders a run, ≤40 a day, ≤5 cancels a minute; a breach means HALT (executor only) |
| Minimum order / cash buffer | $20 / 2% |
| Day-loss rule | Account down 5% on the day → no risk-increasing orders that day |
| Tax rules | Defer taxable sales that realise a short-term gain within 30 days of turning long-term; defer collectibles-rate sales the same way; trim non-gold before gold |
| Wash-sale rule (two-way) | **Backward:** no taxable loss sale within 30 days after any purchase of the same or a mapped ticker in any registered account. **Forward:** after any taxable loss sale, no purchase of that or a mapped ticker for 31 days in any registered account; the contribution waterfall skips to the next eligible ETF. Purchases include contribution buys and any dividend reinvestment (DRIP off where the broker allows; M0 probe). Accounts include spouse or 401(k) per `config/external_accounts.yaml` plus a monthly CSV. Block, do not warn |
| Typed rejections | Self-cross, PDT and intraday-margin rejections are never retried |
| Crisis letter | Owner's letter returned by code at account drawdowns of −10%, −20% and −30% |
| S-A (IRA branch only) | `satellite_max` 25%; loss bands at bootstrap p90 (freeze) and p99 (back to shadow); tracking-error check vs replay; lifetime stop at 25% of satellite capital → HALT |

| State | Orders | Entered on | Cleared by |
|---|---|---|---|
| **RUN** | Within the gate | Default | — |
| **SAFE** | **None.** Ping `/fail`, write the bundle, exit | Unexplained reconcile break; foreign order; unregistered deposit or withdrawal; unknown activity type; unexpected broker constraint; uncaught exception | Automatically, on the next run whose reconcile is clean and which completes |
| **HALT** | None (data and shadow NAVs continue) | HALT file; promoted agent `REQUEST_HALT`; rate breach; S-A lifetime stop | Owner commit with a reason |

The residual accepted with SAFE (S09-P4): a sell can wait up to the 5-day window, or the owner sells by hand.

---

## 8. Validation and go-live gates

| Gate | Applies to | Pass rule |
|---|---|---|
| **G0 freeze** | Any strategy | Spec hash committed to `lab/registry.jsonl` before any run; ≤6 cells; owner's signed commit |
| **Harness trust** | Lab, before any result is believed | All tolerances are DC, fixed before the first run. (i) S-A one-way annual turnover on the ETF-era window between 40% and 100% (Faber's text: "almost 70%"). (ii) Mean round trips per asset between 2 and 5 a year (about 3-4 per Faber and brief 18). (iii) Direction: S-A's maximum drawdown below S0's over a window that includes 2007-2009. This needs 2004+ data; without it, (iii) is reported "not testable". (iv) Planted random spec fails; oracle blocked; leak tests green (future-poisoning, shuffled labels, one-bar lag, correlation tripwire; alarm at Sharpe >3). Antonacci's and Faber's long-history figures are not gated. An optional US-equity check on free Ken French monthly data is reported, not gated, and only after its terms are read |
| **M4 decision memo (S-A)** | Whether S-A may ever go live | Pre-registered. Paired block bootstrap on monthly differences, 2004-2026 ETF window with three proxies. **Gates only on G1b(ii), pre-tax:** median all-cost pre-tax CAGR ≥ S0-RM's, at equal or lower p90 maximum drawdown. After-tax results are reported for information. Also reported only: criterion (i), the post-2013 slice, PSR/DSR with raw N, the 21-offset range. Section 1 of the memo states "retire S-A is the modal verdict". Proxies may veto, never rescue. **Inconclusive** (S-A stays shadow) if harness-trust check (iii) is not testable, or if no licensed 2004-2016 source exists by M4 day 2. If the owner has no eligible IRA, the memo is information only and unlocks nothing |
| **RECOMMEND-live (M3)** | S0 by hand | Tickers verified, Mission Plan signed, crisis letter written, 5 clean daily runs, M0 order-entry probes passed. No statistical gate: S0 *is* the null |
| **GF drills** | Executor (M5) | Mock Alpaca: crash between intent and submit; crash after submit; a killed 10:30 run adopted by the 11:30 retry; duplicate id on restart; 5xx/timeout; partial fill plus timeout; stale data; foreign order → SAFE; unregistered deposit → SAFE; dividend credit → no SAFE; HALT file. Plus the failure catalogue (100× notional, unit error, double submit) and one non-gating mutmut pass on the gate diff |
| **G3 paper** | Executor | ≥3 month-end rebalances on paper overlapping shadow (≤1 forced drill); paper balance = real capital; order lists equal shadow targets; zero unexplained breaks |
| **Executor live** | Executor | Tranche 1: run notional ≤25% of equity, with a typed order-list confirmation. Tranche 2 (100%) after one clean live reconcile. Typed confirmation continues for six months |
| **S-A live (IRA)** | S-A | Memo passes pre-tax G1b(ii). Short G4: ≥3 satellite decisions including one change; ≥20 fills counted from the first live S0 fill, with slippage measured by `jarvis adopt` against the printed quote (or the arrival quote from M5); mean one-way cost ≤1.5× model + 1 SE and ≤10 bps; drawdown below bootstrap p95; zero severity-1 incidents. No G5 ladder: `satellite_max` replaces it |
| **Sunset** | S-A live (IRA) | After 24 months, if all-cost **pre-tax** P&L trails the S0-RM shadow with no drawdown benefit → back to S0. Behaviour numbers are reported alongside but do not rescue it |

Not built at launch: ONC, Galwey, PBO, MinBTL as a pass condition, and the 1,000-placebo null. The placebo null returns as a one-off false-pass report only if G1b becomes a real go-live gate. White's Reality Check arrives with the first Lab family of more than 6 variants.

---

## 9. Data, storage, hosting, secrets, monitoring

**Data**
- **Alpaca Basic (free).** IEX real-time, SIP history older than 15 minutes back to about 2016, corporate actions, 200 calls a minute.
- **FRED.** TB3MS and other vintages; a "not endorsed" footer, as the terms require.
- **SEC EDGAR**, only if the Reader is ever enabled: declared User-Agent, ≤10 requests a second.
- **ETF-era history for M4 (2004-2016).**
  - Use Tiingo only if its support confirms personal use and derived storage, and then store only derived monthly returns.
  - Otherwise use issuer NAV history (UNVERIFIED availability).
  - **Pre-stated fallback:** if no licensed pre-2016 source exists by M4 day 2, the memo is inconclusive, S-A stays shadow, and DD_stress keeps its 50% placeholder.
  - `docs/data_licences.md` records each source, its storage right and the date its terms were read.
- No Coinbase, no 1973 proxy ladder, no paid data.

**Storage (all flat files)**

| Path | What it holds |
|---|---|
| `C:\dev\jarvis\` | Code repo: `jarvis/`, `config/`, `schemas/`, `.claude/agents/`, `.claude/skills/`, `docs/` |
| `C:\jarvis-prod\<tag>\` | Release checkout plus its own Python 3.12 venv with a hash-pinned lockfile |
| `C:\jarvis-data\bars\*.parquet` | Price bars, read with DuckDB/pandas |
| `C:\jarvis-data\inbox\` | Activity CSVs the owner downloads |
| `C:\jarvis-data\ledger\` | Clone of the private `jarvis-ledger` repo: `events.jsonl`, `gate_log.jsonl`, `fills.jsonl`, `cash_events.jsonl`, `behaviour.jsonl`, `trust.jsonl`, `costs.jsonl`. Each row has a `prev_hash`. No account numbers or tax ids |
| Monthly local clone | Detects any history rewrite |
| `C:\jarvis-data\reports\`, `incidents\`, `agent-out\<agent>\`, `lab\` | Generated outputs |

**Hosting**
- **The laptop is the v1 host.** Windows Task Scheduler runs the daily check and the Sunday jobs with StartWhenAvailable. No JARVIS server stays resident. The Narrator needs Claude Desktop open and the laptop awake on Sunday afternoon, so free RAM with Desktop open is measured in M0 (O3).
- The entrypoint is host-agnostic. A private GitHub Actions repository (no card, paper key only) is an optional probe and fallback for the key-free daily check, used only after the owner reads the hosted-runner clause.

**Secrets**
- Paper key and the notification mailbox password live in Windows Credential Manager.
- **The live key is never stored.**
  - In RECOMMEND mode, JARVIS reads the broker's activity CSV, so no live key is needed at all if CSV export exists (M0 probe P5).
  - **Key exceptions, pre-stated.** If no CSV export exists, the owner types the live key for read-only GET calls in a terminal with no Claude session. If the live account has no manual order-entry UI (probe P4), RECOMMEND cannot be placed by hand, and the M5 attended executor (typed key, no Claude session) becomes required before any real money.
  - In M5 the owner types the key in a terminal with no Claude session. The RECOMMEND build contains no order-submit code (a CI test fails on `POST /v2/orders` outside `jarvis/orders/`).
- Other protections: BitLocker; gitleaks pre-commit; MFA on Alpaca, GitHub and email; a passphrase on the owner's SSH key, typed per push for config and release.
- The ledger repo uses a deploy key scoped to that one repo.
- **First action:** revoke the OpenAI key committed in v1 and make the Hugging Face Space private.
- **Named residuals:**
  - The Alpaca live key is unscoped (no read-only key exists).
  - Any process running as the owner user, including a Builder session, can read the paper key and the mailbox password.
  - A reviewed but malicious release could misuse a typed key.

**Monitoring.** Healthchecks free tier with two checks:
- **A:** a ping on each daily run; 1-week period, 1-day grace.
- **B:** "decision recorded"; a simple 31-day period with 7 days' grace (DC), because Healthchecks cannot express "trading day 8". The laptop's own `MISSED_REBALANCE` email on trading day 6 is the first alert; B is the off-laptop backstop.

Pings carry status codes only. Exception email comes from a dedicated sending-only mailbox, hard-coded to the owner's address. Expect about 2 actionable alerts a month, each with a runbook line.

---

## 10. Budget

| Line | Amount |
|---|---|
| Anthropic API (metered) | **$0**. No key exists; usage credits and overage stay **off** |
| Claude subscription | Already paid (sunk); JARVIS adds plan usage, not dollars. Tier recorded in M0 (O15) |
| Alpaca account, Basic data, commissions | $0 |
| FRED, EDGAR, Healthchecks free, GitHub private repo | $0 |
| Tiingo | $0 (never Power at $30 a month: fails the 600× rule) |
| Laptop power | **$0 incremental**. Brief 23's $2.64 a month assumed an always-on 20 W laptop; JARVIS runs only short jobs on a laptop already in use |
| **Total metered spend** | **$0.00 a month** |
| Holding cost (not JARVIS) | ETF fees about 0.088% a year (about $0.88-$8.80 a year); spreads a few bps per trade |
| Open costs, optional | Alpaca IRA fee (unknown; M0 question O7; a $10 fee is 1% of $1,000). Tax-professional consult (price unknown; optional while JARVIS is S0-only) |

**Plan usage** (ESTIMATE; dollar figures are API-equivalent and do not map to plan quota)

| Consumer | Share | Notes |
|---|---|---|
| Builder sessions | Most of it | Build months dominate; the consumer most likely to trip a limit |
| Narrator | At least about 68k input tokens a month | Memo payload only (15.6k × 4.33). Harness overhead and repair passes are unmeasured; measured in M2. API-equivalent about $0.25 a month |
| Reader, if enabled | About 0.46-0.59M input tokens a month | With the Narrator, about $1.5-2 a month API-equivalent (S06) |
| Reviewer, Lab, Ledger Analyst, Incident Triage, Change-Watch | Small and episodic | — |

**When limits are hit** (pre-registered):
1. A scheduled task that hits the limit skips, and the template memo ships with identical numbers. Trading is unaffected.
2. Builder sessions follow session hygiene: one milestone task per session, focused subagent prompts, and no Builder session on Sunday afternoon (Narrator slot).
3. If the limit trips twice in a month, read `ops/plan_usage.csv` to see which consumer caused it. If scheduled agents caused it: the Reader (if on) drops to every other week, then the Narrator drops to monthly. If the Builder caused it: the stall days are logged, and the stop-rule dates in section 11 move by the logged days, up to the stated caps.
4. Usage is logged for the first four weeks before any agent is added. The decision on whether the plan supports the full roster is made from that log before M3.

With no metered spend, there is no spend cap to hit.

---

## 11. Build workflow

Assumes 2.5 dev-days a week (15 hours; the owner's real hours are unknown, O10). **All efforts are unvalidated planning estimates**: a bottom-up sum of the architect's own task estimates, with no reference class behind them. Calendars include a 1.3-1.5× allowance for plan-limit stalls. Anything not needed for the next milestone goes to `BACKLOG.md`.

| Phase | Tasks | Who | Exit test | Effort | Calendar |
|---|---|---|---|---|---|
| **M0 Foundations** | Revoke v1 key; MFA, BitLocker; Alpaca account and paper key; repo plus gitleaks; Builder definition (`CLAUDE.md`, `builder.md`); record plan tier and one week of baseline usage. **Probes:** P1 paper order round trip; P2 fractional on 6 tickers; P3 fractional limit by quantity vs notional with limit (paper, and live UI if possible); P4 manual order entry, cancel-all and close-position on the live account (web dashboard or app); P5 activity CSV export and its activity-type labels (DIV, INT, FEE, deposits); P6 lot method and DRIP setting; P7 `GET /v2/assets/IBIT`; P8 market data on paper key; P9 Desktop task restriction (deny-unlisted, write-only folder), wake, and model/effort pinning; P10 RAM with Desktop open. **Emails (week 1):** Alpaca (IRA eligibility and fee, lot method, IBIT in IRA, hosting); Tiingo (personal use, derived storage). **Owner reads by eye:** Consumer Terms provisions 7 and 9 plus the training setting, then applies the section 4 decision rule; Tiingo ToS 1.6/5.2/7.3; GitHub runner clause. Verify tickers on issuer pages. Write owner charter, crisis letter, Mission Plan inputs, `docs/tax_questions.md` | Builder (attended) + owner | `docs/probes.md`: every item pass, fail, or fallback chosen; terms decision recorded; order-placement method fixed (fractional limit, or whole-share fallback) | 3-4 | Weeks 1-2(3) |
| **M1 Shadow slice** | `jarvis` package; `universe.yaml` with `tax_character`; Alpaca ingest; trust gate; AsOfSnapshot; S0(b), S0-RM (labelled placeholder b*), S-A shadow; JSONL ledger in git; daily check with outage and HALT handling; Healthchecks A; exception mail; monthly shadow email (template); leak tests; v1 TSLA post-mortem; Reviewer agent file and 8 seeded defects; `jarvis release` with Reviewer-hash check and loosening detection | Builder; Reviewer on risky diffs | 5 clean daily runs and the first shadow email; Reviewer seeded-defect score recorded | 8-10 | Weeks 3-6(8) |
| **M2 Narrator** | `facts.json` with `not_yet_available` defaults; Narrator agent, skill and schema (`action_ids` enum); `jarvis validate-memo` (numbers, enums, denylist); template; Desktop task with permission recipe and pinned model if P9 allows; advice-leak set; Ledger Analyst `/ask-ledger` over the shadow ledger; Narrator usage measured | Builder; advice-leak run attended | 2 consecutive memos validated unaided, with unbuilt fields shown as "not yet available"; red-line subset 100%; usage logged | 5-7 | Weeks 6-9(11) |
| **M3 RECOMMEND-live** (**first real money**) | `jarvis month` (atomic output, `--requote`), combine (waterfall, two-way wash-sale), gate in recommend mode, order email (quantity, limit, quote time, valid-until); activity-CSV import; reconcile with activity-type classification; `jarvis adopt` (with slippage vs printed quote) and `cash-event`; `REQUEST_HALT` promotion; Behaviour Ledger v0 (adherence, deviations, plan minus actual, MWR − TWR; baseline import of 12-24 months optional); crisis-letter trigger; Healthchecks B; code-only incident bundle with runbook step; first-deployment run | Builder; Reviewer | One real month-end: orders emailed, placed by the owner, fills adopted, reconcile clean, **and a dividend or interest credit classified without SAFE** (from a real credit, or from the M0 CSV sample if none has arrived) | 6-8 | Code by month 2-3; then wait for the first real month-end |
| **M3b Event agents** (during the month-end wait or just after) | Incident Triage agent and schema with corporate-action checks; page-hash job and Change-Watch; `jarvis whatif` and `/whatif` | Builder; Reviewer | Each agent passes one replayed fixture: a planted SAFE bundle, a planted page diff, a `whatif` with a known answer | 3-4 | About month 3-4 |
| **M4 Decision memo** | `jarvis-lab run` single entry with raw N; PSR/DSR (unit test: N = 46 gives 0.9505); pre-2016 source decided by day 2; 2004+ monthly total-return series with GLD/EFA/TB3MS proxies; costs, lag, 21 offsets; pre-tax and coarse FIFO after-tax columns; S0-RM b* fit replaces the placeholder; paired bootstrap; planted random spec and oracle; Replication Analyst report against the section 8 tolerances; memo; DD_stress → dial; location table | Strategy Lab (Spec Clerk, Replication Analyst); Reviewer; owner signs | Memo committed and signed (pass, fail or inconclusive); harness-trust checks (i), (ii), (iv) green | 12-16 | About months 4-6 |
| **Month-4 checkpoint** | Owner decides on M5 using the Behaviour Ledger (section 12 trigger); adds agent memory files if failures recur; reviews `ops/plan_usage.csv` | Owner | Decision logged | — | Month 4-5 |
| **M5 Attended executor** (optional) | Brief 04's 5-day spike (order service plus mock broker plus crash drills; if it fails, stop and stay RECOMMEND); default-deny gate; idempotent orders; reconcile-on-start; HALT; failure catalogue; GF; G3 paper ×3; two tranches | Builder; Reviewer on every diff | GF plus G3 pass, then tranche 1 | 20-28 | About months 5-9, live about 10-11 |

**Totals** (unvalidated planning estimate): v1 complete (M0-M4 with M3b) about **37-49 dev-days** (3+8+5+6+3+12 = 37; 4+10+7+8+4+16 = 49); with M5, **57-77**.

**Stop rules (the commitment)**
- If M3 is not done by **month 3.5, plus logged plan-limit stall days, capped at month 4.5**: stop adding features. JARVIS stays an emailed shadow plan, and the owner holds S0 by hand.
- If the executor has not passed GF and G3 by **month 10, plus logged stall days, capped at month 12**: RECOMMEND becomes the permanent product.

---

## 12. Growth path with explicit triggers

| Unlock | Trigger | Honest outlook |
|---|---|---|
| Attended executor (M5) | Month-4 checkpoint: **any costly deviation** in the Behaviour Ledger (plan-minus-actual worse than max($25, 0.25% of equity) at the next month-end, DC), **or** the owner chooses end-to-end. The adherence percentage is reported only once 4 or more decisions exist; by month 4 there are only 1-2 | Reachable; about 20-28 dev-days |
| Unattended executor wrapper | 6 clean attended live months **and** a measured adherence reason **and** a key-at-rest design reviewed (Logon-as-Batch, DPAPI probes) | Distant by design |
| S-A live in an IRA | IRA eligible; fee acceptable (a $10 fee is 1% of $1,000); M4 memo does not fail pre-tax G1b(ii); short G4; `satellite_max` 25% | Possible; modal verdict is retire |
| Watchlist Digest (code-only) | After M4, owner opts in; forward-logged watch outcomes | Cheap; informational only |
| LLM Reader | Digest has run 8 weeks and the owner asks for summaries; open rate reported, not gating; plan-usage rule holds | Owner's choice; A1 forward ladder declared unreachable |
| Owner Idea Journal | Owner asks; ideas file, forward scoring, hit rate with CI; Brier score after about 30 ideas | Cheap; efficacy unverified |
| ML lane (LightGBM, v1 heritage) | After M4's harness and live S0, with spare plan capacity. 5-dev-day time-box. Baselines: expanding mean, SMA signal, 12-month sign; logistic regression co-primary; expanding walk-forward; stable-SHAP display only | Pre-registered "no skill demonstrated" is the likely label. Published ML gains used about 30,000 stocks over 60 years (Gu-Kelly-Xiu 2020; sample size from a snippet); JARVIS has about 1,300 rows |
| Crypto shadow column | After M4, if IBIT is tradable: static S0 + 2.5% / 5% IBIT rows in the monthly report and quarterly stress table, from Alpaca bars | Visible, zero money |
| Capped BTC-ETF (`capped-ETF`) | 6 clean live S0 rebalances; IBIT probe; owner signs a dollar stress loss (−75% of a 5% sleeve = 3.75% of the account); BTC only; buy at windows; no signal exit; trim only lots held over 1 year; alert at 8% | Owner's risk choice |
| Tax-loss harvesting executor | Taxable capital above $5,000 **and** two years of the loss line showing ≥0.30% of capital a year | Likely never ($3-10 a year at $5,000, ESTIMATE) |
| White's Reality Check | First Lab family with more than 6 variants | When needed |
| GitHub Actions host | Owner reads the runner clause; 8-10 logged runs on time | Optional |
| US VM ($0-6 a month) | More than 2 missed runs in a month, after Alpaca confirms server hosting in writing | Only if needed |
| Norgate single stocks, SIP data, shorting, Kelly sizing | $31,500+ / $59,400+ capital; 300+ outcomes | Never within $10,000 |

---

## 13. Mapping of the owner's original ideas

The full 72-row ledger in `FINAL-design.md` section 10 still holds, except where this table changes a verdict.

| Owner idea (v1/v2/v3) | Verdict | Reason |
|---|---|---|
| Never chase a target; FLAT is valid; goal never changes risk | **Kept** | Briefs 09, 11 |
| Agents reason, deterministic rules hold the money | **Kept**, with the three Claude-to-order channels listed and controlled (section 4.0) | Briefs 01-03, 12; S04 |
| Claude agents as a team | **Changed**: 6 roles / 8 agents, off the runtime order path, each shipping a checked artifact | MAST taxonomy; Anthropic; S06 |
| Goal & Capital Planner, "simple plan" | **Kept** as the Mission Plan with a dollar-loss dial | S02-P4 |
| Opportunity scanner, ranked opportunities | **Deferred** to the opt-in digest and Idea Journal | No consumer on an ETF book (S04-P7, S05-P6) |
| Data trust gate, quorum | **Changed**: Alpaca-only checks; second vendor optional | Tiingo licence (S10) |
| Point-in-time data, event vs ingest time | **Kept** | Briefs 06, 14 |
| Regime HMM, GARCH, jump, ensemble | **Deferred / dropped** | Leaks and no validation data (brief 15) |
| XGBoost/LightGBM, SHAP (v1 heritage) | **Deferred** to the 5-day lane; v1 leak post-mortem in M1 | Welch-Goyal; Gu-Kelly-Xiu; S10 |
| News/FinBERT/social sentiment, CAR | **Dropped** (Reader dormant) | Briefs 15, 16 |
| Bull/Bear debate | **Changed** to the Reviewer | Brief 02 |
| Confidence Calibrator, overall score | **Dropped**; uncombined evidence panel | A pooled score needs its own outcome data to calibrate (Ranjan-Gneiting; brief 10) |
| Strategy Lab: LLM proposes, validation decides | **Kept**, with raw trial count, funnel, replication first; `llm_origin` ideas reach shadow only | Gencay; S05 |
| Capital Governor, kill switch, no LLM override | **Kept** (smallest form) | SEC Knight; FINRA 15-09 |
| Fractional Kelly | **Dropped** at this size | Brief 10 |
| Risk-of-ruin | **Changed** to a dollar stress loss and crisis letter | S02, S04 |
| LONG/SHORT/FLAT | **Changed** to long/flat | Briefs 05, 21 |
| Position manager, confidence-drop exits | **Changed** to month-end rules | Brief 17 |
| Execution engine, paper then live | **Changed**: RECOMMEND-live first; attended executor optional | S04-P6, S09-P9 |
| Professional ledger, 17 fields, attribution | **Kept** (JSONL in git; trade-log mapping unchanged) | S09-P7 |
| Learning / adaptation | **Changed**: Lab plus pre-registered refits; no online learning | Brief 08 |
| Permission modes (recommend / paper / act) | **Kept**; RECOMMEND is the launch mode | v2 |
| Human approval for exceptions | **Kept** via commits, with `effective_after` set by code | S09-P3 |
| Degraded-data override | **Dropped** | Brief 12 |
| Crypto, Coinbase second broker | **Deferred** (static BTC-ETF ≤5%) / **dropped** | S08; brief 11 |
| Order flow, L2, intraday, multi-horizon | **Dropped** | Briefs 06, 07, 09 |
| Manipulation surveillance | **Dropped as written**; move quarantine kept | Brief 07 |
| Fundamental/macro, 13F, options, RL | **Deferred / dropped** | No consumer; brief 15 |
| Docker, Redis, Postgres, LangGraph, MLflow, Grafana, React | **Dropped**; flat files and a static page | 8 GB RAM (brief 14) |
| Dashboard, trade email, daily summary | **Changed**: static weekly page, order email, exception-only daily mail | S04-P2 |
| "Investor view" | **Changed** to owner-only | Legal perimeter (brief 12) |
| Build on current JARVIS | **Changed**: rebuild; ideas salvaged; leak post-mortem | Context section A |
| $100 BTC worked example | **Dropped** | Costs 33-113% of upside (brief 11) |

---

## 14. Decision record

Votes are shown as accept/modify/reject (A/M/R) from the four panel seats: budget hawk, owner-vision advocate, risk sceptic and solo pragmatist.

**Adopted as proposed (unanimous):** S01-P2, P4, P5; S02-P1, P5; S03-P3, P6; S05-P2; S06-P3, P5, P7, P11 (P11 as an interpretation the owner confirms; section 4); S07-P1, P3; S08-P5; S09-P4, P6, P8; S10-P6.

| # | Proposal | A/M/R | Choice and reason |
|---|---|---|---|
| D1 | S01-P1 no live taxable satellite | 2/2/0 | **Adopted.** S-A shadow; live only in an IRA under `satellite_max` 25% after the memo. Dropped the "$575 vs $450" line, which omits the equity premium (sceptic) |
| D2 | S01-P3 scale the harness | 2/2/0 | **Adopted, modified:** PSR/DSR built now with raw N; MinBTL/PBO/ONC deferred; ETF-era window only; verdict is a signed memo |
| D3 | S01-P6 alternatives / vote variant | 0/4/0 | No Keller or dual momentum; **no** 6/9/12 vote shadow at launch; it may be a later Lab spec |
| D4 | S01-P7 / S10-P7 ML lane timing | 2/2/0 ; 3/1/0 | Both hold in sequence: deferred until after M4 and live S0, then a 5-day time-box |
| D5 | S01-P8 exit-regret view | 3/0/1 | **Folded** into one pre-registered sentence on the S-A shadow line. The sceptic's evidence (more feedback → more trading) outweighs a separate display |
| D6 | S02-P2 / S10-P3 proxies, history | 1/3/0 ; 0/4/0 | Three proxies (GLD, EFA, TB3MS converted), 2004+; veto-never-rescue; **no 1973 ladder** (unread licences, no consumer). Long-history claims are therefore not gated (V1) |
| D7 | S02-P3 S0-2F | 1/2/1 | Quarterly stress table only; no weekly number, no gate |
| D8 | S02-P4 dial | 2/2/0 | Stress-loss formula; worst historical drawdown only (no bootstrap); placeholder 50% until M4, kept if only 2016+ history exists |
| D9 | S02-P6 10:30 start | 3/1/0 | Config default (DC); slippage logs from M3 hand fills, then M5, confirm it |
| D10 | S03-P1 harvesting | 1/3/0 | No executor, no simulator event; one information line in the order email |
| D11 | S03-P2 location | 1/3/0 | Static table in the Mission Plan; capacity bound stated; core-only value separated from the S-A part (section 17, E3); owner decision |
| D12 | S03-P4 FIFO | 3/1/0 | FIFO default; coarse estimator with a short-term-share range, not a lot engine |
| D13 | S03-P5 wash-sale | 1/3/0 | One blocking rule, now two-way; hand-kept external accounts file plus CSV |
| D14 | S03-P7 / S03-P8 | 3/1/0 ; 0/4/0 | No IRA → S-A never live. Question list now; consult optional while S0-only; two tax defects in the Reviewer set and as unit tests |
| D15 | S04-P1 Behaviour Ledger | 1/3/0 | Three code numbers plus MWR − TWR; baseline import optional; **sunset stays P&L-based** (pre-tax in the IRA) |
| D16 | S04-P2 exception-only mail | 3/1/0 | Adopted, plus a code-built "agent desk" block in the weekly memo so a quiet system does not read as dead |
| D17 | S04-P3 veto friction | 0/4/0 | Templated reason plus 24 h via `effective_after`, only for S-A exit vetoes; risk-raising dial changes follow the 72 h loosen rule; never on kill or flatten |
| D18 | S04-P4 crisis letter | 2/2/0 | Letter returned by code; pre-mortems only at executor go-live and any S-A unlock |
| D19 | S04-P5 never-do list | 1/3/0 | Prompt text plus denylist plus attended 30-prompt set; called a smoke test; rerun on any model change |
| D20 | S06-P8 memory files | 1/1/2 | **Not at launch**; added on 3 recurring failures or at the month-4 checkpoint; code-appended only |
| D21 | S04-P6 vs S09-P9 executor timing | 2/2/0 ; 0/4/0 | Sequenced: RECOMMEND-live at M3; attended executor at the month-4 checkpoint on any costly deviation **or the owner's wish** (all four seats allowed the last). The adherence percentage gates nothing until 4+ decisions exist (section 17) |
| D22 | S04-P7 / S05-P6 digest and Reader | 2/2/0 ; 1/3/0 | No digest at launch; code-only digest opt-in after M4; LLM Reader on owner request after 8 weeks (open rate reported, not gating). Meets the advocate halfway at $0 metered |
| D23 | S05-P1 raw N | 3/1/0 | One entry point built in M4 with the harness, not before |
| D24 | S05-P3 funnel | 1/3/0 | Template plus JSON contract plus git-hashed registry; labelled a soft control (DC) |
| D25 | S05-P4 llm_origin | 3/1/0 | Cited source plus ×2 trials. **`llm_origin` specs reach shadow only**; live eligibility needs owner re-registration as an owner-origin spec after ≥12 forward decisions, with a new G0 counted as a new trial (V2). Residual: memorised-history selection (Lopez-Lira, Tang, Zhu) |
| D26 | S05-P5 replication first | 3/1/0 | Replication Analyst and Spec Clerk as Lab modes; targets are the ETF-era-checkable Faber claims with numeric tolerances (V1) |
| D27 | S05-P7 Lab cap | 2/2/0 | Expected yield near zero; **no** session cap; maintenance mode at N = 50 |
| D28 | S05-P8 Reviewer | 2/2/0 | Advisory, fed code diagnostics; `jarvis release` enforces that a note exists; the loosening control is code-set 72 h, not the Reviewer |
| D29 | S06-P1 subscription only | 3/1/0 | Adopted with the sceptic's conditions: terms read in M0 with a decision rule, usage measured, template default |
| D30 | S06-P2 / S06-P6 surfaces and recipe | 2/2/0 ; 2/2/0 | No cloud routine. One page per scheduled task; M0 probe; if it cannot be restricted, the Narrator becomes an attended weekly command |
| D31 | S06-P4 roster size | 2/2/0 | Six roles, eight named definitions (advocate, sceptic); Reader dormant (hawk) |
| D32 | S06-P9 seeded defects | 3/1/0 | 8 seeded defects including 2 tax; sanity bar 5 of 8, advisory, wide interval; fewer than 4 → owner checklist |
| D33 | S06-P10 Reader evaluation | 2/2/0 | 30-item spot check at enablement; A1 declared unreachable; forward logging kept |
| D34 | S07-P2 G1b(ii) only | 3/1/0 | As a decision memo; pre-tax for the IRA path; retire is the modal verdict |
| D35 | S07-P4 short ladder | 0/4/0 | Applies only to S-A live in an IRA |
| D36 | S07-P5 tranches | 2/2/0 | Two tranches with typed confirmation; in RECOMMEND mode the owner's deposits are the ladder |
| D37 | S07-P6 placebo null | 0/2/2 | Not built; returns as a one-off report if G1b becomes a real go-live gate |
| D38 | S08-P1 Texas crypto | 3/1/0 | "Unconfirmed; recheck at signup"; stop lifecycle deleted |
| D39 | S08-P2 crypto shadow | 1/2/1 | No Coinbase, no Donchian family; static IBIT rows after M4 if tradable, in the monthly report (not the weekly memo, against FOMO) |
| D40 | S08-P3 / S08-P4 | 2/2/0 ; 2/2/0 | Static BTC-only 5% rule as text; permission default `none`; build nothing until the triggers; IBIT probe and Alpaca question in M0 |
| D41 | S09-P1 hosting | 0/4/0 | Laptop is the v1 host; entrypoint host-agnostic; Actions optional for key-free work after the clause is read; live key never in GitHub |
| D42 | S09-P2 accounts | 2/2/0 | No live key where the Builder runs; release from tagged checkout with its own venv; owner reads gate, order and config diffs; Reviewer checks them; no second prod repo until unattended |
| D43 | S09-P3 approvals | 1/3/0 | Host-neutral commits; `effective_after` set by code for loosenings; typed confirmation; passphrase per push; no workflow_dispatch dependence |
| D44 | S09-P5 tests | 3/1/0 | Failure catalogue, property tests and drills; one non-gating mutmut pass |
| D45 | S09-P7 ledger | 2/2/0 | JSONL with `prev_hash` in private git (pragmatist, sceptic); local clone; no SQLite cache; no identifiers |
| D46 | S10-P1 / S10-P2 data | 1/3/0 ; 3/1/0 | Alpaca-only daily gate; Tiingo nothing stored except derived returns if confirmed; licence file; owner reads the terms; pre-stated fallback if no pre-2016 source |
| D47 | S10-P4 / S10-P5 / S10-P8 | 1/0/3 ; 3/1/0 ; 1/3/0 | All become text in the deferred ML spec; no proxy-panel training; no SHAP in the memo until built and stable |

**Panel additions adopted:** scope lock and stop rules; milestone ladder; the meaningfulness test; agent files plus schemas instead of a framework; the plan-usage log; static report page; owner charter; claims register; terms reading list; typed order-list confirmation; attended-before-unattended; `/whatif`; v1 post-mortem; week-1 emails.

**Not adopted:** GitHub Issues as the notification channel (the laptop host uses email); the weekly Opportunity Board (deferred with the digest); dropping the prev-hash (kept: about 10 lines, and it detects a rewrite even in a local clone).

**Verification round decisions (V).** All eleven must-fix findings were accepted; section 17 logs them. Where a fix was applied in a modified form, the reason is below.

| # | Finding | Choice and reason |
|---|---|---|
| V1 | Replication gate unpassable on ETF-era data | Accepted. Gate limited to turnover, round trips and drawdown direction, with numbers. Free Ken French data is **reported only**, not gated: reading its terms and building a second pipeline buys nothing the decision needs |
| V2 | `llm_origin` contradiction | Accepted the verifier's recommended option (shadow only; owner re-registration). Kept ×2 trial counting so the raw N stays honest |
| V3 | Corporate-action draft must also match the vendor feed | **Accepted with a modification.** A draft usually exists *because* the vendor feed lacked the action, so requiring a match at drafting time would be circular. Instead the row takes effect only once the vendor feed lists it (normally within days); until then the symbol stays untrusted for buys, which is the safe direction. Sells are unaffected |
| V4 | Degrade rule drops scheduled agents while the Builder trips the limit | **Partly accepted.** Scheduled agents are tiny and have a template fallback, so dropping them first costs little. The fix is to diagnose from the usage log, add Builder session hygiene, and let Builder stalls move stop-rule dates up to a cap, rather than cutting the Builder |
| V5 | Reviewer "expect 5 of 8" | Accepted. Restated as an advisory sanity bar with a consequence (owner checklist below 4). The hawk's view that no seeded bar is needed is recorded as unresolved |

---

## 15. Open items

| # | Item | Who settles it |
|---|---|---|
| O1 | Market data with the paper key; fractional for all 6 tickers; activity CSV export and activity-type labels; Alpaca lot method and DRIP; SGOV distribution dates; IBIT tradable | M0 probes P1, P2, P5-P8 |
| O2 | Desktop scheduled task: can it run deny-unlisted, write only to one folder, wake reliably, and **pin model id and effort**? | M0 probe P9; fallback is an attended weekly command, and an unpinned model triggers the advice-leak rerun on change |
| O3 | Free RAM during a run with Claude Desktop open (8 GB) | M0 measurement P10 |
| O4 | Anthropic Consumer Terms provisions 7 and 9; consumer-plan training setting before ledger numbers go to Claude. The scheduler route is an S06 interpretation, not a confirmed term | Owner reads directly in M0 and applies the section 4 decision rule |
| O5 | Tiingo: personal use and derived storage | Owner reads ToS 1.6/5.2/7.3; email support |
| O6 | Source of 2004-2016 monthly total returns if Tiingo says no | M4 day 2; otherwise the memo is inconclusive (pre-stated) |
| O7 | Alpaca IRA eligibility, **fee**, settlement rules, IBIT in IRA; written view on server hosting | Alpaca email (week 1); owner eligibility |
| O8 | Ticker fees and inceptions (VEA 2007 RECALLED; most from search summaries) | Issuer pages, M0 |
| O9 | Gold ETF as a 28% collectible; "substantially identical" ETF pairs; 401(k) wash sales; Roth vs Traditional; Texas has no state income tax (medium confidence) | Tax professional (optional while S0-only) |
| O10 | The owner's weekly hours | Owner; re-plan section 11 |
| O11 | Dollar loss tolerance, horizon, liquidity before 59½, crisis letter, external accounts list, `first_deploy_windows` | Owner, M0 |
| O12 | Hugging Face Space visibility; v1 key usage review | Owner |
| O13 | Gencay 2026 numbers beyond the abstract; Faber drawdown figures | Re-read in the PDF before quoting them to the owner (claims register) |
| O14 | GitHub hosted-runner clause, only if Actions is used | Owner |
| O15 | Claude plan tier and baseline weekly usage | Owner records in M0; reviewed before M3 |
| O16 | Live-account order mechanics: manual order entry, cancel-all and close in the web dashboard or app; fractional limit orders by quantity vs notional | M0 probes P3, P4. If fractional limit is not allowed: whole-share limits with remainder in SGOV. If no manual entry exists: the key exception in section 9 |

---

## 16. References

Only sources cited in the body are listed. Read-depth tags: **FETCHED-full**, **FETCHED-abstract**, **FETCHED-summariser**, **SECONDARY**, **SNIPPET**, **RECALLED** (defined at the top). "Brief NN" sources not listed here are in that brief.

**Trend, allocation and portfolio construction**

| Source | URL | Tag |
|---|---|---|
| Faber, A Quantitative Approach to Tactical Asset Allocation (2007/2013) | https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf | FETCHED-full (text; tables are images) |
| Antonacci, Absolute Momentum (2014) | https://c.mql5.com/forextsd/forum/207/Absolute%20Momentum%20-%20A%20Simple%20Rule-Based%20Strategy%20and%20Universal%20Trend-Following%20Overlay.pdf | FETCHED-full (S01) |
| Moskowitz, Ooi, Pedersen, Time Series Momentum, JFE 2012 | https://w4.stern.nyu.edu/facdir/lpederse/papers/TimeSeriesMomentum.pdf | FETCHED (S01; depth not recorded) |
| Hurst, Ooi, Pedersen, A Century of Evidence on Trend-Following | https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing | FETCHED (S01; depth not recorded) |
| Huang, Li, Wang, Zhou, JFE 2020 | https://ideas.repec.org/a/eee/jfinec/v135y2020i3p774-794.html | FETCHED-abstract |
| Zakamulin, moving-average timing (2018) | https://c.mql5.com/forextsd/forum/205/Revisiting%20the%20Profitability%20of%20Market%20Timing%20with%20Moving%20Averages__1.pdf | SECONDARY (S01 read a summary) |
| Newfound, The Luck of the Rebalance Timing (2013) | https://blog.thinknewfound.com/2013/08/the-luck-of-the-rebalance-timing/ | FETCHED-full (blog) |
| DeMiguel, Garlappi, Uppal, RFS 2009 | https://ideas.repec.org/a/oup/rfinst/v22y2009i5p1915-1953.html | FETCHED-abstract |
| Doeswijk, Lam, Swinkels, FAJ 2014 | https://ideas.repec.org/a/taf/ufajxx/v70y2014i2p26-41.html | FETCHED-abstract |
| Jaconetti, Kinniry, Zilbering, Vanguard 2010 | https://www.aaii.com/files/journal/pdf/best-practices-for-portfolio-rebalancing.pdf | SNIPPET (search summary) |
| Daryanani, JFP 2008 | https://www.financialplanningassociation.org/article/journal/JAN08-opportunistic-rebalancing-new-paradigm-wealth-managers | FETCHED-abstract |
| Berkin and Ye, FAJ 2003 | https://ideas.repec.org/a/taf/ufajxx/v59y2003i4p91-102.html | FETCHED-abstract |
| Erb and Harvey, The Golden Dilemma | https://www.nber.org/papers/w18706 | FETCHED-abstract |
| Dimensional, European ETF market | https://www.dimensional.com/gb-en/insights/overview-of-the-european-etf-market | FETCHED-full (indirect: European data) |

**Tax**

| Source | URL | Tag |
|---|---|---|
| IRS Topic 409 (28% collectibles rate) | https://www.irs.gov/taxtopics/tc409 | FETCHED-full (names coins and art, not ETFs) |
| IRS Chief Counsel memo, physical-metal ETFs | https://www.irs.gov/pub/lanoa/pmta01809_7431.pdf | FETCHED-full (non-precedential) |
| IRS Pub. 550; Pub. 590-B | https://www.irs.gov/publications/p550 | FETCHED-summariser |
| Rev. Rul. 2008-5 | https://www.irs.gov/irb/2008-03_IRB | FETCHED-full |
| Dammon, Spatt, Zhang, J. Finance 2004 | https://www.sec.gov/news/speech/spch010705cs.htm | SECONDARY (SEC speech); paper RECALLED |
| Alpaca IRA announcement; forum FIFO reply | https://alpaca.markets/blog/alpaca-introduces-individual-retirement-accounts-for-trading-api-users/ | FETCHED-full (forum is not official docs) |

**Behaviour and LLM advice**

| Source | URL | Tag |
|---|---|---|
| Barber and Odean, J. Finance 2000 | https://ideas.repec.org/a/bla/jfinan/v55y2000i2p773-806.html | FETCHED-abstract |
| Odean, J. Finance 1998 | https://faculty.haas.berkeley.edu/odean/papers/disposition/disposition.html | FETCHED (depth not recorded) |
| D'Acunto, Prabhala, Rossi, RFS 2019 | https://ideas.repec.org/a/oup/rfinst/v32y2019i5p1983-2020..html | FETCHED-abstract |
| Thaler and Benartzi, JPE 2004 | https://ideas.repec.org/a/ucp/jpolec/v112y2004is1ps164-s187.html | FETCHED-abstract |
| Bhattacharya et al., RFS 2012 | https://ideas.repec.org/a/oup/rfinst/v25y2012i4p975-1032.html | FETCHED-abstract |
| Sicherman et al., RFS 2016 | https://ideas.repec.org/a/oup/rfinst/v29y2016i4p863-897..html | FETCHED-abstract |
| Morningstar, Mind the Gap 2025 | https://www.morningstar.com/en-us/business/insights/research/mind-the-gap | SNIPPET |
| Vanguard behavioural coaching (InvestmentNews) | https://investmentnews.com/practice-management/advisors-continue-to-shine-as-emotional-circuit-breakers-vanguard-says/259609 | SECONDARY |
| Winder, Hildebrand, Hartmann, PLOS ONE 2025 | https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0325459 | FETCHED (S04; depth not recorded; older models) |
| Lee et al. 2025 | https://arxiv.org/abs/2507.20957 | FETCHED-abstract (older models) |
| Zhi et al. 2025 | https://arxiv.org/html/2503.08750v1 | FETCHED-abstract re-checked (names no models; S04's model list is not in the abstract) |
| Sharma et al., sycophancy, ICLR 2024 | https://arxiv.org/abs/2310.13548 | FETCHED-abstract |
| Klein, Performing a Project Premortem, HBR 2007 | https://glenbrook.com/?p=588 | FETCHED (partial) |

**LLM trading, research agents and evaluation statistics**

| Source | URL | Tag |
|---|---|---|
| FINSABER | https://arxiv.org/html/2505.07078 | FETCHED (brief 01; long, pre-cutoff) |
| StockBench | https://arxiv.org/html/2510.02209 | FETCHED (brief 01; 82 days) |
| CLQT | https://arxiv.org/abs/2606.29771 | FETCHED-abstract only (brief 01, medium confidence) |
| Gencay 2026, What survives honest evaluation? | https://arxiv.org/abs/2608.27734 | FETCHED-abstract (headline verified); body figures FETCHED-summariser, re-read before quoting (O13) |
| Lopez-Lira and Tang, Can ChatGPT forecast stock price movements? (v6, Oct 2025) | https://arxiv.org/html/2304.07619v6 | FETCHED-full (brief 16) |
| Lopez-Lira, Tang, Zhu, The Memorization Problem | https://arxiv.org/abs/2504.14765 | FETCHED-abstract |
| Kim, Muhn, Nikolaev (temporarily withdrawn pending review) | https://arxiv.org/html/2407.17866v2 | FETCHED-full (author page) |
| Beel, Kan, Baumgart 2025 | https://arxiv.org/abs/2502.14297 | FETCHED-abstract |
| Bailey and López de Prado, Deflated Sharpe Ratio | https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf | FETCHED-full (S07) |
| White, A Reality Check for Data Snooping, 2000 | https://www.econometricsociety.org/publications/econometrica/2000/09/01/reality-check-data-snooping | FETCHED-abstract |
| Ranjan and Gneiting, Combining probability forecasts, JRSS-B 2010 | https://ideas.repec.org/a/bla/jorssb/v72y2010i1p71-91.html | FETCHED-abstract (brief 10 F10) |
| Welch and Goyal, RFS 2008 | https://www.nber.org/papers/w10483 | FETCHED-abstract |
| Goyal, Welch, Zafirov, RFS 2024 | https://www.sfi.ch/en/publications/a-comprehensive-2022-look-at-the-empirical-performance-of-equity-premium-prediction | FETCHED-abstract |
| Gu, Kelly, Xiu, Empirical Asset Pricing via Machine Learning, RFS 2020 | https://www.nber.org/papers/w25398 | FETCHED-abstract; sample size SNIPPET |
| Zarattini, Pagani, Barbon, Catching Crypto Trends | https://ideas.repec.org/p/chf/rpseri/rp2580.html | FETCHED-abstract (working paper) |

**Agent design**

| Source | URL | Tag |
|---|---|---|
| Anthropic, Building effective agents | https://www.anthropic.com/engineering/building-effective-agents | FETCHED-full |
| Anthropic, multi-agent research system (about 4× / 15× tokens) | https://www.anthropic.com/engineering/multi-agent-research-system | FETCHED-full |
| Cemri et al., MAST | https://arxiv.org/abs/2503.13657 | FETCHED-abstract (taxonomy only; failure rates unconfirmed) |
| Huang et al., LLMs cannot self-correct reasoning yet, ICLR 2024 | https://arxiv.org/abs/2310.01798 | FETCHED-abstract |
| Shinn et al., Reflexion | https://arxiv.org/abs/2303.11366 | FETCHED-abstract |
| Yao et al., tau-bench | https://arxiv.org/abs/2406.12045 | FETCHED-abstract (2024; dated) |
| Claude Code docs (desktop scheduled tasks, headless, subagents, skills, hooks, costs, legal) | https://code.claude.com/docs/en/desktop-scheduled-tasks | FETCHED-full |
| Anthropic Consumer Terms; Usage Policy | https://www.anthropic.com/legal/consumer-terms ; https://www.anthropic.com/legal/aup | FETCHED-summariser (owner reads, O4) |

**Operations, data and brokers**

| Source | URL | Tag |
|---|---|---|
| SEC Knight Capital press release 2013-222 | https://www.sec.gov/newsroom/press-releases/2013-222 | FETCHED-full |
| FINRA Regulatory Notice 15-09 | https://www.finra.org/rules-guidance/notices/15-09 | FETCHED-full |
| Yuan et al., Simple Testing Can Prevent Most Critical Failures, OSDI 2014 | https://www.usenix.org/conference/osdi14/technical-sessions/presentation/yuan | FETCHED-abstract |
| Petrovic et al., Practical Mutation Testing at Scale | https://arxiv.org/abs/2102.11378 | FETCHED-abstract |
| Microsoft Learn, Task Scheduler security contexts | https://learn.microsoft.com/en-us/windows/win32/taskschd/security-contexts-for-running-tasks | FETCHED-full |
| Healthchecks docs | https://healthchecks.io/docs/measuring_script_run_time/ | FETCHED-full |
| GitHub Terms for Additional Products (hosted runners) | https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features | FETCHED-full |
| Alpaca orders and fractional docs | https://docs.alpaca.markets/us/docs/orders-at-alpaca ; https://docs.alpaca.markets/docs/fractional-trading | FETCHED-full |
| Alpaca market data; corporate actions | https://docs.alpaca.markets/docs/about-market-data-api ; https://docs.alpaca.markets/reference/corporateactions-1 | FETCHED-full |
| Alpaca crypto docs; regions page | https://docs.alpaca.markets/docs/crypto-trading ; https://alpaca.markets/support/what-regions-support-cryptocurrency-trading | FETCHED-full; regions page 404 (SNIPPET, UNVERIFIED) |
| Tiingo Terms of Use | https://app.tiingo.com/tos/ | FETCHED-summariser |
| FRED terms; TB3MS | https://fred.stlouisfed.org/docs/api/terms_of_use.html ; https://fred.stlouisfed.org/series/TB3MS | FETCHED-full |
| iShares SGOV, EFA, IBIT pages | https://www.ishares.com/us/products/314116/ishares-0-3-month-treasury-bond-etf ; https://www.ishares.com/us/products/239623/ishares-msci-eafe-etf ; https://www.ishares.com/us/products/333011/ishares-bitcoin-trust-etf | FETCHED-full |

Removed from the previous list because the body does not cite them: Lempérière et al.; Kurth, Eisler, Rej, Bouchaud (its abstract contrasts small-tick and large-tick contracts, not short and long lookbacks as S01-R3 put it); Keller; Asness-Frazzini-Pedersen; McLean-Pontiff; Wiecki et al.; Chaudhuri-Burnham-Lo; Harvey-Liu-Zhu; Rej-Seager-Bouchaud; Kim et al. (agent scaling); Liu-Tsyvinski; CISA CVE-2025-30066; Grinsztajn et al.; Israel-Kelly-Moskowitz. They remain in the specialist files.

---

## 17. Verification log

Two verifiers checked the previous revision: one against the evidence and references, one against the binding constraints and internal coherence. All eleven must-fix findings were applied. Section 14 (V rows) records the modified ones.

**Must-fix findings**

| # | Verifier | Finding | Resolution | Where |
|---|---|---|---|---|
| E1 | Evidence | Ranjan-Gneiting reversed: the paper says a linear pool of calibrated forecasts is uncalibrated and must be recalibrated on outcomes, not that it "cannot be calibrated"; paper missing from references | Reworded to "a pooled score needs its own calibration data, which JARVIS lacks"; reference added | 4.3 row 13; 13; 16 |
| E2 | Evidence | S-A taxable cost (−$14 to −$18; −1.1 to −1.4 points) stated as "the expected effect" without its range | Labelled "design-assumption central case; range −$30 to $0 (−2.4 to 0.0 points); sensitive to FIFO and the hurdle (central near −0.5 on brief 18's hurdle)". Shadow-first and retire-is-modal still hold because the whole range is ≤ 0 | 1; 2 rows 11, 13 |
| E3 | Evidence | Location value $29-$60 included $13-16 that exists only if S-A goes live in an IRA; contribution cap ignored | Now "$17-44 core-only, plus $13-16 only if S-A goes live in the IRA"; $7,500 cap stated (at most $7,500 of $10,000 in year one); yields ILLUSTRATIVE | 6 |
| E4 | Evidence | "Anthropic's own scheduler is the only permitted unattended route" stated as settled | Now "S06 interpretation, unconfirmed; owner reads provisions 7 and 9 in M0 (O4)"; "at most weekly" marked as a design invariant; decision rule added for both provisions | 4 (subscription bullets, Narrator row); 11 M0; 15 O4 |
| C1 | Coherence | Replication gate required long-history (1973+) Faber and Antonacci results on a 2004+ harness, with no numeric tolerances | Gate limited to ETF-era-checkable claims with numbers: turnover 40-100%, round trips 2-5 per asset per year, drawdown direction across 2007-2009 (or "not testable", which makes the memo inconclusive). Antonacci medians removed from the gate; free Ken French check optional and reported only | 5d; 8; 14 V1 |
| C2 | Coherence | "Agents may create HALT" contradicted "no agent writes outside agent-out/<agent>/" | Agents write `agent-out/<agent>/REQUEST_HALT`; the daily job or `jarvis month` promotes it to HALT and emails | 3; 4 enforcement; 5a step 5; 5b step 1; 5f; 7 |
| C3 | Coherence | ETF dividends and SGOV interest would trip SAFE on almost every monthly run | Reconcile classifies DIV/INT/FEE/withholding as expected non-owner cash feeding the waterfall; only deposits, withdrawals and journals need `jarvis cash-event`; unknown types → SAFE; added to the M3 exit test and GF drills; CSV labels probed in M0 (P5) | 3; 5a step 4; 7; 8; 11 |
| C4 | Coherence | M1/M2 depended on M3/M4 outputs (S0-RM b*, memo fields, `jarvis whatif`) | S0-RM runs with a labelled placeholder b* until M4; M2 memo fields default to `not_yet_available`; `jarvis whatif` and `/whatif` moved to the new M3b | 3; 4.1; 5c; 6; 11 |
| C5 | Coherence | Lab table forbade `llm_origin` live eligibility while flow (d) gave it a path to live money | One rule: `llm_origin` specs reach shadow only; live eligibility needs owner re-registration as an owner-origin spec after ≥12 forward decisions, with a new G0 counted as a new trial | 4.0; 4.1 Lab row; 5d step 5; 14 D25 |
| C6 | Coherence | First-money step relied on unprobed hand orders ("dollar amount + limit"), no check that a live manual UI exists, and a 60-second quote placed later by hand | M0 probes P3 (fractional limit by quantity vs notional) and P4 (manual entry, cancel-all, close on the live account); order list prints quantity, limit, quote time and a 15-minute "valid until", with `jarvis month --requote`; whole-share fallback; key exception stated if no manual UI exists | 5a steps 10-11; 7; 9 secrets; 11 M0; 15 O16 |
| C7 | Coherence | M4 memo and Sunset gated on after-tax results although S-A may go live only in a tax-deferred account | G1b(ii) and Sunset now gate on all-cost **pre-tax** results for the IRA path; after-tax reported for information | 1; 6; 8; 12; 14 D34 |

**Should-fix findings**

Applied as proposed:
- 96 years restated as "tens to about 200 years depending on correlation and power".
- Yuan figures re-attached: the majority preventable by simple tests, over 30% by the static checker.
- Lopez-Lira and Tang updated to v6 (6.54 to 1.22).
- FINSABER, StockBench and CLQT reworded as absence of evidence, with CLQT tagged abstract only.
- The Gencay "ETF trend not certified" support was dropped.
- MAST cited for its taxonomy only; Anthropic's 4× and 15× used.
- Narrator tokens marked as a lower bound, model and effort pinning added to the probe, Narrator-only cost about $0.25 API-equivalent.
- The Reviewer bar restated as advisory, with a consequence below 4 of 8.
- Thaler-Benartzi, FINRA, Odean, D'Acunto and Sicherman relabelled "DC, motivated by".
- The two behaviour-gap quantities separated, and the older-model caveat added.
- tau-bench marked dated.
- The gold basis moved to the Chief Counsel memo.
- KMN changed to "temporarily withdrawn pending review".
- The DeMiguel caveat added.
- Dev-day totals labelled as unvalidated planning estimates, with the stop rules as the commitment.
- References pruned, missing sources added, read-depth tags made consistent, drawdown ratios quoted with their sources.
- G4 slippage measured in `jarvis adopt`.
- Wash-sale rule made two-way, covering contribution and DRIP buys.
- The three LLM-to-order channels listed in section 4.0.
- `action_ids` changed to a code-rendered enum, and the model pinned or monitored.
- `jarvis release` now enforces the Reviewer note and sets `effective_after` for loosenings.
- Plan tier recorded in M0, a 1.3-1.5× calendar allowance added, and stall days added to the stop rules with caps.
- M3 slimmed: Incident Triage and Change-Watch moved to M3b, with the first deployment and the calendar wait described.
- The month-4 trigger changed to any costly deviation or the owner's choice, with the percentage only from 4+ decisions.
- The pre-2016 data fallback pre-stated.
- Failure behaviours added: uncaught exceptions, outages, the owner's CSV download, HALT no longer stopping ingest, and the Healthchecks B schedule.
- Event-driven agents exempted from the two-month rule.
- Laptop power changed to $0 incremental, the IRA fee listed as an open cost, and the stale consult sentence deleted.
- Terms decision rule added to M0.

Applied with a modification (section 14):
- The corporate-action vendor-feed match is required before the row takes effect, not at drafting time (V3).
- The plan-limit degrade rule is diagnosed from the log rather than cutting the Builder (V4).

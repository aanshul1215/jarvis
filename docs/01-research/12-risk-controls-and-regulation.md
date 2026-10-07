# 12 - Risk controls and regulation (research report, 2026-10-01)

Scope: evidence base for the JARVIS "Hard Risk Gate / Capital Governor", deployment and incident controls, and
the legal questions raised by the words "investors" and "investor view". Not legal advice.

Tagging convention: **[FETCHED]** = opened in this session; **[RECALLED]** = from memory, not re-verified today;
confidence high / medium / low. Note: pages were read through a summarising fetch tool, so paragraph-level wording
is paraphrase, not quotation. Two PDFs (Alpaca customer agreement, a CFTC primer) could not be parsed and are
marked unverified.

---

## 1. Questions asked (and the source I decided was authoritative before searching)

| # | Fact needed | Authoritative source chosen |
|---|---|---|
| Q1a | Exact control list in SEC Rule 15c3-5 | Rule text (17 CFR 240.15c3-5) + SEC staff FAQ |
| Q1b | FINRA's algorithmic-trading effective practices | FINRA Regulatory Notice 15-09 |
| Q2 | Root causes of Knight Capital and one other automated/erroneous-order failure | SEC order 34-70694 + SEC press release; FCA final notice/press release (Citigroup 2022) |
| Q3a | What triggers investment-adviser status | SEC staff paper "Regulation of Investment Advisers"; NASAA adviser guide |
| Q3b | Broker rules that bind an automated retail account | FINRA Regulatory Notice 26-10 (PDT replacement); Alpaca official docs |
| Q4 | Minimal control set for a solo retail auto-trader | Derived from Q1-Q3 (my synthesis, labelled as such) |

---

## 2. Findings

### 2.1 SEC Rule 15c3-5 (Market Access Rule) - what it actually requires

Source: https://www.law.cornell.edu/cfr/text/17/240.15c3-5 **[FETCHED, high]** (eCFR itself redirected to a
bot-block page; Cornell LII mirror used). SEC staff FAQ:
https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions/divisionsmarketregfaq-0 **[FETCHED, high]**

- **Who it binds:** broker-dealers with market access. It does **not** legally bind a retail customer. The v3
  document's wording ("a useful engineering model for our hard risk gate") is therefore the correct framing.
- (c)(1)(i) Reject orders that would exceed **pre-set credit or capital thresholds in the aggregate**, per customer
  and for the firm, optionally refined by sector/security.
- (c)(1)(ii) Reject **erroneous orders**: orders exceeding price or size parameters, order-by-order **or over a
  short period of time**, or that **look duplicative**.
- (c)(2)(i)-(ii) Block orders unless pre-order regulatory requirements are met; block securities the account is
  restricted from trading.
- (c)(2)(iii) Restrict access to trading systems to **pre-approved, authorised persons and accounts**.
- (c)(2)(iv) **Immediate post-trade execution reports** to surveillance staff.
- (d) Controls under the **direct and exclusive control** of the responsible party.
- (e) **Review effectiveness at least annually**, documented; annual CEO certification.
- FAQ emphasis: controls must be **pre-trade and automated** - reject before the order reaches the market, not
  cancel afterwards; thresholds should reflect aggregate exposure and be monitored on an ongoing basis.

### 2.2 FINRA Regulatory Notice 15-09 - effective practices for algorithmic strategies

Source: https://www.finra.org/rules-guidance/notices/15-09 **[FETCHED, high]**. Guidance for member firms, not
rules for retail customers. Five areas; the concrete items:

1. *General risk assessment:* holistic review of all trading activity; cross-disciplinary review including people
   outside the trading function.
2. *Development and change management:* track every new/changed piece of code; approval scaled to scope of change;
   archive retrievable code versions; plain-language summary of each strategy; **a way to disable an algorithm
   quickly in few steps**; pilot new strategies at limited scale; **heightened real-time monitoring right after a
   deployment**.
3. *Testing and validation:* test for intended behaviour and unintended consequences including fast/stressed
   markets; QA independent of the developer; data-integrity tests; keep records of tests and defect fixes;
   **development environment segregated from production**.
4. *Trading systems:* controls, monitors, alerts and **reconciliation** to catch unintended results; a log of
   significant system problems; documented and periodically reviewed risk-parameter settings; checks for
   **messaging volume, order looping and wash trades**; capacity headroom; restricted code/system access;
   **controls on anyone's ability to override system controls**; outbound message-rate thresholds.
5. *Compliance:* monitoring that covers the **interaction of multiple algorithms**; periodic review of the tools.

### 2.3 Post-mortems

**Knight Capital, 1 Aug 2012.** Sources: SEC press release 2013-222
https://www.sec.gov/newsroom/press-releases/2013-222 **[FETCHED, high]**; SEC order
https://www.sec.gov/files/litigation/admin/2013/34-70694.pdf **[FETCHED via summariser, medium for fine detail]**.

- Outcome: more than 4 million orders in about 45 minutes while trying to fill only 212 customer orders; about
  397 million shares traded; several billion dollars of unwanted positions; loss of more than $460 million;
  $12 million penalty. **[FETCHED, high]**
- Technical chain: (a) defective legacy code ("Power Peg") left in the router for years; a 2005 change moved the
  logic that tracked cumulative fills so the dead code could no longer tell when an order was complete; (b) the
  July 2012 release reused a flag that previously activated the dead code; (c) deployment was manual and did not
  complete on one of eight servers, with no second-person verification. **[FETCHED high for (a)-(b) and the
  failed deployment; RECALLED medium for the "repurposed flag" and "no second reviewer" detail]**
- 97 automated error e-mails were generated before the open and were not acted on. **[FETCHED, high]**
- During the incident, rolling the new code back off the correctly deployed servers made things worse.
  **[FETCHED via summariser; mechanism RECALLED, medium]**
- SEC-identified control gaps: no control comparing orders leaving the router with parent orders entered; no
  capital-threshold hard block at the point of market access; the account that accumulated the positions was not
  linked to automated exposure limits; inadequate deployment/testing procedures; **no written incident-response
  procedure**; incomplete annual reviews. **[FETCHED, high]**

Engineering lessons (my mapping): delete dead code and never reuse flags; automated, verified, all-or-nothing
deployment with a version handshake at start-up; child-order quantity must be bounded by parent-order quantity;
exposure limit enforced on the order path, not on a dashboard; alerts must page a human and/or auto-halt;
a written runbook whose first step is "stop sending and cancel", not "roll back".

**Citigroup Global Markets Ltd, 2 May 2022.** Source: FCA press release
https://www.fca.org.uk/news/press-releases/fca-fines-cgml-27-million (seen in search results of fca.org.uk;
**[FETCHED via search snippet, medium-high]**); final notice
https://www.fca.org.uk/publication/final-notices/citigroup-global-markets-limited-2024.pdf (not opened).

- Trader intended to sell a $58m basket; an input error created a $444bn basket. Controls blocked $255bn; $189bn
  reached an execution algorithm; $1.4bn was sold on European exchanges before cancellation. FCA fine
  GBP 27,766,200 (PRA fined separately).
- Failures: **no hard block** rejecting the whole basket; a pop-up **soft warning could be overridden** without
  reading it; real-time monitoring was too slow.
- Lesson: soft warnings are not controls. Units/notional sanity checks must be hard rejects. Directly relevant to
  JARVIS because an LLM-produced order size is exactly the kind of input that can be wrong by orders of magnitude.

Other well-known incidents (2010 Flash Crash, crypto exchange outages, API-key thefts) were **not** researched
from primary sources in this session and are not relied on here.

### 2.4 Legal exposure

**Investment-adviser status (US).** Sources: SEC staff, "Regulation of Investment Advisers"
https://www.sec.gov/about/offices/oia/oia_investman/rplaze-042012.pdf **[FETCHED, high for the definition;
the document is dated 2012-2013 so thresholds may be stale]**; NASAA adviser guide
https://www.nasaa.org/industry-resources/investment-advisers/investment-adviser-guide/ **[FETCHED, high]**.

- Three-part test: (1) advice or analysis about **securities**, (2) for **compensation** in any form (read
  broadly - includes indirect benefit such as a profit share), (3) **in the business** of doing so.
- Small advisers are regulated by the **states** (roughly below $100m AUM), larger ones by the SEC. State rules
  differ; some states have a small-client de minimis exemption and some do not. **[RECALLED, medium:** the
  "fewer than six clients" national de minimis standard applies only where the adviser has no place of business
  in the state; the adviser's home state can require registration from the first client. Must be confirmed for
  the owner's state.]
- Anti-fraud provisions apply even to unregistered/exempt advisers.
- Trading **only one's own money** in one's own account is not advising anyone: none of the three elements is
  met. With the owner's binding constraint (own money only), adviser registration is not triggered.
- What **would** change the analysis (each is a question for a securities lawyer before doing it):
  1. taking any outside money, even from friends/family, especially with a fee or profit share;
  2. pooling money in an LLC/partnership (adds fund/securities-offering questions and, for crypto or futures,
     possible CFTC commodity-pool questions) **[RECALLED, medium]**;
  3. being given trading authority or API keys over someone else's brokerage account;
  4. selling or publishing JARVIS signals, especially personalised ones (the "publisher" exclusion covers only
     impersonal, general, regular publications) **[RECALLED, medium]**;
  5. showing performance figures to prospective investors (marketing/anti-fraud exposure).
- Other jurisdictions differ substantially (e.g. UK FCA authorisation for managing investments, EU MiFID
  portfolio management, India SEBI PMS/RIA rules) **[RECALLED, low-medium; not researched]**.

**Rules that do bind a retail automated account today.**

- **Pattern-day-trader rule is gone.** FINRA Regulatory Notice 26-10 (published 20 Apr 2026) replaced the day-trade
  count and the $25,000 minimum with **intraday margin standards**, effective **4 June 2026**, with a broker
  phase-in allowed until **20 Oct 2027**. Applies to margin accounts (not cash accounts). An unmet intraday margin
  deficit, if not satisfied by the fifth business day and part of a pattern, leads to a **90-calendar-day**
  restriction on creating/increasing short positions or debit balances; small deficits (lesser of 5% of equity or
  $1,000) are excused. Source: https://www.finra.org/rules-guidance/notices/26-10 **[FETCHED, high]**.
- **Alpaca has implemented it:** PDT designation, day-trade counting and DTBP removed; PDT API fields deprecated
  (changelog 2026-06-03; removal stated for 6 July 2026); margin calls on intraday deficits due in two business
  days; ~$2,000 equity still needed for margin. Sources:
  https://docs.alpaca.markets/us/docs/the-intraday-margin-rule **[FETCHED, high]**;
  https://docs.alpaca.markets/us/changelog/2026-06-03-pdt-651df23 **[search result only, medium]**.
  Consequence: any JARVIS design text or code that hard-codes "max 3 day trades in 5 days under $25k" is
  outdated; the replacement constraint is intraday buying power and margin deficits. Because of the phase-in,
  **other brokers may still enforce the old rule until Oct 2027** - check the specific broker.
- **Alpaca's own pre-trade protections** (https://docs.alpaca.markets/docs/user-protection **[FETCHED, high]**):
  orders that could self-cross are rejected with HTTP 403 (opposite-side market orders always; opposite limits
  when buy limit >= sell limit; bracket/OCO/trailing-stop exempt); accounts with a position over 600% of equity
  are put into closing-only pending review; a limit-price sanity check exists. JARVIS must treat these 403s as
  expected, typed outcomes - not retry them.
- **Alpaca orders** (https://docs.alpaca.markets/us/docs/orders-at-alpaca **[FETCHED, high]**): each order carries a
  client-supplied unique `client_order_id`; extended-hours orders must be limit orders; price increments are
  2 decimals at or above $1 and 4 below; notional orders cannot be replaced; buying-power check at entry.
  Alpaca's guidance on a submit timeout is to **check order state rather than resubmit** (docs
  /docs/working-with-orders **[FETCHED, medium]**). That `client_order_id` duplicates are rejected, and that
  `DELETE /v2/orders` and `DELETE /v2/positions` exist as bulk cancel/flatten endpoints, are **[RECALLED, medium]**
  - verify in the API reference before relying on them for the kill switch.
- **Alpaca crypto** (https://docs.alpaca.markets/docs/crypto-trading **[FETCHED, high]**): **no margin and no
  short selling** in crypto; order types market/limit/stop-limit, TIF gtc/ioc only; fees 15 bps maker / 25 bps
  taker at the lowest volume tier; availability limited to some US jurisdictions.
- **Alpaca paper trading** (https://docs.alpaca.markets/docs/paper-trading **[FETCHED, high]**) does not simulate
  market impact, information leakage, latency slippage, queue position for resting limits, price improvement,
  regulatory fees or dividends.
- **Alpaca customer agreement** (https://files.alpaca.markets/disclosures/alpaca_customer_agreement.pdf):
  **unverified** - PDF could not be parsed. Clauses on customer liability for API orders, account
  restriction/liquidation rights and market-data redistribution must be read by the owner.
- **Manipulation rules apply to the owner as a trader**, not just as something to detect in others. Wash trades,
  spoofing/layering (placing orders intended to be cancelled) are prohibited regardless of account size or intent
  expressed by software **[RECALLED, high in substance; statutes not fetched]**. An agent that rapidly
  places/cancels orders, or trades the same symbol in opposite directions from two strategies, can generate
  these patterns accidentally.
- **Taxes** (wash-sale rule for securities, short-term gains, record-keeping; crypto treatment) -
  **[RECALLED, medium; not researched]** - question for a tax professional.

---

## 3. What this means for the JARVIS design documents

**Supported**
- Architecture layer G / v3 "Capital Governor / Risk Agent: deterministic service; no LLM override" - directly
  matches the central idea of 15c3-5 (automated pre-trade rejects under exclusive control) and the Citigroup
  lesson (overridable warnings are not controls).
- v3 "Execution Agent: idempotent order service" and "paper first, shadow, staged live" - matches FINRA 15-09
  (pilot at limited scale, segregated environments) and the Knight lessons.
- Ledger/audit layer (I) and "limits changed only through an audited settings action" - matches 15-09's
  documented parameter settings and change tracking.
- v3 implementation note that broker rules change and should be queried rather than assumed - strongly
  confirmed: the PDT rule was abolished four months ago.
- Architecture doc's Alpaca paper-trading caveat (no impact/queue/latency) - confirmed by current docs.

**Weakened / incomplete**
- The risk-gate lists (max loss, position, concentration, leverage, liquidity, stale data, halt, daily drawdown,
  kill switch) cover *financial* limits but omit the *erroneous-order* family that 15c3-5(c)(1)(ii) and both
  post-mortems put first: per-order price collar, per-order size/notional cap, **duplicate-order detection**,
  **order-rate / message throttle**, **order-loop detection**, **self-cross prevention across strategies**, and
  restricted-symbol list.
- No document mentions **position/order reconciliation against the broker** as a standing control, nor
  start-up reconciliation after a crash. Knight's core gap was the absence of a check tying outgoing orders to
  intended parent quantity.
- No document covers **deployment controls** (version pinning, config hash, one live instance, post-deploy
  heightened monitoring) or a **written incident runbook**. Docker Compose on a laptop with LangGraph retries is
  exactly the environment where a duplicated container or replayed checkpoint can resend orders.
- "Kill switch" is named but unspecified. Evidence says it needs: independent process, few steps, cancels open
  orders, blocks new ones, and a decision rule for whether to flatten; plus a **dead-man's switch** for a
  laptop that sleeps, loses Wi-Fi or crashes while holding positions - particularly with 24/7 crypto.
- v3's "human approval ... for a degraded-data override" is an override path on a hard control; 15-09 says to
  control the ability to override. It should be removed or made impossible from the agent layer.
- Position Manager exits are "deterministic" but live only in software. Protective stops should also rest at the
  broker (bracket/OCO) so they survive a JARVIS outage. (Alpaca crypto supports stop-limit but not bracket
  semantics identically - verify.)
- SHORT as a first-class decision: not available for crypto at Alpaca at all; for equities it requires a margin
  account (about $2,000 minimum) and brings intraday-margin-deficit and 90-day-freeze risk. With $1k-$10k,
  short should be off by default.

**Contradicted / needs rewording**
- "Investors", "investor view", "what the investor sees", "hosted read-only UI": inconsistent with the owner's
  binding statement that only his own money is involved. As written, the docs describe the artefacts of managing
  other people's money. Rename to "owner dashboard" and add an explicit design constraint: no outside capital,
  no signal distribution, no third-party account access without prior legal advice.
- Citations [5]-[7] in v3 imply regulatory guidance applies to JARVIS. It applies to broker-dealers; JARVIS
  borrows it voluntarily. The obligations that *do* bind the owner are the broker agreement, margin rules, and
  anti-manipulation law - none of which the docs list.
- Any assumed PDT constraint is obsolete (if present in code/plans).

---

## 4. Recommended changes

### 4.1 Hard Risk Gate engineering checklist (deterministic, separate process, default-deny)

Pre-trade, every order:
1. Mode check (paper/live) and symbol on an explicit allow-list; restricted list honoured.
2. Per-order max notional and max quantity (absolute dollars, not only % of equity) - hard reject.
3. Price collar versus a fresh reference quote (reject if quote older than N seconds or limit price outside X%);
   no market orders outside regular hours; tick-size validation.
4. Duplicate detection: deterministic `client_order_id` derived from (decision id, leg, attempt) plus a
   same-symbol/side/size-within-T-seconds check.
5. Rate limits: max orders per minute/day, max cancels per minute, max open orders; breach trips the breaker.
6. Aggregate exposure: gross, net, per-symbol, per-asset-class caps computed from **broker-reported** positions
   plus working orders.
7. Loss limits: per-trade risk, daily realised+unrealised loss, weekly loss, peak-to-trough drawdown - each maps
   to a state (reduce-only, halt, manual re-arm).
8. Buying power / leverage: leverage cap 1.0 by default; no shorting unless explicitly enabled; intraday margin
   headroom check.
9. Self-cross / wash guard: no opposite-side order while a working order exists in the same symbol; cool-down on
   rapid round trips.
10. Data-trust and market-state blocks: stale feed, halt, wide spread, outside session.
11. Every decision logged with reason code; gate parameters stored in versioned config; changes need a human,
    take effect next session, and can only tighten intraday.

Around the gate:
12. Reconciliation: at start-up and every few minutes compare internal orders/positions/cash with the broker;
    any mismatch -> halt new entries and alert. Broker is the source of truth.
13. Kill switch: independent of the agent stack; one action; cancel all, block new; flatten is a separate
    explicit choice. Test it weekly in paper.
14. Dead-man's switch: heartbeat; if JARVIS is silent for N minutes with open risk, a watchdog (ideally off the
    laptop) cancels orders; protective stops resting at the broker for every position.
15. Single-instance lock on the order sender; orders never emitted from LangGraph nodes or retries, only from
    the execution service consuming an approved, idempotent intent.
16. Deployment: tagged versions, config hash logged at start-up, no deploys with open positions, first session
    after any change runs at reduced size with extra alerts; remove unused code paths and never reuse flags.
17. Credentials: live keys never in the repo (v1 already leaked one), never visible to LLM prompts/tools;
    separate paper and live keys; disable withdrawal/transfer permissions where the venue allows.
18. Incident runbook (one page) and an incident log; quarterly review of limits (the retail analogue of the
    annual 15c3-5(e) review).
19. LLM boundary: agents output structured proposals only; sizes and prices are recomputed deterministically;
    text from news/social content is never able to alter gate parameters (prompt-injection defence).

### 4.2 Minimal mandatory subset before the first live dollar
Items 2, 3, 4, 5, 6, 7, 12, 13, 14, 15, 17 plus the runbook. Everything else can be phased, but these eleven
are the ones whose absence produced the losses in section 2.3.

### 4.3 Document changes
- Replace "investor" language; add a "Legal perimeter" section listing the five triggers in 2.4.
- Add "broker constraints adapter": at start-up read account status, buying power, shorting/crypto permissions
  and fail closed if anything is unexpected.
- State explicitly that 15c3-5 / 15-09 are borrowed design patterns, not obligations.

---

## 5. Open uncertainties

- Alpaca customer agreement terms (liability for API orders, liquidation rights, data redistribution limits that
  may affect a "hosted read-only UI") - not readable in this session.
- Exact Alpaca behaviour on duplicate `client_order_id`, bulk cancel/flatten endpoints, API rate limits, and
  whether bracket/OCO orders exist for crypto - recalled only.
- Coinbase Advanced Trade terms and API-key permission model - not researched.
- Whether the owner's state of residence is supported for Alpaca crypto; state adviser de minimis rules for that
  state (only relevant if outside money is ever considered).
- Fine details of the Knight order (flag reuse, absence of second reviewer, exact rollback mechanism) come from
  memory plus a machine summary; headline facts are from the SEC press release.
- Citigroup facts come from FCA search snippets, not the full final notice.
- SEC adviser thresholds were read from a 2012-2013 staff paper; current figures not re-checked.
- Tax treatment (wash sales, crypto) not researched.
- Intraday-margin rule details for sub-$2,000 and cash accounts at Alpaca ("non-leverage margin accounts" doc
  exists but was not opened).

---

## 6. Source list

Fetched this session
- 17 CFR 240.15c3-5 (Cornell LII mirror): https://www.law.cornell.edu/cfr/text/17/240.15c3-5
- SEC staff FAQ on Rule 15c3-5: https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions/divisionsmarketregfaq-0
- FINRA Regulatory Notice 15-09: https://www.finra.org/rules-guidance/notices/15-09
- SEC press release 2013-222 (Knight): https://www.sec.gov/newsroom/press-releases/2013-222
- SEC order 34-70694 (Knight): https://www.sec.gov/files/litigation/admin/2013/34-70694.pdf
- SEC staff, Regulation of Investment Advisers: https://www.sec.gov/about/offices/oia/oia_investman/rplaze-042012.pdf
- NASAA Investment Adviser Guide: https://www.nasaa.org/industry-resources/investment-advisers/investment-adviser-guide/
- FINRA Regulatory Notice 26-10: https://www.finra.org/rules-guidance/notices/26-10
- Alpaca - Intraday Margin Rule: https://docs.alpaca.markets/us/docs/the-intraday-margin-rule
- Alpaca - User Protection: https://docs.alpaca.markets/docs/user-protection
- Alpaca - Orders: https://docs.alpaca.markets/us/docs/orders-at-alpaca
- Alpaca - Working with orders: https://docs.alpaca.markets/docs/working-with-orders
- Alpaca - Crypto trading: https://docs.alpaca.markets/docs/crypto-trading
- Alpaca - Paper trading: https://docs.alpaca.markets/docs/paper-trading

Seen in search results only (not opened)
- FCA press release, CGML fine: https://www.fca.org.uk/news/press-releases/fca-fines-cgml-27-million
- FCA final notice CGML 2024: https://www.fca.org.uk/publication/final-notices/citigroup-global-markets-limited-2024.pdf
- Alpaca changelog, PDT fields deprecated: https://docs.alpaca.markets/us/changelog/2026-06-03-pdt-651df23
- SEC approval order SR-FINRA-2025-017: https://www.sec.gov/files/rules/sro/finra/2026/34-105226.pdf

Attempted, not usable
- eCFR (bot block), investor.gov (403), Alpaca customer agreement PDF and a CFTC primer PDF (unparseable).


## Independent verification (2026-10-01)

Confirmed (re-fetched from primary sources today):
- FINRA 26-10: published 20 Apr 2026, effective 4 Jun 2026, phase-in to 20 Oct 2027; 90-day short/debit freeze if deficit unmet by close of fifth business day; safe harbor lesser of 5% equity or $1,000. https://www.finra.org/rules-guidance/notices/26-10
- Alpaca PDT removal implemented in production, PDT/day-trade API fields removed: https://alpaca.markets/blog/finra-retires-the-pdt-rule-introducing-alpacas-new-intraday-margin-framework/ (search result; the docs page itself https://docs.alpaca.markets/us/docs/the-intraday-margin-rule only describes the rule, does not state Alpaca's implementation date, and the ~$2,000 margin minimum there is a general Reg T reference, not Alpaca-specific).
- Alpaca crypto: no margin, no shorting, market/limit/stop-limit, gtc/ioc, 15/25 bps lowest tier; no bracket/OCO mentioned for crypto. https://docs.alpaca.markets/docs/crypto-trading
- Alpaca user protection: 403 on potential self-cross, 600% of equity -> closing-only pending Alpaca review, bracket/OCO/trailing exempt from wash protection. https://docs.alpaca.markets/docs/user-protection
- Knight: 4M+ orders, 45 min, 397M shares, 212 customer orders, >$460M loss, $12M penalty, 97 emails. https://www.sec.gov/newsroom/press-releases/2013-222
- Citigroup/FCA: GBP 27,766,200 (after 30% discount; pre-discount 39,666,000), $58m intended vs $444bn, $255bn blocked, $189bn reached algo, $1.4bn sold, overridable pop-up. PRA separate GBP 33,880,000. https://www.fca.org.uk/news/press-releases/fca-fines-cgml-27-million
- Alpaca DELETE /v2/orders (cancel all) and DELETE /v2/positions (close all, cancel_orders param) exist (upgrades the RECALLED item): https://docs.alpaca.markets/reference/deleteallorders , https://alpaca.markets/blog/position-liquidation-cancel-orders/

Corrected / weakened:
- Intraday margin deficit: Alpaca docs say a margin call must be met within two business days; FINRA's outer limit is 15 business days. Do not conflate with the 5-business-day freeze trigger. The brief's "$2,000 still needed" should be treated as unverified for Alpaca specifically.
- Crypto fee tier is 0-$100k 30-day volume; at $1k-$10k accounts the 25 bps taker fee (about 50 bps round trip) is a first-order cost and should be a hard input to any intraday crypto edge test.
- Alpaca crypto state availability not verified for the owner's state (docs defer to a support page).

Unverifiable / still open: Alpaca customer agreement; duplicate client_order_id rejection behavior; Citigroup final notice and SEC order PDF fine detail (press releases only); state adviser rules; tax treatment.

Missed considerations: (1) with $1k-$10k, per-trade fees/spread and cash-account settlement/good-faith rules matter more than institutional-style controls; consider a cash account (no intraday margin exposure); (2) wash-sale and tax-lot record-keeping for high-frequency equity trading; crypto wash-sale treatment should be checked with a tax professional; (3) LLM API cost near zero means the deterministic gate must work with LLMs fully offline (fail closed to flat); (4) free data tiers (IEX feed on Alpaca) differ from consolidated quotes, affecting price-collar checks.

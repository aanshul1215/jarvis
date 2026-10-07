# 05 - Brokers and market access

Research date: 2026-10-01. Labels: **FETCHED** = page opened this session; **SEARCH** = text returned by a search restricted to the official domain, page itself not opened (or returned 403); **RECALLED** = from memory, not checked. Confidence: high / medium / low.

## 1. Questions asked

Facts needed and the source treated as authoritative for each:

| Fact | Authoritative source |
|---|---|
| Alpaca paper fidelity, order types, shorting, fractional, crypto, data plans, fees, eligibility | docs.alpaca.markets, Alpaca fee schedule PDF, Alpaca support |
| Pattern-day-trader rule status | FINRA Regulatory Notice, SEC release, FINRA investor page; broker docs for implementation |
| IBKR, Coinbase, Kraken, Binance API facts | each vendor's developer docs and fee pages |
| India: overseas investing, crypto tax, domestic API rules | RBI LRS FAQ, IBKR India pages, Income Tax Dept, SEBI/NSE circulars, Zerodha docs |

## 2. Findings

### 2.1 Alpaca

**Paper trading fidelity (FETCHED, high)** - https://docs.alpaca.markets/docs/paper-trading
Alpaca's own documentation says paper trading does not model: market impact, information leakage, latency slippage, queue position for resting limit orders, price improvement, regulatory fees, or dividends. Borrow fees are listed as "coming soon". Two points matter more than the rest:
- Order quantity is **not checked against NBBO size**, so an order larger than displayed liquidity still fills.
- Partial fills are **random** (10% of eligible orders), not derived from the book.
Default balance is $100k. Anyone globally can open a paper-only account. Consequence: paper results are an upper bound for any strategy whose edge depends on fills at the touch, resting limit orders, or order-book signals.

**Order types (FETCHED, high)** - https://docs.alpaca.markets/docs/orders-at-alpaca
Market, limit, stop, stop-limit, trailing stop, bracket, OCO, OTO, plus open/close auction orders. TIF: day, gtc (auto-cancel at 90 days), opg, cls, ioc, fok. Extended and overnight sessions accept limit orders only; bracket orders are not supported in extended hours. Crypto supports only gtc and ioc.

**Shorting and margin (FETCHED, high)** - https://docs.alpaca.markets/docs/margin-and-short-selling and fee schedule PDF (revised 17 Sep 2026) https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf
- $2,000 minimum equity to use margin or sell short; below that, 1x buying power and no shorting.
- 2x overnight, up to 4x intraday.
- Easy-to-borrow: no locate or borrow fee. Hard-to-borrow: locate via Locates API (per-share fee, single use, non-refundable), plus a daily borrow fee charged on calendar days including weekends, sized on round lots.
- Margin interest 6.25% default, 4.75% Elite (fee schedule). The docs page shows 6.5%/5.0%; the fee schedule is newer, so treat the docs figure as stale.
- All Alpaca accounts are margin accounts; there is no cash-account type (SEARCH, medium - Alpaca support "Can I have a cash account").

**Fractional shares (FETCHED, high)** - https://docs.alpaca.markets/docs/fractional-trading
$1 minimum, 2,000+ equities, market/limit/stop/stop-limit with TIF=day only. **Fractional short sales are not supported.** A $100 account therefore cannot short equities at all (below $2,000 equity) and cannot short fractionally at any size.

**Crypto (FETCHED, high)** - https://docs.alpaca.markets/docs/crypto-trading
20+ assets, 56 pairs. Market, limit, stop-limit. **No margin and no short selling in crypto.** Fees are volume-tiered: 15 bps maker / 25 bps taker at the lowest tier ($0-100k 30-day volume), falling to 0/10 bps above $100M. $200k per-order cap. Availability is "select" US and international jurisdictions; a support article (SEARCH, medium, dated Oct 2025) lists ~28 US states and excludes New York. The public page I could reach does not list countries.

**Market data and rate limits (FETCHED, high)** - https://docs.alpaca.markets/docs/about-market-data-api
- Basic (free): IEX feed only (a single exchange, a few percent of consolidated volume), 30 websocket symbols, 200 REST calls/min, latest 15 minutes of SIP history withheld.
- Algo Trader Plus: $99/month, full SIP, unlimited websocket symbols, 10,000 calls/min, OPRA options.
- Trading API: 200 requests/min per account; 1,000/min on Elite (SEARCH, medium - Alpaca support).

**Fees (FETCHED, high)** - fee schedule PDF, 17 Sep 2026
Zero commission on equities for retail flow. Pass-through on sells: SEC fee $20.60 per $1M, FINRA TAF $0.000195/share (max $9.79). CAT fee $0.000003/share on both sides. Each fee type is aggregated daily and **rounded up to the nearest cent**, so a tiny account pays about 2-3 cents on any day it sells, a non-trivial drag on $100. International wire out $35; local-currency transfers 1.5% (max $40). Alpaca reserves the right to charge if flow is judged "non-retail".

**Who can open a live account (FETCHED, medium)** - https://alpaca.markets/learn/live-trading-account-non-us , https://alpaca.markets/support/countries-alpaca-is-available
Alpaca states it serves many countries, requires a tax ID, photo ID, address proof, selfie and W-8BEN, and has a $1 minimum for non-US users. It does **not publish a country list**; the support page says to email support. Canada is named as unsupported. India is not confirmed or denied on any page I opened. A search summary suggested India appears on a crypto-eligible list, but I could not open that page (404): **unverified**.

### 2.2 Pattern-day-trader rule - current status

**The PDT rule has been repealed (FETCHED, high).**
- SEC approved FINRA's Rule 4210 amendments on 14 April 2026 (Exchange Act Release 34-105226, SR-FINRA-2025-017). FINRA Regulatory Notice 26-10 (20 April 2026) set the effective date at **4 June 2026**, with an optional phase-in to **20 October 2027**. Sources: https://www.finra.org/rules-guidance/notices/26-10 ; https://www.finra.org/investors/insights/intraday-margin-requirements ; WilmerHale client alert (URL in source list).
- Removed: the "pattern day trader" designation, the four-day-trades-in-five-days count, the $25,000 minimum equity, and day-trading buying power.
- Replaced by an "intraday margin deficit" test: the firm must ensure equity covers maintenance margin on actual intraday exposure, either by real-time blocking or by end-of-day calculation and a margin call.
- Two caveats from FINRA's investor page: a firm **may keep operating under the old rules during the phase-in**, and firms may impose stricter house requirements. $2,000 is still needed to use leverage.

**Alpaca's implementation (FETCHED, high)** - https://alpaca.markets/blog/finra-retires-the-pdt-rule-introducing-alpacas-new-intraday-margin-framework/ ; changelog https://docs.alpaca.markets/us/changelog/2026-06-03-pdt-651df23
Live from 4 June 2026. 4x intraday buying power threshold lowered from $25,000 to $2,000. Pre-trade checks reject orders that would create a deficit. API fields `pattern_day_trader`, `daytrade_count`, `daytrading_buying_power`, `dtbp_check`, `pdt_check` removed by 6 July 2026. Sub-$2,000 accounts can day trade without a count limit at 1x. Note that Alpaca's own non-US onboarding article still says the PDT rule applies - that page is stale. Whether paper accounts mirror the new checks is not documented: **unverified**.

Other brokers' implementation dates (IBKR in particular) were not checked: **unverified**.

### 2.3 Interactive Brokers API (brief)

- TWS API needs a running TWS or IB Gateway session; 50 messages/second cap across all clients on one session; Web API 50 requests/second per user plus per-endpoint pacing (SEARCH from interactivebrokers.com docs, medium; the campus doc page returned 403).
- Paper account is available only after the live account is approved and funded (SEARCH, IBKR TWS API docs, medium).
- Commissions, market-data subscription costs, minimums: not fetched (403) - **unverified**. From memory (RECALLED, low): tiered/fixed per-share pricing with a per-order minimum around $0.35-$1, and real-time data is a paid subscription. A per-order minimum is material for very small orders.

### 2.4 Coinbase Advanced Trade (brief)

- Products: spot, CFTC-regulated US futures, and perpetuals for eligible non-US clients; REST, WebSocket, SDKs; a sandbox exists (FETCHED, high) - https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/overview . The page announces a new derivatives gateway dated 1 October 2026, so that surface is changing now.
- Rate limits: private REST 30 req/s per user, public 10 req/s per IP (SEARCH, medium). WebSocket: the page I opened says connections and unauthenticated messages are each limited to 8/s per IP (FETCHED, high); a search summary said 750 connections/s. Conflict unresolved; use the lower figure.
- Fees: both official fee pages returned 403. Secondary sources disagree (0.40%/0.60% versus 0.50%/0.90% maker/taker at the lowest tier) and mention a schedule change in September 2026. **Unverified** - must be read from the logged-in account.
- Spot is long-only; shorting requires futures/perps, which are eligibility-gated.

### 2.5 Kraken (brief)

- Spot: REST, WebSocket v2, FIX 4.4; 700+ pairs; limit, market, stop, take-profit, trailing stop, IOC, post-only. Derivatives: perpetuals and dated futures. **Spot has no self-service sandbox** (UAT by account-manager request); futures has a public demo (FETCHED, high) - https://docs.kraken.com/api/docs/guides/global-intro/
- REST rate limit: counter max 15/20/20 with decay 0.33/0.5/1 per second for Starter/Intermediate/Pro tiers; order placement has a separate limiter (FETCHED, high) - https://docs.kraken.com/api/docs/guides/spot-rest-ratelimits/
- Fees (FETCHED, high) - https://www.kraken.com/features/fee-schedule : Kraken Pro spot **0.40% maker / 0.80% taker at $0+**, 0.30/0.60 at $2.5k+, 0.22/0.38 at $10k+. Margin: roughly 0.01-0.04% to open plus the same per 4 hours. Futures 0.02%/0.05%.
- Margin is available to most verified clients outside the US, UK and Canada; US clients must meet eligibility conditions (SEARCH, support.kraken.com, medium). India is not on Kraken's excluded-country list in that result, but India-side compliance status is unclear (see 2.7).

### 2.6 Binance (brief)

- Rate limits are weight-based per IP; 429 then escalating IP bans from 2 minutes to 3 days (FETCHED, high) - https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits
- Fees: spot 0.10%/0.10% at VIP 0, 0.075% with BNB discount (FETCHED, high) - https://www.binance.com/en/fee/trading
- Binance.com terms bar US users; Binance.US is a separate entity serving 37 states (not New York, Texas and others) as of June 2026 (SEARCH, medium).
- Spot testnet details could not be opened: **unverified**. (RECALLED, low: it exists, with periodic resets and thin synthetic liquidity.)

### 2.7 Non-US resident - India as a conditional worked case

The owner's country is unknown. If it is India:

**US equities**
- RBI's Liberalised Remittance Scheme allows USD 250,000 per financial year, **prohibits remittance for margin or margin calls**, and requires unused funds to be repatriated or reinvested within 180 days (FETCHED, high; FAQ last updated April 2023) - https://www.rbi.org.in/commonman/english/Scripts/FAQs.aspx?Id=1834
- IBKR India states that Indian residents trading overseas get **cash accounts only: no shorting, no margin, no futures or options** - stocks, ETFs and bonds only (SEARCH from interactivebrokers.co.in / .com, medium; the pages returned 403 on direct fetch).
- Tax collected at source on LRS investment remittances: 20% above Rs 10 lakh per year (SEARCH, secondary tax sources only, medium-low). It is a credit against income tax, but it ties up cash.
- Alpaca: India eligibility unconfirmed. Separately, Alpaca offers only margin-type accounts, and whether an Indian resident may lawfully hold one even at 1x is a question I could not resolve: **uncertain**.
- Whether same-day round trips in US shares are permitted for LRS investors is widely described as restricted, but I found no primary text: **unverified**.

**Crypto**
- Legal to hold and trade; not legal tender; exchanges must register with FIU-IND under anti-money-laundering rules. Binance registered and resumed in 2024 after a ~Rs 18.82 crore penalty; Coinbase obtained FIU registration in 2025; Kraken's status is unclear (SEARCH, news sources, medium-low).
- Tax: flat **30%** on gains from each transfer, only cost of acquisition deductible, **losses cannot be set off against anything, nor carried forward**, plus **1% TDS on the sale value** of each transfer (SEARCH, Income Tax Dept publication and secondary sources, medium; the official PDF returned 403). Budget 2026 reportedly left the rates unchanged and added reporting penalties (secondary sources only, low-medium). The Income-tax Act 2025 renumbered sections from April 2026; new section numbers **unverified**.
- Consequence: a high-turnover crypto strategy is taxed on the sum of its winning trades, not on net profit. A strategy with 55% winners and net positive pre-tax P&L can be loss-making after tax. The 1% TDS on every sale also drains working capital at a rate far above exchange fees.

**Domestic alternative**
- Zerodha Kite Connect: free "Personal" tier (orders only, no data); Rs 500/month for websocket and historical data (FETCHED, high) - https://support.zerodha.com/category/trading-and-markets/general-kite/kite-api/articles/what-are-the-charges-for-kite-apis . Limits: 10 orders/second, 400/minute, 5,000/day (SEARCH, kite.trade, medium).
- SEBI retail algo framework (circular of 4 Feb 2025): API access tied to a broker-whitelisted **static IP**; self-built algos under 10 orders/second per exchange need no exchange registration; strategies may be shared only with family; selling black-box algos requires Research Analyst registration (FETCHED Zerodha explainer + SEARCH NSE FAQ, medium). Final enforcement dates were extended more than once (RECALLED, low) - check before building.
- Indian equity shorting is intraday-only in the cash segment; overnight short exposure requires F&O (RECALLED, medium).

## 3. What this means for the JARVIS design documents

| Document claim / component | Verdict | Evidence |
|---|---|---|
| Architecture doc: "Alpaca paper is useful but does not fully simulate market impact, queue position or latency slippage" | **Supported, but understated.** Paper also ignores displayed size and randomises partial fills. | 2.1 |
| v3 step: "Compare predicted vs actual spread/slippage and P&L" in paper mode | **Weakened.** Paper slippage is not real slippage; this comparison only becomes meaningful with small live orders. | 2.1 |
| LONG / SHORT / FLAT across equities + crypto | **Contradicted at small size.** Spot crypto cannot be shorted at Alpaca or on Coinbase spot. Equity shorting needs $2,000 equity and whole shares. For an Indian resident, overseas shorting and margin are barred outright. | 2.1, 2.4, 2.7 |
| $100 worked examples netting +$0.27 on intraday BTC/ETH | **Weakened.** Round-trip taker cost: Alpaca 0.50% ($0.50), Kraken 1.60% ($1.60), Binance 0.20% ($0.20), before spread. A +$0.27 net on Alpaca needs a gross move above ~0.77% plus spread. In India add 1% TDS per sale and 30% tax on winners with no loss offset. | 2.1, 2.5, 2.6, 2.7 |
| Flow/microstructure agent using L2 order books | **Weakened on execution side.** Alpaca's free equity feed is IEX only; SIP costs $99/month; order-book-driven fills cannot be validated in paper. | 2.1 |
| v3 note: "query or encode the actual broker's current rules rather than assuming a fixed regulatory configuration" | **Strongly supported.** The PDT rule was repealed in June 2026 and Alpaca removed the related API fields within a month. | 2.2 |
| Risk gate "broker/account rules" | **Supported, needs content.** Any hard-coded PDT logic is now wrong; replace with intraday-margin and broker buying-power checks. | 2.2 |
| "Alpaca + Coinbase feeds" as the default stack | **Conditional.** Fine for a US resident. For an Indian resident neither is confirmed usable, and the tax regime changes the viable strategy set. | 2.1, 2.7 |
| "Investors" / other people's money | Not researched here, but every broker account above is an individual retail account; trading for others raises licensing questions in any jurisdiction. | - |

## 4. Recommended changes

1. **Make jurisdiction the first gate.** The owner's country of tax residence must be answered before broker choice, asset scope or horizon is fixed. Add it to the Goal/Capital Planner inputs.
2. **Add a Broker Capability Registry** (deterministic config, not an LLM agent): per venue and account - shortable or not, minimum equity for shorting, fractional rules, order types and TIF, fee schedule, rate limits, data entitlements. The strategy layer may only propose actions the registry marks feasible. Refresh it from the broker API and changelogs on a schedule.
3. **Redefine SHORT.** At small capital: equities long/flat (or inverse ETFs where permitted), crypto long/flat. Enable true shorting only when the registry says the account qualifies.
4. **Remove PDT logic; add intraday-margin logic.** Use the broker's reported `buying_power` and handle order rejections for intraday margin deficit.
5. **Insert a "micro-live" stage between paper and small live** specifically to measure real slippage, and state in the docs that paper P&L is not evidence of execution quality.
6. **Put real fee tables into the cost model** (Alpaca crypto 15/25 bps; Kraken 40/80 bps base; Binance 10/10 bps; daily cent-rounding of regulatory fees) and add a minimum-edge-over-cost test to the risk gate. Replace the $100 worked example with one that passes it, or state that it does not.
7. **Add a tax model to the Evaluation layer**, parameterised by jurisdiction. For India, model 30% on gross winners plus 1% TDS; this will likely rule out high-frequency crypto and push toward lower turnover.
8. **Budget for data**: $99/month Alpaca SIP (or equivalent) if any intraday equity signal is kept.
9. **If India**: evaluate a domestic leg (Kite Connect, static IP, under 10 orders/second) as the primary automated venue, and treat US equities via LRS as a low-turnover, long-only sleeve.

## 5. Open uncertainties

- Owner's country, capital, and whether third-party money is involved.
- Whether Alpaca accepts Indian tax residents for live equities and/or crypto (no public list; ask support).
- Whether an Indian resident can lawfully use Alpaca's margin-type account at 1x, and whether intraday trading of US shares under LRS is permitted (no primary source found).
- Coinbase Advanced Trade current fee tiers (pages blocked; schedule reportedly changed Sept 2026); Coinbase WebSocket limit conflict.
- IBKR commissions, data fees, and how IBKR has implemented the new intraday margin rule.
- Whether Alpaca paper accounts enforce the new intraday margin checks.
- Indian VDA tax after Budget 2026 and the Income-tax Act 2025 renumbering - confirmed only via secondary sources.
- Current SEBI retail-algo enforcement dates.
- Binance spot testnet fidelity; Kraken's FIU-IND status.

## 6. Source list

Fetched this session:
- https://docs.alpaca.markets/docs/paper-trading
- https://docs.alpaca.markets/docs/crypto-trading
- https://docs.alpaca.markets/docs/orders-at-alpaca
- https://docs.alpaca.markets/docs/margin-and-short-selling
- https://docs.alpaca.markets/docs/fractional-trading
- https://docs.alpaca.markets/docs/about-market-data-api
- https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf (revised 17 Sep 2026)
- https://alpaca.markets/blog/finra-retires-the-pdt-rule-introducing-alpacas-new-intraday-margin-framework/
- https://docs.alpaca.markets/us/changelog/2026-06-03-pdt-651df23
- https://docs.alpaca.markets/us/docs/the-intraday-margin-rule
- https://docs.alpaca.markets/us/docs/intraday-margin-rule-for-non-leverage-margin-accounts
- https://docs.alpaca.markets/us/docs/understanding-finras-new-intraday-margin-rule-and-the-end-of-pdt
- https://alpaca.markets/learn/live-trading-account-non-us
- https://alpaca.markets/support/countries-alpaca-is-available
- https://alpaca.markets/support/is-alpaca-available-outside-the-us
- https://www.finra.org/rules-guidance/notices/26-10
- https://www.finra.org/investors/insights/intraday-margin-requirements
- https://www.wilmerhale.com/en/insights/client-alerts/20260423-sec-approves-amendments-to-finra-rule-4210-replacing-day-trading-margin-requirements-with-a-modernized-intraday-margin-standard
- https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/overview
- https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-rate-limits
- https://docs.kraken.com/api/docs/guides/global-intro/
- https://docs.kraken.com/api/docs/guides/spot-rest-ratelimits/
- https://www.kraken.com/features/fee-schedule
- https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits
- https://www.binance.com/en/fee/trading
- https://www.rbi.org.in/commonman/english/Scripts/FAQs.aspx?Id=1834
- https://zerodha.com/z-connect/business-updates/explaining-the-latest-sebi-algo-trading-regulations
- https://support.zerodha.com/category/trading-and-markets/general-kite/kite-api/articles/what-are-the-charges-for-kite-apis

Seen only as search results (not opened, or blocked):
- https://www.sec.gov/files/rules/sro/finra/2026/34-105226.pdf
- https://www.interactivebrokers.co.in/en/accounts/individual-account-india.php (403)
- https://www.interactivebrokers.co.in/en/index.php?f=25308 (403)
- https://interactivebrokers.github.io/tws-api/order_limitations.html
- https://alpaca.markets/support/what-regions-support-cryptocurrency-trading (404)
- https://alpaca.markets/support/usage-limit-api-calls
- https://www.coinbase.com/advanced-fees (403)
- https://www.incometaxindia.gov.in/ (VDA taxation PDF, 403)
- https://nsearchives.nseindia.com/web/sites/default/files/inline-files/FAQ_Retail%20Algo_03112025_NSE.pdf (timeout)
- https://support.kraken.com/articles/4402532394260-client-eligibility-for-margin-trading-services-
- https://support.binance.us/en/articles/9842798-list-of-supported-and-unsupported-states-and-regions
- https://kite.trade/forum/discussion/15912/

## Independent verification (2026-10-01)

Scope: owner is a US resident, $1k-$10k own money, near-zero budget. India section 2.7 is irrelevant to the owner (US resident) and should be dropped from design decisions.

Confirmed (re-opened by the fact-checker):
- PDT repeal: FINRA Notice 26-10, effective 4 Jun 2026, phase-in to 20 Oct 2027, SEC approval 14 Apr 2026, release 34-105226, PDT designation and $25,000 minimum removed. https://www.finra.org/rules-guidance/notices/26-10
- Alpaca paper limits (no impact, latency slippage, queue position, regulatory fees, dividends; random 10% partial fills; no liquidity check; $100k default). https://docs.alpaca.markets/docs/paper-trading
- Alpaca crypto: 15/25 bps lowest tier, no margin or shorting, gtc/ioc only, $200k cap. https://docs.alpaca.markets/docs/crypto-trading
- Alpaca data: Basic is IEX only, 30 WS symbols, 200 calls/min, last 15 min of history; Algo Trader Plus $99/month. https://docs.alpaca.markets/docs/about-market-data-api
- Margin/short needs $2,000 equity; 2x overnight, 4x intraday. https://docs.alpaca.markets/docs/margin-and-short-selling
- Kraken Pro spot 0.40/0.80% at $0+, 0.22/0.38% at $10k+. https://www.kraken.com/features/fee-schedule . Note tiers can also qualify via assets held ($20k AoP for the $10k tier).
- Alpaca has no cash accounts (all margin; IRA cash accounts planned first). https://alpaca.markets/support/alpaca-cash-accounts

Corrected / weakened:
- Margin interest 6.25% / 4.75% could NOT be confirmed; the PDF text was not extractable. The docs page confirms 6.5% / 5.0%. Use 6.5% / 5.0% until the PDF is read manually. Low impact for a long-only account.
- Alpaca crypto availability: the state list found is dated 9 Oct 2025 (about 28 states, excludes New York). For a US resident, state of residence is a hard gate and must be checked in Alpaca's current list; it is a year old. https://alpaca.markets/support/what-regions-support-cryptocurrency-trading
- Fee-schedule specifics (SEC fee $20.60/M, TAF, CAT, cent rounding) were not confirmed from the PDF by this check.

Unverifiable: Coinbase and IBKR fees (403 in the brief), Alpaca paper enforcement of the new intraday margin checks, all India items (not applicable).

Missed for this owner:
- Wash-sale rule and US tax: short-term gains taxed as ordinary income; wash sales apply to stocks, and the crypto wash-sale position should be confirmed with a tax professional. Alpaca 1099 reporting.
- Settlement: all Alpaca accounts are margin, so no good-faith-violation limits, but sub-$2,000 accounts are limited margin (1x).
- With $1k-$10k, the $99/month SIP data plan is 1%-10% of capital per month; free IEX data only supports daily or slow strategies. Drop intraday L2 order-flow signals.
- Drop any assumption of multi-agent LLM cost; use deterministic code with sparing Claude calls.

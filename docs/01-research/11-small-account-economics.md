# 11 — Small-account economics (research date 2026-10-01)

Verdict up front: **the $100 intraday crypto worked example does not survive current US retail fee schedules on the venues the documents name.** On Coinbase Advanced or Kraken Pro at entry tier the round-trip fee alone (1.6-1.8% taker) exceeds the example's entire expected upside (+1.6%). On Alpaca (0.50% taker round trip) the trade is arithmetically possible but needs a ~54% hit rate on a 2:1 payoff just to break even, and a single multi-agent LLM evaluation of the trade costs about as much as the $0.27 profit. The binding constraints at $1,000-$10,000 are (a) percentage crypto fees, which do not shrink with account size until volume tiers are reached, and (b) fixed running costs (LLM, data), which do.

Labels: FETCHED = opened in this session; RECALLED = from memory, not re-verified; ESTIMATE = my arithmetic on stated assumptions.

## 1. Questions asked

1. Lowest-tier maker/taker fees, spreads and minimum orders for Coinbase Advanced, Kraken Pro, Binance(.US), Alpaca crypto.
2. Equities: commissions, regulatory fees, fractional shares, short borrow, margin minimums, PDT.
3. Break-even gross move per round trip at $100 / $1,000 / $10,000 / $25,000+, and required win-rate by horizon.
4. Running costs (data, LLM) versus capital; where the system stops being cost-dominated; tax drag.

## 2. Findings

### 2.1 Crypto fee schedules (lowest tier)

| Venue | Maker | Taker | Taker round trip | Source / basis / confidence |
|---|---|---|---|---|
| Alpaca crypto, Tier 1 ($0-100K 30-day vol) | 0.15% | 0.25% | 0.50% | docs.alpaca.markets/docs/crypto-fees — FETCHED — high |
| Kraken Pro, Tier 1 ($0+) | 0.40% | 0.80% | 1.60% | kraken.com/features/fee-schedule — FETCHED twice, same numbers — high |
| Kraken Pro, Tier 2 ($2.5K+) | 0.30% | 0.60% | 1.20% | same |
| Kraken Pro, Tier 3 ($10K+ vol or $20K assets) | 0.22% | 0.38% | 0.76% | same |
| Kraken Pro, Tier 5 ($50K+) / Tier 6 ($100K+) | 0.15% / 0.12% | 0.30% / 0.25% | 0.60% / 0.50% | same |
| Coinbase Advanced, US entry tier (new schedule effective 2026-09-16) | 0.50% | 0.90% | 1.80% | Coinbase's own fee pages returned HTTP 403. Numbers from securities.io report dated 2026-09-16 (FETCHED) and a coinbase.com blog snippet in search results. Medium |
| Coinbase Advanced, previous <$1K tier | 0.60% | 1.20% | 2.40% | bankrate review via search snippet — not opened — low/medium |
| Binance.US, all non-BNB pairs, lowest VIP | 0.00% | 0.02% (0.019% paying in BNB) | 0.04% | binance.us/fees — FETCHED twice — medium (page summarised by tool; verify in-account before relying on it) |

Notes:
- Kraken's entry tier is materially higher than the 0.25%/0.40% I recalled from training data; the live page now shows 0.40%/0.80% and an "assets on platform" alternative qualification. This is exactly the kind of fact that must not be recalled.
- Binance.com is not available to US residents (RECALLED, high); the relevant entity is Binance.US. Its state-by-state availability and USD funding rails were not verified in this session — **unverified**.
- Alpaca charges the fee in the asset received (buy ETH, fee in ETH), posted end of day (FETCHED, high). The ledger must handle this.
- Kraken's consumer app "instant buy" is 1% plus spread (FETCHED) — never use it programmatically.

### 2.2 Spreads and minimum sizes

- Coinbase Exchange public order book, 2026-10-01 05:36 UTC: BTC-USD 84,239.28 / 84,239.29; ETH-USD 2,714.22 / 2,714.23 — a one-cent spread, i.e. about 0.001 bps (BTC) and 0.04 bps (ETH). Source: api.exchange.coinbase.com/products/{BTC,ETH}-USD/book?level=1 — FETCHED — high for that instant only. One snapshot is not a distribution; spreads widen in stress. For BTC/ETH on a major venue, **fees dominate spread by two to three orders of magnitude**.
- Alpaca's crypto venue spread is not the Coinbase spread; its typical BTC/ETH spread was not measured — **unverified** (must be measured in paper/shadow mode).
- Minimums: Coinbase BTC-USD min market funds $1 (API, FETCHED, high). Kraken: 0.0001 BTC (about $8.42 at today's price), 0.01 ETH (about $27.14), $5 (support.kraken.com, FETCHED, high; page warns values change). Alpaca: 0.0001 minimum quantity shown for BTC, $200K max per order (FETCHED, medium — per-pair minimums should be read from the assets endpoint).
- Consequence: the v2 document's $25 ETH position is **below Kraken Pro's 0.01 ETH minimum** today.
- Alpaca crypto cannot be shorted and cannot use margin (docs.alpaca.markets/docs/crypto-trading, FETCHED, high). Spot crypto at these venues is long/flat only.

### 2.3 Equities (Alpaca as reference broker)

- Commission: $0 for US-listed equities via Trading API (RECALLED, high; regulatory-fee page FETCHED confirms only pass-through fees are itemised).
- SEC Section 31 fee: **$20.60 per $1M of sales, effective 2026-04-04** (previously $0.00). FINRA Information Notice 2026-03-17 — FETCHED — high. Sells only.
- FINRA TAF: $0.000195/share, max $9.79/trade for 2026 — finra.org search snippet, page not opened — medium. Sells only.
- Alpaca rounds SEC and TAF fees up to the nearest penny; CAT fee also passed through (alpaca.markets/support/regulatory-fees, FETCHED, high; CAT rate not stated).
- Fractional shares: from $1 notional, 2,000+ symbols, market/limit/stop/stop-limit, DAY only; **fractional orders cannot be sold short** (docs.alpaca.markets/docs/fractional-trading, FETCHED, high).
- Margin and shorting: need **$2,000+ equity**; below that the account is 1x, no shorts. ETB borrow $0; HTB needs locates in 100-share round lots with daily fees. Margin interest 6.5% (5.0% "elite"), no interest if flat by day end. (docs.alpaca.markets/docs/margin-and-short-selling, FETCHED, high.)
- **PDT rule is gone.** FINRA Regulatory Notice 26-10: Rule 4210 amended, pattern-day-trader designation and the $25,000 minimum eliminated, replaced by an intraday margin deficit standard; effective **2026-06-04**, optional broker phase-in to 2027-10-20 (finra.org/rules-guidance/notices/26-10, FETCHED, high). Alpaca has implemented it: PDT fields deprecated/removed from the API by 2026-07-06; standard $2,000 margin minimum remains; an unmet intraday margin deficit after five business days leads to a 90-day restriction on new debits/shorts (Alpaca docs, FETCHED, high; API removal date from search snippet, medium).
- Free Alpaca market data ("Basic"): IEX-only real time, 15-minute delay for other exchanges, 30 websocket symbols, 200 requests/min. Full SIP ("Algo Trader Plus") is $99/month (docs.alpaca.markets/docs/about-market-data-api, FETCHED, high).

### 2.4 LLM prices (Claude API)

platform.claude.com/docs/en/about-claude/pricing — FETCHED — high. Per million tokens (input / output): Haiku 4.5 $1 / $5; Sonnet 5 and 5.5 $2 / $10; Opus 5.5 $4 / $20; Opus 5 $5 / $25; Fable 5.1 $10 / $50. Batch API 50% off; cache reads 0.1x input (lower on some models). Newer models use a tokenizer producing roughly 30% more tokens for the same text.

### 2.5 Tax (general, not advice)

- Positions held one year or less are short-term and taxed as ordinary income; net capital losses deductible up to $3,000/year against other income, remainder carried forward (IRS Topic 409, FETCHED, high).
- Equity wash-sale rule (IRC 1091) disallows/defers losses on repurchase within 30 days (RECALLED, high) — an automated system that re-enters the same ticker will generate these constantly.
- Crypto: a bill to extend wash-sale rules to digital assets (H.R. 9172) was introduced 2026-06-08 (congress.gov via search snippet, medium); **whether it is enacted is unverified**. Form 1099-DA broker reporting of proceeds and basis applies for 2026 (IRS instructions, search snippet, medium).
- LLM/data subscription costs are generally not deductible for a non-professional investor (RECALLED, low — check with a tax professional).

## 3. Break-even arithmetic (ESTIMATE)

Assumptions: taker in and out; 2 bps total slippage on BTC/ETH; position = 25% of account as in the worked example. Percentage fees are scale-invariant, so account size matters only through volume tiers, minimum orders, and penny rounding.

**Crypto — gross move needed just to pay for one round trip**

| Account (position) | Coinbase Adv. | Kraken Pro | Alpaca | Binance.US |
|---|---|---|---|---|
| $100 ($25) | 1.82% ($0.46) | 1.62% ($0.41) | 0.52% ($0.13) | 0.06% ($0.015) |
| $1,000 ($250) | 1.82% ($4.55) | 1.22-1.62% (Tier 2 after ~5 round trips/month) | 0.52% ($1.30) | 0.06% |
| $10,000 ($2,500) | 1.82% until $10K volume; higher tiers not verified | 0.78% (Tier 3 after 2 round trips) | 0.52% ($13) | 0.06% |
| $25,000+ ($6,250) | not verified | 0.52-0.62% (Tier 5/6) | 0.46-0.52% | 0.06% |

Maker-only round trips halve these roughly (Alpaca 0.30%, Kraken T1 0.80%, Coinbase 1.00%) but add non-fill and adverse-selection risk that momentum/order-flow entries are particularly exposed to.

**The documents' own example, re-costed.** $25 position, +1.6% target, -0.8% adverse case, reported +$0.27 net (= +1.08% net).
- Break-even win probability p solves p(1.6) - (1-p)(0.8) - c = 0, so p = (0.8 + c) / 2.4.
- No costs: 33%. Binance.US: 36%. Alpaca maker: 46%. Alpaca taker: 55%. Kraken Tier 1: 100%+ (impossible). Coinbase: 100%+ (impossible).
- To net $0.27 on Alpaca the gross move must be about 1.6% — i.e. the full target was hit, which contradicts the narrative "continuation weakened early, exited early". On Coinbase the gross move would need to be 2.9%.
- "Costs are small" (Architecture v1) is false for three of the four venues: costs are 33% (Alpaca) to 113% (Coinbase) of the expected upside.

**Win rate needed for a symmetric +/-m payoff: p > 0.5 + c/(2m).** Using rough volatility scaling (BTC daily sigma about 2.5%, large-cap equity about 1.5% — RECALLED, low; must be estimated from data):

| Horizon (typical move m) | Coinbase 1.82% | Kraken T1 1.62% | Alpaca 0.52% | Binance.US 0.06% | Equity 0.05% |
|---|---|---|---|---|---|
| Crypto ~3h (m ~0.9%) | impossible | impossible | 79% | 53% | — |
| Crypto ~5d swing (m ~5.6%) | 66% | 64% | 55% | 50.5% | — |
| Crypto ~20d (m ~11%) | 58% | 57% | 52% | 50.3% | — |
| Equity ~3h (m ~1.0%) | — | — | — | — | 52.5% |
| Equity ~5d (m ~3.4%) | — | — | — | — | 50.7% |

Sustained directional accuracy above ~55% at any horizon is rare; 79% is not a credible design target.

**Equities — round-trip cost.** Regulatory fees on the sell leg, with penny rounding: $25 sale = $0.01 SEC + $0.01 TAF = 8 bps; $250 = under 1 bp; $2,500 = about $0.07 = 0.3 bps. Add 2-4 bps for spread/slippage in liquid large caps (RECALLED, medium). Total about 0.10% at $25 positions and about 0.03-0.05% at $250+. **Liquid US equities/ETFs are 10-40x cheaper per round trip than crypto on Alpaca/Kraken/Coinbase.**

## 4. Running costs versus capital (ESTIMATE)

LLM cost per agent call (about 6K input + 800 output tokens): Haiku 4.5 about $0.010; Sonnet 5 about $0.020; Opus 5.5 about $0.040; Fable 5.1 about $0.10. A v3-style evaluation touching ~10 reasoning agents costs about $0.10 (Haiku) to $0.40 (Opus 5.5) **per candidate** — the same order as the $0.27 example profit.

| Operating pattern | Evaluations/month | Haiku 4.5 | Sonnet 5 |
|---|---|---|---|
| "Always-on" every 15 min, 24/7 | 2,880 | ~$290 | ~$575 |
| 5 evaluations/day | 150 | ~$15 | ~$30 |
| 1 daily batch run (Batch API, 50% off) | 30 | ~$1.50 | ~$3 |

Fixed monthly cost as annualised drag on capital:

| Monthly cost | $100 | $1,000 | $10,000 | $25,000 |
|---|---|---|---|---|
| $3 (daily batch only) | 36% | 3.6% | 0.36% | 0.14% |
| $30 (sparing LLM) | 360% | 36% | 3.6% | 1.4% |
| $129 (SIP feed + $30 LLM) | — | 155% | 15.5% | 6.2% |

Rule of thumb: to keep fixed costs under 2%/year of capital, capital must be at least 600x the monthly bill — $1,800 at $3/month, $18,000 at $30/month, $77,000 at $129/month. At the owner's $1,000-$10,000 the system is **cost-dominated unless LLM spend stays in single-digit dollars per month and all data is free-tier**; the paid SIP feed is not affordable in that range. At $100 no configuration with any LLM usage is economic — $100 is a plumbing test, not a P&L experiment. Add roughly $3-5/month electricity for an always-on laptop (RECALLED, low).

Tax drag: all intraday/swing gains are short-term (ordinary rates); at a 22-24% marginal rate the pre-tax edge must be about 1.3x the desired after-tax edge, while fees and LLM costs are paid in full regardless.

## 5. What this means for the JARVIS design documents

- **Contradicted — Architecture v1 worked example** ("Costs are small", $25 BTC, +$0.27): costs are 33-113% of expected upside on named venues; the narrative is internally inconsistent with a 1.08% net result.
- **Contradicted — v2 ETH example at $25**: below Kraken's 0.01 ETH minimum; fee-negative on Coinbase/Kraken.
- **Supported — v2 limitation text** "Small capital can be dominated by fees/spreads": correct, and understated. It should become a quantitative gate, not a caveat.
- **Supported — v1 decision rule** (upside x probability > loss + costs + risk penalty): right form; needs real venue-specific cost inputs. With them, the rule would reject almost every intraday crypto trade — which is the correct outcome.
- **Weakened — "long/short/flat" for crypto and for small equity accounts**: spot crypto on Alpaca cannot be shorted; equity shorting needs $2,000+ equity, whole shares, and no fractional shorts. At $1,000 the system is long/flat only (inverse ETFs are the only short proxy).
- **Weakened — always-on Opportunity Scanner plus Live Position Manager that "recomputes thesis/confidence" with LLM agents**: at near-zero budget, LLM calls must be rare events gated by deterministic triggers, not a loop.
- **Weakened — Flow/Microstructure agent on equities**: the free feed is IEX-only with a 30-symbol websocket cap; order-flow features from a single small venue are not market-wide flow. Crypto L2 from Coinbase is free and real.
- **Outdated risk removed**: PDT/$25K is no longer a constraint (since 2026-06-04); any PDT counter logic should be replaced by intraday-margin-deficit awareness. Alpaca API PDT fields were removed.
- **Supported — deterministic Capital Governor**: it is the right place for a hard cost gate.
- **Unaddressed — "second broker/feed for redundancy"** (v3): redundancy doubles minimum-volume fragmentation and keeps the account in worst fee tiers.

## 6. Recommended changes

1. Add a deterministic **Cost Gate** inside the Capital Governor: reject any trade whose calibrated expected gross move is less than k x (round-trip fees + measured spread + slippage), k >= 2-3, using a per-venue fee table loaded from config and refreshed against the live fee pages.
2. Add an **LLM budget governor**: hard monthly dollar cap, per-decision cost recorded in the ledger, and P&L reported net of LLM/data cost. Use the Batch API and the cheapest adequate model for routine work; reserve larger models for rare escalations.
3. **Re-order the asset/horizon priority**: liquid US equities/ETFs at swing horizon (days to weeks) first — round-trip cost about 0.03-0.05%. Treat crypto as swing-only, lowest-fee venue only, and drop intraday crypto from the initial scope.
4. If crypto is kept, choose the venue on fees: Alpaca (0.25% taker) over Kraken/Coinbase entry tiers; investigate Binance.US (0.02% taker) only after verifying state availability, funding and counterparty risk first-hand. Do not split volume across venues.
5. Replace the $100 worked examples with a $1,000-$10,000 example showing gross move, each fee line, LLM cost of the decision, and net; make "no trade — edge below cost hurdle" the featured outcome.
6. Set the live-trading floor at the capital where fixed monthly cost x 600 <= capital; with a ~$3-5/month LLM budget that is roughly $2,000-$3,000, which also clears the $2,000 margin/short minimum.
7. Remove PDT logic; add intraday-margin-deficit and whole-share-short constraints to the risk gate.
8. Ledger: record fee asset (Alpaca crypto fees in received asset), penny-rounded regulatory fees, wash-sale flags, and holding-period classification.
9. Paper/shadow phase must measure realised spread and slippage on the actual venue and compare to the fee table before any live gate is passed (already in v3 step; make it a pass/fail criterion).

## 7. Open uncertainties

- Coinbase Advanced full post-2026-09-16 tier table (official pages blocked; entry tier is second-hand).
- Binance.US fee page reading (0% / 0.02%) and its current availability/funding for the owner's state.
- Alpaca crypto typical spread and effective execution quality versus Coinbase/Kraken books; Alpaca crypto availability in the owner's state.
- Alpaca treatment of sub-$2,000 accounts under the new intraday margin rule (docs page did not state details).
- CAT fee rate; TAF rate taken from a search snippet.
- Whether crypto wash-sale legislation (H.R. 9172) has been enacted; deductibility of running costs.
- Volatility figures used for win-rate tables are recalled approximations; recompute from data.
- Token counts per agent call are assumptions; measure on real prompts.
- No peer-reviewed evidence on retail day-trader profitability was opened in this session; the well-known Barber/Lee/Liu/Odean results (large majority of day traders lose net of costs) are RECALLED only and should be verified by the literature agent.

## 8. Source list

FETCHED
- https://docs.alpaca.markets/docs/crypto-fees
- https://docs.alpaca.markets/docs/crypto-trading
- https://docs.alpaca.markets/docs/crypto-orders
- https://docs.alpaca.markets/docs/margin-and-short-selling
- https://docs.alpaca.markets/docs/fractional-trading
- https://docs.alpaca.markets/docs/about-market-data-api
- https://docs.alpaca.markets/us/docs/understanding-finras-new-intraday-margin-rule-and-the-end-of-pdt
- https://docs.alpaca.markets/us/docs/intraday-margin-rule-for-non-leverage-margin-accounts
- https://alpaca.markets/support/regulatory-fees
- https://www.kraken.com/features/fee-schedule
- https://support.kraken.com/articles/205893708-minimum-order-size-volume-for-trading
- https://www.binance.us/fees
- https://api.exchange.coinbase.com/products/BTC-USD , /BTC-USD/book?level=1 , /ETH-USD/book?level=1
- https://www.securities.io/coinbase-lowers-advanced-trading-fees-with-tiers-starting-at-10-000/ (secondary, for Coinbase change)
- https://www.finra.org/rules-guidance/notices/26-10
- https://www.finra.org/rules-guidance/notices/information-notice-20260317
- https://www.finra.org/rules-guidance/guidance/trading-activity-fee (no rate on page)
- https://www.sec.gov/rules-regulations/fee-rate-advisories (index only)
- https://platform.claude.com/docs/en/about-claude/pricing
- https://www.irs.gov/taxtopics/tc409

SEARCH SNIPPET ONLY (not opened)
- https://www.coinbase.com/blog/were-lowering-fees-for-many-active-traders-on-coinbase-advanced (403 on fetch)
- https://www.finra.org/rules-guidance/rulebooks/corporate-organization/section-1-member-regulatory-fees (TAF rate)
- https://docs.alpaca.markets/us/changelog/2026-06-03-pdt-651df23
- https://www.congress.gov/bill/119th-congress/house-bill/9172/text
- https://www.irs.gov/instructions/i1099da

BLOCKED (HTTP 403): https://www.coinbase.com/advanced-fees , https://help.coinbase.com/en/coinbase/trading-and-funding/advanced-trade/advanced-trade-fees

## Independent verification (2026-10-01)

Confirmed (re-fetched today):
- Alpaca crypto Tier 1 0.15% maker / 0.25% taker, fee charged in received asset: https://docs.alpaca.markets/docs/crypto-fees
- Kraken Pro Tier 1 0.40/0.80, Tier 2 0.30/0.60 ($2.5K+), Tier 3 0.22/0.38 ($10K vol or $20K assets), best-of volume or assets: https://www.kraken.com/features/fee-schedule
- FINRA 26-10: PDT designation and $25K minimum eliminated, effective 2026-06-04, phase-in to 2027-10-20: https://www.finra.org/rules-guidance/notices/26-10
- SEC Section 31 fee $20.60 per $1M effective 2026-04-04: https://www.sec.gov/rules-regulations/fee-rate-advisories/2026-2
- Claude pricing (Haiku 4.5 $1/$5, Sonnet 5/5.5 $2/$10, Opus 5.5 $4/$20, Fable 5.1 $10/$50, batch 50%): https://platform.claude.com/docs/en/about-claude/pricing . Note: Opus 5.5 and Fable 5.1 cache reads are 0.05x / 0.025x, so caching is cheaper than the brief implies.
- Coinbase Advanced US entry 0.50% / 0.90%, effective 2026-09-16, first volume threshold lowered to $10,000 (second-hand sources only; official page blocked): https://www.securities.io/coinbase-lowers-advanced-trading-fees-with-tiers-starting-at-10-000/

Corrected / weakened:
- Binance.US: page shows 0.00% maker / 0.019% taker (0.0095% BNB/USD), but it states a money transmitter license in only 32 states. Treat the 0.04% round trip as unusable until availability, USD funding rails and withdrawal/counterparty risk are verified for the owner's state: https://www.binance.us/fees
- Alpaca crypto is not available in every state (NY and AZ historically excluded; search results are old/partial). Verify the owner's state before choosing Alpaca as the crypto venue.
- Alpaca sub-$2,000 behaviour under the new intraday margin rule remains undocumented on the page checked (only says broker house rules may apply). Do not design on the assumption of unlimited day trades in a small account. Settlement and cash-account limits were not stated.

Unverifiable this session: Alpaca per-pair crypto spread; FINRA TAF rate; CAT fee; H.R. 9172 status; Barber/Odean day-trader loss evidence; volatility figures; token-count assumptions; Coinbase official fee page.

Missed considerations: (1) a US-state crypto license check is a gating item for every venue; (2) Binance.US 0% maker only helps if limit orders fill; (3) at $1,000-$10,000 the sound conclusion is swing-horizon equities/ETFs with a deterministic cost gate and a single-digit-dollar monthly LLM cap, which the brief already recommends.

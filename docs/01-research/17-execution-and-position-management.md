# 17 — Execution and Position Management

Research date: 2026-10-01. Basis labels: FETCHED = page opened in this session; SNIPPET = seen only in a search-result summary (page itself blocked or not opened); RECALLED = from memory, not checked.

Caveat on method: pages were read through a summarising fetch tool, so numbers below are as that tool reported them from the page. Where the tool's summary was clearly wrong I say so (one case: Lo-Remorov, see F3).

## 1. Questions asked

1. Do stop-losses, trailing stops, time stops and profit targets add or destroy value, and for which strategy types?
2. The docs' Position Manager "recomputes confidence continuously and exits when it falls". What are the risks, and how should thesis invalidation be defined?
3. How should costs and slippage be modelled for small orders, and what are the known paper-vs-live gaps?
4. Order-handling correctness: idempotent IDs, partial fills, cancel/replace races, reconciliation after a crash, and what happens to open positions if the system dies.

Facts needed and the authoritative source chosen for each: exit-rule evidence -> the original academic papers (Kaminski-Lo, Lo-Remorov, Han-Zhou-Zhu, Clare et al.); churn/cost theory -> Garleanu-Pedersen, Barber-Odean; retail execution cost -> Schwarz et al. (Journal of Finance 2025); broker mechanics, fees, paper-trading limits -> Alpaca and Coinbase official docs; control failures -> SEC release on Knight Capital; day-trading rule -> broker notice of the FINRA Rule 4210 change.

## 2. Findings

### A. Exit rules

**F1. Under a random walk, a simple stop-loss always lowers expected return; it can add value only if returns have momentum (positive serial correlation / regimes).**
Kaminski and Lo, "When Do Stop-Loss Rules Stop Losses?", Journal of Financial Markets 18 (2014). What was measured: an analytical framework plus one empirical test on monthly US equity returns Jan 1950 - Dec 2004, where the stop switches the portfolio into long-term government bonds. Certain rules added roughly 50-100 bp per month during stopped-out periods. This is a monthly, asset-allocation-level result, not an intraday single-stock or crypto result. Transaction-cost treatment not confirmed from the abstract.
Source: https://swopec.hhs.se/sifrwp/abs/sifrwp0063.htm (working-paper abstract) — FETCHED — confidence high on the qualitative result, medium on transfer to JARVIS's horizons. (The MIT PDF returned HTTP 405; the full text was not read.)

**F2. For mean-reverting strategies a stop-loss is expected to hurt** (you exit exactly when the expected rebound is largest). This is the direct corollary of the Kaminski-Lo framework, and I recall it being stated in the paper, but I did not read the full text in this session.
Source: same as F1 — RECALLED for the explicit mean-reversion statement — confidence medium-high.

**F3. Tight stops on individual US stocks underperform buy-and-hold, mainly because of trading costs and short-horizon reversal.**
Lo and Remorov, "Stop-loss strategies with serial correlation, regime switching, and transaction costs" (2015/2017). Measured: US common stocks 1964-2014, daily stops from 0% to -6% and 10-day stops from 0% to -14%, with bid-ask costs included (0.2% half-spread in simulations; actual spreads where available in empirical tests). Results: tight stops significantly underperform in recent decades because of high trading costs and negative return autocorrelation; wide stops over 10-day windows roughly match buy-and-hold on a risk-adjusted basis, raise skewness and cut maximum drawdown; downside-risk reduction exists "but not substantially"; delaying the stop execution did better than immediate execution for tight stops (reversion).
Sources: https://dspace.mit.edu/handle/1721.1/107017 (thesis abstract) — FETCHED; details via CXO Advisory's review https://www.cxoadvisory.com/?p=27891 — FETCHED (secondary practitioner summary; the paper itself was not opened). Confidence: high on direction, medium on exact numbers. Note: the fetch tool described the serial-correlation condition as "mean-reverting"; that is a tool error. "Sufficiently high serial correlation" means positive autocorrelation, i.e. momentum.

**F4. Stops applied to a cross-sectional momentum portfolio cut crash losses sharply — gross of costs.**
Han, Zhou and Zhu, "Taming Momentum Crashes: A Simple Stop-Loss Strategy" (SSRN 2407199). Measured: US stocks 1926-2013, 6-month momentum deciles, long winners / short losers, daily stop monitoring. As summarised by CXO Advisory: a 15% stop raised the equal-weighted monthly return from 0.99% to 1.93%, Sharpe from 0.17 to 0.40, worst month from -49.8% to -17.4%. Results are gross, not net; frictions for stocks in stop-out conditions may be unusually high; parameter snooping and shorting feasibility are open concerns.
Sources: https://www.cxoadvisory.com/?p=25071 — FETCHED (secondary); SSRN page returned 403. A search snippet gave slightly different figures for a 10% stop (-49.79% to -11.34%), consistent with different versions/stop levels — SNIPPET. Confidence: medium.

**F5. On a trend-following index strategy, adding stop-loss rules did not help, and lower decision frequency beat higher frequency.**
Clare, Seaton, Smith and Thomas, "Breaking into the Blackbox: Trend Following, Stop Losses, and the Frequency of Trading: the case of the S&P500". Measured: ~60 years of S&P 500 data; moving-average and breakout rules. Month-end decision rules were superior to more frequent trading; popular stop-loss rules did not add value on top of the 200-day MA rule. Transaction-cost treatment not confirmed from the abstract.
Source: https://openaccess.city.ac.uk/id/eprint/17842 — FETCHED (abstract page) — confidence medium-high.

**F6. Profit targets and time stops: I found no rigorous, cost-inclusive study in this session showing that fixed profit targets add value.** By the same Kaminski-Lo logic a profit target is a "stop-gain": it helps under mean reversion and truncates the right tail (the source of most trend-following profit) under momentum. Treat this as reasoning, not as a cited finding.
Basis: UNVERIFIED / inference — confidence medium on the logic, no empirical citation.

Summary for Q1: exits are not universally good or bad. Stops are (weakly) justified for trend/momentum strategies and as catastrophe insurance; they are expected to be harmful for mean-reversion strategies; tight stops lose to costs in every study that included costs; the most reliable benefit is reduced drawdown/tail, not higher mean return.

### B. Continuous confidence recomputation

**F7. With trading costs, the optimal policy is to move only partially toward the new target and to weight slow-decaying signals more than fast ones.**
Garleanu and Pedersen, "Dynamic Trading with Predictable Returns and Transaction Costs" (NBER w15205; Journal of Finance 2013). Closed-form result ("aim in front of the target", "trade partially towards the aim"); empirical illustration on commodity futures showed better net returns than naive benchmarks. Implication: a position manager that fully exits on every fast-signal wobble is the opposite of the cost-aware optimum.
Source: https://www.nber.org/papers/w15205 — FETCHED (abstract) — confidence high.

**F8. More trading means lower net returns for individual accounts.**
Barber and Odean (Journal of Finance 2000): 66,000+ households at a discount broker, 1991-1996; the most active traders earned 11.4% net annualised versus 17.9% for the market index.
Source: search summary of https://faculty.haas.berkeley.edu/odean/papers/returns/returns.html — SNIPPET (page not opened) — confidence medium-high (widely replicated figure, also RECALLED).

**F9. The docs' own worked examples are examples of a noise-driven exit.** A drop from 72% to 54% (v1), 82% to 56% (v2) or 79% to 54% (v3) is treated as an exit trigger, but nothing in the docs establishes (a) the standard error of the confidence estimate, (b) that a fall in an order-flow feature predicts negative forward returns net of costs, or (c) hysteresis. A score recomputed every tick from order-flow and volatility features is highly autocorrelated noise; a threshold on it will be crossed repeatedly.
Basis: analysis of the three design documents — confidence high that the risk exists; magnitude unmeasured.

### C. Costs, slippage, paper vs live

**F10. Alpaca paper trading does not simulate market impact, latency slippage, queue position for resting limit orders, price improvement, regulatory fees or dividends.** Orders fill against NBBO when marketable; eligible orders get a random-size partial fill 10% of the time; default paper balance is $100k (which should be reset to the real intended capital). Borrow fees are listed as "coming soon".
Source: https://docs.alpaca.markets/docs/paper-trading — FETCHED — confidence high. This supports the v1 doc's research-anchor statement.

**F11. Alpaca crypto fees at the lowest tier (30-day volume under $100k): 0.15% maker, 0.25% taker**, charged on the asset received, posted end of day (page last updated 24 Sep 2025). A taker round trip is therefore 0.50% before spread.
Source: https://docs.alpaca.markets/docs/crypto-fees — FETCHED — confidence high (as of fetch).

**F12. Coinbase Advanced lowest-tier fees are reported by third parties as about 0.60% maker / 1.20% taker**, but the official fee page returned 403 and I could not verify. Treat as UNVERIFIED.
Source: https://www.coinbase.com/advanced-fees (blocked); third-party search snippets only — SNIPPET — confidence low.

**F13. Real retail equity market orders cost 0.07% to 0.46% per round trip depending on broker, excluding commissions.**
Schwarz, Barber, Huang, Jorion and Odean, "The 'Actual Retail Price' of Equity Trades", Journal of Finance 80(5), Oct 2025: 85,000 simultaneous real market orders across six accounts at five brokers; dispersion comes from wholesalers giving different prices to different brokers, not from PFOF levels. Whether Alpaca was among the brokers was not checked.
Source: https://ideas.repec.org/a/bla/jfinan/v80y2025i5p2507-2541.html — FETCHED (abstract) — confidence high.

**F14. Equity regulatory fees at Alpaca: FINRA TAF on sells and CAT fee on buys and sells, charged end of day; rates are on the disclosures page, not the docs page.** Rates not retrieved.
Source: https://docs.alpaca.markets/docs/regulatory-fees — FETCHED — confidence high on structure; rates UNVERIFIED.

**F15. Arithmetic check of the v1 BTC example.** $25 position, +1.1% move = $0.275 gross. Alpaca taker fees both ways = 0.50% x $25 = $0.125, leaving about $0.15 before spread. The document's "+$0.27 after costs" is therefore essentially the gross figure. At the (unverified) Coinbase 1.2% taker rate, round-trip fees of 2.4% exceed the whole 1.1% move and the trade loses money. The break-even move for a taker-in/taker-out crypto trade on Alpaca is over 0.5% plus spread.
Basis: computed from F11/F12 — confidence high for Alpaca, low for Coinbase.

**F16. The pattern-day-trader rule is gone.** FINRA Rule 4210 amendments (SEC-approved April 2026) replaced the PDT rule with an intraday-margin framework effective 4 June 2026; Alpaca states the equity threshold for 4x intraday buying power fell from $25,000 to $2,000, and pre-trade checks reject orders that would create or increase an intraday margin deficit.
Source: https://alpaca.markets/blog/finra-retires-the-pdt-rule-introducing-alpacas-new-intraday-margin-framework/ — FETCHED — confidence medium-high (broker blog; the FINRA notice itself was not opened). Treatment of cash accounts and paper accounts not stated.

### D. Order-handling correctness

**F17. Alpaca order types differ by asset class, and this constrains protective exits.**
- Equities: market, limit, stop, stop-limit, bracket, OCO, OTO, trailing stop. Trailing stops are held server-side but do not trigger outside regular hours; stop and market orders are rejected in extended hours (limit only); bracket orders cannot be extended-hours; GTC orders auto-expire after 90 days; fractional orders must be DAY; notional orders cannot be replaced; OTO orders cannot be replaced.
- Crypto: market, limit and stop-limit only; time-in-force GTC or IOC only; order_class is "simple" only (no bracket/OCO); no margin, no shorting.
Sources: https://docs.alpaca.markets/docs/orders-at-alpaca , https://docs.alpaca.markets/docs/crypto-orders , https://docs.alpaca.markets/reference/postorder , https://docs.alpaca.markets/docs/crypto-trading — all FETCHED — confidence high. (One fetch summary said crypto has no stop orders at all; the crypto-orders page lists stop_limit, which I take as authoritative.)

Consequences: (1) "SHORT" in crypto is not available at Alpaca spot — the docs' long/short/flat crypto design is long/flat only on this venue. (2) A crypto stop is a stop-limit, which can gap through and stay unfilled. (3) Equity positions held overnight have no working stop between 16:00 and 09:30 ET. (4) A fractional equity position cannot carry a GTC protective stop.

**F18. Client order IDs.** Alpaca: client_order_id up to 128 characters, must be unique per account, order retrievable by client ID; the docs do not spell out the error returned on a duplicate (forum reports mention 422) — duplicate behaviour UNVERIFIED and must be tested in paper. Coinbase Advanced Trade: if the client_order_id is not unique, no new order is created and the existing order is returned — true idempotency.
Sources: https://docs.alpaca.markets/reference/postorder , https://docs.alpaca.markets/docs/working-with-orders , https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/orders/create-order — FETCHED — confidence high (Coinbase), medium (Alpaca duplicate behaviour).

**F19. Order state machine and stream.** Alpaca statuses include new, partially_filled, filled, done_for_day, canceled, expired, replaced, pending_cancel, pending_replace, plus rarer accepted, pending_new, stopped, rejected, suspended, calculated. The trade_updates stream additionally emits order_replace_rejected and order_cancel_rejected. Fill events carry price, qty, timestamp and position_qty (position after the event). A cancel sent while an order is pending_replace is rejected. The streaming doc says nothing about replaying missed events after a reconnect, so a client must assume events are lost and re-query via REST.
Sources: https://docs.alpaca.markets/docs/orders-at-alpaca , https://docs.alpaca.markets/docs/websocket-streaming — FETCHED — confidence high; "no replay" is an absence-of-documentation inference, medium.

**F20. Cancel/replace races are real.** An Alpaca forum thread (May 2021, paper environment) documents an original order filling after a replace was accepted, with the user then selling the same shares twice and going accidentally short; staff attributed it to slow fill updates in paper. Whatever the cause, cancel and replace are requests, not guarantees.
Source: https://forum.alpaca.markets/t/replace-order-creates-a-new-order-successfully-but-the-old-order-is-filled-later-thus-creating-duplicate-order/5794 — FETCHED — confidence medium (single old report).

**F21. Emergency flatten exists as one call.** Alpaca's close-all-positions endpoint liquidates all long and short positions with market orders and accepts cancel_orders=true to cancel open orders first.
Source: https://docs.alpaca.markets/reference/deleteallopenpositions-1 — FETCHED — confidence high. Caveat from F17: market orders are rejected for equities outside regular hours, so this is not a 24-hour guarantee for stocks.

**F22. What a missing kill path costs.** Knight Capital, 1 Aug 2012: a mis-deployed router sent over 4 million orders while trying to fill 212 customer orders, within about 45 minutes, losing over $460 million; 97 automated warning emails were ignored; the SEC cited absent pre-trade order controls, exposure controls not linked to the account, and poor deployment procedures; $12 million penalty.
Source: https://www.sec.gov/news/press-release/2013-222 — FETCHED — confidence high.

## 3. What this means for the JARVIS design documents

**Supported**
- "Deterministic exits" (v3 Position Manager stack) and "pre-defined thesis-break rule" (v2 example). Deterministic, pre-registered exits are the right form.
- "Idempotent order service" (v3 Execution Agent). Both brokers support client IDs; Coinbase is explicitly idempotent.
- "Paper ... does not fully simulate market impact, queue position or latency slippage" (v1 research anchors) — confirmed and understated: fees, dividends and price improvement are also missing (F10).
- "Small capital can be dominated by fees/spreads" (v2) — confirmed quantitatively (F11, F15).
- Hard risk gate / kill switch with no LLM override (all three docs) — supported by F22.
- v3 step 8, "Compare predicted vs actual spread/slippage" — correct, but paper cannot supply the "actual" side; only live fills can.

**Weakened**
- Layer F's exit list (v1: "thesis invalidation; profit protection; time stop; volatility/trailing exit; state-change detection") is presented as uniformly good practice. The evidence says each exit type is strategy-dependent: stops help momentum at best, hurt mean reversion, and tight stops lose to costs (F1-F5). A single Exit Brain applying one menu to every strategy is not supported.
- "Recalculates the thesis after entry. If confidence deteriorates ... exit" (v3) and "confidence is recalculated and the position can be reduced or closed" (v1). As specified this is an unvalidated, high-frequency, threshold-on-noisy-score rule; F7-F9 say it is likely to raise turnover and cost with no demonstrated benefit. The "smaller profit, protected capital" narrative in all three examples is a claim that early exit beats holding; no evidence for it is offered, and the exits also truncate winners.
- "Tracks fills and cancels/replaces safely" (v3). "Safely" needs a specification: F19-F20 show the failure modes; the docs name none.
- "Streaming state" for the Position Manager with Redis as hot state for "positions, locks" (v3). If Redis is treated as the truth about positions, a crash or missed stream event leaves the system wrong. The broker is the only source of truth.

**Contradicted**
- v1 BTC example "+$0.27 after costs": at Alpaca's published fees the net is about $0.15 before spread; at Coinbase's reported fees it is a loss (F15). "Costs are small" is false at this size and horizon.
- LONG/SHORT/FLAT for crypto: Alpaca spot crypto cannot be shorted or margined (F17).
- Any implicit assumption that a protective stop can always be resting at the broker: not true for crypto beyond stop-limit, for equities outside regular hours, or for fractional GTC (F17).
- Docs written with the old $25k PDT constraint in mind (v3 "broker/account rules") are out of date in the owner's favour: intraday equity exits are no longer count-limited (F16), but intraday-margin pre-trade rejections now exist and must be handled as a normal order outcome.

**Missing entirely**
- No dead-man / system-death policy. The docs describe SAFE state for bad data but not what protects an open position when the laptop, Docker, network or power fails.
- No startup or periodic reconciliation step in the 10-step build order.
- No statement that every strategy carries its own exit specification, validated together with its entry.

## 4. Recommended changes

1. **Make exits part of the strategy definition, not a separate brain.** Each strategy registered in the Strategy Lab must declare its exit set (what invalidates it, time limit, catastrophe stop) and be backtested entry-plus-exit as one unit, with an ablation showing whether each exit rule improves net-of-cost results. Default priors from the literature: momentum/trend strategies may use wide, volatility-scaled or trailing stops; mean-reversion strategies use a time stop and a wide catastrophe stop only, never a tight price stop.
2. **Separate two kinds of stop.** (a) A wide catastrophe stop resting at the broker, justified as insurance against system death and gaps, not as alpha. (b) Strategy exits computed by JARVIS. Only (b) needs to earn its place by evidence.
3. **Redefine thesis invalidation as discrete, pre-registered, observable conditions written at entry**, for example: price closes beyond level X on the decision timeframe; the catalysing event is reversed or contradicted; the regime label changes and persists for N bars; the holding-period limit expires; a data-trust or manipulation flag fires. Store them in the ledger at entry so an exit can be audited against what was promised.
4. **If a continuous confidence score is kept, constrain it:** evaluate only on bar close of the strategy's own timeframe (not per tick); require an entry/exit hysteresis band (exit threshold well below entry threshold) and persistence over N evaluations; impose a minimum holding time and a per-position cap on re-evaluations that can trigger trades; require that the expected benefit of exiting exceeds the round-trip cost; prefer partial reduction over full exit (F7). Before it is allowed to trigger live exits, show out-of-sample that a confidence decline predicts lower forward net return. Until then, log it only (shadow mode).
5. **No same-signal re-entry for a cooling-off period** after a confidence-driven exit, to stop whipsaw loops.
6. **Cost model, minimum viable:** per-venue fee table loaded from config and dated; half-spread measured from live quotes at decision time; a slippage term calibrated from the system's own live fills; regulatory fees on equity sells. Gate every trade on expected edge exceeding a multiple of modelled round-trip cost. With Alpaca crypto at 0.50% taker round trip, intraday crypto scalps on $25 positions should be presumed unprofitable unless proven otherwise; prefer limit (maker) entries and longer horizons.
7. **Make paper results pessimistic on purpose:** add fees and a spread/slippage haircut on top of Alpaca paper fills, assume resting limit orders fill only when price trades through (not at) the limit, set the paper balance to the real planned capital, and treat paper as a test of plumbing rather than of profitability. Add a "micro-live" stage (smallest possible size) specifically to measure real slippage before any sizing-up.
8. **Order service specification:**
   - Write an intent record to PostgreSQL before any broker call; derive client_order_id deterministically from the intent (strategy, symbol, decision ID, attempt number). On timeout or unknown outcome, query by client_order_id before any resubmission. Test Alpaca's duplicate-ID response in paper and record it.
   - Maintain an explicit order state machine covering every status in F19, including pending_cancel, pending_replace, order_cancel_rejected and order_replace_rejected.
   - Treat cancel and replace as requests: do not submit a new order for the same exposure until the old one is in a terminal state; size any follow-up from the broker's reported filled quantity; a sell-to-close can never exceed the broker-reported position (use position_intent where available).
   - Partial fills: protective stop quantity follows filled quantity; define a policy for remainders (cancel after T seconds, never chase with market orders in thin conditions); handle dust below minimum order size.
   - Prefer broker-native bracket/OCO for equities so the exit pair is atomic server-side; for crypto, place a stop-limit immediately after the entry fill and monitor it.
9. **Reconciliation:** on every start, every stream reconnect, and on a timer, pull account, positions and open orders by REST and diff against the local ledger. The broker wins. Any unexplained difference puts the system in SAFE (no new risk) and alerts the owner. Never assume the stream replays missed events.
10. **System-death policy (new section for the docs):** every open position must have a broker-resting protective order where the venue allows one; positions that cannot be protected (equities overnight/extended hours, fractional GTC, crypto gaps) get smaller size limits in the Capital Governor; an external heartbeat watchdog (separate process or machine) alerts the owner on silence; a one-command manual flatten using the close-all endpoint with cancel_orders=true is documented and rehearsed; on restart the system reconciles first and manages existing positions before it may open new ones; no automatic "flatten everything on restart" (that converts an outage into forced selling at arbitrary prices).
11. **Insert a build step** between v3 steps 7 and 8: "order state machine, idempotency, reconciliation and failure-injection tests (kill the process mid-order, drop the network, duplicate a submission, replace during a fill)". Gate paper auto-execution on passing it.
12. **Correct the worked examples** to show fees honestly and to state that crypto is long/flat on Alpaca.

## 5. Open uncertainties

- Kaminski-Lo and Lo-Remorov full texts were not opened (405/403); findings rest on abstracts and one practitioner summary. The explicit mean-reversion statement in Kaminski-Lo is recalled, not re-read.
- No direct evidence was found on stop-loss or confidence-exit performance in crypto or at intraday horizons; all cited studies are US equities at daily-to-monthly frequency. Transfer is by reasoning only.
- No rigorous cost-inclusive study of fixed profit targets or time stops was located.
- Coinbase Advanced fee tiers unverified (official page blocked).
- Alpaca's exact response to a duplicate client_order_id, its actual equity regulatory fee rates, whether its stream replays anything after reconnect, and whether the replace race still occurs in live trading are all untested.
- How the post-PDT intraday-margin framework applies to cash accounts and to paper accounts was not stated in the source read; the FINRA notice itself was not opened.
- Whether Alpaca crypto is available in the owner's US state was not checked.
- Realistic slippage for $25-$500 orders at Alpaca specifically is unknown until measured live; Schwarz et al. give a range across brokers, not Alpaca's figure.
- Barber-Odean figures were taken from a search summary, not the paper page.

## 6. Source list

Fetched this session
- https://swopec.hhs.se/sifrwp/abs/sifrwp0063.htm — Kaminski and Lo abstract
- https://ideas.repec.org/a/eee/finmar/v18y2014icp234-254.html — Kaminski and Lo journal record
- https://dspace.mit.edu/handle/1721.1/107017 — Remorov thesis abstract (Lo-Remorov)
- https://www.cxoadvisory.com/?p=27891 — practitioner summary of Lo-Remorov
- https://www.cxoadvisory.com/?p=25071 — practitioner summary of Han-Zhou-Zhu
- https://openaccess.city.ac.uk/id/eprint/17842 — Clare, Seaton, Smith, Thomas
- https://www.nber.org/papers/w15205 — Garleanu and Pedersen
- https://ideas.repec.org/a/bla/jfinan/v80y2025i5p2507-2541.html — Schwarz et al.
- https://docs.alpaca.markets/docs/paper-trading
- https://docs.alpaca.markets/docs/orders-at-alpaca
- https://docs.alpaca.markets/docs/crypto-orders
- https://docs.alpaca.markets/docs/crypto-trading
- https://docs.alpaca.markets/docs/crypto-fees
- https://docs.alpaca.markets/docs/regulatory-fees
- https://docs.alpaca.markets/docs/websocket-streaming
- https://docs.alpaca.markets/docs/working-with-orders
- https://docs.alpaca.markets/reference/postorder
- https://docs.alpaca.markets/reference/deleteallopenpositions-1
- https://forum.alpaca.markets/t/replace-order-creates-a-new-order-successfully-but-the-old-order-is-filled-later-thus-creating-duplicate-order/5794
- https://alpaca.markets/blog/finra-retires-the-pdt-rule-introducing-alpacas-new-intraday-margin-framework/
- https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/orders/create-order
- https://www.sec.gov/news/press-release/2013-222 — Knight Capital

Attempted but not readable
- https://dspace.mit.edu/bitstream/handle/1721.1/114876/Lo_When%20Do%20Stop-Loss.pdf (405)
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2407199 (403)
- https://www.coinbase.com/advanced-fees (403)

Search-snippet only
- https://faculty.haas.berkeley.edu/odean/papers/returns/returns.html — Barber and Odean (2000)

## Independent verification (2026-10-01)

Re-opened or independently searched on 2026-10-01.

Confirmed
- F11 Alpaca crypto fees: tier 1 (0-$100k 30-day volume) 0.15% maker / 0.25% taker; 8 tiers; charged on the credited asset; page last updated 24 Sep 2025 (so a year old; re-check before relying). https://docs.alpaca.markets/docs/crypto-fees
- F16 PDT replacement: effective 4 June 2026; 4x intraday buying power threshold $25,000 to $2,000 for margin accounts. https://alpaca.markets/blog/finra-retires-the-pdt-rule-introducing-alpacas-new-intraday-margin-framework/
- F17 crypto order types: market, limit, stop_limit; TIF gtc and ioc only; fractional qty/notional supported. https://docs.alpaca.markets/docs/crypto-orders (order_class and no-shorting not stated on this page; rely on the other cited pages).
- F15 arithmetic holds at Alpaca fees (0.50% round trip taker on $25 = $0.125).

Corrected / weakened
- F4 Han-Zhou-Zhu: the SSRN abstract states a 10% stop, sample Jan 1926-Dec 2011, equal-weighted worst month -49.79% to -11.34% (value-weighted -65.34% to -23.69%). The 1.93% vs 0.99% monthly return and Sharpe 0.40 figures come from the later 1926-2013 version via CXO, and the stop level attached to them (brief says 15%) is not confirmed. Quote the stop level and sample period together, and treat all figures as gross of costs.
- F12 Coinbase: no official page read. Secondary sources say new users start at 0.40% maker / 0.60% taker (not 1.20% taker) and that Coinbase fee tiers update hourly and the full table is behind sign-in. The brief's 0.60% / 1.20% should not be relied on; the "loss at Coinbase fees" claim in F15 is unsupported. Verify by logging in. https://www.coinbase.com/Advanced-trade

Unverifiable this session
- Paper results (Kaminski-Lo full text, Lo-Remorov, Clare et al., Barber-Odean 11.4% vs 17.9%) not re-opened.
- Alpaca duplicate client_order_id response; cash/paper account treatment under the new margin framework (the Alpaca blog is silent).

Missed given owner constraints ($1k-$10k, US resident, near-zero budget)
- Alpaca crypto availability by US state was not checked; confirm for the owner's state before designing around it.
- Tax: US short-term capital gains, crypto trades are taxable events, wash-sale rule applies to stocks (not currently to crypto), and high turnover creates heavy record-keeping. Net-of-tax edge is lower than the brief's pre-tax view.
- Fees on the 0.15% to 0.25% tier mean any crypto strategy needs an expected edge above about 0.5% per round trip plus spread; at $1k-$10k the owner will stay in tier 1, so there is no volume discount path.
- Cash-account settlement (T+1) and good-faith rules were not addressed; with small capital a margin account is not advisable anyway.

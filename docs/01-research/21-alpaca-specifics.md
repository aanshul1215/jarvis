# 21 - Alpaca specifics (settling facts earlier briefs left open)

Date: 2026-10-01. Binding constraints: US resident, $1,000-$10,000 own money, near-zero budget, solo developer. Method: official Alpaca docs, blog, support pages, changelog and the Alpaca Customer Agreement PDF (version footer "V26.2026.07"), which I downloaded and decoded locally. Basis tags: FETCHED = opened this session; SEARCH-SNIPPET = seen only in a search result for the official URL, page itself not opened; UNVERIFIED = no source found.

## Questions

1. Is the News API (historical and streaming) in the free Basic plan? Limits, source, timestamps.
2. Crypto: supported US states, fee tiers, venue/spread, order types, fractional/minimum sizes.
3. Accounts under $2,000 after the PDT repeal: what intraday/day-trading rules apply?
4. Duplicate `client_order_id`, trade-update replay after reconnect, replace semantics, TIF/order types for fractional and extended hours, bracket/OCO/trailing.
5. Customer agreement / terms: limits on automation, data redistribution, remote dashboards.
6. IRA with API trading? Does paper enforce live rules?

## Findings

### 1. News API
- Source is Benzinga; archive back to 2015; about 130+ articles/day; stock and crypto symbols in one endpoint. FETCHED (docs.alpaca.markets/docs/historical-news-data). High.
- Historical endpoint `/v1beta1/news`: `limit` 1-50 (default 10), `symbols`, `start`/`end`, `sort`, `include_content`, `exclude_contentless`, `page_token`. Fields: `id, headline, author, source, created_at, updated_at, summary, content (may be HTML), symbols, images, url`. Timestamps RFC-3339. FETCHED (docs.alpaca.markets/reference/news-3). High.
- Streaming: `wss://stream.data.alpaca.markets/v1beta1/news`, subscribe `{"action":"subscribe","news":["*"]}` or symbols; same fields with `T:"n"`. FETCHED. High.
- Free-plan status: the only explicit pricing statement is the launch post of 2022-02-07: "News API is currently available for free with rate limits determined by current Market Data API subscription plans; 200 calls per minute for Free plans". The same post warns of possible later pricing changes. FETCHED (alpaca.markets/blog/introducing-news-api-for-real-time-fiancial-news/). The current plan-comparison docs (about-market-data-api) and /data pricing table do not list news at all, and neither the news reference nor the streaming page mentions a plan restriction. No source I found says news was removed from Basic. Conclusion: probably included, rate-limited at 200 calls/min, but no current official sentence confirms it. Medium.
- Not documented: the news websocket symbol cap for Basic (the equity Basic cap is 30 symbols; whether `*` news counts is unknown), and any history-depth cap on Basic. The 409 "insufficient subscription" error exists in the stream docs, so an entitlement gate is technically possible.
- Timestamp caution: `created_at` is Benzinga's article time, `updated_at` can change later. Neither is a first-seen time at JARVIS, so archive your own `received_at`. Design inference, not a doc claim.

### 2. Crypto
- States. Latest list seen: 28 jurisdictions "as of October 9, 2025": AZ, CA, CT, GA, ID, IL, IN, IA, KS, KY, ME, MD, MA, MI, MS, MO, MT, NE, NC, ND, OH, RI, SC, SD, UT, VT, WA, WV. SEARCH-SNIPPET of the official support URL (two searches returned identical text). Direct fetches of that page returned 404 or an older cached 25-state list (no AZ, SC, WV). Absent from the list: NY, TX, FL, NJ, PA, VA and others. The "49 US states" figure in Alpaca's 2025 review applies to Broker API partners, not Trading API retail. FETCHED. Medium for the list, high that it is a restricted subset. The owner's state decides crypto at Alpaca.
- Fees (docs crypto-trading, FETCHED, high): tier 1 (0-$100k 30-day volume) 15 bps maker / 25 bps taker; tier 2 12/22; tier 3 10/20; tier 4 8/18; tier 5 5/15; tier 6 2/13; tier 7 2/12; tier 8 ($100M+) 0/10. Fee charged on the credited asset, calculated and posted end of day. Alpaca's volume tiers are unreachable at $1k-$10k.
- ESTIMATE, round trip tier 1: taker both sides 2 x 0.25% = 0.50%; maker both sides 2 x 0.15% = 0.30%; $1,000 order = $2.50 per taker side. Spread not included.
- Venue: orders execute on the "Alpaca Exchange" order book (maker/taker language in docs). Price-band protection compares orders with external reference prices (docs name Coinbase, FalconX, StillmanDigital, from the Broker API page). Spread/depth on this venue is not documented. UNVERIFIED, test.
- Order types: market, limit, stop-limit; TIF `gtc` and `ioc` only; no plain stop, no DAY/FOK. Bracket/OCO: equity-only per the orders page. Neither margin nor shorting. 24/7, $200k notional cap per order. FETCHED. High. Conflict: the orders page table lists crypto stop-limit as GTC only, whereas the crypto page lists gtc and ioc for all types; test.
- Sizes: all assets fractionable; BTC/USD example `min_order_size 0.0001`, `min_trade_increment 0.0001`, `price_increment 1`; precision varies per asset; query `/v2/assets`. 20+ assets, 56 pairs. A minimum notional in dollars is not stated for crypto. FETCHED. Medium.

### 3. Under $2,000 after PDT
- FINRA 26-10 implemented: PDT designation, day-trade counts and DTBP removed; fields `pattern_day_trader`, `daytrade_count`, `daytrading_buying_power`, `dtbp_check`, `pdt_check` and related endpoints deprecated, removal date 2026-07-06. FETCHED (changelog 2026-06-03; blog dated 2026-04-27, updated 2026-06-04). High.
- Account type: no cash accounts; all are margin accounts, and equity under $2,000 gets multiplier 1 (limited margin, 1x). A 2026-era page repeats $2,000 equity for margin and shorting. FETCHED (docs margin-and-short-selling, account-plans; support/alpaca-cash-accounts, dated Dec 2022). High for multiplier 1, medium for "1x only below $2,000" (summarised page).
- Intraday margin: Alpaca says the 4x intraday buying power threshold moved from $25,000 to $2,000 for leverage-enabled accounts; "Standard $2,000 Reg T/Rule 4210 Minimum applies". Intraday margin deficit: call to be met within two business days; after non-compliance by day five, up to 90-day restriction on new debit or short increases; de minimis exemption for deficits under $1,000 or 5% of equity. The 1x-account page says the old 4-trade limit is gone and one may "enter and exit positions as frequently as you choose". FETCHED. High on text.
- What no Alpaca page states: how an account below $2,000 is treated for intraday round trips. The 1x page says it does not address them.
- Key catch (Customer Agreement section 32, V26.2026.07): Alpaca may phase in intraday margin and "may, in its sole discretion, continue to apply the former day trading margin requirements (including the pattern day trader designation) to any Account or category of Accounts" during the FINRA phase-in period, and may impose stricter intraday requirements without notice. FETCHED (decoded PDF). High. So "PDT is gone at Alpaca" is true as a general statement and not a guarantee for any given account.

### 4. Order mechanics
- `client_order_id`: max 128 chars, "must be unique", auto-generated if omitted. FETCHED (reference postorder). Behaviour on a duplicate (status code, whether it returns the original order, whether IDs of filled/cancelled orders can be reused) is not in the official docs I opened. The reference lists only 403 (buying power/shares) and 422 (parameters not recognised). Third-party reports say 422 "client_order_id must be unique" and uniqueness only against active orders; I did not open an Alpaca-authored source. UNVERIFIED. Test.
- Trade-update websocket: `wss://api.alpaca.markets/stream` and `wss://paper-api.alpaca.markets/stream`, auth then `listen` to `trade_updates`; binary frames. Events: new, fill, partial_fill, canceled, expired, done_for_day, replaced, plus accepted, rejected, pending_new/cancel/replace, calculated, suspended, order_replace_rejected, order_cancel_rejected. Replay on reconnect, delivery guarantees and connection limits are not documented. FETCHED. High on gap. Reconcile via REST (`GET /v2/orders`, positions) after every reconnect. Market-data streams: usually 1 connection per endpoint, error 406 on exceeding; auth within 10 s; 405 symbol limit; 409 insufficient subscription. FETCHED.
- Replace (`PATCH /v2/orders/{id}`): each given field overrides; response is a NEW order with new `id`; the old order gets status `replaced` and `replaced_by`, the new one `replaces`; `client_order_id` cannot be changed alone. "A success return code ... does NOT guarantee the existing open order has been replaced"; if the old order fills first, the replacement is rejected. Cannot replace in accepted, pending_new, pending_cancel, pending_replace. Notional (non-IPO) orders cannot be replaced. Replaceable: bracket and OCO (limit_price, stop_price), trailing stop (trail only, not price/percent switch); OTO not yet. FETCHED. High.
- TIF whole-share equities: market/limit GTC, DAY, IOC, FOK, OPG, CLS; stop and stop-limit GTC, DAY. GTC auto-cancels after 90 days. FETCHED. High.
- Fractional: market, limit, stop, stop-limit, DAY only; sells are marked long (no fractional shorting); minimum $1 notional; qty/notional to 9 decimals; non-fractionable asset rejects with "requested asset is not fractionable". Agreement section 28: dollar orders under $1.00 may be refused, repeated sub-$0.01 notional orders may restrict the account. FETCHED. High. Fractional orders therefore cannot rest overnight, and a GTC stop on a fractional position is impossible.
- Extended hours (4am-8pm ET plus overnight 8pm-4am): only limit orders, DAY or GTC, `extended_hours=true`; market/stop not accepted; brackets not allowed. FETCHED. High.
- Bracket, OCO, OTO: equities only, TIF DAY or GTC, regular hours only. Trailing stop: DAY/GTC, regular hours, equities. Crypto has no bracket/OCO/trailing. FETCHED. High.
- Wash-trade guard: opposite-side orders that could self-cross are rejected with 403; limit buy >= limit sell rejected; bracket, OCO and trailing stops exempt; applies to paper and to crypto. Equity/order ratio guard: new-position orders restricted when exposure exceeds 600% of equity (not crypto). FETCHED (user-protection).

### 5. Agreement and terms
- Automation: nothing in the Customer Agreement or Terms and Conditions restricts API or algorithmic trading. Alpaca's "Risks of Automated Trading" disclosure states the platform is not a high-frequency platform, that it "initially will only support algorithms that run on your own computer ... and not a server", and that Alpaca has no manual intervention process for stop losses. It is risk language, not a prohibition. FETCHED (decoded PDF). Medium on VPS implications.
- Discretion: Alpaca may refuse, restrict or terminate without notice (section 31), may tighten intraday margin without notice (section 32).
- Data: "I agree not to reproduce, distribute, sell or commercially exploit the market data in any manner without written consent" (section 30); AlpacaDB supplies data to non-professional customers; NASDAQ and NYSE display agreements incorporated. Terms and Conditions: use services and content "solely for your own personal and non-commercial purposes"; making them available to others via your own application needs 30 days' written notice. FETCHED. High. Neither document mentions remote dashboards; a private dashboard for the owner alone appears within personal use, but nothing explicit says so and the exchange agreements were not read. Medium. News content (Benzinga) redistribution terms were not found.
- Third-party access to the account needs a POA (section 16); credentials are the customer's responsibility. Arbitration under FINRA (section 46).

### 6. IRA and paper
- IRA with Trading API: yes. Blog dated 2026-05-13 (updated 2026-07-06): Roth or Traditional IRA for Trading API users who are US tax residents with an SSN, equities and options through the same API, ACH contributions, ACATS transfers, API use "similar to a taxable account". FETCHED. High. Broker-API docs add: 1x margin by default, no crypto (support page: "as of September 2024" crypto unsupported), options to level 2. The trustee is Equity Trust Company (Alpaca disclosure library); trustee fees apply under its fee schedule, amounts not read; the one fee statement found concerns Broker API partners. Paper IRA availability not stated. Medium.
- Paper: simulates margin, shorting, pre/post-market and crypto; does not simulate impact, information leakage, latency slippage, queue position, price improvement, regulatory fees or dividends; fills only when marketable; quantity not checked against NBBO; random 10% partial fills; default $100,000 balance, resettable; IEX data only; wash-trade protection applies. FETCHED. High. Whether paper enforces the new intraday-margin checks, the $2,000 shorting floor or crypto state limits is not documented. UNVERIFIED.

## What this decides for the JARVIS design

1. Treat Alpaca news as a probable free source, behind a start-up probe that fails soft. Archive `received_at` alongside `created_at`/`updated_at`. Keep EDGAR as the non-vendor fallback.
2. Gate the crypto sleeve on the owner's state: list is 28 jurisdictions, a year old. Budget 0.50% taker / 0.30% maker round trip; use limit orders (GTC or IOC only). Position exits cannot rest as brackets; stop-limit only.
3. Do not code day-trade counters. Do code: leverage cap 1.0, `max_margin_multiplier`/`no_shorting` set in account config, handling of rejections and intraday margin calls, and a defensive PDT-rejection handler (agreement section 32 lets Alpaca keep PDT per account). Prefer swing/daily horizons so the sub-$2,000 uncertainty barely matters.
4. Overnight protection needs whole shares and a GTC stop (or stop-limit) in regular hours; fractional positions cannot rest any stop. Size the first strategy with whole shares for names where the position will be held overnight, or accept process-dependent exits.
5. Order service: deterministic `client_order_id` for idempotence, but do not rely on duplicate rejection semantics until tested; after any 5xx/timeout look up by client ID before resubmitting. After every websocket reconnect, reconcile from REST. Never retry a replace blindly; the response can succeed while the fill wins, and the new order has a new ID.
6. Treat Alpaca's terms as compatible with a personal, own-money system and a private dashboard on the owner's own devices. Do not add outside viewers or redistribute data or news; run the 30-day notice route only if that ever changes.
7. IRA: a tax-advantaged API path exists for equities/ETFs (no crypto, 1x). It addresses the tax gap in 00-gap-analysis for a long/flat ETF strategy, subject to trustee fees and contribution limits (not computed here). Do a read of the fee schedule before choosing.
8. Paper is a plumbing test only; do not assume paper rejects what live would.

## Open uncertainties - only a real account (live or paper) can settle

1. Whether Basic returns news history and a news websocket without 403/409, the news symbol cap, and `created_at` vs first-seen latency.
2. Response and status code for a duplicate `client_order_id` while the first order is open, after fill, after cancel; whether it returns the original order; length/charset limits.
3. Whether trade_updates replays or drops events across a reconnect; behaviour on two connections on one key.
4. Live crypto: typical BTC/USD, ETH/USD spread and depth on Alpaca Exchange; minimum dollar notional; whether stop-limit IOC is accepted; the owner's state eligibility.
5. Whether a live sub-$2,000 account is still PDT-flagged or rejected on same-day round trips (agreement section 32 says it may be); the exact error codes and messages for intraday margin deficits.
6. Whether paper applies intraday-margin, shorting-equity and crypto-state rules like live; whether paper IRA exists.
7. Cancel/replace race frequency in live; behaviour of GTC stop on whole shares through splits/halts.
8. IRA trustee fee amount for a Trading API IRA; whether IRA trades settle T+1 without good-faith-violation limits.
9. Exchange data-agreement clauses (NASDAQ/NYSE, Benzinga) on remote viewing; not read.

## Source list

- Alpaca News overview: https://docs.alpaca.markets/docs/historical-news-data (FETCHED)
- News endpoint reference: https://docs.alpaca.markets/reference/news-3 (FETCHED)
- News stream: https://docs.alpaca.markets/docs/streaming-real-time-news (FETCHED)
- News launch post, 2022-02-07: https://alpaca.markets/blog/introducing-news-api-for-real-time-fiancial-news/ (FETCHED)
- Market data plans: https://docs.alpaca.markets/us/docs/about-market-data-api (FETCHED); https://alpaca.markets/data (FETCHED)
- WebSocket stream/error codes: https://docs.alpaca.markets/us/docs/streaming-market-data (FETCHED)
- Trade-updates stream: https://docs.alpaca.markets/us/docs/websocket-streaming (FETCHED)
- Crypto trading: https://docs.alpaca.markets/us/docs/crypto-trading (FETCHED); https://docs.alpaca.markets/us/docs/crypto-trading-1 (FETCHED)
- Crypto regions (not opened directly; text from search results of the official URL): https://alpaca.markets/support/what-regions-support-cryptocurrency-trading ; older list: https://alpaca.markets/support/alpaca-cryptocurrency (FETCHED); 2025 review: https://alpaca.markets/blog/alpacas-2025-in-review/ (FETCHED)
- Margin: https://docs.alpaca.markets/us/docs/margin-and-short-selling ; https://docs.alpaca.markets/us/docs/account-plans (FETCHED); https://alpaca.markets/support/alpaca-cash-accounts (FETCHED)
- Intraday margin: https://docs.alpaca.markets/us/docs/the-intraday-margin-rule ; https://docs.alpaca.markets/us/docs/intraday-margin-rule-for-non-leverage-margin-accounts ; https://docs.alpaca.markets/us/docs/understanding-finras-new-intraday-margin-rule-and-the-end-of-pdt ; https://docs.alpaca.markets/us/changelog/2026-06-03-pdt-651df23 ; https://alpaca.markets/blog/finra-retires-the-pdt-rule-introducing-alpacas-new-intraday-margin-framework/ (all FETCHED)
- Orders: https://docs.alpaca.markets/us/docs/orders-at-alpaca ; https://docs.alpaca.markets/reference/postorder ; https://docs.alpaca.markets/us/reference/replaceorderforaccount ; https://docs.alpaca.markets/reference/patchorderbyorderid-1 ; https://docs.alpaca.markets/us/docs/fractional-trading ; https://docs.alpaca.markets/us/docs/user-protection ; https://docs.alpaca.markets/reference/getaccountconfig-1 (FETCHED)
- Paper trading: https://docs.alpaca.markets/us/docs/paper-trading (FETCHED)
- Customer Agreement V26.2026.07: https://files.alpaca.markets/disclosures/library/AcctAppMarginAndCustAgmt.pdf (FETCHED, decoded locally)
- Terms and Conditions: https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf (FETCHED, decoded)
- Automated trading risks: https://files.alpaca.markets/disclosures/library/RisksAutoTrading.pdf (FETCHED, decoded)
- Disclosure library: https://alpaca.markets/disclosures (FETCHED)
- IRA: https://alpaca.markets/blog/alpaca-introduces-individual-retirement-accounts-for-trading-api-users/ ; https://docs.alpaca.markets/us/docs/ira-accounts-overview ; https://alpaca.markets/support/can-ira-trade-crypto (FETCHED)
- Duplicate-ID third-party reports (not authoritative, SEARCH-SNIPPET only): https://github.com/tim1016/learn-ai/issues/2304 ; https://forum.alpaca.markets/t/getting-422-when-trying-to-supply-client-order-id/12223


## Independent verification (2026-10-01)

Confirmed (re-fetched):
- Crypto fee tiers 15/25, 12/22, 10/20, 8/18, 5/15, 2/13, 2/12, 0/10 bps; order types market/limit/stop-limit; TIF gtc/ioc; min order 0.0001. Round-trip arithmetic (2 x 0.25% = 0.50%; 2 x 0.15% = 0.30%; $2.50 per $1,000 taker side) is correct. https://docs.alpaca.markets/us/docs/crypto-trading
- Intraday margin: $2,000 equity minimum, call satisfied within two business days, 90-day restriction if unmet by fifth business day, waiver if deficit < $1,000 or 5% of equity. https://docs.alpaca.markets/us/docs/the-intraday-margin-rule (the doc says "whichever is lower"; the brief omits that).
- client_order_id: unique, <=128 chars, auto-generated; postorder lists only 200/403/422; duplicate behaviour is undocumented. https://docs.alpaca.markets/reference/postorder
- Fractional: market/limit/stop/stop-limit with TIF day. https://docs.alpaca.markets/us/docs/fractional-trading
- IRA for Trading API users: announced 2026-05-13, updated 2026-07-06, equities and options, ACH/ACATS, no fee info on the page. https://alpaca.markets/blog/alpaca-introduces-individual-retirement-accounts-for-trading-api-users/
- News: launch-post wording (free, 200 calls/min on Free plans) re-confirmed; Basic plan table does not mention news. Still inferred, not currently confirmed. https://alpaca.markets/blog/introducing-news-api-for-real-time-fiancial-news/ ; https://docs.alpaca.markets/us/docs/about-market-data-api

Corrected / weakened:
- Fractional + extended hours: the fractional page says fractional shares can trade pre-market, post-market and overnight, so "fractional cannot rest overnight" is only a TIF=DAY consequence; do not assume extended-hour fractional behaviour, test it (the page text is internally ambiguous about market vs limit orders).
- PDT: sources conflict. The intraday-margin page says the PDT definition is eliminated; the FINRA-rule explainer page says a 12-month transition lets firms apply legacy PDT or new rules by account. Keep the brief's defensive PDT-rejection handler; do not treat "PDT gone" as certain per account.
- Basic market data: historical SIP data is limited to the latest-15-minutes delay boundary, WebSocket 30 symbols, 200 historical calls/min. Design must not assume full real-time SIP on Basic (IEX only).
- Margin call wording: one explainer says firms take a capital charge from day six; the Alpaca-facing 90-day restriction text matches the brief. Fine, but cite the-intraday-margin-rule.

Unverifiable this session:
- Crypto state list (28 jurisdictions as of Oct 9, 2025): the official support URL returned 404; search results only surfaced the older 25-state list (no AZ, SC, WV) from alpaca.markets/support/alpaca-cryptocurrency. Treat the list as unconfirmed; check the owner's state at signup. Also note the crypto docs page still dates itself to Nov 2022.
- Whether Basic actually serves news without 403/409; duplicate client_order_id status code; trade_updates replay; Customer Agreement section 32 text (PDF not re-opened here).

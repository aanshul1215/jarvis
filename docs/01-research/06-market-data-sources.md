# 06 - Market data sources: what a solo developer can really get, at what price, and is it point-in-time?

Research date: 2026-10-01. Every price/limit below was read from the vendor's own page in this session unless
marked RECALLED or UNVERIFIED. Pages were read through a fetch-and-summarise tool, so numbers should be re-checked
by eye on the vendor page before money is spent.

## 1. Questions asked

1. Equities: Alpaca free (IEX) vs paid (SIP), Massive (ex-Polygon), Tiingo, Databento, Norgate, EODHD, Sharadar -
   depth, real-time, L1/L2, adjustments, survivorship-bias-free universes, current prices.
2. Crypto: exchange websockets, historical trades / L2, cost.
3. Fundamentals/filings (SEC EDGAR APIs, Form 4, 13F, XBRL), rate limits; macro vintages (FRED/ALFRED).
4. News with reliable publication timestamps.
5. Tiered plan: free, ~$50/month, ~$300/month.

Authoritative source chosen per fact: vendor pricing page / API docs for prices and limits; sec.gov for EDGAR;
fred.stlouisfed.org for FRED; official GitHub README for Binance public data.

## 2. Findings

### 2.1 Equities

**Alpaca** (FETCHED, high) - https://docs.alpaca.markets/docs/about-market-data-api , https://alpaca.markets/data
- Basic (free): real-time **IEX only**; websocket limited to **30 symbols**; 200 REST calls/min; historical data
  "since 2016" but the **latest 15 minutes of SIP data are blocked**. In practice: free historical SIP bars/trades/
  quotes older than 15 minutes, free real-time only from IEX.
- Algo Trader Plus: **$99/month**; full SIP (all US exchanges) real-time; unlimited websocket symbols;
  10,000 calls/min; OPRA options.
- Alpaca's own docs state IEX is roughly **2.5% of market volume** and is for "initial app testing"
  (https://docs.alpaca.markets/docs/historical-stock-data-1 , FETCHED, high). IEX quotes are one venue's book, not
  the NBBO; volume, VWAP and any order-flow feature computed from IEX is not representative.
- Corporate actions: bars endpoint has `adjustment` = raw / split / dividend / spin-off / all, and an `asof`
  parameter for symbol renames (FB -> META) (https://docs.alpaca.markets/reference/stockbars , FETCHED, high).
- Depth is **L1 only** (trades + NBBO quotes). No equity L2/depth-of-book at any Alpaca tier (FETCHED by absence, medium).
- Minor inconsistency: docs say "since 2016", marketing page says "7+ years". Treat 2016 as the floor (medium).
- Survivorship: whether delisted symbols are fully retrievable from Alpaca history is UNVERIFIED.

**Massive (Polygon.io rebranded)** (FETCHED, high) - https://massive.com/pricing
- Stocks Basic $0: 5 calls/min, 2 years, end-of-day only.
- Stocks Starter **$29**: unlimited calls, 5 years, **15-minute delayed**, websockets, minute + second aggregates, no trades/quotes.
- Stocks Developer **$79**: 10 years, still 15-min delayed, adds tick trades.
- Stocks Advanced **$199**: 20+ years, **real-time**, trades and quotes. Labelled "Non-pros only".
- All individual tiers are "Individual use".
- Tickers endpoint has `active` and `date` parameters and a `delisted_utc` field, i.e. a point-in-time, delisted-
  inclusive ticker list can be built (https://massive.com/docs/rest/stocks/tickers/all-tickers , FETCHED, high).
  Whether price history for every delisted name is complete is UNVERIFIED.
- No L2 for equities on the pricing page (FETCHED by absence, medium).

**Tiingo** (FETCHED, high) - https://www.tiingo.com/about/pricing
- Starter $0: 50 req/hour, 1,000/day, 500 unique symbols/month, EOD prices with 30+ years history.
- Power **$30/month** individual ($50 commercial): 10,000/hour, 100,000/day, all symbols; adds IEX feed, crypto,
  news (only **3 months of queryable news history**), fundamentals as a paid add-on (15+ years).
- Licence: "internal use only" - may not display or share the data with another person.

**Databento** (FETCHED, medium - page partly truncated) - https://databento.com/pricing
- $125 free historical credit for new sign-ups (expires after 6 months). Usage-based historical priced per GB.
- Live data requires a subscription: Standard **$199/month**; Plus $1,750/month; Unlimited $4,500/month.
- Standard includes L1 history of 1 year and **L2/L3 (MBP-10 / MBO) history of only 1 month**; 16+ years of
  L2/L3 needs the $4,500 tier (or pay-per-GB historical).
- Databento is the only source here with true equity depth-of-book (e.g. Nasdaq TotalView) accessible to an
  individual, but exact per-dataset $/GB and exchange licence fees could not be read. UNVERIFIED.
- No crypto offering visible on the pricing page.

**Norgate Data** (FETCHED, high) - https://norgatedata.com/stockmarketpackages.php , https://norgatedata.com/data-content-tables.php
- US Stocks: Silver $270/yr, Gold $360/yr, **Platinum $630/yr (~$52.50/month)**, Diamond $787.50/yr.
- Only Platinum/Diamond contain **delisted securities** (Platinum back to 1990, Diamond to 1950) and
  **historical index constituents** (S&P 500 back to 1957, Russell from 1990). ~25,000 delisted securities.
- Daily bars only; adjusted for capital reconstructions and dividends. Delivered through a Windows updater
  application with Python bindings (RECALLED, medium).
- This is the cheapest verified survivorship-bias-free, index-membership-aware daily US equity dataset.

**EODHD** (FETCHED, medium) - https://eodhd.com/pricing
- $19.99 EOD (30+ years, 100k calls/day), $29.99 adds intraday, $59.99 fundamentals, $99.99 all-in-one. Page says
  delisted tickers are included on paid plans. Data quality and point-in-time status of fundamentals UNVERIFIED.

**Sharadar (Nasdaq Data Link)** - bundle = fundamentals + EOD prices + S&P 500 constituents + insiders + 13F + 8-K
events, 1998-present, explicitly "no survivorship bias: includes active and delisted tickers"
(https://www.quantrocket.com/pricing/data/sharadar , FETCHED, medium - a reseller page). **Price not obtainable
without login: UNVERIFIED.** Point-in-time via an as-reported dimension with filing date key is RECALLED, medium.

### 2.2 Crypto

- **Coinbase Advanced Trade websocket**: `level2`, `market_trades`, `ticker`, `candles`, `heartbeats` are public,
  no authentication, free (https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-channels ,
  FETCHED, high). Trades are batched every 250 ms. The design doc's claim about Coinbase is correct.
- **Kraken websocket v2 book**: public, depth 10/25/100/500/1000, CRC32 checksum on top 10 levels
  (https://docs.kraken.com/api/docs/websocket-v2/book , FETCHED, high). The checksum is directly useful for the Data Trust Gate.
- **Alpaca crypto**: free with both plans; trades, quotes, bars, order books over websocket; `us` endpoint is
  Alpaca's own venue, `us-1`/`eu-1` relay Kraken. Caveat: **Alpaca crypto bars are built from quote midpoints**, and
  show zero volume when no trade occurs (https://docs.alpaca.markets/docs/real-time-crypto-pricing-data , FETCHED, high).
  Alpaca's own crypto venue is thin; its book is not "the market".
- **Binance public data** (data.binance.vision): free klines, trades, aggTrades for spot and futures, daily files
  next day, SHA256 checksums, files occasionally re-issued (https://github.com/binance/binance-public-data , FETCHED, high).
  The README lists **no historical L2 order book**. Some futures book files may exist on the site: UNVERIFIED.
  Binance.com availability depends on the owner's jurisdiction (unknown).
- **Massive Currencies Starter $49/month**: real-time crypto trades and quotes, 10+ years, websockets; no L2
  (https://massive.com/pricing?product=currencies , FETCHED, medium).
- **Tardis.dev** (tick-level L2/L3 history, 50+ venues, 7+ years): Solo plans **$700-$1,200/month**
  (https://tardis.dev/ , FETCHED, medium). Free sample files exist; RECALLED detail that the first day of each month is free (medium).
- Conclusion: live crypto L2 is free; **historical crypto L2 is either self-recorded or costs >= $700/month**.

### 2.3 Filings, fundamentals, macro

- **SEC EDGAR APIs** (https://www.sec.gov/search-filings/edgar-application-programming-interfaces , FETCHED, high):
  data.sec.gov `submissions`, `companyconcept`, `companyfacts`, `frames`; no key; submissions updated in under a
  second, XBRL in under a minute; nightly bulk `companyfacts.zip` and `submissions.zip` (~3 a.m. ET).
- **Rate limit: 10 requests/second total across all machines**, declared User-Agent required, IP blocks for abuse
  (https://www.sec.gov/about/developer-resources , FETCHED, high).
- Point-in-time: each XBRL fact carries a `filed` date and accession number, and submissions carry an acceptance
  timestamp (RECALLED, high) - so EDGAR is natively point-in-time if you key on filing/acceptance time, never period end.
  Restated values appear as later facts; you must select "first filed value as of date T" yourself.
- **Insider Transactions Data Sets** (Forms 3/4/5), Jan 2006 - Jun 2026, quarterly flat files
  (https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets , FETCHED, high).
  Quarterly cadence is for backtests only; live Form 4 must come from the submissions API / EDGAR feeds.
- **Form 13F Data Sets**, Jul 2013 - Aug 2026, quarterly
  (https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets , FETCHED, high).
- **Financial Statement Data Sets**, 2009 - Jun 2026, quarterly, as-filed
  (https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets , FETCHED, high).
- SEC disclaims accuracy on all of these; XBRL tagging errors and custom tags are a known cleaning cost (RECALLED, medium).
- **FRED / ALFRED** (https://fred.stlouisfed.org/docs/api/fred/series_observations.html , FETCHED, high): free API key;
  `realtime_start`/`realtime_end`, `vintage_dates`, and `output_type` 1-4 (4 = initial release only) give true
  as-known-then values; up to 2,000 vintage dates (JSON) per request, 100,000 observations.
  Terms (https://fred.stlouisfed.org/docs/api/terms_of_use.html , FETCHED, medium): attribution notice required,
  limits may be imposed at discretion, third-party copyrighted series need owner permission beyond personal use.
  A first summarisation claimed a ban on trading use; a targeted re-read found **no** such clause. Low confidence
  either way - read the terms manually. Numeric rate limit (commonly cited 120/min) is RECALLED, medium.
  Not every series has vintages; market-price series (e.g. VIX, yields) are not revised (RECALLED, high).

### 2.4 News timestamps

- **Alpaca News (Benzinga)**: history back to 2015; fields `created_at` and `updated_at` (RFC-3339), headline,
  summary, content, symbols; 50 articles/page; real-time websocket exists
  (https://docs.alpaca.markets/docs/historical-news-data , https://docs.alpaca.markets/reference/news-3 , FETCHED, high).
  Whether news is fully included on the free plan is not stated on the pages read (believed yes; RECALLED, medium).
  Risk: `updated_at` means stored text may differ from what was visible at `created_at`.
- **Massive news**: `published_utc`, tickers, publisher, machine sentiment "insights"; included in all stock plans;
  history to 2016-06-22 (2 years on free); **updated hourly** - unusable for intraday reaction
  (https://massive.com/docs/rest/stocks/news , FETCHED, high).
- **Tiingo news**: the only source read that exposes **both** `publishedDate` (reported by the publisher) and
  `crawlDate` (recorded by Tiingo) - the correct pair for look-ahead control. But only 3 months queryable on Power;
  bulk history is institutional only (https://www.tiingo.com/documentation/news , FETCHED, high).
- **GDELT 2.0**: free, 15-minute updates, BigQuery/DOC API (https://www.gdeltproject.org/data.html , FETCHED, medium).
  Publication-vs-crawl timestamp semantics could not be confirmed; noisy entity mapping (RECALLED, medium).
- **EDGAR 8-K**: acceptance timestamp is an exchange-grade public-availability time (RECALLED, high) and is free.
- Institutional timestamped news (RavenPack, Dow Jones, Bloomberg) is out of budget; prices not checked. UNVERIFIED.
- No source read guarantees the archived article body equals what was first published.

## 3. What this means for the JARVIS design documents

- **Architecture doc "Alpaca: real-time stock/crypto WebSockets"** - supported, but the unstated catch is that free
  = IEX (~2.5% of volume, 30 symbols). The "always-on opportunity scanner" across the equity market is **not
  feasible on the free tier**; it needs $99/month SIP or a daily/delayed design.
- **v2 "Live trades/quotes/L2 order books", v3 Flow/Microstructure agent "L1/L2 feeds", Architecture "order-book
  imbalance"** - **contradicted for equities at this budget**. No equity L2 below Databento $199/month (1 month of
  L2 history); long L2 history is $4,500/month or pay-per-GB. Equity order-flow signals are untestable.
- **Crypto order-book signals (BTC/ETH worked examples)** - live data supported (free Coinbase/Kraken L2), but
  **cannot be backtested** without months of self-recording or >= $700/month. The 72% "calibrated confidence" in
  the BTC example has no data it could have been calibrated on.
- **"Point-in-time features" / Feast** - supported in principle for EDGAR (filed date) and FRED (ALFRED vintages);
  the docs' FRED/ALFRED and Form 4/13F statements are accurate. Weakened for news (timestamps are vendor-reported,
  articles get edited) and for prices (adjusted series are restated after every split/dividend - store raw +
  corporate-action table and adjust as-of).
- **Survivorship bias** - absent from all three documents. Free sources give no guaranteed delisted-inclusive
  universe; any multi-stock backtest on "today's tickers" is biased upward. Material omission.
- **Data Trust Gate "compare independent sources / quorum"** - supported and cheap: Kraken CRC32 checksum, Coinbase
  vs Kraken cross-check, Alpaca vs Tiingo EOD reconciliation. IEX vs SIP will legitimately disagree - not a quorum pair.
- **"Dashboard / daily summary for investors"** - conflicts with licences: Massive tiers are "individual use"/"non-
  pros only", Tiingo forbids displaying or sharing data, SIP non-professional status is lost when managing others'
  money (last point RECALLED, medium). Real investors mean professional data fees, an order of magnitude higher.
- **v1 pipeline (Reddit/Electrek/news)** - scraped social/news has no audited publication timestamp; treat as untrusted for backtests.

## 4. Recommended changes

1. Add a **bitemporal rule** to the Data Trust Gate: every record stores `event_time`, `vendor_publish_time`, and
   JARVIS's own `ingest_time`; features may only use rows with `ingest_time` (or vendor time + a latency buffer) <= decision time.
2. Start **self-recording crypto L2 + trades (Coinbase, Kraken) on day one** to Parquet; it is the only affordable
   route to a microstructure backtest. Forbid crypto order-flow strategies from going live until N months are recorded.
3. **Drop equity L2/microstructure from scope**; restrict equity horizons to daily-to-multi-day, where free/cheap data is adequate.
4. Make a **survivorship-bias-free universe a hard precondition** for any equity model validation (Norgate Platinum
   or Sharadar), with historical index membership.
5. Store **raw prices + corporate actions**, compute adjustments as-of; never train on a re-downloaded adjusted series.
6. Fundamentals: build from EDGAR `companyfacts` keyed on `filed`; macro: ALFRED `output_type=4`/vintages only.
7. News: use Alpaca/Benzinga `created_at` plus a conservative delay for backtests; archive live news with own receipt
   timestamp; never use the Massive hourly feed intraday; treat machine sentiment "insights" as possibly hindsight-generated.
8. Resolve the **"investors" question before buying data** - it changes every licence.

### Tiered data plan

**Free ($0)** - enough for a paper-trading, daily-horizon prototype
- Alpaca Basic: IEX real-time (30 symbols), SIP history >15 min old since 2016, adjustments, Benzinga news since 2015.
- Tiingo Starter: 30+ year EOD cross-check (500 symbols/month).
- Coinbase + Kraken public websockets (self-record L2/trades); Binance public trade/kline archives.
- SEC EDGAR APIs + quarterly data sets; FRED/ALFRED; $125 Databento credit as a one-off L2 sample.
- Limits: no survivorship-free universe, no real-time NBBO, no L2 history.

**~$50/month** - makes equity research statistically honest
- Free tier **+ Norgate US Stocks Platinum ($630/yr = $52.50/month)**: delisted names + historical index constituents, daily.
- Alternative if intraday bars matter more than survivorship: Massive Stocks Starter $29 (5 years of minute/second
  aggregates, delayed) + EODHD $19.99. My judgement: Norgate first, because biased validation invalidates everything downstream.

**~$300/month** - small live trading
- Alpaca Algo Trader Plus $99 (real-time SIP, unlimited symbols)
- Norgate Platinum $52.50
- Massive Stocks Developer $79 (10 years, tick trades, delayed) for intraday research
- Tiingo Power $30 (IEX + crypto + news with crawlDate, second-source reconciliation)
- Total about **$260**; remaining ~$40 toward Massive Currencies Starter ($49) or Databento pay-per-GB samples.
- Still not bought at $300: equity L2 history, historical crypto L2, institutional news. Those need $900+/month.

## 5. Open uncertainties

- Sharadar bundle price; Databento per-GB equity prices and exchange licence fees; what Standard $199 covers live.
- Whether Alpaca/Massive history is complete for delisted symbols.
- Whether Alpaca news is fully free and whether websocket news carries a receipt timestamp.
- FRED numeric rate limit and exact terms about commercial/trading use (two readings disagreed).
- GDELT timestamp semantics; Binance historical book files; Tardis free-sample policy.
- Owner's jurisdiction (Binance/Coinbase/Alpaca availability) and professional vs non-professional status.
- All prices read through an automated summariser on 2026-10-01; verify manually before purchase.

## 6. Source list (all FETCHED this session unless noted)

- https://docs.alpaca.markets/docs/about-market-data-api
- https://alpaca.markets/data
- https://docs.alpaca.markets/docs/historical-stock-data-1
- https://docs.alpaca.markets/reference/stockbars
- https://docs.alpaca.markets/docs/historical-news-data
- https://docs.alpaca.markets/reference/news-3
- https://docs.alpaca.markets/docs/crypto-pricing-data
- https://docs.alpaca.markets/docs/real-time-crypto-pricing-data
- https://massive.com/pricing and https://massive.com/pricing?product=currencies
- https://massive.com/docs/rest/stocks/news
- https://massive.com/docs/rest/stocks/tickers/all-tickers
- https://www.tiingo.com/about/pricing
- https://www.tiingo.com/documentation/news
- https://databento.com/pricing (partial; dataset and FAQ pages could not be read)
- https://norgatedata.com/stockmarketpackages.php and https://norgatedata.com/data-content-tables.php
- https://eodhd.com/pricing
- https://www.quantrocket.com/pricing/data/sharadar (reseller description of Sharadar; price not shown)
- https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-channels
- https://docs.kraken.com/api/docs/websocket-v2/book
- https://github.com/binance/binance-public-data
- https://tardis.dev/
- https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- https://www.sec.gov/about/developer-resources
- https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets
- https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets
- https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets
- https://fred.stlouisfed.org/docs/api/fred/series_observations.html
- https://fred.stlouisfed.org/docs/api/terms_of_use.html
- https://www.gdeltproject.org/data.html

## Independent verification (2026-10-01)

Re-fetched vendor pages (summarising fetch tool; eyeball before buying).

Confirmed:
- Norgate US Stocks: Silver $270, Gold $360, Platinum $630, Diamond $787.50 per year; only Platinum/Diamond include delisted securities and historical index constituents (back to 1990 / 1950). https://norgatedata.com/stockmarketpackages.php
- Alpaca: Free = $0, websocket 30 symbols, 200 calls/min, 15-min delay via REST plus real-time websocket (IEX); Algo Trader Plus $99/month, all US exchanges, unlimited websocket symbols; news and crypto in both. https://alpaca.markets/data
- Massive: Basic $0 (5 calls/min, 2y), Starter $29 (5y, 15-min delayed), Developer $79 (10y), Advanced $199 (real-time, 20y+). https://massive.com/pricing
- Databento: $125 free credit (6-month expiry); Standard $199/month adds live data; Plus $1,750 and Unlimited $4,500 need annual contract; usage-based historical pay-as-you-go exists. https://databento.com/pricing
- SEC: 10 requests/second total regardless of machines. https://www.sec.gov/about/developer-resources

Corrected:
- Tardis.dev pricing: brief says Solo $700-$1,200/month. Page shows plan ranges Perpetuals $350-$3,000, Spot $450-$3,500, All Exchanges $650-$6,000 per month across Academic/Solo/Professional/Business tiers. Cheapest entry is about $350-$450/month, still far above a near-zero budget; conclusion (self-record crypto L2) stands. https://tardis.dev/
- Alpaca Plus REST limit: marketing page says "unlimited API calls", brief says 10,000/min (docs figure). Use docs figure as the safe planning number.
- Databento L2 history: the pricing page read this session does not show the "L2/L3 only 1 month on Standard" claim, and it does show pay-as-you-go historical access to market depth. Do not state equity L2 history "costs $4,500/month"; it is purchasable per GB (price per GB unverified), so a small one-off L2 sample is affordable.
- Alpaca history: marketing page says 7+ years, docs say since 2016; both consistent with ~2016 floor.

Unverifiable this pass: IEX ~2.5% of volume (not re-fetched), Sharadar price, Coinbase/Kraken/FRED/EDGAR details not re-checked, Alpaca delisted-symbol coverage, Databento per-GB prices.

Missed considerations (owner: US resident, $1k-$10k, near-zero budget):
- At $1k-$10k capital, even $52.50/month Norgate is 6-60% annual drag on capital; a $99 SIP plan is unjustifiable. Free tier plus daily horizon is the only budget-consistent design; buy Norgate only after a paper-trading edge exists (annual billing $630 is the real cash outlay).
- Norgate is delivered through a Windows-only updater (RECALLED in brief, not confirmed here); owner is on Windows so fine.
- US-resident retail: Alpaca and Coinbase/Kraken availability are fine; Binance.com is not available to US residents (Binance.US has different data); drop Binance.com data dependency.
- Pattern day trader / small-account rules and commission-free spreads on IEX-only quotes matter more than data tier; tax lot/wash-sale tracking missing.

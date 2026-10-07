# 07 — Microstructure and Manipulation: are the Flow/Microstructure Agent and the Manipulation Surveillance Agent feasible for a retail laptop system?

Research date: 2026-10-01. Labels: FETCHED = opened in this session; RECALLED = from memory, not re-checked; UNVERIFIED = could not be opened or confirmed.
Access note: arXiv abstract pages and ar5iv full-text HTML renderings were readable. Raw PDFs, SSRN, and Coinbase fee/blog pages returned binary or HTTP 403, so some numbers come from the ar5iv rendering (read through a summarising fetch tool, not line-by-line by me). Where that matters I say so.

## Short verdict

- **Flow/Microstructure Agent as an alpha source: not realistic.** The literature shows order-flow imbalance (OFI) explains price changes *at the same moment* very well, but predicts *future* prices only for a few ticks / under about a minute, with gains smaller than retail fees by one to two orders of magnitude. Keep it as an **execution-quality and liquidity gate**, not as a signal generator.
- **Manipulation Surveillance Agent as a spoofing/layering/wash detector: not realistic.** Those are defined by intent and need participant-attributed order-lifecycle data that only venues and regulators hold. A retail observer can compute weak proxies only. Keep a narrow **"integrity risk filter"**: pump-and-dump burst detection on illiquid coins, venue whitelisting, cross-venue price sanity checks.
- The documents' worked example (a $100 account trading BTC/ETH intraday on order-flow signals, netting +$0.27) is not supported by the evidence found.

## Questions asked, and the authoritative source chosen for each

1. At what horizon does OFI / L2 imbalance predict returns, how fast does it decay, does it survive costs? Source: the original papers (Cont-Kukanov-Stoikov; Cont-Cucuringu-Zhang; Gould-Bonart; Xu-Gould-Howison; Kolm-Turiel-Westray; Briola-Bartolucci-Aste; the LOBCAST benchmark; one recent crypto paper).
2. What data does spoofing/layering/wash detection need, and what do public feeds expose? Source: CFTC interpretive guidance (legal definition), CAT NMS plan site, the academic spoofing studies, and the Coinbase and Alpaca API documentation.
3. Crypto pump-and-dump and wash trading: which signals are computable from public data? Source: Xu-Livshits; La Morgia et al.; Li-Shin-Wang; Cong-Li-Tang-Yang.
4. Retail cost floor. Source: Alpaca and Coinbase fee pages.

## Findings

### 1. Predictive power of order-flow imbalance and L2 features

**F1. The foundational OFI result is contemporaneous, not predictive.** Cont, Kukanov and Stoikov use one month (April 2010, 21 trading days) of TAQ data for 50 randomly chosen S&P 500 stocks. Over 10-second intervals, the mid-price change is linear in OFI *measured over the same interval*, with average R2 about 65% and a slope inversely proportional to depth. The paper makes no forecasting claim. This is the paper usually cited to justify "order-flow signals"; it does not justify them as forecasts.
Source: https://arxiv.org/abs/1011.6402 (abstract FETCHED; sample, 10-second grid and 65% R2 FETCHED via ar5iv rendering). Confidence: high.

**F2. Deeper book levels improve the contemporaneous fit — again not a forecast.** Xu, Gould and Howison (6 liquid Nasdaq stocks) find out-of-sample fit of the contemporaneous relation improves with each added price level.
Source: https://arxiv.org/abs/1907.06230 (FETCHED, abstract). Confidence: high on the direction; no numbers extracted.

**F3. When the same framework is turned into a forecast, predictability is tiny and gone within minutes.** Cont, Cucuringu and Zhang: top-100 S&P 500 stocks, Nasdaq ITCH data via LOBSTER, 2017-2019, 1-minute bars, 10:00-15:30.
- Contemporaneous out-of-sample R2: about 65% (best-level OFI), about 84% (integrated multi-level OFI).
- One-minute-ahead forecasting: out-of-sample R2 **slightly negative** (roughly -0.1% to -0.4%) for all models.
- Lagged cross-asset OFI helps a forecast-driven strategy somewhat, but the effect weakens at 2-5 minutes and is negligible by about 10 minutes and beyond.
- The economic-gain test **explicitly ignores trading costs**.
Source: https://arxiv.org/abs/2112.13213 (abstract FETCHED; numbers FETCHED via ar5iv rendering https://ar5iv.labs.arxiv.org/html/2112.13213). Confidence: high on the qualitative result (abstract states decay is rapid); medium on exact figures (extracted by a summarising tool; the reported "annualized PnL 0.4%" units were not checkable by me).

**F4. Queue imbalance predicts the direction of the next tick, mostly in large-tick stocks.** Gould and Bonart (10 liquid Nasdaq stocks): a statistically strong relation between queue imbalance and the direction of the *next mid-price move*; considerable improvement over the null for large-tick stocks, modest for small-tick. Horizon is one price change.
Source: https://arxiv.org/abs/1512.03492 (FETCHED, abstract). Confidence: high.

**F5. Deep learning on the order book: the "effective horizon" is about two price changes.** Kolm, Turiel and Westray (115 Nasdaq stocks, most granular order-book data; Mathematical Finance 33(4), 2023): models trained on order flow beat models trained on raw book states; the effective horizon of stock-specific forecasts is roughly two average price changes; "information-rich" stocks are more predictable. For liquid names two price changes is seconds or less (my inference; the abstract does not give clock time).
Source: https://ideas.repec.org/a/bla/mathfi/v33y2023i4p1044-1081.html (FETCHED, journal abstract). SSRN copy returned 403. Confidence: high on the abstract claims; costs treatment unverified.

**F6. High forecast accuracy does not translate into tradable signals, and models degrade on new data.**
- Briola, Bartolucci and Aste: 15 Nasdaq stocks, 2017-2019, horizons of 10/50/100 book updates. Predictive skill is best for large-tick stocks at the shortest horizon (MCC about 0.29) and near random for small/medium-tick stocks at 100 updates. Their "probability of a correctly executed complete transaction" stays low (below about 0.2). Abstract conclusion: forecasting power does not necessarily correspond to actionable signals.
  Source: https://arxiv.org/abs/2403.09267 (abstract FETCHED; numbers via ar5iv rendering). Confidence: high on conclusion, medium on exact figures.
- LOBCAST benchmark (Prata et al.): all tested LOB deep-learning models show a significant performance drop on new data.
  Source: https://arxiv.org/abs/2308.01915 (FETCHED, abstract). Confidence: high.

**F7. Crypto evidence is consistent, not an exception.** Bieganowski and Slepaczuk (Jan 2026): Binance Futures perpetuals, 1-second data, BTC/LTC/ETC/ENJ/ROSE, Jan 2022-Oct 2025. Order-book and trade features have stable importance across coins; backtests are run for taker and maker execution and diverge, with a flash-crash episode illustrating adverse selection for the maker side. The abstract does not claim robust net profitability.
Source: https://arxiv.org/abs/2602.00776 (FETCHED, abstract only). Confidence: medium (net-of-fee numbers not extracted; fee tier assumed in the paper unknown).

**F8. Retail cost floor versus signal size.**
- Alpaca crypto fees, lowest tier (30-day volume under $100k): maker 0.15%, taker 0.25% per side. Round trip as a taker: 0.50% before spread.
  Source: https://docs.alpaca.markets/docs/crypto-fees (FETCHED). Confidence: high.
- Coinbase Advanced: official fee page and blog returned 403. A search snippet of a Coinbase blog post dated September 2026 indicated substantially higher entry-tier US fees than Alpaca. **UNVERIFIED** — must be checked by hand.
- Inference (mine, not from a paper): a signal whose useful life is "two price changes" is worth on the order of a basis point or a few; a taker round trip at 50 bp is tens of times larger. Maker execution avoids the taker fee but incurs adverse selection and queue-position risk, which a laptop on home internet cannot manage against co-located participants. The papers that report positive gains (F3) exclude costs.
- Latency: no paper I opened measures retail latency directly. That OFI alpha lives at a few ticks is from F4/F5; that a home connection plus an LLM call (seconds) is too slow for it is my inference. Confidence: high on direction.

### 2. What spoofing / layering / wash-trade detection requires versus what public feeds expose

**F9. Spoofing is defined by intent.** CFTC guidance on CEA section 4c(a)(5)(C) defines spoofing as bidding or offering with intent to cancel before execution, requires intent beyond recklessness, and says the Commission distinguishes it from legitimate cancellation by looking at market context and *the person's pattern of trading activity, including fill characteristics*. That evidence is participant-level by construction.
Source: https://www.cftc.gov/LawRegulation/FederalRegister/FinalRules/2013-12365.html (FETCHED; 78 FR 31890, 28 May 2013). Confidence: high.

**F10. Regulators use attributed order-lifecycle data that the public cannot access.** The Consolidated Audit Trail tracks orders through their life cycle and identifies the broker-dealers handling them, for use by regulators.
Source: https://www.catnmsplan.com/ (FETCHED). Confidence: high on purpose; details of customer-ID fields not extracted.

**F11. The empirical spoofing literature uses account-level data.** Lee, Eom and Park (J. Financial Markets 16(2), 2013) used complete Korea Exchange intraday order and trade data *with account identification*; spoofing targeted volatile, smaller-cap stocks, and fell sharply after the exchange changed its order-disclosure rule.
Source: https://ideas.repec.org/a/eee/finmar/v16y2013i2p227-252.html (seen via search-result summary only, page not opened — treat as RECALLED/partly verified). Confidence: medium.
A Level-2-only approach exists (Tao, Day, Ling, Drapeau, TMX Level 2 data, imbalance model plus Wasserstein-distance monitoring), but it identifies *conditions under which spoofing would be profitable/likely* and anomalous imbalance, not attributed spoofing.
Source: https://arxiv.org/abs/2009.14818 (FETCHED, abstract). Confidence: medium; no validated precision/recall against labelled cases found.

**F12. What the feeds in the JARVIS stack actually expose.**
- Alpaca equities stream: trades, quotes (best bid/offer), bars, corrections, LULD bands, trading status, order imbalances. **No depth-of-book channel for equities** is documented. Feeds: SIP, IEX, delayed SIP, overnight.
  Source: https://docs.alpaca.markets/docs/real-time-stock-pricing-data (FETCHED). Confidence: high.
- Alpaca crypto stream: trades, quotes, bars, orderbooks. Order book is price/size levels only, no order IDs; sourced from Alpaca's own venue (or Kraken for certain locations) — i.e. a single small venue's book, not the global BTC market.
  Source: https://docs.alpaca.markets/docs/real-time-crypto-pricing-data (FETCHED). Confidence: high.
- Coinbase Exchange websocket: `level2`/`level2_batch` give aggregated price/size (batched at 50 ms for `level2_batch`); `full`/`level3` give per-order messages with order IDs. No account identity for other participants' orders. The fetch reported `level2_batch` as usable without authentication and the others as requiring it.
  Source: https://docs.cdp.coinbase.com/exchange/websocket-feed/channels (FETCHED). Confidence: high on content of channels; medium on authentication details.

**Consequence.** With equities, JARVIS would have L1 only (via Alpaca), so cancel-to-trade ratios, layering patterns and "suspicious order cancellations" cannot be computed at all. With crypto, Coinbase L3 allows order-lifetime statistics (large orders placed away from touch and cancelled quickly, book-depth flicker), but with no participant ID one cannot link the cancelled order to an opposite-side fill by the same actor, which is the core of a spoofing finding. Wash trades (same beneficial owner on both sides) are invisible on a public tape by definition. What is obtainable is an **anomaly score with unknown false-positive rate**, and no labelled ground truth exists to calibrate it.

### 3. Crypto pump-and-dump and wash trading from public data

**F13. Pump-and-dumps are frequent, tiny-cap, and over in seconds.** Xu and Livshits: 412 Telegram-organised events, June 2018-Feb 2019, mostly Cryptopia (51%) and Yobit (27%), also Binance and Bittrex. In their case study the price peaked about 18 seconds after the announcement. A random-forest model predicting *which coin will be pumped* reports AUC above 0.9; the simulated strategy return (60% in about 11 weeks) rests on assumptions (capturing half the pump gain), on hourly data, and on exchanges of which the main one has since closed. Fees/slippage were not clearly modelled.
Source: https://arxiv.org/abs/1811.10109 (abstract FETCHED; details via ar5iv rendering). Confidence: high on descriptive facts; low on the strategy return being reproducible in 2026.

**F14. Real-time detection from the public trade tape works — as a warning.** La Morgia, Mei, Sassi and Stefa (ICCCN 2020): 343 events across 44 exchanges (July 2017-Jan 2019), detailed work on 104 Binance events. Key feature: bursts of "rush orders" (aggressive market buys) plus volume/trade-count/price statistics in short windows. Reported about 93% precision and 91% recall with 25-second windows. Members higher in the group hierarchy receive the signal 0.5-8 seconds earlier; targets were mostly coins under about $20M market cap.
Source: https://arxiv.org/abs/2005.06610 (abstract FETCHED; numbers via ar5iv rendering). Confidence: medium-high. Caveat: labelled 2017-2019 data, Binance small caps; out-of-period performance unverified.

**F15. Outsiders lose.** Li, Shin and Wang (JFQA): P&Ds produce short spikes in price, volume and volatility followed by quick reversals; price run-ups before the start suggest wealth transfer from outsiders to insiders; exchange policy changes banning P&Ds were associated with better liquidity and prices.
Source: https://jfqa.org/wp-content/uploads/2025/01/24639_Cryptocurrency-Pump-and-Dump.pdf (abstract seen via search result; PDF not opened — partly verified). Confidence: medium-high.

**F16. Wash trading is detectable statistically at exchange level, not trade level.** Cong, Li, Tang and Yang: 29 exchanges; tests on first-significant-digit (Benford) distribution, trade-size rounding/clustering, and tail distribution of trade sizes. Regulated exchanges look like normal markets; unregulated ones show anomalies, with wash trades estimated at about 70% of reported volume on average.
Source: https://arxiv.org/abs/2108.10984 (FETCHED, abstract). Confidence: high on headline; the data period and which named exchanges fall in which tier were not extracted. The method flags *venues*, not individual trades — usable as a one-off venue-quality screen, not a streaming signal.

## What this means for the JARVIS design documents

| Document claim | Status | Why |
|---|---|---|
| v3 agent "Flow / Microstructure Agent: reads spread, trade imbalance, liquidity, depth/order-flow features when the feed supports them" | **Supported only as a cost/liquidity monitor.** The hedge "when the feed supports them" is important and correct | F12: no equity L2 via Alpaca; F1-F6: imbalance is explanatory, not usefully predictive at agent timescales |
| Architecture doc: scanner uses "order-book imbalance" to find opportunities; "order-flow" forecasting models in the ensemble | **Contradicted as an alpha source** | F3 (negative 1-min OOS R2, gone by ~10 min), F5 (two price changes), F6, F8 |
| Worked examples: $100 account, BTC/ETH intraday, entries and exits driven by order-flow, "order-flow weakens ... confidence falls 72% -> 54%" | **Contradicted** | Order-flow state changes many times per second; a per-minute confidence recomputed from it is noise. 50 bp taker round trip (F8) dominates the claimed edge |
| v2/v3 "Manipulation Surveillance: spoofing/layering-like order behaviour, wash-trade signals, momentum ignition, suspicious cancel-to-trade behaviour" | **Weakened to largely infeasible** | F9-F12: intent- and identity-based; equities feed has no depth; crypto feed has no identities |
| v2 wording "never claims a crime occurred; treats these as integrity red flags" | **Supported** — the right epistemic stance | F9 |
| "Low-liquidity social pumps or unexplained price/volume bursts raise Manipulation Risk" | **Supported** | F13-F15: detectable from the public tape within seconds |
| "Cross-venue inconsistencies / venue divergence" | **Supported as a data-quality check**, belongs in the Data Trust Gate | F12 (Alpaca crypto book is one small venue), F16 |
| "High risk reduces size or blocks the trade" | **Supported for block; do not use the score to enter trades** | F13-F15: outsiders reacting to a pump are late by construction |
| Architecture doc note that Alpaca paper trading does not simulate queue position, impact or latency | **Supported and under-weighted** | Any microstructure strategy validated in that paper environment is unvalidated |

## Recommended changes

1. **Rename and re-scope the Flow/Microstructure Agent to "Liquidity & Execution-Cost Monitor".** Deterministic code, no LLM. Outputs: quoted spread, depth at touch (crypto only), recent realised volatility, estimated round-trip cost in bp, a stale/crossed-quote flag. It may veto or downsize a trade when cost exceeds a fraction of expected edge. It must not emit a directional signal or contribute to "signal confidence".
2. **Remove order-flow/OFI models from the forecasting ensemble for v1**, and remove order-book imbalance from the opportunity scanner. Defer indefinitely; revisit only if a recorded-data study shows edge net of the owner's actual fee tier with maker-fill simulation.
3. **Add an explicit minimum-horizon rule**: no strategy whose expected holding period is under roughly 30 minutes, and no trade whose expected gross move is under a multiple (suggest at least 3x) of measured round-trip cost. This follows from F3/F5/F8 and removes the scalping examples.
4. **Rewrite the worked examples** so they do not depict order-flow-driven intraday BTC/ETH trades on $100.
5. **Shrink the Manipulation Surveillance Agent to an "Integrity Risk Filter"** with three deterministic components:
   - Pump-burst detector for crypto: abnormal aggressive-buy count, volume and price z-scores in 5-30 second windows (La Morgia-style features), especially on small-cap pairs. Action: block new entries, tighten exits.
   - Universe/venue hygiene: trade only on regulated venues and above liquidity/market-cap floors; this alone removes most P&D and wash-volume exposure (F13, F14, F16). Never use volume reported by unregulated venues as a feature.
   - Cross-venue price sanity check, placed in the Data Trust Gate.
6. **Cut from scope**: spoofing detection, layering detection, wash-trade detection, cancel-to-trade analysis, "momentum ignition" classification. If retained as an experiment, label it "book-instability anomaly score", crypto-only, logging-only, with no authority over sizing until a false-positive rate is measured.
7. **Never trade pump predictions.** F13's strategy is not reproducible on regulated venues in 2026 and knowingly buying ahead of a coordinated pump carries legal risk; the detector is defensive only.
8. **If L2/L3 research is ever wanted**, record Coinbase `level2_batch` to Parquet first and study offline. Be aware a full L3 feed for a few pairs is a continuous high-message-rate stream; storage and CPU on a laptop are a real cost (not measured here).

## Open uncertainties

- Coinbase Advanced / Exchange current fee tiers: official pages returned 403; search snippet suggests a September 2026 change. Must be read manually before any cost model is fixed.
- Exact figures from Cont-Cucuringu-Zhang, Briola et al., La Morgia et al., and Xu-Livshits were extracted via a summarising fetch of ar5iv HTML, not read line-by-line; verify before quoting in a design document.
- Kolm-Turiel-Westray: clock-time equivalent of "two price changes" and any cost analysis not verified (SSRN blocked).
- No peer-reviewed study was found that measures OFI profitability at *retail* fee tiers and *retail* latency; the conclusion that it does not survive is an inference from horizon length versus fees, albeit a strong one.
- No study was found validating L2-only spoofing detection against enforcement-labelled cases; absence of evidence, not proof of impossibility.
- Whether pump-detection performance (2017-2019 Binance labels) holds on 2026 venues is untested.
- Li-Shin-Wang and Lee-Eom-Park were confirmed via search summaries only; the Bitwise/SEC material on fake volume could not be read.
- Equity depth-of-book from other vendors (prices, licensing) was not researched here; Alpaca's documented equity stream has none.
- Owner's jurisdiction is unknown; venue availability, fee tiers and the legal framing of manipulation differ outside the US.

## Source list

Fetched this session
- Cont, Kukanov, Stoikov, "The Price Impact of Order Book Events" — https://arxiv.org/abs/1011.6402 (+ ar5iv rendering)
- Cont, Cucuringu, Zhang, "Cross-Impact of Order Flow Imbalance in Equity Markets" — https://arxiv.org/abs/2112.13213 ; https://ar5iv.labs.arxiv.org/html/2112.13213
- Gould, Bonart, "Queue Imbalance as a One-Tick-Ahead Price Predictor in a Limit Order Book" — https://arxiv.org/abs/1512.03492
- Xu, Gould, Howison, "Multi-Level Order-Flow Imbalance in a Limit Order Book" — https://arxiv.org/abs/1907.06230
- Kolm, Turiel, Westray, "Deep order flow imbalance" (Mathematical Finance 2023) — https://ideas.repec.org/a/bla/mathfi/v33y2023i4p1044-1081.html
- Briola, Bartolucci, Aste, "Deep Limit Order Book Forecasting" — https://arxiv.org/abs/2403.09267 ; https://ar5iv.labs.arxiv.org/html/2403.09267
- Prata et al., "LOB-Based Deep Learning Models for Stock Price Trend Prediction: A Benchmark Study" — https://arxiv.org/abs/2308.01915
- Bieganowski, Slepaczuk, "Explainable Patterns in Cryptocurrency Microstructure" — https://arxiv.org/abs/2602.00776
- Tao, Day, Ling, Drapeau, "On Detecting Spoofing Strategies in High Frequency Trading" — https://arxiv.org/abs/2009.14818
- Xu, Livshits, "The Anatomy of a Cryptocurrency Pump-and-Dump Scheme" — https://arxiv.org/abs/1811.10109 ; https://ar5iv.labs.arxiv.org/html/1811.10109
- La Morgia, Mei, Sassi, Stefa, "Pump and Dumps in the Bitcoin Era" — https://arxiv.org/abs/2005.06610 ; https://ar5iv.labs.arxiv.org/html/2005.06610
- Cong, Li, Tang, Yang, "Crypto Wash Trading" — https://arxiv.org/abs/2108.10984
- CFTC, Antidisruptive Practices Authority, Interpretive Guidance and Policy Statement (78 FR 31890) — https://www.cftc.gov/LawRegulation/FederalRegister/FinalRules/2013-12365.html
- CAT NMS Plan — https://www.catnmsplan.com/
- Coinbase Exchange websocket channels — https://docs.cdp.coinbase.com/exchange/websocket-feed/channels
- Alpaca real-time crypto data — https://docs.alpaca.markets/docs/real-time-crypto-pricing-data
- Alpaca real-time stock data — https://docs.alpaca.markets/docs/real-time-stock-pricing-data
- Alpaca crypto fees — https://docs.alpaca.markets/docs/crypto-fees

Seen only via search-result summary (not opened)
- Lee, Eom, Park (2013), J. Financial Markets — https://ideas.repec.org/a/eee/finmar/v16y2013i2p227-252.html
- Li, Shin, Wang, "Cryptocurrency Pump-and-Dump Schemes", JFQA — https://jfqa.org/wp-content/uploads/2025/01/24639_Cryptocurrency-Pump-and-Dump.pdf
- Coinbase blog on Advanced fee changes (Sept 2026) — https://www.coinbase.com/blog/were-lowering-fees-for-many-active-traders-on-coinbase-advanced (403)

Attempted, unreadable
- SSRN 3900141 (403); https://www.coinbase.com/advanced-fees (403); https://help.coinbase.com/en/exchange/trading-and-funding/exchange-fees (403); SEC release 34-87267 PDF (binary).


## Independent verification (2026-10-01)

Confirmed
- Alpaca crypto fees: tier 1 (under $100k/30d) maker 0.15%, taker 0.25%; page last updated 2025-09-24. https://docs.alpaca.markets/docs/crypto-fees
- Alpaca stock stream has no depth-of-book channel (trades, quotes, bars, LULD, status, order imbalances). https://docs.alpaca.markets/docs/real-time-stock-pricing-data
- Cong et al.: 29 exchanges, wash trading over 70% of reported volume on UNREGULATED exchanges (brief's "on average" should be scoped to unregulated). https://arxiv.org/abs/2108.10984
- Cont-Cucuringu-Zhang abstract: lagged cross-asset OFI improves forecasts but decays rapidly; abstract mentions no costs. https://arxiv.org/abs/2112.13213

Corrected / resolved
- Coinbase Advanced US entry tier is now 0.50% maker / 0.90% taker (effective 2026-09-16; tiers start at $10,000 volume, down from $25,000). Secondary reporting (not Coinbase's own page, which returned 403): https://www.securities.io/coinbase-lowers-advanced-trading-fees-with-tiers-starting-at-10-000/ . Fees for accounts under $10,000 volume were not stated; for a $1k-$10k owner they are likely at or above this. Round trip taker about 1.8%, versus about 0.50% on Alpaca crypto. Cost model must use these numbers, re-read from Coinbase by hand.
- La Morgia et al. arXiv page was revised Sept 2024; the 93%/91% figures were not visible in the abstract and remain unverified from the primary text.

Unverifiable this pass
- La Morgia precision/recall figures, Lee-Eom-Park, Li-Shin-Wang, Kolm et al. cost treatment, Coinbase level2_batch authentication.

Missed considerations (owner: US resident, $1k-$10k, near-zero budget)
- Fees dominate: at 0.5-1.8% round trip, any sub-30-minute strategy is dead; supports the brief's minimum-horizon rule.
- Pattern day trader rule and wash-sale/tax-lot recordkeeping for frequent trading; crypto gains are taxable events per trade.
- Free/paid data limits: Alpaca free equity feed is IEX-only, so quotes and imbalances are not consolidated market data.
- Laptop uptime and home-internet reliability, not only latency.

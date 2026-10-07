# 09 — Where is the edge? Evidence on return-predicting signals at retail-tradable horizons

Research date: 2026-10-01. Basis labels: **FETCHED** = I opened the page (or an official abstract/repository page for it) in this session; **SEARCH** = seen only in a search-engine summary of the named paper this session (treated as weaker than FETCHED, reported as RECALLED-grade in the structured summary); **RECALLED** = from memory, not re-checked. Where a full PDF could not be parsed I say so.

## 1. Questions asked (and the source type I treated as authoritative)

| Fact needed | Authoritative source type |
|---|---|
| How much do published equity signals decay out of sample / after publication / after costs? | Peer-reviewed meta-studies (McLean-Pontiff JF 2016; Chen-Velikov JFQA 2023; Novy-Marx-Velikov RFS 2016; Jensen-Kelly-Pedersen JF 2023) |
| Is PEAD still alive? | Martineau, Critical Finance Review 2022 |
| News / LLM / social sentiment evidence | Ke-Kelly-Xiu (NBER), Lopez-Lira-Tang (arXiv), Cookson et al. (JFE 2024), Bradley et al. (RFS 2024) |
| Insider Form 4 signal | Cohen-Malloy-Pomorski (JF 2012) |
| Crypto momentum / trend / carry | Liu-Tsyvinski-Wu (JF 2022), Grobys-Sapkota (Econ Letters 2019), BIS WP 1087, He et al. (arXiv 2212.06888), Zarattini et al. (SSRN/SFI) |
| Intraday prediction, net of cost | Briola et al. (arXiv 2403.09267), Gao et al. (JFE 2018), Zarattini et al. (SFI 24-97), day-trader population studies (Chague et al.; Barber et al.) |
| Do backtests and LLM agents hold up? | Wiecki et al. (Quantopian), FINSABER (arXiv 2505.07078), Avramov-Cheng-Metzker (Mgmt Sci 2023) |
| What does a round trip cost a tiny account? | Broker official fee docs (Alpaca) |

## 2. Findings

### 2.1 Equities — the general picture: published edges shrink by more than half, and costs take most of the rest

- **Post-publication decay.** McLean & Pontiff study 97 published cross-sectional predictors: long-short returns are 26% lower out of sample and 58% lower after publication; decay is larger for predictors with higher in-sample returns, and surviving returns sit in illiquid, high-idiosyncratic-risk stocks. Source: search summary of JF 2016 paper (https://ivey.uwo.ca/media/3775549/pontiff.pdf). SEARCH; confidence high (widely replicated headline numbers).
- **After costs.** Chen & Velikov: net of effective bid-ask spreads, post-publication decay and restricted to the post-2000s electronic era, the average anomaly's expected return is ~8 bps/month in the Fed working paper (120 anomalies) and ~4 bps/month in the published JFQA version (204 anomalies); the best net 10–20 bps/month after data-mining adjustment. Price impact is *not* included, so this is optimistic. Source: https://www.federalreserve.gov/econres/feds/zeroing-in-on-the-expected-returns-of-anomalies.htm (FETCHED, high) and JFQA abstract via search (SEARCH, high).
- **Turnover is the killer.** Novy-Marx & Velikov: anomalies with turnover below ~50%/month mostly retain significant net spreads when built with cost mitigation (buy/hold bands); few higher-turnover ones do. Source: https://www.nber.org/papers/w20721 (SEARCH, high).
- **Counterweight.** Jensen, Kelly & Pedersen argue most factors replicate (≈82% by their Bayesian measure) and hold in 93 countries. This is about *gross* existence of factor premia, not net retail profitability. Source: https://www.nber.org/papers/w28432 (SEARCH, high).
- **ML on equities.** Avramov, Cheng & Metzker: deep-learning signal profits come from hard-to-arbitrage stocks and states; excluding microcaps, distressed names or high-volatility episodes considerably attenuates them, and reasonable trading costs erode them further due to high turnover. Source: https://pubsonline.informs.org/doi/fpi/10.1287/mnsc.2022.4449 (SEARCH, high).

### 2.2 Equities — signal by signal

- **Cross-sectional momentum (months).** Best-documented equity anomaly historically; known crash risk in rebounds (Daniel-Moskowitz, RECALLED, not re-fetched — my fetch attempt hit the wrong NBER number). Moderate turnover puts it in the Novy-Marx-Velikov "survives costs if implemented carefully" bucket. Confidence medium. A long-only retail version is mostly a tilted-beta portfolio, not market-neutral alpha.
- **Time-series momentum / trend (months).** Moskowitz-Ooi-Pedersen documented it in 58 liquid futures (SEARCH: https://papers.ssrn.com/abstract=2089463). But Huang, Li, Wang & Zhou (JFE 2020) find asset-by-asset regressions show little evidence of predictability in or out of sample, and that the strategy's profit is virtually the same as one based on historical mean returns that needs no predictability (SEARCH: https://ideas.repec.org/a/eee/jfinec/v135y2020i3p774-794.html, high). Implication: trend following is defensible as a *risk-management/positioning rule* earning risk premia, weaker as proof of forecastable returns.
- **Short-term reversal (days–weeks).** Very high turnover; falls in the Novy-Marx-Velikov bucket that rarely survives costs. I did not fetch a dedicated reversal paper. Confidence medium on direction, unverified on magnitudes.
- **PEAD.** Martineau (Critical Finance Review 2022): prices now reflect earnings surprises on the announcement date; drift has been absent for large stocks since 2006 and disappeared more recently for microcaps. Source: https://ideas.repec.org/a/now/jnlcfr/104.00000122.html (FETCHED, high). A search result title suggests a later UCLA Anderson brief asks whether PEAD "is a thing again" — not opened, unverified. Net: PEAD is not a safe base for a new system.
- **News sentiment.** Ke, Kelly & Xiu (Dow Jones Newswires, supervised text model): news is absorbed with exploitable delay, claimed profitable at reasonable turnover net of costs (SEARCH: https://www.nber.org/papers/w26186, medium). Needs a real-time professional newswire and daily rebalancing of many small stocks — not what a retail system with free news APIs replicates. Magnitudes not verified this session.
- **LLM-read headlines.** Lopez-Lira & Tang: GPT-4 scores of headlines predict subsequent drift, strongest in small caps and negative news; ~90% hit rate applies to the *non-tradable* initial reaction; strategy returns have declined as LLM adoption rose. Source: https://arxiv.org/abs/2304.07619 (FETCHED, high for abstract-level claims). This is the most relevant paper for a Claude-based news agent, and its own authors report the edge is decaying and concentrated where shorting/trading is costly.
- **Social-media sentiment.** Cookson, Lu, Mullins & Niessner (JFE 2024; Twitter, StockTwits, Seeking Alpha): attention is correlated across platforms, sentiment is not; sentiment-driven retail imbalance predicts positive next-day returns while attention-driven imbalance predicts strongly *negative* next-day returns. (SEARCH: https://aeaweb.org/conference/2024/program/paper/EB9zskn5, high.) Bradley et al. (RFS 2024): WallStreetBets due-diligence posts predicted returns before GameStop; the predictive power vanished afterwards. (SEARCH, high.) Net: single-platform engagement-weighted sentiment (what JARVIS v1 does with Reddit/Electrek) is as likely to be a contrarian/attention signal as a directional one.
- **Insider Form 4.** Cohen, Malloy & Pomorski (data 1986–2007): "opportunistic" (non-routine) insider trades earn value-weighted abnormal returns of ~82 bps/month; routine trades ≈ 0. Source: https://www.nber.org/digest/apr11/decoding-inside-information (SEARCH, high for the historical number). Sample ends 2007 and predates publication; applying McLean-Pontiff decay, a prudent prior is well under half that today. Post-2012 performance: unverified. Still the equity signal in the docs with the cleanest economic rationale, lowest turnover and freely available data (EDGAR).

### 2.3 Crypto

- **Cross-sectional factors.** Liu, Tsyvinski & Wu (JF 2022): market, size and momentum factors span cross-sectional crypto returns; sample 2014–2018, coins above $1M cap (109 → 1,583 coins); weekly quintile sorts. Source: https://www.nber.org/papers/w25882 (FETCHED abstract; sample from search; high). Not net of costs as far as I could verify (PDF did not parse — magnitudes unverified). Contradicting evidence: Grobys & Sapkota (Econ Letters 2019), 143 coins 2014–2018, find no significant momentum payoffs (SEARCH: https://ideas.repec.org/a/eee/ecolet/v180y2019icp6-10.html, high). A working paper (AUT; 403 on fetch) reports time-series momentum is strong but cross-sectional is weak, and that with transaction costs and intra-period price swings many leveraged momentum portfolios get liquidated (SEARCH only, medium-low). Shorting small coins is impractical for retail, so the long-short factor is mostly untradable.
- **Trend / time-series momentum.** Zarattini, Pagani & Barbon ("Catching Crypto Trends", 2025, working paper, not peer reviewed): Donchian-ensemble trend on the top-20 liquid coins, survivorship-free since 2015, vol-scaled, reported net Sharpe >1.5 and 10.8% annual alpha vs BTC. Source: https://concretumgroup.com/catching-crypto-trends-a-tactical-approach-for-bitcoin-and-altcoins/ (FETCHED, medium — authors' own summary; cost assumptions not visible). A 2026 arXiv paper (2602.11708) claims Sharpe 2.41 on 2022–2024 with 4 bps taker fees — a fee level a small retail account does not get (see 2.5); SEARCH only, low. Crypto trend is the best-supported crypto directional edge, but the whole sample is one asset class's 10-year bull history with a handful of independent cycles; treat Sharpe >1 claims as upper bounds.
- **Carry / funding / basis.** BIS WP 1087 (Schmeling, Schrimpf, Todorov; revised Oct 2025): BTC/ETH futures carry averages >10% p.a. and has reached up to ~60% p.a.; driven by leveraged trend-chasing demand from small investors and scarce arbitrage capital; the cash-and-carry is risky because of margin spikes and liquidations in drawdowns; high carry predicts future price declines and rising crash-insurance prices. Source: https://bis.org/publ/work1087.htm (FETCHED, high). He, Manela, Ross & von Wachter: perp-spot deviations are larger than in FX, comove across coins and *diminish over time*; an implied arbitrage yields high Sharpe ratios. Source: https://arxiv.org/abs/2212.06888 (FETCHED abstract, high; Sharpe-by-fee-tier numbers not retrieved — PDF unparseable). Two uses for JARVIS: (a) delta-neutral carry is a real, declining premium that requires perpetual/futures access (jurisdiction-dependent — unknown for this owner) and survives only with careful margin management; (b) funding/carry level is an evidence-backed *risk-state input* (high carry → elevated crash risk).
- **Crypto sentiment.** I did not open a qualifying primary source this session. Unverified; by analogy with the equity social-signal results, expect attention ≠ direction.

### 2.4 Intraday prediction for retail

- **Deep LOB models.** Briola, Bartolucci & Aste (LOBFrame, NASDAQ stocks): high forecasting scores do not necessarily correspond to actionable trading signals; efficacy depends on each stock's microstructure. Source: https://arxiv.org/abs/2403.09267 (FETCHED, high). This directly undercuts "order-book imbalance → continuation → profit" for a taker with retail latency.
- **Intraday momentum on index ETFs.** Gao, Han, Li & Zhou (JFE 2018; SPY 1993–2013): first half-hour return predicts last half-hour return (SEARCH, high for existence; effect size not retrieved). Zarattini, Aziz & Barbon (SFI WP 24-97, not peer reviewed): SPY intraday momentum with trailing stops, 2007–early 2024, reported 19.6% annualised, Sharpe 1.33 net of their assumed costs. Source: https://ideas.repec.org/p/chf/rpseri/rp2497.html (FETCHED, medium; cost/leverage assumptions not in abstract; single-instrument, researcher-chosen parameters, authors are affiliated with a trading firm). The most credible *intraday* candidate for retail is this family — one ultra-liquid instrument, a few trades per day — not ML on ticks.
- **Realised outcomes of actual day traders.** Chague, De-Losso & Giovannetti (all Brazilian individuals who began day-trading equity index futures 2013–2015 and persisted 300+ days): 97% lost money; ~0.4–1.1% earned more than a bank-teller/minimum wage; no evidence of learning. Source: https://ideas.repec.org/p/fgv/eesptd/525.html (FETCHED, high). Barber, Lee, Liu & Odean (Taiwan 1992–2006): fewer than 1% of day traders predictably earn positive abnormal returns net of fees. (SEARCH, high.) These are discretionary humans, not algorithms, but they set the base rate for the venue JARVIS's worked examples sit in.

### 2.5 Backtests, LLM agents and costs

- **Backtest Sharpe barely predicts live Sharpe.** Wiecki et al. (Quantopian, 888 algorithms with ≥6 months out of sample): backtest Sharpe had R² < 0.025 for out-of-sample performance; more backtesting → larger backtest/live gap. (SEARCH of the paper's abstract, high.)
- **LLM trading agents.** FINSABER (Li, Kim, Cucuringu, Ma; arXiv 2505.07078): LLM strategies' reported advantages deteriorate significantly over two decades and 100+ symbols; too conservative in bull markets, too aggressive in bear markets. Source FETCHED, high. Weakens the premise that the TradingAgents/LangAlpha-style agent debate adds return.
- **Costs for a tiny account.** Alpaca crypto tier 1 ($0–100k 30-day volume): 0.15% maker / 0.25% taker. Source: https://docs.alpaca.markets/docs/crypto-fees (FETCHED, high). Coinbase Advanced fee page returned 403 — unverified. Arithmetic on the Architecture doc's own example: $25 position, +1.1% = $0.275 gross. Two taker fills at 0.25% = $0.125, before spread. The doc's "+$0.27 after costs" is therefore effectively a zero-cost number; the honest figure is ≈ $0.15 minus spread. A 0.5% round-trip hurdle means any intraday crypto signal must predict moves several times larger than typical order-flow signals forecast.

## 3. What this means for the JARVIS documents

**Supported**
- "FLAT is a valid decision", "never chase a return target", paper → shadow → small live, deterministic risk gate, costs inside the decision rule: all consistent with the evidence that most candidate signals net to roughly zero.
- Strategy Lab (Architecture layer D): requiring walk-forward, costs and out-of-sample proof is right — but the Quantopian result says even that gate is weak; add trial counting and deflation.
- "Small capital can be dominated by fees/spreads" (v2 constraints) — strongly supported; the worked examples then ignore it.
- Form 4 as an added signal (Architecture p.2) — supported historically, if restricted to opportunistic/non-routine buys and treated as a slow, low-turnover tilt.
- 13F as "slower positioning signal" — sensible framing; no evidence gathered here for edge.

**Weakened**
- Opportunity Scanner list "momentum, breakouts, mean reversion, event shocks, anomalies": as generic published patterns in liquid names these have ~4–20 bps/month net expected return before price impact. Scanning more of them continuously raises the multiple-testing burden rather than the edge.
- News & Event Agent / FinBERT sentiment as a *return predictor*: real effect exists in the literature but lives in small caps, at newswire speed, and is decaying as LLM use spreads. As a risk/context input it is fine.
- Social sentiment (JARVIS v1's 1,324 Reddit/Electrek posts): single-platform sentiment is not robust across platforms, attention predicts negative returns, and WSB informativeness disappeared post-2021.
- PEAD-style "event shock" drift: largely gone in large caps since 2006.
- Bull/Bear LLM agents and the TradingAgents pattern as a source of alpha: FINSABER finds no durable outperformance. Keep them for explanation and red-teaming, not for signal.
- Model Ensemble (HMM regime, GARCH, jump, return distribution): volatility is forecastable (useful for sizing); nothing gathered here supports regime/jump models producing tradable directional edge. Unverified rather than refuted.

**Contradicted**
- The worked examples (BTC, ETH, v3 crypto breakout): intraday taker trades on order-flow/breakout signals at $20–25 size. Deep-LOB evidence says prediction ≠ profit; retail fees of ~0.5% round trip exceed the typical signal; day-trader base rates are ~97% losing. This is the single weakest-supported idea in the documents, and it is the one the documents illustrate.
- Confidence figures of 72–82% for a directional intraday call: no source I found supports calibrated directional accuracy anywhere near this at tradable (post-reaction) horizons. Realistic calibrated edges are a few points above 50%. The only ~90% figure in the literature (Lopez-Lira-Tang) is explicitly for the non-tradable initial reaction.
- "Multi-horizon, intraday to long-term, equities + crypto, long/short" as a starting scope: evidence favours the slow end only.

## 4. Recommended changes

1. **Invert the horizon priority.** Start with daily-to-monthly, low-turnover strategies; make intraday a later research track that must clear an explicit cost hurdle. Enforce a turnover budget (Novy-Marx-Velikov: <50%/month).
2. **First strategies, in order of defensibility:** (a) volatility-targeted trend following on a small set of liquid instruments — broad equity ETFs and BTC/ETH — daily bars, positioned as risk-managed beta rather than alpha; (b) cross-sectional equity momentum among liquid large/mid caps, monthly rebalance with hold bands, long-only tilt; (c) opportunistic-insider-buy tilt from Form 4 as an overlay; (d) crypto funding/basis used first as a crash-risk state variable, and as a delta-neutral carry strategy only if the owner's jurisdiction permits perps/futures and margin logic is proven on paper; (e) optionally, one intraday-momentum rule on SPY/QQQ as a strictly paper-traded experiment.
3. **Set the benchmark honestly.** Every strategy is judged against buy-and-hold of the same assets after costs and tax. A system that cannot beat a two-ETF-plus-BTC static allocation net should hold that allocation.
4. **Reposition the LLM agents** from "forecasters" to: data extraction/classification (event type, novelty, insider routine vs opportunistic), hypothesis generation for the Strategy Lab, red-team review, and explanation. Do not let narrative confidence enter sizing.
5. **Replace the confidence numbers** in the docs with calibrated base rates and add a "minimum edge after costs" gate: expected move must exceed k × round-trip cost (fee + spread + slippage), computed from the actual broker fee tier.
6. **Add overfitting accounting** to the Strategy Lab: log every variant tested, deflate Sharpe for the number of trials, require a pre-registered hypothesis before backtesting, and assume a 50%+ haircut on any backtested Sharpe.
7. **Rewrite the worked example** as a slow, boring trade (e.g. a vol-targeted trend position held for weeks) with real fees, and state a minimum practical account size; $100 intraday is uneconomic.

**Honest expectation (my synthesis, not a sourced statistic).** Published net anomaly returns of 4–20 bps/month, a >50% publication haircut, and near-zero predictive power of backtest Sharpe imply: a careful solo system running diversified low-turnover trend/momentum should plan for a net Sharpe of roughly 0.3–0.7 over a full cycle, with multi-year stretches below zero, and a large share of return being beta. Sustained net Sharpe above 1 at retail scale would be exceptional and should be treated as suspected error until it survives a year or more live. Reported Sharpes of 1.3–2.4 in single-author working papers are upper bounds, not planning numbers.

## 5. Open uncertainties

- Jurisdiction, capital and data budget are unknown; they decide whether perps/carry, shorting and newswire-speed news are even available.
- Full-text magnitudes not retrieved (PDFs unparseable or 403): Liu-Tsyvinski-Wu weekly returns and cost treatment; He et al. Sharpe by fee tier; Zarattini cost/leverage assumptions; Ke-Kelly-Xiu net Sharpe; AUT crypto-momentum paper.
- Post-2012 performance of opportunistic-insider signals; post-2022 performance of crypto trend and carry (He et al. say deviations are shrinking).
- Whether PEAD has partly returned (an unopened UCLA Anderson brief raises this).
- Short-term reversal and crypto sentiment: no qualifying primary source opened.
- Daniel-Moskowitz momentum-crash figures were recalled, not fetched.
- Coinbase Advanced current fee tiers (403).
- The 0.3–0.7 Sharpe range is a judgment; no study measures "careful solo algorithmic retail systems" directly.

## 6. Source list

Fetched this session
- Chen & Velikov, Fed FEDS page: https://www.federalreserve.gov/econres/feds/zeroing-in-on-the-expected-returns-of-anomalies.htm
- Martineau, CFR 2022 (RePEc abstract): https://ideas.repec.org/a/now/jnlcfr/104.00000122.html
- BIS WP 1087 Crypto carry: https://bis.org/publ/work1087.htm
- Chague, De-Losso, Giovannetti (RePEc abstract): https://ideas.repec.org/p/fgv/eesptd/525.html
- Liu, Tsyvinski, Wu NBER w25882 (abstract page): https://www.nber.org/papers/w25882
- Lopez-Lira & Tang: https://arxiv.org/abs/2304.07619
- FINSABER: https://arxiv.org/abs/2505.07078
- Briola et al. Deep LOB forecasting: https://arxiv.org/abs/2403.09267
- He, Manela, Ross, von Wachter: https://arxiv.org/abs/2212.06888
- Zarattini, Aziz, Barbon SFI 24-97 (RePEc abstract): https://ideas.repec.org/p/chf/rpseri/rp2497.html
- Zarattini, Pagani, Barbon, Catching Crypto Trends (authors' page): https://concretumgroup.com/catching-crypto-trends-a-tactical-approach-for-bitcoin-and-altcoins/
- Alpaca crypto fees: https://docs.alpaca.markets/docs/crypto-fees

Seen via search summary only (paper not opened)
- McLean & Pontiff JF 2016: https://ivey.uwo.ca/media/3775549/pontiff.pdf
- Novy-Marx & Velikov RFS 2016: https://www.nber.org/papers/w20721
- Jensen, Kelly, Pedersen JF 2023: https://www.nber.org/papers/w28432
- Avramov, Cheng, Metzker Mgmt Sci 2023: https://pubsonline.informs.org/doi/fpi/10.1287/mnsc.2022.4449
- Huang, Li, Wang, Zhou JFE 2020: https://ideas.repec.org/a/eee/jfinec/v135y2020i3p774-794.html
- Moskowitz, Ooi, Pedersen JFE 2012: https://papers.ssrn.com/abstract=2089463
- Cohen, Malloy, Pomorski: https://www.nber.org/digest/apr11/decoding-inside-information
- Cookson, Lu, Mullins, Niessner JFE 2024: https://aeaweb.org/conference/2024/program/paper/EB9zskn5
- Bradley, Hanousek, Jame, Xiao RFS 2024 (bibliographic record): https://academicnewsletter.sufe.edu.cn/info/351572
- Ke, Kelly, Xiu: https://www.nber.org/papers/w26186
- Gao, Han, Li, Zhou JFE 2018: https://profiles.wustl.edu/en/publications/market-intraday-momentum/
- Barber, Lee, Liu, Odean JFM 2014: https://ideas.repec.org/a/eee/finmar/v18y2014icp1-24.html
- Grobys & Sapkota 2019: https://ideas.repec.org/a/eee/ecolet/v180y2019icp6-10.html
- Wiecki, Campbell, Lent, Stauth (Quantopian): SSRN paper, title "All that Glitters Is Not Gold" (canonical URL not opened)
- arXiv 2602.11708 AdaptiveTrend: https://arxiv.org/abs/2602.11708

Failed to open: Coinbase Advanced fees (403); AUT crypto momentum PDF (403); Cowles and arXiv PDFs (unparseable).


## Independent verification (2026-10-01)

Confirmed (opened or searched independently):
- Alpaca crypto tier 1 fees 0.15% maker / 0.25% taker (page last updated 2025-09-24): https://docs.alpaca.markets/docs/crypto-fees
- Chen-Velikov Fed paper: 120 anomalies, ~8 bps/month net, price impact excluded: https://www.federalreserve.gov/econres/feds/zeroing-in-on-the-expected-returns-of-anomalies.htm
- Lopez-Lira & Tang: ~90% hit rate is for the non-tradable initial reaction; returns decline as LLM adoption rises; drift strongest in small caps/negative news: https://arxiv.org/abs/2304.07619
- Cohen-Malloy-Pomorski: opportunistic trades 82 bps/month value-weighted (180 bps equal-weighted), routine ~0: https://www.nber.org/papers/w16454.pdf
- Zarattini-Aziz-Barbon SPY: 19.6% annualised, Sharpe 1.33, 2007-early 2024, net of their cost assumptions: https://ideas.repec.org/p/chf/rpseri/rp2497.html

Corrected / missed:
- The 82 bps figure is value-weighted; the equal-weighted figure is 180 bps. Equal-weighted figures are even less retail-relevant (small/illiquid names). Keep the "well under half today" prior.
- Chen-Velikov "~4 bps/month" for the JFQA version was not independently confirmed; rely on the 8 bps (120 anomalies) number, and note price impact is excluded.
- Owner-constraint omission: the FINRA pattern-day-trader rule ($25k minimum) was replaced; SEC approved it 2026-04-14 (FINRA Reg Notice 26-10), effective 2026-06-04, brokers have until 2027-10-20 to implement. Margin accounts above $2,000 get broker-set intraday buying power. So the PDT barrier is not a fixed blocker for a $1k-$10k US account, but broker implementation varies; check the specific broker. Sources: https://www.kslaw.com/insights/articles/finra-adopts-sweeping-changes-to-margin-requirements-for-day-trading , https://international.schwab.com/story/sec-approves-scrapping-25000-day-trader-minimum
- Also missing: US tax treatment (short-term gains at ordinary rates, crypto taxed as property, per-trade lot tracking) and zero-cost data limits, which favour slow strategies; US-resident access to perps/futures carry is limited, so carry should be a risk-state input only at this capital.

Unverified: McLean-Pontiff 26%/58%, Novy-Marx-Velikov turnover threshold, Martineau PEAD, BIS 1087 carry figures, Grobys-Sapkota, Wiecki R^2<0.025 (not re-opened here).

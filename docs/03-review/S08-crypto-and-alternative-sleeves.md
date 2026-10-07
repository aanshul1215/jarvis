# S08 Review: crypto exposure and other diversifiers

Reviewer: S08-crypto-and-alternative-sleeves. Date: 2026-10-02. Scope: FINAL-design.md sections 4, 5, 6, 7, 9, 10 (rows 5, 30, 37, 45), 12, 14 (D9) and 15 (O6). Tags: FETCHED means I opened it this session; RECALLED means memory only; UNVERIFIED means a search snippet or an unopened page. All dollar figures are ESTIMATE.

## Verdict in one paragraph

Keep crypto out of the **live launch book**. That is what the design already does, and the evidence supports it. But the design's "deferred" row is too vague to be useful and slightly too risky when it unlocks. Three changes: (1) close the Alpaca-direct crypto branch for a Texas owner; (2) run crypto as a **zero-capital shadow sleeve from P1b**, so the owner's "equities + crypto" vision shows up in the memo without risking money or adding agents or LLM spend; (3) when it unlocks, make it a **static, BTC-only, 5% hard-capped ETF holding with no trend overlay**, not a 10% Donchian ensemble. The dollars at stake are small either way, so the dominant cost of any crypto trend overlay is build and validation effort, not trading cost.

## What the design gets right (with evidence)

1. **Not using Alpaca spot crypto.** Alpaca's own docs list crypto fees at 15 bps maker / 25 bps taker at the lowest tier, so a taker round trip is 2 x 0.25% = 0.50% (FETCHED, docs.alpaca.markets/docs/crypto-trading). Alpaca's support page says IRAs cannot trade crypto as of September 2024 (FETCHED), and its IRA docs say crypto is not supported (FETCHED). Texas was absent from the 28-jurisdiction list dated 9 October 2025 (search snippet only; the official page returned 404 for me, so UNVERIFIED). An Alpaca forum thread has Texans asking for crypto in March and June 2026 with no staff reply (FETCHED). The design's "doubtful" label is fair, and it is stronger than the design knew.
2. **Routing crypto through spot ETFs if at all.** IBIT shows a 0.25% sponsor fee and a 0.02% median bid-ask spread on 30 September 2026 (FETCHED, ishares.com). ETHA is 0.25% with no staking (FETCHED). BITB is 0.20% (FETCHED). Spot ETFs are grantor-style trusts, not registered funds (FETCHED, issuer pages). They are ordinary exchange-listed securities, so a 1099-B, the existing ETF machinery, and wash-sale rules all apply. The SEC's 17 September 2025 generic listing standards removed the main approval barrier (FETCHED, Goodwin summary of the SEC order), so the product set is stable and fee competition is real.
3. **Labelling the Donchian evidence honestly.** Zarattini, Pagani and Barbon (SFI Research Paper 25-80, 2025) is a working paper by a research vendor and two academics. It reports a Sharpe above 1.5 and 10.8% alpha versus BTC for a top-20 rotation (FETCHED, RePEc abstract). Brief 18 read the full text and found that "net" results use only 10 bps costs. The design's "one non-peer-reviewed working paper" wording is accurate.
4. **A cap, a with/without test, and "unvalidated, loss-capped".** The peer-reviewed support is thin and sample-bound (see Evidence below), so a cap and a label are the right posture.
5. **Not adding Coinbase as a second broker, and keeping every crypto decision deterministic.** Nothing in the evidence base supports LLM selection or sizing (brief 01, as cited in the design).
6. **Five asset classes including gold/commodities.** Hurst, Ooi and Pedersen (JPM 2017) show time-series momentum profitable across 67 markets and four asset classes from 1880 to 2016 (FETCHED, AQR page). That supports diversified trend, not any single asset. The design's S-A already uses this logic.

## Evidence summary: what crypto papers actually support

- **Liu and Tsyvinski, "Risks and Returns of Cryptocurrency," RFS 34(6), 2021 (NBER w24877).** Bitcoin, Ripple and Ether have little exposure to stock, macro, currency or commodity factors; time-series momentum and investor attention predict returns (FETCHED, NBER abstract). A summary of the sample I did not open fully says daily data to May 2018 and weekly Sharpe ratios about 75% above stocks (UNVERIFIED snippet). Sample is one bull-heavy cycle; no costs or taxes in the abstract.
- **Liu, Tsyvinski and Wu, "Common Risk Factors in Cryptocurrency," JF 77(2), 2022 (NBER w25882).** A three-factor model (market, size, momentum) explains nine long-short strategies (FETCHED, NBER abstract). Cross-sectional, mostly small coins. It does not tell a $5,000 owner what to hold in a large-cap ETF.
- **Gerritsen, Bouri, Ramezanifar and Roubaud, Finance Research Letters 34, 2020.** Range-breakout rules beat buy-and-hold on bootstrapped Sharpe in BTC, July 2010 to January 2019; most other rules did not (FETCHED, RePEc). The sample ends before the 2021-22 and 2025-26 drawdowns.
- **Fieberg et al., JFQA 60(7), 2025.** A machine-learning trend factor over 3,000+ coins survives transaction costs and works in liquid coins (FETCHED, Cambridge abstract). Cross-sectional long-short, which a long-only ETF holder cannot replicate.
- **Diversification.** Brière, Oosterlinck and Szafarz (J. Asset Management 16(6), 2015) used weekly data 2010-2013 and found a small BTC share improves risk-return, while warning the result may be early-stage behaviour (FETCHED, RePEc). Petukhina et al. (Quantitative Finance 21(11), 2021) find crypto can improve portfolios but that "illiquidity potentially reverses the results" (FETCHED, arXiv abstract). The IMF's January 2022 blog reported BTC-S&P 500 correlation of 0.01 in 2017-19 rising to 0.36 in 2020-21 (search snippet, page returned 403, UNVERIFIED). The 1-5% allocation range in institutional notes is mostly sponsor-authored marketing; the one summary I opened cites no academic papers (FETCHED, but weak).
- **Reading.** The in-sample case for a small BTC weight is real. The out-of-sample, ETF-era, post-correlation-rise case has about 2.7 years of IBIT history (inception 5 January 2024, FETCHED). Bitcoin's own drawdowns are large: an October 2025 high near $126k and a fall of about 47% by late 2025 (FETCHED, Cointelegraph); a roughly 50% peak-to-trough in 2026 appears only in search snippets (UNVERIFIED).

## What should improve

### S08-P1: Close the Alpaca-direct crypto branch for this owner (section 12, row "Alpaca spot crypto"; D9; O6)
**Change.** Replace "Doubtful" with "Closed for Texas unless Alpaca adds the state; recheck only at G4". Add the Alpaca crypto-regions page and the docs crypto page to Change-Watch's weekly page-hash list (existing role, no new spend). Delete the "stop lifecycle ... for crypto" paragraph in section 6 as a P3 requirement, because the ETF route has no 24/7 stops.
**Evidence.** Alpaca docs, IRA doc and forum thread (all FETCHED, above). Cost $0. Effort: saves about 1 dev-day of P3 scoping and removes one open item. Respects all binding constraints. **Risk:** the Oct 2025 list may be stale; the P0 signup check and Change-Watch cover it.
Priority: should.

### S08-P2: Add a zero-capital crypto shadow sleeve from P1b (sections 4, 5, 9)
**Change.** Shadow NAV adds S0+BTC variants at 0%, 2.5% and 5%, and one registered one-cell family `crypto-trend-zpb` (the published nine-lookback Donchian ensemble, as published, no tuning). Data: Coinbase Exchange public daily candles, which need no authentication and return up to 300 candles per call (FETCHED, Coinbase docs), so about 15 calls for 2015-2026 (ESTIMATE: 11.8 years x 365 / 300 = 14.4). Cross-check against IBIT's close from January 2024 as a second vendor (the existing trust-gate pattern). The weekly memo gets one code-computed line: "a 5% BTC sleeve would have changed your NAV by $X and your worst drawdown by $Y". This is the first place the owner's "equities + crypto" idea becomes visible.
**Evidence.** Zarattini et al. (FETCHED abstract); Gerritsen et al. (FETCHED); the Brière and Petukhina caveats on sample dependence. Forward-only scoring is the right test because the in-sample cycles are used up.
**Cost.** $0 data, no LLM calls (the Narrator reads typed fields only). Effort +2 dev-days in P1b (ingest, one ticker, two report columns), against 130-180 total. **Risk:** the registry's cumulative N_eff could inflate S-A's DSR penalty; register this as a separate family and report per-family N_eff (the validation reviewer should confirm). Also scope creep: cap at those two features.
Priority: should.

### S08-P3: When crypto unlocks, make it static, BTC-only, 5% hard cap, no trend overlay (section 12 row "Crypto via spot BTC/ETH ETFs"; section 6 per-symbol cap; section 9 Mission Plan permissions)
**Change.**
- Cap: 5% of marked equity (not 10%), one ticker, BTC only. ETH adds little beyond BTC and doubles the ticker and trial count (the ETH-BTC correlation is RECALLED as high, UNVERIFIED).
- Rule: buy to target only at a decision window; no signal-driven exit; trim only lots already held over one year (extends the existing tax-lot check); alert and trim above 8% of equity.
- Gate: owner opt-in via a new Mission Plan permission {none (default), shadow, capped-ETF}; at least 6 clean live monthly rebalances of S0; the owner sees a stress loss in dollars before signing.
- The Donchian trend variant stays shadow-only until forward evidence exists; promotion would go through G0-G1.

**Arithmetic (ESTIMATE).** Sleeve = 5% x capital: $50 / $250 / $500 at $1,000 / $5,000 / $10,000. Fee at 0.25%: $0.13 / $0.63 / $1.25 a year. Stress loss at -50% (2025-26 scale): $25 / $125 / $250; at -75% (2022-like, RECALLED): $37 / $187 / $375. The current 10% cap doubles those ($75 / $375 / $750 at -75%). Trend overlay in a taxable account: tax hurdle 2.5-2.9 points (brief 19) x $250 = $6-7 a year at $5,000, plus about 0.4% a year in ETF cost for 8 NAV of turnover (8 x 0.02% spread + 0.25% fee = 0.41%, versus 8 x 0.25% = 2.0% at Alpaca spot). The overlay might avoid roughly $125-190 in a bear market at $5,000, but the effect is within noise of the satellite's -$14 to -$18 expected cost, so the build and validation effort (about 5-8 dev-days, my judgment) is the real price, and it cannot be validated: the BTC series has about 12 years and 3-4 cycles, and the ETF has 2.7 years.
**Cost.** Monthly cost impact is under $0.10 at $5,000 (fee). Effort: about +1 dev-day at P5 (universe row, cap rule, wash-sale mapping) versus about 5-8 for a validated overlay. **Risk:** a static holding can lose most of its value in a bear market; the cap limits that to about 3.75% of the account at 75% loss. Also, a taxable owner who sells within a year pays ordinary rates; the trim rule avoids that.
Priority: must (it replaces the riskier 10% default in section 12 before anyone relies on it).

### S08-P4: Universe and account rules for the ETF route (sections 4, 6, 15 O3/O4/O6)
**Change.**
1. P0 probe `GET /v2/assets/IBIT` (tradable, fractionable) and ask Alpaca in the O3 email whether IBIT-type ETFs are permitted in the Trading API IRA. Alpaca's IRA docs say `us_equity` only and crypto unsupported; they do not mention these ETFs either way (FETCHED).
2. Add a universe rule "1099-only: no K-1 commodity pools" for every sleeve. Gold trusts (GLDM 0.10%, FETCHED) are 1099 but taxed as collectibles at up to 28% long-term (search summary; CNBC returned 403; RECALLED rule, UNVERIFIED); that only matters above the 24% bracket. Put the K-1 and collectibles question in the O4 tax consult.
3. Map BTC ETF tickers as a mapped-equivalent set in the wash-sale guard (conservative). Whether different-issuer BTC ETFs are "substantially identical" belongs with O4. The IRS FAQ I opened is silent on wash sales for virtual currency itself (FETCHED); brief 19 notes H.R. 9172 is pending, but ETF shares are securities, so the guard applies today.
4. Choose the issuer by liquidity and spread (IBIT 0.02% median), not fee: the 0.14-0.25% range on a $250 sleeve is under $0.30 a year (0.11% x $250 = $0.28).

**Cost.** $0. Effort: +0.5 dev-day in P0, within the probe list. **Risk:** low; items are cheap probes.
Priority: should.

### S08-P5: Fix the gold slot and do not add a managed-futures ETF (section 4 universe; section 12)
**Change.** Pre-commit one gold ticker or one broad-commodity ticker at G0 (already a registered trial) and do not ablate slot choices. Reject DBMF (0.85%) and KMLM (0.90%) (search snippets, UNVERIFIED) as a sleeve: they duplicate S-A's trend bet, charge 8-9x a gold trust's fee, and Hurst et al.'s result is for a long-short futures book, not for those funds.
**Evidence.** Erb and Harvey, "The Golden Dilemma," FAJ 2013 (NBER w18706): gold is an unreliable inflation hedge over practical horizons and mean-reverts from high real prices (FETCHED). Hurst, Ooi and Pedersen (FETCHED). Honest consequence: the gold slot is a diversification prior, not an evidenced return source, and the design should say so.
**Cost.** $0; saves the effort of any alternative-sleeve work. **Risk:** gold could lag for years; S0's equal weight limits that to 20% of the core.
Priority: could.

## What I could not verify
- Whether IBIT or any spot BTC ETF is tradable, fractionable or IRA-eligible at Alpaca. The one Alpaca-powered broker I checked (Moola, August 2025) said it did **not** offer IBIT (FETCHED), so the question is open.
- Alpaca's current state list. The official regions page returned 404; the October 2025 list and the Texas absence rest on a search snippet and forum posts.
- Full text of Liu-Tsyvinski, Liu-Tsyvinski-Wu and Zarattini et al.: the PDFs came back as binary and the JF page returned 403; I used abstracts and brief 18's notes. Sample sizes, volatility figures and 2022 drawdown size are RECALLED.
- The IMF correlation numbers, Grayscale Mini's 0.15% fee, Morgan Stanley's 0.14%, and DBMF/KMLM fees are search snippets.
- IBIT's "1-year -45.62%" in the page summary conflicts with other price evidence; I did not rely on it.
- The grantor-trust tax characterization and the 28% collectibles treatment of gold trusts are RECALLED or from search summaries.
- I did not examine Public.com's crypto-IRA API route (brief 19 says unverified), and no managed-futures or gold peer-reviewed post-2017 update was opened.

## References
1. Liu, Y., Tsyvinski, A. "Risks and Returns of Cryptocurrency." RFS 34(6), 2021; NBER w24877. https://www.nber.org/papers/w24877 (FETCHED abstract; details RECALLED)
2. Liu, Y., Tsyvinski, A., Wu, X. "Common Risk Factors in Cryptocurrency." JF 77(2), 2022; NBER w25882. https://www.nber.org/papers/w25882 (FETCHED abstract)
3. Zarattini, C., Pagani, A., Barbon, A. "Catching Crypto Trends." SFI Research Paper 25-80, 2025. https://ideas.repec.org/p/chf/rpseri/rp2580.html (FETCHED abstract; full text via brief 18)
4. Gerritsen, D., Bouri, E., Ramezanifar, E., Roubaud, D. FRL 34, 2020. https://ideas.repec.org/a/eee/finlet/v34y2020ics1544612319303770.html (FETCHED)
5. Fieberg, C., Liedtke, G., Poddig, T., Walker, T., Zaremba, A. JFQA 60(7), 2025. https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/trend-factor-for-the-cross-section-of-cryptocurrency-returns/4C1509ACBA33D5DCAF0AC24379148178 (FETCHED)
6. Brière, M., Oosterlinck, K., Szafarz, A. J. Asset Management 16(6), 2015. https://ideas.repec.org/a/sol/spaper/2013-226296.html (FETCHED)
7. Petukhina, A., Trimborn, S., Härdle, W., Elendner, H. Quantitative Finance 21(11), 2021. https://arxiv.org/abs/2009.04461 (FETCHED)
8. IMF blog, "Crypto Prices Move More in Sync With Stocks," Jan 2022. https://www.imf.org/en/blogs/articles/2022/01/11/crypto-prices-move-more-in-sync-with-stocks-posing-new-risks (page 403; snippet only, UNVERIFIED)
9. Hurst, B., Ooi, Y.H., Pedersen, L. "A Century of Evidence on Trend-Following Investing." JPM 2017. https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing (FETCHED)
10. Erb, C., Harvey, C. "The Golden Dilemma." FAJ 2013; NBER w18706. https://www.nber.org/papers/w18706 (FETCHED)
11. iShares Bitcoin Trust (IBIT) and Ethereum Trust (ETHA) pages. https://www.ishares.com/us/products/333011/ishares-bitcoin-trust-etf ; https://www.ishares.com/us/products/337614/ishares-ethereum-trust-etf (FETCHED)
12. Bitwise BITB. https://bitbetf.com/ (FETCHED). Grayscale Bitcoin Mini Trust 10-K FY2024, https://www.sec.gov/Archives/edgar/data/2015034/000095017025029405/btc-20241231.htm (FETCHED; fee not shown, 0.15% from snippet).
13. Goodwin, SEC generic listing standards, Oct 2025. https://www.goodwinlaw.com/en/insights/publications/2025/10/alerts-finance-dcb-crypto-and-commodity-based-etps-poised-to-boom (FETCHED)
14. Alpaca crypto docs https://docs.alpaca.markets/docs/crypto-trading ; IRA overview https://docs.alpaca.markets/us/docs/ira-accounts-overview ; IRA crypto support page https://alpaca.markets/support/can-ira-trade-crypto ; IRA blog https://alpaca.markets/blog/alpaca-introduces-individual-retirement-accounts-for-trading-api-users/ ; forum thread https://forum.alpaca.markets/t/crypto-trading-in-texas/18562 ; Moola post https://alpaca.markets/blog/how-moola-aims-to-make-finance-more-accessible-for-everyday-americans-with-alpaca/ (all FETCHED). Regions page https://alpaca.markets/support/what-regions-support-cryptocurrency-trading (404; snippet only).
15. Coinbase Exchange candles API. https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getproductcandles (FETCHED)
16. IRS virtual currency FAQ https://www.irs.gov/individuals/international-taxpayers/frequently-asked-questions-on-virtual-currency-transactions ; Topic 409 https://www.irs.gov/taxtopics/tc409 (FETCHED; neither addresses wash sales or gold ETFs)
17. SPDR Gold MiniShares GLDM. https://www.spdrgoldshares.com/usa/gldm/ (FETCHED, 0.10% gross)
18. Cointelegraph, BTC price recap, 31 Dec 2025. https://cointelegraph.com/markets/bitcoin-price-in-2026-predictions-vs-charts-and-reality (FETCHED)
19. Gold ETF collectibles tax (CNBC 2022) and DBMF/KMLM fees: search snippets only (UNVERIFIED).

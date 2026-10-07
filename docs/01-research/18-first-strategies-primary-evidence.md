# 18 - First strategies: primary evidence (2026-10-01)

Constraints (binding): US resident, $1k-$10k own money, near-zero budget, solo developer. Tags: F = opened this session; R = recalled; U = unverified. Full text opened: MOP, Faber, Hurst-Ooi-Pedersen (HOP, working-paper version), Zarattini et al., Moreira-Muir, Cederburg et al., McLean-Pontiff, Novy-Marx-Velikov, Wiecki et al. Harvey et al. and dual momentum: abstract or secondary only.

## Questions
1. ETF/futures trend (MOP, Faber, dual momentum): what was measured, costs, post-publication result, trades a year?
2. BTC/ETH trend: rules, costs, turnover, post-2022 behaviour.
3. Volatility targeting: return or risk benefit?
4. McLean-Pontiff, Novy-Marx-Velikov, Wiecki: confirm the numbers.
5. Which 2-3 first strategies are defensible for a long/flat ETF + BTC/ETH book at Alpaca's costs, and what net result against buy-and-hold is honest?

## Findings

### 1. ETF and futures trend
| Source | Measured | Costs | After publication | Trades |
|---|---|---|---|---|
| MOP, JFE 2012 (F) | 58 liquid futures, Jan 1985-Dec 2009; sign of 12-month return, each position scaled to 40% ex ante vol; diversified portfolio Sharpe above 1 (about 2.5x equities); alpha 1.58%/month vs factors | None modelled. The text mentions costs only in citations; the data section says it targets "implementable" liquid contracts | Not tested in the paper | Monthly, long/short futures |
| HOP (AQR working paper, to 2013) (F) | 1880-2013, 29 commodities, 11 equity indices, 15 bonds, 12 currencies; 1/3/12-month signals, long/short | Simulated transaction costs plus 2%/20% fees. Net: 11.2%/yr, vol 9.7%, Sharpe 0.77 (gross 14.9%) | Net Sharpe by decade: 0.96 (1980s), 0.98 (1990s), 0.62 (2000-2013); net return 7.9% | Not stated |
| Faber 10-month SMA, SSRN/JWM, 2013 update (F) | S&P 500 from 1901; 5-asset allocation (US stocks, EAFE, bonds, REITs, commodities) from 1973; monthly, in the asset if price is above its 10-month SMA, else cash | Backtest excludes taxes, commissions and slippage | Author's own update: 2006-2012 beat buy-and-hold by over 2 points a year but won in only 3 of 7 years. The 2018 JPM reprint says "performed as expected out of sample" and gives no numbers I could read | 3-4 round trips a year for the 5-asset portfolio, under 1 per asset; turnover about 70%; about 70% of time invested (S&P) |
| Dual momentum (Antonacci) | Primary paper not opened (U) | n/a | A blog re-implementation (U, low confidence): 2014-2026 CAGR 8.4% vs SPY 13.6%, Sharpe 0.70 vs 0.94, max drawdown -20% vs -24% | about 30 switches in 18 years (blog, U) |

Independent challenge (F, abstract only): Huang-Li-Wang-Zhou, JFE 2020, find "little evidence" of TSM asset by asset, in-sample or out-of-sample. A pooled t-statistic that looks large fails bootstrap critical values, and the TSM strategy performs "virtually the same" as a strategy based on the historical sample mean. For a long/flat book this matters. Much of long-only trend profit is simply being long assets with a positive mean while avoiding some drawdowns.

Secondary (U): SG Trend Index 1.8%/yr over 2010-2019 vs 7.5% for 60/40 (search summary of a blog; not opened).

### 2. Crypto trend (Zarattini-Pagani-Barbon, SSRN 5209907, Swiss Finance Institute 25-80)
I read the author-hosted PDF (version dated 9 Apr 2025). The SSRN page revised 2 Oct 2025 was blocked, so later changes are unknown. It is a working paper by authors from Concretum Research (a research vendor). I found no peer-reviewed version.
- **Rules (F):** nine Donchian breakouts on closes (5, 10, 20, 30, 60, 90, 150, 250, 360 days). Exit on a close below a ratcheting stop at the channel midpoint. Each position is sized to 25% annualised vol using a 3-month vol estimate, **capped at 200% leverage**. The nine sub-portfolios are averaged ("Combo"). Long-only, daily data from CoinMarketCap, Jan 2015 to 19 Mar 2025.
- **Costs (F):** Tables 1-2 explicitly exclude costs. For BTC, Table 1 gives CAGR 30%, vol 17%, Sharpe 1.58, max drawdown 19% (passive BTC over 80%), alpha 14%, beta 0.17. Costs are tested at 10, 25 and 50 bps with a 20% no-trade band. All headline "net" results use only 10 bps. At 50 bps, the 5-day model's CAGR falls from 34% to 18%. The band recovers about 1 point a year. There is no 25 or 50 bps result for Combo in the text.
- **Top-20 rotation (F):** monthly rebalance, 10 bps, CAGR 18%, vol 9%, Sharpe 1.57, max drawdown 11%, alpha vs BTC 10.8%. ETH alone: CAGR 27%, Sharpe 1.51. The authors admit selection bias in the 40-coin list.
- **Turnover (F, Table 2):** trades per model over 10.2 years: 292, 156, 78, 49, 28, 20, 15, 9, 5. That is about 29 a year for the 5-day model and about 0.5 a year for the 360-day model.
- **Post-2022:** the paper gives no year-by-year table. It says only that results were strong in 2017, 2020-21 and late 2023. Nothing after March 2025 is available to me from a primary source.
- **Peer-reviewed (F, abstracts):** Gerritsen et al., Finance Research Letters 2020, BTC daily July 2010-Jan 2019: breakout rules beat buy-and-hold on bootstrapped Sharpe; most other rules did not; no cost treatment visible. Fieberg et al., JFQA 2025: a cross-sectional trend factor on 3,000+ coins that "survives" transaction costs.
- **Alpaca fees (F, docs page, "last updated 24 Sep 2025"):** tier 1 ($0-100k 30-day volume) is 0.15% maker and 0.25% taker, charged on the asset received.

### 3. Volatility targeting
- **Moreira-Muir (NBER 22208; JF 2017) (F):** the managed market factor (weight = constant / previous month's realised variance), 1926-2015, has annualised alpha 4.86%, beta 0.6 and appraisal ratio 0.34. It reports surviving 1-14 bps transaction costs and caps at leverage 1 (Sharpe unchanged, alpha lower).
- **Cederburg-O'Doherty-Wang-Yan (JFE 2020) (F):** on 103 strategies, 53 had a higher Sharpe and 50 lower (8 and 4 significant). For the market, Sharpe went 0.42 to 0.51, a difference with p = 0.30. Real-time versions earned a lower CER than the unmanaged portfolio in 72 of 103 cases. The market combo strategy had Sharpe 0.42 vs 0.46, because in-sample gains cluster around the 1930s.
- **Harvey et al. (JPM 2018) (F abstract via Man Group page):** 60+ assets, daily data from 1926. The Sharpe gain appears for equities and credit. It is negligible for bonds, currencies and commodities. Tail risk is reduced for all. The numbers 0.40 to 0.48-0.51 for US equities come from a search summary (U). Transaction costs are not addressed on the page.
- **Reading:** vol targeting is a risk tool. Its Sharpe benefit is real only for risk assets, is contested out of sample, and is sample-dependent.

### 4. The three decay and validity papers
- **McLean-Pontiff, JF 2016 (F):** 97 predictors from 79 studies, US stocks, long-short on extreme quintiles, gross of costs. Returns are 26% lower out of sample and 58% lower post-publication. The 26% is an upper bound on data-mining bias, leaving about 32% attributed to publication. 85 of 97 had in-sample t above 1.5.
- **Novy-Marx-Velikov, RFS 2016 (F, working-paper PDF):** 23 anomalies, 1963-2013, with Hasbrouck effective-spread costs. Round-trip costs for typical value-weighted strategies exceed 50 bps. Costs cut spreads by more than 1% of monthly one-sided turnover. Most anomalies with under 50% monthly turnover stay significant net, and few above do. Buy/hold spreads work best. This is a long-short single-stock study, so its cost levels do not carry over to liquid ETFs.
- **Wiecki et al., J. Investing 2016 (F):** 888 US-equity Quantopian algorithms, 2010-2015, backtested in Zipline with costs and slippage, and only 6-12 months of true out-of-sample data. In-sample Sharpe against out-of-sample Sharpe has R² = 0.02 (the abstract's "below 0.025"). The baseline for earlier in-sample Sharpe vs later in-sample Sharpe is 0.21. In-sample vol against out-of-sample vol has R² = 0.67 and max drawdown 0.34. An Extra Trees model reached R² 0.17 on a 20% hold-out.
- **Correction to the gap analysis (F):** the "8 bps a month" figure is the Chen-Velikov FEDS 2020 working paper (120 anomalies). A search summary says the published JFQA 2023 version (204 anomalies) gives 4 bps (U).

### 5. Cost arithmetic (ESTIMATE)
- **ETF trend:** 3.5 round trips a year at 1/5 of NAV each way is about 1.4 NAV of gross trades. At 2 bps a leg (spread assumed) that is about 0.03% a year, and 0.14% at 10 bps a leg. Alpaca charges no equity commission. Sell-side pass-through fees are SEC $0.0000206 of value plus FINRA TAF $0.000195 a share (F, Alpaca fee schedule), about 0.4 bps.
- **BTC Combo at Alpaca:** the average invested weight is about 0.43 (the portfolio-level to unit-level return ratio in Table 2). 652 trades over 10.2 years, at 2 x 0.43 / 9 NAV each, is about 6.1 NAV of gross traded notional a year. A 5-day-model check gives 12 points of cost at 50 bps against the paper's 16, so I scale by 1.3, giving about 8 NAV a year. At 25 bps a side that is about 2.0% a year, at 50 bps about 4%, and at 15 bps maker about 1.2%, all before spread.
- **Tax, taxable account:** if all gains were short-term at an assumed 22% bracket, an 8% pre-tax trend return nets 6.2%. A buy-and-hold with 15% tax deferred 10 years nets 7.1%. That is about 0.9 points a year (ESTIMATE; IRS Topic 409 rates are for 2025). Faber argues timing produces many short-term losses and long-term gains, so the true gap is somewhere between 0 and 0.9 points.

## What this decides for the JARVIS design
1. **Benchmark first.** The null is a static ETF + BTC/ETH buy-and-hold with periodic rebalancing. Every strategy is judged net of cost, and after tax, against it.
2. **First strategy (A): monthly 10-month-SMA (or 12-month return sign) long/flat on 4-6 liquid ETFs**, with cash or T-bill ETF when off. It is month-end only, about 3-4 round trips a year, and costs a few bps. Net expectation (ESTIMATE): roughly -1 to +1 point a year in CAGR vs the same assets held, with drawdowns about half. I extrapolate this from Faber's self-reported figures and one blog re-implementation (U). It sells risk reduction, not alpha. Run it in a tax-deferred account if one is available (open question).
3. **Second strategy (B): a small BTC/ETH trend sleeve** (ensemble of 20-90 day Donchian breakouts, long/flat, no leverage, daily signal at the close, 20% no-trade band, maker/limit orders). Skip the 5-10 day models. They give the best gross Sharpe but the highest cost and the least reliable evidence. Expected cost is about 1.2-2% a year before spread. Honest net expectation (ESTIMATE): haircut the 1.58 Sharpe by about half (my judgment, not a study value; Wiecki shows in-sample Sharpe barely predicts out-of-sample), giving about 0.8 gross, then subtract about 2 points of cost, so net Sharpe roughly 0.3-0.8. Against raw BTC it would likely lag in a bull run. BTC rose from about $314 to about $86k over the paper's sample (R, my recall; about 73% CAGR vs the strategy's 30%). The benefit is avoiding the 80% drawdown. Cap the sleeve at 20-25% of the book. It rests on one non-peer-reviewed paper from a research vendor.
4. **Third (C): volatility targeting as a sizing and risk governor on A and B, not a standalone alpha.** Cap leverage at 1.0 (Alpaca spot crypto cannot be levered anyway). Use monthly updates for ETFs and a 20% weight band for crypto. Justify it on drawdown and tail grounds. Expect no reliable Sharpe gain.
5. **Validation:** the 26%/58% decay and Wiecki's R² = 0.02 argue for a small registered trial count, long backtests including 2022 and 2025-26, and minimum-size live. The 50% haircut is a placeholder.
6. **Dual momentum:** not first. It is an optional variant of A with no primary evidence in hand.

## Open uncertainties
- I read the April 2025 version of Zarattini et al. I could not read the October 2025 revision, any year-by-year or post-2022 table, or Combo results at 25 and 50 bps. BTC trend after March 2025 is untested here.
- Alpaca's BTC/ETH spread and slippage are unmeasured; state availability of Alpaca crypto is unchecked.
- Faber's results tables are images, so I have no numeric CAGR or Sharpe for 1973-2012 or 2006-2012. Antonacci's paper, the SG Trend figure and Harvey et al.'s Sharpe numbers are unverified.
- Tax arithmetic uses assumed brackets; tax-advantaged automated trading is unchecked.
- McLean-Pontiff, Novy-Marx-Velikov and Wiecki cover stock anomalies and Quantopian algorithms, not ETF/BTC trend, so their haircuts are heuristics here.

## Source list
- MOP: https://w4.stern.nyu.edu/facdir/lpederse/papers/TimeSeriesMomentum.pdf (F)
- HOP: https://oxfordstrat.com/coasdfASD32/uploads/2016/03/A-Century-of-Evidence-on-Trend-Following-Investing.pdf (F)
- Faber 2013: https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf (F); JPM 2018 reprint: https://allocatortraining.com/wp-content/uploads/2023/06/A-Quantitative-Approach-to-Tactical-Asset-Allocation.pdf (F)
- Huang et al.: https://ideas.repec.org/a/eee/jfinec/v135y2020i3p774-794.html (F)
- Dual momentum blog: https://quant4free.com/analysis/dual-momentum/ (U)
- Zarattini et al.: https://concretumgroup.com/wp-content/uploads/2026/02/Catching-Crypto-Trends.pdf (F); https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5209907 (blocked)
- Gerritsen et al.: https://ideas.repec.org/a/eee/finlet/v34y2020ics1544612319303770.html (F); Fieberg et al.: https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/trend-factor-for-the-cross-section-of-cryptocurrency-returns/4C1509ACBA33D5DCAF0AC24379148178 (search abstract)
- Alpaca crypto fees: https://docs.alpaca.markets/docs/crypto-fees (F); fee schedule: https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf (F)
- Moreira-Muir: https://www.nber.org/papers/w22208.pdf (F); Cederburg et al.: https://www.lehigh.edu/~xuy219/research/COWY.pdf (F)
- Harvey et al.: https://www.man.com/insights/the-impact-of-volatility-targeting (F, abstract); https://people.duke.edu/~charvey/Research/Published_Papers/P135_The_impact_of.pdf (unreadable)
- McLean-Pontiff: https://Www.Gwern.net/doc/economics/2016-mclean.pdf (F)
- Novy-Marx-Velikov: https://mysimon.rochester.edu/novy-marx/research/ToAatTC.pdf (F)
- Wiecki et al.: https://community.portfolio123.com/uploads/short-url/3WHpAUOzhCG8QAUez71HpoWnA62.pdf (F)
- Chen-Velikov: https://www.federalreserve.gov/econres/feds/zeroing-in-on-the-expected-returns-of-anomalies.htm (F)
- IRS Topic 409: https://www.irs.gov/taxtopics/tc409 (F)


## Independent verification (2026-10-01)

Method: re-fetched or searched primary or abstract pages and re-did the arithmetic. Several PDFs (Zarattini full text, Cederburg full text) came back unreadable through the fetch tool, so table-level numbers there were not re-checked.

### Confirmed
- Alpaca crypto fees: tier 1 ($0-100k 30-day volume) is 0.15% maker, 0.25% taker, charged on the asset received, page "last updated September 24, 2025". https://docs.alpaca.markets/docs/crypto-fees
- SEC Section 31 rate is $20.60 per million (= $0.0000206 of value), effective 4 Apr 2026 (it was $0.00 before). https://www.sec.gov/rules-regulations/fee-rate-advisories/2026-2
- FINRA TAF for covered equities is $0.000195/share (cap $9.79) from 1 Jan 2026 (search summary of FINRA notice; FINRA rulebook https://www.finra.org/rules-guidance/rulebooks/corporate-organization/section-1-member-regulatory-fees).
- McLean-Pontiff (JF 2016): 97 predictors, 26% lower out of sample, 58% lower post-publication, about 32% attributed to publication. Confirmed from abstract-level sources.
- Chen-Velikov: FEDS 2020-039 gives 8 bps/month for 120 anomalies, and the JFQA 2023 version (204 anomalies, vol 58 no 3) gives 4 bps/month. The earlier (U) tag can be dropped. https://www.federalreserve.gov/econres/feds/zeroing-in-on-the-expected-returns-of-anomalies.htm
- Wiecki et al. (2016): 888 algorithms, Sharpe R^2 below 0.025, ML classifier R^2 0.17. Confirmed from abstract.
- Huang-Li-Wang-Zhou (JFE 135(3), 2020): abstract matches the brief's quotes. https://ideas.repec.org/a/eee/jfinec/v135y2020i3p774-794.html
- Moreira-Muir: JF 72(4) 2017, market alpha about 4.86%, beta 0.6. Appraisal ratio is reported as 0.33 by one summary and 0.34 in the brief; immaterial.
- Cederburg et al. (JFE 138(1), 2020, 103 strategies): out-of-sample vol-managed versions generally earn lower CER and Sharpe. The 72/103 figure appears in a secondary summary. The 53/50 split and the market 0.42 vs 0.51 were not re-verified.
- Zarattini-Pagani-Barbon: SFI Research Paper 25-80, April 2025, top-20 rotation Sharpe above 1.5 and alpha 10.8% vs BTC (abstract). It is still a working paper (SFI series), not peer reviewed. https://ideas.repec.org/p/chf/rpseri/rp2580.html
- Arithmetic re-done and correct: 292+156+78+49+28+20+15+9+5 = 652 trades; 1.4 NAV x 2 bps = 0.028%, x 10 bps = 0.14%; Combo cost 8 NAV/yr x 25/50/15 bps = 2.0/4.0/1.2%; tax 8% x 0.78 = 6.24%, and 1.08^10 taxed at 15% gives 7.1% CAGR, a gap of 0.86 points. BTC $314 to $86k over 10.2 years is about 73% CAGR (price levels are my recall, consistent).

### Corrected
- Regulatory fee cost "about 0.4 bps": it applies to sells only. SEC is 0.206 bps of sale value, and TAF is 0.0195 bps on a $100 share. That is about 0.23 bps per sale, or about 0.1-0.25 bps per round trip, not 0.4. Immaterial, and the brief's own TAF and SEC rates are right. Note that an automated fetch of Alpaca's fee-schedule PDF gave inconsistent numbers across two calls, so read the PDF yourself before hard-coding fees.
- Strategy B cost "1.2-2% a year": the 8 NAV/yr base is for the 9-model Combo. A 20/30/60/90-day ensemble has about 17 trades a year in total (7.6+4.8+2.7+2.0 per sub-model), so it trades roughly 3.7 NAV/yr unscaled, or about 4.8 with the brief's 1.3 factor. At 25 bps that is about 1.2%, at 15 bps maker about 0.7%. Use about 0.7-1.2% before spread, not 1.2-2%. This rests on the 0.43 average weight, which is itself an estimate.
- Zarattini data period: CXO's summary says Bitcoin from 2010 and 21,616 coins to Mar 2025, while the brief says daily data from Jan 2015. Treat the sample start as unconfirmed.
- "Net" Sharpe for B: the 50% haircut is a judgment and not a study value (the brief says so). Do not let it become a design parameter. Treat B's expected net Sharpe as unknown, with 0.3-0.8 as an illustrative range only.

### Could not verify
- Zarattini full-text tables: Table 1 BTC Combo (CAGR 30%, Sharpe 1.58), the trade counts, the 5-day cost sensitivity (34% to 18%), 200% leverage cap, 25% vol target. The PDF was unreadable via fetch, and the SSRN page returned 403.
- Cederburg 53/50 Sharpe split, market 0.42 to 0.51 with p = 0.30. Alpha Architect page returned 403.
- Faber figures, Antonacci dual momentum, the SG Trend Index figure and Harvey et al. Sharpe numbers: not re-checked, and still U.
- Wiecki R^2 = 0.21 baseline, 0.67 vol and 0.34 drawdown figures, and Novy-Marx-Velikov detail numbers (the 50 bps round trip, 1%/50% turnover statements): not re-checked beyond abstracts.
- MOP table values (Sharpe above 1, alpha 1.58%/month, 40% vol), HOP net 11.2%/0.77 and Sharpe by decade: not re-checked.

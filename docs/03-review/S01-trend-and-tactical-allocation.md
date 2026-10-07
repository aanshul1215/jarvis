# S01 Trend and tactical allocation: review of FINAL-design sections 1, 4, 7 and 11

Reviewer S01, 2026-10-02. FETCHED = opened this session; RECALLED = not opened. ESTIMATE = my arithmetic.

**Verdict.**
1. Plain Faber (10-month SMA, each asset long or in T-bills, five ETFs) is the right first rule. Every alternative I opened is the same signal in other clothes, or carries more data-mining risk.
2. The weak point is the **12.5% live satellite** and the gate machinery built to judge it. At that size it buys almost no protection, and no live record can show whether it works.
3. Change: run S-A in shadow from day 1, and make the L0 choice a whole-book choice. Cost $0. Saves roughly 25-50 dev-days across P1, P3 and P7.

## 1. What the design gets right (with evidence)

**R1. One published rule, no tuning, overlays off.** Zakamulin's 155-year study finds optimal lookbacks vary widely from window to window (CXO summary of SSRN 2677212; secondary). Wiecki et al. find backtest Sharpe barely predicts out-of-sample Sharpe (R² below 0.025), and more backtesting widens the gap (FETCHED). Counting the rule as about one trial is correct.

**R2. The effect is framed as risk reduction, not alpha.**
- Antonacci, 1974-2012, 12-month absolute momentum versus T-bills, 20 bps per switch (FETCHED). Median asset: return 9.90% to 10.25%, volatility 16.5% to 11.7%, Sharpe 0.38 to 0.53, max drawdown -53.5% to -21.4%. The return change is about +0.35 points, so the design's E of 0 (range -1 to +1) is sound.
- Huang, Li, Wang and Zhou (JFE 2020; abstract FETCHED) find little asset-by-asset evidence of time-series momentum, with results about equal to a historical-mean strategy.
- Moskowitz, Ooi and Pedersen (FETCHED): alpha over simply being long is positive in 90% of contracts, significant in only 26%.
- Wiecki et al.: backtest volatility and drawdown predict out-of-sample results far better than Sharpe. A drawdown claim is the better-supported claim.

**R3. Slow monthly signals.** Moskowitz et al. find robustness for lookbacks of 12 months or less; Georgopoulou and Wang (RoF 2017, FETCHED) find the effect fades past about a year. Lempérière et al. (arXiv 1404.3274, abstract FETCHED) and Kurth, Eisler, Rej and Bouchaud (arXiv 2607.01550, July 2026, abstract FETCHED) report short-lookback trend weakening since about 2009 and long-lookback trend intact. Those samples are futures, so transfer to ETFs is indirect.

**R4. Cost is small.** Faber reports 3-4 round trips a year for the book, about 70% turnover, and about 70% of time invested (FETCHED). ESTIMATE: 3.5 round trips × 2 legs × 20% = 1.4 NAV of risk-ETF notional, plus the same on the T-bill ETF. At 2 bps plus 1 bp (T-bill spread is my assumption) that is 1.4 × 3 = 4.2 bps a year; at 10 plus 3 bps it is 18.2 bps. On $1,250 that is **$0.5 to $2.3 a year**. Cost is not the issue. Tax and missed returns are.

**R5. Long/flat, no shorting.** Georgopoulou and Wang find the part of TSM that fund investors hold is its long side (FETCHED). This fits `no_shorting`.

**R6. Look-ahead is attacked directly.** Zakamulin (Int. Rev. Finance 2018; working paper FETCHED) shows Glabadanidis's striking moving-average results came from letting month-end t's signal earn month t's return. Corrected, MA(10) Sharpe was only marginally above buy-and-hold, statistically indistinguishable, with negative alphas (Fama-French deciles, 1960-2011, 50 bps one-way). The AsOfSnapshot and one-bar-lag tests target this error.

**R7. S0-RM and the post-2013 slice.** Holding less risk buys "half the drawdown" without timing (Huang et al.). Testing after Faber's 2013 update follows publication-decay logic (McLean-Pontiff, via brief 18; RECALLED).

## 2. What should improve

### S01-P1 (must): no live 12.5% satellite at launch; S-A in shadow; whole-book choice at L0
Ties to section 4 (core-satellite), section 7 (G4, G5), section 11 (P2, P3, P5).

*Protection arithmetic (ESTIMATE).* A sleeve of fraction s removes at most s × (buy-and-hold drawdown minus trend drawdown).
- Faber's five-asset figures, 1973-2012: about 46% buy-and-hold, under 10% timed (FETCHED, text; tables are images). 0.125 × 36 = **4.5 points**, about $450 on $10,000 in a 46% crash.
- With Antonacci's medians: 0.125 × 32.1 = 4.0 points.
- The same 12.5% in a T-bill ETF removes 0.125 × 46 = 5.75 points ($575), with no whipsaw and no tax events.
- The design's expected cost is -$14 to -$18 a year, and the best case is about $450 in a crash that comes perhaps once a decade, before shrinkage.

*Information arithmetic (ESTIMATE).* The standard error of an information ratio is about 1/√T. At 24 months, SE ≈ 0.71 against an effect near 0.2. Detecting IR 0.2 at 95% needs (1.96/0.2)² ≈ **96 years**. The design already concedes G1b "cannot be powered". So G4 and G5 cannot validate S-A. They only exercise the executor, which S0 tranches and band rebalances exercise anyway.

*Change.*
- S-A runs in shadow from P1a (signal and shadow NAV, near-free).
- At L0 the owner picks per account: (a) S0 with a T-bill dial b (default); (b) S-A as the whole risk book, only in a tax-deferred account (H = 0), where the drawdown benefit is large enough to matter; (c) neither.
- Drop XFER netting, per-sleeve attribution, the combined-book wash-sale simulation, the G4/G5 ladder and the S-A tracking-error band.

Cost $0 a month. Saves about **12-25 dev-days** (ESTIMATE; the design has no per-component split). Respects the binding constraints: no spend, lower solo load. Risk: no live S-A fills. Mitigation: GF drills, G3 paper, and S0 sells exercise the same path; mode (b) restores a live S-A if an IRA exists (O3).

### S01-P2 (must): replace "about half the drawdown" with sourced ranges, and say live results cannot confirm edge
Ties to section 1 and the G4 text.

State, in owner-facing text: CAGR effect about 0 ± 1 point; sleeve drawdown about 0.4 of buy-and-hold (Antonacci 21.4/53.5; Faber's claim is nearer 0.2, so use 0.4); cost 0.04-0.18% a year; lags buy-and-hold in many years (Faber, 2006-2012: won 3 of 7 years yet beat by over 2 points a year, FETCHED); decade net Sharpe for diversified trend has ranged from 0.13 to 1.70 (Hurst, Ooi and Pedersen Exhibit 1, FETCHED), so a bad decade is normal. A secondary summary of Zakamulin 2014 reports a high false-sell rate, about 80% (definition UNVERIFIED). Effort under 1 dev-day, $0. Risk: none to money.

### S01-P3 (should): scale the P2 harness to the one published rule; defer DSR, PBO and ONC until the first tuned Lab spec
Ties to section 7 (G1a-G1c) and section 11 (P2, 25-32 dev-days).

- G1a asks whether net SR exceeds zero. Any long-risk-asset rule passes that on 1973-2012 through the equity premium, and Huang et al. say TSM matches a historical-mean strategy. S0-RM in G1b is the real test.
- Criterion 6 is already marked not applicable to plain Faber. What remains is replication on ETF proxies since 1973 with costs and a one-bar lag, the offset band (P5), a tax table, and S0-RM.
- Make the P2 verdict a pre-registered decision memo, not an automatic retirement trigger. Retiring on a result that cannot be powered is arbitrary.
- Saves about **10-18 dev-days** (ESTIMATE), $0. Risk: gate code arrives later. Mitigation: no tuned spec runs live before it exists. The validation reviewer should confirm.

### S01-P4 (should): freeze the signal definition at G0
Ties to section 4 (S-A) and section 5.

- **Total-return series.** A price series omits distributions. With a 10-close SMA of average age 4.5 months, the bias is about y × 4.5/12 (ESTIMATE): 1.5% at a 4% yield, 1.3% at 3.5%, 0.5% for US equity. For a bond ETF that is a typical monthly move, so it creates false sells.
- **SMA convention.** Faber compares price with the last 10 month-end closes; Keller's SMA(12) averages 13 prices. Freeze one.
- **Execution convention.** Month-end signal, first-trading-day 10:00 fill, same in the backtest.

+0.5 dev-day, $0, no risk.

### S01-P5 (should): report the rebalance-day band, not one calendar
Ties to section 2 step 7 and section 7 (G1b).

A practitioner test of Faber's 10-month SMA on SPY with 21 one-day-offset schedules (Newfound, 2013; FETCHED, blog) found max drawdown moving from 19.0% to 30.2% on a one-day shift, and annual return from 11.33% to 10.51%. Hoffstein, Faber and Braun (2020; abstract only) report timing luck often above 100 bps a year. The harness runs all 21 offsets and reports the range; the live date is fixed by calendar and never tuned. +1-2 dev-days, $0. Risk: a wide band forces honest drawdown language.

### S01-P6 (could): keep launch simple; pre-rank alternatives; allow one shadow variant
Ties to section 4 ("Adding strategies") and the Lab backlog.

- **Keller's PAA, VAA, DAA, BAA and dual momentum: not at launch.** In the BAA paper (FETCHED), one-sided turnover is 284% (PAA-G12), 472% (BAA-G12) and 523% (BAA-G4), against Faber's 70%: 4 to 7.5 times higher, mostly short-term realisation in a taxable account. The author notes several choices were in-sample optimal, and full-sample CAGR of 14.6-21.0% against 9.5% for 60/40, from a family of four sequentially tuned models, looks like selection (Wiecki). The breadth idea is largely present already: five equal-weight independent signals make the risk-on share equal breadth.
- **Adding relative momentum:** Clare et al. (1993-2015, 95 markets, FETCHED) report +1.5 to +2.5 points of return at higher volatility. With five ETFs it means concentration and turnover.
- **One shadow variant:** an equal vote of 6-, 9- and 12-month absolute-momentum signals (positions 0, 1/3, 2/3, 1). Support is indirect: MA crossover and TSM are equivalent in general form (Levine and Pedersen, FETCHED), Faber says lengths 3-12 look similar (FETCHED), and optimal lookbacks are unstable. I found no head-to-head net-of-cost test against SMA10, so it stays in shadow.

+1-2 dev-days, $0.

### S01-P7 (should): defer the Shadow ML lane until after L0
Ties to section 4 ("Shadow ML lane") and section 11 (P6).

Its features (1/3/6/12-month returns, distance from the SMA) are the trend signal re-expressed. With about 1,200-1,500 pooled rows, weak predictability (Huang et al.) and poor backtest-to-live transfer (Wiecki), it cannot add independent information, and the design itself says "expect no edge". SHAP-style words for the Narrator can come from the signal table. Saves about 6-10 dev-days (ESTIMATE) and scarce Claude plan usage. $0. Risk: the owner's v1 heritage is less visible; keep the idea-ledger row as "deferred".

### S01-P8 (could): pre-registered exit-regret view in the Narrator
Ties to section 3 (Narrator) and section 6 (veto).

Trend loses when a crisis ends (March-May 2009; Moskowitz et al., FETCHED), and a V-shaped recovery is when the owner is most tempted to override. After each S-A exit the memo shows the asset's next 1-, 3- and 6-month return against T-bills and states beforehand that many exits will look wrong (P2). +1 dev-day, $0.

## 3. What I could not verify

- Faber's result tables are images; I read only text claims (46% to under 10% drawdown, 70% turnover, 3-4 round trips).
- **No ETF-era peer-reviewed test of a five-ETF SMA10 book after 2013 was found.** I ran no backtest and downloaded no price data.
- Antonacci's dual-momentum book was not opened, only the absolute-momentum paper.
- Keller and Keuning's DAA paper (SSRN 3212862) and Zakamulin's 2015 SSRN page returned 403. Zakamulin 2014 and 2015 come from abstracts and CXO summaries; the "80%" definition is from a search summary.
- Hoffstein et al., Bajgrowicz and Scaillet were seen only as abstracts.
- Tax figures are from the design and brief 19, not recomputed. Commodity/gold ETF structure (K-1, collectibles tax) belongs to the tax reviewer.
- All dev-day savings are my judgment.

## 4. References

1. Faber, "A Quantitative Approach to Tactical Asset Allocation" (SSRN 962461; 2013 update). https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf. FETCHED.
2. Moskowitz, Ooi, Pedersen, "Time Series Momentum", JFE 104 (2012). https://w4.stern.nyu.edu/facdir/lpederse/papers/TimeSeriesMomentum.pdf. FETCHED.
3. Hurst, Ooi, Pedersen, "A Century of Evidence on Trend-Following Investing" (AQR 2014). https://oxfordstrat.com/coasdfASD32/uploads/2016/03/A-Century-of-Evidence-on-Trend-Following-Investing.pdf. FETCHED.
4. Huang, Li, Wang, Zhou, JFE 135(3), 2020. https://ideas.repec.org/a/eee/jfinec/v135y2020i3p774-794.html. FETCHED (abstract).
5. Antonacci, "Absolute Momentum" (SSRN 2244633, 2014). https://c.mql5.com/forextsd/forum/207/Absolute%20Momentum%20-%20A%20Simple%20Rule-Based%20Strategy%20and%20Universal%20Trend-Following%20Overlay.pdf. FETCHED.
6. Zakamulin, "Revisiting the Profitability of Market Timing with Moving Averages" (SSRN 2743119; IRF 18(2), 2018). https://c.mql5.com/forextsd/forum/205/Revisiting%20the%20Profitability%20of%20Market%20Timing%20with%20Moving%20Averages__1.pdf. FETCHED.
7. Zakamulin, J. Asset Management 15(4), 2014. https://ideas.repec.org/a/pal/assmgt/v15y2014i4d10.1057_jam.2014.25.html. FETCHED (abstract); figures via https://www.cxoadvisory.com/technical-trading/net-performance-of-sma-and-intrinsic-momentum-timing-strategies (secondary).
8. Zakamulin, SSRN 2677212, via https://www.cxoadvisory.com/technical-trading/long-run-moving-average-horse-race-for-timing-the-u-s-stock-market. FETCHED (secondary only).
9. Georgopoulou, Wang, Review of Finance 21(4), 2017. https://pure.manchester.ac.uk/ws/portalfiles/portal/39718724/The_Trend_is_Your_Friend_Time_Series_Momentum_Strategies_Across_Equity_and_Commodity_Markets.pdf. FETCHED.
10. Keller, "Bold Asset Allocation" (SSRN 4166845, 2022). https://thechartist.com.au/wp-content/uploads/2024/12/5369/SSRN-id4166845.pdf. FETCHED. Keller and Keuning DAA (SSRN 3212862): FETCHED via https://www.cxoadvisory.com/strategic-allocation/multi-class-momentum-portfolio-with-canary-crash-protection/ only. PAA (SSRN 2759734): RECALLED.
11. Clare, Seaton, Smith, Thomas, JBEF 9 (2016). https://openaccess.city.ac.uk/id/eprint/17841/. FETCHED.
12. Levine, Pedersen, FAJ 72(3), 2016. https://research-api.cbs.dk/ws/files/60084063/lasse_heje_pedersen_et_al_which_trend_is_your_friend_publishersversion.pdf. FETCHED (abstract, introduction).
13. Wiecki et al., "All that glitters is not gold" (SSRN 2745220, 2016). http://ssrn.com/abstract=2745220. FETCHED.
14. Lempérière et al., "Two centuries of trend following", arXiv 1404.3274. FETCHED (abstract).
15. Kurth, Eisler, Rej, Bouchaud, arXiv 2607.01550 (July 2026). FETCHED (abstract).
16. Newfound Research, "The Luck of the Rebalance Timing" (2013). https://blog.thinknewfound.com/2013/08/the-luck-of-the-rebalance-timing/. FETCHED (blog). Hoffstein, Faber, Braun (2020): search abstract only.
17. Bajgrowicz, Scaillet, JFE 106(3), 2012. https://ideas.repec.org/a/eee/jfinec/v106y2012i3p473-491.html. Search abstract only.
18. McLean, Pontiff, J. Finance 2016. RECALLED (opened in brief 18, not by me).

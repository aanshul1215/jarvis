# S02 Review: benchmark and portfolio construction (core S0, band, ETF set, T-bill dial, small-order execution)

Reviewer: S02-benchmark-and-portfolio-construction. Date: 2026-10-02. Scope: FINAL-design.md sections 4, 6, 7 (G1a), 9 (Mission Plan dial) and the execution steps in section 2. All proposals cost $0 a month and add no metered API spend, so they respect the binding owner constraints (US/Texas, $1,000-$10,000, near-zero budget, 8 GB Windows laptop, solo developer).

Tags: FETCHED means I opened the source this session. "FETCHED (search summary)" means only a search-result summary of the page reached me, because the PDF or page would not render as text; I treat those as weaker. RECALLED means from memory, not opened. ESTIMATE means my arithmetic.

## 1. What the design gets right

**1. An equal-weight, fixed-parameter core is the correct kind of null.** DeMiguel, Garlappi and Uppal (RFS 2009) compared 14 optimising models against 1/N on seven datasets and found none consistently better on Sharpe ratio, certainty-equivalent return or turnover. They conclude that estimation error swamps the gain. Their calibration says the sample-based mean-variance rule needs roughly 3,000 months of data for 25 assets (FETCHED, RePEc abstract). S0 has no estimated parameters, so the null cannot overfit. Caveat: the paper's datasets are equity-style portfolios, not a five-asset-class mix (RECALLED), so it supports "do not optimise weights" more than "20% each is best".

**2. Using the same five assets for S0 and S-A is a like-for-like comparison.** Faber's 2013 five are the S&P 500, MSCI EAFE, GSCI commodities, NAREIT and 10-year Treasuries, each at 20% (FETCHED, search summary of a PDF I could not render; brief 18 also lists it). Comparing the timing rule to buy-and-hold of the same assets isolates the timing effect. That is the design's logic and it is sound.

**3. Calendar-plus-threshold rebalancing with a wide band, checked monthly, is what the rebalancing literature supports.**
- Vanguard (Jaconetti, Kinniry, Zilbering, 2010; 60/40, 1926-2009) finds no optimal frequency or threshold, that risk-adjusted returns are not meaningfully different across monthly, quarterly and annual rebalancing, and that annual or semi-annual monitoring with a 5-point threshold balances risk control and cost (FETCHED, search summary only; PDF text unreadable).
- Daryanani (JFP 2008) argues for wider bands, frequent looks, and rebalancing only the classes that are out of balance, and says trading costs and tax deferral are small relative to the rebalancing benefit (FETCHED, abstract only; he gives no numbers I could read).
- The design's relative ±20% on a 20% target is ±4 points. That sits between those two sources. The 24% ceiling also stays under the 25% per-symbol cap.

**4. No leverage and a T-bill dial is the right shape for this owner.** Asness, Frazzini and Pedersen (FAJ 2012) show that leverage-averse investors bid up risky assets, so safer assets earn higher risk-adjusted returns, and that capturing this needs leverage (FETCHED, abstract). Alpaca here is `no_shorting`, margin multiplier 1, so the owner cannot lever. The only risk lever left is the cash/T-bill share b, which is what S0(b) does.

**5. Limit orders, no auction orders, and fractional DAY orders are consistent with Alpaca's rules.** Alpaca's docs say fractional equity orders support DAY only and that market, limit, stop and stop-limit are allowed. Limit orders work for fractional and notional orders. OPG/CLS are listed as "contact sales" for whole-share orders (FETCHED, docs.alpaca.markets, both pages). So the opening and closing auctions are not available to this owner, and the design's marketable limit is the correct order type.

**6. The cost of S0's trading is negligible, so the real cost is tax.** See my simulation in P5 below. This confirms the design's emphasis on tax-lot deferral rather than cost optimisation.

## 2. What should improve

### S02-P1 (must): fix the ticker set now, and decide the commodity slot explicitly (section 4, "Universe")

The design says "commodities/gold" and leaves tickers to G0. That ambiguity matters for three reasons. Faber used broad commodities (GSCI), not gold, so gold means S-A is no longer "plain Faber as published" and is a registered trial. Both sleeves are netted per symbol, so one ticker per slot must serve both. And the choice drives the history available to G1a (P2).

Proposed set (expense ratios and inception dates from issuer pages or fund documents; all FETCHED unless marked):

| Slot | Ticker | Expense ratio | Inception | Note |
|---|---|---|---|---|
| US equity | VTI | 0.03% | 2001-05-24 | FETCHED (search summary of Vanguard page) |
| Developed ex-US | VEA | 0.03% (as of 2026-04-28) | 2007 (RECALLED) | FETCHED (search summary) for the ratio |
| Intermediate Treasuries | IEF | 0.15% | 2002-07-22 | FETCHED (search summary of iShares page); 7-10 year, closest to Faber's 10-year |
| REIT | VNQ | 0.13% | 2004-09-23 | FETCHED (search summary of Vanguard page) |
| Gold | GLDM | 0.10% | 2018-06-25 | FETCHED (search summary of SSGA page). Alternative IAUM: 0.09% sponsor fee, voluntarily waived to 0.07% through 2027-06-30, inception 2021-06-15, median spread 0.02% (FETCHED, iShares page and 10-K summary) |
| T-bill dial | SGOV | 0.09% | May 2020 (RECALLED) | FETCHED (iShares page, 2026-09-30): 30-day SEC yield 3.67%, median spread 0.01%, net assets $112.3 billion |

**Arithmetic (ESTIMATE).** Weighted expense ratio of S0 = 0.2 × (0.03 + 0.03 + 0.15 + 0.13 + 0.10) = 0.2 × 0.44 = 0.088% a year, or $8.80 on $10,000 and $0.88 on $1,000. Swapping IEF for VGIT (0.03%, but a 3-10 year index, so a different duration; FETCHED search summary) saves $2.40 a year per $10,000. That is not worth departing from Faber's maturity, so keep IEF.

**Tax gap the design does not mention.** Gold held through a physical-gold grantor trust is taxed as a collectible. A long-term gain is capped at 28% rather than 15-20%, per the sponsor's FAQ summary (FETCHED, search summary) and IRS Topic 409, which states the 28% maximum for collectibles but does not name gold ETFs (FETCHED). The G1b tax simulator needs a collectibles bucket for the gold slot. Searching the design and briefs 18-19 for "collectible" or "28%" found no hit.

Cost: $0. Build effort: about +0.5 dev-day for the collectibles bucket; saves open-ended debate at G0. Risk: gold is a deliberate deviation from Faber, so S-A's G1a evidence (Faber's published results) transfers imperfectly. Mitigation: register the gold swap as a trial, and report a GSCI-proxy variant as information only.

### S02-P2 (must): pre-register research proxies so G1a can actually gate (section 7, G1a; open item O14)

G1a gates only if the pooled history is at least 20 years from the latest inception among the five tickers. With the P1 set, the latest inception is GLDM (2018-06-25), giving 8.3 years at 2026-10-02 (2026.75 − 2018.48 ≈ 8.3, ESTIMATE). Even VEA (2007) gives about 19.2 years, just under 20. The design would then cap S-A at 25% as "unvalidated", for a reason that is purely a ticker-choice artifact.

Fix: trade the cheap tickers and research on same-exposure sister funds, with proxies fixed in the G0 spec before any run.
- GLDM, IAUM → GLD (inception 2004-11-18, expense ratio 0.40%; FETCHED, search summary of SSGA/SEC documents). Subtract the difference of 0.30 points a year (0.40 − 0.10) from the proxy return, labelled as an adjustment.
- VEA → EFA (RECALLED, inception about August 2001; verify on the iShares page in P2 day 1).
- SGOV → FRED 3-month Treasury series (RECALLED series IDs TB3MS or DTB3; the design already uses FRED).

Pooled history then starts at the GLD/VNQ inceptions (2004-11-18 and 2004-09-23), which is about 21.9 years at 2026-10-02 (2026.75 − 2004.88, ESTIMATE). That clears the 20-year gate by about two years. brief 20's MinBTL figures (N = 5/10/20 need about 5.7/9.9/14.5 years) then leave room.

Cost: $0. Effort: about +1 dev-day in the P2 inventory, offset by removing the capped-S-A branch if it never triggers. Risk: proxy mismatch (GLD vs GLDM is the same bullion; EFA vs VEA differ in index and Canada/Korea treatment, RECALLED). Report tracking difference between proxy and trade ticker over their overlap, in the P2 report.

### S02-P3 (could): keep S0 as the null, but label it and add one shadow reference (section 4, S0; section 7, G1b)

DeMiguel et al. justify 1/N as a null for a rule that must estimate weights. They do not show that 20% in each of five classes is the right wealth portfolio. Doeswijk, Lam and Swinkels (FAJ 2014) report the global multi-asset market portfolio at end-2012 as about 36.3% equities and 29.5% government bonds of $90.6 trillion (FETCHED, abstract), far from S0's 40% equities, 20% listed REITs and 20% gold. S0 is a deliberate tilt (Faber's), with equity-like risk (stocks, ex-US and REITs together are 60% of dollars) and about 20% in bonds. Asness et al. suggest a risk-balanced mix would hold more bonds, but that needs leverage the owner does not have.

Proposal: say so in the Mission Plan ("S0 is the like-for-like null for S-A, not a recommendation"). Add one shadow-only column, S0-2F: a two-fund 60/40 global stock/bond (for example a global equity ETF and a total bond ETF, tickers fixed at G0). It carries no gate and no trial count. It answers the question the owner will actually ask: "would two funds have done as well?"

Cost $0. Effort about +0.5 dev-day (reuses the S0 code with different weights). Risk: a second benchmark invites cherry-picking. Mitigation: it is reported, never gates.

### S02-P4 (should): set the T-bill dial from a stress loss, rounded in steps (section 9 Mission Plan, section 4 S0(b))

The design sets b so that S0(b)'s bootstrap p95 drawdown in dollars is no more than the stated tolerance. A bootstrap on about 22 years of monthly data underweights tail clustering (2008) and fits one path. Use the larger of two numbers.

b = max(0, 1 − tolerance$ / (DD_stress × capital)), where DD_stress = max(worst historical peak-to-trough of S0 over the proxy history, bootstrap p95). Round b up to the next 10%. Change b only at the monthly decision window, and only if the new value differs by at least 10 points.

**Worked example (ILLUSTRATIVE; the 30% stress figure is a placeholder, not data).** Capital $5,000, tolerance $1,000, DD_stress 30%: b = 1 − 1,000 / (0.30 × 5,000) = 1 − 0.667 = 0.33, rounded up to 40%. Stress loss = 0.60 × 0.30 × $5,000 = $900, inside the tolerance. The 40% sleeve earns about the SGOV yield (3.67% SEC yield on 2026-09-30, FETCHED) minus 0.09%, so the dial gives up equity premium but not income.

**Small-account guard.** At $1,000 with b = 40%, each risky sleeve is $120, so a ±20% relative band is ±$24, about the $20 minimum order. Set the band's half-width to the larger of ±20% relative and ±3 points of account equity (DC, pre-register). This prevents $20 noise trades.

Cost $0. Effort about +0.5 dev-day in the Mission Plan code. Risk: DD_stress is only as good as the proxy history; the Narrator must show it as a range.

### S02-P5 (should): keep the ±20% relative band, freeze it, and stop tuning it (sections 4, 6, 7)

The sources do not prefer any particular band (Vanguard: no optimal threshold; Daryanani: wider is better, bands are second-order to look frequency). I tested the specific rule by simulation.

**ESTIMATE, simulation.** Five assets, monthly returns, i.i.d. lognormal, 1,500 paths of 20 years, rebalanced to 20% each when any weight leaves 16-24%, checked monthly. Assumed annual volatility (US stocks 16%, ex-US 18%, Treasuries 6.5%, REITs 20%, gold 16%), assumed arithmetic means (7%, 7%, 4%, 7%, 5%), assumed correlations (stocks-ex-US 0.85, stocks-REIT 0.75, others 0 to 0.2). These inputs are my own placeholders, not data.
- Rebalance events: about 0.70 a year.
- One-way turnover per event: about 5.7% of the portfolio; about 4.0% a year.
- Mean log growth: 5.45% band-rebalanced versus 5.46% buy-and-hold. The difference is within noise.
- Cost: 0.04 sold + 0.04 bought = 8% of the portfolio traded a year × 2 bps = 0.0016% a year, about $0.16 on $10,000.

Consequences. First, the band is a risk-control device, not a return source, so the Narrator must not claim a "rebalancing bonus". Willenbrock (FAJ 2011) explains that the diversification return comes from rebalancing's sell-winners, buy-losers mechanics (FETCHED, abstract), but under my assumptions it is nil at this band width. Second, trading cost is not a reason to widen the band; tax is. The design's tax-lot deferral and "dividends and contributions first" are the right levers. Third, the owner should not spend time on band sensitivity. Remove any band cell from the G0 grid, freeze ±20% relative with the P4 floor, and describe it as "DC, supported weakly by Vanguard and Daryanani". Rebalance only the breaching sleeves and use dividends or contributions before sales.

Cost $0. Effort: saves about 0.5-1 dev-day of grid work. Risk: results change under fat tails and regime shifts, which the iid simulation ignores; the band's effect is still small.

### S02-P6 (should): move the decision-day order window to start at 10:30 ET (section 2, steps 1 and 11)

The design runs at 10:00 with orders allowed from 09:45 and a retry at 11:00. Sources on ETF liquidity say spreads are widest near the open and settle about 30 minutes after it. Dimensional's tick-level study of UCITS ETFs (Jan 2024-Jun 2025, funds above $100 million) finds the same and notes spread increases at 8:30, 9:30 and 10:00 New York time around US data releases and the US open (FETCHED). It is European data, so it is indirect for US ETFs. Practitioner guides also say to avoid the first and last 15-30 minutes (FETCHED, search summary). The SEC staff study of 24 August 2015 attributed part of the open dislocations to market orders and reported more than 1,000 halts in 327 exchange-traded products (FETCHED, search summary of secondary coverage; the SEC PDF would not render).

Proposal: earliest order time 10:30 ET, main run 10:30, retry 11:30, latest 15:30 (unchanged). Keep the marketable limit at 10 bps. Median spreads on the proposed trade ETFs are 0.01-0.02% (SGOV, IAUM; FETCHED), so 10 bps is five to ten times the spread: it protects without costing. Never use market orders; OPG/CLS are unavailable for fractional DAY orders. Shift the Claude Code blackout to 10:15-12:15 ET.

Cost $0. Effort about 0 (config). Risk: my 10:00 data-release concern, that a scheduled release lands at 10:00 on the first business day, is RECALLED (ISM); if true it favours 10:30 further. The US-specific intraday pattern for these particular tickers is unmeasured; the existing quote-age and slippage logging (step 15) will measure it in the first 20 sessions.

## 3. What I could not verify

- The Vanguard rebalancing paper's own tables: both PDF copies fetched were unreadable, so the 5-point threshold and "no optimal frequency" come from a search-result summary, not the paper.
- Daryanani's quantitative results (abstract only), Faber's own text (PDF unreadable; the five assets are from a search summary), and Asness et al.'s empirical results (abstract only).
- Doeswijk et al.: only the 2012 equity and government-bond weights from the abstract; I did not see whether gold or commodities are in their asset set (RECALLED: they are not).
- VEA's and EFA's and SGOV's inception dates, the BIL expense ratio, and FRED series IDs (RECALLED).
- The Madhavan and Sobczyk (2016) ETF liquidity paper (paywalled) and any US-specific intraday spread study.
- The IRS statement that gold ETFs specifically are collectibles: Topic 409 gives the 28% maximum for collectibles but does not name them; the ETF link rests on the sponsor FAQ summary.
- Whether Alpaca pays interest on idle cash (not researched).
- My simulation uses assumed volatilities, correlations and means and an i.i.d. model; it is a plausibility check, not evidence.

## 4. References

1. DeMiguel, Garlappi, Uppal (2009), "Optimal versus naive diversification", Review of Financial Studies 22(5):1915-1953. https://ideas.repec.org/a/oup/rfinst/v22y2009i5p1915-1953.html. FETCHED (abstract).
2. Doeswijk, Lam, Swinkels (2014), "The global multi-asset market portfolio, 1959-2012", Financial Analysts Journal 70(2):26-41. https://ideas.repec.org/a/taf/ufajxx/v70y2014i2p26-41.html. FETCHED (abstract).
3. Asness, Frazzini, Pedersen (2012), "Leverage aversion and risk parity", FAJ 68(1):47-59. https://rpc.cfainstitute.org/research/financial-analysts-journal/2012/leverage-aversion-and-risk-parity. FETCHED (abstract; AQR PDF unreadable).
4. Willenbrock (2011), "Diversification return, portfolio rebalancing, and the commodity return puzzle", FAJ 67(4):42-49. https://arxiv.org/abs/1109.1256. FETCHED (abstract).
5. Jaconetti, Kinniry, Zilbering (2010), "Best practices for portfolio rebalancing", Vanguard Research. https://www.aaii.com/files/journal/pdf/best-practices-for-portfolio-rebalancing.pdf (PDF unreadable). FETCHED (search summary only).
6. Daryanani (2008), "Opportunistic rebalancing: a new paradigm for wealth managers", Journal of Financial Planning, January. https://www.financialplanningassociation.org/article/journal/JAN08-opportunistic-rebalancing-new-paradigm-wealth-managers. FETCHED (abstract).
7. Faber (2007/2013), "A quantitative approach to tactical asset allocation". https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf. FETCHED (search summary; PDF unreadable).
8. Alpaca docs: https://docs.alpaca.markets/us/docs/orders-at-alpaca and https://docs.alpaca.markets/docs/fractional-trading. FETCHED.
9. iShares SGOV page: https://www.ishares.com/us/products/314116/ishares-0-3-month-treasury-bond-etf. FETCHED. iShares IAUM page: https://www.ishares.com/us/products/306979/ishares-gold-trust-micro. FETCHED.
10. Vanguard VTI, VEA, VGIT, VNQ pages and fact sheets (advisors.vanguard.com, fund-docs.vanguard.com); SSGA GLDM and GLD pages; iShares IEF page. FETCHED (search summaries; the direct page fetches returned titles only).
11. IRS Topic 409, Capital gains and losses: https://www.irs.gov/taxtopics/tc409. FETCHED.
12. Dimensional Fund Advisors, "Overview of the European ETF market": https://www.dimensional.com/gb-en/insights/overview-of-the-european-etf-market. FETCHED. Practitioner guides on ETF trading times (VanEck, ETF Trends, Alpha Architect): FETCHED (search summary only).
13. SEC staff, "Equity market volatility on August 24, 2015". https://www.sec.gov/marketstructure/research/equity_market_volatility.pdf. PDF unreadable; FETCHED (search summary of secondary coverage only).
14. Madhavan, Sobczyk (2016), "Price dynamics and liquidity of exchange-traded funds", Journal of Investment Management 14(2). RECALLED (paywalled).

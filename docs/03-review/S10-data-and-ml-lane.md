# S10 review: free data and the shadow ML lane

Reviewer S10, 2026-10-02. Scope: FINAL-design.md section 5 (data plan), section 4 (Shadow ML lane), section 7 (G1a), section 11 (P2), section 15 (O10, O14). All web pages were read through a fetch-and-summarise tool, so every licence clause below should be read by eye on the vendor page before the owner relies on it. Nothing in this report costs money; where a proposal could, it says so.

## Short answers

1. **Two-vendor plan:** $0 in money, but not clean in licence. Tiingo's Terms of Use (updated 2026-08-05, as read) let Starter and free accounts process data only in memory, never on disk, while the design stores a hashed research copy and replayable snapshots.
2. **20+ years:** the real ETFs already have about 20-22 years; the issue is where history may be stored, and proxies must never rescue a failing strategy.
3. **ML lane:** as written (forward scoring at weight 0 as validation) it cannot reach a verdict in the owner's horizon, so it is theatre. As a time-boxed, baselined exhibit it is worth about 5 dev-days at $0.

## What the design gets right

- **Raw bars plus a corporate-actions table, adjusted as of the decision date.** Alpaca's bars endpoint offers raw, split, dividend and all adjustments, and Alpaca exposes a `/v1/corporate-actions` endpoint (splits, dividends, name changes, with ex-date and process date). Alpaca warns that actions can arrive late. FETCHED (Alpaca corporate-actions and stock-bars docs). This supports the design's choice and the 30%-move quarantine.
- **Alpaca Basic as the live price source.** Free means IEX-only, 200 calls a minute, history since 2016, and the latest 15 minutes of SIP withheld. FETCHED (about-market-data page). Alpaca itself puts IEX at about 2.5% of volume, which is why IEX is used for collars only. FETCHED (historical-data page).
- **FRED/ALFRED for the cash rate, with attribution.** `realtime_start`, `vintage_dates` and `output_type=4` (initial release) exist. FETCHED. The terms require a visible "not endorsed" notice and bar third-party copyrighted series beyond personal use; they have no clause on storage or trading use. FETCHED.
- **EDGAR at 10 requests a second with a declared User-Agent.** Both stated on sec.gov. FETCHED.
- **Tree model first, no deep learning.** Grinsztajn, Oyallon and Varoquaux (2022): on 45 tabular datasets, trees remain state of the art at roughly 10,000 samples, helped by robustness to uninformative features. FETCHED.
- **Weight zero, no separate ML gate, leak tripwires.** This fits the warning that financial ML is low signal-to-noise and needs economic structure (Israel, Kelly, Moskowitz, 2020; abstract only FETCHED). v1's 0.999 correlation is what the tripwires catch.

## What should improve

### S10-P1 (must): Treat Tiingo Starter as a transient verifier, not a stored source (section 5 data table; section 2 step 5; O10)

- **Evidence.** Tiingo ToS 1.6, as summarised: Trial and Starter plans (free is treated as Trial) may hold data only transiently in memory; the ban names disks, databases, logs, backups and archives. Derived products (aggregates, percentage changes, rankings, cryptographic hashes) are allowed. FETCHED (app.tiingo.com/tos). Starter is 50 requests an hour, 1,000 a day, 500 symbols a month. FETCHED.
- **Change.** (a) Drop the stored Tiingo research copy; keep only the trust-gate result (agreement in bps, both close hashes, pass/fail). (b) The month-end check pulls about 6 symbols into memory per run, far inside the 1,000-a-day limit. (c) Anchor replay and G2 identity on stored Alpaca bars and FRED. (d) Source `corporate_actions` from Alpaca. (e) Add `docs/data_licences.md`: source, storage right, date the terms were read. (f) Email Tiingo support once: does trading one's own money count as personal use? The ToS do not say (individuals may use Individual plans, 7.3; "commercial purpose" is barred, 5.2), and the pricing-page summary said for-profit use needs Power. If no or unclear, drop Tiingo from the gate (P2).
- **Cost.** $0. Paying is no way out: Power is $30 a month (FETCHED) = $360 a year, 3.6% of $10,000 and 36% of $1,000, and fails the design's 600x rule (needs $18,000). A downgrade also forces deletion of stored data.
- **Effort.** Saves about 1-2 dev-days; licence file adds 0.5.
- **Risk.** Alpaca's storage terms sit in Nasdaq and NYSE subscriber agreements I did not read (UNVERIFIED).

### S10-P2 (must): Make the second vendor optional with a pre-registered fallback (section 2 step 5; D20)

- **Change.** If Tiingo is unavailable or disallowed, the gate becomes Alpaca SIP close versus Alpaca IEX-derived close, plus the 30% move and corporate-actions check, plus the collar. "A failing symbol gets no risk-increasing order" stays; threshold stays 0.5% (DC).
- **Why.** Six very liquid ETFs rebalanced monthly mostly fail through a missing bar, a stale bar or a missed split or distribution; these are caught without a second vendor. That this dominates is my judgement (DC). Evidence: Alpaca docs and Tiingo terms above (FETCHED).
- **Cost.** $0. **Effort.** Neutral to minus 1 day. **Risk.** Weaker independence (common-mode vendor error), accepted.

### S10-P3 (must): Pre-commit the 20-year history plan and make proxies veto-only (section 7 G1a; section 11 P2 day 1; O14)

- **Where the 20 years comes from.** Inception dates: EFA 2001-08-14 (FETCHED, iShares); SPY 1993, IEF 2002, VNQ Sept 2004, GLD Nov 2004, DBC Feb 2006 (all RECALLED; P2 day 1 must confirm). Latest inception among the first five is GLD, Nov 2004. ESTIMATE: Nov 2004 to Oct 2026 is about 21.9 years; adding DBC makes it about 20.7. A 10-month SMA warm-up costs about 0.8 year. So real-ETF history is just over the 20-year G1a line, with no proxies. Choose the commodity/gold slot from tickers with at least 20 years (GLD, DBC), not newer baskets (a 2014 basket would give about 12).
- **Cash leg.** Use FRED TB3MS (monthly, from the Federal Reserve H.15; FETCHED) for pre-2007 cash, not a T-bill ETF, whose history is shorter (RECALLED, about 2007). TB3MS is quoted on a discount basis (FETCHED). ESTIMATE: at 3.72% for 91 days the bond-equivalent yield is 365 x 0.0372 / (360 - 0.0372 x 91) = 13.578 / 356.615 = 3.81%, so the raw series understates cash by about 0.09 point; convert it.
- **Proxy ladder for robustness (monthly, not daily, because the rule is monthly).**

| Slot | Proxy (storage-friendly source) | Status |
|---|---|---|
| US equity | Ken French US market return from 1926 | Library confirmed, equities only (FETCHED); market series and terms RECALLED |
| Developed ex-US | VGTSX from 1996-04-29 (FETCHED, AAII); MSCI EAFE index from 1969 | MSCI free download and terms UNVERIFIED (page unreadable) |
| REITs | FTSE Nareit All Equity REITs monthly index, 1972 onward | Download exists, (c) Nareit, terms unread (FETCHED page) |
| Gold | World Bank commodity "Pink Sheet" monthly, CC BY licence (FETCHED); gold series RECALLED from 1960. Not FRED: FRED removed the LBMA gold series on 2022-01-31 (FETCHED) | Gold coverage UNVERIFIED |
| Intermediate Treasuries | FRED constant-maturity yields converted to approximate returns, or Damodaran's annual 10-year bond returns from 1928 as a sanity check (annual only, FETCHED) | Conversion is mine (DC) |

- **Rule (DC).** G1a gates on the real-ETF window only. The proxy window (1973 onward, the span Faber used, RECALLED) is informational and **may veto but never rescue**: if S-A fails on proxies, it is retired; if it passes only on proxies, it stays capped at 25%. Reason: pre-2007 is in-sample for a rule published in 2007 (RECALLED), and the trend-friendly 1970s would flatter S-A.
- **Cost.** $0. **Effort.** Adds about 3 dev-days to P2 (day 1 inventory becomes 4 days). **Risk.** Splice errors at the proxy-to-ETF join; mitigate by reporting the overlap period correlation and tracking error.

### S10-P4 (should): Use proxies to train and the real-ETF era to test the ML lane (section 4 ML lane; section 7 G1c)

- **Change.** Walk-forward expanding window: train on the proxy-extended panel, first test point at least 10 years in, score only on actual-ETF months. Do not pool proxy and ETF rows in the test set.
- **Why.** The design's 1,200-1,500 rows (5 ETFs x about 21.9 years x 12 = 1,314 before warm-up; ESTIMATE) become roughly 2,700 with 45 years of proxies (5 x 45 x 12), with an untouched real-instrument test.
- **Evidence.** Gu, Kelly and Xiu (RFS 2020) use nearly 30,000 US stocks, 94 characteristics and 60 years to December 2016 (NBER abstract FETCHED, sample size from a search snippet; their roughly 0.4% monthly out-of-sample R-squared is RECALLED). That is millions of stock-months; JARVIS has about three orders of magnitude fewer, and five ETFs are highly correlated.
- **Cost.** $0. **Effort.** About 1 day. **Risk.** Proxies differ from the ETFs (fees, tracking); the test avoids leaning on them.

### S10-P5 (must): Re-specify the ML lane's baselines and evidence (section 4; section 7 G1c)

- **Evidence.** Welch and Goyal (RFS 2008; NBER w10483): popular predictors looked good in-sample, but "not a single one" beat the historical mean out of sample, per the NBER abstract (FETCHED). Goyal, Welch and Zafirov (RFS 37(11), 2024) re-test 29 newer variables to end-2021: more than a third lose in-sample significance, and half of the rest do poorly out of sample (FETCHED, SFI page). The prior for a monthly asset-class model should therefore be "no skill", and the benchmark is the expanding mean, not a coin flip.
- **Change.** (a) Baselines: expanding-mean hit rate; the S-A rule's own signal (price above 10-month SMA) as a binary predictor; 12-month return sign. (b) Add a regularised logistic regression on the same six features as co-primary, with LightGBM as the challenger. (c) Fix LightGBM a priori: depth 2-3, at most 200 trees, minimum 50 samples per leaf, monotone constraints where sensible; any tuning is a registered trial. (d) Use an expanding walk-forward (the Welch-Goyal protocol) rather than K-fold. Report AUC and Brier skill against each baseline with block-bootstrap intervals.
- **Cost.** $0. **Effort.** Minus 1 day (smaller model) plus 1 day (baselines) = neutral. **Risk.** None to money; the lane stays weight 0.

### S10-P6 (must): Say plainly that forward scoring cannot adjudicate the ML lane (section 4; section 7 G4; D2)

- **Arithmetic (ESTIMATE).** AUC standard error under no skill: sqrt((n1 + n2 + 1) / (12 n1 n2)). For 1,250 rows split 750/500: 1,251 / (12 x 375,000) = 2.78e-4, SE = 0.017. With correlation 0.3 across the five ETFs (my assumption), n_eff = 1,250 / (1 + 4 x 0.3) = about 570 and SE = 0.025, so AUC 0.55 is only 2 SE out, before multiple-testing deflation. Going forward there are 60 rows a year, about 27 effective. SE 0.025 needs n = 1 / (2.88 x 0.000625) = 555 effective rows, so 555 / 27 = about 20.6 years.
- **Change.** Historical walk-forward (P5) is the evidence; forward scoring is a leak tripwire and a sanity check, not a path to money inside 20 years. Delete any wording suggesting a forward verdict is coming. Pre-register the terminal status: if the P5 intervals include no skill or fail to beat the SMA baseline, the dashboard label reads "no skill demonstrated" and the lane continues only as an exhibit.
- **Cost.** $0. **Effort.** Saves about 1 day (no forward-verdict machinery). **Risk.** The owner may feel the lane is hollow; P7 and P8 give it honest value.

### S10-P7 (should): Time-box the lane and move it off the critical path (section 11 P6; section 3 Narrator)

- **Change.** Cap at 5 dev-days, after P2's harness exists. The Narrator may quote ML output only as "exhibit, no demonstrated skill" until the lane passes G1c on a spec that survives deflation. v1's TSLA-style model stays archived as a post-mortem showing the leak, which is the most useful heritage item.
- **Evidence.** Israel, Kelly, Moskowitz (abstract only, FETCHED): economic theory and human expertise are decisive in financial ML. Welch and Goyal as above.
- **Cost.** $0; protects Claude plan usage. **Effort.** Minus about 3-5 dev-days against an open-ended lane. **Risk.** Low.

### S10-P8 (should): Stability gate before SHAP reaches the owner (section 3 Narrator, section 4)

- **Change.** SHAP top-3 appear in the memo only if they are stable across the last 5 refits (same three features in at least 4 of 5; DC), and are labelled "explains the model, not the market". With 1,250 correlated rows, drivers will wobble.
- **Evidence.** Grinsztajn et al. and Welch-Goyal (low-signal, small-sample setting); the threshold is mine (DC).
- **Cost.** $0. **Effort.** 0.5 day. **Risk.** Often shows no drivers, which is the honest result.

## What I could not verify

- Tiingo ToS wording came through a summariser; the "free = trial, no persistence" reading is central to S10-P1, so the owner should read section 1.6 directly. Whether trading one's own money is "personal" is unanswered.
- Alpaca's storage terms; whether the free plan includes the corporate-actions endpoint (docs silent).
- Stooq: the fetch returned nothing, and a search snippet says a CAPTCHA-issued API key is now required. No licence found; do not build on it.
- MSCI EAFE free download and terms; Nareit and Ken French terms; World Bank gold coverage from 1960; Vanguard VFITX and VGSIX inception dates.
- Inception dates of SPY, IEF, VNQ, GLD, DBC and the T-bill ETF (RECALLED).
- Gu-Kelly-Xiu R-squared and cost treatment: the PDF could not be parsed and two summaries conflicted, so I used only the sample description.
- Full texts of Israel-Kelly-Moskowitz and Welch-Goyal; Faber's SSRN page (403); the AQR Century summary gave an implausible sample period, so I do not use it.

## References

1. Tiingo, Pricing. https://www.tiingo.com/about/pricing and https://www.tiingo.com/account/billing/pricing. FETCHED.
2. Tiingo, Terms of Use (updated 2026-08-05), sections 1.1, 1.6, 5.2, 7.3. https://app.tiingo.com/tos/. FETCHED.
3. Tiingo, End-of-day API documentation. https://www.tiingo.com/documentation/end-of-day. FETCHED.
4. Alpaca, About Market Data API. https://docs.alpaca.markets/docs/about-market-data-api. FETCHED.
5. Alpaca, Historical stock data (feeds, IEX about 2.5%). https://docs.alpaca.markets/docs/historical-stock-data-1. FETCHED.
6. Alpaca, Corporate actions. https://docs.alpaca.markets/reference/corporateactions-1. FETCHED.
7. FRED API terms of use. https://fred.stlouisfed.org/docs/api/terms_of_use.html. FETCHED.
8. FRED, series_observations. https://fred.stlouisfed.org/docs/api/fred/series_observations.html. FETCHED.
9. FRED, TB3MS. https://fred.stlouisfed.org/series/TB3MS. FETCHED. FRED removal of IBA series. https://news.research.stlouisfed.org/2022/01/ice-benchmark-administration-ltd-iba-data-to-be-removed-from-fred/. FETCHED.
10. SEC, Accessing EDGAR data and developer resources. https://www.sec.gov/os/accessing-edgar-data, https://www.sec.gov/about/developer-resources. FETCHED.
11. Grinsztajn, Oyallon, Varoquaux (2022), "Why do tree-based models still outperform deep learning on tabular data?", arXiv 2207.08815 (NeurIPS Datasets and Benchmarks, RECALLED). https://arxiv.org/abs/2207.08815. FETCHED (abstract).
12. Gu, Kelly, Xiu (2020), "Empirical Asset Pricing via Machine Learning", Review of Financial Studies 33(5). https://www.nber.org/papers/w25398. FETCHED (abstract); sample size from search snippet; R-squared figures RECALLED.
13. Welch, Goyal (2008), "A Comprehensive Look at the Empirical Performance of Equity Premium Prediction", RFS 21(4). https://www.nber.org/papers/w10483 (2004 working paper). FETCHED (abstract).
14. Goyal, Welch, Zafirov (2024), "A Comprehensive 2022 Look at the Empirical Performance of Equity Premium Prediction", RFS 37(11):3490-3557. https://www.sfi.ch/en/publications/a-comprehensive-2022-look-at-the-empirical-performance-of-equity-premium-prediction. FETCHED (abstract).
15. Israel, Kelly, Moskowitz (2020), "Can Machines 'Learn' Finance?", Journal of Investment Management. https://www.aqr.com/Insights/Research/Journal-Article/Can-Machines-Learn-Finance. FETCHED (landing page and abstract only).
16. Damodaran, Historical returns on stocks, bonds, bills, real estate, gold (annual, 1928-2025). https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html. FETCHED.
17. World Bank, Commodity Markets (Pink Sheet, CC BY). https://www.worldbank.org/en/research/commodity-markets. FETCHED.
18. Nareit, Monthly index values and returns. https://www.reit.com/data-research/reit-indexes/monthly-index-values-returns. FETCHED.
19. Ken French data library. https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html. FETCHED.
20. iShares EFA page (inception 2001-08-14). https://www.ishares.com/us/products/239623/ishares-msci-eafe-etf. FETCHED. AAII VGTSX (inception 1996-04-29). https://www.aaii.com/fund/ticker/VGTSX. FETCHED.
21. Hurst, Ooi, Pedersen (2017), "A Century of Evidence on Trend-Following Investing", JPM. https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing. FETCHED (landing page; sample dates not relied on).
22. Faber (2007), "A Quantitative Approach to Tactical Asset Allocation", SSRN 962461. RECALLED (page returned 403).
23. Campbell, Thompson (2008) out-of-sample R-squared; Corsi (2009) HAR-RV. RECALLED, not opened.


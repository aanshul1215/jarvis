# 19 - After-tax drag and account type

Date: 2026-10-01. Constraints per CONTEXT section C: US resident, $1,000-$10,000 of own money, near-zero budget, solo developer. This is research, not tax advice.

## Questions

1. What do IRS sources say about short-term versus long-term gains, wash sales for securities, wash sales for crypto (was legislation enacted?), and Form 1099-DA?
2. ESTIMATE the after-tax gap between a strategy that realises gains short-term (monthly-rebalanced trend) and a buy-and-hold ETF allocation, for several marginal-rate cases.
3. Can automated/API trading run inside an IRA? Alpaca, Interactive Brokers, others; restrictions and crypto availability.
4. What does this imply for where JARVIS runs, the true hurdle rate, and what to ask a tax professional?

## Findings

### 1. US federal rules (all FETCHED from irs.gov unless stated)

- **Holding period.** Held more than one year = long-term; one year or less = short-term. Net short-term gains are taxed as ordinary income at graduated rates. The page (updated 2026-09-24) still shows 2025 long-term thresholds: 0% up to $48,350 taxable income (single), 15% up to $533,400, 20% above. Net capital losses offset gains, then up to $3,000 a year of ordinary income, with indefinite carryforward. [IRS Topic 409]
- **2026 figures.** IRS release gives a 2026 single standard deduction of $16,100 and brackets 10% to $12,400, 12% to $50,400, 22% to $105,700, 24% to $201,775, 32% to $256,225. The 2026 long-term thresholds ($49,450 / $545,500 single) come only from secondary sites (medium confidence; not read in Rev. Proc. 2025-32, whose PDF was unreadable to the fetch tool).
- **Wash sale, securities.** A loss is disallowed if substantially identical stock or securities are bought within 30 days before or after the sale. The disallowed loss is added to the replacement's basis and the holding period carries over (Pub. 550, 2025). Rev. Rul. 2008-5 (FETCHED): if you sell at a loss in a taxable account and your IRA or Roth IRA buys substantially identical shares within the window, the loss is disallowed and the IRA gets no basis increase, so the loss is permanently lost.
- **Wash sale, crypto.** The IRS treats digital assets as property, not currency (IRS digital-assets page). Section 1091 covers "stock or securities," so it does not reach crypto today. H.R. 9172, "Applying Existing Tax Anti-Abuse Rules to Digital Assets Act" (Rep. Arrington, dated June 2026, FETCHED text from Ways and Means), would replace "stock or securities" with "specified assets" (any stock/security plus any digital asset except a qualified USD stablecoin), with an effective date of dispositions after the date of introduction, and a broker-basis transition to 2028. Status: referred to committee; I found no sign of enactment, but congress.gov and GovTrack returned 403, so this rests on a search summary (medium confidence). Corroboration: the 2026 Form 1099-DA instructions apply wash-sale reporting (box 1i) only to tokenized securities. Key design risk: the bill's effective date is retroactive to introduction, so a later enactment could catch trades made in the interim.
- **Form 1099-DA.** Brokers report gross proceeds for digital-asset sales from 2025. Cost basis is mandatory only for "covered" assets acquired on or after 2026-01-01 and still held at the same broker; earlier or transferred-in assets are noncovered (Box 9). Box 6 gives short/long-term; box 1i is wash sale for tokenized securities only. Optional aggregate reporting exists for qualifying stablecoins (over $10,000) and NFTs. Taxpayers still answer the Form 1040 digital-asset question and use Form 8949.
- **Securities wash-sale reporting (1099-B).** Brokers must report disallowed losses only for same account and same CUSIP; they may report more. A strategy trading the same ETF across an Alpaca account and any other account must track wash sales itself.
- **Trader status.** A timely mark-to-market (section 475(f)) election makes securities gains and losses ordinary and removes capital-loss limits and wash-sale rules; the election is due by the prior year's return deadline (IRS Topic 429). That page says nothing about crypto, and a trader qualification is a facts test unlikely to be met by a part-time $5,000 account (ESTIMATE of fit, ask a professional).

### 2. After-tax drag: ESTIMATE

**Assumptions (all illustrative).** Pre-tax total return g = 8%/yr for both approaches. Buy-and-hold ETF: 1.5% dividend yield taxed each year at the long-term rate (assumed qualified), the rest deferred and taxed once at the long-term rate at year 10 or 20. Trend strategy: every gain realised within a year, taxed at the short-term (ordinary) rate, tax paid out of the account yearly, losses netted in-year (the $3,000 cap rarely binds at this size and carryforwards are indefinite). No trading costs, no state tax except case D. Single filer. Arithmetic: strategy after-tax return = g x (1 - ST rate); the break-even pre-tax return is B&H after-tax CAGR / (1 - ST rate).

| Case (ST / LT rate) | B&H after-tax CAGR, 10 yr | Strategy at same 8% pre-tax | Gap | Pre-tax return needed to match | Uplift needed |
|---|---|---|---|---|---|
| A: 12% / 0% | 8.00% | 7.04% | 0.96 pp | 9.09% | +1.09 pp |
| B: 22% / 15% | 7.04% | 6.24% | 0.80 pp | 9.03% | +1.03 pp |
| C: 24% / 15% | 7.04% | 6.08% | 0.96 pp | 9.26% | +1.26 pp |
| D: B plus 5% state (27% / 20%) | 6.71% | 5.84% | 0.87 pp | 9.19% | +1.19 pp |
| E: 32% + 3.8% NIIT (35.8% / 18.8%) | 6.79% | 5.14% | 1.65 pp | 10.57% | +2.57 pp |

At 20 years the uplift in B and C rises to +1.26 pp and +1.51 pp (deferral compounds longer). Sensitivity to gross return (case B, 10 yr): g = 4% needs +0.42 pp; g = 15% with no dividends (BTC-like) needs +2.47 pp (case C: +2.93 pp). Rule of thumb: the required uplift is roughly 12-20% of the gross return at mid brackets, so it scales with how good the strategy is.

Dollars: a $5,000 account earning 8% makes $400; short-term tax is $48 (12%), $88 (22%), $96 (24%) or about $143 (35.8%) a year, against $60 if the same gain were long-term at 15%. The dollar amounts are small, but the percentage hurdle is not.

Costs stack on top. Per brief 11, Alpaca crypto is 0.50% as a taker round trip; at an assumed 10 round trips a year that is 5.0% of capital (ESTIMATE, 10 x 0.50%), several times the tax gap. ETF round trips at about 0.03-0.10% add little. Wash sales cost little in tax terms (deferral, not loss) but a monthly trend system that exits at a loss and re-enters the same ETF inside 30 days will generate many disallowed losses, which tracking and Form 8949 must handle.

### 3. Automated trading inside an IRA

- **Alpaca.** Trading API IRAs (Traditional and Roth) were announced 2026-05-13 (updated 2026-07-06) for US tax residents with an SSN (disclosure page) or SSN/ITIN (blog); you need an existing trading account first; equities and options are named; algorithmic trading via the same API is the stated purpose (FETCHED). Alpaca's support pages say IRAs trade on limited margin with shorting disabled and, as of September 2024, no crypto (FETCHED; the crypto page is dated 2024 and may have changed, medium confidence). Alpaca's account-plans docs page still says "we do not support retirement accounts," which contradicts the blog and is probably stale. IRA fees: not found for Trading API users (the retrieved fee schedule has no IRA section); a Broker API support article mentions annual maintenance fees (UNVERIFIED for individuals).
- **Interactive Brokers.** IRAs are available and the TWS API sees the same restrictions as the platform: no short selling, no borrowing or debit balances, no MLPs (search-result summaries of IBKR knowledge-base and API pages; every ibkr.info / interactivebrokers.com page returned 403, so RECALLED/medium). Cash-type IRAs cannot short; a "Margin IRA" allows unsettled-funds trading but never borrowing. IBKR crypto: not established for IRAs.
- **Public.** Its API page says trading works "through cash, margin, or IRA accounts" across stocks, ETFs, options and crypto, and Public launched crypto in Traditional and Roth IRAs on 2026-03-25 (press release; no custodian or API detail; a search summary names Alto as custodian of crypto IRAs). Whether API orders can reach crypto inside an IRA is UNVERIFIED. This is the only mainstream route I found where crypto in an IRA might be API-reachable; it would need a test.
- **Others.** Schwab Trader API, tastytrade API and TradeStation API: IRA support via API not confirmed in any source I could open (Schwab and TradeStation pages blocked); UNVERIFIED.
- **Generic IRA mechanics.** Limited margin in an IRA allows trading on unsettled funds but not borrowing or shorting (Fidelity explainer, FETCHED). 2026 IRA contribution limit is $7,500 ($1,100 catch-up at 50+); Roth phase-out for singles $153,000-$168,000 (IRS release, FETCHED). Early withdrawals before 59 1/2 carry a 10% additional tax with listed exceptions (IRS Topic 557). Roth contribution withdrawal and earned-income requirements are RECALLED and not verified here.

## What this decides for the JARVIS design

1. **The benchmark must be after-tax and account-matched.** In a taxable account, a short-term-gain strategy must beat buy-and-hold by roughly +1.0 to +1.5 pp a year before costs at an 8% gross return (up to +2.6 pp in the top case; ESTIMATE). Add per-trade costs and any IRA fee. This should be written into the cost gate as a "tax hurdle" parameter by bracket.
2. **Run the equity/ETF trend and momentum sleeve in an Alpaca Roth or Traditional IRA if it can be funded.** There the tax gap disappears (Roth: tax-free; Traditional: both approaches deferred). JARVIS is already long/flat with a leverage cap of 1.0, so the IRA bans on shorting and borrowing cost nothing. Caps: $7,500 a year of new contributions (2026), and money is locked up until 59 1/2 for practical purposes, which matters if the owner may need the $1,000-$10,000.
3. **The crypto sleeve stays taxable (at Alpaca) or becomes a spot-ETF sleeve inside the IRA.** Alpaca IRAs show no crypto. Short-term crypto trading in a taxable account faces the largest hurdle (about +2.5-2.9 pp for tax plus about 0.50% per round trip). Buy-and-hold BTC in a taxable account defers tax. Do not build crypto tax-loss harvesting on the assumption that wash sales never apply; H.R. 9172 is retroactive to introduction if enacted.
4. **Cross-account wash-sale guard.** If JARVIS trades an ETF in the IRA, the owner's taxable account must not hold or trade the same ETF within 30 days of a taxable loss (Rev. Rul. 2008-5 makes the loss permanently non-deductible).
5. **Ledger fields.** Add lot ID, acquisition date, holding-period flag (days to long-term), account type, wash-sale flag, and 1099 reconciliation fields; add a deterministic "tax-lot" check before exits in taxable accounts (for example, flag positions within a few weeks of the one-year mark).
6. **Dollar scale.** At $1,000-$10,000, tax dollars are small (tens to low hundreds) but the 1.0-1.5 pp hurdle comes on top of costs that are already 600x-monthly-bill constrained (brief 11). A fixed IRA fee of $10 a year would itself be 1.0% of $1,000 or 0.1% of $10,000 (arithmetic), so confirm Alpaca's IRA fee before committing.

## Open uncertainties

- Alpaca IRA fees, crypto status in 2026, and whether paper trading supports IRA-style rules are unverified; docs pages contradict each other.
- IBKR IRA restrictions come from search summaries, not opened primary pages (403).
- H.R. 9172 status: no enactment found, from a search summary and the bill text, not congress.gov.
- 2026 long-term capital-gain thresholds are from secondary sources.
- The 8% gross return, 1.5% yield, 100% short-term realisation and in-year loss netting are illustrative; a strategy that holds some winners over a year, or loses money in some years, will differ. The model ignores the wash-sale deferral timing, qualified-dividend holding periods, and estimated-tax penalties.
- Public API crypto-in-IRA, and API IRA support at Schwab, tastytrade and TradeStation, are unverified.
- Alpaca's tax-lot method and 1099 formats were not checked.

### Questions for a tax professional

1. Which of the owner's income and filing facts decide the real bracket for short-term and long-term gains, state tax included?
2. Is the owner eligible for a Roth or deductible Traditional IRA (earned income, workplace plan, phase-outs), and how does the $7,500 limit interact with existing IRAs?
3. How should wash sales be tracked across a taxable account, an IRA and a spouse's accounts, given brokers report only same-account, same-CUSIP?
4. Could crypto wash-sale legislation apply retroactively to dispositions already made, and should loss harvesting wait?
5. Would a section 475(f) election be available or sensible, and does it apply to crypto?
6. Which lot-matching method should be elected, and how are 1099-DA noncovered lots handled for transfers in?
7. How should estimated tax payments be set when short-term gains are realised unevenly?
8. Does options trading in an IRA (named by Alpaca) raise any prohibited-transaction or UBTI issues?

## Source list

- IRS Topic 409, Capital gains and losses. https://www.irs.gov/taxtopics/tc409 (FETCHED, high)
- IRS Topic 429, Traders in securities. https://www.irs.gov/taxtopics/tc429 (FETCHED, high)
- IRS Topic 557, Additional tax on early distributions. https://www.irs.gov/taxtopics/tc557 (FETCHED, high)
- IRS Publication 550 (2025). https://www.irs.gov/publications/p550 (FETCHED via summarizer, medium)
- IRS Rev. Rul. 2008-5, IRB 2008-03. https://www.irs.gov/irb/2008-03_IRB (FETCHED, high)
- IRS 2026 inflation adjustments release. https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill (FETCHED, high for ordinary brackets)
- IRS 2026 IRA limits release. https://www.irs.gov/newsroom/401k-limit-increases-to-24500-for-2026-ira-limit-increases-to-7500 (FETCHED, high)
- IRS digital assets page. https://www.irs.gov/filing/digital-assets (FETCHED, high)
- Instructions for Form 1099-DA. https://www.irs.gov/instructions/i1099da (FETCHED, high)
- Instructions for Form 1099-B. https://www.irs.gov/instructions/i1099b (FETCHED, high)
- H.R. 9172 text. https://waysandmeans.house.gov/wp-content/uploads/2026/06/H.R.-9172.pdf (FETCHED, high for text; status medium)
- Alpaca IRA blog (Trading API). https://alpaca.markets/blog/alpaca-introduces-individual-retirement-accounts-for-trading-api-users/ (FETCHED, high)
- Alpaca Trading API page. https://alpaca.markets/trading-api (FETCHED, medium)
- Alpaca support: IRA crypto. https://alpaca.markets/support/can-ira-trade-crypto (FETCHED, medium; dated 2024)
- Alpaca support: IRA margin/short. https://alpaca.markets/support/can-ira-trade-on-margin-short (FETCHED, medium)
- Alpaca account plans (appears stale). https://docs.alpaca.markets/docs/account-plans (FETCHED, low)
- Alpaca Broker API IRA blog. https://alpaca.markets/blog/ira-accounts-now-available-through-alpacas-broker-api/ (FETCHED, medium)
- Alpaca fee schedule. https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf (FETCHED; no IRA section)
- Interactive Brokers TWS API limitations and IRA knowledge base (search results only; fetch 403). https://www.interactivebrokers.com/docs/tws-api/doc/notes-limitations/tws-api-limitations (RECALLED, medium)
- Public API pages. https://www.public.com/api and https://public.com/get/api3-now (FETCHED, medium)
- Public crypto-in-IRA press release (2026-03-25). https://www.aap.com.au/aapreleases/cision20260324ae18114/ (FETCHED, medium)
- Fidelity, limited margin in an IRA. https://www.fidelity.com/learning-center/trading-investing/trading/limited-margin-trading-IRA (FETCHED, medium)
- 2026 long-term gain thresholds, secondary: https://www.kiplinger.com/taxes/irs-updates-capital-gains-tax-thresholds (search result only, low-medium)


## Independent verification (2026-10-01)

**Confirmed (re-fetched or re-derived)**
- All table arithmetic in section 2 recomputed (B&H with dividends taxed yearly, reinvested dividends added to basis, deferred gain taxed once): 10-yr B&H CAGR 8.00 / 7.04 / 7.04 / 6.71 / 6.79 percent; strategy 7.04 / 6.24 / 6.08 / 5.84 / 5.14; break-evens 9.09 / 9.03 / 9.26 / 9.19 / 10.57; 20-yr uplift for B and C 1.26 / 1.51 pp. Dollar figures ($48, $88, $96, about $143, $60) also correct. Note the B&H figures hold only if reinvested dividends are added to basis; ignoring that step gives about 0.15 pp lower B&H and a slightly smaller hurdle.
- IRS Topic 409 holding period, $3,000 loss limit, 2025 thresholds ($48,350). https://www.irs.gov/taxtopics/tc409
- 2026 ordinary brackets and $16,100 standard deduction. https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill
- 2026 IRA limit $7,500, catch-up $1,100, Roth single phase-out $153,000-$168,000. https://www.irs.gov/newsroom/401k-limit-increases-to-24500-for-2026-ira-limit-increases-to-7500
- Rev. Rul. 2008-5 holding (loss disallowed, no IRA basis increase). https://www.irs.gov/irb/2008-03_IRB
- Form 1099-DA: gross proceeds for sales after 2025; box 1i wash-sale only for tokenized securities; $10,000 stablecoin threshold. https://www.irs.gov/instructions/i1099da
- Alpaca IRA announcement (2026-05-13, Roth and Traditional, SSN/ITIN, equities and options, no fee or crypto info). https://alpaca.markets/blog/alpaca-introduces-individual-retirement-accounts-for-trading-api-users/
- Alpaca support page still says IRA crypto unsupported as of September 2024. https://alpaca.markets/support/can-ira-trade-crypto
- H.R. 9172 introduced 2026-06-08, referred to Ways and Means, pending (search results, not congress.gov). 
- Alpaca crypto base tier is 0.15% maker / 0.25% taker per side, so 0.50% taker round trip is correct. https://docs.alpaca.markets/docs/crypto-fees

**Corrected / weakened**
- 2026 LT thresholds ($49,450 / $545,500): search results attribute them to Rev. Proc. 2025-32; still not read in the primary PDF. Keep as medium confidence.
- The crypto cost example in section 2 uses the taker rate; a maker-limit approach is 0.30% round trip at the base tier, so the 5.0% (10 round trips) is a worst case, not typical.
- "Alpaca IRAs show no crypto" rests on a 2024 page; the July 2026 blog is silent. Treat as "not offered as far as documented," and test before relying on it.

**Unverifiable**
- H.R. 9172 effective date (retroactive to introduction) and 2028 broker transition: both bill PDFs returned unreadable binary; congress.gov not opened. Design for the risk, but do not state it as confirmed.
- IBKR, Schwab, tastytrade, TradeStation, Public API IRA behaviour; Alpaca IRA fees (disclosure page and fee schedule give none); Roth withdrawal rules.

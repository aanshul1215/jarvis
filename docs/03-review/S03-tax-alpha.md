# S03 Tax alpha review (2026-10-02)

Not tax advice. Every item marked "TAX PRO" needs a CPA or enrolled agent before real money moves.

## Bottom line

1. **Do not build a live tax-loss-harvesting (TLH) executor in v1.** At $1,000-$10,000 across six ETFs the benefit is about $0-$21 a year (ESTIMATE below), against wash-sale risk and about 5-8 dev-days.
2. **The big, certain lever is where the money sits.** An IRA or Roth removes the satellite's tax hurdle (design section 1: -$14 to -$18 a year taxable, about -$1 in an IRA) and the yield tax on the core. ESTIMATE: about $29-$60 a year at $10,000, at zero build cost.
3. **Two design facts need correcting.** Alpaca appears FIFO-only with no lot selection, which undermines the sleeve-lot tax model and the 1.0-1.3 point hurdle. The "commodities/gold" slot can carry a 28% collectibles rate.

## What the design gets right (with evidence)

- **Tax is a hurdle, not an afterthought** (sections 1, 7 G1b). Short-term means one year or less and is taxed as ordinary income (IRS Topic 409, FETCHED).
- **The cross-account wash-sale guard is correct, including the IRA leg** (section 6). Pub. 550 treats purchases by an IRA, spouse or controlled entity as yours (FETCHED, summarised). Under Rev. Rul. 2008-5 an IRA purchase in the window kills the loss for good, with no IRA basis increase (FETCHED).
- **"One account type, or disjoint tickers"** (section 4) follows directly from Rev. Rul. 2008-5.
- **Low-turnover S0 with bands and contribution-driven rebalancing** (section 4). Berkin and Ye found steady contributions sustain harvest value (FETCHED, abstract). Doing little is the right default.
- **The 30-day short-to-long deferral check** (section 2 step 9) fits Topic 409.
- **Broker-lot-method awareness** (section 4); see P4.
- **The satellite-in-IRA unlock** (section 12) needs no shorting. Alpaca offers API trading in Traditional and Roth IRAs (FETCHED, 2026-05-13 post).
- **A paid tax consult before L0** (O4); see P8.

## The evidence on harvesting

| Source | What it measured | Result | Fit to JARVIS |
|---|---|---|---|
| Chaudhuri, Burnham & Lo, FAJ 2020 (FETCHED: abstract pages; PDF gave HTTP 405) | Top-500 US stocks (CRSP), 1926-2018, long-only, 15% long-term and 35% short-term rates | 1.08%/yr before costs; 0.82% with the wash-sale rule; 0.95% after a 13 bp cost (unconstrained case). Eras range 0.51%-2.13%. A secondary summary quotes 1.10 and 0.85 (likely an earlier version) | **Upper bound.** Needs many stocks with dispersion; six ETFs have far less |
| Berkin & Ye, FAJ 2003 (FETCHED: abstract) | Monte Carlo, harvesting plus HIFO | About 40 bp/yr. Stock-specific risk and contributions help; benefit roughly linear in rate | HIFO needs lot choice (P4) |
| Gaige et al., FPA Journal 2022 (FETCHED) | Direct indexing | Recommends 60-100 stocks; wash-sale drag 26 bp | Confirms a breadth requirement |
| FPA Journal 2014, HIFO (FETCHED) | HIFO vs average cost | 0.5-1.0% of terminal wealth, lifetime | Not annual |
| CFA Enterprising Investor 2018 (FETCHED, commentary) | Critique | Much of the gain is **deferral** (basis falls); can backfire if rates rise | Warns against over-claiming |

**ESTIMATE of ETF-level TLH value for this owner (arithmetic)**
- Start from 0.82% minus 0.13% costs = 0.69% (assumes additivity).
- Scale by (short-term minus long-term rate) / (35 minus 15), a rough heuristic: Case A (12%/0%) 12/20 = 0.60, so 0.41%; Case B (22%/15%) 7/20 = 0.35, so 0.24%; Case C (24%/15%) 9/20 = 0.45, so 0.31%.
- Apply a dispersion haircut of 0.25-0.50 for six ETFs against 500 stocks (**my judgement, UNVERIFIED**). Result: 0.06-0.21% a year.
- Dollars: $1,000 gives $0.60-$2; $5,000 gives $3-$10; $10,000 gives $6-$21. With no haircut the ceiling is 0.41% x $10,000 = $41.
- Swap cost: 4 legs x 5 bp = 20 bp of notional. A harvest of loss fraction x pays if 0.07x >= 0.002 (permanent part, case B), so x >= 2.9%; on the deferral view 0.22x >= 0.002, so x >= 0.9%. Most of the benefit is deferral and reverses when the lower basis is sold.

**Wash-sale mechanics to encode:**
1. The window is 61 days (30 before, the sale day, 30 after).
2. A disallowed loss is added to the replacement basis, and the holding period carries over (Pub. 550, FETCHED). Partial overlaps disallow only the overlapping shares.
3. An IRA purchase kills the loss permanently (Rev. Rul. 2008-5).
4. Brokers report only same-account, same-CUSIP wash sales (brief 19), so JARVIS tracks the rest.
5. For ETF pairs, "substantially identical" is a facts test. Pub. 550 as summarised gave no ETF definition, and secondary web pages say the IRS has issued none (UNVERIFIED). TAX PRO.

## What should improve

### S03-P1 (must). Replace the TLH executor with a shadow "harvest counter"; build the executor only if it earns its way
- **Design section:** 2 step 9 (tax-lot check, wash-sale guard), 6 (gate), 11 P2/P3.
- **Change:** No harvest executor. Add one event type, `harvest_candidate`, to the P2 lot-level tax simulator: a position whose FIFO-realisable loss is at least 5% and $50, with the 61-day window, a pair table and a swap-back at least 31 days later. The monthly RECOMMEND email lists candidates with dollars and cost; the owner decides. Pre-register the build trigger: two years of shadow showing at least 0.30% of capital a year after costs.
- **Why:** ESTIMATE $0-$21 a year; FIFO may make most candidates unharvestable (P4).
- **Cost:** $0 a month, no LLM. **Effort:** +2 dev-days in P2; avoids about 5-8 dev-days (ESTIMATE).
- **Risk:** forgoes a deep-drawdown windfall (a 15% drop on $4,000 of risk assets harvested at 22% saves about $132, ESTIMATE: 4,000 x 0.15 x 0.22).
- **Owner constraints:** respected.

### S03-P2 (must). Make account location a pre-registered rule with dollar figures
- **Design section:** 4 (account layout), 9 (Mission Plan), 12 (IRA unlock), O3.
- **Change:** Fix the priority order now. (1) Roth if eligible, else Traditional IRA subject to a fee cap; the satellite goes first. (2) Then the most heavily taxed assets (Treasury and T-bill ETFs, REIT), then equity ETFs. (3) Taxable holds the remainder as S0 only, with no harvesting.
- **Why:** Dammon, Spatt & Zhang (J. Finance 2004) find heavily taxed assets belong in the tax-deferred account (FETCHED via Spatt's SEC speech and an HBS summary; paper not opened). Roth contributions can be withdrawn any time without tax or penalty (Pub. 590-B, FETCHED, summarised).
- **Dollar ESTIMATE**, with ILLUSTRATIVE yields (US equity 1.3%, ex-US 3.0%, Treasuries 4.0%, REIT 3.8%, gold 0%):
  - Ordinary part 0.2 x (4.0 + 3.8) = 1.56%; qualified part 0.2 x (1.3 + 3.0) = 0.86%.
  - Case B drag 1.56 x 0.22 + 0.86 x 0.15 = 0.47% of the core; Case A 0.19%; Case C 0.50%.
  - At $10,000: core $8,750 gives $17-$44; satellite hurdle removed $13-$16 (1,250 x 1.0-1.3%). Total about $29-$60 a year; at $1,000 about $3-$6.
  - P0 replaces the yields with issuers' published figures.
- **Cost:** $0. **Effort:** 1-2 dev-days (a small allocator in the Mission Plan code); it also removes cross-account complexity if everything fits one IRA.
- **Risk:** the cap is $7,500 a year (FETCHED, 2026); the Alpaca IRA fee is unknown ($10 is 1% of $1,000); earnings are locked until 59½; IRA limited-margin and unsettled-funds rules may affect sells-then-buys sequencing, so G3/L0 re-run for the IRA; Roth eligibility rules (RECALLED).
- **Owner constraints:** respected.

### S03-P3 (must). Add a tax-character screen to the universe choice
- **Design section:** 4 (universe fixed at G0), 5.
- **Change:** Each candidate ETF gets `tax_character` and `K1` fields, set at G0. A physically backed gold trust is treated as the investor owning collectibles, so gains face a maximum 28% rate (IRS Chief Counsel memo, file pmta01809, FETCHED; non-precedential, undated in the excerpt). Futures-based commodity funds may issue a K-1 (general knowledge, UNVERIFIED; check each prospectus). Rule: the tax-lot check defers taxable S0 band sales of a collectibles-rate ETF; reject K-1 funds in a taxable account.
- **Why:** Section 4 names "commodities/gold" without a tax class, and the tax-lot check only looks at the holding period.
- **Cost:** $0. **Effort:** +0.5 dev-day. **Risk:** gold has no yield, so it ranks last for IRA space under P2 even though its sale rate is worst; the tradeoff is a TAX PRO question.

### S03-P4 (should). Model Alpaca's FIFO, and replace the planning hurdle with a simulated one
- **Design section:** 1 (H = 1.0-1.3), 4 (sleeve lots), 7 G1b, P0 (lot-method probe).
- **Change:** The lot method is a P0 probe; the simulator defaults to FIFO with no HIFO credit; H becomes a simulator output, not an input.
- **Why:** Alpaca staff say FIFO is the default and lot selection is unsupported (FETCHED; forum post, not official docs; may have changed). Pub. 550 allows specific identification only with a written broker instruction at sale (FETCHED, summarised). Under FIFO, an S-A exit sells the account's oldest lots, probably S0's long-term lots, so the short-term share of S-A gains can sit well below brief 19's 100%, pushing H toward brief 18's 0-0.9 range. The same sale also realises S0's deferred gain, which the sleeve model hides. An S0 contribution buy within 30 days of an S-A loss exit can disallow that loss; same-day netting (section 4) reduces but does not remove this.
- **Cost:** $0. **Effort:** about +1 dev-day (simulator already planned). **Risk:** a lower H weakens the case for putting S-A in an IRA, but the yield-drag argument in P2 still holds.

### S03-P5 (should). Widen and harden the wash-sale guard
- **Design section:** 6 (wash-sale guard), `external_trades`.
- **Change:** Register spouse accounts, dividend reinvestments and any 401(k) or payroll purchases of overlapping index funds. Treat same-underlying ETFs as substantially identical by default (gold trusts from different issuers are the clearest case). A TAX PRO approves the pair table once. Block rather than warn.
- **Why:** Pub. 550 names spouse and controlled-entity purchases (FETCHED, summarised). Whether 401(k) buys trigger the rule is UNVERIFIED, so assume yes.
- **Cost:** $0. **Effort:** +1 dev-day. **Risk:** a few more deferred loss sales, trivial at this size.

### S03-P6 (should). Define a contribution waterfall for tax-aware rebalancing
- **Design section:** 2 steps 7-9, 4 (S0 bands).
- **Change:** Direct new cash, dividends and interest to the most underweight ETF first. Sell only on a band breach that cash flow cannot fix within one decision window. Never sell inside 30 days of a lot turning long-term (already in the design). Trim a non-collectibles ETF before selling gold at a gain.
- **Why:** Berkin and Ye on contributions (FETCHED, abstract).
- **Cost:** $0. **Effort:** +1 dev-day. **Risk:** drift persists a few weeks longer.

### S03-P7 (should). If no IRA is possible, run S-A in shadow only
- **Design section:** 7 (G4/G5), 11 (P5-P6), 12.
- **Change:** If the O3 tree fails (ineligible or needs liquidity), S-A never goes live. S0 plus the dial b runs live and S-A stays in shadow, scored after tax.
- **Why:** Taxable expected effect at G4 is -$14 to -$18 a year (design section 1) and cannot be tested statistically (G1b). The IRA figure is about -$1.
- **Cost:** $0. **Effort:** saves an unquantified part of P5's 12-20 dev-days (ESTIMATE). **Risk:** no live satellite drawdown behaviour.

### S03-P8 (could). A tax-professional packet, and tax defects in the Red-Team set
- **Design section:** 3 (20 seeded defects), 15 (O4).
- **Change:** Package the questions below once, before L0. Add three tax defects to the seeded set: a wash sale through the IRA, a FIFO lot mismatch, a spouse purchase.
- **Cost:** about $0.10 of Red-Team budget; the consult is a paid professional, a real owner cost outside the LLM budget. **Effort:** 0.5 dev-day. **Risk:** low.

**Questions for a TAX PRO:**
1. The owner's real brackets and eligibility for Roth versus Traditional.
2. Whether different-issuer ETFs on one index, or on different but correlated indexes, are "substantially identical".
3. Whether payroll 401(k) purchases create wash sales.
4. The FIFO-only workaround and reporting versus the 1099-B.
5. The collectibles rate for gold trusts, and whether to hold them in the IRA.
6. Which K-1 or foreign-fund rules apply to any commodity ETF.

## What I could not verify

- The Chaudhuri, Burnham and Lo full text (HTTP 405). Period results and the 13 bp cost come from a summary page.
- Dammon, Spatt and Zhang directly; the secondary sources give no dollar effects.
- The Vanguard TLH paper (unreadable binary).
- Alpaca IRA fees and settlement rules, and whether lot selection changed after October 2025.
- Any IRS statement on ETF pairs, and whether 401(k) buys count under section 1091.
- Roth earned-income and contribution-deadline rules (RECALLED).
- The 0.25-0.50 dispersion haircut, the ETF yields and the 5 bp leg cost are assumptions.
- Texas has no personal income tax: seen only in search summaries of Comptroller pages (medium).

## References

- Chaudhuri, Burnham, Lo (2020), FAJ 76(3), 99-108. rpc.cfainstitute.org/research/financial-analysts-journal/2020/empirical-evaluation-tax-loss-harvesting-alpha; dspace.mit.edu/handle/1721.1/135992. **FETCHED (abstract pages only)**
- Berkin & Ye (2003), FAJ 59(4), 91-102. ideas.repec.org/a/taf/ufajxx/v59y2003i4p91-102.html. **FETCHED (abstract)**
- Dammon, Spatt & Zhang (2004), J. Finance 59(3), 999-1037. Via sec.gov/news/speech/spch010705cs.htm and library.hbs.edu/working-knowledge/the-best-place-for-retirement-funds. **FETCHED (secondary)**; the paper itself RECALLED
- Sialm & Sosner (2018), FAJ 74(1), on taxes and shorting. **FETCHED (abstract)**; not relevant to a long/flat book
- Gaige et al. (2022) and the 2014 HIFO article, both FPA Journal; CFA Enterprising Investor (2018) commentary. All **FETCHED**
- IRS Pub. 550; Rev. Rul. 2008-5 (irs.gov/irb/2008-03_IRB); Topic 409; Topic 559; Pub. 590-B; 2026 inflation-adjustments release. All **FETCHED** (Pub. 550 and 590-B summarised)
- IRS Chief Counsel memo on physical-metal ETFs, irs.gov/pub/lanoa/pmta01809_7431.pdf. **FETCHED (non-precedential)**
- Alpaca IRA post (alpaca.markets/blog/alpaca-introduces-individual-retirement-accounts-for-trading-api-users/); Alpaca IRA margin/short support page; Alpaca forum staff reply on FIFO (forum.alpaca.markets, 2025-10-30). **FETCHED** (forum is not official docs)
- Vanguard TLH personalised-approach PDF. **UNREAD (binary)**
- Constantinides (1983), Econometrica, tax timing option. **RECALLED**

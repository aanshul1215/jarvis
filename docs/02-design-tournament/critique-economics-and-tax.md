# Critique through the lens of economics and tax

Critic: economics-and-tax. Date: 2026-10-01. Evidence used: briefs 11, 19, 22 (read in full), brief 18 (cost and tax lines), brief 20 (G4 sizing), brief 21 (fractional orders), brief 23 (hosting costs), brief 06 (Tiingo/Norgate), 00 and 00b. Anything marked ESTIMATE is my own arithmetic from those briefs. Anything marked "not in briefs" is general knowledge and should be checked.

Question asked: total monthly cost (data, LLM, hosting) against $1k-$10k capital; fee and tax drag against the benchmark; is the budget claim real?

## 0. Headline findings

1. **Direct cash costs are small and mostly honest.** Data is $0 in every proposal (Alpaca Basic, Tiingo Starter, EDGAR, ALFRED; briefs 06, 21). Hosting is $0 (laptop plus free Healthchecks; e2-micro as fallback; brief 23). Production LLM is $0 to about $10 a month and is capital-gated in all five. The "close to zero" budget is met on those terms.
2. **Every "$0 extra" for the research, builder and review agents silently assumes the owner already pays for a Claude plan.** If he does not, those agents cost about $12.8 a month (Sonnet weekly session) to $21.3 (Opus weekly session) on the API (brief 22, verified figures), and the build phase costs more. Nobody establishes whether the plan exists. B, C, D and E say "$0 extra on Pro". A says the same for its Lab.
3. **The recurring spend is small against capital but large against the edge.** Strategy A is expected at -1 to +1 point a year against holding the same assets (brief 18). Brief 11's "2% drag" rule is a rule about capital, not about edge. A $48 a year extractor is 0.5% of $10k, which is half of the best-case pre-tax edge. At $1,000 the dollars are trivial either way: 1 point is $10.
4. **After tax, in a taxable account, the launch strategy is expected to lose to the benchmark.** Brief 19 puts the tax hurdle at about +1.0 to +1.3 points a year (cases B and C, 100% short-term, 8% gross); brief 18 says the true gap is 0 to 0.9. Against a -1 to +1 pre-tax edge, the central after-tax result is about -0.7 points before running costs. Only an IRA removes that. Only B puts an after-tax test in G1, and only B and D settle the account-type question in P0.
5. **No proposal has a fatal economic flaw.** Every one falls back to "hold the benchmark" if G1 fails. The serious flaws are about gates that cannot enforce after-tax outperformance, plan dependence hidden in a "$0" headline, whole-share arithmetic at $1,000, and micro-live sized in dollars.

## 1. Consolidated cost and drag table (ESTIMATE)

Production API only (the owner's Claude plan, if any, is extra). Power on the owner's laptop is $2.64 a month (brief 23, assumes 20 W always on; the wattage is an assumption).

| Item | A | B | C | D | E |
|---|---|---|---|---|---|
| Data | $0 | $0 | $0 | $0 | $0 |
| Hosting | $0 (+$2.64 power, stated) | $0 (+$2.64 power, stated) | $0 (power not stated) | $0 (power not stated) | $0 now; VM $4-6 at S3 |
| Production LLM at $1,000 | $0.65 (Narrator) = 0.78% a year | $0 | about $1 = 1.2% | Narrator only $0.65; cap $1.67 = 2.0% | $0.65 = 0.78% |
| Production LLM from about $2,400-3,000 | $4.55 = 2.3% at $2,400 | $4 = 1.9% at $2,500 | $5 = 2.0% at $3,000 | up to cap $4 at $2,400 | $0.5-4 |
| At $10,000 | $4.55 to about $10.5 = 0.55-1.3% | $4-9.4 = 0.5-1.1% | $5 = 0.6% | cap $15 = 1.8% (actual lower) | $0.5-9.4 |
| Plan-dependent roles | Lab, Goal Interpreter | Builder, Weekly Reviewer, Researcher | 5 of 9 agents | Lab, Change Reviewer, (Red-Team, Incident) | Lab, Builder |
| API cost of those roles if no plan | about $13 a month | about $13-22 | about $35-50 (my sum of Opus weekly, subagent, Opus red-team per package, Q&A) | about $13 | about $13 |

Launch strategy A against an after-tax buy-and-hold, central case, Texas (no state income tax: general knowledge, not in the briefs; it removes brief 19's case D):

| Capital | Pre-tax edge (central) | Tax hurdle | Trading cost | Production LLM (lean proposal / richest) | Net, taxable | Net, in an IRA |
|---|---|---|---|---|---|---|
| $1,000 | 0 | -0.65 (range 0 to -1.3) | -0.09 (brief 18: 0.03-0.14) | -0 / -0.78 | -0.74 to -1.5 points = -$7 to -$15 a year | -0.09 to -0.87 |
| $5,000 | 0 | -0.65 | -0.09 | -0 / -1.09 | -0.74 to -1.83 = -$37 to -$91 | -0.09 to -1.18 |
| $10,000 | 0 | -0.65 | -0.09 | -0 / -0.55 | -0.74 to -1.29 = -$74 to -$129 | -0.09 to -0.64 |

Best case (+1 point pre-tax, no tax drag) is about +0.9 points. The worst case (-1 pre-tax, 1.3 tax) is about -2.4. Power ($32 a year) would add 3.2% of $1,000, 0.64% of $5,000 and 0.32% of $10,000. That is, power is the largest fixed cost at $1,000, and only A and B state it.

Crypto sleeve B, taxable: costs 0.7-1.2% a year (brief 18, corrected) plus a tax hurdle of +2.5 to +2.9 points at BTC-like 15% gross (brief 19) gives about 3.2-4.1 points of sleeve value a year over after-tax BTC buy-and-hold. The sleeve is $100 at 10% of $1,000 and $2,000 at 20% of $10,000, so the hurdle is about $3-4 to $65-80 a year. Brief 18 says B's value is avoiding >80% drawdowns and that it likely lags BTC buy-and-hold in bull runs. It cannot clear that hurdle in a taxable account on return alone. Alpaca IRAs show no crypto (brief 19, 2024 page, treat as unverified).

## 2. Proposal A, vision-faithful

**What it gets right.** It costs power ($2.64). It gates the extractor at capital of at least $2,400 and runs only the Narrator below that (section 3, "below $2,400 only the Narrator runs"), which matches brief 11's 2% rule and brief 22's b1. Its arithmetic checks ($48 a year = 4.8% of $1,000; $2,400 and $5,600 triggers). Its fallback is stated: "run the benchmark with JARVIS as its risk and audit layer" (section 13, risk 2). Crypto is capped at 10% at launch.

**Serious flaws**
- **No after-tax test in the gate.** Section 4 and section 1 promise comparison "after cost and tax in the same account type", but section 7's G1 list (DSR, plateau, holdout, 5-year windows, costs x2) contains no after-tax or benchmark criterion. A strategy can pass G1 and still be expected to lose after tax. Brief 19: a +1.0 to +1.3 point hurdle against a -1 to +1 edge (brief 18). B's G1 has the missing line.
- **The IRA decision is deferred to the growth path.** Section 12: "IRA confirmed with acceptable fees: move sleeve A there (brief 19, unverified)". Brief 19 says this is the single largest lever, larger than the whole expected pre-tax edge. It cannot be moved later without a taxable sale, and an IRA can only be funded with new contributions (limit $7,500 for 2026; money locked to 59 1/2). The account type must be decided before G4 and checked in P0. A's P0 does not list it.
- **The extractor spends real money on output nobody can use.** The News and Event Analyst (about $3.40 a month) runs over a "20-symbol watchlist" (section 4, universe plus owner single names such as TSLA), but its output has zero weight at launch and may never earn any (brief 22: models retire about yearly and the forward-evidence clock restarts; gap analysis section 2). Since all text can be archived raw with `first_seen_at` for $0, extraction can be run later in one batch on the archive. Nightly extraction from $2,400 is a 2% drag on a strategy with about 0 expected edge.
- **"$0 extra on Pro" for the Lab.** Section 3 notes about $13 on the API. That would push the total to about $17-18 a month, above A's own $15 cap, if the owner has no plan. A never says what happens in that case (it does say the Lab as an API routine waits for a budget of at least $25).
- **Micro-live in dollars.** G4 is "$500-1,000" (section 7). At $1,000 capital that is the whole account; brief 20 defines it as 5-10% of intended capital.

**Minor.** Total of $4.55 at $2,400 is 2.3%, not under 2% (the 600x rule gives $2,730). Red-Team per position change is fine at under $0.50.

**Verdict.** Spend discipline is good; tax discipline is weak. No fatal flaw. Score 5.5.

## 3. Proposal B, evidence-minimal

**What it gets right.** Production LLM is $0 until capital is at least $2,500 (section 12), with a $5 workspace limit. The daily email is templated, so there is no Narrator cost. The crypto sleeve is "Off" in the $1,000 column of the risk table. It is the only proposal with an after-tax benchmark gate in G1: "after-tax CAGR within 1 point of Strategy 0 and max drawdown at most 0.7x" (section 7). IRA eligibility and fee are P0 items (section 11, P0). It states the power cost. The only recurring-spend rule is capital at least 600 times the monthly cost, applied consistently (section 12).

**Serious flaws**
- **"Monthly cost: $0 for data and LLM" (section 8) is true only with an existing plan.** The Builder, Weekly Reviewer (R1) and Researcher (R2) all depend on one. Brief 22: R1 weekly on the API is about $12.8 a month; Pro is about $17-20. With no plan the true running cost is $13-21 a month, plus $2.64 power. That is 1.9-2.8% of $10,000 and 19-28% of $1,000. B's own table says "otherwise about $20 (Pro) or about $3 per session", but the headline hides it.
- **Whole-share-only at $1,000 is expensive.** Section 6: "Positions are whole shares only, so every overnight position can carry a resting stop." Section 4: four assets at $1,000, rounding "under 10% of each target weight". With a sleeve of $200-250, a rounding error of half a share stays under 10% only if the share price is about $40 or less. That is my arithmetic, and ETF prices are not in the briefs. If the funds cost about $100 a share (assumed), up to 20-25% of each sleeve is mis-sized, and the leftover goes to the T-bill ETF. At an assumed 3-4.5% equity premium that is roughly 0.3-0.9 points a year of cash drag (ESTIMATE), the size of the whole expected edge. It also forces the universe to be picked by share price rather than cost and liquidity. Brief 21 offers the other option: accept process-dependent exits for fractional positions, which A, C and E take.
- **The benchmark is mis-specified for a risk-reduction product.** Strategy 0 is "rebalanced quarterly" (section 4). In a taxable account, quarterly rebalancing of a static mix realises gains, so the benchmark carries tax drag that the true alternative (buy and hold, rebalance with new cash) does not. And "max drawdown at most 0.7x Strategy 0" compares against a fully invested mix, not a risk-matched one (see section 8 below).
- **E1 on an ETF universe.** E1 reads "fund/issuer 8-Ks and crypto venue/regulatory news". Brief 22's $4 assumes 100 items and about 3 filings a night over 20 symbols. How many such items an ETF-only universe produces is not in the evidence. The unlock may buy nothing.

**Minor.** G4 is "$500-1,000" in section 7 against "5-10% of intended capital" elsewhere in the gate text; the same dollar-versus-percent issue as A.

**Verdict.** Best economics of the five. No fatal flaw. Score 7.5.

## 4. Proposal C, agents as the quant team

**What it gets right.** Production spend is listed per agent and sums correctly (Reporter $0.65, Triage under $0.25, Reviewer $0.10, about $1 at launch; Reader about $4 from $3,000, which is the 600x rule on $5). The workspace limit is $10. Section 12 is honest about the no-plan case: "Lab sessions move to monthly on the API at about $3-5 each; weekly would cost $13-21 a month".

**Serious flaws**
- **Five of the nine agents run on the owner's subscription** (section 3, "Research and ops agents ... run in Claude Code sessions the owner attends, on his subscription"). The headline "$1-5 a month" (section 8) therefore excludes the largest cost. If priced at API rates, as in brief 22: Lab Lead on Opus weekly $21.3; plus a Sonnet subagent, an Opus red-team on every G0/G1 package, ad hoc Ledger Q&A and incident work. My sum is about $35-50 a month, which is 3.5-5% of $10,000 and above 36% of $1,000. This breaks "near-zero budget" for any owner without a plan.
- **The Lab is central, and its expected return is about zero.** Brief 02 verification and gap item 11 (Gençay): every LLM-discovered strategy was rejected once deflated by trial count, and an LLM's ideas are mined from history it was trained on. Spending the most capacity on the part with the lowest expected yield is the weakest use of a near-zero budget. C's own risk 1 concedes this.
- **No after-tax or benchmark criterion in G1** (section 7). The gate list is DSR, plateau, holdout, windows and costs x2 only.
- **Unpriced extras.** Section 3 puts the live key under a second Windows user and runs a pre-commit hook and permission hooks. Fine on cash, but they add owner time with no payoff at $1k-$10k.

**Verdict.** Cheapest in API cash, most expensive in true cost if the plan is not already paid, and the most owner time (weekly 60-90 minutes). No fatal flaw. Score 5.

## 5. Proposal D, failure-first

**What it gets right.** The only explicit capital-scaled LLM cap: `min($15, 2% x capital / 12)` (section 3). It checks: $1.67 at $1,000, $8.33 at $5,000, $15 at $10,000. "Hitting the cap means LLM unavailable. Trading is unaffected." S0 runs in shadow always, and "if nothing beats S0 through G1, JARVIS runs S0" (section 4). F10 names tax drift as a failure mode and puts "ETF sleeve in an IRA if fundable (fee unconfirmed)" in P0. The growth table applies the 600x rule to every unlock ($99 SIP needs about $59,400; Norgate about $31,500; $5 VPS at $3,000). The "cost of overrides" counter and the weekly measurement of the cost of controls against S0 (section 13, risk 2) are the only attempt to price risk controls in dollars.

**Serious flaws**
- **The after-tax comparison has no threshold.** G1: "after-tax comparison with S0" (section 7). It does not say what result passes. B's "within 1 point and drawdown at most 0.7x" is a test; D's is a report.
- **Whole shares for overnight holdings** (section 2, step 9, and F6). Same $1,000 rounding cost as B. D at least says "within 5 points of target" and "fewer and cheaper ETFs" at $1,000 (section 4), which treats the issue but narrows the universe.
- **Tax-lot check in the order path.** Step 9 and F10 flag lots near one year. Delaying a pre-registered exit to cross the long-term line is discretionary, was not in the backtest, and conflicts with D's own rule that exits are backtested with entries (brief 17).
- **Heavy build for no dollar return.** F1-F14, 13 failure drills, hash-chained ledger, a future-poisoning CI test, a Change Reviewer on every deploy: P2 is weeks 6-10. D's risk 2 says so. The economics are that a solo developer spends perhaps three to four months of effort on a book whose expected net edge is -$7 to -$130 a year at best, as computed above.
- **The cap formula is capped at 2% of capital, which is the full size of the edge.** At $5,000 the cap lets $8.33 a month through; the actual spend is lower, so this is a ceiling more than a cost.

**Verdict.** Best spend control and best honesty about a likely null. No fatal flaw. Score 7.

## 6. Proposal E, staged platform

**What it gets right.** The best growth table: every step S1-S10 carries a capital trigger from the 600x rule and an "honest outlook" ("likely never" for S4b, S9, S10). The arithmetic is right ($52.50 x 600 = $31,500; $99 x 600 = $59,400; $700 x 600 = $420,000; $6 x 600 = $3,600). Launch cost is $0-1 under a $5 limit. The Narrator can run weekly only (about $0.15). The report falls back to a template if the LLM is off. Agent evidence defaults to weight 0.

**Serious flaws**
- **G4 cannot be run at the low end of the range.** Section 7: "Micro-live: 5-10% of intended capital". Section 6: "Skip orders under $20 notional". At $1,000 capital that is $50-100 in total, or $10-20 for each of five sleeves, so the order floor would skip most of them. The G4 cost estimate (brief 20: per-fill sd 10 bps, n = 20, SE 2.2 bps) is meaningless at $10-20 fills where a penny is 5-10 bps. A, B, C, D use "$500-1,000", which at $1,000 is the whole account. Either way, G4 does not scale with capital.
- **No after-tax criterion in G1** (section 7) and the IRA is S4a, behind S1-S3, with the decision at P5 (section 11). Brief 19 makes it the largest lever; it needs deciding before paper balances and micro-live are set.
- **Typo in the cost line.** The Narrator row says "about $0.65 nightly (22: $0.031/night)". It is $0.65 a month. As written it is $14 a month, so the table cannot be read at face value.
- **VM at $4-6 a month** at S3 (section 12) while briefs 23 and the other four proposals use the free e2-micro first. Cheap, but at $3,600 capital a $6 VM is a 2% drag by construction.
- **Platform overbuild is a cost.** Five frozen contracts in P0 and empty slots for S5-S10 that the table itself rates "doubtful" or "never". E's own risk 1 says a spreadsheet could run Strategy A.

**Verdict.** Honest ladder; weak gate on tax; one buildability problem at $1k. No fatal flaw. Score 6.5.

## 7. Where the proposals are right and the ranking

Economics-and-tax ranking: B (7.5), D (7), E (6.5), A (5.5), C (5). The order follows how far each avoids spending or building anything that cannot pay for itself at $1k-$10k, and how much of the tax problem it puts in a gate rather than a footnote.

## 8. Ideas to graft

- **B: the after-tax G1 gate** (within 1 point of the benchmark and drawdown at most 0.7x), made harder: the benchmark must be tax-efficient and risk-matched (below).
- **B and D: IRA eligibility, contribution limit, lock-up and fee as a P0 checklist, with account type fixed before G3.** B and D already do the first half. Add the rule: if no IRA is available, strategy A must clear the +1.0 to +1.3 point hurdle to leave S0.
- **B: production LLM $0 and a templated email.** Narrator optional, weekly (E's $0.15).
- **B: crypto sleeve OFF in the $1,000 column.** Add a dollar rule: do not build B until the sleeve is worth enough to cover its tax-plus-cost hurdle.
- **D: capital-scaled spend cap** `min($15, 2% x capital / 12)`, tightened to 0.5% of capital until a feature has earned weight.
- **D: "cost of controls" and "cost of overrides" counters,** reported against S0 weekly.
- **E: the growth table** (capital at least 600 x cost, with an outlook column) for every recurring spend.
- **A: power as a cost line,** and "below $2,400 only the Narrator runs".
- **A and D: the "hold the benchmark, JARVIS as audit layer" fallback written as a sunset rule** (below).
- **My own: archive raw text now, extract later.** Store news and filings with `first_seen_at` ($0). Run extraction once, in a Batch job, only when a golden set and a forward test are actually due. This keeps brief 22's clean post-cutoff window (text dated after the model cutoff stays clean when extracted later) and removes the nightly $4 from the launch budget. This is my inference, not a brief's finding; test it on the golden-set harness.

## 9. Missing from all five proposals

1. **Whether the owner already pays for a Claude plan.** Every "$0" for the builder, lab and review agents depends on it. Ask first. If not, price the roles at API rates and expect $13-50 a month.
2. **Build-phase cost.** Months of Claude Code sessions to build P0-P3 (heavy sessions are about $9.6 each on the API, brief 22). Nobody prices the build, and nobody prices the owner's hours: weekly 60-90 minute rituals against an edge of $10-$130 a year.
3. **A risk-matched, tax-efficient benchmark.** "Half the drawdown" can also be had by holding half the money in T-bills with zero turnover and zero tax drag. Test A against that, not only against a fully invested mix. Rebalance the benchmark with new cash or wide bands, not quarterly.
4. **Where the undeployed capital sits during the 18-30 months of gates** (A P5-P6; B 13-30 months; E 18 months after shadow). If it sits in cash, the opportunity cost against the benchmark is the main cost of the system. The fix is core-satellite: the benchmark holds everything JARVIS has not yet earned, and JARVIS controls only the growing satellite. None says so.
5. **A sunset rule on running costs.** If cumulative after-tax, after-cost P&L trails the benchmark after a set period (for example 24 months), switch the LLM spend off and hold S0. Brief 11 recommendation 2 asks for P&L reported net of LLM and data cost; the proposals report LLM spend but none reports net P&L after all costs.
6. **Dollar-denominated hurdles.** Everything is in percent. At $1,000, 1 point is $10 and a $20 order floor or $1 fractional minimum matters. G4 should be set as a percentage of capital with a dollar floor.
7. **The tax-professional consult and the tax-lot method.** Brief 19 lists eight questions for a professional. No proposal budgets it, though any fee is large against a $10-$130 edge. The Alpaca tax-lot method and 1099 format were not checked (brief 19).
8. **IRA limits.** $7,500 a year in 2026 (so $10,000 cannot go in at once), earned income, lock-up to 59 1/2 with a 10% early-withdrawal charge (brief 19). A $1k-$10k pot that may be needed in an emergency is a poor fit; the proposals mention only "if fundable" or "IRA eligible".
9. **Crypto fee mechanics in the ledger.** Alpaca charges the crypto fee in the asset received (brief 11), so basis and quantity shift; only some ledgers list the fee asset. Also the fee table should be config refreshed against live pages (brief 11 recommendation 1).
10. **The cost of spot BTC/ETH ETFs** (expense ratio against Alpaca's 0.30-0.50% round trip). Brief 21 marks it unresearched; four proposals name it as the fallback for crypto but none costs it. Texas was absent from Alpaca's crypto state list in the (year-old) data (brief 21), so the fallback may be the main route.
11. **Texas has no state income tax** (not in the briefs; check). It removes brief 19's case D and leaves the federal hurdle of +1.0 to +1.3 points at 12-24% brackets.

## 10. Is the budget claim real?

- **Cash budget (data plus LLM API): yes, for all five,** at $0 to about $10 a month, with caps. The gating by capital works as designed.
- **Total cost of ownership: not as claimed.** The "$0" depends on an unstated subscription, an unpriced build, unpriced owner time and, for A and B only, $2.64 of power. The honest statement is "cash $0-10 a month, plus an existing Claude plan, plus months of owner time".
- **Value against the benchmark: negative in expectation in a taxable account** (central about -0.7 points, range about -2.4 to +0.9, before LLM spend). It is about neutral in an IRA. The designs sell risk reduction, not return; that is honest, but only B and D carry it into a gate or a fallback, and none prices the risk reduction against a risk-matched alternative.

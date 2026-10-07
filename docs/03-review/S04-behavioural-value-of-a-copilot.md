# S04 - Behavioural value of a co-pilot (specialist review of FINAL-design.md)

Reviewer: S04. Date: 2026-10-02. Tags: FETCHED = opened this session; RECALLED = from memory or a search snippet only, not opened; DC = design choice; ESTIMATE = my arithmetic.

## Bottom line

The design's own arithmetic says the satellite is worth about -$14 to -$18 a year (section 1). The owner-value case for JARVIS therefore rests on behaviour: keeping one person on a plan. The evidence says that this value is real but is not measured anywhere in the design. It also says a co-pilot can raise trading as easily as lower it. Three changes matter most.
1. Measure behaviour directly (S04-P1).
2. Put friction on the owner's deviations, not on information (P2, P3).
3. Turn the "agents never do" list into a testable policy (P5).

On the reviewer's over-build concern, the behavioural evidence points toward cheap friction (delay, a written pre-commitment, a default) and away from heavy machinery. It also supports getting the owner onto the S0 plan before the 43-53 dev-day executor exists (P6).

## What the design gets right (with evidence)

1. **No Claude output reaches an order (section 1, section 3).** Studies of LLMs as investment advisers show systematic bias.
   - Winder, Hildebrand and Hartmann (PLOS ONE 2025) prompted three chatbots in 270 runs for a $10,000 portfolio. Portfolios were over 93% US equities (benchmark 59%), had up to 27.9% in recently traded names (benchmark 9%), and carried higher fees. FETCHED.
   - Lee et al. (arXiv 2507.20957, ICAIF) find tech and large-cap preferences, and models that cling to a first judgment despite counter-evidence. FETCHED.
   - Zhi et al. (arXiv 2503.08750) generated 567,000 recommendations from seven LLMs, including Claude-3.5-Sonnet, and found severe concentration in a few names (Gini about 0.93-0.94). FETCHED.
   - Sharma et al. (ICLR 2024) show five assistants tilt toward the user's stated view, partly because people prefer agreeable answers. FETCHED.
   - Together these support "Claude explains, code decides". Sycophancy matters most when the owner asks a chatbot whether to override the plan.
2. **Dollar-denominated risk tolerance and a code-computed dial b (section 9).** Winder et al. found chatbots recommend more equity to users who sound confident or optimistic. Keeping the risk dial out of the LLM's hands avoids this. FETCHED.
3. **Passive core, near-zero turnover, long/flat monthly (sections 4, 6).** Barber and Odean (JF 2000, 66,465 households, 1991-96): market 17.9%, average household 16.4%, heaviest traders 11.4%, average turnover about 75% a year. FETCHED (abstract). Barber, Lee, Liu and Odean (RFS 2009, all Taiwan investors) report an individual-investor penalty of 3.8 points a year, about 2.2% of GDP. FETCHED. A monthly ETF rule gives the owner little to churn.
4. **Tax-aware sells and the wash-sale guard (sections 2, 6).** Odean (JF 1998, about 10,000 accounts) shows investors sell winners and hold losers, which is not justified by later returns and lowers after-tax returns in taxable accounts. FETCHED. Code-enforced tax-lot checks counter a documented behavioural bias.
5. **Pre-commitment machinery: G0 freeze, 72-hour cool-off, approval expiry (sections 6, 7).** Thaler and Benartzi's Save More Tomorrow (JPE 2004) shows how well advance commitment works: 78% joined, 80% stayed through the fourth raise, and savings rose from 3.5% to 13.6% over 40 months. FETCHED (abstract). Note that SMarT works through a default and delay, not through technical lock-in.
6. **Veto-but-not-add, with counterfactual P&L logged (section 9) and the "cost of overrides" counter (weekly memo).** This is the one metric in the design that measures behavioural value directly. It is under-used (see P1).
7. **No overall confidence score, evidence panels, no "Thesis" component (sections 9, 10 rows 28, 56).** This blocks the false-precision failure mode.

## What should improve

### S04-P1 (must): add a Behaviour Ledger and make it part of the sunset rule
- **Section:** 7 (sunset rule), 9 (weekly memo), 3 (Narrator inputs), 15 (new open item).
- **Change:** Define "Behaviour P&L" as the owner's actual time-weighted NAV minus the plan-shadow NAV. JARVIS already computes the shadow NAV (step 16) and `cash_events`.
  - Attribute the difference to events: veto, manual trade, late execution, deposit timing.
  - Report monthly: adherence rate (decisions executed as specified within N days), counts of vetoes, manual trades and loosening requests, and the owner's money-weighted return minus time-weighted return (the same idea as Morningstar's "gap").
  - Add one baseline step before L0. The owner imports 12-24 months of past broker history, and JARVIS computes the owner's own historical gap against an S0-equivalent.
  - Add a clause to the sunset rule: JARVIS is judged on process measures (adherence, override cost) as well as P&L.
- **Why:** The satellite's expected effect is about -$14 to -$18. Population estimates of the behaviour gap are larger:
  - Morningstar's 2025 edition: 7.0% dollar-weighted versus 8.2% total return over 10 years, a 1.2-point gap. RECALLED (search snippet).
  - Vanguard's behavioural-coaching estimate: 150 bps, and "up to 2%" in its coaching guidance. FETCHED via InvestmentNews; Vanguard's own PDFs could not be read.
  - ESTIMATE at $5,000: 1.2 points = $60 a year; 1.5 points = $75 a year; a Barber-Odean heavy trader's 6.5-point shortfall = $325 a year (5,000 x 0.065).
  - These are population averages from vendor-friendly or older samples. A FatFIRE critique (FETCHED) points to selection bias and says the value is near zero for people who would never have panicked. That is why the owner's own baseline is needed.
- **Why it cannot be measured through returns (ESTIMATE):**
  - At sigma = 11% a year (DC, a five-ETF mix), detecting a 1.5-point edge at about 2 standard errors needs T = (2 x 11 / 1.5)^2, about 215 years.
  - Returns cannot prove the value. Behaviour P&L can, because the shadow plan is an exact counterfactual and needs no statistics.
- **Cost:** $0 a month (no LLM). +2-3 dev-days in P1b/P4.
- **Risk:** The measure only sees behaviour that exists. If JARVIS prevents panic selling, the avoided loss is invisible. The baseline import is the only hedge. n = 1.

### S04-P2 (should): change the information diet; make the daily digest exception-only
- **Section:** 9 (rhythm, weekly memo), 3 (Narrator).
- **Change:**
  - The daily email goes out only when something needs action or the state changes. Liveness is already covered by Healthchecks.
  - NAV and after-tax comparisons move to the weekly memo.
  - Remove ML-lane forecasts, SHAP drivers and regime labels from the default memo. They stay on a "Lab" dashboard tab.
- **Why:**
  - D'Acunto, Prabhala and Rossi (RFS 2019): robo-advice helped undiversified investors, but already-diversified adopters traded more after adoption, and everyone logged in more. FETCHED (abstract).
  - Sicherman et al. (RFS 2016): logins fall 9.5% after market declines, so attention is selective and tends to rise in good news. FETCHED (abstract).
  - Benartzi and Thaler's myopic loss aversion work (1995; frequent evaluation makes people avoid risk) is RECALLED.
  - A weight-0 forecast is a promise to the code, not to the owner's mind.
- **Cost:** $0. -0.5 to +1 dev-day (a filter, not new code).
- **Risk:** Less visible activity may feel "hollow". Mitigation: the weekly memo's override cost and adherence lines.

### S04-P3 (should): apply the loosening rule to vetoes of exits
- **Section:** 9 (permission modes), 6 (changing a value).
- **Change:**
  - Vetoing a risk-increasing buy stays immediate; this is tighten-only.
  - Vetoing a signal exit, or any other deviation that raises risk, becomes a loosening. It needs the emailed hash, a structured reason (which pre-registered rule is being broken, and what the owner expects to happen), and a 24-hour delay. Its counterfactual P&L is logged.
  - Templated text only. No LLM evaluates the reason.
- **Why:**
  - The design's own principle is "tighten fast, loosen slowly", but section 9 lets the owner veto at once, and a veto of a sell is the likeliest panic action.
  - Odean (1998) shows what discretionary selling looks like. FETCHED.
  - Gollwitzer and Sheeran's meta-analysis (94 tests, d about 0.65 for implementation intentions) supports an "if X then Y" plan. RECALLED (search snippet).
  - Bhattacharya et al. (RFS 2012, about 8,000 German brokerage customers): only about 5% took unbiased advice, those who needed it least took it, and most did not follow it. FETCHED (abstract). The lesson is that friction on deviations works better than more advice.
- **Cost:** $0. +1-2 dev-days (reuses `JARVIS-Approve`).
- **Risk:** The owner bypasses it in the Alpaca app. The existing rule (unregistered activity means SAFE, and counts toward P1) handles this.

### S04-P4 (should): owner-written crisis letter and pre-mortems at stage steps
- **Section:** 9 (Mission Plan), 7 (L0, G4, G5), 3 (Red-Team).
- **Change:**
  - At onboarding the owner writes a short letter: what I will do at -10%, -20% and -30% (in dollars, using the Mission Plan's tolerance), and why I chose this plan.
  - Code, not an LLM, sends the owner their own letter when the loss bands trip.
  - At L0 and at each G5 step, the owner answers three fixed pre-mortem questions: "it is a year later and this went badly; what happened?" Red-Team's pre-mortem on artifacts stays.
- **Why:**
  - Vanguard says its behavioural value is concentrated in extreme markets. That is a vendor claim. FETCHED via InvestmentNews.
  - Klein's 2007 premortem rests on prospective hindsight (Mitchell, Russo and Pennington 1989, reported as about 30% more correctly identified reasons). FETCHED (Klein, partial); the 30% figure is RECALLED.
  - No controlled study of premortems or decision journals in retail investing was found. The evidence is thin, but the cost is very low.
- **Cost:** $0 (template). +1-2 dev-days.
- **Risk:** A boilerplate letter is ignored. A model-written reassurance would be worse (see P5).

### S04-P5 (must): make the "agents never do" list a tested policy
- **Section:** 3 (Narrator, Ledger Analyst, Builder, Strategy Lab forbidden columns), 5 (CI tests).
- **The list:** No agent may:
  1. give a buy, sell, hold or timing view, or say whether to override;
  2. give a price forecast, target or bare probability;
  3. agree with an owner's stated belief or reassure after a loss in its own words;
  4. offer a causal story for a price move as fact (DC; no paper opened);
  5. choose or recommend tickers, or change risk from owner mood (tickers come from a code screen on expense ratio, size and inception; Zhi et al. and Winder et al. show product and fee bias);
  6. present shadow or backtest results as predictions;
  7. use urgency or fear-of-missing-out language.
- **Test:** An "advice-leak" set of about 30 prompts (override requests, "I'm sure X will rise, agree?", crash questions) run against the Narrator and `/ask-ledger` in the eval workspace, pass bar 100% refuse-and-redirect to the rule. This gates every model change.
- **Why:** Sharma et al. (sycophancy) FETCHED; Winder et al. FETCHED; Lee et al. FETCHED; Zhi et al. FETCHED. Lo and Ross (HDSR 2024) discuss fiduciary, tailoring and regulatory problems for LLM advice; I read only a secondary MIT Sloan summary. Those studied older models, so current magnitudes are unknown.
- **Cost:** About $0.31 per model change (ESTIMATE: 30 x (2.6k tokens x $2/M + 0.5k x $10/M)), inside the section 3 validation budget of $2-6. +2-3 dev-days. No change to the monthly cap. This respects the near-zero budget.
- **Risk:** Over-refusal makes `/ask-ledger` less useful. Keep the factual "why did the rule do X?" path open.

### S04-P6 (should): start with RECOMMEND-live S0, and gate the executor on measured adherence
- **Section:** 11 (build order), 1 (timeline), 9 (permission modes), 13 (risk 1).
- **Change:**
  - From about month 2-3, run S0 with real money in RECOMMEND mode: JARVIS emails the orders, the owner places them by hand, and fills are adopted with `jarvis adopt`. S0 is the null and needs no validation gate.
  - Decide the P3 executor (43-53 dev-days, mutation testing) from adherence. If adherence is at least 95% over 6 months and Behaviour P&L is near zero, the executor adds little behavioural value, and the design's own month-15 fallback applies without regret. If not, the executor, which removes the owner from the loop, has measured value.
- **Why:** The design's first live dollars are at month 12-15. Behavioural value is lost while the owner trades by hand or sits idle. Bhattacharya et al. show advice alone is often not followed, so adherence is the thing to measure. FETCHED.
- **Cost:** $0. Saves up to 43-53 dev-days if the executor is deferred or dropped (ESTIMATE from section 11); adds about 2 for hand-order adoption flows.
- **Risk:** Manual execution errors and tax-lot choices. This is the owner's decision. Not tax advice.

### S04-P7 (could): demote the Reader digest; add an owner Idea Journal
- **Section:** 3 (Reader, tier T1), 9 (Watchlist Digest), 4 (Owner Idea Lane).
- **Change:**
  - Do not enable the weekly Watchlist Digest at T1 by default. It feeds single-name attention with no allowed action: the design itself rules out single-name trading below $31,500, and its A1 is "likely unreachable".
  - The owner types ideas (for example TSLA) with a direction and horizon. Code scores them forward against the benchmark, and the memo shows the owner's hit rate and Brier score.
- **Why:** Barber and Odean show active single-name trading by individuals loses (FETCHED). Feedback on one's own track record is the debiasing mechanism I am proposing. I found no study showing it works, so the evidence is UNVERIFIED.
- **Cost:** Saves about $0.80 a month at T1 and about 4-8 dev-days of Reader A0 and labelling work (ESTIMATE; section 11 does not itemise it). Adds 1-2 dev-days.
- **Risk:** The owner may see this as removing a "meaningful" agent. Mitigation: archive and Reader capability stay; only the owner-facing digest is off until P1 data justifies it.

## Ranking of the 8 Claude roles by owner value that does not depend on beating the market
1. **Narrator**, if its content is mostly adherence, override cost and downside in dollars (P1, P4). High.
2. **Ledger Analyst** (explanation on demand), if bounded by P5. Medium.
3. **Incident Analyst.** Operational value, moderate.
4. **Red-Team** on gate loosening and stage steps. Moderate; the 12-of-20 catch bar is expensive to build for one user.
5. **Builder, Strategy Lab.** Build value, not owner-behaviour value.
6. **Change-Watch.** Low, operational.
7. **Reader.** Low, with a risk of negative behavioural value (P7).

## What I could not verify
- Vanguard's own Advisor's Alpha PDFs returned binary content, so the derivation of the 150 bps figure is **unverified**. I relied on InvestmentNews and a critique blog. The link to DALBAR comes from search results only.
- Morningstar's "Mind the Gap" figures come from a search snippet; the page itself would not load.
- Gollwitzer and Sheeran's effect size (d about 0.65) and the Mitchell-Russo-Pennington 30% figure come from search snippets. Klein's article was read only in part.
- Barber and Odean's 11.4% is described in the abstract as the heaviest traders' return; whether it is net of costs I did not confirm from the full text.
- Benartzi and Thaler (1995) on myopic loss aversion, and DALBAR's methodology and its critics, are RECALLED.
- Lo and Ross (HDSR 2024) returned HTTP 403; I used a secondary summary.
- All LLM-bias studies used older models. No study was found on current Claude models as retail advisers. No study was found that compares LLM-written with templated messages for adherence.
- No controlled evidence was found that decision journals or premortems change retail investing behaviour.
- The 11% volatility used in the detectability arithmetic is my assumption.

## References
1. Barber, B. and Odean, T. (2000). Trading Is Hazardous to Your Wealth. Journal of Finance 55(2), 773-806. https://ideas.repec.org/a/bla/jfinan/v55y2000i2p773-806.html. FETCHED (abstract page; full PDF was unreadable).
2. Barber, B., Lee, Y.-T., Liu, Y.-J. and Odean, T. (2009). Just How Much Do Individual Investors Lose by Trading? Review of Financial Studies 22(2), 609-632. https://ideas.repec.org/a/oup/rfinst/v22y2009i2p609-632.html. FETCHED (abstract).
3. Odean, T. (1998). Are Investors Reluctant to Realize Their Losses? Journal of Finance 53(5), 1775-1798. https://faculty.haas.berkeley.edu/odean/papers/disposition/disposition.html. FETCHED.
4. D'Acunto, F., Prabhala, N. and Rossi, A. (2019). The Promises and Pitfalls of Robo-Advising. Review of Financial Studies 32(5), 1983-2020. https://ideas.repec.org/a/oup/rfinst/v32y2019i5p1983-2020..html. FETCHED (abstract).
5. Thaler, R. and Benartzi, S. (2004). Save More Tomorrow. Journal of Political Economy 112(S1), S164-S187. https://ideas.repec.org/a/ucp/jpolec/v112y2004is1ps164-s187.html. FETCHED (abstract).
6. Bhattacharya, U., Hackethal, A., Kaesler, S., Loos, B. and Meyer, S. (2012). Is Unbiased Financial Advice to Retail Investors Sufficient? Review of Financial Studies 25(4), 975-1032. https://ideas.repec.org/a/oup/rfinst/v25y2012i4p975-1032.html. FETCHED (abstract).
7. Sicherman, N., Loewenstein, G., Seppi, D. and Utkus, S. (2016). Financial Attention. Review of Financial Studies 29(4), 863-897. https://ideas.repec.org/a/oup/rfinst/v29y2016i4p863-897..html. FETCHED (abstract).
8. Winder, P., Hildebrand, C. and Hartmann, J. (2025). Biased echoes: LLMs reinforce investment biases and increase portfolio risks of private investors. PLOS ONE. https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0325459. FETCHED.
9. Lee, H. et al. (2025). Your AI, Not Your View: The Bias of LLMs in Investment Analysis. arXiv 2507.20957. https://arxiv.org/abs/2507.20957. FETCHED.
10. Zhi, Y. et al. (2025). Exposing Product Bias in LLM Investment Recommendation. arXiv 2503.08750. https://arxiv.org/html/2503.08750v1. FETCHED.
11. Sharma, M. et al. (2024). Towards Understanding Sycophancy in Language Models. ICLR 2024; arXiv 2310.13548. https://arxiv.org/abs/2310.13548. FETCHED.
12. Vanguard, Advisor's Alpha / InvestmentNews coverage. https://investmentnews.com/practice-management/advisors-continue-to-shine-as-emotional-circuit-breakers-vanguard-says/259609. FETCHED (secondary). Vanguard PDFs: RECALLED (unreadable).
13. FatFIRE, Vanguard Advisor Alpha: Does the 3% Apply to You? https://fatfire.com/vanguard-advisor-alpha-study/. FETCHED (critique blog, secondary).
14. Morningstar, Mind the Gap (2025 edition). https://www.morningstar.com/en-us/business/insights/research/mind-the-gap. RECALLED (search snippet only).
15. Klein, G. (2007). Performing a Project Premortem. Harvard Business Review. https://glenbrook.com/?p=588. FETCHED (partial, secondary host). Mitchell, Russo and Pennington (1989): RECALLED.
16. Gollwitzer, P. and Sheeran, P. (2006). Implementation intentions and goal achievement: a meta-analysis. Advances in Experimental Social Psychology. RECALLED (search snippet only).
17. Lo, A. and Ross, J. (2024). Can ChatGPT Plan Your Retirement? Harvard Data Science Review. https://hdsr.mitpress.mit.edu/pub/jnml28pl/release/1. RECALLED (403); summary read via https://mitsloan.mit.edu/node/47207 (FETCHED, secondary).
18. Benartzi, S. and Thaler, R. (1995). Myopic Loss Aversion and the Equity Premium Puzzle. QJE. RECALLED.

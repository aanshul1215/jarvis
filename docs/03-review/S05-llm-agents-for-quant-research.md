# S05 - LLM agents for quant research: Strategy Lab and Reader

Reviewer: S05. Date: 2026-10-02. Scope: FINAL-design.md sections 3 (rows 4, 5, 7), 4 ("Adding strategies", Idea Lane), 7 (G0-G1c), 11 (P2, P5).
Tags: FETCHED = opened this session (note: pages were read through a fetch-and-summarise tool, so numbers should be re-checked against the PDF before being quoted). RECALLED = from memory. ESTIMATE = my arithmetic.

## Bottom line

The evidence says an LLM research agent is cheap and fluent at generating and coding candidate strategies. It cannot be trusted to evaluate them, remember which ones it has tried, or avoid contamination from what it already knows. The best-evidenced controlled test I opened (Gencay 2026) found that every LLM-discovered strategy failed certification once the search count was honestly deflated, while passive benchmarks survived. The design already puts the LLM on the right side of that line. What it can still improve is (a) how strictly the trial count is enforced, (b) a few structural leak checks that statistics cannot replace, (c) a one-way Lab loop, and (d) shrinking the Reader, whose evidence base for this owner is the thinnest in the whole roster. Every proposal below costs $0 a month in metered spend; several save money and dev-days.

## What the design gets right (with evidence)

1. **LLM authors, code decides.** Gencay (2026) ran two frontier models, 453 US equities and 39 ETFs, searches up to 100 candidates and five repeats, with costs; every LLM-found strategy failed certification at the agent's own recorded trial count, and a plain equal-weight buy-and-hold was certified. In one multi-asset experiment, ETF time-series momentum (SR 0.49, CI -0.13 to +1.24) was *not* certified despite a +55% return. S-A is exactly that kind of rule, so the design's pre-declared outcome "S-A may fail G1 and S0 runs" matches the literature. FETCHED (arXiv 2608.27734).
2. **A trial ledger plus deflated Sharpe.** Gencay's DSR input is a ledger of every evaluation the search performed; the design's trader-side registry, `jarvis-lab run` logging and cumulative N_eff are the same idea (Bailey and Lopez de Prado, DSR; FETCHED, abstract-level only).
3. **No reliance on LLM backtests over pre-cutoff text or prices.** Lopez-Lira, Tang and Zhu show exact recall of pre-cutoff economic values, that "respect the date" instructions do not stop it, and that masked entities and dates are reconstructed; no recall post-cutoff. This justifies the `llm_origin` tag, the sealed holdout and "model change restarts the clock". FETCHED (arXiv 2504.14765).
4. **Reader quarantined, no order effect, A2 deleted.** Lopez-Lira and Tang find GPT-4 headline scores predict next-day drift (Oct 2021 to Dec 2023, 134,129 headlines, all NYSE/NASDAQ/AMEX names), but the Sharpe fell from 6.54 (2021 Q4) to 3.68 (2022) to 2.33 (2023), the gross long-short Sharpe was 3.28, returns were gone at 20 bps round trip, and the effect is in small stocks and negative news. That is a short-horizon, high-turnover, small-cap signal an owner running a monthly five-ETF book cannot use. FETCHED (arXiv 2304.07619 v5).
5. **Honest agent census and no LLM confidence.** Huang et al. (ICLR 2024) find LLMs do not reliably self-correct reasoning without external feedback; the design's mechanical verifiers per role are the right response. FETCHED (arXiv 2310.01798).
6. **The ladder of stated cost is correct in scale.** RD-Agent(Q) reports under $10 of LLM cost for its full run (about 44 loops, 24 valid, o3-mini); AI Scientist about $6-15 per paper. Generation is cheap; validation is the bottleneck, which is where the design spends its effort. FETCHED (arXiv 2505.15155; 2408.06292; 2502.14297).

## What the evidence says an LLM research agent can and cannot do

| Can (author-reported unless stated) | Cannot or unproven |
|---|---|
| RD-Agent(Q): on CSI 300 (train 2008-14, test Jan 2017-Aug 2020) ARR 14.21% versus 5.70% for Alpha158, with 70% fewer factors; also tried CSI 500 and NASDAQ 100 over 2024-mid 2025 (FETCHED). | Same paper: relies on the LLM's internal financial knowledge, so contamination is untested; transaction costs described only as "realistic"; no multiple-testing correction mentioned; single market and window. |
| AlphaAgent: adds originality (AST similarity), hypothesis-factor alignment and complexity limits against alpha decay; CSI 500 and S&P 500, four years (FETCHED; no numbers read). | No cost treatment seen; author-reported only. |
| Alpha-GPT (EMNLP 2025 demo) and QuantAgent frame it as human-in-the-loop or knowledge-base refinement (FETCHED, abstracts). | No independent replication found by me. |
| Generate working code cheaply and quickly. | Beel et al. independently found 42% of AI Scientist experiments failed on coding errors, some hallucinated numbers, and poor novelty judgments (FETCHED, arXiv 2502.14297). |
| Extract text signals that are real but short-lived (Lopez-Lira and Tang above). | Kim, Muhn and Nikolaev reported GPT-4 at 60.35% earnings-direction accuracy versus 52.71% for analysts (150,678 firm-years, 1968-2021, no transaction costs addressed). The author's own page now says the paper was withdrawn because of "inconsistencies in the underlying data and analyses" while findings are reviewed. Treat it as unreplicated. FETCHED (arXiv 2407.17866 v2; Nikolaev's research page). |
| Look-ahead can be small out of sample: Glasserman and Lin find anonymised headlines do better in-sample, and look-ahead is negligible after the training window (FETCHED); ChronoBERT/ChronoGPT match a larger Llama's Sharpe (FETCHED, abstract). | Sarkar and Vafa find direct evidence of lookahead bias in two applications (RECALLED detail; SSRN 4754678; only a metadata snippet seen). Masking is helpful, not sufficient. |

## What should improve

### S05-P1 - Count every harness call; use the raw ledger count as N for Lab specs (sections 4 "Adding strategies", 7 G0 and G1a)
- **Change:** one evaluation entry point (`jarvis-lab run`) writes a trial row for every call, including exploratory ones. For Lab and `llm_origin` specs, the DSR input is the raw ledger count, not N_eff = max(ONC, Galwey). N_eff stays for hand-registered published rules.
- **Why:** Gencay states the count is complete "by construction" only because all candidates pass one entry point, and lists as a limitation that DSR assumes exchangeable trials, which hypothesis rotation (each idea informed by the last result) violates. Effective-N shrinkage is least safe exactly where an LLM reacts to results.
- **Arithmetic (ESTIMATE):** expected maximum null SR0 = sd x [(1-g) x Phi^-1(1-1/N) + g x Phi^-1(1-1/(N e))], g = 0.5772, with the design's trial-SR sd floor 0.15. N = 6: 0.4228x0.967 + 0.5772x1.54 = 1.30, SR0 = 0.19. N = 20: 1.90, SR0 = 0.29. N = 50: 2.28, SR0 = 0.34. N = 100: 2.53, SR0 = 0.38. N = 500: 3.05, SR0 = 0.46. The cost of honesty from 20 to 100 is only about 0.09 SR. The unit of the 0.15 floor is the design's; the formula is as displayed in Gencay (FETCHED), original RECALLED.
- **Cost:** $0. **Effort:** +1 dev-day in P2. **Risk:** a higher bar kills more specs; that is the intended outcome. **Priority:** must.

### S05-P2 - Add a planted look-ahead oracle to G1c (sections 5 CI leak tests, 7 G1c)
- **Change:** a CI spec that trades on next-month return must be rejected by construction (the harness refuses any series without a declared `available_at`), and the test must assert the DSR step alone would have passed it.
- **Why:** Gencay's planted oracle (design SR 34.7, evaluation 51.5, DSR 1.00) passed deflation and was stopped only by a structural guard. Statistics do not catch leaks. The design's future-poisoning and shuffled-label tests are good but should be paired with this case.
- **Cost:** $0. **Effort:** +0.5 dev-day. **Risk:** none material. **Priority:** must.

### S05-P3 - Make the Lab a one-way funnel with a pre-registration stage (section 3 row 5; section 4)
Structure: (0) pre-register mechanism, cited source, sign, universe, a grid of at most 6 cells, kill condition, hashed into the registry before any data is run; (1) harness run, one entry point, output a JSON of at most about 1.5k tokens, with no price rows ever entering Claude's context; (2) critique in a fresh context that receives the code-computed diagnostics (leak tests, plateau, costs x2, 5-year windows) and must cite them; (3) registry entry, including **negative results**; (4) forward shadow only. No results-conditioned re-tuning inside a family; a rewrite is a new family and a new trial.
- **Why:** RD-Agent(Q)-style loops feed results back to the LLM, which is the channel through which search intensity inflates in-sample Sharpe. Gencay's best design had SR 1.69 in design versus 0.18 out of sample (DSR 0.86 below the 1.21 threshold). Huang et al.: critique helps only with external feedback, so give it code diagnostics. A small context also protects the owner's limited plan usage; ginlix-LangAlpha's code-executing pattern is the same idea (FETCHED by brief 01, not re-opened).
- **Cost:** $0, plan usage falls. **Effort:** -1 to +2 dev-days (schema is small; it replaces ad hoc process). **Risk:** the owner can still paste results into the session; this is a soft control and should be labelled DC. **Priority:** must.

### S05-P4 - Replace the "only data from July 2026 is clean" rule (section 4 "Adding strategies")
- **Problem:** with a model cutoff near mid-2026 and a monthly strategy, the clean slice is about 12 months by the P2 verdict, which is 12 observations: no test can pass on it, so the rule either blocks every `llm_origin` spec or gets ignored.
- **Change:** every `llm_origin` spec needs a cited pre-existing source and mechanism; it carries a trial multiplier (x2, DC) in N; the post-cutoff slice is reported and shadow-scored but not gating.
- **Why:** contamination affects what the LLM chooses to test, not the harness's computation (Lopez-Lira, Tang, Zhu); the ledger is the correction. **Cost:** $0. **Effort:** 0. **Risk:** judgement call. **Priority:** should.

### S05-P5 - Replication first, with two planted controls; one extra role at $0 (section 11 P2; section 3)
- **Change:** the first Lab job is a **Replication Analyst** task: reproduce plain Faber 10-month SMA in the harness, plus a planted random spec (must fail) and the P2 oracle (must be blocked). Only then may a novel spec enter. Add a **Spec Clerk** step (the Lab's stage 0, same attended session) that turns an owner idea into the pre-registration form. Both are modes of the Lab, not new unattended agents.
- **Why:** Beel et al. show unchecked agent code fails often; the harness must demonstrate it reproduces a known result and rejects known junk before anything is trusted. Total new roles on the roster: zero; named duties: two.
- **Cost:** $0 (plan). **Effort:** about +2 dev-days inside P2's 25-32. **Risk:** low. **Priority:** should.

### S05-P6 - Shrink the Reader to code-only first (section 3 row 7, Reader ladder, section 9, P5)
- **Evidence for this owner:** the published text-return results are short-lived, small-cap and high-turnover (Lopez-Lira and Tang); the KMN paper is withdrawn pending review; and the design itself rates A1 "likely unreachable" and says `event_type` labels are deterministic from 8-K item numbers and Form 4 codes. So the LLM adds only `materiality` and `novelty`, which need 3-4 hours of owner hand-labelling and a 300-item golden set.
- **Change:** ship the Watchlist Digest in P1b as code only (item numbers, Form 4 codes, cluster counts, EDGAR links). Add the LLM Reader only if the owner has opened the digest in at least 6 of 8 weeks and asks for summaries. Then run it weekly in an attended or plan session at $0 metered (no production dependence; failure just skips the digest), or on the API at T2 only.
- **Arithmetic (ESTIMATE):** Reader $0.80 a month x 12 = $9.60 a year, 0.48% of $2,000, comparable to the satellite's expected effect of -$14 to -$18 a year. Plan usage if run on the subscription: 217 items x 2,100 tokens x 1.3 = about 0.59M input tokens a month (about 137k a week), small but real given the owner has hit a session limit once.
- **Cost:** saves $0.80 a month. **Effort:** defers about 6-10 dev-days (my ESTIMATE of golden set, injection set, submit/collect jobs, labelling). **Risk:** fewer visible agents in the first year; the Narrator, Incident Analyst and Lab remain. A plan session reading untrusted filing text needs a no-tools mode (UNVERIFIED flag syntax). **Priority:** should.

### S05-P7 - State the Lab's expected yield and cap its effort; defer the ML lane (sections 1, 4 Shadow ML lane, 11 P6)
- **Why:** with a monthly ETF book, 20 years of data gives a Sharpe standard error of about sqrt((1 + 0.5 x 0.4^2)/20) = 0.23 (ESTIMATE); at N = 50 a spec would need an observed SR near 0.34 + 1.645 x 0.23 = 0.72 to clear a 95% bar. Truly new alpha is unlikely to be detectable, and Gencay's 100-candidate result is the same story. The design's own ML lane expects "no edge" from 1,200-1,500 rows.
- **Change:** cap Lab to 4 sessions a year until the S-A verdict; if the registry reaches N = 50 with no spec clearing G1a, the Lab goes to maintenance mode (harness, replication, null reports). Build the LightGBM lane only after P2, as one Lab spec through the same funnel.
- **Cost:** $0. **Effort:** saves about 4-8 dev-days up front (ESTIMATE). **Risk:** less optionality for the owner's ML interest. **Priority:** could.

### S05-P8 - Make Red-Team earn its keep (section 3 row 4)
- **Change:** feed it the code diagnostics (P3), score it on defects code cannot see (economic implausibility, universe choice, post-hoc ticker selection), and drop or downgrade it if its marginal catch is zero after the first 3 reviews. Pre-screen Lab specs in an attended fresh-context subagent ($0 metered); keep the API Red-Team for G0 and loosening requests.
- **Why:** Huang et al.; the design's own "same-model debate is the weakest configuration." **Cost:** saves up to about $0.10 a month. **Effort:** 0 to +1 day. **Risk:** an attended pre-screen shares the owner's trust domain; the G0-stage API review remains the control. **Priority:** could.

## Over-building check (my domain only)
Lab, Red-Team and Reader together account for a large share of the 8-role roster, but the Lab's real product is a trustworthy harness and a null-results log, which the design needs anyway. The Reader is the one role whose removal in year one changes nothing about money or safety. Proposals P6, P7 and P3 reduce scope; P1, P2 and P5 add 3.5 dev-days that buy the main defence against self-deception.

## What I could not verify
- Gencay (2026) was read through a summariser. One PDF fetch returned a wrong expansion of "DSR" (discarded); the HTML fetch matched the formula and the search abstract. Numbers (SR 1.69 / 0.18, DSR 0.86 versus 1.21, oracle SR 34.7) should be re-read in the PDF. The arXiv ID and "Claude-Sonnet-5" model listing are as returned.
- Sarkar and Vafa: only the abstract-level snippet was available (NBER PDF was unreadable).
- Chen, Kelly and Xiu "Expected Returns and LLMs": search snippet only; no cost analysis read.
- RD-Agent(Q), AlphaAgent, Alpha-GPT, QuantAgent: abstract or setup summaries only; AlphaAgent and Alpha-GPT numbers not read; QuantAgent results not read.
- KMN withdrawal: page gives no date and says "temporarily"; check its current status before citing.
- Whether `claude -p` can run with tools disabled on a subscription, and plan-usage limits for the Reader, were not researched.
- Original Lopez-Lira and Tang sample cutoffs for GPT-4 are as reported by the fetch tool.

## References
- Gencay, E. (2026). What survives honest evaluation? Leakage-safe, search-aware assessment of LLM-driven trading strategy discovery. arXiv 2608.27734. https://arxiv.org/abs/2608.27734 - FETCHED
- Li, Y. et al. (2025). R&D-Agent-Quant. arXiv 2505.15155. https://arxiv.org/abs/2505.15155 - FETCHED
- Tang, Z. et al. (2025). AlphaAgent. arXiv 2502.16789. https://arxiv.org/abs/2502.16789 - FETCHED (abstract)
- Wang, S. et al. (2023/2025). Alpha-GPT, EMNLP 2025 demo. arXiv 2308.00016. https://arxiv.org/abs/2308.00016 - FETCHED (abstract)
- Wang, S. et al. (2024). QuantAgent. arXiv 2402.03755. https://arxiv.org/abs/2402.03755 - search snippet only (treat as RECALLED)
- Lu, C. et al. (2024). The AI Scientist. arXiv 2408.06292. https://arxiv.org/abs/2408.06292 - FETCHED
- Beel, J., Kan, M.-Y., Baumgart, M. (2025). Evaluating Sakana's AI Scientist. arXiv 2502.14297. https://arxiv.org/abs/2502.14297 - FETCHED
- Lopez-Lira, A., Tang, Y. (2023, v5 2025). Can ChatGPT forecast stock price movements? arXiv 2304.07619. https://arxiv.org/abs/2304.07619 - FETCHED
- Lopez-Lira, A., Tang, Y., Zhu, M. (2025). The Memorization Problem. arXiv 2504.14765. https://arxiv.org/abs/2504.14765 - FETCHED
- Kim, A., Muhn, M., Nikolaev, V. (2024). Financial Statement Analysis with LLMs. arXiv 2407.17866. https://arxiv.org/html/2407.17866v2 and withdrawal note at https://faculty.chicagobooth.edu/valeri-nikolaev/ongoing-research-projects - FETCHED
- Glasserman, P., Lin, C. (2023). Assessing look-ahead bias in GPT sentiment. arXiv 2309.17322. https://arxiv.org/abs/2309.17322 - FETCHED
- He, S., Lv, L., Manela, A., Wu, J. (2025). Chronologically consistent LLMs. arXiv 2502.21206. https://arxiv.org/abs/2502.21206 - FETCHED (abstract)
- Huang, J. et al. (2024). LLMs cannot self-correct reasoning yet. ICLR 2024, arXiv 2310.01798. https://arxiv.org/abs/2310.01798 - FETCHED
- Bailey, D., Lopez de Prado, M. Deflated Sharpe Ratio. https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf - FETCHED (summary only); formula RECALLED, shown in Gencay
- Sarkar, S., Vafa, K. (2024). Lookahead bias in pretrained language models. SSRN 4754678. - RECALLED (search snippet)
- Chen, Kelly, Xiu. Expected returns and large language models. - RECALLED (search snippet)
- Brief 01 (this project) for FINSABER, AlphaForgeBench, CLQT, StockBench, ginlix-LangAlpha - FETCHED by brief 01, not re-opened by S05

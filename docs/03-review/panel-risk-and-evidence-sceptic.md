# Panel position: risk-and-evidence-sceptic (2026-10-02)

Stance. I accept a change only if the evidence behind it was opened by the specialist (FETCHED) or the change is evidence-neutral and cheap. I guard the money with three rules: no LLM on the order path, no unvalidated strategy at size, no weakened control without a named residual risk. Evidence grades below follow the specialists' own labels. I did no new research.

## 0. Verdict on the reviewer's over-build concern

The concern is correct for the satellite machinery and wrong for the order-path controls.

- The expected satellite effect is about -$14 to -$18 a year (design section 1, an ESTIMATE built on E = 0 +/- 1 point). Nothing the owner can build will measure it: SE of an information ratio is about 1/sqrt(T) (S01, S07 arithmetic, ESTIMATE; I re-checked 1/sqrt(2) = 0.71 and (1.96/0.2)^2 = 96 years). So G4/G5, sleeve tags, XFER netting, a combined-book wash-sale simulator, a tracking-error band and a 130-180 dev-day plan are spending to run a bet that cannot be judged live.
- The order-path controls (default-deny gate, idempotent ids, reconcile-on-start, kill, dead-man) are needed the moment S0 is placed by code, because S0 alone still sends real orders. Knight (SEC 2013-222, FETCHED by S09) is the evidence class for those. They stay, in their smallest form (S09 "minimum control set").
- The test I applied to every control: does it prevent a loss class that exists with S0 only? If not, it is satellite machinery and goes, unless S-A is later made live.

## 1. Evidence-quality flags (things to re-read before anything relies on them)

| Claim | Where it is used | Grade as reported | My concern |
|---|---|---|---|
| Faber: five-asset buy-and-hold drawdown about 46% vs under 10% timed | S01-P1 arithmetic ($450 protection) | FETCHED text; tables are images | Self-reported, in-sample, 1973-2012. Antonacci medians (53.5 -> 21.4, FETCHED) give a more honest 0.4 ratio. Use 0.4 |
| Tiingo ToS 1.6 transient-only for Starter/free | S10-P1 | FETCHED through a summariser | Conservative action is free, but owner must read 1.6, 5.2, 7.3 by eye |
| Anthropic Consumer Terms provisions 7 and 9 | S06-P11, S06-P1 | FETCHED through a summariser, numbering "as returned" | The whole zero-metered-cost plan sits on provision 7 "explicit permission" for Anthropic's own scheduler. Owner reads it directly in P0 |
| GitHub hosted-runner clause | S09-P1 | FETCHED docs; reliability only two anecdotal threads | Terms gray area; measure before relying |
| Alpaca FIFO-only, no lot selection | S03-P4 | Forum staff reply, 2025-10-30 | Not official docs; P0 probe is authoritative |
| Texas absent from Alpaca crypto list | S08-P1 | Search snippet; official page 404 | Fine as a default because crypto is off anyway; wording must say "unconfirmed" |
| Gencay 2026 (SR 34.7 oracle, 1.69 vs 0.18) | S05-P1, P2, P3 | Summariser; S05 says re-check PDF | The proposals are structurally sensible without the numbers; do not quote the numbers to the owner |
| Gold ETF collectibles 28% | S02-P1, S03-P3, S08-P4 | IRS Chief Counsel memo (non-precedential) plus sponsor FAQ summaries; Topic 409 does not name gold ETFs | Treat as a tax-professional item; the model default of 28% is the conservative side |
| Morningstar 1.2-point gap, Vanguard 150 bps | S04-P1 | Search snippet and secondary | Vendor-friendly; the owner's own baseline matters more than these |
| ETF open spreads and 10:30 start | S02-P6 | European UCITS study plus practitioner guides plus secondary SEC coverage | Indirect. Config change only, measure in 20 sessions |
| Dispersion haircut 0.25-0.50 for TLH | S03-P1 | "my judgement, UNVERIFIED" | Irrelevant if no harvesting is built |
| All dev-day savings | everywhere | Reviewer judgement | Not additive; overlaps between S01, S06, S07, S09, S05, S10 |

Two arithmetic issues I found while checking the specialists' sums:

1. S01-P1 compares the 12.5% sleeve ($450 protection) with a 12.5% T-bill holding ($575 protection) and calls the T-bill "no whipsaw". It leaves out the equity premium the dial gives up (12.5% x a premium of roughly 4-5 points is about $55-60 a year on $10,000, my ESTIMATE, premium assumed). The conclusion (S-A should not be live in a taxable account) still stands on the -$14 to -$18 expected effect, but the "$575 vs $450" line must not go to the owner as stated.
2. S03-P2 values moving the core into an IRA at $29-$60 a year on $10,000 (I re-computed 0.2x(4.0+3.8)=1.56, 0.2x(1.3+3.0)=0.86, drag 0.47% case B; correct). That assumes about $8,750 of core fits in the IRA. The cap is $7,500 a year of contributions (S03, FETCHED 2026), and moving existing taxable holdings in is not a contribution. In year 1 the capacity is at most $7,500 of new money; rollovers and transfers were not researched. The benefit is capacity-bound and the yields are ILLUSTRATIVE.

## 2. Votes on all 76 proposals

Format: id, vote, reason, modification.

### S01 trend and tactical allocation

- S01-P1 MODIFY. Strongest money-guard proposal: S-A is not validated, cannot be validated live, and expected taxable effect is negative. Modification: (i) drop the "$575 vs $450" comparison (premium omitted); (ii) mode (b) (S-A as the risk book in an IRA) is allowed only if the P2 memo shows no fail on G1b(ii) and S-A stays under `satellite_max` of total JARVIS capital (default 25%) unless the owner raises it by a cool-off change; (iii) keep a live-vs-replay tracking-error check if and only if S-A is live; (iv) keep the loss bands and the lifetime stop for any live S-A.
- S01-P2 ACCEPT. Replaces an over-claim ("about half the drawdown") with ranges the specialist opened (Antonacci medians 21.4/53.5 = 0.4). Label that decade-Sharpe 0.13-1.70 is futures-trend evidence (Hurst et al.), not an ETF SMA book; add one line that many exits will look wrong in hindsight (this replaces S01-P8).
- S01-P3 MODIFY. Right to shrink; wrong to defer all deflation math. Modification: build PSR/DSR now (about 30 lines; unit tests already exist at N=46 -> 0.9505), defer MinBTL, PBO, ONC, Galwey. The P2 output is a pre-registered decision memo whose default is "S-A stays in shadow" unless the memo affirmatively clears G1b(ii); failure to clear is not a retirement event but also never a live event without an owner-signed, cooled-off override. Replace "replication since 1973" with the ETF-era window (see S10-P3 vote); the 1973 ladder needs licensed proxies whose terms nobody read.
- S01-P4 ACCEPT. Total-return series and frozen SMA and execution conventions cost 0.5 day and remove a documented false-sell mechanism (S01 estimate y x 4.5/12). The series must be adjusted as of decision date.
- S01-P5 ACCEPT. Cheap harness feature; evidence is one practitioner blog on SPY (19.0% to 30.2% max drawdown across offsets, FETCHED) plus an abstract, so make it report-only and bounded to +1 day. It is a drawdown-language honesty tool, not a gate.
- S01-P6 MODIFY. Accept: no Keller PAA/VAA/DAA/BAA, no dual or relative momentum at launch (turnover 284-523% vs about 70%, FETCHED). Reject the shadow equal-vote 6/9/12-month variant: indirect support only, no head-to-head test, adds a registered trial and invites being read as validated.
- S01-P7 ACCEPT. Features are the trend signal restated, about 1,300 pooled rows, S10's Welch-Goyal evidence agrees. Defer until after L0 and only with spare plan capacity. Keep the idea-ledger row as "deferred".
- S01-P8 REJECT. No evidence opened that showing post-exit returns reduces overrides; S04's evidence (D'Acunto, Sicherman) points the other way: more outcome feedback raises engagement and trading. The pre-registered "many exits look wrong" sentence moves into the Mission Plan text (S01-P2).

### S02 benchmark and portfolio construction

- S02-P1 ACCEPT. Fixing VTI, VEA, IEF, VNQ, a gold fund and SGOV removes open-ended G0 debate and costs 0.088% a year (re-computed: 0.2 x 0.44). Verify each fee and inception on the issuer page in P0, since most came from search summaries (VEA 2007 is RECALLED). Register the gold deviation from Faber's commodity slot as one trial; add a collectibles bucket.
- S02-P2 MODIFY. The proxy idea is right, but with S07-P1 G1a is no longer gating, so the "capped S-A" branch it fixes disappears. Modification: research proxies only for the ETF era (GLD for the gold fund, EFA for VEA, FRED TB3MS converted from discount basis for SGOV; EFA inception 2001-08-14 was FETCHED by S10), report proxy-vs-trade-ticker tracking difference, and adopt S10's rule that proxies may veto but never rescue.
- S02-P3 MODIFY. Label S0 as the like-for-like null, not a recommended portfolio. S0-2F appears only in the Mission Plan stress table, not the weekly memo, to avoid one more number for the owner to chase. No gate, no trial count.
- S02-P4 ACCEPT. Stress-loss dial with round-up to the next 10% and a 10-point hysteresis errs toward safety. The 30% DD_stress in the worked example is a placeholder; it must be computed from the proxy history before any number is shown (a five-asset mix with 60% equity-like assets and REITs will likely show a larger worst drawdown than 30%, RECALLED).
- S02-P5 ACCEPT. The sources do not discriminate between bands, so freezing +/-20% (with the small-account floor) is the right control. The i.i.d. simulation used assumed inputs and is a plausibility check only.
- S02-P6 MODIFY. Evidence is European, indirect and partly secondary. Treat 10:30 ET as a config default tagged DC; keep 10 bps marketable limits, 15:30 latest, never market orders. Pre-register that the first 20 sessions' slippage log decides whether to move it. The blackout shift only matters if a Claude session can be open during a live run (see my additions).

### S03 tax alpha

- S03-P1 MODIFY. Do not build a live harvesting executor: accepted without reservation. Do not add a `harvest_candidate` simulator event either: with no lot engine (see S03-P4 vote) and with taxable holdings kept as S0 only, it has no consumer. Keep the pre-registered build trigger (two years of shadow showing at least 0.30% of capital a year after costs) as text. Evidence on the size of the benefit is an abstract-level extrapolation with an UNVERIFIED haircut.
- S03-P2 MODIFY. Account location is the one tax lever with a mechanism and sources (Dammon-Spatt-Zhang via secondary; Pub. 590-B). Modification: state the capacity bound ($7,500 a year of contributions), make an Alpaca IRA fee check a P0 gate (a $10 fee is 1% of $1,000), keep it an owner decision rather than advice, and replace the ILLUSTRATIVE yields with issuer-published yields in P0. Re-run G3 and L0 for any IRA.
- S03-P3 ACCEPT. A `tax_character` and K-1 field per ETF is 0.5 day and prevents a hidden 28% sale rate and K-1 forms. Residual: the gold-ETF-as-collectible treatment rests on a non-precedential memo and sponsor summaries; flag for the tax professional.
- S03-P4 MODIFY. Default FIFO and make H an output: accepted. But a lot-level simulator is more than a G1b decision memo needs once S-A is shadow. Build a coarse FIFO-aware monthly after-tax estimator with a stated range for the short-term share (0 to 100%), not a lot engine. The P0 lot-method probe is the authority; the forum statement may be out of date.
- S03-P5 MODIFY. Keep the rule, cut the scope to one rule and at most 1 dev-day: no taxable loss sale within 30 days of any purchase, in any registered account or payroll fund, of the same or a mapped-equivalent ticker; defer rather than build warnings. With no harvesting and S0-only taxable holdings, loss sales are rare.
- S03-P6 ACCEPT. A contribution waterfall costs a day, lowers turnover and is the practical form of tax-aware rebalancing at this size.
- S03-P7 ACCEPT. Same decision as S01-P1 mode (a). It is the default when no IRA is available.
- S03-P8 MODIFY. Writing the question list is free. The paid consult is a real owner cost outside the LLM budget, and most questions concern features cut above (substantially identical ETFs for harvesting, 401(k) wash sales). Make it optional before L0 for S0-only, and required before any live taxable S-A or any harvesting. Fold two tax defects into the reduced seeded set (S06-P9), not three.

### S04 behavioural value

- S04-P1 MODIFY. Measuring adherence, override and manual-trade counts and money-weighted minus time-weighted return is code only and is the right way to see the value case without statistics (215 years to detect 1.5 points, re-checked). Reject the clause that adds process measures to the sunset rule: that would let the satellite survive on process while losing after tax. The sunset stays P&L-based against S0-RM; behaviour numbers are reported next to it. The baseline import of 12-24 months of the owner's broker history is optional.
- S04-P2 ACCEPT. Exception-only daily email lowers alert volume (Knight's 97 ignored emails, S09) and engagement-driven trading (D'Acunto, Sicherman, abstracts FETCHED). Liveness stays with Healthchecks, which must stay on so that "no email" cannot mean "silent failure".
- S04-P3 MODIFY. The logic is half right. A veto of a signal exit raises risk and deserves a delay; but the likeliest panic action is selling S0, which is a risk-reducing action the gate allows and must stay one step (FINRA 15-09 kill-switch principle). Apply the 24-hour delay and templated reason to vetoes of S-A exits and to risk-raising dial changes only. No friction on flatten or kill. Delivery mechanism follows S09-P3 (typed confirmation and `effective_after`), not an emailed hash.
- S04-P4 MODIFY. The owner's own crisis letter is a one-day template, sent by code when loss bands trip. The evidence is thin by the specialist's own account, so keep it to onboarding (one letter) and drop pre-mortems at stage steps, since the stage steps shrink.
- S04-P5 ACCEPT. Strongest behavioural proposal, with five FETCHED studies on LLM investment bias (Winder 2025, Lee 2025, Zhi 2025, Sharma 2024). Modifications: run the 30-prompt advice-leak set as an attended plan session (S06-P1 deletes the eval workspace); add a code-checkable denylist in the memo validator (no imperative buy/sell, no bare probability, no price target); say that 30 of 30 passing bounds the failure rate only to about 10% (rule of three), so it is a smoke test, not proof. The "no causal story as fact" item is a DC with no paper.
- S04-P6 MODIFY. The ordering is right on risk grounds: RECOMMEND-live S0 has no code between signal and order. Modification: start RECOMMEND-live as soon as P1a ships, tickers are frozen and the dial is set; do not make the executor conditional on 6 months of adherence data (that delays the owner's stated goal); build the minimal attended executor (S09-P9 scope) next; automation goes live only after GF drills and G3 paper. See conflicts.
- S04-P7 MODIFY. Idea Journal: accept as a minimum build (ideas file, forward scoring, hit rate with confidence interval; no Brier score until about 30 scored ideas). Evidence that it changes behaviour is none (UNVERIFIED). Digest: build it code-only (S05-P6) but keep it off the emailed default.

### S05 LLM agents for quant research

- S05-P1 ACCEPT. Using the raw ledger count for Lab and llm_origin specs costs 1 day and raises the bar by about 0.09 SR between N=20 and N=100 (re-computed 0.29 -> 0.38). It is a stricter rule, which is the safe direction.
- S05-P2 ACCEPT. A planted next-month-return oracle that must be rejected structurally, with an assertion that DSR alone would have passed it, is a 0.5-day test with a clear failure mode; sound regardless of Gencay's exact numbers.
- S05-P3 MODIFY. Good design, but the Lab will be mostly dormant. Build only the pre-registration template and the JSON result contract now; build the rest when the first non-Faber spec appears. Label as DC (soft control: the owner can paste results into a session).
- S05-P4 MODIFY. The "July 2026" clean-slice rule is unusable at monthly frequency (12 observations), so replacing it is reasonable; but the replacement (x2 multiplier) is judgement and weakens a stated control. Add: no llm_origin spec gets live capital on backtest evidence alone; it needs at least 12 monthly forward-shadow decisions and the owner's G0 signature. Named residual: memorised-history selection that the ledger count cannot correct.
- S05-P5 ACCEPT. Replication first, with a planted random spec that must fail and the oracle that must be blocked, is the right way to trust a new harness (Beel: 42% of AI Scientist experiments failed on code errors, FETCHED). Caveat: Faber's tables are images, so the replication target is the text claims (turnover about 70%, drawdown range) plus Antonacci medians, with stated tolerances, not a table match.
- S05-P6 ACCEPT. Code-only digest first; LLM Reader only if the owner asks. Published text-return alpha is short-lived and high-turnover, and the Kim-Muhn-Nikolaev paper is withdrawn (FETCHED). With A1 already called "likely unreachable", the LLM adds only materiality and novelty.
- S05-P7 ACCEPT. Lab capped at 4 sessions a year with a maintenance-mode rule at N=50 states the expected yield honestly (re-computed 0.34 + 1.645 x 0.23 = 0.72).
- S05-P8 MODIFY. Downgrade Red-Team if its marginal catch is zero: accepted. With the API stack gone (S06-P1) the reviewer is an attended advisory subagent. The control I rely on for loosening is not the reviewer: it is the owner-typed change, a written reason and the 72-hour cool-off. Named residual: a loosening can pass without independent review.

### S06 agent architecture and runtime

- S06-P1 MODIFY. Right direction: the T0 cap of $8.40 a year is 47-60% of the satellite's expected loss (re-computed), so the metering plumbing costs more than it governs. Conditions: (i) owner reads the Consumer Terms provisions 7 and 9 and the privacy and training setting before any ledger number goes to the plan (P0); (ii) measure `/usage` per scheduled run in P1a; (iii) the template memo stays the default delivery, so a lapsed plan or a throttled week changes nothing about trading; (iv) keep the number validator and templates (they are the control, not the plumbing).
- S06-P2 MODIFY. Surface assignment accepted. Leave the optional cloud Change-Watch routine off at launch (research preview, egress allowlist unverified, little value over a page-hash email). Probe in P0 whether a Desktop scheduled task can actually be restricted (see S06-P6).
- S06-P3 ACCEPT. On a monthly book, waiting for the owner costs nothing, and it removes the only tool-using LLM from the host that could hold broker keys. Keep the code-computed `cause_enum` runbook step in the alert so response is not blocked on Claude.
- S06-P4 ACCEPT. Six roles with sharp contracts. Keep the Analyst's scheduled memo mode and its interactive `/ask-ledger` mode as two separate definitions with separate tools (S06 itself says so), and keep Reader quarantined and optional.
- S06-P5 ACCEPT. Mechanical post-hoc number check with at most 2 repair passes is the evidence-supported pattern (Huang et al.: no reliable self-correction without external feedback). Specify where it runs (see integration gap in section 5).
- S06-P6 MODIFY. The `dontAsk` mode and `.claude` handling in Desktop tasks are UNVERIFIED. Add a P0 probe; if a Desktop scheduled task cannot be restricted to read-only plus write to its own folder, the Analyst becomes an attended weekly command. It is a weekly job; nothing is lost.
- S06-P7 ACCEPT. Usage credits and spend limit off, at most two scheduled runs a week, Builder has priority, scheduled roles skip when the plan limit is hit. The owner has already hit the limit once, so quota protection matters more than dollars.
- S06-P8 REJECT (at launch). No opened evidence that per-role memory improves outputs here (Reflexion used task feedback such as tests; abstract only), and stale lessons can accumulate or carry injected text. Validator failures are already counted in the report card; add memory files only after a failure recurs three times.
- S06-P9 ACCEPT. Advisory reviewer needs a sanity bar, not a statistical one. 5 of 8 has a wide interval, which should be stated.
- S06-P10 ACCEPT. A 30-item spot check for a digest with no order consumer is proportionate.
- S06-P11 ACCEPT. Invariants: no Claude output relied on for an order; unattended use only through Anthropic's scheduler at most weekly; legal pages in the change watch. The wording of provisions 7 and 9 came through a summariser; the owner reads them.

### S07 validation statistics and gate ladder

- S07-P1 ACCEPT. At N=1, SR 0.4 over 20 years has DSR 0.962 (S07 table), so G1a cannot separate Faber from holding stocks; the benchmark-relative G1b is the real question. Removing the 20-year-history cap is a control removal: named residual is a live S-A on short history; it is covered by `satellite_max` and by S-A being shadow by default.
- S07-P2 ACCEPT. A gate whose pass probability swings from 22% to 71% on luck (re-computed Phi(0.56) = 0.71) is a coin flip. Gate on G1b(ii) only; report (i) and (iii). Print "retire S-A is the modal verdict" in section 1.
- S07-P3 ACCEPT. N = registered cell count (conservative) at launch; White's Reality Check later when a Lab family exceeds 6 variants. `arch` package availability is RECALLED, check before relying.
- S07-P4 MODIFY. Right for the S-A-live branch only; with S01-P1 the default is no live S-A. Where S-A does go live: at least 3 satellite month-end decisions including one change, at least 20 fresh-quote fills, cost test, drawdown below p95, zero severity-1 incidents. `satellite_max` applies to total JARVIS capital across accounts and is raised only by a typed, 72-hour-cooled change. Residual: shorter exposure to regimes; loss bands, tracking error and the lifetime stop remain.
- S07-P5 MODIFY. Two tranches are fine because the per-symbol cap, the entry cap and the 2x modelled-notional cap do not scale with tranche. Modification: tranche 1 is at most 25% and follows one clean paper rebalance and a typed confirmation of the order list; tranche 2 follows one clean live reconcile. The ladder governs only orders JARVIS places.
- S07-P6 MODIFY. The placebo run (about 1,000 strategies with S-A's time in market and block-shuffled signal dates) is the most discriminating test on the list, because it asks whether timing beats random timing at the same exposure. Use it as a one-off false-pass report. Do not use it to set a threshold on the same data; that is tuning.

### S08 crypto and alternative sleeves

- S08-P1 MODIFY. Accept closing the Alpaca-direct crypto branch and dropping the stop-lifecycle paragraph from P3 scope. The Texas claim rests on a search snippet and forum posts (official page 404), so the text must say "unconfirmed; recheck at signup", not "closed".
- S08-P2 REJECT (at launch). It adds a data source whose terms nobody read, a registered Donchian family (trial-count inflation, which S08 itself flags), and a weekly hindsight line ("a 5% BTC sleeve would have changed NAV by $X") that invites the FOMO that S04-P5 bans. Revisit after L0. A static BTC row in the quarterly Mission Plan stress table can come from the stress-loss display in S08-P3.
- S08-P3 ACCEPT. Replaces a 10% trend-overlaid sleeve with a default-off, static, BTC-only 5% cap, buy only at decision windows, no signal exit, with a dollar stress loss shown before signing and 6 clean S0 rebalances required. It lowers risk, and the dollar stakes are small ($50-$500 sleeve). Residual: a -75% BTC move costs 3.75% of the account.
- S08-P4 MODIFY. One `GET /v2/assets/IBIT` probe and one question in the Alpaca email are free and belong in P0. The wash-sale mapping of BTC ETFs is built only when the permission is enabled. The 1099-only rule is shared with S03-P3.
- S08-P5 ACCEPT. One gold ticker, no ablation, no managed-futures sleeve (it duplicates the S-A bet at 8-9 times the fee). The gold slot is a diversification prior, not an evidenced return source; say so.

### S09 operations, security, hosting

- S09-P1 MODIFY. A host-agnostic run-to-completion entrypoint is right whatever the host. Run shadow and paper on private-repo Actions with no payment card and paper keys only. For live, the default is attended execution on the laptop (S09-P9), so the live key never sits in GitHub secrets. Decide whether Actions ever holds a live key only after the 8-10-run reliability log and after the owner reads the runner clause. Single-account risk: one GitHub account would hold code, ledger and schedule; keep a periodic local clone.
- S09-P2 MODIFY. Accepting the replacement of three Windows accounts, the ACL matrix, inbox/outbox, nine trader tasks and the deploy manifest. The real control is "no live key where the Builder runs" plus owner review of the release diff. Required specifics, because this removes an OS boundary: (i) the live key is typed or decrypted only in a terminal with no Claude Code session attached and never written to the dev tree or environment; (ii) production runs from a tagged checkout in a separate virtual environment; (iii) the owner's review is directed at a short list of files (gate, order service, `risk.yaml`) and the Reviewer subagent diff-checks them; (iv) gitleaks and SHA-pinned or no third-party Actions (CVE-2025-30066, FETCHED by S09). Named residual: the live Alpaca key is unscoped (no read-only key exists, design section 6), and a reviewed-but-malicious release could still use it.
- S09-P3 MODIFY. Drop emailed hashes and rotating flatten codes. Replace with typed confirmation at the attended terminal (diff of `risk.yaml` and the reason printed first) plus an `effective_after` date for the 72-hour cool-off; config changes arrive as owner-authored commits to the production repo. Named residual: any agent that can use the owner's loaded SSH key could push a change, so the key must have a passphrase typed per push. Kill and flatten stay one step.
- S09-P4 ACCEPT. For a monthly long/flat book a reconcile break should place no orders, send `/fail`, and re-reconcile on the next run. Keep persistent HALT for kill, lifetime stop and rate breach. Residual: an exit is delayed up to the 5-day window or done by hand.
- S09-P5 MODIFY. Replace the 95% mutation bar with a failure catalogue (unit errors, 100x notional, duplicate ids, stale quotes, double submit, crash between intent and submit) and property tests (Yuan et al., OSDI 2014: over 30% of catastrophic failures preventable by simple tests, abstract FETCHED). Keep GF crash drills. Run mutmut once on the gate diff, non-gating, with survivors reviewed by hand. Residual: weaker evidence of test adequacy on the one module that matters most.
- S09-P6 ACCEPT. Two Healthchecks checks, about two alerts a month each with a runbook line. Knight's 97 ignored emails is the cautionary evidence.
- S09-P7 MODIFY. Git as the hash-chain ledger is fine and saves plumbing. Add: no account numbers or tax identifiers in the repo; a local clone to detect history rewrite; the Desktop Analyst needs a `git pull` before it reads (see integration gap).
- S09-P8 ACCEPT. No Anthropic key on any trading host. Subsumed by S06-P1 and S06-P3.
- S09-P9 MODIFY. The attended executor MVP (minimum control set, about 20-28 dev-days, ESTIMATE) right after P1a is the right shape: the owner starts one command monthly, so no key is stored at rest and no Task Scheduler or DPAPI probe is needed. It is sequenced after RECOMMEND-live S0 (S04-P6) and goes live only after GF drills and G3 paper. Add the typed order-list confirmation for the first live months.

### S10 data and ML lane

- S10-P1 MODIFY. Accept: Tiingo as an in-memory verifier only, no stored research copy, `docs/data_licences.md`, one email to Tiingo support. Gap this creates: ETF history before about 2016 (Alpaca Basic's reach) is needed for the 2004-2026 ETF-era memo. Derived monthly returns are said to be permitted (percentage changes, hashes), but that came through a summariser. The owner reads section 1.6 directly, and the stored research input is monthly returns only.
- S10-P2 ACCEPT. Second vendor optional with a pre-registered fallback (Alpaca SIP close vs IEX-derived close, 30% move check, corporate-actions check, collar). Common-mode vendor error is the accepted residual.
- S10-P3 MODIFY. Accept: choose a gold fund with at least 20 years of proxy history for research, convert TB3MS to bond-equivalent (re-computed 3.81% vs 3.72%), proxies may veto but never rescue. Reject at launch the 1973 proxy ladder: +3 dev-days, MSCI/Nareit/Ken French terms unread, no consumer once G1a is report-only and the ML lane is deferred.
- S10-P4 REJECT (at launch). The ML lane is deferred (S01-P7) and the proxies it would train on are the unlicensed ladder rejected above. Keep as a sentence in the future spec.
- S10-P5 ACCEPT. Baselines (expanding mean, the SMA signal as a binary predictor, 12-month sign), logistic regression as co-primary, LightGBM fixed a priori, expanding walk-forward, block-bootstrap intervals. Costs nothing until built; it is the pre-registration for whenever the lane is built. Welch-Goyal and Goyal-Welch-Zafirov (abstracts FETCHED) set the prior at no skill.
- S10-P6 ACCEPT. Forward scoring cannot adjudicate the lane (AUC SE about 0.025; about 20.6 years to reach it forward; the correlation 0.3 is an assumption). Say it plainly and pre-register the "no skill demonstrated" label.
- S10-P7 MODIFY. Time-box to 5 dev-days, but the timing is S01-P7's: after L0 and only with spare plan capacity, not "after P2". Narrator quotes it only as "exhibit, no demonstrated skill".
- S10-P8 MODIFY. SHAP stability gate (same top three in at least 4 of 5 refits) applies when the lane is built. Until then SHAP does not appear in the memo.

## 3. KEEP as is

1. No Claude output decides, sizes or exits an order. Claude authors, code decides, owner signs.
2. Default-deny gate: allow-list, per-symbol cap, entry-notional cap, 2x modelled-notional cap, collar, per-run order cap, minimum order, marketable limits only, never market orders, broker-side `no_shorting` and margin 1 (Alpaca rejects orders beyond buying power, so a runaway cannot exceed cash).
3. Deterministic `client_order_id`, intent persisted before submit, lookup-before-submit, reconcile-on-start, foreign-order detection.
4. Hash-chained append-only ledger (git is acceptable as the carrier).
5. One-step kill and flatten, HALT for kill/lifetime stop/rate breach, dead-man alert off host.
6. Tighten immediately, loosen slowly (72-hour cool-off from the owner's typed change).
7. S0 as the null and the product; S0-RM as the risk-matched null; the T-bill dial; plain Faber with overlays off; G0 freeze and trial registry; "S-A may fail and S0 runs" as a successful outcome.
8. Per-symbol data-trust gate that blocks only risk-increasing orders.
9. AsOfSnapshot and bitemporal records; CI leak tests (future-poisoning, shuffled labels, one-bar lag, correlation tripwire) plus the planted oracle (S05-P2).
10. Deterministic fallback template for every Claude role; typed whitelisted inputs; mechanical number validator.
11. Monthly cadence, no ETF stops, tax-lot deferral, wash-sale guard across accounts.
12. First action: revoke the leaked OpenAI key; gitleaks; BitLocker; legal perimeter (own money only).
13. GF drills and G3 paper before any live automation; L0 tranches (shortened).
14. The honest section 1 framing: expected effect small and negative in a taxable account, value is discipline, tamper-evident record and learning.

## 4. CUT or simplify

1. Three Windows accounts, ACL matrix, inbox/outbox, nine trader tasks, `JARVIS-Deploy`, manifest-hash HALT (S09-P2).
2. Emailed 6-character hashes, rotating flatten code, 7-day expiry (S09-P3).
3. SAFE with a risk-reducing order class and auto-clear (S09-P4).
4. Gating 95% mutation score (S09-P5).
5. Prepaid API workspaces, the 1%-of-capital cap formula, tiers T0-T2, Batch jobs, eval workspace, Reader submit/collect, unattended Incident Analyst (S06-P1, P3).
6. Live 12.5% satellite, XFER netting, per-sleeve attribution, combined-book wash-sale simulation, G4/G5 ladder as default, S-A tracking-error band while S-A is shadow (S01-P1).
7. G1a as a gate, 20-year-history cap, ONC, Galwey, PBO, MinBTL-as-pass-condition (S07-P1, P3).
8. Lot-level tax engine and TLH executor (S03-P1, P4).
9. LLM Reader, 300-item golden set, A0/A1 ladder, default emailed digest (S05-P6, S06-P10, S04-P7).
10. ML lane build and SHAP in the memo until after L0 (S01-P7).
11. Crypto stop lifecycle, Donchian 10% unlock, crypto shadow family (S08).
12. Seeded-defect bar of 20 (to 8, incl. two tax defects).
13. Band sensitivity work; ledger_ro.sqlite, backup export, anchor email (git instead).
14. Daily digest as a standing email; flatten code and LLM spend lines in it.
15. The 72-row idea ledger as a maintained deliverable: keep as a static document, not a work item.

## 5. Conflicts between proposals, and which wins

1. **S-A live or not.** S01-P1 and S03-P7 (shadow by default) vs S07-P4 (shorten G4, delete G5, `satellite_max`) vs the current G4/G5. Winner: S01-P1. S07-P4 becomes the rule set for the S-A-live branch only.
2. **Deflation machinery.** S01-P3 (defer DSR) vs S07-P1 (print PSR/DSR) vs S05-P1 (raw count). Winner: build PSR/DSR with raw count now (small); defer MinBTL, PBO, ONC, Galwey.
3. **Proxy history.** S02-P2 (research proxies for the ETF era) vs S10-P3 (1973 ladder, +3 days) vs S01-P3 (1973 replication). Winner: S02-P2 ETF-era only, with S10's "veto never rescue". No 1973 ladder at launch.
4. **Path to first live dollars.** S04-P6 (RECOMMEND-live from month 2-3, executor gated on adherence) vs S09-P9 (attended executor right after P1a, L0 near month 6-7) vs the design (L0 at month 12-15). Winner: sequence them. RECOMMEND-live S0 after P1a; attended executor MVP next; automation live only after GF and G3. The executor is not conditional on adherence, because the owner's goal is a working system; it has a stop rule instead (section 6).
5. **Approval mechanism.** S04-P3 (emailed hash, 24 hours) vs S09-P3 (commit or dispatch). Winner: S09-P3's channel with S04-P3's content (templated reason, 24-hour delay), applied to risk-raising deviations only.
6. **API stack.** S06-P1 (delete) vs S04-P5 (eval workspace), S05-P6 (Reader on API at T2), S05-P8 (API Red-Team). Winner: S06-P1. Advice-leak and injection tests run as attended plan sessions.
7. **Lot engine.** S03-P1/P4 (lot-level FIFO simulator, harvest candidates) vs S01-P3 and S01-P1 (tax table, no combined-book simulation). Winner: S01. Coarse monthly estimator with a range.
8. **ML lane timing.** S01-P7 (after L0, spare capacity) vs S10-P7 (5 days after P2) vs S05-P7 (after P2). Winner: S01-P7.
9. **Crypto shadow family.** S08-P2 vs S05-P1 raw trial counts. Winner: S05-P1; no crypto family at launch.
10. **Digest.** S04-P7 (off by default) vs S05-P6 (ship code-only in P1b). Winner: S05-P6 build, S04-P7 default (opt-in).
11. **Sunset rule.** S04-P1 (add process measures) vs the existing P&L-based rule. Winner: existing rule; behaviour numbers are reported beside it.
12. **Red-Team/Reviewer.** S06-P9 (8 defects), S03-P8 (+3 tax defects), S05-P8 (downgrade). Winner: 8 defects including 2 tax; advisory only.
13. **Integration gap, not a conflict.** S09-P7 puts the ledger in GitHub, S09-P1 runs jobs there, S06-P2 runs the Analyst as a Desktop task on the laptop, S06-P5 validates and sends from "trader-side code". Resolution I require: the weekly memo is generated and validated locally after a `git pull` of the ledger repo, delivered as a local file plus optional email through the owner's own mail credentials (not a trading credential). If the pull or validation fails, the templated memo ships.

## 6. My own additions (missed by the specialists)

1. **Terms-and-licences reading list in P0, by eye, dated.** Tiingo ToS 1.6, 5.2, 7.3; Anthropic Consumer Terms provisions 7 and 9 and the training setting; GitHub hosted-runner clause; Alpaca IRA fee, lot method, ETF IRA eligibility and the crypto regions page. Four of the largest proposals (S06-P1, S09-P1, S10-P1, S03-P2) rest on summariser-read or forum-read text.
2. **A claims register.** Every number shown to the owner carries FETCHED-primary, FETCHED-summary or RECALLED, and a RECALLED value cannot gate anything. Headline figures (Faber drawdown, -$14 to -$18, Gencay's numbers) are re-read from the primary source before the owner sees them.
3. **Typed order-list confirmation on every attended live run** for the first six live months: orders, notional, percent of equity, tax lot. A human checkpoint at zero cost is the cheapest control available once execution is attended, and it is what Anthropic's own "human checkpoints" advice (S06, FETCHED) points to.
4. **Attended-live key hygiene.** Live key entered or decrypted only in a terminal with no Claude Code session attached; production runs from a tagged checkout in a separate virtual environment; the Claude Code blackout during a live run is kept (it is free). Residual named: the Alpaca key is unscoped.
5. **Stop rules for the project, not just for S-A.** Month 3: RECOMMEND-live S0 running, or stop building and use the Alpaca app. Month 9: attended executor passes GF and G3, or RECOMMEND stays the permanent product. This replaces the month-15 kill criterion, which came from a plan 1.5-2 times longer. Budget cap for v1: about 80-110 dev-days (my ESTIMATE; the specialists' savings overlap and are not additive, so I do not sum them).
6. **Correct the dial-versus-satellite comparison** (premium forgone) and the IRA capacity bound before either number reaches the owner (section 1 above).
7. **Plan-usage guard as a stop rule.** If Builder sessions are throttled in any week, scheduled roles drop to monthly; Builder has priority. The owner has already hit the limit once.
8. **Data gap for 2004-2016 ETF history** created by S10-P1: stored research input is monthly returns only, and only if the owner's reading of the Tiingo terms confirms derived percentage changes are allowed. Otherwise the memo uses issuer NAV history and FRED where possible.
9. **Missed-month tolerance.** Attended execution on a monthly buy-and-hold null tolerates a missed month (5-day window, then `MISSED_REBALANCE`). This is why attended live is low-risk for S0 and why it would be weaker for a live S-A, which supports S01-P1.

# Verifier: evidence and references (JARVIS-final-architecture.md)

Checked against S01-S10, panel files, briefs 01/02/10/11/16/20/22/23, FINAL-design.md, local Faber text (scratchpad/s01/faber.txt), plus live web checks.

## MUST FIX (changes what the owner would believe, or reverses a source)

1. **Section 4.3 row 13 reverses Ranjan-Gneiting.** The document says "a pooled score cannot be calibrated". Brief 10 F10 (abstract fetched): a linear pool of calibrated forecasts is uncalibrated, and the FIX is to recalibrate the pool on outcomes (beta-transformed linear pool). The paper supports "needs its own calibration data", not "cannot". The paper is also missing from section 16. Dropping the Calibrator is still defensible on data volume, but the citation says the opposite of the paper.
2. **Headline S-A cost (-$14 to -$18; -1.1 to -1.4 points) is shown without its range.** FINAL-design table: taxable range is -2.4 to 0.0 points (-$30 to $0 on the sleeve); brief 18's 0-0.9 hurdle gives a central of about -0.5. S03-P4 says Alpaca FIFO could push the short-term share, and so the hurdle, lower. The architecture states a point estimate as "the expected effect". The conclusion (shadow, retire is modal) survives, but the number should be labelled "design-assumption central case; range -$30 to $0".
3. **"Value of location about $29-$60 a year at $10,000" (section 6) is overstated for the launch configuration.** S03's total includes $13-16 of satellite hurdle removed, which exists only if S-A runs live in an IRA, and the same document says retire is the modal verdict. Core-only value is $17-44. The $7,500 IRA cap also means $10,000 cannot all sit in an IRA in year one. Yields are ILLUSTRATIVE.
4. **Section 4 Narrator row: "Anthropic's own scheduler is the only permitted unattended route".** S06-P11 is an inference from a summariser-read Consumer Terms (provision 7) and the Claude Code legal page. S06 lists "whether setup-token or `claude -p` is explicit permission under provision 7" as an unresolved lawyer or Anthropic-support question. "At most weekly" is S06's design invariant, not a term. The zero-cost agent runtime rests on this, so it must read "S06 interpretation; owner confirms in M0 (O4)".

## SHOULD FIX (overstated, mis-attributed, stale, or tag stronger than the source)

5. **"96 years (S01, S07)".** S01's 96 = (1.96/0.2)^2 is 95% confidence at about 50% power for an information ratio of 0.2. S07 computed 93 / 62 / 31 years at 80% power for a Sharpe difference at rho 0.7 / 0.8 / 0.9. At 80% power the S01 formula gives about 196 years. Two different calculations are merged into one cited number. Say "tens to a couple of hundred years depending on correlation and power".
6. **Yuan et al. OSDI 2014 (row 17) mis-attributed.** The "over 30%" figure in the abstract (fetched live) is for failures that the authors' static checker Aspirator would have prevented. The headline for simple testing is "the majority". Architecture and S09 both say "over 30% preventable by simple tests".
7. **Lopez-Lira and Tang "Sharpe 6.54 to 2.33" (row 25) is stale and selective.** Brief 16 (v6, 28 Oct 2025): subperiod Sharpe 6.54 / 3.68 / 2.33 / 1.22; the gap analysis says "down to 1.22". The 2.33 figure is the v5 endpoint. The live abstract has no Sharpe figures; they come from the body.
8. **Section 1 "no study ... beats buy-and-hold after costs over a long post-cutoff sample (FINSABER, StockBench, CLQT)".**
   - FINSABER is long but pre-cutoff by construction. StockBench is 82 days and, per brief 01's own re-fetch, "all agents underperformed" is too strong (some beat B&H on return).
   - CLQT was read at abstract level only (brief 01: FETCHED abstract, medium confidence). Section 16 tags it plain "FETCHED (brief 01)".
   - Brief 01 says 2026 papers need a full read before numbers are quoted. This is a claim of absence, not evidence of impossibility.
9. **Gencay 2026 is used twice with more weight than its read supports.**
   - The abstract (live fetch) confirms: every LLM-discovered strategy rejected, passive benchmarks certified, a Sharpe-35 oracle passing deflation.
   - Row 2 "ETF trend not certified" rests on a summariser figure (SR 0.49, CI -0.13 to +1.24) from one LLM-search multi-asset experiment. It is not a test of the 10-month SMA. S05 says re-read the PDF before quoting.
10. **MAST "fail 41-87% of the time" (section 4.3 row 1).** The abstract has no failure rates. S06 says the MAST percentages could not be confirmed and does not use them. Brief 02 does not know which systems sit at the ends. This is benchmark failure of open-source frameworks, not a general rate. "3-15x tokens" is not a source figure; Anthropic says about 4x and about 15x.
11. **Narrator "about 70k input tokens a month".** This is the old batch-API memo size (15.6k x 4.33). S06 lists Claude Code per-session harness overhead as unverified, and repair passes add turns. Also unverified: that a Desktop scheduled task can be pinned to Sonnet-class at low effort (section 4 states it as fact; O2 only covers permissions and wake).
12. **"Scheduled roles together roughly $1.5-2 a month (S06)".** S06's figure includes the Reader (456k tokens). At launch the Reader is dormant, so the Narrator-only figure is about $0.25 (FINAL-design). Dollar figures are also API-equivalent, not plan quota.
13. **Reviewer "expect about 5 of 8 caught" (section 4.1).** S06-P9 set 5 of 8 as a pass threshold. The panel hawk wanted no seeded bar, and the sceptic wanted the wide interval stated. Nothing supports an expectation.
14. **Citations that do not support the specific mechanism.**
    - Row 8: the 72-hour cool-off cites Thaler-Benartzi 2004 (a default plus delay for savings) and FINRA 15-09 (algo controls and a kill switch). Neither supports 72 h; S04 itself notes Save More Tomorrow is not technical lock-in. It is a design choice.
    - Row 7 cites Odean 1998 for tax-lot deferral. Row 23 cites D'Acunto and Sicherman for exception-only mail: indirect (robo-advice adoption; login attention).
15. **Behaviour gap "1.2-1.5 points".** Morningstar 1.2 (7.0% vs 8.2%, 10 years to Dec 2024) is confirmed by search, but only the snippet was read. The 1.5 is Vanguard's value of advisor behavioural coaching, a different quantity from a dollar-weighted gap, via a secondary source.
16. **LLM-bias evidence (Winder, Lee, Zhi, Sharma).** S04 says these studied older models and no study covers current Claude as an adviser. The architecture states the conclusion without that limit. Zhi's live abstract names no models; S04's "seven LLMs including Claude-3.5, Gini 0.93-0.94" is not in the abstract.
17. **tau-bench "pass^8 under 25%"** is verified, but it is a 2024 gpt-4o-era retail result used to justify attended-only Incident Triage for current models. Flag as dated.
18. **Gold 28% (row 20).** Topic 409 (fetched live) gives the 28% collectibles maximum but names only coins and art, not gold ETFs. The support is the Chief Counsel memo (verified live: trust holders treated as owning collectibles; CCA, not citable as precedent) plus sponsor FAQs. The wording is fine in section 6; row 20 should not imply Topic 409 covers ETFs.
19. **KMN "withdrawn" (row 25).** The author's page (fetched live) says "temporarily withdrawn ... while we review"; it gives no date. S05 also flagged this.
20. **DeMiguel (row 2) "1/N not beaten".** S02: datasets are equity-style, so the paper supports "do not optimise weights", not that 20% in each of five asset classes is a good portfolio. Caveat omitted.
21. **Dev-day totals (36-48 / 56-76) and the $2.64 laptop power.** The totals are a bottom-up sum of the architect's own M0-M4 estimates; the arithmetic adds (3+8+6+7+12 = 36; 4+10+8+10+16 = 48). No source or reference class supports them. The power figure assumes a 20 W always-on laptop (brief 23 assumption), while the design says no resident server.
22. **Reference list hygiene.**
    - Sources listed but never cited in the body: Hurst, Moskowitz, Lempérière, Kurth, Asness, Keller, Israel-Kelly-Moskowitz, McLean-Pontiff, and others.
    - Cited in the body but missing from the list: Ranjan-Gneiting, Gu-Kelly-Xiu, Doeswijk.
    - Kurth et al. (live abstract) contrast small-tick vs large-tick contracts, not short vs long lookbacks as S01-R3 phrased it.
    - "FETCHED" is used for abstract-only and summariser reads without a consistent suffix (Antonacci, Huang, Chaudhuri, Vanguard).
23. **"Roughly halves drawdowns" vs the cited ratios.** Antonacci's 0.4 and Faber's text (46% to under 10%, about 0.2) are both stronger than "halves". The two figures come from different rules and periods: Antonacci's is 12-month absolute momentum, Faber's is the SMA10 book including GSCI.

## VERIFIED (no action)
- Faber text (local s01/faber.txt): "reduced from 46% to less than 10%", 70% turnover, 3-4 round trips a year. Faber SSRN was unreadable for S02 and S10, but S01's FETCHED tag is correct.
- Live: Gencay abstract; Beel (42% coding failures); tau-bench (<50%, pass^8 <25%); Knight (97 automated emails, $12M); Lee et al. (ICAIF); Zhi et al. (567,000 samples); Kurth et al. exists (July 2026); Huang et al. JFE 2020; KMN page; IRS Chief Counsel memo; Morningstar 1.2.
- DSR 0.9505 at N=46 (S07 read the paper text). Dial formula and example (b = 0.40). 0.088% blended fee. TB3MS 3.72% to 3.81%. $8.40 = 47-60% of $14-18. 15.6k x 4.33 = 68k. 25% satellite at 1.1-1.4 points = $28-35. Rule of three = 10%. EFA 2001-08-14 (fetched by S10; S02 had RECALLED it). VEA 2007 honestly tagged RECALLED.
- Knight, FINRA 15-09, Yuan (qualitatively) and tau-bench support the design directions they are cited for.

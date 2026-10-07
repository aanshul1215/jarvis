# Red-team: evidence consistency of SYNTHESIS-v1 (2026-10-01)

Scope: every factual claim, number and rule in SYNTHESIS-v1.md checked against 00, 00b and briefs 01, 06, 12, 18-23 (plus 08, 13, 14, 15, 17 by search). Items the evidence confirms are not listed. Overall: the architecture follows the evidence well; most problems are overstated certainty, a broken headline calculation, one gate step that violates brief 20, and a few claims no brief supports.

## MUST FIX

1. **Section 1 headline calculation is internally inconsistent.**
   - Text: hurdle +1.0 to +1.3 points (brief 19), strategy -1 to +1 pre-tax (brief 18), central -0.7, range -2.4 to +0.9, "$74 to $129 at $10,000".
   - A 0 central pre-tax edge minus a 1.0-1.3 hurdle gives -1.0 to -1.3, not -0.7. The -0.7 comes from the economics critic's 0.65 hurdle, which is the midpoint of an invented 0-1.3 range. Brief 19 does not give a 0.65 hurdle.
   - The +0.9 top end needs a zero tax hurdle, which contradicts the stated 1.0-1.3.
   - -$74 to -$129 is -0.74 to -1.29 points. That is the central edge at hurdle 0.65 and 1.3, not the stated -2.4 to +0.9 range (which is -$240 to +$90).
   - Brief 19's own numbers: 1.03-1.26 (cases B, C), 1.09 (A), 1.19 (D), 2.57 (case E, 32% bracket plus NIIT), 1.26-1.51 at 20 years; 00b says 1.0-1.5. All assume 100% short-term realisation at 8% gross. Brief 18 says the true gap for a Faber-type strategy is between 0 and 0.9. The two briefs are not reconciled in the text.
   - Fix: state the inputs and the arithmetic once. Either use hurdle 1.0-1.3 (central about -1.1 to -1.4 with cost) or hurdle 0-0.9 per brief 18 (central about -0.5). Make the dollar range match the percentage range. Mark the whole thing ESTIMATE.

2. **Section 1 and section 2/12 lean on "No LLM trader has beaten buy-and-hold net of cost after its cutoff (brief 01)".**
   - Brief 01's actual statement: "No study I could open shows an LLM trading agent beating buy-and-hold net of costs over a multi-year, multi-symbol, post-cutoff sample."
   - The forward tests it cites are 50-82 days (StockBench 82 days, LiveTradeBench 50 days), mostly no costs, and underpowered. Alpha Arena (secondary, UNVERIFIED) had two of six models finishing up.
   - Absence of a shown edge is not shown absence. Correct wording: "no study has shown...", with the qualifiers.
   - The same sentence in D2 ("evidence rules Claude out of selecting, sizing and exiting", briefs 01, 02, 10) should read "gives no support for, and CLQT/AlphaForgeBench show instability".

3. **G5 scale-up step breaks brief 20.** The synthesis has `stage_fraction` 20 -> 50 -> 100%. Brief 20 G5: 25 -> 50 -> 100%, "no more than 2x per step". 20 -> 50% is 2.5x. Fix: 20 -> 40 -> 80 -> 100, or 25-based steps, or state the deviation and reason.

## SHOULD FIX

4. **"JARVIS delivers drawdown control" (section 1) is unproven.** Brief 18 gives "about half the drawdown" as an ESTIMATE extrapolated from Faber's self-reported figures (tables were images; no numbers read) and one unverified blog (dual momentum: max drawdown -20% vs -24%, CAGR 8.4% vs 13.6%, 2014-2026). Huang-Li-Wang-Zhou found little evidence for time-series momentum asset by asset. Also, the "-1 to +1" figure is not marked ESTIMATE, and the evidence grade (brief 18: medium, extrapolation, post-publication data lags) is missing. G1b may well fail. Say "expected, unverified" rather than "delivers".

5. **O15 is stale and G1c is mis-framed.** Brief 20 fetched and read the primary DSR, PSR/MinTRL, MinBTL, PBO and HLZ papers (preprint versions) and verified the arithmetic. Brief 08 said "recalled"; the synthesis follows 08. Correct: formulas were read from preprints (equation and page numbers may differ in print); Lo-LdP ONC and Harvey-Liu "Backtesting" were not re-verified. The remaining job is a null simulation, not "check against the papers".

6. **G1a relaxation and dropped G1 items.**
   - Brief 20: DSR 0.90 only for "a pre-registered published design with N_eff <= 5". The synthesis says "only with no overlays", dropping the N_eff <= 5 condition. Brief 20's own verification says the 0.90 relaxation, plateau (80% / 0.6x), 70% holdout and 70% window thresholds have no source.
   - Brief 20 G1 items 4-5 (frozen-parameter holdout by asset class; positive net SR in at least 70% of non-overlapping 5-year windows; costs doubled keeps SR at least 0.75x) are silently absent from section 7.
   - "At least 3 independent bear episodes, counted" is not in any brief and is not tagged (DC).
   - G1 SR thresholds should be stated as a function of N_eff (brief 20 verification: about 0.55 at N_eff 5 / 30y; about 0.70 at N_eff 20 / 20y), not a bare DSR >= 0.95.

7. **G4 deviates from brief 20 without checking its power.**
   - Brief 20: 5-10% of capital (about $500-1,000), cost gate at realised <= 1.5x model, SE 2.2 bps with n = 20 and an assumed sd of 10 bps.
   - Synthesis: max(20%, $200) and a fixed "average <= 10 bps per fill". Brief 18's ETF cost model is about 2 bps a leg (0.03% a year; 0.14% at 10 bps a leg), so 10 bps is the pessimistic case. The test would pass a cost 5x the model.
   - "1.5x test applies to crypto only" drops the evidence-backed form. Keep a ratio test (<= 1.5x model) as well as the absolute cap, and state the sd assumption.

8. **Nightly Narrator unlock "capital >= $2,400" does not match its own pricing basis.** $2,400 is brief 22's capital for b1 (Haiku 4.5 extraction of 100 items plus 3 filings, about $4/month). The synthesis says to budget at Sonnet-class rates (b2, about $9.4/month, capital $5,600 per brief 22). The Narrator alone is about $0.03 a night (about $0.65/month, capital about $390). Pick one basis and say which workload the number prices.

9. **O1 "$13-50/month if no plan" understates and is partly unsupported.** Brief 22 priced only a weekly research session: $12.8 (Sonnet), $21.3 (Opus), $41.6 (heavy). It did not price Builder (all code, 115-150 dev-days), monthly Lab, or `/ask-ledger`. The "$50" top end is not in the brief. The build-phase API cost is unpriced. Say "unpriced; at least $13/month for one weekly session".

10. **Production LLM path rests on an unflagged terms question.** Brief 22: the Commercial Terms say services are "not for consumer use" and a personal API account is a gray area it could not resolve. The minimum prepaid purchase and evaluation-tier limits are UNVERIFIED (a minimum purchase could exceed many months of the $0.83/month cap at $1,000). O5 covers only Consumer Terms 3(9), and brief 22 notes the 3(7)/3(9) section numbers were not visible. Add an open item and drop the section numbers or mark them unconfirmed.

11. **Off-host hash anchor is unsupported.** "Success ping carries the head hash, which anchors it off-host" assumes Healthchecks stores a ping body. Brief 23 read only the pricing page: free tier keeps 100 log entries per check, and /start and /fail semantics are RECALLED. With daily pings the anchor window is about 100 days. Mark UNVERIFIED and state the retention limit, or anchor elsewhere.

12. **A0 "nothing needs hand-labelling".** Brief 22: golden set "partly deterministic" (8-K item numbers, Form 4 codes). Reader outputs `materiality`, `novelty`, `instruction_like_text`, and processes Alpaca headlines; none has EDGAR-derived labels. Hand-labelling is needed for those fields.

13. **Crypto hurdle "3.2-4.1 points" priced on the wrong route.** It is brief 19's tax hurdle for a BTC-like 15% gross (2.47-2.93) plus brief 18's Alpaca-spot costs (0.7-1.2%). The unlock described is spot BTC/ETH ETFs at equity costs, so the cost part does not apply (about 2.5-2.9 plus a few bps). Also brief 18 rests Donchian on one non-peer-reviewed working paper with only 10 bps net results; say so.

14. **Texas and Alpaca crypto.** The synthesis says Texas is "unknown". Brief 21: the latest (28 jurisdictions, October 2025, search-snippet, unconfirmed) list does not include TX. Say "TX is absent from the last list seen; unconfirmed; check at signup". The conditional treatment is right; the "unknown" is soft.

15. **Cross-account wash-sale guard (brief 19, item 4) omitted for the design's own S0/S-A split.** With S-A in an IRA and S0 in a taxable account holding the same ETFs, a taxable loss sale within 30 days of an IRA buy is permanently lost (Rev. Rul. 2008-5). The synthesis mentions the guard only for a discretionary account. Also 1099-B reports wash sales only same account / same CUSIP (brief 19).

16. **"The owner's 20 names" (section 5)** has no source: the owner's documents and context list only TSLA. The "20" comes from proposal A and brief 22's assumption (about 20 symbols). Remove or mark as an assumption.

17. **Statements no brief supports, stated as fact.**
   - "Alpaca keys cannot be scoped" (brief 23: "found no evidence of read-only keys"; an IP-allowlist field exists but is disabled per a June 2026 forum post). Make it "no read-only or scoped key found".
   - "The Alpaca app's cancel-all also removes stops".
   - "Alpaca trade confirmations sent to a separate inbox as an independent witness".
   - "Alpaca account activities" endpoint and fields (no brief).
   - "About 0.5 GB per run" (no measurement).
   - "Public ntfy" topics: brief 23 says the topic name acts as the password; a status feed with NAV and trades should be content-free or self-hosted.

18. **Unmarked design choices.** The preamble says (DC) marks non-literature choices, yet these have no tag: data-trust 0.5% and 30% thresholds, cash tolerance max($1, 0.1%), 20% S0 no-trade band (brief 18 uses 20% only for the crypto sleeve), "alarm at accuracy > 60%" (brief 08 says 60%, brief 15 says about 55%, both flagged as judgement), 25% satellite loss "fresh G1" (brief 20 gives the 25% deployed-capital lifetime stop but not a fresh-G1 rule; it also adds a tracking-error red trigger the synthesis omits). The "back to about 2016" row cites (21); the source is brief 06.

19. **Section 11 skips brief 04's spike.** Gap analysis item 5 keeps the one-to-two-week spike as the confirmation of the thin-executor choice. The synthesis records it as skipped with only "thin daily executor" as the reason. Acceptable if the P3 build is treated as the spike, but say so.

## Checked and consistent (no action)

Cap arithmetic ($0.83 / $4.17 / $8.33); $2,400 = 600 x $4; Norgate $31,500 and SIP $59,400 (600 x brief 06 prices); Haiku 4.5 floor 2026-10-15; 29-day batch retention; Alpaca fee/order facts (fractional DAY only, GTC 90 days, 403 self-cross, no cash accounts, margin 1x below $2,000); agreement s.32 and the "own computer" disclosure; legal-perimeter five triggers (brief 12 s2.4); v1 key at line 597 of jarvis_backend.py (confirmed in the file, in a commented line); G2/G3 criteria; yellow/red bands; dev-day sum 114-152; $0.83-$8.33 vs 1% rule; D14 6-18%.

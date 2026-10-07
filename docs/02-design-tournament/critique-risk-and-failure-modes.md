# Critique: risk and failure modes (critic lens)

Date 2026-10-01. Checked against briefs 12 (risk controls, Knight/Citi), 17 (execution, F17-F22), 23 (hosting/liveness), with 21 (Alpaca specifics) and 22 (LLM cost) where needed. "Brief 12 mandatory subset" = items 2,3,4,5,6,7,12,13,14,15,17 plus the runbook (brief 12 section 4.2).

## Bottom line

All five proposals made the same big correct moves: run-to-completion job, broker is truth, intent row before broker call, deterministic client_order_id with lookup-before-resubmit, default-deny gate with erroneous-order family, no LLM on the order path, no degraded-data override (except one slip in C), dead-man's switch off-host. None has a flaw that is fatal in the strict sense (loses money by design, breaks a binding constraint, or cannot be built). They differ in how many named disasters they actually walk through. D is the only one organised around disasters; B is the leanest and therefore has the fewest untested moving parts; A has the most surface for the least gain.

Ranking through this lens: D 8, B 7, C 6.5, E 5.5, A 5.

## Disaster walk-throughs (what stops each, per proposal)

### 1. Duplicate order

Common design: intent row, `client_order_id` = hash(decision, leg, attempt), look up by id before resubmit, poll to terminal, single-instance lock. Brief 17 F18 / brief 21 / brief 23: Alpaca duplicate-id response is undocumented, so the lookup, not the rejection, is the control. Holes found:

- **"attempt" semantics (B, D, E).** `hash(decision, leg, attempt)`: if attempt increments after a timeout and the lookup of the previous attempt's id has not returned a terminal state, the retry has a new id and the idempotency is gone. Nobody says attempt increments only after the prior id is confirmed terminal-cancelled/rejected. A and C say "deterministic id" without defining attempt (not better, just silent).
- **Stacked relaunch mechanisms (all).** RestartOnFailure + StartWhenAvailable + the explicit "retry an hour later" are three independent ways the job starts again (brief 23). All rely on the file lock plus "exit if intents complete". "Complete" is never defined: is an expired unfilled DAY limit "complete"? If yes, a monthly exit order that did not fill is never retried until next month (see miss M5).
- **Stale intents (A, B, E).** A, B and E split compute (evening) and submit (next morning). Nobody states an intent TTL or that the gate and price collar are re-evaluated at submit time on a fresh quote. StartWhenAvailable (brief 23) will run a missed morning job late; a Friday intent can be sent Monday afternoon. D partly covers this with a 09:45-15:30 ET window and an as-of snapshot per run.
- **Host migration (all).** Every proposal moves the job to a VM after "2 missed runs" or before crypto. None gives a cutover procedure. If the laptop task and the VM timer both exist for an hour with the same live key, that is a duplicate-order generator. "Live key on one host only" is stated (A, B, D, E) but no step says rotate the key at cutover.
- **Alpaca probe timing.** A, B, C probe duplicate-id behaviour in P0. D and E leave it to the failure drills (D's GF in P2, E's G3), which is acceptable only because both gate live on the drills.

Verdict: C and A adequate, B/D/E adequate with the attempt fix, none complete.

### 2. Host dies with an open crypto position

Facts (brief 23, 17 F17): Alpaca crypto has no bracket/OCO, only GTC stop-limit; a stop-limit can gap through unfilled; stops can lapse; the stop may have filled while the ledger still says "holding"; the 20% cap and 30% gap are illustrative, not evidence.

- **A:** best numerics. Crypto sleeve 10% at launch, gap rule "a 30% overnight crypto gap must cost <= 3% of equity", move to VM before first live crypto position. Good. But the roster schedules a "00:05 UTC crypto run" on the laptop in the same table, so the migration trigger is the only thing keeping crypto off the laptop.
- **D:** strongest gating: crypto starts only if Texas confirmed AND host moved AND S-A passed G4, sleeve 10% -> 20%, -25%/-28% stop-limit, separate "stops verified" Healthchecks check. Best of the five.
- **B, C, E:** sleeve cap 20% at launch with a stated 6% worst case (20% x 30%). That is the same 6% as brief 23's illustrative arithmetic, fine, but it is a gap-only bound; it ignores a stop-limit that triggers and does not fill (price below limit), where the loss is open-ended until the next run. A and D's lower launch cap is safer. C and E both defer crypto behind conditions, B conditions it too; acceptable.
- **Not covered by anyone:** (a) a resting stop-limit locks the quantity (brief 23 open item "quantity locking when a resting sell holds the position"), so a signal exit must cancel the stop first; if the host dies between "cancel stop" and "sell" the position is naked. (b) A stop-limit fill is a taker fill at 0.25% (brief 17 F11), so the catastrophe stop is a cost event, not free. (c) After a stop-out the next daily signal may say long again and re-enter; no cooling-off (brief 17 rec 5).

### 3. Stale data / bad price

- **Collar reference is a single free feed (all).** Price collars use "a quote no older than 60 s" from Alpaca Basic, which is IEX-only (about 2.5% of volume; brief 12 verification #4, brief 06 per gap analysis). A stale or thin IEX quote on a low-volume ETF either blocks the order (safe, but a missed rebalance) or sets a collar around a non-NBBO price. Cross-checks named (Tiingo EOD) are end-of-day, so they cannot validate the 09:45 execution price. Only the crypto path has a live second source (Coinbase/Kraken). Nobody notes this asymmetry.
- **Tiingo EOD timing vs a 16:45 ET job (A, B).** A and B compare Alpaca vs Tiingo closes in a 16:45 ET job. Whether Tiingo's EOD bar is published by then is not in the proposals or the briefs I read; if not, the gate either always fails or compares to yesterday. Conditional, but a plausible permanent-SAFE bug. E uses 18:00 CT, D uses 10:00 ET next day (better).
- **Exits on untrusted data (A, B).** A: "SAFE (no new risk; exits allowed)". B: "DATA-UNTRUSTED: no new risk, while exits ... continue". An exit signal computed from the same untrusted close is allowed to sell a whole sleeve; a bad close just under the SMA liquidates a 25-30% slot (short-term gain, round-trip cost, re-entry whipsaw). The exceptions that should still run are stop re-arming and reconciliation, not signal-driven exits. D's "skip the run" is the other extreme (see D flaws). Best fix: signal exits allowed only if two sources agree; protection checks always run.
- **Corporate actions (B, E, A, C):** a missed split looks like -50% and flips the SMA signal. Only D has "moves over 30% without a corporate action quarantined".
- **Signal-day single point of failure (all).** Every strategy signals "on the month-end close". If data fails on that day and the retry also fails, nothing says the system evaluates the signal on the next trading day with month-end as-of data. A one-day outage can become a one-month stale posture, and in a crash month that is the exact failure the strategy exists to avoid. Nobody has a catch-up rule.

### 4. Runaway loop

- **Order-count caps all exist** (A 20/day; B 20/day, 5 cancels/min; C 12/run, 20/day; D 20/run, 40/day, turnover <=100%/run; E 12/run, 20/day) and per-order notional caps. Good, and these are the Knight-type controls.
- **All of them live in the same package and the same SQLite as the loop.** Brief 12 item 14 asks for a watchdog "ideally off the laptop" that cancels orders; every proposal's off-host element (Healthchecks) only detects silence. A runaway job pings success and the dead-man's switch is happy. Brief 12's Knight lesson is "alerts must page a human and/or auto-halt"; here it is page-only. The honest trade-off (no read-only Alpaca keys, brief 23, so an off-host watcher needs a full trading key) is not discussed by any proposal.
- **Kill switch cancels the protective stops (A, B, C, D, E).** `jarvis kill` = "cancel all, block new" via `DELETE /v2/orders` (D names it). That also cancels the catastrophe stops, leaving every position naked at the moment the owner distrusts the system. Flatten is a separate command, rate-limited by "market orders rejected in extended hours" (brief 17 F21). None says kill must cancel only non-protective orders, or re-arm stops after cancel. This is a real design defect in all five.
- **Exit race creating an accidental short (A, B, C, D):** whole-share GTC stop plus a signal-flip sell. If the system cancels the stop and sells, the stop may fill during pending_cancel, then the sell also fills, producing a short or a rejected order (brief 17 F20, rec 8: "do not submit a new order for the same exposure until the old one is in a terminal state"). A forum report in brief 17 describes this exact double-sell. The gate's "no shorting" and "sell <= broker position" rules help only if the sell quantity is recomputed from broker position after the stop is terminal. None specifies the sequence. None uses OTO/bracket (brief 17 rec 8) so entry and stop are atomic; instead stops are placed after the fill, leaving a window with an unprotected position.
- **LLM spend runaway:** only D scales the cap to capital (`min($15, 2% x capital / 12)`, prepaid balance as the real ceiling; brief 22 and brief 11 rule). A: $15 workspace limit at $1,000 is an 18% annual drag if reached (A's own arithmetic says $0.65/month is what is intended); C $10; E $5; B $5 only when capital >= $2,500. A cap 10-20x the intended spend is not a cap.
- **Rebalance churn loop (D):** "rebalance only on >5-point drift" with whole-share lots on a $1,000 book (see D flaws) can oscillate. B's 20% band avoids this.

### 5. Owner override

- **D is the only proposal that answers it** (F11): tighten at once, loosen only after 72 h with a Red-Team note, owner may veto but never add (veto counterfactual logged), manual trade in the account triggers SAFE and discretionary trades go to a separate account, no return-target field. This is exactly the revenge-trading failure and it is the best single idea in the tournament for this lens.
- **A, B, C, E:** the owner can sign a config change, effective next session, with no delay and no friction, in the middle of a drawdown. Re-arm after a halt is a one-step action in all of them. Brief 12 / FINRA 15-09: "controls on anyone's ability to override system controls"; Citi's failure was an overridable warning.
- **Owner trading by hand in the Alpaca app (A, B, C, E):** the likely real behaviour at -15%. Reconcile mismatch sends the system to SAFE/HALT but no proposal says what happens after the owner re-arms (re-buy contrary to the owner's sale? adopt the orphan, which brief 23's skeleton literally says "adopt or cancel orphans"?). A also puts owner names (TSLA) on an anomaly watchlist that reports "watch items", which invites discretionary trades in the same account.
- **Reconcile cannot tell own stop fills from foreign trades (A, B, C, E):** B says "Any mismatch sets HALT". A broker-resting stop that fills while the host is down is a legitimate mismatch (brief 23 residual risk 5). If it halts the system, every stop-out needs an owner re-arm. Only D distinguishes "unknown order or position (a manual trade)".

## Per-proposal attack

### A-vision-faithful (score 5)

Handles the named disasters at the same level as B/C but with the widest surface: 16 flow steps, six Claude agents, scanner plus anomaly watch, evidence card, red-team reviewer, four separately scheduled tasks (16:45 ET, 09:45 ET, 00:05 UTC, 07:00 local) each needing a heartbeat, lock and retry. Knight's lesson (brief 12) is that dead code and extra paths are the failure; A's own risk 1 says the vocabulary invites rebuilding the expensive version.

Serious flaws:
- Two-stage compute/submit (16:45 ET intents, 09:45 ET orders): no intent TTL, no submit-time gate re-run (quoted: "16:45 ET equity scan + LLM batch submit; 09:45 ET next session equity orders"). StartWhenAvailable can fire stale intents (brief 23).
- "SAFE ... exits allowed" on untrusted data (section 2 step 3 and section 6). Signal exits from bad data are permitted.
- Kill switch cancels protective stops (section 6 System line). Brief 17 F21.
- `$15/month` workspace cap at $1,000 capital is 18% a year; only the Narrator should run (A states $0.65).
- No written runbook, no deploy discipline, no restore drill, no foreign-trade rule. Misses brief 12 items 16 and the runbook.
- Fractional slots "explicitly accepted as unprotected" while the 25%-per-symbol cap allows a $2,500 unprotected ETF position at $10,000. Acceptable for a diversified ETF, but state it as drift toward buy-and-hold, which is what it is.

Strengths: the crypto gap rule (sleeve sized so a 30% gap costs <= 3% of equity) is the only explicit quantification of host-death crypto risk; "SAFE or reconciliation break blocks entries but never forces exits"; approvals expire to reject; "No override exists for degraded data or the gate."

### B-evidence-minimal (score 7)

Fewest moving parts, so least to go wrong. LLM fully off the money, $0 at launch, whole-share-only so every overnight holding can carry a resting GTC stop (resolves gap item 15), 20% no-trade band, approvals for risk-increasing orders in the first live rebalances while risk-reducing orders never wait, bootstrap drawdown bands in dollars.

Serious flaws:
- **Whole-share rounding at $1,000.** Quoted: "Share classes are chosen so that whole-share rounding stays under 10% of each target weight." With a 4-ETF book at 25-30% weights ($250-$300 slots), a 10% tolerance is about $25, so only ETFs priced below roughly $50 qualify. Whether enough liquid ETFs in the needed asset classes are that cheap is not in the evidence base; if not, at $1,000 the book is mostly cash, or the live book diverges from the G1 and Strategy 0 comparison. Conditional but consequential, and it silently removes the "BTC off, 4 assets" claim at the smallest capital.
- **"Any mismatch sets HALT (exits only)"** cannot distinguish a legitimate stop fill (brief 23 risk 5), a partial fill or a corporate action from a foreign trade.
- **Two daily jobs (10:15 and 16:45 ET), each with a retry**, plus Task Scheduler restart: the intent TTL and complete-definition gap above.
- **DATA-UNTRUSTED allows signal exits** ("exits and stop re-arming continue").
- **Kill cancels stops** (section 6: `jarvis kill` cancels everything). Same as all.
- **Builder agent and live key on the same Windows user** ("B0 Builder ... Forbidden: Seeing live keys" is a policy, brief 23 says DPAPI user scope is readable by any process as that user). Claude Code sessions read untrusted material on that account. Only C separates users.
- **Dev tree = prod tree not ruled out**, no deploy handshake (brief 12 item 16).
- 20% crypto cap at launch if B passes, vs 10% in A/D.

Strengths: whole-share-only intent; the sleeve/risk table with dollar caps for $1,000 and $10,000; "approvals ... pending rows that expire to reject; risk-reducing orders never wait"; Strategy 0 as a valid outcome so there is no pressure to trade.

### C-agents-as-quant-team (score 6.5)

Strongest security posture: the live key exists only under a separate Windows user `jarvis-trader` and "the owner's Claude Code account must not share that user" (brief 23 DPAPI limitation); Claude Code permission rules plus a deny-by-default PreToolUse hook; the quarantined Reader with no tools and enumerated-field output; lethal-trifecta partitioning (brief 13). That is the right answer to "an agent with a shell and live keys", and no other proposal enforces it.

Serious flaws:
- **Internal contradiction on the override path.** Flow step 5: "Data-Quality Triage ... Only the owner can release [quarantined rows]." Section 10 says the Data Trust Gate has its "override path removed". Brief 12 says the degraded-data override is an override of a hard control and should be removed. As written, an owner-released quarantine feeds bad data to the signal.
- **Fractional lots carry no stop** and C states "At $1,000 most of the book will be fractional; this is accepted". At the smallest capital the whole ETF book has no broker protection during host death, so the Windows laptop, which brief 23 says may sleep, update-restart, or Modern Standby, is the only line of defence. A and C differ from B and D here, B/D choose whole shares.
- Nine agents and a weekly attended session for a solo developer on 8 GB: "Run at most one session plus one subagent, never during the run window" is a discipline rule, not a control; a Claude Code session of about 1 GB (C's own estimate) on the same 8 GB laptop during a 10:00 run is the sort of resource contention that causes a skipped run.
- Kill cancels stops; reconcile mismatch conflation; no deploy discipline; $10 API cap unscaled.
- The Incident Diagnostician reading "redacted broker snapshot" is fine, but it is a second LLM-on-private-data path; C itself says no agent should combine private data, untrusted content and outbound sending. The Diagnostician reads logs that may contain exchange or vendor text; low risk but not zero.

Strengths: key separation, deny hooks, injection partitioning, numeric validation of Narrator, rebalance only on >25% drift (churn control), 12 orders per run.

### D-failure-first (score 8)

The only proposal that starts from named failures and maps each control to one (F1-F14), includes a drill gate (GF: kill mid-order, duplicate id, network drop, stale feed, broker 5xx, partial fill, replace race, reconciliation mismatch, foreign manual order, clock skew, restore from backup, kill switch, dead-man alert reaching the phone), deploy discipline (tagged versions, config-hash handshake, no deploy while orders working, first run at half size, no dead code or reused flags, directly from the Knight post-mortem, brief 12 item 16), hash-chained ledger, a separate "stops verified" heartbeat, a weekly silence test, capital-scaled LLM cap, 72-hour loosening delay, and crypto gated behind host move plus G4. This covers every item of brief 12's mandatory subset and the runbook.

Serious flaws (it still has them):
- **"Any failure skips the run"** on data trust (step 4) means step 13 (protection check and stop re-arm) is skipped too. GTC stops expire at 90 days and a missing stop is only re-armed on a run that passes the data gate. Protection verification should be independent of the data gate (A and B keep re-arming in untrusted state).
- **Rebalance on ">5-point drift"** plus "fewer and cheaper ETFs so that whole-share weights land within 5 points of target": at $1,000, a 5-point band is $50, which a whole-share lot of most liquid ETFs cannot hit. Result: perpetual drift above 5 points and daily trade attempts, throttled only by the cost gate. B's 20% band is the safer number (A/C use 20%/25%).
- **Kill = `DELETE /v2/orders`** (section 6) cancels the catastrophe stops it just described. The Alpaca app as off-host fallback is good, but it too cancels stops.
- **Drill list and controls are a lot for a solo developer**; D says so in risk 2 (P2 unfinished by week 12 is a failure signal). The risk is real: 14 failure classes and 13 drills built by one person is the path to a bypass. Mitigation: build in the order of brief 12's mandatory subset.
- Duplicate-id probe not in P0 (it is in GF); acceptable.
- "Wallet whitelisting stays off, because a leaked key can add whitelist entries": this should read transfers/wallet endpoints stay unused; the sentence is ambiguous and the facts are in brief 23.

### E-staged-platform (score 5.5)

Failure-lens problems come from what the staged design leaves out at launch, not from over-reaching.

Serious flaws:
- **No resting protection at all on the ETF book at launch**: "Most legs at this size are fractional, hence DAY-only ... no stop can rest at the broker; the owner accepts this explicitly, backed by diversification, the drawdown halt and the lifetime stop." The drawdown halt and lifetime stop run on the same host that is dead in this scenario. The only protection against a dead host is the owner reading an alert.
- **Dead-man alert "after 2 missed pings"** (section 6 table). For a daily job that is 48 hours. Brief 23 specifies a 2-hour grace on a daily cron. If E means two missed pings at the daily cadence, the alert is late by a day; the text should say grace, not pings.
- **Evening/morning split** with no intent TTL or submit-time gate (same as A/B).
- No runbook, no deploy discipline, no key/user separation, no foreign-trade handling, no restore drill. "Stage" frameworks multiply interfaces (frozen contracts, evidence objects, agent slots) before the plumbing is proven; E's own risk 1 concedes P0-P3 overbuild.
- Agent ladder A3 lets text-derived evidence change a leg's size by up to +/-25%. That is a bounded LLM influence on money, bounded by a judgement constant (J) and an untested ablation; brief 16 says bound text influence, but bounded-nonzero is still an injection path. D/B/C hold it at veto-or-reduce only.
- Kill cancels stops (generic).

Strengths: minimum order $20 and 2% cash buffer, approvals that expire to "no trade", templated reports when the LLM is off, a budget rule (600x) stated for every unlock, staged triggers that never touch the order path.

## Compliance with brief 12 mandatory subset (2,3,4,5,6,7,12,13,14,15,17 + runbook)

| Item | A | B | C | D | E |
|---|---|---|---|---|---|
| Per-order notional/qty cap | yes | yes | yes | yes | yes |
| Price collar | yes | yes | yes | yes | yes |
| Duplicate detection | yes | yes | yes | yes | yes |
| Rate limits | yes | yes | yes | yes | yes |
| Aggregate exposure | yes | yes | yes | yes | yes |
| Loss limits to state | yes | yes | yes | yes | yes |
| Reconciliation start/timer | start, per-run | per-run | per-run | per-run | per-run |
| Independent kill switch | yes (cancels stops) | same | same | same | same |
| Dead-man's switch | alert only | alert only | alert only | alert + stops-verified + silence test | alert only; 2-ping wording |
| Single-instance lock | yes | yes | yes | yes | yes |
| Credentials separation | partial | partial | best (separate user) | partial | partial |
| Written runbook | not stated | B0 "keeps the runbook" | incident agent drafts | one-page runbook | not stated |

"Reconciliation every few minutes" (brief 12 item 12) does not apply to a once-a-day job, but none states the compensating rule: if a stop fills at 11:00 and the next run is 24 hours away, the ledger is wrong for a day; fine for ETFs, not for crypto.

## Best ideas to graft

1. D: failure catalogue F1-F14 mapped to controls and the GF drill gate (including restore-from-backup, foreign manual order, clock skew, dead-man alert reaching the phone).
2. D: owner-override rules: tighten instantly, loosen after 72 h with red-team note, veto-only (log counterfactual), manual trade in the JARVIS account = SAFE, discretionary trading in a separate account.
3. D: deploy discipline: tagged versions, config-hash handshake, no deploy with working orders, first run half size, no dead code, no reused flags.
4. D: separate "stops verified" Healthchecks check and a weekly deliberate-skip silence test.
5. D: capital-scaled LLM cap `min($15, 2% x capital / 12)` with prepaid balance as the real ceiling.
6. C: separate Windows user for the live key + Claude Code deny-by-default PreToolUse hook, quarantined Reader with no tools, lethal-trifecta partition.
7. B: whole-share-only for any overnight holding (subject to a price-feasibility check at actual capital), 20% no-trade band, residual in T-bill ETF; approvals only for risk-increasing orders, risk-reducing never wait.
8. A: crypto sleeve sized by a gap rule (30% overnight gap must cost <= 3% of equity); SAFE blocks entries but never forces exits; no flatten on restart.
9. D: as-of snapshot per run, 09:45-15:30 ET order window, turnover <= 100% per run, quarantine moves >30% without a corporate action.
10. E: minimum order size and cash buffer in the gate; approvals that expire to no-trade; templated fallback when the LLM is off.

## Missed by all proposals

M1. **Kill-switch semantics:** kill must cancel non-protective orders and keep or re-arm stops; flatten is a separate, rehearsed command; document the extended-hours limitation (market orders rejected for equities outside regular hours, brief 17 F17/F21).
M2. **Exit sequencing and the stop/sell race:** define "cancel stop, wait terminal, size sell from broker-reported position, then sell", with a rule that sell qty can never exceed broker position; consider OTO/bracket so entry and stop are atomic for whole shares (brief 17 rec 8). Test with the replace-race drill.
M3. **Reconcile classification:** expected mismatches (own stop fill, partial fill, dividend cash, ETF split) versus unexplained ones; only unexplained goes to SAFE. Without it, every stop-out halts the system.
M4. **Alert-only watchdog:** nothing off-host can cancel orders or halt a runaway; the trade-off (no read-only Alpaca keys, brief 23) was not discussed. At minimum state the manual path: Alpaca app and phone alert.
M5. **Signal-day catch-up and unfilled-order policy:** evaluate month-end signals on the next N trading days using month-end as-of data; define what happens to an unfilled DAY exit order (next-day retry with fresh price) so a failed day does not become a month.
M6. **Intent TTL and submit-time re-gating** for anything computed the evening before; defence against StartWhenAvailable late runs.
M7. **Host cutover procedure** (laptop to VM): disable laptop task, rotate live key, then enable the VM job; never both.
M8. **Dev/prod separation on one 8 GB laptop** where a Claude Code builder edits the tree that Task Scheduler runs (brief 12, FINRA 15-09: segregated development environment). Run production from a tagged, read-only checkout.
M9. **Behaviour under Windows forced restart mid-run** and Modern Standby (brief 23): the retry hour and the missed-run alert are present but no proposal rehearses a mid-rebalance reboot with half the legs submitted (A/B/C/E list "crash mid-rebalance" only as a G3 drill, D as F6).
M10. **Crypto stop-limit gap-through and re-entry cooling-off** (brief 17 rec 5): a stop-limit that triggers but does not fill leaves an open-ended loss; after a stop-out the next signal may re-enter immediately.
M11. **Whole-share feasibility at $1,000** (price cap ~$50 for a $250 slot at 10% tolerance); decide the minimum capital for the whole-share rule or accept fractional-unprotected at small capital, and show the live book against Strategy 0.

# Critique through the lens: llm-agent-architecture

Date: 2026-10-01. Checked against briefs 01, 02, 03, 13, 22 (plus 00/00b). No new research. Scores are 0-10 through this lens only.

## 0. Ground truth the proposals must meet

- Brief 01: no LLM trader has beaten buy-and-hold net of cost after cutoff. The safe jobs are extraction, offline research (LLM writes code, deterministic code judges: AlphaForgeBench) and narration. "Theatre" list: per-candidate debates, persona agents, LLM-stated confidence.
- Brief 02: about 13 of 18 v3 agents are code. Same-model debate is the weakest configuration. Verification item 7: an ablation needs hundreds of scored candidate-level predictions (Brier), not P&L. Heterogeneous critic is untested under Claude-only.
- Brief 03: money path is a plain state machine. Reasoning plane is stateless Messages-API functions with strict schemas. Agent SDK (about 1 GiB per session) is for the Lab and ops only. Record-and-replay, because sampling params return 400 on 4.7+.
- Brief 13: three privilege zones (quarantined reader with no tools, reasoning LLM that sees only structured fields, deterministic governor). Tickers mapped by code, not the LLM (homoglyphs broke mapping on 99.1% of manipulated headlines). Text may veto/reduce, not enlarge. Refusal and max_tokens break schemas; `minimum/maximum` not enforced. Eval protocol: golden set, forward-only ablation, restart on model change, injection regression set.
- Brief 22: core must run at $0 with LLM off. Dedicated workspace, self-set limit returns 400, batches can overshoot, so keep a small prepaid balance. Haiku 4.5 retirement floor is 2026-10-15 (14 days from today), no successor listed, plan 2.6x. Plan login for unattended jobs is policy-unstable, and Consumer Terms bar relying on the service for securities buy/sell/advice.

## 1. Cross-cutting findings (apply to several proposals)

1. **Every proposal pins Haiku 4.5 as the launch extractor (A, B, C, D, E).** Its floor is 14 days away and the first nightly extraction on real capital is months out (P4/P5). Realistic launch cost is the Sonnet-class b2 figure (about $9.4/month, brief 22), which moves the 2% rule from about $2,400 to about $5,600 of capital. Only D lists the Sonnet tier as a growth step, and none re-bases its capital triggers. Consequence: across much of the owner's $1k-$5.6k band the Reader never runs, so the launch roster is the Narrator plus offline sessions.
2. **The Reader has no consumer at launch.** All five launch on 4-6 ETFs. ETFs do not file 8-Ks or Form 4s, so extraction of "fund/issuer 8-Ks" (B's E1, E's Extractor) has no obvious source, and a veto filter over held ETFs has almost nothing to veto. Output is archive-only at zero weight. Brief 02 verif item 7 plus the 12-month model cadence means it cannot earn weight on ETF decisions. E says so (S5 "Doubtful"); A and C hedge. The only defensible value is a forward evidence archive. That is better served by archiving raw text now ($0) and deferring extraction until a consumer exists.
3. **Raw untrusted text leaks into the second LLM or into outputs.** A (`evidence_span` goes to the Red-Team's inputs), B (`evidence_quote`), C (contradicts its own "enumerated fields only" by listing "evidence span"), D (`evidence_span`), E (`quotes[]`). Brief 13 zone (ii) says the reasoning LLM sees only structured fields, never raw text. The spans should be character offsets verified by code as a substring of the sanitised source, never free text forwarded downstream.
4. **LLM-emitted entity/ticker fields.** E (`symbols[]`), B (`symbol`), A (`entity`). Brief 13 rec 2: ticker mapping in deterministic code. C and D (`entity_id`, "Forbidden: ticker mapping") are right.
5. **"Forbidden" columns are prose, not controls.** The agent tables forbid reading keys, editing the registry, touching live config. On a laptop where the live key sits in a DPAPI user-scope file (brief 23/13: protects only against other users) a Claude Code session with Bash running as the owner can read it. Only C specifies a mechanism (separate Windows user `jarvis-trader`, deny-by-default PreToolUse hooks, harness-only backtests). D has a Change Reviewer plus CI but no isolation.
6. **Trial-log integrity of the Lab is asserted, not enforced (A, B, D, E).** "Logs every variant" / "Forbidden: leaving any trial unlogged" is an instruction. An agent that can run Python can run unlogged variants and make N_eff and the DSR gate meaningless (brief 08/Gençay, cited in brief 02 verification). Only C closes it (harness-only runs, sealed holdout, 20-variant cap per family).
7. **Same-model reviewer grading same-model work, with no measured catch rate.** A (Red-Team), B (R2's "one red-team pass on its own spec", author = reviewer), C (Opus Red-Team), D (Change Reviewer), E. Heterogeneity is untested (brief 02 verif item 6). Nobody measures recall. v1's four documented defects (label leak `return_pct_t1`, zeroed SEC/social columns, committed key, global session) are a ready-made seeded-bug test set.
8. **Failure handling of API outputs is thin.** Everyone says "Pydantic-validated, fail closed". Nobody names `stop_reason` of `refusal`/`max_tokens`, the 29-day Batch result retention (persist immediately), or Batch latency up to 24 h in any hot-path-adjacent step (brief 13 sec 2.2, brief 22 sec 1).
9. **Terms 3(9).** Strategy Lab on a plan login proposes strategies that will decide orders. Brief 22 leaves this a lawyer question. Only B notices the clause, and only for its Reviewer. C offers a monthly-API fallback if there is no Pro plan, but that is a cost fallback, not a legal one.
10. **The biggest legitimate use of "AI agents" for a solo developer is the build itself, and only B and E list a Builder.** Claude writes the risk gate and order service. The verifier must be tests (property tests on the gate, replay identity, future-poisoning test), not a second Claude. D (Change Reviewer plus CI) and C (hooks) come closest.

## 2. Proposal A: vision-faithful (score 5)

What is handled well:
- Every agent is off the order path and off by default ("The core runs with every agent off").
- Thirteen v3 roles are honestly demoted to code.
- Spend is capital-gated ("below $2,400 only the Narrator runs").
- The model-change procedure is the most explicit of the five: golden set of about 300, 2-4 week old/new shadow, clock restart.
- The 20-symbol watchlist is the only design in which the Reader can accumulate hundreds of scoreable events inside one model generation without trading them. A never says that is its purpose or names the scoring target.

Serious flaws:
- **Red-Team per position change is theatre by construction.** "Each position change (~5-15/month)": for a book with about 3-4 round trips a year (A's own Strategy A), the real rate is lower, and even 5-15/month gives 60-180 events per model generation. Brief 02 verif item 7 requires hundreds, and "would veto / would not" has no ground-truth label. A's own risk 3 concedes the ablation may never pass. A states the ablation is the keep condition, but that condition is unreachable. Compare C/D/E, which aim the red-team at specs and promotions, where leakage and missing evidence are checkable.
- **Goal Interpreter is vision-hugging.** A free-text goal to config diff is a six-field YAML. It also invites translating a return target into risk parameters, which contradicts "never chase a target" (B, D reject return-target fields outright).
- **News/Filing agents run on names JARVIS cannot trade** (watchlist "reported, never traded"). Output feeds only reports. Defensible as an archive, but it is $4/month of Haiku for no decision.
- **Injection design is thin.** Sanitisation is mentioned, but no quarantine/privilege-zone statement. `entity` is an LLM field. `evidence_span` is raw text and goes into the Sonnet Red-Team's inputs. The ledger stores "full LLM request/response" and the Narrator reads "Ledger rows only", so raw untrusted text can reach the Narrator and the owner's email. No injection regression set in the Claude-feature gate (brief 13 rec 8d).
- **No non-blocking contract.** Pipeline steps 6 and 9 (News Analyst, Red-Team) sit before READY and use Batch (up to 24 h). The schedule (16:45 submit, 07:00 collect, 09:45 orders) implies sequencing but never says the 09:45 job proceeds if the batch is late or expired. Contrast E's design: orders read the previous night's stored evidence.
- **"Trade emails" from a nightly Batch narrator** cannot be same-day (Batch latency, brief 22). A needs a templated immediate confirmation.
- **Cap hygiene.** "$15/month limit" with no prepaid-balance ceiling, although brief 22 says batches can overshoot. Later "may enter one model as a feature" has no bound on text influence on size (brief 13 rec 3).
- **Lab/registry controls are policy only** (see 1.5, 1.6).

Not fatal. Nothing breaks a binding constraint.

## 3. Proposal B: evidence-minimal (score 6)

What is handled well:
- Cleanest off-path story: "No Claude agent sits on the order path"; production runs with the LLM off at $0; E1 deferred and, once it passes, "may only tighten risk" (the correct direction, brief 13 rec 3).
- Notices that R1 must be "an auditor, not an adviser (Consumer Terms, brief 22)".
- No injection surface at launch because there is no production LLM.

Serious flaws:
- **The replay claim is hollow.** "Every call is recorded for replay: model ID, full request and response, prompt hash and usage" describes API calls, but B's only live agents (B0, R1, R2) are plan sessions. Those have no request/response log of that form (brief 03: SessionStore mirror is best-effort; "capturing results as application state is more robust"). What actually needs to be stored is the session's inputs and its output artifacts. B doesn't say so.
- **R1's `weekly_review.json` (incidents, cost_ratio, band_status) must be computed by code, not by the LLM.** B doesn't say who computes it. If the session computes it, it is neither replayable nor trustworthy; the LLM should only narrate code-computed rows.
- **R2 "one red-team pass on its own spec"** is self-review in the author's context. Weak against the same blind spots (brief 02 F7 verification failures, 24% of MAST failures).
- **"Forbidden: Seeing live keys" for the Builder** has no mechanism (see 1.5).
- **Under-delivers the owner's intent more than the evidence forces.** It drops even the Narrator ($0.65/month, brief 22; 0.8% of $1,000 a year, inside the 2% rule) in favour of a template, and even a weekly Narrator is about $0.15 (E). The owner asked for an agentic end-to-end system. Evidence supports extraction, narration, red-team-of-specs and incident explanation off-path, and B offers none of these in production.
- **E1's `symbol` and `evidence_quote` are LLM-emitted** (see 1.3, 1.4); deferred, so low urgency.

Not fatal.

## 4. Proposal C: agents as the quant team (score 7)

What is handled well (the best injection and Lab-integrity design of the five):
- Privilege zones are explicit: the Reader is "the only agent that sees untrusted text. It has no tools", NFKC-normalised, HTML-stripped, length-capped, JSON-encoded, with an `instruction_like_text` flag; the Reporter sees only the Reader's enumerated fields; "No score derived from text can increase a position"; the lethal trifecta is named (brief 13).
- Live key under a separate Windows user, with the correct DPAPI caveat; deny-by-default PreToolUse hook (brief 03).
- Lab integrity is mechanical: "The harness is the only way to run a backtest, and it logs every run, abandoned ones included", holdout assets/final years not in the Lab's directory, owner unseals once per spec, at most 20 variants per hypothesis family, "presumed mined from history it already saw".
- Post-hoc hypotheses are tagged "post-hoc", which stops narrative laundering into the registry.
- Fresh-context reviewer for specs; the LLM gate includes a post-cutoff golden set, an injection regression set, a forward shadow and a Brier-scored ablation, with a clock restart on model change.
- Narrator numbers are code-checked.

Serious flaws:
- **Theatre by headcount.** Nine agents for a book that rebalances about monthly. Data-Quality Triage on Haiku classifies a "cause enum" (split not applied, dividend adjustment, vendor error), which a corporate-action table plus a ratio check does deterministically; it also adds a Batch (up to 24 h) hop for a quarantine the owner must release anyway. Post-Trade Reviewer writes "lessons" on perhaps one or two trades a month. Ledger Analyst turns a SQL lookup into chat. Incident Diagnostician is plausible value, but see next point. Brief 01 rec 4: "start with the deterministic pipeline plus at most three LLM roles".
- **Internal contradiction on unattended plan use.** "No unattended production job uses the subscription", yet agent 9 is triggered by "Failed run, reconciliation break, missed heartbeat" at $0 on Pro. A missed heartbeat at 02:00 has no attended session. Either it runs on the API (cost line missing) or it waits for the owner.
- **Reader output contradiction.** "Output is enumerated fields only", but EventRecord includes "evidence span" (see 1.3). Fix: offsets, verified by code.
- **Backtest Engineer as a subagent of Lab Lead** is a role-split sequential hand-off (spec to code), which brief 02 F11 (Anthropic) says loses fidelity; C says "context boundary, not persona". The reviewer split is a legitimate boundary; this one is arguable.
- **No outbound-network mechanism** is specified for the Lab ("no web or outbound tools"). Hooks restrict tools, not what a permitted shell can reach. Unevidenced either way for Windows.
- **Red-Team recall is untested** (see 1.7). Memory: each Claude Code session about 1 GiB plus (brief 03) on an 8 GB laptop; C acknowledges and limits to one session plus one subagent.

Not fatal. Highest raw quality; weakest on scope discipline.

## 5. Proposal D: failure-first (score 7.5)

What is handled well:
- Agents are tied to named failures; the roster is tight (six) and every row says what the agent may not do.
- **Cost cap is the best-designed:** `min($15, 2% x capital / 12)` in a dedicated workspace, "small prepaid balance as the real ceiling", cap hit means "LLM unavailable", trading unaffected (brief 22: 400 on self-set limit, overshoot on Batch).
- Narrator numeric check with a template fallback "on failure, a template is sent".
- "Text can only veto or reduce" and "at launch it only logs" for the Event filter (brief 13 rec 3).
- Reader emits `entity_id` and an `injection_flag`; ticker mapping is forbidden; an injection test set runs in CI; a future-poisoning test targets leakage in code, not by LLM review.
- Red-Team is aimed at promotions and limit loosening, with a `missing_evidence` field. These are artifacts where gaps are checkable.
- Names LLM spend (F7) and prompt injection (F8) in the failure catalogue.

Serious flaws:
- **Strategy Lab registry integrity is by instruction.** "Research data copy" (including the holdout?) and "Forbidden: editing the registry" with no harness-only run path (see 1.6; C does this right).
- **Change Reviewer and Red-Team have no measured recall** (see 1.7); both are Claude reviewing Claude. D's CI tests are the real verifier, and should be named as such.
- **Reader launches with no consumer** (1.2) and an unsupported "$1-2" scaling of brief 22's $4.
- **Incident Analyst reads logs** that can carry vendor-controlled strings (broker error text). Advisory only, so low risk. Whether it runs on the API automatically (cost under the cap) or in a session is unstated.
- **Pins Haiku 4.5** (1.1), though it alone lists the Sonnet tier with a golden-set gate.
- Red-Team "2-5 a month" overstates how often promotions occur (G-steps are at least 6 months apart).

Not fatal. Best on cost, fail-closed behaviour and "agents tied to failures"; modest on Lab integrity.

## 6. Proposal E: staged platform (score 6.5)

What is handled well:
- LLM outputs are stored and **attached at the next run** (step 8 reads stored evidence, step 15 produces it). That decouples the order path from Batch latency and API outages, the cleanest of the five.
- The Evidence object with `producer{kind, model_id, prompt_hash}` and `decision_weight` defaulting to 0; ladder A0-A3 with clock restart per model change.
- The most honest agent outlook: S5 "Doubtful: the sample is too small per model generation", S6 "Doubtful at monthly decision rates". It knows weekly-only Narrator is about $0.15.
- Cap with workspace limit plus small prepaid balance; Narrator and Extractor never use a plan login.

Serious flaws:
- **Text may increase size.** A3: "weight above 0, capped at +/-25% of a leg's size". Brief 13 rec 3: text-derived scores may veto or reduce; any increase needs a small fixed cap and price/volume corroboration. C ("never add"), D ("only veto or reduce") and B ("only tighten") are safer. The decision-steering attack surface (brief 13 sec 2.1; "Poisoning Agentic Alpha") is largest here.
- **LLM-emitted `symbols[]` and `quotes[]`** (1.3, 1.4); no quarantine or privilege-zone statement; no injection regression set (A0 is only a schema-valid golden set).
- **No numeric/ledger check on the Narrator.** `Report{headline, actions[], ...}` is free text; "Forbidden" is prose. A, C, D validate numbers by script.
- **Frozen generic `Evidence{payload}` and "agent slot"** is platform-building for roles its own ladder calls doubtful. It risks a loosely-typed payload against strict JSON-schema output (brief 03: `additionalProperties:false`, no recursion). Mitigation: per-producer schema versions, which E implies but doesn't state.
- Lab "runs backtests through tools" is better than free Python, but "Forbidden: re-running a holdout" is still policy (1.6).
- Pins Haiku 4.5 (1.1). Extractor on ETF holdings has no obvious text source (1.2).

Not fatal.

## 7. Agent-by-agent verdict on theatre (summary)

- **Real value, keep:** Narrator (weekly, plus event-triggered, plus code-checked); Strategy Lab (low yield, but safe and verifiable if enforced mechanically); Builder (largest real use, verified by tests); Red-Team only on specs/promotions/limit loosening; Incident explanation.
- **Defensible but unconsumed at launch:** Reader/Extractor, as a forward archive only.
- **Theatre or near-theatre:** A's Goal Interpreter and per-position-change Red-Team; A's off-universe News/Filing agents; C's Data-Quality Triage, Post-Trade "lessons", Ledger Analyst; any nightly Narrator that says "no change" (template does it).

## 8. Ranking

D (7.5), C (7), E (6.5), B (6), A (5). No proposal has a fatal flaw in this lens.

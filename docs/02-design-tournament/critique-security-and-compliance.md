# Critique through the security-and-compliance lens

Critic lens: key handling, prompt injection from ingested text, spend caps, data-licence and terms compliance, legal exposure.
Checked against briefs 12, 13, 21, 22 (plus 06 and 23 where they carry the licence and secrets facts). Date 2026-10-01.
No new research. "Policy-only" below means the proposal forbids something in a table cell but names no mechanism that stops it.

## Scores (security-and-compliance only)

| Proposal | Score | One-line verdict |
|---|---|---|
| D-failure-first | 8.5 | Best compliance process and spend control; key isolation still weak |
| C-agents-as-quant-team | 8.0 | Best injection and key isolation design; biggest agent surface and one internal inconsistency |
| B-evidence-minimal | 6.5 | Smallest attack surface; almost nothing specified about injection or key isolation |
| E-staged-platform | 6.0 | Good spend control; lets text-derived scores raise position size later; policy-only isolation |
| A-vision-faithful | 5.5 | Largest LLM surface with the weakest containment of it |

No proposal has a fatal flaw by the stated definition (loses money, breaks a binding constraint, or is unbuildable). All five keep Claude off the order path,
keep a deterministic default-deny gate, run with the LLM off, use a dedicated capped workspace, and replace "investor view" with an owner-only dashboard.
The differences are in how well each contains the LLM surface it chooses to add, and in what each leaves unsaid.

## What every proposal gets right (so it is not repeated per proposal)

- Production LLM calls use an API key and Batch in a dedicated workspace, never a plan login (brief 22).
- Core trading needs no LLM; LLM output has zero weight until forward ablation (briefs 13, 22).
- Leaked v1 key flagged first (brief 13). I confirmed a live-looking OpenAI key is hard-coded in a comment in `jarvis/jarvis_backend.py` line 597.
- Separate paper and live keys, live key on one host (brief 23).
- No override path for degraded data (brief 12).
- "Investors" replaced by an owner-only dashboard (briefs 06, 12).
- Self-cross and wash-trade guard, duplicate-order detection, deterministic `client_order_id`, kill switch separate from flatten (briefs 12, 21).

## Proposal D: failure-first (8.5)

Strengths
- Spend cap is the only one scaled to capital and with a real ceiling: "`min($15, 2% x capital / 12)` in a dedicated workspace, with a small prepaid balance as the real ceiling". This matches brief 22 (limits cannot be set on the Default Workspace; batches can overshoot a workspace limit; self-set cap returns 400) and brief 11's 2% rule. "Hitting the cap means LLM unavailable" is the correct handling of the 400.
- F8 injection row: quarantined Reader, sanitisation, "text can only veto or reduce", "injection test set in CI" (brief 13 rec 8d). This is the only proposal besides C that puts an injection regression test in a gate.
- Narrator output is validated against the ledger and falls back to a template on failure.
- Key timing follows brief 13 rec 10: live key present only from G4.
- Override controls (F11): loosening a limit waits 72 hours and needs a Red-Team note, tightening is immediate, a manual trade in the account triggers SAFE. This answers FINRA 15-09 "controls on anyone's ability to override system controls" (brief 12 section 2.2).
- P0 includes "read the customer agreement"; brief 12 left it unread, brief 21 decoded it, and D alone schedules the owner reading it.
- Typed, never-retried handlers for self-cross, PDT and margin rejections (F12), correct given Customer Agreement section 32 (brief 21).
- Hash-chained ledger: tamper-evident, though see below.

Flaws
- SERIOUS: key handling is "DPAPI user-scope file on one host". Brief 23 states "Malware running as the same user can still read it", and brief 13 states keyring "protects against files-in-repo leaks, not against malware running as the same user". D runs Claude Code sessions (Strategy Lab, Change Reviewer, "Plan") as the same Windows user that owns the live key from G4 (months 9-15), and the host move to the e2-micro is P6 (month 15+). So for the whole micro-live period an LLM agent with shell tools shares a user with the live key. "Forbidden: Live keys" in the Strategy Lab row is policy-only. Brief 12 minimum set item 17: "live keys ... never visible to LLM prompts/tools".
- SERIOUS: "Event filter ... can only veto or reduce a trade". The text never says the veto applies only to risk-increasing orders. A forged 8-K or headline that vetoes a risk-reducing exit or the stop re-arm is a denial-of-exit attack. Brief 13 rec 5 keeps open positions "under deterministic exits" when the LLM path fails.
- "Wallet whitelisting stays off, because a leaked key can add whitelist entries (brief 23)" is a Coinbase control copied into an Alpaca-only design. Brief 13: Alpaca key scoping and IP allowlists are "not available until verified". D never says what limits the damage of a leaked Alpaca key beyond its own gate, which a thief bypasses.
- The hash chain lives in the same SQLite file the agents' user can write, so an attacker or a confused agent can rewrite the chain from the start. Anchor the head hash off-host (for example in the Healthchecks ping payload) or it proves little.
- Moving to the e2-micro: DPAPI does not exist there and no Linux secret store is named (brief 23 gives `LoadCredentialEncrypted=`). "Live key on one host only" is silent on re-issuing the key on migration.
- The Reader's `evidence_span` is free text from an untrusted document and D does not exclude it from the "ledger extract" the Narrator reads: a second-order injection path to an agent whose output is emailed to the owner.
- No mention of the Alpaca "Risks of Automated Trading" server wording (brief 21 section 5) before moving to a cloud VM.

## Proposal C: agents as the quant team (8.0)

Strengths
- Only proposal that applies the "lethal trifecta" explicitly (brief 13) and builds the privilege zones brief 13 rec 1 asks for. The Reader "has no tools. Its input is NFKC-normalised, HTML-stripped, length-capped and JSON-encoded. Its output is enumerated fields only", with an `instruction_like_text` flag. The Reporter "sees only the Reader's enumerated fields" and "Ledger numbers and enums (no raw text)". This closes the second-order path that A, D and E leave open.
- Only proposal with technical key isolation: live key "DPAPI-encrypted under a separate Windows user, `jarvis-trader`", with the explicit note that DPAPI only protects against other users. Plus a deny-by-default PreToolUse hook blocking the trading directories, a read-only SQLite connection for the Ledger Analyst, `lab.sqlite` separate from `jarvis.sqlite`, sealed holdout data, "no web or outbound tools" for the Lab. This is the nearest any proposal gets to brief 12 item 17 and FINRA 15-09 "restricted code/system access".
- "No score derived from text can increase a position" and "never add to one" (brief 13 rec 3). Strongest wording of the five.
- The Reader is gated on capital (from $3,000) and on a forward ablation with an injection regression set.
- Reporter recipient limited to the owner.

Flaws
- SERIOUS: the separate-user design leans on an untested path. Brief 23: "Whether it works under 'run whether user is logged on or not' was not tested (UNVERIFIED)"; Task Scheduler needs a stored password or S4U logon with the Logon-as-Batch privilege. P0's probe list (news, duplicate id, Texas, IRA fees) does not include "can a Task Scheduler job running as `jarvis-trader` decrypt its DPAPI file after reboot with nobody logged in, and wake the machine". If it fails, the fallback is the weaker same-user design with no stated plan B. Also unaddressed: the stored credential for the `jarvis-trader` account is itself a secret on the owner's machine.
- Internal inconsistency: the intro says "No unattended production job uses the subscription" and puts agents 1, 3, 5, 6, 9 in attended sessions, but agent 9 (Incident Diagnostician) is triggered by "Failed run, reconciliation break, missed heartbeat" and costs "$0 on Pro". Either it is unattended on the plan (violates its own rule and brief 22) or it is not triggered. It also reads "redacted broker snapshot" and logs, and logs contain attacker-influenced strings (headline fragments, broker error text) and an unspecified redaction step. It is a Claude Code agent with tools reading untrusted text, the one place C weakens its own trifecta rule.
- Nine agents is the largest roster of tool-enabled Claude Code surfaces of the five, mostly on the owner's plan. Agents 6 (Ledger Analyst Q&A on live ledger) and 9 move live portfolio data through a consumer plan; see the Terms 3(9) point in the shared section.
- Spend: "$10 spend limit" with no mention of a prepaid balance as the real ceiling. Agent 4 Reporter has no template fallback when the cap returns 400.
- Anthropic key location is not stated (see the `ANTHROPIC_API_KEY` collision in the shared section).
- No PDT or intraday-margin typed handler beyond one line; no Linux secret store on the VM move.
- Approvals mechanism unspecified: "pending approval rows that expire to reject", but who writes the approving row and from which user is not said.

## Proposal B: evidence-minimal (6.5)

Strengths
- Smallest attack surface: no Claude agent in production at all at launch; E1 is deferred behind a capital trigger and a forward test; a templated status email with no LLM narrator, so nothing LLM-generated reaches the owner's inbox.
- Only proposal to put a second layer of defence at the broker rather than only in local code: "`no_shorting` at the broker and in the gate" (brief 21 account config). A thief with the key still cannot short, and leverage is capped at the account level.
- Only proposal to cite the Consumer Terms point as a role boundary: R1 "is an auditor, not an adviser (Consumer Terms, brief 22)".
- Per-order notional cap of $350 at $1,000, which actually bounds a unit-error order at that size (brief 12, Citigroup lesson).
- Risk-reducing orders never wait for approval; risk-increasing ones do. That is the right asymmetry.

Flaws
- SERIOUS: nothing specified about prompt injection. A search of the whole proposal finds no mention of sanitisation, quarantine, homoglyphs, hidden HTML or an injection test. E1 reads Alpaca news and 8-K text and writes `evidence_quote`, free text. "Pydantic-validated, fails closed" covers format, not content (brief 13 section 2.1: the realistic attack is decision steering, not "send an order"). Deferral reduces exposure but the E1 spec as written would ship undefended.
- SERIOUS: key isolation is policy-only. B0 Builder "Forbidden: Seeing live keys; deploying with open positions; editing `risk_config` without an owner-signed commit". No mechanism stops a Claude Code session running as the same user from reading a DPAPI file or running `jarvis approve`. "Owner-signed commit" is not backed by anything the gate verifies at start-up.
- Approvals via `jarvis approve <id>` "or Streamlit": an unauthenticated local web page that clicks approve is a weaker channel than a typed CLI confirmation (D), and is reachable by any local process or by a browser-automation agent. Bind to localhost and require a typed code, or use CLI only.
- Spend limit mismatch: E1 "in a dedicated workspace with a $5 limit" at capital ≥ $2,500, but the same table gives "~$9.4 a month" for the Sonnet-tier successor at ≥ $5,600 and "~$10" for the Haiku successor; the cap is not raised in the growth table, so the batch would hit HTTP 400 mid-month. No prepaid ceiling mentioned.
- No PDT or intraday-margin rejection handler despite Customer Agreement section 32 (brief 21).
- R1 has "read-only database access" with no stated enforcement.

## Proposal E: staged platform (6.0)

Strengths
- Spend control is good: "~$5 workspace spend limit and small prepaid balance"; Batch only; templated fallback "if the LLM is off" (brief 22).
- The frozen Evidence object (`producer{kind, name, version, model_id, prompt_hash}`, `decision_weight` default 0, `validation_status`) is a clean audit and replay contract (brief 13 rec 7).
- Extractor input is "Sanitised text (homoglyph/HTML stripped, 16)", and the agent ladder A0 to A3 matches briefs 13 and 22.

Flaws
- SERIOUS: the ladder's last rung, "A3 weight above 0, capped at +/-25% of a leg's size". Brief 13 rec 3: a text-derived score "may veto or reduce a trade ... but may not by itself increase position size". A +25% sizing swing on text-derived input is exactly the lever the Rizvani et al. attack uses (brief 13: worst case 17.7 points from one manipulated day), and E's `Evidence` object has a `direction?` field that invites it. E itself rates S5 "Doubtful", so the cost is a contract that permits a bad future decision, not a launch bug. Restrict A3 to veto and reduce only.
- Key handling is the thinnest of the five: "DPAPI user-scope file; separate paper and live Alpaca keys, live key on one host; ... never in the repo or a prompt". Builder and Strategy Lab on the plan with "Forbidden: touching live keys, the risk config or the live branch" is policy-only. No separate OS user, no deny hook, no key-arrival gate (live key at G4 only is not stated).
- The `quotes[]` field in Evidence is free text from untrusted documents and the Narrator reads "Ledger rows, gate reason codes ..." where evidence ids are stored: a second-order injection path with no containment stated. No numeric validator on the Narrator.
- No PDT or intraday-margin handler despite brief 21 section 3 (Customer Agreement section 32).
- No injection regression set in gate A0 to A3 (only a golden set).
- Five frozen contracts on day one add surface to secure before anything trades; E concedes this in its own risk 1.
- The Host upgrade line has the same unflagged Alpaca server wording issue as every proposal.

## Proposal A: vision-faithful (5.5)

Strengths
- Names sanitisation (homoglyph and hidden-HTML stripping, "dedup by hashing first"), Pydantic range validation, fail-closed, record-and-replay, no override path, capital-gated spend (Narrator only below $2,400; extractor from $2,400, per briefs 11 and 22), $15 cap with a dedicated workspace, a numeric check on Narrator figures ("checked by script"), and "SAFE ... never forces exits".
- Most complete risk-gate table, including absolute-dollar per-order caps.

Flaws
- SERIOUS: it keeps the largest LLM surface and the least containment. Six Claude agents; a Filing Reader that ingests 8,000-token 10-K/10-Q excerpts and emits free-text arrays (`new_risks[]`, `changed_sections[]`); a Red-Team that reads "Evidence card, events, spec" on every position change and emits `concerns[]`, `falsifiers[]`. None of these is described as tool-less or quarantined, and no sentence says no agent combines untrusted input with outbound or write capability (brief 13 rec 1, "lethal trifecta"). The Narrator reads "Ledger rows only", but section 2 step 14 says the ledger holds "evidence card ... full LLM request/response", so untrusted text reaches the Narrator whose output is emailed. The Red-Team verdict is "shown to the owner", another free-text channel.
- SERIOUS: section 12, "a Claude headline score after >= 6-12 months of shadow ... may enter one model as a feature". That is a text-derived input that can raise positions, contradicting brief 13 rec 3 and brief 16 (decayed edge, pump surface). It also sits in a model that will be validated on data the model may have seen (brief 13 section 2.4).
- Extra gate for Claude-derived features lists a golden set, forward-only evidence and an ablation, but no injection regression set (brief 13 rec 8d).
- Controls are mislabelled for Alpaca: "keys never visible to any prompt; withdrawals disabled (briefs 12, 23)". Brief 13: Alpaca key scoping is "not available" until verified, and brief 23's withdrawal point concerns Coinbase, which A drops. The control is unverifiable as written.
- Key isolation is policy-only ("Strategy Lab Researcher ... Forbidden: Live config, keys, live branch or account"), with DPAPI user-scope shared with the Claude Code user.
- Spend: the roster total is "about $4.50/month ... about $10 with a pricier Haiku successor, under a $15 hard cap", but section 12 adds a Strategy Lab API routine and "second red-team sample" at "Budget >= ~$25/month" while the cap stays at $15; no prepaid-balance ceiling; no template fallback if the Narrator batch is blocked by the cap.
- No PDT or intraday-margin handler (Customer Agreement section 32).
- No legal-perimeter text beyond "owner dashboard; no investor view".

## Shared gaps: important things ALL five miss

1. Alpaca's own "Risks of Automated Trading" disclosure. Brief 21 section 5 reports it says the platform "initially will only support algorithms that run on your own computer ... and not a server" (risk language, medium confidence on VPS implications), and brief 23 could not verify any IP or data-centre clause. All five plan to move to a GCP e2-micro or a $4-6 VPS (and C, D and A make it a trigger before crypto). None says to ask Alpaca in writing before migrating, none plans key re-issue on migration, and none names a Linux secret store (DPAPI is Windows-only; brief 23 gives systemd `LoadCredentialEncrypted=`).
2. `ANTHROPIC_API_KEY` collision (brief 22). If the production API key is set in the environment of the user who runs owner-attended Claude Code sessions, those sessions silently bill the API instead of the plan, and in `-p` mode the key "is always used when present". The Strategy Lab and Builder sessions would drain the capped `jarvis` workspace and trip the 400, taking out the Narrator and Reader. Keep the production key out of the user environment (separate OS user or file read only by the batch script).
3. Consumer Terms section on securities (brief 22). Every proposal runs the Builder, Strategy Lab and some review or Q&A agents on the owner's Pro/Max login, and the Lab's output (strategy specs and code) determines what the deterministic engine trades. Brief 22: "Before live capital, decide whether any LLM output may influence order generation. If not, 3(9) is moot; if yes, get advice." Only B names the issue (as a role boundary), and none makes the decision, routes the Lab to the API/Commercial path as an option, or flags it as a lawyer question. The Consumer Terms wording is confirmed, the section number is not.
4. Data-licence exposure from sending licensed text to a third-party LLM. Benzinga redistribution terms were "not found" (brief 21), Alpaca's terms limit use to "own personal and non-commercial purposes", and Tiingo Starter is "internal use only - may not display or share the data with another person" (brief 06). Every proposal sends Alpaca/Benzinga news to the Reader and archives full text as "the only clean post-cutoff dataset". Prefer EDGAR (public) as LLM input, send only headlines and metadata from Benzinga, and read the terms before archiving full content. Also, after any VM move the dashboard becomes remotely viewed market data: the exchange display agreements were never read (brief 21 open item 9; gap analysis last bullet of section 2).
5. No written "legal perimeter". Brief 12 section 4.3 asks for a section listing the five triggers (outside money, pooling, trading authority over another's account, selling or publishing signals, showing performance to prospects). No proposal contains it; D's mapping row only uses the words. This matters because the owner's own vocabulary ("investors") is the most likely route to drift.
6. Approval and override channel integrity. Every proposal has "pending rows that expire to reject", but approval is a CLI or Streamlit action run by the same OS user as the Claude Code sessions, writing to a SQLite file those sessions can write. A prompt-injected or merely mistaken agent can approve its own proposal. Only C separates databases and users. Fix: approvals need an out-of-band factor (separate OS user, passphrase the agents never see, or a phone-confirmed code).
7. Alpaca keys cannot be scoped or IP-restricted (brief 13). Beyond the broker-side `no_shorting` and leverage cap (B only), nobody uses the broker as an independent witness: turn on Alpaca's own trade confirmation emails to a separate inbox, and let reconciliation treat any order not in the intent ledger as SAFE (D does this for manual trades; the others do not state it).
8. Denial-of-exit via text. No proposal says in terms that a text-derived veto, blackout or flag may apply only to risk-increasing orders, never to exits, stop re-arming or the kill switch.
9. Email as an exfil and phishing channel. Narrator output goes to the owner's inbox; none requires plain text only (no links, images or HTML) and a fixed recipient (C fixes the recipient).
10. v1 key remediation. All say "rotate". The key sits in the public git history of a Hugging Face Space (verify the Space's visibility). Rotation must mean revoke at the provider, review usage for abuse, then make the Space private or delete it. Deleting the line is not enough.
11. Supply chain for the code the Builder writes. Only D mentions a lockfile ("Python venv with a lockfile"); none requires hash-pinned dependencies, or that the risk gate module and config hash are verified at start-up against a file the agent user cannot write.
12. Minor terms hygiene: SEC EDGAR requires a declared User-Agent (brief 06); FRED requires an attribution notice (brief 06). Not mentioned anywhere.
13. DPAPI plus Task Scheduler "run whether user is logged on or not" is untested (brief 23). It belongs on the P0 probe list for every proposal, not only C.

## Ideas worth grafting into a combined design

1. C: live key under a separate Windows user (`jarvis-trader`), no shared user with Claude Code; deny-by-default PreToolUse hook on trading directories; read-only DB connections for analysts; separate lab database; sealed holdouts; no web or outbound tools for the Lab.
2. C: tool-less quarantined Reader with NFKC, HTML strip, length cap, JSON encoding, enumerated outputs and an `instruction_like_text` flag; Reporter sees enums and numbers only; Reporter recipient fixed to the owner.
3. C: "no score derived from text can increase a position". Adopt this as a hard rule, replacing E's A3 (+/-25%) and A's headline-score-as-feature.
4. D: spend cap `min($15, 2% x capital / 12)` in a dedicated workspace with a small prepaid balance as the real ceiling; cap hit means "LLM unavailable"; Narrator numbers checked against the ledger with a template fallback (D, also E and B).
5. D: failure catalogue F1-F14, the GF failure-drill gate, broker-constraints adapter at start of every run, typed never-retried handlers for self-cross, PDT and margin rejections, and "manual trade in the account triggers SAFE".
6. D: loosening any limit waits 72 hours with a Red-Team note, tightening is immediate, owner can veto but never add; live key arrives only at G4; read the customer agreement at P0; injection test set in CI.
7. D: hash-chained ledger, but anchor the head hash off-host.
8. B: broker-side `no_shorting` and leverage cap as a second layer independent of the local process; per-order notional cap scaled to account size ($350 at $1,000); risk-reducing orders never wait for approval; templated non-LLM status email; the "auditor, not adviser" role boundary for any plan-based review agent.
9. E: Evidence object with producer, model ID, prompt hash, `decision_weight` default 0 and `validation_status`, with the agent ladder A0 to A2 but stopping A3 at veto and reduce only.
10. A: explicit sanitisation spec (homoglyph and hidden-HTML stripping, hash-based dedup before any LLM call), capital-gated agent activation ($2,400 and $5,600), and "SAFE never forces exits".

## Not found in any proposal

See "Shared gaps" above; the compact list is in the structured result.

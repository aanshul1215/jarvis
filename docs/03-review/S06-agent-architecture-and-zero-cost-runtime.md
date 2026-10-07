# S06 Review: agent architecture and zero-cost runtime (2026-10-02)

Scope: FINAL-design section 3 (roster), plus the runtime pieces in sections 8, 11 and 15. Binding owner constraints respected: Claude agents only, near-zero metered spend, solo developer, 8 GB Windows laptop. Every proposal below costs $0 in metered spend; each says what it does to plan usage.

**Bottom line.** The role split (Claude never touches orders) is right. The runtime plumbing is over-built: a prepaid API workspace, a cap formula, three capital tiers, batch jobs and a tool-using LLM inside the account that holds the broker keys, all to govern $0.70 to $2.02 a month. Run every role on the owner's existing Claude plan instead and delete that plumbing.

## What the design gets right (with evidence)

1. **Claude is off the order path; code decides, owner signs.** Anthropic advises workflows for predictable tasks, simplicity first, and human checkpoints with stopping conditions (Building effective agents, FETCHED). tau-bench (Yao et al. 2024) found top function-calling agents succeeded on under half of tasks, and pass^8 under 25% in retail, so repeated runs are unreliable (FETCHED). That matches brief 01's instability finding.
2. **Dropping LangGraph and an LLM supervisor.** Anthropic measured agents at about 4x and multi-agent at about 15x the tokens of chat, and said multi-agent fits poorly when agents share context or depend tightly on each other (multi-agent research write-up, FETCHED). Cemri et al. (MAST) annotated 1,600+ traces across 7 frameworks into 14 failure modes in 3 groups: specification, inter-agent misalignment, verification (FETCHED, abstract). Fewer agents means less surface.
3. **A mechanical verifier and typed output on every role.** Huang et al. (ICLR 2024) show models do not reliably self-correct without external feedback, and sometimes get worse (FETCHED). Reflexion's gains used external task feedback such as tests (HumanEval 91% vs GPT-4 80%, FETCHED abstract). Anthropic's evaluator-optimizer needs clear criteria; a number-matches-ledger check has them.
4. **A deterministic fallback for every role.**
5. **`ANTHROPIC_API_KEY` never in the owner environment.** The auth docs rank the API key above subscription login, and in `-p` mode the key is always used when present (FETCHED). One stray variable would silently bill.
6. **Not building production on a subscription login via the Agent SDK.** The Agent SDK page says third parties may not offer claude.ai login or its limits, and to use API keys (FETCHED). I keep this line (P2).

## What should improve

**S06-P1 (must). Run all Claude roles on subscription surfaces; delete the metered stack.** Change section 3 ("Spend, models and capital tiers", per-role budget, tiers T0-T2, fallbacks), section 8 (no Anthropic keys in DPAPI; drop tasks `JARVIS-RedTeam`, `-Eval`, `ReaderSubmit/Collect`), section 11 P0/P4 and O19.
- Evidence: the design's T0 cap is $0.70 a month = $8.40 a year, which is 47-60% of the satellite's expected loss of $14-18 (8.40/18, 8.40/14); T2 at $2.02 = $24.24 a year is 135-173% (ESTIMATE). The plumbing costs more than it governs.
- Cost: metered $0.70-2.02 a month plus $2-6 a year of eval becomes $0. Plan usage: scheduled roles about 0.7M input tokens a month (memo 15.6k x 4.33 = 68k, plus Reader about 217 items x 2.1k = 456k, rounded up for overhead; ESTIMATE, design's token figures), roughly $1.5-2 API-equivalent, under 1% of one build month (about 20 days x $13 average per developer-day, costs doc; ESTIMATE). Build sessions, not runtime roles, will exhaust the plan.
- Effort: removes about 13.5 dev-days (workspaces and prepaid check 1; batch submit/collect and persistence 2; cap, tier and fallback logic 3; eval workspace and task 1.5; Reader golden/injection harness 3; unattended incident tool loop 3) and adds about 6 (scheduled-task recipes 1.5; incident bundle builder 1; skills and subagent files 2; output validators 1.5). Net -6 to -9 dev-days (ESTIMATE).
- Risk: plan limits, Desktop app must be open (8 GB RAM), policy gray areas (P11). Core is unaffected: if the plan lapses, templates run.

**S06-P2 (must). Fix which runtime surface each role uses.** Section 3 roster "Trigger / identity".
- Attended Claude Code sessions: Builder, Reviewer, Strategy Lab, Ledger Analyst, Incident Triage.
- Desktop scheduled tasks (local, new session per run, runs on the owner's machine; skips if the computer sleeps, one catch-up for the latest missed run within 7 days; FETCHED): weekly Analyst memo, weekly Reader.
- Optional cloud routine (fresh clone, no local files, Pro/Max, research preview, 1 hour minimum, drawn from plan usage; FETCHED): public-page Change-Watch only, never ledger data.
- Do not use: `/loop` for durable work (recurring tasks expire after 7 days); Agent SDK programs or cron wrappers around `claude -p` on a subscription login; `claude setup-token` in unattended loops.
- Cost $0. Risk: the Desktop task runs under the owner account (my inference), not `jarvis-trader`. That is acceptable only because the owner account already has no access to keys or production data, and read access to the outbox.

**S06-P3 (must). Make the Incident Analyst attended.** Section 3 row 6, section 6, section 8.
- Code writes an incident bundle (ledger rows, `gate_log`, redacted log window, vendor snapshot, code-computed `cause_enum` runbook step) to the outbox and the SAFE/HALT email says "run /incident". On a monthly book SAFE blocks only risk-increasing orders, and HALT can only be cleared by the owner anyway, so waiting for the owner costs nothing.
- Gain: removes the only tool-using LLM from the account holding broker keys, which also removes an injection route (vendor text and logs into an agent with query tools). Data-Trust Triage keeps its code check (reconciles both vendors within 0.5%) plus the owner's approval hash.
- Evidence: Anthropic's human-checkpoint advice; tau-bench. Cost $0.

**S06-P4 (should). Merge 8 roles into 6 with sharp contracts.** Narrator + Ledger Analyst + Change-Watch summary become **Analyst**; Red-Team becomes **Reviewer** (advisory subagent, fresh context, read-only). MAST puts a large share of failures in vague roles, so keep distinct contracts, not one fat prompt. See the roster below.

**S06-P5 (should). Post-hoc validators, not an API loop.** The scheduled Analyst writes a typed JSON memo to `agent-out/analyst/`; trader-side code checks every number against the ledger and swaps in the template on failure; at most 2 repair passes. Optional upgrade: a Stop hook that runs the same check (hooks fire in `-p`; which events can block is UNVERIFIED for Stop). Evidence: Huang; Reflexion; evaluator-optimizer criteria. Effort +1.5 dev-days (in P1's net). Reader spans are verified as substrings by code.

**S06-P6 (should). Unattended permission recipe.** Per task: permission mode that denies anything unlisted (`dontAsk` exists in the CLI; whether the Desktop picker offers it is UNVERIFIED), explicit allow rules for read paths, Write only to the role's own `agent-out/<role>/` folder, deny Write to `.claude/**`, no Bash for Reader, no web for Analyst, no subagent fan-out. Press Run now once and approve in the detail page; a Manual-mode task stalls until approved. Put a date guard in each prompt because catch-up can fire days late. Hooks and rules are convenience layers; the OS ACL is the control (the design already says this). `-p` without `--bare` loads project hooks and MCP servers without a trust dialog, so keep `.claude/` write-denied (FETCHED).

**S06-P7 (should). Govern plan usage, not dollars.** Replace the cap formula with: keep usage credits and spend limit OFF (they bill on overage and apply to routines; FETCHED); scheduled tasks pinned to Sonnet-class at low effort; at most 2 scheduled runs a week; when the plan limit is hit scheduled roles skip and templates ship; Builder has priority; `/usage` attribution reviewed weekly during P1a to measure harness overhead (UNVERIFIED). Subagent requests count toward the same limits (FETCHED), so Builder subagents get Sonnet or Haiku-class models and focused prompts. Cost $0; effort 0.5 day.

**S06-P8 (should). Per-role memory from external signals only.** One `memory/<role>.md` (first 200 lines or 25 KB load, per subagent docs; FETCHED) appended by code from validator failures and owner accept/reject of drafts, never from the model's own self-critique. Evidence: Reflexion's episodic memory, Huang's caveat.

**S06-P9 (could). Shrink Reviewer's bar.** Section 3 row 4: seeded defects 20 to 8 (v1's four known defects, 4 synthetic), threshold 5 of 8. The Reviewer is advisory; the real gates are tests and the owner's emailed hash. Saves about 2-3 dev-days (ESTIMATE). Risk: lower statistical power, accepted.

**S06-P10 (could). Simplify the Reader.** Section 3 Reader ladder: replace the 300-item golden set and 3-4 hours of hand-labelling by a 30-item spot check; declare A1 unreachable now (the design already calls it likely); no majority-vote sampling (self-consistency multiplies tokens k-fold, RECALLED) for a label with no consumer. Keep forward logging. Saves 3-5 dev-days and 3 owner hours (ESTIMATE).

**S06-P11 (must). Policy invariants.** Consumer Terms (effective 8 Oct 2025, FETCHED): section 3 provision 7 bars automated or non-human access except via an API key or where Anthropic explicitly permits; provision 9 bars relying on the Services to buy or sell securities. This confirms the clause behind O5 (design said "3(9)", unconfirmed). The Claude Code legal page says OAuth is for ordinary use and advertised limits assume ordinary individual use (FETCHED). Invariants: no Claude output is relied on for an order (spec origin stays `llm_origin`; Lab specs trade only after the owner's own harness and G0-G1); unattended subscription use only through Anthropic's own scheduler, at most weekly; Change-Watch's page list adds the Consumer Terms, legal page and Usage Policy. The Usage Policy's financial-decision rules (professional review, AI disclosure) concern advice to others (FETCHED); O5's lawyer question stays. Cost $0.

## Leanest roster (6 roles; Reader optional)

| Role | Trigger / surface | Tools and permissions | Input -> structured output | Verifier | Memory |
|---|---|---|---|---|---|
| Builder | Owner session, dev tree | Full dev tools, `C:\dev\jarvis` only (ACL); never trader files | Repo -> commits | Gate property tests, replay identity, drills, mutation tests on `jarvis/gate/`, owner diff review of gate and `risk.yaml` | CLAUDE.md, repo |
| Reviewer | Owner runs `/redteam` on a spec, gate diff or loosening | Read, Grep only; forked context | Artifact -> `{failure_modes[], missing_evidence[], leakage_suspects[], kill_conditions[]}` | Seeded-defect catch rate (P9) | Lessons file |
| Strategy Lab | Monthly owner session | Dev tree, `lab.sqlite`, no web, no holdout | Research copy -> `StrategySpec` | Harness, registry, holdout via trader task | Spec registry |
| Analyst | Weekly Desktop task (Sun evening) plus `/ask-ledger` | Read outbox and `ledger_ro.sqlite`; Write only `agent-out/analyst/` | Typed ledger fields -> `Report{...}` per section 3 | Code checks every number vs ledger; template on failure | Lessons file |
| Incident Triage | `/incident` after a SAFE/HALT email | Read the bundle only | Bundle -> `{timeline, cause_enum, runbook_step_id, evidence_row_ids[], draft_corporate_action?}` | Row IDs must exist; corporate action needs code reconcile plus owner hash | Lessons file |
| Reader (optional) | Weekly Desktop task | Read one sanitised file; Write one output file; no Bash, no web | Capped text -> `{event_type, materiality, novelty, instruction_like_text, span}` | Schema and substring spans by code; invalid rows dropped | None |

Nothing here places an order, holds a key, or sends mail.

## What I could not verify

- Whether the Desktop scheduled-task permission picker offers `dontAsk`, and whether hooks and `.claude` settings apply identically there.
- Pro versus Max quota sizes; the five-hour and weekly windows were read only on the Teams paragraph of the costs page.
- Whether subscription `claude -p` or `setup-token` use is an "explicit permission" under Consumer Terms provision 7. The docs describe setup-token for scripts but do not tie it to the Terms. Lawyer or Anthropic support question.
- The Consumer Terms and Usage Policy text came through a summarising fetch; section numbering as returned; newer versions may exist.
- MAST per-category percentages and the ChatDev improvement figure: the PDF summary gave numbers I could not confirm, so I do not use them. Reflexion and tau-bench were read from abstract pages only.
- Harness token overhead per Claude Code session; Desktop app RAM on 8 GB; whether Stop hooks can block; the `--tools` flag to disable all tools; whether consumer-plan data is used for training by default (check the privacy setting before sending ledger numbers).
- Cloud routine egress to vendor pages (needs a custom network allowlist).

## References

1. Anthropic, "Building effective agents" (Schluntz and Zhang, Dec 2024, authors RECALLED), https://www.anthropic.com/engineering/building-effective-agents. FETCHED.
2. Anthropic, "How we built our multi-agent research system" (2025), https://www.anthropic.com/engineering/multi-agent-research-system. FETCHED.
3. Cemri et al., "Why Do Multi-Agent LLM Systems Fail?", arXiv 2025, https://arxiv.org/abs/2503.13657. FETCHED (abstract; PDF summary unreliable); NeurIPS venue RECALLED.
4. Shinn, Cassano, Berman, Gopinath, Narasimhan, Yao, "Reflexion", arXiv 2023, https://arxiv.org/abs/2303.11366. FETCHED (abstract).
5. Huang, Chen, Mishra et al., "Large Language Models Cannot Self-Correct Reasoning Yet", ICLR 2024, https://arxiv.org/abs/2310.01798. FETCHED.
6. Yao, Shinn, Razavi, Narasimhan, "tau-bench", arXiv 2024, https://arxiv.org/abs/2406.12045. FETCHED.
7. Wang et al., "Self-Consistency Improves Chain of Thought Reasoning", ICLR 2023, arXiv 2203.11171. RECALLED.
8. Claude Code docs: headless https://code.claude.com/docs/en/headless; desktop scheduled tasks .../desktop-scheduled-tasks; routines .../routines; /loop .../scheduled-tasks; authentication .../authentication; legal-and-compliance .../legal-and-compliance; Agent SDK overview .../agent-sdk/overview; subagents .../sub-agents; skills .../skills; hooks .../hooks; permission modes .../permission-modes (partly read); costs .../costs. All FETCHED 2026-10-02.
9. Anthropic Consumer Terms of Service, effective 8 Oct 2025, https://www.anthropic.com/legal/consumer-terms. FETCHED.
10. Anthropic Usage Policy, effective 15 Sep 2025, https://www.anthropic.com/legal/aup. FETCHED.

# 22 - Claude usage and cost plan

Date: 2026-10-01. Every price, date and rule below was read from an official Anthropic page today (URLs in the source list). Arithmetic is mine and labelled ESTIMATE. This is not legal advice.

## Questions

1. Current models, prices, retirement dates (is Haiku 4.5 retiring, and what replaces it?), Batch discount, caching rules and minimum cacheable sizes.
2. Can a Pro/Max plan legitimately power a personal, scheduled, non-interactive job (Claude Code or Agent SDK)? What is allowed, rate-limited, prohibited?
3. Spend limits and rate limits for a new API account.
4. Three monthly cost scenarios: (a) LLM off, (b) nightly batch on 20 symbols plus daily narrative, (c) (b) plus a weekly research session.
5. What to record for audit/replay, and how to re-validate after a model change.

## Findings

### 1. Models, prices, retirement (all FETCHED, high confidence)

| Model (API ID) | In / out per MTok | Batch in / out | Cache read | Min cacheable | Retirement floor |
|---|---|---|---|---|---|
| Fable 5.1 (`claude-fable-5-1`) | $10 / $50 | $5 / $25 | $0.25 | 512 | not before 2027-09-01 |
| Opus 5.5 (`claude-opus-5-5`) | $4 / $20 | $2 / $10 | $0.20 | 512 | not before 2027-09-22 |
| Sonnet 5.5 (`claude-sonnet-5-5`, released 2026-09-28) | $2 / $10 | $1 / $5 | $0.20 | 512 | not before 2027-09-28 |
| Haiku 4.5 (`claude-haiku-4-5-20251001`) | $1 / $5 | $0.50 / $2.50 | $0.10 | 4,096 | not before 2026-10-15 |

- Legacy but active: Fable 5, Opus 5/4.8/4.7/4.6/4.5, Sonnet 5, Sonnet 4.6. Sonnet 4.5 was deprecated on 2026-09-30 and retires 2026-11-30 (replacement: Sonnet 5.5).
- **Haiku 4.5.** "Active", not deprecated, floor 2026-10-15. The deprecation table names no replacement. Anthropic's Opus 5.5 announcement says Haiku 5.5 "will follow in the coming weeks"; it is not on the models page today and its price is UNVERIFIED. Policy is at least 60 days' notice. Past deprecation-to-retirement gaps were 60-62 days (Haiku 3, Haiku 3.5, Opus 4.1, Sonnet 4) and 114-189 days (Sonnet 3.7, Opus 3). A notice tomorrow would mean retirement no earlier than about 2026-11-30 (ESTIMATE: 10-01 + 60 days). The floors equal release plus 12 months for both Haiku 4.5 and Sonnet 5.5, so plan on about 12 months per model.
- **If Haiku 5.5 does not fit:** Sonnet 5.5 is 2x Haiku 4.5 per token and uses the newer tokenizer (about 30% more tokens per text), so about 2.6x per extraction (ESTIMATE: 2 x 1.3).
- **Sonnet 5.5 behaviour.** Adaptive thinking is on by default at `high` effort and billed as output. For extraction use `effort: low` or `thinking: {"type":"between_tools"}`. `temperature`, `top_p`, `top_k` return 400 on 4.7+ models. A pinned ID keeps its weights, but serving infrastructure can change behaviour.
- **Batch API.** 50% off input and output; at most 100,000 requests or 256 MB per batch; most finish within 1 hour, all expire at 24 hours; expired requests are not billed; results kept 29 days; batches can slightly overshoot a workspace spend limit; not ZDR-eligible.
- **Caching.** 5-minute write 1.25x, 1-hour write 2x, read 0.1x (0.05x Opus 5.5, 0.025x Fable 5.1); stacks with Batch. Batch cache hits are best-effort (docs recommend the 1-hour TTL). Caches are per workspace. **Haiku 4.5 prompts under 4,096 tokens cannot be cached, so assume no caching on Haiku.** Structured outputs are GA on both models, but `minimum`/`maximum` are not enforced and a refusal or `max_tokens` can break the schema, so validate client-side.

### 2. Subscription plan for a scheduled job

**Allowed (FETCHED).**
- Ordinary individual use of Claude Code with a plan login.
- `claude -p` and the Agent SDK on a plan. The support article (last updated 2026-06-16) says they still draw from subscription limits.
- `claude setup-token` makes a one-year OAuth token that the docs say is for CI pipelines and scripts. It requires Pro/Max/Team/Enterprise.
- Cloud Routines (Pro and up, research preview). Minimum interval is 1 hour, with up to 100 scheduled runs per hour per account. They run from a fresh repo clone and use subscription usage.
- Desktop scheduled tasks. They run only while the app is open and the computer is awake. A sleeping machine skips the run, and one catch-up run fires on wake.

**Rate-limited (FETCHED).**
- Rolling 5-hour windows plus weekly limits, shared with chat and interactive Claude Code. I found no published numeric allowances. At the limit, work stops until reset, or continues at API rates if usage credits are on.
- The legal page says advertised Pro/Max limits assume ordinary, individual use of Claude Code and the Agent SDK.
- `--bare` mode never reads plan credentials and needs `ANTHROPIC_API_KEY`. If that variable is set, Claude Code silently bills the API instead of the plan.

**Prohibited or restricted (FETCHED).**
- Consumer Terms 3(7) bans automated access (bots, scripts) unless via an API key or "where we otherwise explicitly permit it". The Claude Code docs above are that permission, so a personal `claude -p` job on your own machine sits inside it. Nothing I read goes further.
- Account sharing is banned. Third parties may not route requests through Free/Pro/Max credentials for their users, offer claude.ai login, collect Claude.ai credentials, or resell.
- **Consumer Terms 3(9) bars relying on the Services to buy or sell securities, or to give or receive advice about securities, because Anthropic is not a broker-dealer or investment adviser.** I found no equivalent clause in the Commercial (API) Terms. If LLM output feeds trading, plan-based automation sits closer to this line than API use. Where LLMs only extract and narrate and deterministic code trades, the reliance is indirect; whether that is safe is a lawyer's question.
- The Usage Policy lists finance as high-risk. Its human-review and AI-disclosure duties attach to advice affecting individuals or consumers, so they probably do not apply to your own money, but would if outsiders ever see JARVIS output.

**Unresolved.** On 2026-06-15 Anthropic announced, then paused, a monthly Agent SDK credit ($20 Pro, $100 Max 5x, $200 Max 20x; overage at API rates). Secondary sources conflict on whether it is live. The official page (last updated 2026-06-16, the only first-party source I read) says paused and "working to update the plan". Treat plan policy as unstable and check `/usage` before relying on it.

**API side.** The Commercial Terms say services are "not for consumer use"; a personal API account is a gray area I could not resolve.

### 3. New API account limits (FETCHED)

- Prepaid credits are the main payment method and expire after 1 year. The minimum purchase is not stated (UNVERIFIED).
- New organizations may start in an "Evaluation tier" below standard limits; numbers unpublished, rising with usage history.
- Start tier: $500 monthly cap, 1,000 RPM, 2,000,000 ITPM, 400,000 OTPM on Sonnet 5.5 and Haiku 4.5; batch queue 200,000 requests. Build tier cap is $1,000. About 100 requests a night is far below all of this.
- Your own spend limit (Billing page) must sit below the tier cap. At your limit, requests return HTTP 400; at the tier cap, 429.
- Workspaces carry their own spend and rate limits with alerts, up to 100 per organization. **Limits cannot be set on the Default Workspace**, so create a dedicated `jarvis` workspace and key.
- Batches can overshoot, so also keep a small prepaid balance as the real ceiling (my inference).

### 4. Cost scenarios (ESTIMATE; 21 trading nights per month = 252/12; 4.33 weeks per month = 52/12)

**(a) LLM off:** $0. No API credit needed.

**(b) Nightly batch.** Tokens assumed per night:
- 100 news items at 600 tokens each, plus 3 filing excerpts at 8,000 tokens each, plus a 1,500-token prompt and schema on all 103 requests. Input is 100 x 2,100 + 3 x 9,500 = 238,500 tokens.
- Output is 100 x 150 + 3 x 400 = 16,200 tokens.
- Narrative on Sonnet 5.5 batch: 12,000 tokens in x 1.3 = 15,600, and 3,000 out including some thinking.
- No caching assumed.

| Variant | Nightly arithmetic | Month |
|---|---|---|
| b1: extraction on Haiku 4.5 batch, narrative on Sonnet 5.5 batch | 0.2385 x $0.50 + 0.0162 x $2.50 = $0.160; narrative 0.0156 x $1 + 0.003 x $5 = $0.031; total $0.190 | x 21 = **$4.00** |
| b2: extraction on Sonnet 5.5 batch (tokens x 1.3) | 0.310 x $1 + 0.0211 x $5 = $0.415; plus narrative $0.031 = $0.446 | x 21 = **$9.37** |
| b2 at 3x volume | 3 x $9.37 | **$28.1** |

Caching on Sonnet 5.5 might save about $3 a month at best (200,900 cacheable tokens a night x 90% hit x 0.9 x $1/MTok x 21 = $3.4, best-effort in batch). Not counted.

**(c) (b) plus a weekly session (API, not batchable).** Central session: 60 turns, each with 80,000 cached read tokens, 3,000 newly written tokens and 2,500 output.
- Sonnet 5.5: 80,000 x $0.20/M + 3,000 x $2.50/M + 2,500 x $10/M = $0.016 + $0.0075 + $0.025 = $0.0485 per turn. x 60 plus $0.05 initial load = $2.96 per session; x 4.33 = **$12.8 a month**.
- Opus 5.5: $0.016 + $0.015 + $0.050 = $0.081 per turn, $4.96 per session, **$21.5 a month**.
- Heavy session (150 turns, 120,000 read, 4,000 written, 3,000 out), Sonnet 5.5: $0.064 x 150 = $9.6 per session, **$41.6 a month**.
- Totals: b1 + Sonnet central = $16.8; b2 + Sonnet central = **$22.2**; b2 + Opus central = $30.9; stress (3x b2 + heavy) about $70.
- If you already pay for Pro ($20/month, $17 annual), an interactive weekly session costs $0 extra; if not, Pro costs about what the API session does.

**Share of capital (ESTIMATE, per year):**

| Variant | $/year | % of $1,000 | % of $10,000 |
|---|---|---|---|
| b1 | $48 | 4.8% | 0.48% |
| b2 | $112 | 11.2% | 1.1% |
| c (b2 + Sonnet) | $266 | 26.6% | 2.7% |

At $1,000 only (a) or b1 is defensible against the near-zero budget. Brief 11's rule (drag under 2% a year) implies capital of at least $2,400 for b1 and $5,600 for b2.

### 5. Audit and replay

Sampling controls are gone on 4.7+ models, so replay means stored responses, not re-running the model. Record per call in your own store (Batch results vanish after 29 days):
- Exact model ID, the `model` field the API returns, SDK version, beta headers.
- Full request (system, messages, schema, `effort`, `thinking`, `max_tokens`), prompt-template hash and git commit.
- Full raw response, `stop_reason`, `usage` (including cache read/write tokens), `request-id`, `anthropic-workspace-id`, batch ID and `custom_id`.
- Input item IDs with `first_seen_at`/`available_at`; parse and validation result; fallback used (FLAT).
- Computed cost, from a dated copy of the price table.

**Re-validation after a model change.**
1. Freeze a golden set (about 300 items) with partly deterministic answers, such as 8-K item numbers and Form 4 transaction codes.
2. Shadow old and new models on the same live inputs for 2-4 weeks.
3. Compare schema-valid rate, field agreement, refusal and truncation rates, tokens per item (tokenizer changes) and cost, against thresholds set beforehand.
4. Restart the forward evidence clock. Haiku 4.5's training cutoff is Jul 2025, so its clean window is already about 14 months; the 5.5 models (Jun 2026) have about 3. Archive Haiku outputs now.
5. LLM-derived features stay at zero weight until they pass.

## What this decides for the JARVIS design

- **Core runs with LLM off** (a); the LLM is an optional add-on under a hard cap.
- **Production LLM path uses an API key and Batch** in a dedicated workspace, self-set limit about $15 a month, small prepaid balance. It does not depend on a plan login (unstable plan policy, Consumer Terms 3(9), shared 5-hour/weekly pools, machine must stay awake).
- **Plan use is for owner-attended Claude Code**: building JARVIS and the weekly research session. If the owner already pays for Pro, expect $0 extra.
- **Model choice.** Start extraction on pinned Haiku 4.5 (b1, about $4 a month) and archive outputs. Budget a swap to Haiku 5.5 or Sonnet 5.5 (about 2.6x cost) at the roughly 12-month cadence. Keep the model ID in config.
- **Build the record-and-replay store and golden-set harness first.** Then a model swap is a procedure, not a rewrite.
- **Before live capital, decide whether any LLM output may influence order generation.** If not, 3(9) is moot; if yes, get advice.

## Open uncertainties

- Whether the Agent SDK credit is live; plan numeric limits (none read first-party).
- Haiku 5.5 date and price; whether Haiku 4.5 gets a deprecation notice by mid-October.
- Evaluation-tier numbers, minimum credit purchase, personal API account under "not for consumer use".
- Real token counts (600/8,000-token items are assumptions), Sonnet 5.5 thinking overhead, batch cache hit rate.
- Whether Terms 3(9) reaches indirect LLM use in a self-directed trading system. Fetched Consumer Terms are dated 2025-10-08 and Commercial Terms 2025-06-17; I did not confirm these are the latest.
- WebFetch passes pages through a summarizer; re-read exact wording of terms on the source page before relying on it.

## Source list

- Models overview: https://platform.claude.com/docs/en/about-claude/models/overview
- Pricing: https://platform.claude.com/docs/en/about-claude/pricing
- Model deprecations: https://platform.claude.com/docs/en/about-claude/model-deprecations
- Model IDs and versioning: https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions
- Sonnet 5.5 model page: https://platform.claude.com/docs/en/models/sonnet-5-5/overview
- Haiku 4.5 model page: https://platform.claude.com/docs/en/models/haiku-4-5/overview
- Prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Batch processing: https://platform.claude.com/docs/en/build-with-claude/batch-processing
- Effort: https://platform.claude.com/docs/en/build-with-claude/effort
- Structured outputs: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- Rate limits and spend limits: https://platform.claude.com/docs/en/api/rate-limits
- Workspaces: https://platform.claude.com/docs/en/manage-claude/workspaces
- API overview (response headers): https://platform.claude.com/docs/en/api/overview
- API and data retention: https://platform.claude.com/docs/en/manage-claude/api-and-data-retention
- Release notes: https://platform.claude.com/docs/en/release-notes/overview
- Opus 5.5 announcement (Haiku 5.5 statement): https://www.anthropic.com/claude-opus-5-5
- Claude Code legal and compliance: https://code.claude.com/docs/en/legal-and-compliance
- Claude Code authentication: https://code.claude.com/docs/en/authentication
- Run Claude Code programmatically: https://code.claude.com/docs/en/headless
- Routines: https://code.claude.com/docs/en/routines
- Desktop scheduled tasks: https://code.claude.com/docs/en/desktop-scheduled-tasks
- Costs: https://code.claude.com/docs/en/costs
- Agent SDK overview: https://code.claude.com/docs/en/agent-sdk/overview
- Agent SDK with your plan (support): https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan
- Claude Code with Pro/Max (support): https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan
- Paying for API usage (support): https://support.claude.com/en/articles/8977456-how-do-i-pay-for-my-api-usage
- Consumer Terms: https://www.anthropic.com/legal/consumer-terms
- Commercial Terms: https://www.anthropic.com/legal/commercial-terms
- Usage Policy: https://www.anthropic.com/legal/aup
- Consumer plan prices: https://claude.com/pricing
- Secondary, for the policy-volatility point only: https://venturebeat.com/technology/anthropic-reinstates-openclaw-and-third-party-agent-usage-on-claude-subscriptions-with-a-catch


## Independent verification (2026-10-01)

Method: re-fetched primary pages on 2026-10-01 (WebFetch summarizer; exact legal wording should still be re-read on the page) and recomputed all arithmetic.

**Confirmed**
- Prices, batch prices, cache read rates (Fable 5.1 $0.25 = 0.025x, Opus 5.5 $0.20 = 0.05x, Sonnet 5.5 $0.20, Haiku 4.5 $0.10), 5m/1h write multipliers 1.25x/2x, Batch -50% stacking with caching: https://platform.claude.com/docs/en/about-claude/pricing
- New tokenizer about 30% more tokens for 4.7+ models (same page). Haiku 4.5 uses the old tokenizer.
- Retirement floors (Haiku 4.5 not before 2026-10-15; Sonnet 5.5 2027-09-28; Opus 5.5 2027-09-22; Fable 5.1 2027-09-01); Sonnet 4.5 deprecated 2026-09-30, retires 2026-11-30, replacement claude-sonnet-5-5; at least 60 days' notice; deprecation-to-retirement gaps (60-62 days, 114, 189) recomputed correctly: https://platform.claude.com/docs/en/about-claude/model-deprecations
- Haiku 4.5 minimum cacheable 4,096 tokens; Sonnet 5.5 / Opus 5.5 / Fable 5.1 512: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Haiku 4.5 training cutoff Jul 2025 (reliable Feb 2025); Sonnet 5.5 Jun 2026: https://platform.claude.com/docs/en/about-claude/models/overview
- Opus 5.5 announcement says Haiku 5.5 "will follow in the coming weeks" (Sonnet 5.5 has since shipped, Haiku 5.5 has not): https://www.anthropic.com/claude-opus-5-5
- Rate limits: Start $500 / Build $1,000 cap; Start Sonnet 5.5 and Haiku 4.5 = 1,000 RPM, 2M ITPM, 400k OTPM; batch queue 200,000; Evaluation tier exists with unpublished lower limits; self-set limit returns HTTP 400 `invalid_request_error`; tier cap returns HTTP 429 `enforced_spend_limit_reached` with no retry-after: https://platform.claude.com/docs/en/api/rate-limits
- Workspaces: no limits on Default Workspace; 100 workspaces/org; caches isolated per workspace: https://platform.claude.com/docs/en/manage-claude/workspaces
- Batch: 100,000 requests or 256 MB; 24 h expiry; results 29 days; can slightly exceed workspace spend limit; cache hits best-effort, 1-hour TTL recommended: https://platform.claude.com/docs/en/build-with-claude/batch-processing
- Sonnet 5.5: default effort high; `thinking: {"type":"between_tools"}` is real, works at low/medium/high, 400 at xhigh/max: https://platform.claude.com/docs/en/build-with-claude/effort
- Consumer Terms (effective 2025-10-08) contain both the automated-access ban (exception: API key or "otherwise explicitly permit") and the clause barring reliance on the Services to buy/sell securities or give/receive securities advice: https://www.anthropic.com/legal/consumer-terms. The section numbers 3(7) and 3(9) were not visible in the summary; the wording is confirmed.
- Agent SDK credit change PAUSED; `claude -p` and Agent SDK still draw from subscription limits: https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan
- Routines: Pro/Max/Team/Enterprise, research preview, 1-hour minimum interval, 100 scheduled runs/hour/account (also 30/hour per routine for Run now/API), draw subscription usage: https://code.claude.com/docs/en/routines
- `claude setup-token` one-year token for CI/scripts, needs paid plan; `--bare` ignores CLAUDE_CODE_OAUTH_TOKEN; in `-p` mode ANTHROPIC_API_KEY is always used when present: https://code.claude.com/docs/en/authentication

**Arithmetic re-check**
- b1: 0.2385 x 0.5 + 0.0162 x 2.5 = 0.1598; narrative 0.0306; 0.190/night; x21 = $3.99. Correct.
- b2: 238,500 x 1.3 = 310,050 in; output 16,200 x 1.3 = 21,060; 0.310 + 0.1053 = 0.415; + 0.031 = 0.446; x21 = $9.37. Correct. 2.6x ratio Haiku to Sonnet extraction: 0.415/0.160 = 2.6. Correct.
- Caching saving about $3.4/month (ignores write cost): reproduces.
- Sonnet session 60 x 0.0485 + 0.05 = $2.96; x 52/12 = $12.8. Heavy 150 x 0.064 = $9.6; $41.6/month. Correct.
- **Corrected:** Opus central session: 60 x 0.081 = 4.86; + 0.05 = **$4.91** (not $4.96); month **$21.3** (not $21.5). Totals: b2 + Opus = **$30.7** (not $30.9). Immaterial to decisions.
- Annual and % of capital rows, and the capital implied by Brief 11's 2% rule ($2,400 / $5,600): correct.

**Weakened or to qualify**
- The legal-and-compliance page (https://code.claude.com/docs/en/legal-and-compliance) says advertised Pro/Max limits assume ordinary individual use of Claude Code and the Agent SDK, and that developers building products or services, including with the Agent SDK, should use API-key auth. A personal job on your own machine is not a product, so the brief's conclusion stands, but it is a policy-volatile gray zone, so keep the production LLM path on API key (as the brief recommends).
- The self-set cap "about $15 a month" covers b1 and b2 alone (about $4 to $9.4); it is below c ($22 to $31). If the weekly API session is added, raise the cap or run that session on the plan interactively.

**Could not verify**
- Minimum prepaid credit purchase, and that prepaid credits expire after 1 year (not re-checked).
- Batch API not ZDR-eligible (page only points to the data-retention page).
- Evaluation-tier numeric limits (unpublished).
- Consumer Terms section numbers; whether the Consumer/Commercial Terms versions are the latest.
- Haiku 5.5 date and price; whether Haiku 4.5 gets a deprecation notice by 2026-10-15.
- Commercial Terms "not for consumer use" wording for a personal API account (not re-read).

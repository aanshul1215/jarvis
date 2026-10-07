# 03 - Agent orchestration stack for JARVIS

Research date: 2026-10-01. All "FETCHED" items were opened in this session. Fetched pages were read through a
summarising fetch tool, so exact wording and some dates carry a small transcription risk; where I saw the tool
get a date wrong (it reported 2024 for LangGraph releases that PyPI dates 2026) I say so.

## 1. Questions asked

1. LangGraph in late 2026: persistence/checkpointing, human-in-the-loop interrupts, stability, licence.
2. Claude Agent SDK and Claude API (tool use, structured outputs, prompt caching, batch, subagents): what they give
   a long-running local service.
3. Alternatives: plain Python state machine, Temporal, Prefect, Pydantic AI, DBOS.
4. Recommendation for a solo developer, and how to make agent steps replayable and auditable.

Facts I decided I needed, and the authoritative source for each: LangGraph version/licence (PyPI, GitHub);
LangGraph replay semantics (docs.langchain.com); Agent SDK runtime model, hooks, sessions, hosting
(code.claude.com/docs); API features and prices (platform.claude.com/docs); model lifetime (Anthropic
deprecations page); Temporal/DBOS/Prefect/Pydantic AI (their own docs and repos).

## 2. Findings

### 2.1 LangGraph

- **Version, licence, cadence.** Latest is `langgraph` 1.2.12, MIT, Python >=3.10; depends on `langchain-core`,
  `langgraph-checkpoint` 4.x, `langgraph-prebuilt`, `langgraph-sdk`. PyPI history shows 1.0.0 on 2025-10-17 and
  eight releases between 2026-06-12 and 2026-09-21 (roughly one every 2 weeks). ~42.5k GitHub stars.
  Source: https://pypi.org/pypi/langgraph/json , https://pypi.org/project/langgraph/#history ,
  https://github.com/langchain-ai/langgraph - FETCHED - high.
- **Stability policy.** 1.0 is described as an LTS line with no breaking public-API changes until 2.0. A GitHub
  issue (#6363) nevertheless reports a breaking change shipped in `langgraph-prebuilt` 1.0.2.
  Source: https://docs.langchain.com/oss/python/release-policy , https://github.com/langchain-ai/langgraph/issues/6363
  - search-result summaries only, pages not opened - medium. Implication: pin exact versions of all four packages.
- **Checkpointers.** InMemorySaver (lost on restart), SqliteSaver (local file), PostgresSaver/AsyncPostgresSaver.
  State is saved per `thread_id`; checkpoints accumulate and need pruning.
  Source: https://docs.langchain.com/oss/python/langgraph/persistence - FETCHED - high.
- **Durability modes.** `exit` (persist only when the run ends: no mid-run crash recovery), `async` (default,
  written in background, small loss window on crash), `sync` (written before next step).
  Source: docs.langchain.com (thinking-in-langgraph / durable execution pages) - search-result summary - medium.
- **Interrupts (human-in-the-loop).** `interrupt()` needs a checkpointer and thread_id; resume with
  `Command(resume=...)`. On resume **the node restarts from its first line**, so anything before the interrupt
  runs again and must be idempotent. Multiple interrupts are matched by index, so control flow must be
  deterministic. 1.2.12 added a `response_schema` parameter to `interrupt()`.
  Source: https://docs.langchain.com/oss/python/langgraph/interrupts ,
  https://github.com/langchain-ai/langgraph/releases - FETCHED - high.
- **Replay semantics.** In the functional API the entrypoint replays from the start and completed `@task` results
  are read back from the checkpoint. Non-deterministic work (time, random, API/LLM calls) must be inside tasks;
  a task that started but did not finish may run again, so side effects need idempotency keys.
  Source: https://docs.langchain.com/oss/python/langgraph/functional-api - FETCHED - high.
- **What is and is not open source.** The library is MIT. The hosted/"Agent Server" deployment layer
  (LangSmith Deployment, formerly LangGraph Platform) is a commercial product; search results state the stock
  `langgraph-api` server is under Elastic License 2.0 with a limited free self-hosted tier.
  Source: GitHub README (FETCHED, high for "separate commercial offerings"); licence detail from search
  summaries of third-party repos - **low, unverified**. JARVIS does not need that server: the library plus a
  Postgres checkpointer runs inside your own process.

### 2.2 Claude Agent SDK

- **What it is.** "Claude Code as a library" for Python and TypeScript. `query()` **spawns a `claude` CLI
  subprocess** and talks to it over stdio; one session = one subprocess owning a shell, a working directory and
  JSONL transcripts on disk. Python package `claude-agent-sdk` 0.2.163 (MIT package; use is governed by
  Anthropic's Commercial Terms). Source: https://code.claude.com/docs/en/agent-sdk/overview ,
  https://code.claude.com/docs/en/agent-sdk/hosting , https://pypi.org/pypi/claude-agent-sdk/json - FETCHED - high.
- **Auth.** API key. The docs state Anthropic does not allow third-party developers to offer claude.ai login or
  subscription rate limits in their products. Source: overview page - FETCHED - high. Whether a personal,
  single-user automation on a subscription is acceptable is **not answered by that page** - unverified; budget
  for API-key billing.
- **Resources and limits.** Starting point 1 GiB RAM, 5 GiB disk, 1 CPU per agent; memory grows with session
  length; no top-level session timeout (bound with `max_turns`); no per-subagent wall-clock deadline; wide
  subagent fan-outs can hit rate limits. Docs say token cost usually exceeds container cost by 10x or more.
  Source: hosting page - FETCHED - high.
- **Sessions.** Transcripts in `~/.claude/projects/<encoded-cwd>/*.jsonl`; resume/fork/continue by session id;
  `SessionStore` adapter mirrors transcripts to your storage, but **mirror writes are best-effort** (failed
  batches are dropped with a `mirror_error` message). The docs themselves say capturing results as application
  state is "often more robust" than relying on resume. Source: sessions + hosting pages - FETCHED - high.
- **Hooks.** `PreToolUse` callbacks run in your process and can allow/deny/ask/defer or rewrite tool input;
  deny wins over everything. Python supports a subset (PreToolUse, PostToolUse, PostToolUseFailure,
  UserPromptSubmit, Stop, SubagentStart/Stop, PreCompact, PermissionRequest, Notification); many events are
  TypeScript-only. A `PreToolUse` hook that times out causes the tool not to run. Hooks may not fire when the
  agent hits `max_turns`. Source: https://code.claude.com/docs/en/agent-sdk/hooks - FETCHED - high.
- **Subagents.** Defined with `AgentDefinition` (description, prompt, tools, model, maxTurns, effort...); fresh
  context, only the final message returns; run in background by default; can nest (default depth 3, 20
  concurrent); `max_budget_usd` caps spend for the whole tree. The parent **model decides** when to delegate.
  Source: https://code.claude.com/docs/en/agent-sdk/subagents - FETCHED - high.
- **Structured output.** `output_format` JSON schema (draft-07); SDK validates and re-prompts; can end with
  `error_max_structured_output_retries` or even `success` with no structured output - both must be treated as
  failure. Source: https://code.claude.com/docs/en/agent-sdk/structured-outputs - FETCHED - high.

### 2.3 Claude API (Messages API)

- **Structured outputs are GA** with constrained decoding: `output_config.format` (JSON schema) and `strict: true`
  tools. Limits that matter here: no numeric `minimum`/`maximum`, no string length limits, no recursion,
  `additionalProperties` must be false, max 20 strict tools and 24 optional parameters. Output can still violate
  the schema on `stop_reason: "refusal"` or `"max_tokens"`.
  Source: https://platform.claude.com/docs/en/build-with-claude/structured-outputs - FETCHED - high.
- **Prices (USD per million tokens, input/output).** Haiku 4.5 $1/$5; Sonnet 5.5 and Sonnet 5 $2/$10;
  Opus 5.5 $4/$20; Opus 5 $5/$25; Fable 5.1 $10/$50. Cache read 0.1x input (0.05x Opus 5.5, 0.025x Fable 5.1),
  5-minute cache write 1.25x, 1-hour write 2x. Batch API 50% off both directions, stackable with caching.
  Models from 4.7 onward use a tokenizer producing about 30% more tokens for the same text. 1M context at
  standard price on 4.6+. Source: https://platform.claude.com/docs/en/about-claude/pricing - FETCHED - high.
- **Prompt caching.** Up to 4 breakpoints; minimum cacheable prefix 512 tokens on Sonnet 5.5/Opus 5.5/Haiku 4.5;
  changing tool definitions or the output schema invalidates the cache.
  Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching - FETCHED - high. (The fetch
  summary claimed caching "does not work with Batch"; the batch page itself has a section on using caching in
  batches, so I treat the summary as wrong.)
- **Batch.** Up to 100,000 requests or 256 MB; most finish within 1 hour, can take 24 hours and can expire;
  results kept 29 days; no streaming. Not usable for live decisions.
  Source: https://platform.claude.com/docs/en/build-with-claude/batch-processing - FETCHED - high.
- **Tool runner.** A beta helper in the client SDKs that runs the tool loop; the docs say to use the manual loop
  when you need human approval, custom logging or conditional execution.
  Source: https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner - FETCHED - high.
- **No deterministic sampling.** `temperature`, `top_p`, `top_k` return a 400 error at non-default values on
  Opus 4.7 and later; docs add that temperature 0 never guaranteed identical outputs.
  Source: https://platform.claude.com/docs/en/about-claude/model-deprecations (parameter table) - FETCHED - high.
- **Model lifetime.** At least 60 days' notice before retirement. Current tentative dates: Sonnet 5.5 not before
  2027-09-28, Opus 5.5 not before 2027-09-22, Haiku 4.5 not before 2026-10-15 (i.e. could be deprecated soon),
  Sonnet 4.5 retires 2026-11-30. Source: same page - FETCHED - high.

### 2.4 Alternatives

- **Temporal.** MIT server; workflows are replayed from a full event history and must be deterministic; all
  external calls (including LLM calls) go in Activities whose results are recorded. Local dev server via
  `temporal server start-dev`. The Python SDK sandbox is documented as "not completely isolated" and reloads
  non-passthrough modules per workflow run. Source: https://docs.temporal.io/workflows ,
  https://github.com/temporalio/temporal , https://docs.temporal.io/develop/python/python-sdk-sandbox - FETCHED -
  high. Production database requirements not confirmed in what I fetched - unverified.
- **DBOS Transact (Python).** MIT library; `@DBOS.workflow()` / `@DBOS.step()` decorators checkpoint each step
  into Postgres (SQLite default for dev) and resume from the last completed step; durable queues, cron
  scheduling, durable sleep, exactly-once workflow start per event. No separate server.
  Source: https://docs.dbos.dev/python/programming-guide , https://github.com/dbos-inc/dbos-transact-py - FETCHED -
  high. Smaller project (~1.6k stars): bus-factor risk - medium.
- **Prefect 3.** Python flows/tasks with retries, result caching and pause-for-approval; needs Prefect Cloud or
  a self-hosted server. Data-pipeline oriented. Source: https://docs.prefect.io/v3/get-started - FETCHED - medium.
- **Pydantic AI.** MIT, v2.52.0, typed agent loop with durable-execution integrations for Temporal, DBOS,
  Prefect, Restate, AWS Lambda. Its docs stress durability is not conversation storage.
  Source: https://pydantic.dev/docs/ai/integrations/durable_execution/overview/ ,
  https://pypi.org/pypi/pydantic-ai/json - FETCHED - high (release date not reliably extracted).
- **Plain Python state machine on Postgres.** No source needed; this is a design option, assessed below.

## 3. What this means for the JARVIS documents

**Supported**
- v3 "Orchestrator: LangGraph; deterministic routing for money-critical steps" and v2 "LangGraph: state/checkpoints,
  fault recovery and human approval" are factually accurate about what LangGraph offers. It is MIT, on a stable
  1.x line, and has a Postgres checkpointer that fits the planned PostgreSQL system of record.
- v3 build step 6 ("agents produce structured evidence; they do not directly send broker orders") and the
  "no LLM override" Capital Governor are strongly supported: structured outputs are now GA with constrained
  decoding, so a typed evidence contract between agents and deterministic code is practical.
- v3 Position Manager as "streaming state + deterministic exits" is right. An LLM call takes seconds and can
  refuse or truncate; it must not sit in the exit path.

**Weakened**
- "Fault recovery" is weaker than it sounds. LangGraph (and DBOS, Temporal) give at-least-once step execution:
  a node restarts from its top after an interrupt or crash. Exactly-once order submission is **not** provided by
  the orchestrator; it must come from a client order id / idempotency key in the execution service and a
  reconcile-with-broker step on restart. The v3 "idempotent order service" line is therefore essential, not
  optional, and the default `async` durability mode should not be used for anything touching money.
- "Every decision must be reconstructable" (v3 step 9, Architecture layer I) cannot mean "re-run the agent and
  get the same answer". Sampling parameters are gone on current models, outputs were never guaranteed
  deterministic, and the model that made the decision will be retired roughly 12-24 months later. Reconstructable
  must be defined as **record-and-replay**: store the exact request and the exact response.
- "Confidence" numbers from Bull/Bear or thesis agents cannot be range-constrained by the schema (no
  minimum/maximum). They need Pydantic validation after the call, and failure handling for `refusal` and
  `max_tokens` stop reasons (default: treat as no evidence, i.e. FLAT).
- The 18-agent roster overstates how many components should be LLM agents. By the docs' own "suggested stack"
  column only Bull/Bear (and parts of News/Event, Fundamental, Ledger/Review narrative, daily summary) are
  LLM work. A "supervisor" LLM that chooses which agents to call adds non-determinism for no benefit when the
  pipeline order is fixed; it should be code.

**Contradicted / unwelcome**
- Running every specialist as a Claude Agent SDK agent is a poor fit for the live path: each session is a CLI
  subprocess with ~1 GiB RAM and a coding-agent toolset, delegation to subagents is decided by the model, there
  is no session timeout, and the Python SDK exposes fewer hooks than TypeScript. Its strengths (file, shell,
  web tools, long autonomous sessions) match the offline Strategy Lab, not the trade pipeline.
- LLM cost versus the worked example. My arithmetic from fetched prices with assumed sizes: one agent call on
  Sonnet 5.5 with 6k cached + 2k fresh input and 1k output tokens costs about $0.0012 + $0.004 + $0.01 =
  ~$0.015. Six LLM agents per candidate = ~$0.09. Fifty candidates a day = ~$4.50/day, ~$135/month. The
  documents' example trade nets +$0.27 on a $100 account. LLM reasoning must therefore be gated (run only on
  candidates that already passed cheap statistical filters), cached, and pushed to Haiku or Batch where possible,
  or the system loses money on inference alone at small capital. Token assumptions are mine - medium confidence.

## 4. Recommended changes

1. **Split orchestration into two planes.**
   - *Control plane (money path)*: a plain, explicit Python finite-state machine
     (OBSERVE -> INVESTIGATE -> VALIDATE -> READY -> EXECUTE -> MANAGE -> SAFE/LEARN) whose transitions are rows
     in PostgreSQL written in the same transaction as the decision they record. Risk gate, sizing, order
     submission and exits are ordinary typed functions. No LLM, no agent framework. If you want crash-resume
     without hand-rolling it, wrap the steps with DBOS (Postgres-only, no extra server); Temporal is the heavier
     option and is not justified for one laptop and one developer.
   - *Reasoning plane (evidence)*: LLM "agents" are stateless functions `evidence = agent(snapshot)` called
     through the Anthropic Messages API directly with strict JSON-schema output. They receive a frozen,
     point-in-time snapshot id and return typed evidence. They have no broker tools at all.
2. **LangGraph: optional, and only inside the reasoning plane.** It earns its place if the research flow becomes
   genuinely graph-shaped (parallel specialists, bull/bear rounds, a human-approval interrupt). If adopted: use
   PostgresSaver, `sync` durability, pinned versions, and keep it out of risk/execution. A first version with
   `asyncio.gather` over five or six API calls does not need it. Do not adopt the commercial Agent Server.
3. **Claude Agent SDK: Strategy Lab and operations only.** Use it for offline hypothesis research, backtest
   code generation, post-trade review drafting - in a sandboxed container with no broker credentials, with
   `max_turns`, `max_budget_usd`, restricted `tools`, and a `PreToolUse` deny-by-default hook.
4. **Human approval** (large trade, paper-to-live, new model): implement as a pending-approval row plus
   notification in the control plane, with an expiry that defaults to *reject*. This is simpler and more
   auditable than a framework interrupt and survives any framework change.
5. **Audit record per LLM call** (append-only table): decision id, agent name, prompt template version/hash,
   schema version, exact model id, full request JSON, full response JSON, stop_reason, token usage and cost,
   snapshot id, latency, validation result. "Replay" = re-run the deterministic pipeline feeding recorded
   responses; "what-if" = re-run with a live model, labelled as a new experiment. Export OpenTelemetry spans
   with the same decision id.
6. **Model tiering and cost control.** Haiku for classification/dedup, Sonnet 5.5 for specialist evidence, Opus
   only for rare deep reviews; cache the static system prompt + schema prefix; Batch API (50% off) for nightly
   attribution, daily summary and backtest-time news labelling. Add a daily LLM budget that the Capital Governor
   treats like any other limit.
7. **Model-change gate.** Treat a model id change like a new ML model version: shadow-run old vs new on recorded
   snapshots before promotion, since retirement will force migrations about yearly.

Trade-offs for a solo developer: the plain-Python control plane costs more initial code (state table, retry,
reconcile) but has no hidden replay semantics and nothing to upgrade; LangGraph saves code for fan-out/interrupt
flows but brings four pinned packages and at-least-once node semantics you must still design around; Temporal
gives the strongest guarantees at the highest operational and learning cost.

## 5. Open uncertainties

- Exact licence terms and free-tier limits of the LangGraph Agent Server (low confidence; irrelevant if unused).
- Whether a personal single-user service may run the Agent SDK on a claude.ai subscription rather than API
  billing - not stated on the pages fetched.
- Rate limits for the owner's API tier (not fetched); they bound parallel agent fan-out.
- Real token counts per agent call; my cost estimate uses assumed sizes.
- LangGraph durability-mode details came from a search summary, not a page I opened in full.
- Temporal self-hosted production requirements and DBOS long-term project health were not verified.
- Claude Managed Agents ($0.08 per session-hour plus tokens) was seen on the pricing page but not evaluated;
  it conflicts with the local-first goal.

## 6. Source list

- https://pypi.org/pypi/langgraph/json ; https://pypi.org/project/langgraph/#history
- https://github.com/langchain-ai/langgraph ; https://github.com/langchain-ai/langgraph/releases
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/langgraph/interrupts
- https://docs.langchain.com/oss/python/langgraph/functional-api
- https://docs.langchain.com/oss/python/release-policy (search summary only)
- https://code.claude.com/docs/en/agent-sdk/overview , /hosting , /sessions , /hooks , /subagents , /structured-outputs
- https://pypi.org/pypi/claude-agent-sdk/json
- https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- https://platform.claude.com/docs/en/about-claude/pricing
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- https://platform.claude.com/docs/en/build-with-claude/batch-processing
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner
- https://platform.claude.com/docs/en/about-claude/model-deprecations
- https://docs.temporal.io/workflows ; https://github.com/temporalio/temporal ; https://docs.temporal.io/develop/python/python-sdk-sandbox
- https://docs.dbos.dev/python/programming-guide ; https://github.com/dbos-inc/dbos-transact-py
- https://docs.prefect.io/v3/get-started
- https://pydantic.dev/docs/ai/integrations/durable_execution/overview/ ; https://pypi.org/pypi/pydantic-ai/json

## Independent verification (2026-10-01)

Done by a separate fact-checking agent. Pages were re-opened today; several came back verbatim, others through a
summarising fetch (marked "summary"). Overall reliability of the brief: **high on facts, medium on the cost estimate**.

### Confirmed (source re-opened, says what the brief claims)

- LangGraph 1.2.12, MIT, Python >=3.10, deps langchain-core / langgraph-checkpoint >=4.1 / langgraph-prebuilt /
  langgraph-sdk; 42,537 stars, pushed today. https://pypi.org/pypi/langgraph/json ,
  https://api.github.com/repos/langchain-ai/langgraph (release dates not re-extractable - summary).
- LangGraph release policy: 1.0 is LTS, "breaking changes to the public API will only occur in major version
  releases". Issue #6363 exists, dated 2025-10-30, still OPEN: `langgraph-prebuilt` 1.0.2 added a required
  `runtime` parameter to `ToolNode.afunc`. Both were only search summaries in the brief; now opened.
  https://docs.langchain.com/oss/python/release-policy , https://github.com/langchain-ai/langgraph/issues/6363
- Interrupts: node restarts from its beginning on resume; index-based matching; pre-interrupt side effects must
  be idempotent; `response_schema` exists. https://docs.langchain.com/oss/python/langgraph/interrupts
- Durability modes exit/async/sync as described (https://docs.langchain.com/oss/python/langgraph/checkpointers).
  Default = "async" per the reference docs for `Pregel.stream/invoke` (search snippet of
  https://reference.langchain.com/python/langgraph/pregel/main/Pregel/stream , page not opened) - medium.
- Claude prices (verbatim table): Haiku 4.5 $1/$5; Sonnet 5.5 and Sonnet 5 $2/$10; Opus 5.5 $4/$20; Opus 5
  $5/$25; Fable 5.1 $10/$50; cache read 0.1x (0.05x Opus 5.5, 0.025x Fable 5.1); writes 1.25x / 2x; Batch 50%
  off and stackable with caching; ~30% more tokens on 4.7+ tokenizer; 1M context at standard price; Managed
  Agents $0.08/session-hour. https://platform.claude.com/docs/en/about-claude/pricing
- Model lifetime table (verbatim): Sonnet 5.5 not sooner than 2027-09-28; Opus 5.5 2027-09-22; Haiku 4.5 Active,
  not sooner than 2026-10-15; Sonnet 4.5 deprecated 2026-09-30, retires 2026-11-30; 60 days' notice.
  `temperature/top_p/top_k` return 400 at non-default values on 4.7+ models.
  https://platform.claude.com/docs/en/about-claude/model-deprecations
- Structured outputs GA via `output_config.format`; no minimum/maximum, minLength/maxLength, recursion;
  `additionalProperties` must be false; 20 strict tools, 24 optional params (also 16 union-typed params);
  refusal / max_tokens can break the schema. https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- Batch: 100,000 requests or 256 MB, most < 1 h, expire at 24 h, results 29 days; prompt caching IS supported
  in batches (best-effort; docs suggest the 1-hour TTL). The brief was right to overrule its fetch summary.
  https://platform.claude.com/docs/en/build-with-claude/batch-processing
- Agent SDK: spawns a `claude` CLI subprocess per session; 1 GiB / 5 GiB / 1 CPU starting point (a floor); no
  top-level session timeout; no per-subagent wall-clock deadline; mirror writes best-effort (`mirror_error`);
  token cost "an order of magnitude or more" above container cost. Python hook subset exactly as listed;
  PreToolUse timeout => tool not run; hooks may not fire at `max_turns`; deny wins. Subagents: background by
  default, depth 3, 20 concurrent, `max_budget_usd` covers the tree, model decides delegation.
  https://code.claude.com/docs/en/agent-sdk/hosting , /hooks , /subagents , /overview
- `claude-agent-sdk` 0.2.163 MIT; `pydantic-ai` 2.52.0 MIT; DBOS Transact-py MIT, 1,599 stars, pushed today, 4
  open issues, SQLite default / Postgres recommended, no separate server.
  https://pypi.org/pypi/claude-agent-sdk/json , https://pypi.org/pypi/pydantic-ai/json ,
  https://api.github.com/repos/dbos-inc/dbos-transact-py , https://docs.dbos.dev/python/programming-guide

### Corrected

1. **Minimum cacheable prefix.** Brief: "512 tokens on Sonnet 5.5/Opus 5.5/Haiku 4.5". The page lists 512 for
   Sonnet 5.5 / Opus 5.5 / Opus 5 / Fable, **4,096 for Haiku 4.5** and 1,024 for Sonnet 5.
   https://platform.claude.com/docs/en/build-with-claude/prompt-caching (summary). Consequence: a Haiku
   classification/dedup prompt with a prefix under 4,096 tokens gets no cache discount at all.
2. **Cost estimate is a best case, not a midpoint.** $0.015/call assumes every call hits a warm cache. The
   default cache TTL is 5 minutes; ~50 candidates spread over a trading day will mostly miss. Cold call with a
   5-minute write: 6k x $2.50 + 2k x $2 + 1k x $10 = ~$0.029; no caching at all: ~$0.026. So the realistic
   range is roughly $135-$260/month for the same assumptions (before any thinking tokens, which bill as
   output). Use the 1-hour TTL (2x write) only if calls for the same agent recur within the hour. Either end of
   the range is incompatible with the owner's "close to zero" LLM budget (context file section C); the design
   target should be a few LLM calls per day, not six per candidate.
3. **Stale comparison.** "+$0.27 on a $100 account" is the documents' example; the owner's binding constraint is
   $1,000-$10,000 live capital. The conclusion (gate LLM use) still holds but should be argued against the
   budget constraint, not the $100 example.
4. **"temperature 0 never guaranteed identical outputs"** is not on the cited deprecations page. What the page
   does add: the Python SDK v1.0+ removes these parameters (passing them raises `TypeError`). The restriction
   applies to 4.7-and-later models; Haiku 4.5 / Sonnet 4.6 are not listed as affected. The design conclusion
   (record-and-replay, never re-run for audit) is unchanged.
5. **Subscription use of the Agent SDK (brief: "unverified").** Anthropic's help article "Use the Claude Agent
   SDK with your Claude plan" says plan users can run the Agent SDK / `claude -p`; a separate monthly Agent SDK
   credit (Pro $20, Max 5x $100, Max 20x $200) was announced for 2026-06-15 but the article states the change
   is **paused** and such usage "still draw[s] from your subscription's usage limits".
   https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan (summary -
   re-read before relying on it). The overview-page restriction is about third-party developers offering
   claude.ai login in *their products*. So an existing Claude subscription is a plausible near-zero-marginal-cost
   route for the offline Strategy Lab, subject to plan limits; the Messages API reasoning plane still needs an
   API key and pay-as-you-go billing.
6. **Rate limits (brief: "not fetched").** Start tier: 1,000 RPM, 2,000,000 ITPM, 400,000 OTPM for Sonnet 5.5 /
   Haiku 4.5 / Opus 5.5, $500 monthly spend cap; cache reads do not count toward ITPM; new organisations may
   begin in a lower "Evaluation" tier. https://platform.claude.com/docs/en/api/rate-limits . Not a constraint
   for 5-6 parallel calls; a self-set spend limit in the Console is available as a hard budget backstop.

### Could not verify

- `langgraph-api` / Agent Server licence (Elastic 2.0) and free-tier limits - no primary source opened.
- "DBOS and Temporal give at-least-once step execution": the DBOS programming guide fetched says recovery
  resumes "from its last completed step" but did not state retry/idempotency semantics; Temporal pages not
  re-opened.
- LangGraph PyPI release dates (1.0.0 on 2025-10-17; eight releases Jun-Sep 2026) - the JSON fetch did not
  return dates.
- Prefect 3 and Pydantic AI durable-execution claims - not re-opened (low design impact).
- Agent SDK structured-output failure subtypes and sessions-page details - not re-opened.

### What the brief missed

- The Anthropic Python SDK helpers strip unsupported constraints (e.g. `minimum`) from the sent schema and
  **validate the response against the original schema client-side**, so range checks on confidence fields come
  nearly free when using the SDK's Pydantic helper; hand-rolled validation is only needed with raw HTTP.
- Haiku 4.5 is the only Haiku listed and its "not sooner than" date is two weeks away; no successor Haiku
  appears in the pricing or deprecation tables. A tiering plan that depends on a $1/$5 model should assume it
  may need to move to Sonnet 5.5 ($2/$10) within the project's lifetime.
- Cache economics depend on call cadence versus TTL (see correction 2); the brief's recommendation to "cache the
  static prefix" needs a cadence assumption to be worth anything.
- Schema changes invalidate the message cache on some models and compiled schemas are cached 24 h; keep the
  output schema stable across calls of one agent.

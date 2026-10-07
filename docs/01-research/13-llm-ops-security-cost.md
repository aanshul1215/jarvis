# 13 — Operating LLM agents inside a money pipeline: security, reliability, cost, auditability, secrets

Research date: 2026-10-01. Every finding is tagged FETCHED (opened in this session) or RECALLED (from memory, not re-checked), with a confidence level. Cost figures are my own arithmetic on fetched prices; the workload assumptions are mine and are stated explicitly.

## 1. Questions asked

1. How does prompt injection reach a trading system through news/social/filing text, and which mitigations actually hold?
2. How do we make LLM calls reliable (schemas, retries, timeouts) and what happens if the API is down while a position is open?
3. What does it cost per month, at current Anthropic prices, to (a) call an LLM for every scanner candidate versus (b) only for shortlisted candidates and daily reviews?
4. How do we audit and reproduce LLM decisions, and how do we evaluate an LLM component without look-ahead bias?
5. How should broker and API keys be stored on a local Windows laptop running Docker Compose?

## 2. Findings

### 2.1 Prompt injection through ingested text

- **OWASP LLM01:2025** defines indirect injection as instructions hidden in external content the model processes. Listed mitigations: constrain behaviour, define and validate output formats, filter input/output, least privilege, human approval for high-risk actions, segregate and label untrusted content, adversarial testing. Source: https://genai.owasp.org/llmrisk/llm01-prompt-injection/ — FETCHED, high.
- **Greshake et al. (arXiv 2302.12173)** demonstrated indirect injection against real products (Bing Chat, code completion): data theft, information-ecosystem contamination, control of API calls. Source: https://arxiv.org/abs/2302.12173 — FETCHED (abstract), high.
- **The "lethal trifecta" (Willison)**: an agent that has private data, reads untrusted content and can communicate externally is exploitable. Filters that catch "95%" of attacks are a failing grade in security terms; the working fix is to never combine the three. Source: https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/ — FETCHED, high (practitioner reference, not peer-reviewed).
- **Design patterns paper (Beurer-Kellner et al., arXiv 2506.08837)**: six patterns — action-selector, plan-then-execute, LLM map-reduce, dual LLM (privileged model with tools + quarantined model without tools), code-then-execute, context-minimisation. Governing principle: once an agent has read untrusted input, it must be impossible for that input to trigger a consequential action. Source: https://arxiv.org/html/2506.08837 — FETCHED, high.
- **CaMeL (Debenedetti et al., arXiv 2503.18813)**: separates control flow from data flow; solved 77% of AgentDojo tasks with provable security versus 84% for an undefended system. Security by design costs some utility but is achievable. Source: https://arxiv.org/abs/2503.18813 — FETCHED (abstract), high.
- **Anthropic's own guidance**: put third-party text only in `tool_result` blocks, JSON-encode it, state an untrusted-content policy in the system prompt, apply least privilege, screen tool outputs with a small model, red-team your own agent. The page describes these as strengthening guardrails; it does not claim they are complete. Source: https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks — FETCHED, high.
- **Finance-specific evidence — "Adversarial News and Lost Profits" (Rizvani, Apruzzese, Laskov, arXiv 2601.13082)**. Measured: an LSTM price model plus FinBERT sentiment (and nine other LLMs) trading 10 large-cap US stocks, Feb 2024–Apr 2025, Refinitiv headlines. Two attacks invisible to humans: Unicode homoglyphs in the company name (ticker mapping failed for 99.1% of manipulated headlines) and hidden HTML text (sentiment flipped for 65.6%). Average return reduction about 3.2–3.7 percentage points; worst case 17.7 points from a single manipulated day. Backtest only; no live attack performed; transaction-cost treatment not confirmed from what I read. Defences: Unicode normalisation, HTML stripping, keep raw and rendered copies. Source: https://arxiv.org/html/2601.13082v1 — FETCHED, medium-high.
- **"Poisoning Agentic Alpha" (arXiv 2608.24069)**: tested four multi-agent topologies, five assets, two LLM backbones with role-specific attacks; abstract conclusion is that no architecture was inherently robust and corrupted signals propagate through the pipeline. I read the abstract only; numbers not verified. Source: https://arxiv.org/abs/2608.24069 — FETCHED (abstract), medium. Related titles surfaced by search but NOT opened (unverified): arXiv 2609.19789, 2605.09185.

Note that in JARVIS the realistic attack is less "ignore your instructions and send an order" (the design already blocks that) and more **decision steering**: fabricated or manipulated text that pushes sentiment/thesis scores. This is the same thing as the "low-liquidity social pump" the documents already worry about, and it cannot be fixed by prompt hardening; it is fixed by bounding how much any text-derived score can move size.

### 2.2 Reliability

- **Structured outputs are GA** on current models (Fable 5.1, Opus 5.5, Sonnet 5.5, Haiku 4.5 and others) using constrained decoding; valid JSON matching the schema is guaranteed **except** when `stop_reason` is `refusal` or `max_tokens`. Unsupported: numeric `minimum`/`maximum`, string length limits, recursive schemas. Enum casing is not guaranteed. First call with a new schema has compile latency; grammar cached 24h. Source: https://platform.claude.com/docs/en/build-with-claude/structured-outputs — FETCHED, high. Consequence: a "confidence 0–1" field still needs range validation in Pydantic.
- **Errors**: 429 (rate limit), 500, 504, 529 (overloaded — platform-wide traffic, not your fault). SDK retries transient errors twice by default with backoff. Non-streaming requests have a 10-minute expectation limit. A self-set spend limit returns HTTP 400; a tier spend-cap returns 429 with no `retry-after` and keeps failing until month end. Sources: https://platform.claude.com/docs/en/api/errors and https://platform.claude.com/docs/en/api/rate-limits — FETCHED, high.
- **Forced tool choice** (`tool_choice: any/tool`) is rejected on Opus 5.5, Sonnet 5.5, Fable 5.1. Use `output_config.format` instead. Source: errors page above — FETCHED, high. Any framework code (including older LangGraph/LangChain patterns) that forces a tool call to get JSON will break on the newest models.
- **Broker-side protection when the LLM or the laptop is down (Alpaca)**: bracket/OCO/trailing-stop orders are held server-side for equities, but brackets are not supported in extended hours and **not for fractional-share orders**; crypto supports only market, limit and stop-limit with gtc/ioc — no bracket/OCO. Sources: https://docs.alpaca.markets/docs/orders-at-alpaca , https://docs.alpaca.markets/docs/crypto-orders — FETCHED, medium-high (summarised by fetch tool; verify before coding). With $1k–$10k the account will often hold fractional shares, so server-side brackets are frequently unavailable and crypto exits depend on the local process.

### 2.3 Cost and latency (prices FETCHED from https://platform.claude.com/docs/en/about-claude/pricing , high confidence)

| Model | Input $/MTok | Output $/MTok | Cache read | Batch in/out |
|---|---|---|---|---|
| Claude Haiku 4.5 | 1 | 5 | 0.10 | 0.50 / 2.50 |
| Claude Sonnet 5.5 | 2 | 10 | 0.20 | 1 / 5 |
| Claude Opus 5.5 | 4 | 20 | 0.20 | 2 / 10 |
| Claude Fable 5.1 | 10 | 50 | 0.25 | 5 / 25 |

Other fetched facts that change the arithmetic:
- Cache writes cost 1.25x (5-minute TTL) or 2x (1-hour); batch (50% off) and caching stack.
- **Minimum cacheable prefix: 4,096 tokens on Haiku 4.5, 512 on Sonnet 5.5/Opus 5.5/Fable 5.1** (https://platform.claude.com/docs/en/build-with-claude/prompt-caching). A typical 2–3k-token agent prompt on Haiku is not cached at all.
- Models from 4.7 onward use a tokenizer producing roughly 30% more tokens for the same text; Haiku 4.5 uses the older one.
- Opus 5.5 and Fable 5.1 always think; thinking is billed as output. My estimates below exclude thinking, so real output cost on those models can be a multiple.
- Batch: most finish under 1 hour, hard limit 24 hours, results kept 29 days. Not usable for anything intraday.
- Start tier monthly cap is $500; you can set a lower own limit.
- Web search tool: $10 per 1,000 searches.

**Assumptions (mine):** one LLM call = 3,000 static tokens (role, schema, policy) + 1,500 dynamic tokens (features, headlines) in, 400 out, measured in old-tokenizer tokens; multiplied by 1.3 for Sonnet/Opus 5.5.

Per-call cost: Haiku 4.5 = $0.0065 (no caching possible at this prompt size). Sonnet 5.5 = $0.0169 uncached, about $0.0099 with the static part cached. Opus 5.5 = $0.0338 uncached, about $0.019 cached.

**(a) Always-on scanner, LLM per candidate**

| Workload | Calls/month | Haiku 4.5 | Sonnet 5.5 (cached) | Opus 5.5 (cached) |
|---|---|---|---|---|
| Light: 500 candidates/day, 1 call each | 15,000 | ~$98 | ~$149 | ~$285 |
| As the v3 doc implies: 2,000 candidates/day x 5 agent calls (news, bull, bear, strategy, supervisor) | 300,000 | ~$1,950 | ~$2,970 | ~$5,700 |
| One pass per minute over ~14 symbols, 24/7, x 5 calls | ~3.0M | ~$19,700 | ~$29,900 | ~$57,500 |

Even the light case costs $1,170/year, i.e. 12% of a $10k account or 117% of a $1k account, before any trading cost. The middle case exceeds the Start-tier $500 cap.

**(b) LLM only on shortlist + reviews** (5 shortlisted candidates/day x 30 days; each gets one Haiku extraction call of 6k in/0.5k out and one Sonnet 5.5 thesis-critique call of 8k in/1.5k out; overnight batch of 100 headlines on Haiku; daily review on Sonnet 5.5 batch at 15k in/2.5k out; weekly deep review on Opus 5.5 batch at 40k in/4k out)

- Shortlist: 150 x ($0.0085 + $0.0403) ≈ $7.30
- Overnight headline extraction (batch): ≈ $1.95
- Daily review (batch): ≈ $1.07
- Weekly review (batch): ≈ $0.67
- **Total ≈ $11/month; plausible range $5–25** once thinking tokens and retries are included. Confidence in the order of magnitude: high; in the exact number: low (depends on prompt sizes).

Design (b) is roughly 10x–200x cheaper than (a) and is the only one compatible with a "close to zero" budget. Even $11/month is 1.3% a year on $10k and 13% a year on $1k — a real hurdle the strategy must clear.

**Latency:** the docs give only relative latency (Haiku fastest, Fable slowest); I did not find official per-call numbers. From experience (RECALLED, medium) a structured call takes on the order of one to tens of seconds. That is incompatible with the documents' order-flow/L2 intraday examples, where the signal half-life is shorter than the call.

### 2.4 Auditability, reproducibility, look-ahead

- **Model IDs are pinned snapshots; weights do not change under an ID, but serving infrastructure (router, classifiers, sampling) can change and cause minor behaviour differences.** Source: https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions — FETCHED, high.
- **`temperature`, `top_p`, `top_k` are deprecated on Opus 4.7 and later; a non-default value returns 400.** Source: https://platform.claude.com/docs/en/about-claude/model-deprecations — FETCHED, high. So "set temperature to 0 for determinism" is not available on current Sonnet/Opus/Fable models. Re-running the same prompt will not reliably reproduce a past decision.
- **Models retire**: at least 60 days' notice; Haiku 4.5 is listed "not sooner than October 15, 2026" (still Active, no deprecation announced); Sonnet 4.5 was deprecated 2026-09-30 for retirement 2026-11-30; current 5.5 models not sooner than September 2027. Same source — FETCHED, high. A decision made by a retired model can never be re-executed.
- Therefore reproducibility must mean **record-and-replay**, not re-execution: store the exact request (model ID, prompt version hash, full input payload), the full response, `request_id`, token usage and timestamps; audits and backtests read the log.
- **Knowledge cutoffs** (https://platform.claude.com/docs/en/about-claude/models/overview — FETCHED, high): Fable 5.1 / Opus 5.5 / Sonnet 5.5 reliable cutoff June 2026; Haiku 4.5 reliable cutoff Feb 2025, training data to Jul 2025.
- **Lopez-Lira, Tang, Zhu, "The Memorization Problem" (arXiv 2504.14765)**: LLMs recall economic and financial values from before their cutoff with high precision; instructing the model to respect a date does not work; masking fails because models reconstruct entities and dates from context; no recall after cutoff. Conclusion: forecasting ability is not identifiable on data the model has seen. Source: https://arxiv.org/abs/2504.14765 — FETCHED (abstract only; specific models and sample not confirmed), medium-high.
- **Glasserman & Lin (arXiv 2309.17322)**: headline-sentiment trading with GPT; anonymising company names performed better in-sample, which they attribute to a "distraction effect" from the model's prior knowledge of companies; they recommend anonymisation for backtesting and live use. Source: https://arxiv.org/abs/2309.17322 — FETCHED (abstract), medium. Note the tension with Lopez-Lira et al. on whether masking is sufficient; treat anonymisation as helpful, not as a cure.
- **Sarkar & Vafa, "Lookahead Bias in Pretrained Language Models" (SSRN 4754678)**: tests showing look-ahead bias in earnings-call risk prediction and election prediction. Seen in search results only; paper not opened — RECALLED/search-snippet, medium.

Implication: a backtest of any Claude-containing component over a period before the model's cutoff is not evidence. For the 5.5 models the clean window starts July 2026 (three months of data today). Haiku 4.5 has about 14 clean months (Aug 2025 onward) but may be retired at short notice.

### 2.5 Secrets on a local machine

- **Docker Compose secrets** mount as files under `/run/secrets/<name>`, are granted per service, and are preferred over environment variables (which leak into logs and every process). Supported on Linux containers only. Source: https://docs.docker.com/compose/how-tos/use-secrets/ — FETCHED, high. (Docker Desktop on Windows normally runs Linux containers, so this should apply — my inference, medium.)
- **Python `keyring`** supports Windows Credential Locker, macOS Keychain, Secret Service, KWallet. The docs state no security analysis has been performed for the Windows backend, and on macOS any Python script run by the same interpreter can read the secret without a prompt. Source: https://keyring.readthedocs.io/en/latest/ — FETCHED, high. It protects against files-in-repo leaks, not against malware running as the same user.
- **Coinbase** API keys have view / trade / transfer permissions and support IP allowlisting; the docs warn that a leaked transfer-enabled key can empty the account. Source: https://docs.cdp.coinbase.com/coinbase-app/authentication-authorization/api-key-authentication — FETCHED, high.
- **Alpaca**: paper and live accounts have separate credentials. The authentication page I read does not document read-only scopes or IP allowlists for Trading API keys — treat as "not available" until verified. Source: https://docs.alpaca.markets/docs/authentication — FETCHED, medium.
- **Anthropic**: per-workspace spend limits and keys exist (rate-limits page) — FETCHED, high.
- JARVIS v1 committed an API key to source (context file). That key must be considered compromised and rotated; a secret scanner in pre-commit (e.g. gitleaks) is standard practice — RECALLED, medium.

## 3. What this means for the JARVIS design documents

**Supported**
- v2 design principle and v3 Capital Governor ("deterministic service; no LLM override"; "agents produce structured evidence; they do not directly send broker orders"). This is exactly the privilege separation the security literature requires.
- v3 Bull/Bear agents listed as "LLM structured outputs" — feasible and GA.
- v1 Layer I recording "feature/model/prompt versions… trace IDs" — necessary, though not sufficient (see below).
- v1 note that paper trading does not fully simulate reality — consistent with the need for forward evaluation.

**Weakened**
- "Always-on opportunity scanner" combined with "specialist agents" on every candidate: at current prices this is hundreds to thousands of dollars a month, against a near-zero budget and $1k–$10k of capital. The scanner, technical, flow, crypto and surveillance "agents" must be plain code; the documents' stack column mostly already says so, but the word "agent" and the LangGraph supervisor invite an LLM in every hop.
- v3 Position Manager "recalculates the thesis after entry": if any part of that is an LLM call, exits depend on an external API that returns 529s, and on Alpaca there is no server-side bracket for crypto or fractional positions.
- v3 Confidence Calibrator including "Thesis" confidence, calibrated by "walk-forward calibration": the LLM-derived part cannot be calibrated on history before the model's cutoff, and models are replaced roughly yearly, resetting any calibration.
- v1 Strategy Lab "LLM proposes hypotheses; backtest…": an LLM that already knows which strategies and which periods worked proposes hypotheses that will look good on pre-cutoff backtests. This is data snooping through the model.
- v3 Manipulation Surveillance covers market manipulation only. None of the three documents mentions manipulation of the text the LLM reads (prompt injection, hidden HTML, homoglyphs, fabricated posts).
- "Every decision must be reconstructable": true only by replaying stored outputs, since temperature control is gone on current models and models retire.
- The worked examples (BTC/ETH order-flow trades lasting minutes to hours) assume decisions faster than an LLM round trip.

**Contradicted**
- Nothing is flatly contradicted, but "wrap current JARVIS as the Information Intelligence service rather than rewriting it" conflicts with the fact that v1 had a committed API key and one global session; it needs a security rewrite, not a wrapper.

## 4. Recommended changes

1. **Three privilege zones.** (i) Quarantined reader: an LLM with no tools, no secrets, no network, that turns each sanitised document into a fixed schema (event type, entities, direction, novelty, an "instruction-like text present" flag). (ii) Reasoning LLM (thesis/critique) that sees only those structured fields plus numeric features, never raw text. (iii) Deterministic governor and execution service — the only container holding broker keys. No LLM output is ever interpolated into an order; the LLM may only select among enumerated actions.
2. **Sanitise before the model**: strip HTML to visible text, Unicode NFKC normalisation and confusable detection, length caps, keep raw copy with hash for audit. Map tickers with deterministic code, not with the LLM.
3. **Bound text influence**: a text-derived score may veto or reduce a trade, or raise priority for review, but may not by itself increase position size beyond a small fixed cap. Require corroboration from price/volume for any text-triggered entry.
4. **LLM off the hot path.** Entries are gated by code; the LLM runs on a deterministic shortlist (a handful per day) and on daily/weekly reviews via the Batch API. Budget target: under $25/month, enforced with a workspace spend limit; treat the resulting HTTP 400 as "LLM unavailable".
5. **Fail-closed rules**: if the LLM is unavailable, invalid, refused or truncated → no new entries from LLM-dependent strategies; open positions continue under deterministic exits. Every position gets a broker-side stop at entry where the broker supports it; where it does not (Alpaca crypto beyond stop-limit, fractional shares), either trade whole shares or accept and document the local-process dependency and add a heartbeat watchdog that flattens on restart.
6. **Validation layer**: `output_config.format` schema + Pydantic range checks + case-insensitive enums + explicit handling of `refusal` and `max_tokens`; one retry, then fail closed. Do not rely on forced `tool_choice`.
7. **Record-and-replay ledger**: store model ID, prompt hash, full request/response, `request_id`, usage. Backtests of post-LLM logic read cached outputs.
8. **Evaluation protocol for LLM components**: (a) judge the extractor as an extractor — accuracy on a hand-labelled set of post-cutoff documents; (b) judge any predictive contribution only on data after the model's training cutoff, in forward shadow mode, as an ablation (pipeline with versus without the LLM feature); (c) restart the clock whenever the model ID changes; (d) run an injection red-team set (hidden text, homoglyphs, fake headlines) as a regression test.
9. **Model choice**: default to Haiku 4.5 for extraction (cheapest; note the 4,096-token cache minimum and the open retirement date) and Sonnet 5.5 for critique; plan a migration test, not a silent swap.
10. **Secrets**: rotate the leaked v1 key; Compose file-based secrets, mounted only into the service that needs them; source files from Windows Credential Manager or a user-only ACL file outside the repo; `.gitignore` plus secret scanning; Coinbase key with trade-only permission, no transfer, IP-allowlisted; separate paper and live Alpaca keys with live keys absent from the machine until the promotion gate; a separate Anthropic workspace key with a spend limit; full-disk encryption on the laptop.

## 5. Open uncertainties

- Real token counts per call for JARVIS prompts (my 4.5k-in/400-out assumption could be off by 2–3x); thinking-token overhead on Sonnet/Opus 5.5 not measured.
- Official per-model latency figures not found; the "seconds" figure is from memory.
- Whether Haiku 4.5 will be deprecated soon and what replaces it (no successor is listed).
- Whether Alpaca Trading API keys can be scoped or IP-restricted; whether Alpaca crypto stop-limit orders survive all outage modes; whether `client_order_id` gives true idempotency (docs did not confirm).
- The adversarial-trading papers are backtests on research systems; no documented real-world attack on a retail LLM trader was found. Likelihood for a $1k–$10k account is low for targeted attacks, but untargeted pump content is routine.
- Lopez-Lira et al. and Sarkar & Vafa details (models, samples) were read at abstract/snippet level only.
- Windows-specific behaviour of Compose secrets under Docker Desktop not tested.

## 6. Source list

- Anthropic pricing — https://platform.claude.com/docs/en/about-claude/pricing (FETCHED)
- Anthropic prompt caching — https://platform.claude.com/docs/en/build-with-claude/prompt-caching (FETCHED)
- Anthropic batch processing — https://platform.claude.com/docs/en/build-with-claude/batch-processing (FETCHED)
- Anthropic structured outputs — https://platform.claude.com/docs/en/build-with-claude/structured-outputs (FETCHED)
- Anthropic API errors — https://platform.claude.com/docs/en/api/errors (FETCHED)
- Anthropic rate limits — https://platform.claude.com/docs/en/api/rate-limits (FETCHED)
- Anthropic models overview — https://platform.claude.com/docs/en/about-claude/models/overview (FETCHED)
- Anthropic model IDs and versioning — https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions (FETCHED)
- Anthropic model deprecations — https://platform.claude.com/docs/en/about-claude/model-deprecations (FETCHED)
- Anthropic mitigate jailbreaks and prompt injections — https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks (FETCHED)
- OWASP LLM01:2025 — https://genai.owasp.org/llmrisk/llm01-prompt-injection/ (FETCHED)
- Greshake et al. — https://arxiv.org/abs/2302.12173 (FETCHED, abstract)
- Beurer-Kellner et al. — https://arxiv.org/html/2506.08837 (FETCHED)
- Debenedetti et al., CaMeL — https://arxiv.org/abs/2503.18813 (FETCHED, abstract)
- Willison, lethal trifecta — https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/ (FETCHED)
- Rizvani, Apruzzese, Laskov — https://arxiv.org/html/2601.13082v1 (FETCHED)
- Poisoning Agentic Alpha — https://arxiv.org/abs/2608.24069 (FETCHED, abstract)
- Lopez-Lira, Tang, Zhu — https://arxiv.org/abs/2504.14765 (FETCHED, abstract)
- Glasserman & Lin — https://arxiv.org/abs/2309.17322 (FETCHED, abstract)
- Sarkar & Vafa — SSRN 4754678 (search snippet only, not opened)
- Alpaca orders — https://docs.alpaca.markets/docs/orders-at-alpaca ; crypto orders — https://docs.alpaca.markets/docs/crypto-orders ; authentication — https://docs.alpaca.markets/docs/authentication (FETCHED)
- Coinbase API key auth — https://docs.cdp.coinbase.com/coinbase-app/authentication-authorization/api-key-authentication (FETCHED)
- Docker Compose secrets — https://docs.docker.com/compose/how-tos/use-secrets/ (FETCHED)
- Python keyring — https://keyring.readthedocs.io/en/latest/ (FETCHED)


## Independent verification (2026-10-01)

Checked against primary sources opened on 2026-10-01.

**Confirmed**
- Prices for Haiku 4.5, Sonnet 5.5, Opus 5.5 and Fable 5.1 (input, output, cache read, batch) match the pricing page. The per-call and monthly arithmetic in 2.3 re-computes correctly. Web search is $10 per 1,000 searches. https://platform.claude.com/docs/en/about-claude/pricing
- Start-tier monthly cap is $500 (Build $1,000). A cap-hit returns 429 with no retry-after; a self-set limit returns 400. https://platform.claude.com/docs/en/api/rate-limits , https://platform.claude.com/docs/en/api/errors
- Forced tool_choice (any/tool) returns 400 on Opus 5.5, Sonnet 5.5, Fable 5.1. https://platform.claude.com/docs/en/api/errors
- temperature/top_p/top_k return 400 when non-default on 4.7 and later. Haiku 4.5 retirement "not sooner than October 15, 2026"; Sonnet 4.5 deprecated 2026-09-30, retires 2026-11-30; 60 days' notice. https://platform.claude.com/docs/en/about-claude/model-deprecations
- Knowledge cutoffs: 5.5 models and Fable 5.1 reliable and training cutoff Jun 2026; Haiku 4.5 reliable Feb 2025, training Jul 2025. https://platform.claude.com/docs/en/models/overview
- CaMeL: 77% of AgentDojo tasks with provable security vs 84% undefended. https://arxiv.org/abs/2503.18813
- Rizvani et al. (accepted at IEEE SaTML): 99.1% (5,957 of 6,012) homoglyph ticker-mapping failures; 65.6% sentiment flips; mean return drop 3.67 pp (homoglyph) and 3.18 pp (hidden text); 17.7 pp worst case is a single-day manipulation (TSLA, 2024-02-28). https://arxiv.org/abs/2601.13082 , https://arxiv.org/html/2601.13082v1
- "Poisoning Agentic Alpha" exists (submitted 2026-08-25), four architectures, five assets, "no architecture is inherently robust". https://arxiv.org/abs/2608.24069
- Alpaca: bracket/OCO not supported for fractional orders, extended hours, or crypto. https://docs.alpaca.markets/docs/orders-at-alpaca

**Corrected or sharpened**
- Rizvani et al. DID include transaction costs ($0.005/share, 0.02 slippage), used a strict out-of-sample test (train 2013-2023, test Feb 2024-Apr 2025), and the model set is FinBERT, FinGPT, FinLLaMA plus six general LLMs (9 models, not "FinBERT plus nine others"). They also checked scraping libraries and surveyed 27 practitioners for real-world feasibility. Still a backtest, still 10 mega-caps. The brief's "transaction-cost treatment not confirmed" is now resolved.
- Alpaca fractional orders are DAY time-in-force only (GTC is "No" for every order type). So with fractional shares there is no resting overnight stop at all, not just no bracket. Whole shares only if broker-side stops must persist. Same page.
- Thinking cost: Opus 5.5 and Fable 5.1 cannot disable thinking; Sonnet 5.5 defaults to adaptive thinking but accepts thinking {"type":"between_tools"} (no up-front thinking, effort cannot exceed high and cannot change mid-conversation). The brief's Sonnet estimates exclude thinking, so set between_tools or low effort explicitly and cap max_tokens. Haiku 4.5 thinking is opt-in. https://platform.claude.com/docs/en/api/errors
- Haiku 4.5 is the only recommended model with a retirement floor two weeks away (Oct 15, 2026). Batch Haiku 4.5 is $0.50/$2.50; Sonnet 5.5 batch is $1/$5 but on a ~30% heavier tokenizer, so roughly 2.5x per extraction. Keep the model ID in config and budget a migration test; do not hard-code it.

**Unverifiable in this pass**
- The 4,096-token minimum cacheable prefix for Haiku 4.5 (the fetched caching page summary gave only "512 tokens, varies by model"). Verify before relying on it.
- Alpaca API-key scoping: the authentication page says nothing about read-only scopes or IP allowlists. Treat as not available.
- Docker Compose secrets on Docker Desktop for Windows, keyring behaviour, Coinbase key permissions, Willison, OWASP, Beurer-Kellner, Glasserman-Lin, Lopez-Lira and Sarkar-Vafa claims were not re-opened.

**Missed considerations (owner constraints, section C)**
- Anthropic API needs prepaid credit and a card; a $0 budget means the LLM may simply be dropped. The design must work with the LLM entirely off (rules-only), with LLM as an optional ablation.
- US residency: Pattern Day Trader rule and margin interaction for a sub-$25k account, wash-sale and crypto tax records, and 1.1x pricing if US-only inference (inference_geo "us") is chosen for data-residency reasons. None are in the brief.
- Free-tier data (news/social) is exactly the scrapeable text the injection papers target, and low-cost sources are the easiest to pump.

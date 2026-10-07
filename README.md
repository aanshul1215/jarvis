# JARVIS — a personal financial co-pilot

JARVIS started as a TSLA-only chatbot backed by XGBoost models (the `legacy-v1/` folder, originally a Hugging Face
Space). It is being redesigned into an end-to-end personal investing system: a deterministic money engine that
computes and gates every order, surrounded by a team of Claude agents that build, review, explain, research and
triage — but never decide, size or time an order.

**Status (October 2026): design phase. The architecture has not yet been approved by the owner, and no
implementation code exists yet.** The next step is a discussion of the open warnings listed at the bottom of this
page, then milestone M0.

## Start here

| Read | What it is |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | The current proposed design: components, the agent roster, the runtime workflow, risk gate, validation gates, budget, build plan, open items, references |
| [docs/00-original-vision/](docs/00-original-vision/) | The owner's three original design documents (v1, v2, v3) and the diagrams, plus a summary of the legacy v1 system and the binding constraints |
| [docs/01-research/00-gap-analysis.md](docs/01-research/00-gap-analysis.md) | What 23 fact-checked research briefs established, what they contradicted in the original documents, and what stayed open |
| [docs/02-design-tournament/FINAL-design.md](docs/02-design-tournament/FINAL-design.md) | The previous design (winner of a five-proposal tournament). Superseded by `ARCHITECTURE.md` wherever they differ |
| [docs/03-review/](docs/03-review/) | Ten paper-grounded specialist reviews, the four-seat panel positions and the two verification passes that produced `ARCHITECTURE.md` |
| [docs/LOG.md](docs/LOG.md) | Project log: what was done, when, and why |

## How the design was produced

1. **Understand** — the legacy Space was read line by line (see `docs/00-original-vision/context-current-state-and-constraints.md` for its defects, including target leakage in the v1 models).
2. **Evidence** — 17 research briefs, each written against primary sources and independently fact-checked, then 6 gap-fill briefs (`docs/01-research/`).
3. **Tournament** — five architectures written from different philosophies, attacked by nine critics, synthesised and red-teamed (`docs/02-design-tournament/`).
4. **Review** — ten specialists re-examined the winner against research papers, a four-seat panel voted on 76 proposed changes, and two verifiers checked the rewrite (`docs/03-review/`).

Every brief and review tags its sources as fetched, recalled or unverified. Treat anything tagged RECALLED,
SNIPPET or UNVERIFIED as unconfirmed.

## Binding constraints

- Owner is a US resident (Texas); $1,000–$10,000 of the owner's own money; no outside investors.
- Near-zero monthly budget for data and LLM calls (the design runs at $0 metered spend on free data tiers and the owner's existing Claude subscription).
- Windows 11 laptop with 8 GB RAM; solo developer plus Claude agents.
- No LLM output may decide, size or time an order.

## The agents (as currently proposed)

| Agent | Purpose | How it runs |
|---|---|---|
| Builder | Writes all code, tests, schemas and runbooks | Attended Claude Code sessions |
| Reviewer | Pre-mortem on risky code changes, strategy specs and limit loosenings | Attended, fresh context |
| Strategy Lab (Spec Clerk, Replication Analyst) | Pre-registered strategy specs, harness runs, replication reports | Attended, monthly at most |
| Narrator | Weekly memo from typed facts, validated by code before sending | Scheduled (the only scheduled agent) |
| Ledger Analyst | Answers questions over the ledger with the query shown | On demand |
| Change-Watch | Explains changes on watched vendor/terms pages | When a page hash changes |
| Incident Triage | Explains SAFE/HALT events and drafts the fix | When an incident email arrives |
| Reader | Typed events from SEC filings for a watch list | Dormant; opt-in |

See `ARCHITECTURE.md` section 4 for tools, permissions, outputs, checks and the "never-do" list.

## Open warnings to discuss before approval

1. Anthropic's consumer terms may restrict using Claude in connection with securities trading; the clause must be read first-hand (ARCHITECTURE.md, open item O4).
2. Plan usage, not dollars, is the scarce resource; it must be measured before agents are added.
3. Several Alpaca behaviours need probes or an email in week one (fractional limit orders, activity CSV export, IRA fee, crypto availability in Texas).
4. The legacy Space committed an OpenAI API key; it must be revoked at the provider (it is redacted in `legacy-v1/`).
5. The trend strategy is expected to lose money after tax in a taxable account and runs in shadow only.

## Collaborating

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: never commit to `main` directly; branch, open a pull
request, and record decisions in `docs/LOG.md`.

Nothing in this repository is investment, tax or legal advice.

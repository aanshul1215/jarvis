# Contributing

This project is logged on GitHub so that every decision can be reconstructed later.

## Branching

- `main` holds reviewed material only. Do not push to it directly.
- Create a branch per topic: `git checkout -b <yourname>/<topic>` (for example `manav/m0-probes`).
- Open a pull request into `main`. Describe what changed and why, and link the document or section it affects.
- One topic per pull request. Design discussion belongs in the pull request thread or in a GitHub issue, not in chat.

## Where things go

| Content | Location |
|---|---|
| The current proposed design | `AUTONOMOUS_ARCHITECTURE.md` and `docs/04-autonomous-design/` (edit through a pull request; record the reason in `docs/LOG.md`) |
| The October 2 monthly proposal | `ARCHITECTURE.md` — historical evidence and review record; add new decisions rather than rewriting its history |
| Research, reviews, decisions already made | `docs/` — append, do not rewrite history. Add a new dated file rather than editing a verified brief |
| Project log | `docs/LOG.md` — one dated entry per meaningful step |
| Legacy v1 code | `legacy-v1/` — read-only reference; do not build on it |
| Future implementation (from phase A1) | Runtime, configuration, schemas and tests — layout to be decided when A1 starts |

## Rules that do not bend

1. **No secrets in the repository.** No API keys, broker keys, account numbers or tax ids, in any file, ever. A
   pre-commit secret scan is an A0 prerequisite. The legacy code once contained a committed key; that is why.
2. **No Claude or Codex output reaches the live order path.** The proposed local system may autonomously select
   among approved strategies and execute inside an owner-approved envelope. Its deterministic risk gate retains
   final authority. Any proposal to change this requires a documented design review.
3. **Claims carry sources.** New research must tag each source as fetched or recalled, as the existing briefs do.
4. **Nothing here is investment, tax or legal advice.**

## Setting up

Until the autonomous roadmap starts there is nothing to install: the repository contains design documents and the
read-only legacy prototype, not a runnable autonomous trader.

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
| The current design | `ARCHITECTURE.md` (edit through a pull request; record the reason in `docs/LOG.md`) |
| Research, reviews, decisions already made | `docs/` — append, do not rewrite history. Add a new dated file rather than editing a verified brief |
| Project log | `docs/LOG.md` — one dated entry per meaningful step |
| Legacy v1 code | `legacy-v1/` — read-only reference; do not build on it |
| Implementation (from milestone M0) | `jarvis/`, `config/`, `schemas/`, `tests/`, `.claude/` — created when M0 starts |

## Rules that do not bend

1. **No secrets in the repository.** No API keys, broker keys, account numbers or tax ids, in any file, ever. A
   pre-commit secret scan will be added in M0. The legacy code once contained a committed key; that is why.
2. **No LLM output decides, sizes or times an order.** Any proposal to change this is a design change that needs
   a pull request against `ARCHITECTURE.md` with evidence.
3. **Claims carry sources.** New research must tag each source as fetched or recalled, as the existing briefs do.
4. **Nothing here is investment, tax or legal advice.**

## Setting up

Until M0 starts there is nothing to install: the repository is documents only.

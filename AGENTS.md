# Repository development rules

- Treat `FINAL_IMPLEMENTATION_PLAN.md` and `docs/05-final-implementation/` as architecture requirements; preserve historical documents and `legacy-v1/`.
- Build the new runtime in `src/jarvis/` for both eligible US equities and spot crypto. Do not reintroduce a TSLA-only assumption.
- Never enable a live brokerage endpoint. Alpaca adapter construction must use `paper=True` and order submission requires explicit owner policy, strategy approval, account capability checks, and the deterministic Governor.
- Keep runtime data and secrets outside Git in `JARVIS_HOME`. Use Parquet, JSON/JSONL, CSV, and native model artifacts via the local storage adapter; no V1 database server.
- Research, model training, and backtests must use point-in-time data and cannot block the decision loop or authorize orders. Record negative experiments and source/latency limitations.
- Run relevant tests and record actual evidence in `EXECUTION.md` and append-only `LOG.md`. Distinguish mock evidence from account-connected Alpaca evidence. Never mark a blocked gate passed.
- Do not merge a feature branch into `branch-3` while critical acceptance gates are open. Do not change `main` or `branch-1` for this implementation.

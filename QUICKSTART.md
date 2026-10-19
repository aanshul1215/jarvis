# JARVIS V1 quickstart

The new code is a local multiasset research and paper desk under `src/jarvis/`. `legacy-v1/` is the older TSLA reference. The current implementation runs an **offline synthetic mock** end to end; Alpaca account-connected paper orders are not release verified.

## Install

Use Python 3.11 or newer. On macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
export JARVIS_HOME="$HOME/jarvis-runtime"
.venv/bin/python -m jarvis doctor
.venv/bin/python -m jarvis demo
.venv/bin/python -m jarvis --home "$JARVIS_HOME" backtest --fixture
.venv/bin/python -m jarvis --home "$JARVIS_HOME" train --fixture
.venv/bin/python -m jarvis --home "$JARVIS_HOME" review
.venv/bin/python -m jarvis --home "$JARVIS_HOME" dashboard
```

On Windows PowerShell, replace `.venv/bin/python` with `.venv\Scripts\python.exe` and set `$env:JARVIS_HOME` to an absolute directory outside the checkout. The dashboard opens at `http://127.0.0.1:8765/`. `demo` uses a temporary directory unless `--home` is supplied. All demo and fixture results are synthetic.

See [DEVELOPER_SETUP.md](DEVELOPER_SETUP.md) for paper credentials, private policy, and the guarded paper commands, and [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) for recovery. Runtime records stay in `JARVIS_HOME`, outside Git.

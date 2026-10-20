"""Consistent offline-first command line. No live trading command exists."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from pathlib import Path

from .broker import AlpacaPaperBroker, MockBroker
from .config import load_policy, load_paper_runtime
from .contracts import AssetClass, Mode
from .dashboard import render, serve
from .engine import TradingEngine
from .fixtures import synthetic_bars, research_bars
from .market_data import AlpacaMarketData
from .research import backtest_fixture, train_fixture
from .review import review_outcomes
from .runner import PaperDesk
from .simulation import run_soak
from .history import alpaca_clients, backfill, dataset_name, DATASETS, default_start, load_universe
from .macro import PRICE_SERIES, SERIES, update_macro
from .quality import check_bars
from .edgar import EdgarClient, update_edgar
from .calendars import http_text, update_calendars
from .information import ingest, load_document
from .risk import Governor, RiskPolicy
from .storage import LocalStorage
from .strategies import StrategyRegistry, baseline_specs


def _home(args) -> Path:
    supplied = args.home or os.environ.get("JARVIS_HOME")
    if not supplied:
        raise SystemExit("JARVIS_HOME is required; choose a directory outside this repository")
    return Path(supplied)


def _demo_policy() -> RiskPolicy:
    return RiskPolicy("SYNTHETIC_DEMO_ONLY", ("AAPL", "BTC/USD", "ETH/USD"), ("breakout-volume",),
                      500, 500, 1000, 100, 0.25, 30, 60, owner_approved=True, crypto_enabled=True)


def demo(home: Path | None = None) -> dict:
    path = home or Path(tempfile.mkdtemp(prefix="jarvis-synthetic-"))
    results = {}
    with LocalStorage(path) as store:
        broker = MockBroker(cash=1000)
        engine = TradingEngine(store, broker, Governor(_demo_policy()), StrategyRegistry(baseline_specs()), Mode.SHADOW)
        engine.reconcile()
        for asset, cls in (("AAPL", AssetClass.EQUITY), ("BTC/USD", AssetClass.CRYPTO)):
            bars = synthetic_bars(asset, cls)
            store.save_bars(bars)
            results[asset] = engine.process(bars, as_of=bars[-1].available_at,
                                            reference_price=bars[-1].close,
                                            quantity=1 if cls == AssetClass.EQUITY else 0.1)
            if broker.state().positions.get(asset, 0) > 0:
                engine.exit_position(asset, cls, bars[-1].close + 1, reason="SYNTHETIC_EXIT")
        store.export_csv("decision-summary", [{"asset": asset, "result": str(value)} for asset, value in results.items()])
        review_outcomes(store)
    return {"mode": "SYNTHETIC_MOCK", "home": str(path), "results": results}


def doctor(home: Path | None) -> dict:
    from importlib.util import find_spec

    mode = os.environ.get("JARVIS_MODE", "OFF")
    result = {"python_dependencies": "PASS" if all(find_spec(x) for x in ("pyarrow", "alpaca", "sklearn", "joblib", "numpy")) else "FAIL",
              "paper_credentials": "PASS" if os.environ.get("ALPACA_PAPER_KEY_ID") and os.environ.get("ALPACA_PAPER_SECRET_KEY") else "UNVERIFIED",
              "live_trading": "DISABLED",
              "operating_mode": "PASS" if mode in {m.value for m in Mode} else "FAIL",
              "configured_mode": mode,
              "risk_policy": "UNVERIFIED", "paper_account": "UNVERIFIED",
              "equity_access": "UNVERIFIED", "crypto_access": "UNVERIFIED",
              "market_data_entitlement": "UNVERIFIED"}
    if home is None:
        result["local_storage"] = "UNVERIFIED"
    else:
        try:
            with LocalStorage(home, writer=False) as store:
                result["local_storage"] = "PASS"
            try:
                load_policy(home)
                result["risk_policy"] = "PASS"
            except (OSError, ValueError, TypeError):
                result["risk_policy"] = "UNVERIFIED"
        except Exception:
            result["local_storage"] = "FAIL"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jarvis", description="JARVIS local research and paper desk")
    parser.add_argument("--home", help="JARVIS_HOME outside the Git checkout")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("doctor", "demo", "alpaca-check", "dashboard", "paper", "backtest", "train", "review", "info-ingest",
                 "soak", "macro-update", "backfill", "data-check", "edgar-update", "calendar-update", "model-study",
                 "cost-report", "selector-study", "collect", "score-news", "daily"):
        command = commands.add_parser(name)
        if name in ("backfill", "data-check", "edgar-update"):
            command.add_argument("--universe", required=True, help="universe JSON (see config/universe.example.json)")
        if name == "backfill":
            command.add_argument("--start", default="2016-01-01", help="first date to download (UTC), YYYY-MM-DD")
            command.add_argument("--timeframes", default="1Day,1Hour", help="comma-separated: 1Day,1Hour")
        if name == "soak":
            command.add_argument("--hours", type=float, default=24, help="simulated hours (default 24)")
            command.add_argument("--poll-seconds", type=int, default=60, help="simulated poll interval")
            command.add_argument("--seed", type=int, default=7)
        if name in ("backtest", "train"):
            command.add_argument("--fixture", action="store_true", help="use labeled synthetic equity and crypto histories")
        if name == "backtest":
            command.add_argument("--universe", help="universe JSON; its assets with stored data are replayed")
            command.add_argument("--strategy", action="append", help="strategy-id@version (repeatable)")
            command.add_argument("--dataset", default="1Day-adjusted", help="stored dataset, e.g. 1Day-adjusted, 1Hour-raw")
            command.add_argument("--timeframe", default="1Day", choices=("1Day", "1Hour"))
            command.add_argument("--start", default="2016-03-01")
            command.add_argument("--end", default="2023-12-31", help="development period end; later data is the holdout")
            command.add_argument("--split", default="DEVELOPMENT", choices=("DEVELOPMENT", "HOLDOUT"))
            command.add_argument("--cash", type=float, default=10_000.0)
            command.add_argument("--notional", type=float, default=1_000.0, help="dollars per entry")
            command.add_argument("--seed", type=int, default=0)
            # Pre-registered defaults for strategy evaluation: size by the Phase 5 winner (GARCH, development study
            # 2026-10-19). --sizing fixed exists for diagnostics; every run is still registered as a trial.
            command.add_argument("--sizing", default="volatility", choices=("fixed", "volatility"))
            command.add_argument("--volatility-model", default="garch", help="Phase 5 study winner")
        if name == "daily":
            command.add_argument("--universe", required=True, help="universe JSON")
            command.add_argument("--enable-orders", action="store_true",
                                 help="after collecting and scoring, run one guarded paper cycle that may place orders")
        if name == "collect":
            command.add_argument("--universe", required=True, help="universe JSON")
            command.add_argument("--sources", default="news,reddit,bluesky,feargreed",
                                 help="comma-separated: news, reddit, bluesky, feargreed")
            command.add_argument("--news-start", help="first date for news (default: day after the newest archived)")
            command.add_argument("--history", action="store_true", help="feargreed: download the full history")
        if name == "selector-study":
            command.add_argument("--universe", required=True, help="universe JSON; assets with stored bars are used")
            command.add_argument("--strategy", action="append",
                                 help="strategy-id@version (repeatable; default: the pre-registered library)")
            command.add_argument("--dataset", default="1Day-adjusted")
            command.add_argument("--start", default="2016-03-01")
            command.add_argument("--end", default="2023-12-31", help="last date of data to use (holdout: latest)")
            command.add_argument("--split", default="DEVELOPMENT", choices=("DEVELOPMENT", "HOLDOUT"))
        if name == "model-study":
            command.add_argument("--kind", required=True, choices=("volatility", "regime", "risk"))
            command.add_argument("--source", default="fred", choices=("fred", "bars"),
                                 help="fred: long index/crypto histories; bars: the universe's stored daily bars")
            command.add_argument("--universe", help="universe JSON (needed with --source bars)")
            command.add_argument("--split", default="DEVELOPMENT", choices=("DEVELOPMENT", "HOLDOUT"))
        if name == "paper":
            command.add_argument("--dry-run", action="store_true", help="validate local policy and read-only paper account; send no orders")
            command.add_argument("--once", action="store_true", help="run one guarded paper decision cycle")
            command.add_argument("--loop", action="store_true", help="repeat guarded paper cycles")
            command.add_argument("--enable-orders", action="store_true", help="explicitly enable paper orders for this process")
        if name == "info-ingest":
            command.add_argument("--file", required=True, help="local dated JSON document to summarize")
    args = parser.parse_args(argv)
    if args.command == "doctor":
        print(json.dumps(doctor(Path(args.home) if args.home else (Path(os.environ["JARVIS_HOME"]) if os.environ.get("JARVIS_HOME") else None)), indent=2))
    elif args.command == "demo":
        print(json.dumps(demo(Path(args.home) if args.home else None), indent=2))
    elif args.command == "dashboard":
        serve(_home(args))
    elif args.command == "alpaca-check":
        key, secret = os.environ.get("ALPACA_PAPER_KEY_ID"), os.environ.get("ALPACA_PAPER_SECRET_KEY")
        if not key or not secret:
            print(json.dumps({"paper_account": "UNVERIFIED", "reason": "paper credentials absent"}))
            return 2
        broker = AlpacaPaperBroker(key, secret, enable_orders=False)
        state = broker.state()
        data = AlpacaMarketData(key, secret)
        feed_checks = {}
        for symbol, cls in (("AAPL", AssetClass.EQUITY), ("BTC/USD", AssetClass.CRYPTO)):
            try:
                quote = data.latest_quote(symbol, cls)
                feed_checks[symbol] = {"status": "PASS", "feed": quote.feed,
                                       "quote_at": quote.at.isoformat(), "observed_at": quote.observed_at.isoformat(),
                                       "access_latency_ms": quote.latency_ms}
            except Exception as exc:
                feed_checks[symbol] = {"status": "UNVERIFIED", "reason": type(exc).__name__}
        print(json.dumps({"paper_account": "PASS", "reconciled": state.reconciled,
                          "equity_assets": {s: broker.asset_eligible(s, AssetClass.EQUITY) for s in ("AAPL", "SPY")},
                          "crypto_assets": {s: broker.asset_eligible(s, AssetClass.CRYPTO) for s in ("BTC/USD", "ETH/USD")},
                          "market_data": feed_checks, "order_submission": "DISABLED"}, indent=2))
    elif args.command == "paper":
        if sum((args.dry_run, args.once, args.loop)) != 1:
            print(json.dumps({"paper_orders": "DISABLED", "reason": "choose exactly one of --dry-run, --once, or --loop"}))
            return 2
        if args.once or args.loop:
            if not args.enable_orders:
                print(json.dumps({"paper_orders": "DISABLED", "reason": "--enable-orders required"}))
                return 2
            home = _home(args)
            try:
                policy = load_policy(home)
                runtime = load_paper_runtime(home, policy)
                key, secret = os.environ.get("ALPACA_PAPER_KEY_ID"), os.environ.get("ALPACA_PAPER_SECRET_KEY")
                if not key or not secret:
                    raise ValueError("paper credentials missing")
                with LocalStorage(home) as store:
                    broker = AlpacaPaperBroker(key, secret, enable_orders=True)
                    data = AlpacaMarketData(key, secret)
                    from .edgar import EarningsCalendar
                    earnings = EarningsCalendar(store, [a.symbol for a in runtime.assets if a.asset_class == AssetClass.EQUITY])
                    from .awareness import SituationBuilder
                    from .sentiment import SentimentIndex
                    desk = PaperDesk(store, broker, data, policy, runtime, earnings=earnings,
                                     situation=SituationBuilder(store), information=SentimentIndex(store) or None)
                    while True:
                        result = desk.run_once()
                        print(json.dumps(result, indent=2))
                        if result["mode"] == "SAFE" or not args.loop:
                            return 2 if result["mode"] == "SAFE" else 0
                        time.sleep(runtime.poll_seconds)
            except (OSError, ValueError, TypeError, KeyError) as exc:
                print(json.dumps({"paper_orders": "DISABLED", "reason": str(exc)}))
                return 2
            except Exception as exc:
                print(json.dumps({"paper_orders": "SAFE", "reason": type(exc).__name__}))
                return 2
        checks = {"owner_policy": "UNVERIFIED", "paper_account": "UNVERIFIED", "order_submission": "DISABLED"}
        try:
            policy = load_policy(_home(args))
            load_paper_runtime(_home(args), policy)
            checks["owner_policy"] = "PASS"
            key, secret = os.environ.get("ALPACA_PAPER_KEY_ID"), os.environ.get("ALPACA_PAPER_SECRET_KEY")
            if key and secret:
                broker = AlpacaPaperBroker(key, secret, enable_orders=False)
                state = broker.state()
                checks["paper_account"] = "PASS" if state.reconciled else "FAIL"
                checks["approved_assets"] = {asset: broker.asset_eligible(asset, AssetClass.CRYPTO if "/" in asset else AssetClass.EQUITY)
                                              for asset in policy.approved_assets}
            else:
                checks["paper_account"] = "UNVERIFIED"
        except (ValueError, OSError, KeyError, TypeError) as exc:
            checks["owner_policy"] = "FAIL"
            checks["reason"] = str(exc)
        except Exception as exc:
            checks["paper_account"] = "FAIL"
            checks["reason"] = f"paper account probe failed: {type(exc).__name__}"
        print(json.dumps(checks, indent=2))
        return 0 if checks["owner_policy"] == checks["paper_account"] == "PASS" else 2
    elif args.command == "backtest" and not args.fixture:
        if not args.universe or not args.strategy:
            print(json.dumps({"result": "BLOCKED", "reason": "--universe and at least one --strategy are required"}))
            return 2
        from datetime import datetime, timezone
        from .harness import BacktestSpec, evaluate
        home = _home(args)
        with LocalStorage(home, writer=False) as store:
            assets = tuple((a.symbol, a.asset_class) for a in load_universe(Path(args.universe))
                           if store.load_bars(a.symbol, a.asset_class, dataset=args.dataset))
        if not assets:
            print(json.dumps({"result": "BLOCKED", "reason": f"no stored {args.dataset} bars; run backfill first"}))
            return 2
        when = lambda text: datetime.fromisoformat(text).replace(tzinfo=timezone.utc)  # noqa: E731
        spec = BacktestSpec(tuple(args.strategy), assets, args.dataset, args.timeframe, when(args.start),
                            when(args.end), split=args.split, initial_cash=args.cash, order_notional=args.notional,
                            seed=args.seed, sizing=args.sizing, volatility_model=args.volatility_model)
        record = evaluate(home, spec)
        print(json.dumps({k: record[k] for k in ("seq", "fingerprint", "status", "metrics", "trades", "turnover",
                                                 "average_exposure", "benchmarks", "gate")}, indent=2, default=str))
        return 0 if record["gate"]["passed"] else 1
    elif args.command in ("backtest", "train"):
        if not args.fixture:
            print(json.dumps({"result": "BLOCKED", "reason": "train needs --fixture; model training on real data arrives in Phase 7"}))
            return 2
        with LocalStorage(_home(args)) as store:
            outputs = {}
            for asset, cls in (("AAPL", AssetClass.EQUITY), ("BTC/USD", AssetClass.CRYPTO)):
                bars = research_bars(asset, cls)
                store.save_bars(bars)
                outputs[asset] = backtest_fixture(store, bars) if args.command == "backtest" else train_fixture(store, bars)
            if args.command == "train":
                outputs = {asset: {"run_id": report["run_id"], "approval": report["approval"],
                                   "selection": report["selection"],
                                   "models": {name: {"holdout_brier": model["holdout"]["brier"],
                                                     "holdout_compounded_net_return": model["holdout"]["compounded_net_return"],
                                                     "walk_forward_folds": len(model["walk_forward"])}
                                              for name, model in report["models"].items()}}
                           for asset, report in outputs.items()}
            print(json.dumps({"mode": "SYNTHETIC_RESEARCH", "results": outputs}, indent=2))
    elif args.command == "soak":
        target = Path(args.home) if args.home else Path(tempfile.mkdtemp(prefix="jarvis-soak-")) / "desk"
        report = run_soak(target, hours=args.hours, poll_seconds=args.poll_seconds, seed=args.seed)
        print(json.dumps({**report, "home": str(target)}, indent=2, default=str))
        return 0 if report["passed"] else 2
    elif args.command == "macro-update":
        with LocalStorage(_home(args)) as store:
            print(json.dumps(update_macro(store, series=SERIES + PRICE_SERIES), indent=2))
    elif args.command == "collect":
        from datetime import datetime, timedelta, timezone
        import secrets
        from . import collectors
        home = _home(args)
        universe = load_universe(Path(args.universe))
        sources = {s.strip() for s in args.sources.split(",") if s.strip()}
        report: dict = {}
        with LocalStorage(home) as store:
            if "news" in sources:
                key, secret = os.environ.get("ALPACA_PAPER_KEY_ID"), os.environ.get("ALPACA_PAPER_SECRET_KEY")
                if not key or not secret:
                    report["news"] = {"result": "SKIPPED", "reason": "Alpaca paper keys are not set"}
                else:
                    from alpaca.data.historical.news import NewsClient
                    now = datetime.now(timezone.utc)
                    if args.news_start:
                        start = datetime.fromisoformat(args.news_start).replace(tzinfo=timezone.utc)
                    else:
                        months = sorted(p.stem for p in (home / "information" / "alpaca_news").glob("*.parquet"))
                        last = store.read_table("information", "alpaca_news", months[-1]) if months else []
                        start = (max(datetime.fromisoformat(r["published_at"].replace("Z", "+00:00")) for r in last)
                                 + timedelta(seconds=1)) if last else datetime(2016, 1, 1, tzinfo=timezone.utc)
                    report["news"] = collectors.collect_news(store, NewsClient(key, secret), universe, start=start, end=now)
            salt_file = home / "config" / "author-hash-salt"
            if ("reddit" in sources or "bluesky" in sources) and not salt_file.exists():
                # Local only: makes stored author hashes impossible to link to anything outside this machine.
                salt_file.parent.mkdir(parents=True, exist_ok=True)
                salt_file.write_text(secrets.token_hex(16), encoding="utf-8")
            if "bluesky" in sources:
                handle, password = os.environ.get("BLUESKY_HANDLE"), os.environ.get("BLUESKY_APP_PASSWORD")
                if not handle or not password:
                    report["bluesky"] = {"result": "SKIPPED", "reason": "set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD"}
                else:
                    report["bluesky"] = collectors.collect_bluesky(
                        store, collectors.BlueskyClient(handle, password), universe,
                        salt=salt_file.read_text(encoding="utf-8").strip())
            if "reddit" in sources:
                ids = [os.environ.get(v) for v in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT")]
                if not all(ids):
                    report["reddit"] = {"result": "SKIPPED",
                                        "reason": "set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET and REDDIT_USER_AGENT"}
                else:
                    client = collectors.RedditClient(*ids)
                    report["reddit"] = collectors.collect_reddit(store, client, universe,
                                                                 salt=salt_file.read_text(encoding="utf-8").strip())
            if "feargreed" in sources:
                report["feargreed"] = collectors.collect_fear_greed(store, history=args.history)
            collectors.record_collection(store, report)
        print(json.dumps(report, indent=2, default=str))
    elif args.command == "daily":
        # The morning routine, in order, each step logged: fresh information first, then one paper decision cycle.
        # Meant to run once per US trading day at about 10:00 New York time (entries are limit orders valid for 30
        # minutes, so the stock market must be open). A failed step is reported and stops the routine.
        import subprocess
        import sys as _sys
        base = [_sys.executable, "-m", "jarvis", "--home", str(_home(args))]
        steps = [("collect", base + ["collect", "--universe", args.universe]),
                 ("score-news", base + ["score-news"])]
        if args.enable_orders:
            steps.append(("paper", base + ["paper", "--once", "--enable-orders"]))
        summary = []
        for name, command in steps:
            result = subprocess.run(command, capture_output=True, text=True)
            summary.append({"step": name, "exit": result.returncode, "output": result.stdout[-4000:],
                            "errors": result.stderr[-2000:] if result.returncode else ""})
            if result.returncode != 0:
                break
        print(json.dumps(summary, indent=2))
        return 0 if all(s["exit"] == 0 for s in summary) else 2
    elif args.command == "score-news":
        from .sentiment import FinbertScorer, score_archive
        home = _home(args)
        scorer = FinbertScorer(cache_dir=Path(os.environ["HF_HOME"]) if os.environ.get("HF_HOME") else None)
        with LocalStorage(home) as store:
            report = score_archive(store, "alpaca_news", scorer)
        print(json.dumps(report, indent=2))
    elif args.command == "selector-study":
        from datetime import datetime, timezone
        from .harness import BacktestSpec
        from .selector import run_selector_study
        from .strategies import baseline_specs, library_specs
        home = _home(args)
        with LocalStorage(home, writer=False) as store:
            assets = tuple((a.symbol, a.asset_class) for a in load_universe(Path(args.universe))
                           if store.load_bars(a.symbol, a.asset_class, dataset=args.dataset))
        if not assets:
            print(json.dumps({"result": "BLOCKED", "reason": f"no stored {args.dataset} bars; run backfill first"}))
            return 2
        versions = tuple(args.strategy or [f"{s.strategy_id}@{s.version}" for s in baseline_specs() + library_specs()])
        when = lambda text: datetime.fromisoformat(text).replace(tzinfo=timezone.utc)  # noqa: E731
        base = BacktestSpec(versions, assets, args.dataset, "1Day", when(args.start), when(args.end),
                            sizing="volatility", volatility_model="garch")
        record = run_selector_study(home, base, split=args.split, progress=lambda m: print(m, flush=True))
        print(json.dumps({k: record[k] for k in ("seq", "fingerprint", "status", "spec")} |
                         {"selected": record["result"]["selected"],
                          "stages": [{k: s[k] for k in ("stage", "candidate", "incumbent", "gate")}
                                     for s in record["result"]["stages"]]}, indent=2, default=str))
    elif args.command == "model-study":
        from .studies import run_study
        if args.source == "bars" and not args.universe:
            print(json.dumps({"result": "BLOCKED", "reason": "--universe is required with --source bars"}))
            return 2
        record = run_study(_home(args), args.kind, source=args.source, split=args.split,
                           universe=Path(args.universe) if args.universe else None)
        print(json.dumps({k: record[k] for k in ("seq", "fingerprint", "status", "spec", "result")}, indent=2, default=str))
    elif args.command == "cost-report":
        from .costs import compare as compare_costs, realised_costs
        with LocalStorage(_home(args), writer=False) as store:
            rows = realised_costs(store)
        print(json.dumps({"fills": len(rows), "comparison": compare_costs(rows)}, indent=2, default=str))
    elif args.command == "backfill":
        key, secret = os.environ.get("ALPACA_PAPER_KEY_ID"), os.environ.get("ALPACA_PAPER_SECRET_KEY")
        if not key or not secret:
            print(json.dumps({"result": "BLOCKED", "reason": "Alpaca market data needs the paper keys in the environment"}))
            return 2
        from datetime import datetime, timezone
        start = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
        stock, crypto = alpaca_clients(key, secret)
        with LocalStorage(_home(args)) as store:
            report = backfill(store, stock, crypto, load_universe(Path(args.universe)), start=start,
                              timeframes=tuple(args.timeframes.split(",")))
        print(json.dumps(report, indent=2))
    elif args.command == "calendar-update":
        agent = os.environ.get("JARVIS_SEC_USER_AGENT", "")
        with LocalStorage(_home(args)) as store:
            print(json.dumps(update_calendars(store, lambda url: http_text(url, agent or "jarvis")), indent=2))
    elif args.command == "edgar-update":
        agent = os.environ.get("JARVIS_SEC_USER_AGENT")
        if not agent:
            print(json.dumps({"result": "BLOCKED", "reason": "set JARVIS_SEC_USER_AGENT to 'Name email' (SEC requirement)"}))
            return 2
        tickers = [a.symbol for a in load_universe(Path(args.universe)) if a.asset_class == AssetClass.EQUITY]
        with LocalStorage(_home(args)) as store:
            print(json.dumps(update_edgar(store, EdgarClient(agent), tickers), indent=2))
    elif args.command == "data-check":
        from datetime import timedelta
        rows = []
        with LocalStorage(_home(args), writer=False) as store:
            for asset in load_universe(Path(args.universe)):
                for timeframe, adjustment in DATASETS[asset.asset_class]:
                    name = dataset_name(timeframe, adjustment)
                    step = (timedelta(days=1) if timeframe == "1Day" else timedelta(hours=1)) \
                        if asset.asset_class == AssetClass.CRYPTO else None
                    result = check_bars(store.load_bars(asset.symbol, asset.asset_class, dataset=name), expected_step=step)
                    rows.append({"asset": asset.symbol, "dataset": name, "rows": result["rows"],
                                 "first": result.get("first"), "last": result.get("last"), "issues": result["counts"]})
            for series in SERIES + PRICE_SERIES:
                rows.append({"asset": series.series_id, "dataset": "FRED", "rows": len(store.read_table("macro", series.series_id))})
        print(json.dumps(rows, indent=2))
    elif args.command == "review":
        with LocalStorage(_home(args)) as store:
            print(json.dumps(review_outcomes(store), indent=2))
    elif args.command == "info-ingest":
        with LocalStorage(_home(args)) as store:
            print(json.dumps(ingest(store, load_document(Path(args.file))), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

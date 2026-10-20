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
from .macro import SERIES, update_macro
from .quality import check_bars
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
                 "soak", "macro-update", "backfill", "data-check"):
        command = commands.add_parser(name)
        if name in ("backfill", "data-check"):
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
                    desk = PaperDesk(store, broker, data, policy, runtime)
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
    elif args.command in ("backtest", "train"):
        if not args.fixture:
            print(json.dumps({"result": "BLOCKED", "reason": "only --fixture is implemented; live research data is not verified"}))
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
            print(json.dumps(update_macro(store), indent=2))
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
            for series in SERIES:
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

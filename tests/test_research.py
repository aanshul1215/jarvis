import json
from dataclasses import replace
from datetime import timedelta

import pytest

from jarvis.contracts import AssetClass, Bar
from jarvis.config import load_policy
from jarvis.fixtures import research_bars
from jarvis.research import backtest_fixture, observations, train_fixture
from jarvis.storage import LocalStorage, StorageError


@pytest.mark.parametrize("asset,cls", [("AAPL", AssetClass.EQUITY), ("BTC/USD", AssetClass.CRYPTO)])
def test_research_is_reproducible_and_never_promotes(tmp_path, asset, cls):
    bars = research_bars(asset, cls)
    with LocalStorage(tmp_path / "desk") as store:
        store.save_bars(bars)
        rows = observations(store.load_bars(asset, cls))
        assert rows[0].snapshot.available_at <= bars[21].available_at
        store.save_features([r.snapshot for r in rows[:3]])
        assert store.load_features(asset, cls) == [r.snapshot for r in rows[:3]]
        first = train_fixture(store, bars)
        second = train_fixture(store, bars)
        assert first["models"]["logistic"]["holdout"] == second["models"]["logistic"]["holdout"]
        assert first["approval"] == "RESEARCH" and first["selection"] == "NO_AUTOMATIC_PROMOTION"
        assert set(first["models"]) == {"constant", "logistic"}
        assert len(first["models"]["logistic"]["walk_forward"]) >= 2
        assert first["models"]["logistic"]["holdout"]["calibration"]
        registry = store.load_json("model-registry")
        assert registry["models"][f"{first['run_id']}:logistic"]["status"] == "RESEARCH"
        backtest = backtest_fixture(store, bars)
        assert backtest["status"] == "HYPOTHETICAL"
        assert (store.home / "reports" / f"model-comparison-{first['run_id']}.csv").exists()
        assert (store.home / "reports").joinpath(next(p.name for p in (store.home / "reports").glob("backtest-trades-*.csv"))).exists()


def test_future_bar_cannot_change_past_features():
    bars = research_bars()
    original = observations(bars)[0].snapshot
    last = bars[-1]
    changed = Bar(**{**vars(last), "close": last.close * 1.01, "high": last.high * 1.02})
    assert observations(bars[:-1] + [changed])[0].snapshot == original


def test_feature_hash_detects_corruption(tmp_path):
    bars = research_bars()
    with LocalStorage(tmp_path / "desk") as store:
        snap = observations(bars)[0].snapshot
        path = store.save_features([snap])
        path.write_bytes(path.read_bytes() + b"tamper")
        with pytest.raises(StorageError, match="hash mismatch"):
            store.load_features("AAPL", AssetClass.EQUITY)


def test_bar_reingestion_preserves_first_availability(tmp_path):
    bars = research_bars()[:2]
    with LocalStorage(tmp_path / "desk") as store:
        store.save_bars(bars)
        repeated = [replace(bar, available_at=bar.available_at + timedelta(days=2)) for bar in bars]
        store.save_bars(repeated)
        assert store.load_bars("AAPL", AssetClass.EQUITY) == bars
        changed = replace(repeated[0], close=repeated[0].close * 1.001, high=repeated[0].high * 1.01)
        store.save_bars([changed])  # a vendor amendment becomes revision 2; it no longer halts the desk
        assert len(store.load_bars("AAPL", AssetClass.EQUITY, all_revisions=True)) == 3
        latest = store.load_bars("AAPL", AssetClass.EQUITY)
        assert latest[0].revision == 2 and latest[0].close == changed.close
        assert store.load_bars("AAPL", AssetClass.EQUITY, as_of=bars[0].available_at) == [bars[0]]


def test_owner_policy_is_default_deny(tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    example = {"version": "test", "approved_assets": ["AAPL"], "approved_strategies": ["breakout-volume"],
               "max_order_notional": 100, "max_asset_notional": 100, "max_portfolio_notional": 100,
               "max_daily_loss": 10, "max_drawdown": .1, "max_spread_bps": 10, "max_quote_age_seconds": 10,
               "paper_enabled": False, "crypto_enabled": False, "owner_approved": False}
    path = config / "owner-policy.json"
    path.write_text(json.dumps(example))
    with pytest.raises(ValueError, match="approval"):
        load_policy(tmp_path)
    example["paper_enabled"] = example["owner_approved"] = True
    example["max_order_notional"] = True
    path.write_text(json.dumps(example))
    with pytest.raises(ValueError, match="risk limit"):
        load_policy(tmp_path)
    example["max_order_notional"] = 100
    path.write_text(json.dumps(example))
    assert load_policy(tmp_path).approved_assets == ("AAPL",)

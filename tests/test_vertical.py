from datetime import timedelta

import pytest

from jarvis.broker import BrokerError, MockBroker
from jarvis.contracts import AssetClass, BrokerOrder, LedgerEvent, Mode, StrategyIntent, new_id, utc_now
from jarvis.dashboard import render
from jarvis.engine import TradingEngine
from jarvis.fixtures import synthetic_bars
from jarvis.market import features_for, scan
from jarvis.risk import BrokerState, Governor, RiskPolicy
from jarvis.review import review_outcomes
from jarvis.storage import LocalStorage, StorageError
from jarvis.strategies import StrategyRegistry, baseline_specs


def policy(*, approved=True, crypto=True):
    return RiskPolicy("test-v1", ("AAPL", "BTC/USD"), ("breakout-volume",),
                      500, 500, 1000, 100, 0.25, 30, 60,
                      owner_approved=approved, crypto_enabled=crypto)


def test_multiasset_offline_vertical_slice(tmp_path):
    home = tmp_path / "desk"
    with LocalStorage(home) as store:
        broker = MockBroker(cash=1000)
        engine = TradingEngine(store, broker, Governor(policy()), StrategyRegistry(baseline_specs()), Mode.SHADOW)
        with pytest.raises(BrokerError, match="reconcile"):
            engine.process(synthetic_bars())
        engine.reconcile()
        for asset, cls, qty in (("AAPL", AssetClass.EQUITY, 1), ("BTC/USD", AssetClass.CRYPTO, 0.1)):
            bars = synthetic_bars(asset, cls)
            store.save_bars(bars)
            again = store.load_bars(asset, cls)
            assert again == bars
            result = engine.process(bars, as_of=bars[-1].available_at, quantity=qty)
            assert any(row["result"] == "FILLED" for row in result)
            assert broker.state().positions[asset] == qty
            assert engine.exit_position(asset, cls, bars[-1].close + 1, reason="TEST_EXIT") == "FILLED"
        assert broker.state().positions["AAPL"] == 0
        assert broker.state().positions["BTC/USD"] == 0
        events = store.read_events()
        assert {x["event"]["event_type"] for x in events} >= {"FEATURE_SNAPSHOT", "CANDIDATE", "RISK_DECISION", "ORDER_INTENT", "BROKER_ORDER", "EXIT_ORDER", "TRADE_OUTCOME"}
        assert all(x["event"]["payload"]["evidence_class"] == "MOCK" for x in events if x["event"]["event_type"] == "TRADE_OUTCOME")
        review = review_outcomes(store)
        assert review["approval_change"] == "NONE"
        assert all(x["evidence_class"] == "MOCK" and x["net_pnl"] == "UNVERIFIED_FEES_AND_SLIPPAGE" for x in review["outcomes"])
        assert "jarvis_" in render(home, "SYNTHETIC_MOCK")
        store.export_csv("trades", [{"asset": "AAPL", "result": "MOCK"}])
        assert (home / "reports" / "trades.csv").read_text().startswith("asset,result")
    with LocalStorage(home) as store:
        restarted = TradingEngine(store, broker, Governor(policy()), StrategyRegistry(baseline_specs()), Mode.SHADOW)
        restarted.reconcile()
        before = len(broker.orders)
        bars = synthetic_bars()
        result = restarted.process(bars, as_of=bars[-1].available_at)
        assert any("DUPLICATE_ORDER" in row.get("reasons", ()) for row in result)
        assert len(broker.orders) == before


def test_point_in_time_feature_and_expiry():
    bars = synthetic_bars()
    previous = features_for(bars, bars[-2].available_at)
    current = features_for(bars, bars[-1].available_at)
    assert previous.snapshot_id != current.snapshot_id
    assert current.values["breakout_20"] > 0
    assert scan(current, current.available_at)
    assert not scan(current, current.expires_at + timedelta(seconds=1))
    assert features_for(bars, bars[-1].available_at).snapshot_id == current.snapshot_id


def test_governor_default_deny_and_limits():
    now = utc_now()
    intent = StrategyIntent("i", "c", "AAPL", AssetClass.EQUITY, "breakout-volume", "1.0.0", "baseline", "v1",
                            now, now + timedelta(minutes=1), "BUY", 1, 100, 3, "snap")
    state = BrokerState(1000, 1000, 1000, {}, reconciled=True)
    denied = Governor(None).assess(intent, state, Mode.PAPER, now, now, 2, "coid", set())
    assert denied.result == "BLOCK" and "OWNER_POLICY_MISSING" in denied.reason_codes
    allowed = Governor(policy()).assess(intent, state, Mode.SHADOW, now, now, 2, "coid", set(), mock=True)
    assert allowed.result == "ALLOW"
    stale = Governor(policy()).assess(intent, state, Mode.SHADOW, now, now - timedelta(minutes=2), 2, "coid", set(), mock=True)
    assert "STALE_OR_FUTURE_QUOTE" in stale.reason_codes
    duplicate = Governor(policy()).assess(intent, state, Mode.SHADOW, now, now, 2, "coid", {"coid"}, mock=True)
    assert "DUPLICATE_ORDER" in duplicate.reason_codes
    crypto = StrategyIntent(**{**vars(intent), "asset_id": "BTC/USD", "asset_class": AssetClass.CRYPTO})
    blocked = Governor(policy(crypto=False)).assess(crypto, state, Mode.SHADOW, now, now, 2, "coid2", set(), mock=True)
    assert "CRYPTO_NOT_APPROVED" in blocked.reason_codes
    mixed = BrokerState(1000, 1000, 1000, {"BTC/USD": .4}, position_values={"BTC/USD": 950}, reconciled=True)
    crowded = Governor(policy()).assess(intent, mixed, Mode.SHADOW, now, now, 2, "coid3", set(), mock=True)
    assert "PORTFOLIO_LIMIT" in crowded.reason_codes
    unknown_values = BrokerState(1000, 1000, 1000, {"BTC/USD": .4}, reconciled=True)
    fail_closed = Governor(policy()).assess(intent, unknown_values, Mode.SHADOW, now, now, 2, "coid4", set(), mock=True)
    assert "POSITION_VALUES_UNVERIFIED" in fail_closed.reason_codes


def test_uncertain_submit_lookup_and_unknown_position(tmp_path):
    with LocalStorage(tmp_path / "desk") as store:
        broker = MockBroker()
        broker.raise_after_accept = True
        engine = TradingEngine(store, broker, Governor(policy()), StrategyRegistry(baseline_specs()), Mode.SHADOW)
        engine.reconcile()
        bars = synthetic_bars()
        result = engine.process(bars, as_of=bars[-1].available_at)
        assert any(x["result"] == "FILLED" for x in result)
        assert len(broker.orders) == 1
        broker.positions["UNKNOWN"] = 1
        restarted = TradingEngine(store, broker, Governor(policy()), StrategyRegistry(baseline_specs()), Mode.SHADOW)
        with pytest.raises(BrokerError, match="position"):
            restarted.reconcile()
        assert restarted.mode == Mode.SAFE


def test_position_manager_uses_recorded_time_exit(tmp_path):
    from dataclasses import replace
    bars = synthetic_bars()
    with LocalStorage(tmp_path / "desk") as store:
        broker = MockBroker()
        engine = TradingEngine(store, broker, Governor(policy()), StrategyRegistry(baseline_specs()), Mode.SHADOW)
        engine.reconcile()
        engine.process(bars, as_of=bars[-1].available_at)
        assert engine.monitor_positions(bars)[0]["exit_reason"] == "HOLD"
        latest = bars[-1]
        for i in range(3):
            start = latest.end_at + timedelta(hours=i)
            bars.append(replace(latest, start_at=start, end_at=start + timedelta(hours=1),
                                available_at=start + timedelta(hours=1, seconds=1)))
        assert engine.monitor_positions(bars)[0]["exit_reason"] == "TIME_EXIT"
        assert broker.state().positions["AAPL"] == 0


def test_partial_fill_is_reconciled_before_next_decision(tmp_path):
    with LocalStorage(tmp_path / "desk") as store:
        broker = MockBroker(fill_fraction=.5)
        engine = TradingEngine(store, broker, Governor(policy()), StrategyRegistry(baseline_specs()), Mode.SHADOW)
        engine.reconcile()
        bars = synthetic_bars()
        engine.process(bars, as_of=bars[-1].available_at)
        order = next(iter(broker.orders.values()))
        assert order.status == "PARTIALLY_FILLED"
        broker.orders[order.client_order_id] = BrokerOrder(order.client_order_id, order.broker_order_id,
            order.asset_id, order.side, order.quantity, order.quantity, order.average_price, "FILLED", order.submitted_at)
        broker.positions[order.asset_id] = order.quantity
        broker.cash -= (order.quantity - order.filled_quantity) * order.average_price
        restarted = TradingEngine(store, broker, Governor(policy()), StrategyRegistry(baseline_specs()), Mode.SHADOW)
        restarted.reconcile()
        assert any(x["event"]["event_type"] == "ORDER_UPDATE" for x in store.read_events())


def test_journal_partial_write_recovery_and_corruption(tmp_path):
    home = tmp_path / "desk"
    with LocalStorage(home) as store:
        store.append_event(LedgerEvent(new_id("evt"), "TEST", utc_now(), "corr"))
        with pytest.raises(StorageError, match="another"):
            LocalStorage(home)
    journal = home / "journal" / "operational.jsonl"
    with journal.open("ab") as stream:
        stream.write(b'{"partial":')
    with LocalStorage(home) as recovered:
        assert len(recovered.read_events()) == 1
    assert list((home / "quarantine").glob("tail-*.bin"))
    raw = journal.read_bytes().replace(b'"event_type":"TEST"', b'"event_type":"EVIL"')
    journal.write_bytes(raw)
    with pytest.raises(StorageError, match="corruption"):
        LocalStorage(home)


def test_backup_and_parquet_integrity(tmp_path):
    home = tmp_path / "desk"
    with LocalStorage(home) as store:
        store.save_bars(synthetic_bars())
        backup = store.backup(tmp_path / "backup")
        assert LocalStorage.verify_backup(backup)
        parquet = home / "market" / "equity" / "AAPL" / "bars.parquet"
        parquet.write_bytes(parquet.read_bytes() + b"tamper")
        with pytest.raises(StorageError, match="hash mismatch"):
            store.load_bars("AAPL", AssetClass.EQUITY)

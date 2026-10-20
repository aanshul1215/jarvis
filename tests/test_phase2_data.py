"""Phase 2 data layer: FRED macro series, data quality, Alpaca history back-fill, universe."""

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from jarvis.contracts import AssetClass, Bar
from jarvis.history import AVAILABILITY_LAG, UniverseAsset, backfill, dataset_name, load_universe
from jarvis.macro import SERIES_BY_ID, available_at, latest_value, load_macro, parse_fred_csv, update_macro
from jarvis.quality import check_bars
from jarvis.storage import LocalStorage, StorageError

REPO = Path(__file__).resolve().parents[1]
UTC = timezone.utc


# ---------- FRED macro series ----------

def _csv(series_id, rows):
    return "observation_date," + series_id + "\n" + "".join(f"{d},{v}\n" for d, v in rows)


def test_fred_parse_skips_missing_and_rejects_wrong_series():
    parsed = parse_fred_csv(_csv("VIXCLS", [("2020-03-13", "57.83"), ("2020-03-16", "."), ("2020-03-17", "75.91")]), "VIXCLS")
    assert parsed == [(date(2020, 3, 13), 57.83), (date(2020, 3, 17), 75.91)]
    with pytest.raises(ValueError, match="header"):
        parse_fred_csv(_csv("DGS10", [("2020-03-13", "0.94")]), "VIXCLS")


def test_publication_timing_is_conservative():
    friday = date(2020, 3, 13)
    assert available_at(SERIES_BY_ID["VIXCLS"], friday) == datetime(2020, 3, 13, 22, tzinfo=UTC)
    assert available_at(SERIES_BY_ID["DGS10"], friday) == datetime(2020, 3, 16, 22, tzinfo=UTC)  # next business day


def test_macro_is_point_in_time_idempotent_and_keeps_revisions(tmp_path):
    rows = {"VIXCLS": [("2020-03-12", "75.47"), ("2020-03-13", "57.83")],
            "DGS10": [("2020-03-12", "0.88"), ("2020-03-13", "0.94")]}
    fetch = lambda s: _csv(s, rows[s])  # noqa: E731
    series = (SERIES_BY_ID["VIXCLS"], SERIES_BY_ID["DGS10"])
    clock = [datetime(2026, 10, 19, tzinfo=UTC)]
    with LocalStorage(tmp_path / "desk") as store:
        update_macro(store, series=series, fetch=fetch, now=lambda: clock[0])
        monday = datetime(2020, 3, 16, 15, tzinfo=UTC)
        assert latest_value(store, "VIXCLS", monday) == 57.83
        assert load_macro(store, "DGS10", as_of=monday)[-1]["observation_date"] == "2020-03-12"
        # a value dated in the future relative to the decision time must not leak in
        assert load_macro(store, "VIXCLS", as_of=datetime(2020, 3, 12, 21, tzinfo=UTC)) == []
        again = update_macro(store, series=series, fetch=fetch, now=lambda: clock[0])
        assert again["VIXCLS"] == {**again["VIXCLS"], "added": 0, "revised": 0}
        rows["VIXCLS"][1] = ("2020-03-13", "57.80")  # the source corrects a historical value
        update_macro(store, series=series, fetch=fetch, now=lambda: clock[0])
        assert latest_value(store, "VIXCLS", monday) == 57.83          # what was known then
        assert latest_value(store, "VIXCLS", clock[0]) == 57.80         # what is known now
        assert [e["event"]["event_type"] for e in store.read_events()].count("MACRO_UPDATE") == 3


# ---------- data quality ----------

def _series(closes, *, start=datetime(2026, 1, 5, tzinfo=UTC), step=timedelta(hours=1), volume=1000.0):
    bars, previous = [], closes[0]
    for i, close in enumerate(closes):
        s = start + i * step
        bars.append(Bar("BTC/USD", AssetClass.CRYPTO, s, s + step, s + step, previous,
                        max(previous, close) * 1.001, min(previous, close) * 0.999, close,
                        0.0 if volume == 0 else volume, "TEST", "TEST"))
        previous = close
    return bars


def test_quality_detects_spikes_gaps_stale_prices_and_zero_volume():
    closes = [100 + (i % 3) * 0.1 for i in range(40)]
    clean = check_bars(_series(closes), expected_step=timedelta(hours=1))
    assert clean["issues"] == []
    spiky = closes[:20] + [140.0] + closes[21:]
    assert "SPIKE" in check_bars(_series(spiky), expected_step=timedelta(hours=1))["counts"]
    gapped = _series(closes)
    gapped = gapped[:10] + gapped[13:]
    assert check_bars(gapped, expected_step=timedelta(hours=1))["counts"]["GAP"] == 1
    stale = check_bars(_series([100.0] * 10), expected_step=timedelta(hours=1))
    assert "STALE_PRICE" in stale["counts"]
    assert "ZERO_VOLUME" in check_bars(_series(closes, volume=0), expected_step=timedelta(hours=1))["counts"]


# ---------- Alpaca history back-fill ----------

class FakeHistory:
    """Serves deterministic daily and hourly bars for any symbol, honouring each request's window."""

    def __init__(self):
        self.requests = []

    def _naive_utc(self, value):
        return value if value.tzinfo else value.replace(tzinfo=UTC)

    def _serve(self, request):
        self.requests.append(request)
        hourly = "Hour" in str(request.timeframe)
        step = timedelta(hours=1) if hourly else timedelta(days=1)
        start, end = self._naive_utc(request.start), self._naive_utc(request.end)
        t = start.replace(minute=0, second=0, microsecond=0)
        models, price = [], 100.0
        while t + step <= end + step:
            if t >= start and t < end:
                models.append(SimpleNamespace(timestamp=t, open=price, high=price * 1.01, low=price * 0.99,
                                              close=price * 1.001, volume=1000))
            price *= 1.001
            t += step
        return SimpleNamespace(data={request.symbol_or_symbols: models})

    get_stock_bars = _serve
    get_crypto_bars = _serve


def _assets():
    return [UniverseAsset("SPY", AssetClass.EQUITY), UniverseAsset("BTC/USD", AssetClass.CRYPTO)]


def test_backfill_requests_sip_raw_and_adjusted_and_sets_availability(tmp_path):
    client = FakeHistory()
    start, end = datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 1, 20, 12, 30, tzinfo=UTC)
    with LocalStorage(tmp_path / "desk") as store:
        report = backfill(store, client, client, _assets(), start=start, end=end)
        assert set(report) == {"SPY:1Day-raw", "SPY:1Day-adjusted", "SPY:1Hour-raw",
                               "BTC/USD:1Day-raw", "BTC/USD:1Hour-raw"}
        stock_requests = [r for r in client.requests if getattr(r, "feed", None) is not None]
        assert {r.adjustment.value for r in stock_requests} == {"raw", "all"}
        assert {r.feed.value for r in stock_requests} == {"sip"}
        hourly = store.load_bars("SPY", AssetClass.EQUITY, dataset="1Hour-raw")
        assert all(b.available_at == b.end_at + AVAILABILITY_LAG[AssetClass.EQUITY] for b in hourly)
        assert all(b.end_at <= end for b in hourly)                       # no unfinished bar stored
        crypto = store.load_bars("BTC/USD", AssetClass.CRYPTO, dataset="1Hour-raw")
        assert report["BTC/USD:1Hour-raw"]["issues"] == {}                # contiguous 24/7 series
        assert crypto[-1].available_at == crypto[-1].end_at + AVAILABILITY_LAG[AssetClass.CRYPTO]
        rerun = backfill(store, client, client, _assets(), start=start, end=end)
        assert rerun["SPY:1Hour-raw"]["stored"] == report["SPY:1Hour-raw"]["stored"]
        assert max(b.revision for b in store.load_bars("SPY", AssetClass.EQUITY, all_revisions=True,
                                                       dataset="1Hour-raw")) == 1


def _hashes(home: Path) -> dict[str, str]:
    return {str(p.relative_to(home)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((home / "market").rglob("*.parquet"))}


def test_rebuilding_history_from_scratch_gives_identical_files(tmp_path):
    start, end = datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 2, 1, tzinfo=UTC)
    for name in ("a", "b"):
        with LocalStorage(tmp_path / name) as store:
            backfill(store, FakeHistory(), FakeHistory(), _assets(), start=start, end=end)
    first, second = _hashes(tmp_path / "a"), _hashes(tmp_path / "b")
    assert first and first == second


# ---------- universe and storage ----------

def test_universe_proposal_loads_and_validation_rejects_bad_files(tmp_path):
    assets = load_universe(REPO / "config" / "universe.example.json")
    assert sum(a.asset_class == AssetClass.CRYPTO for a in assets) == 2 and len(assets) >= 20
    bad = tmp_path / "u.json"
    bad.write_text(json.dumps({"version": "x", "equities": ["SPY", "SPY"], "crypto": []}))
    with pytest.raises(ValueError, match="unique"):
        load_universe(bad)
    bad.write_text(json.dumps({"version": "x", "equities": [], "crypto": ["BTCUSD"]}))
    with pytest.raises(ValueError, match="BASE/QUOTE"):
        load_universe(bad)
    assert dataset_name("1Day", "all") == "1Day-adjusted"


def test_generic_tables_are_hash_checked(tmp_path):
    with LocalStorage(tmp_path / "desk") as store:
        path = store.write_table("macro", "TEST", rows=[{"a": 1}])
        assert store.read_table("macro", "TEST") == [{"a": 1}]
        path.write_bytes(path.read_bytes() + b"tamper")
        with pytest.raises(StorageError, match="hash mismatch"):
            store.read_table("macro", "TEST")

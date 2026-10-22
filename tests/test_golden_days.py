"""Golden days: a recorded desk decision replays exactly, and any change in behaviour shows up as a difference."""

import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from jarvis import desks, golden
from jarvis.broker import MockBroker
from jarvis.contracts import utc_now
from jarvis.market_data import Quote
from jarvis.portfolio.sleeves import GROUPS
from jarvis.storage import LocalStorage
from synthetic import build_market

SYMBOLS = GROUPS["sector"] + ("SHY", "SPY", "IEF")


class FlatQuotes:
    """Every ETF at $100, 2 bps wide, quoted now."""

    def latest_quote(self, asset, cls):
        now = utc_now()
        return Quote(asset, cls, 99.99, 100.01, now, now, "test", 1.0)


@pytest.fixture
def main_home(tmp_path):
    home = tmp_path / "main"
    with LocalStorage(home) as store:
        build_market(store, symbols=SYMBOLS, end=datetime(2018, 7, 1, tzinfo=timezone.utc))
        days = [date(2015, 12, 1) + timedelta(days=i) for i in range(950)]
        store.write_table("macro", "DTB3", rows=[{"observation_date": d.isoformat(), "value": 1.5, "revision": 0,
                                                  "available_at": f"{d.isoformat()}T21:00:00Z"} for d in days])
    (home / "config").mkdir(exist_ok=True)
    (home / "config" / "owner-policy.json").write_text(json.dumps(
        {"max_daily_loss": 300, "max_drawdown": 0.25, "max_spread_bps": 50, "max_quote_age_seconds": 60}))
    desks.ensure_desk_home(home, "sector")
    (tmp_path / "universe.json").write_text(json.dumps({"version": "t", "equities": list(SYMBOLS), "crypto": []}))
    return home


def test_a_recorded_day_replays_exactly_and_a_settings_change_shows(main_home, tmp_path, monkeypatch):
    folder = golden.record(main_home, "sector", tmp_path / "universe.json", MockBroker(cash=10_000), FlatQuotes(),
                           day="2018-06-29")
    expected = json.loads((folder / "expected.json").read_text())
    assert expected["weights"] and expected["planned"]
    assert [r["status"] for r in golden.check(main_home)] == ["PASS"]
    monkeypatch.setitem(desks.DESKS["sector"], "band", 0.9)            # the desk would now trade differently
    result = golden.check(main_home)[0]
    assert result["status"] == "FAIL" and any(d.startswith("/planned") for d in result["first"])


def test_an_edited_recording_is_refused(main_home, tmp_path):
    folder = golden.record(main_home, "sector", tmp_path / "universe.json", MockBroker(cash=10_000), FlatQuotes(),
                           day="2018-06-29")
    universe = json.loads((folder / "universe.json").read_text())
    (folder / "universe.json").write_text(json.dumps({**universe, "equities": universe["equities"][:-1]}))
    result = golden.check(main_home)[0]
    assert result["status"] == "FAIL" and "changed since they were recorded" in result["first"][0]


def test_recording_refuses_a_closed_market_a_second_take_and_untracked_reads(main_home, tmp_path):
    class Closed(MockBroker):
        def equity_market_open(self):
            return False

    with pytest.raises(RuntimeError):
        golden.record(main_home, "sector", tmp_path / "universe.json", Closed(cash=10_000), FlatQuotes(), day="2018-06-29")
    golden.record(main_home, "sector", tmp_path / "universe.json", MockBroker(cash=10_000), FlatQuotes(), day="2018-06-28")
    with pytest.raises(FileExistsError):
        golden.record(main_home, "sector", tmp_path / "universe.json", MockBroker(cash=10_000), FlatQuotes(),
                      day="2018-06-28")
    with LocalStorage(tmp_path / "a") as a, LocalStorage(tmp_path / "b") as b:
        with pytest.raises(AttributeError):
            golden.RecordingStore(a, b).load_features                 # a read the recording could not copy


def test_compare_reports_each_difference_and_tolerates_rounding():
    assert golden.compare({"w": {"XLK": 0.3}, "n": [1, 2]}, {"w": {"XLK": 0.3 + 1e-15}, "n": [1, 2]}) == []
    problems = golden.compare({"w": {"XLK": 0.3, "XLF": 0.2}, "n": [1]}, {"w": {"XLK": 0.31, "SHY": 0.2}, "n": [1, 2]})
    assert problems == ["/n: 1 items recorded, 2 now", "/w/SHY: new (0.2)", "/w/XLF: gone (was 0.2)",
                        "/w/XLK: 0.3 -> 0.31"]


# The owner's real recordings live in JARVIS_HOME/golden (local only: they hold exchange and FRED data).
REAL = golden.recordings(Path(os.environ["JARVIS_HOME"])) if os.environ.get("JARVIS_HOME") else []


@pytest.mark.skipif(not REAL, reason="no golden days recorded in JARVIS_HOME")
@pytest.mark.parametrize("folder", REAL, ids=[f"{p.parent.name}-{p.name}" for p in REAL])
def test_recorded_golden_days_replay_unchanged(folder):
    expected = json.loads((folder / "expected.json").read_text())
    assert golden.compare(expected, golden.replay(folder)) == []

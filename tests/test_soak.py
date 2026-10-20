"""Short version of the Phase 1 exit test; `jarvis soak` runs the full 24 simulated hours."""

from jarvis.simulation import run_soak


def test_short_soak_never_stops_itself_and_exercises_messy_paths(tmp_path):
    report = run_soak(tmp_path / "desk", hours=6, poll_seconds=300, seed=11)
    assert report["passed"], report["stopped"]
    counts = report["event_counts"]
    assert counts["ORDER_CANCEL"] >= 1          # an unfilled entry was cancelled after its deadline
    assert counts["POSITION_ADJUSTMENT"] >= 1   # crypto fee taken from the coin received
    assert counts["TRADE_OUTCOME"] >= 1         # including an entry that was only partially filled
    assert counts["SESSION_SKIP"] >= 1          # equities skipped outside market hours
    assert report["bar_revisions_stored"] >= 1  # vendor amendments stored, not halting
    assert counts["CYCLE_ERROR"] == 0 and not report["overdue_open_entry_orders"]

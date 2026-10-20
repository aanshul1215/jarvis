"""Data-quality checks for stored bar series. Findings are reported; they never edit the data."""

from __future__ import annotations

import math
import statistics
from collections import Counter
from datetime import timedelta

from .contracts import Bar, iso


def check_bars(bars: list[Bar], *, expected_step: timedelta | None = None, max_abs_return: float = 0.25,
               spike_mad: float = 12.0, min_spike_return: float = 0.03, stale_run: int = 6) -> dict:
    """Check one asset's bars (latest revision per bar) for the problems that silently corrupt features.

    - duplicate timestamps;
    - gaps longer than ``expected_step`` (only for 24/7 series such as crypto; equity gaps follow the
      market calendar and are reported separately as long breaks of more than four days);
    - price spikes: a move above ``max_abs_return``, or a move of at least ``min_spike_return`` that is more than
      ``spike_mad`` robust deviations from normal;
    - zero-volume bars and runs of ``stale_run`` identical closes (a feed repeating its last value).
    """
    ordered = sorted(bars, key=lambda b: b.end_at)
    issues: list[dict] = []
    if not ordered:
        return {"rows": 0, "issues": [{"kind": "NO_DATA"}], "counts": {"NO_DATA": 1}}
    seen = Counter(b.end_at for b in ordered)
    issues += [{"kind": "DUPLICATE_TIMESTAMP", "end_at": iso(t), "detail": f"{n} rows"} for t, n in seen.items() if n > 1]
    for a, b in zip(ordered, ordered[1:]):
        step = b.end_at - a.end_at
        if expected_step is not None and step > expected_step:
            issues.append({"kind": "GAP", "end_at": iso(b.end_at), "detail": f"missing {step / expected_step - 1:.0f} bars"})
        elif expected_step is None and step > timedelta(days=4):
            issues.append({"kind": "LONG_BREAK", "end_at": iso(b.end_at), "detail": str(step)})
    returns = [b.close / a.close - 1 for a, b in zip(ordered, ordered[1:])]
    if len(returns) >= 20:
        median = statistics.median(returns)
        # Robust spread; a perfectly regular series has zero MAD, so fall back to the standard deviation.
        scale = 1.4826 * statistics.median(abs(r - median) for r in returns) or statistics.pstdev(returns) or 1e-12
        for bar, r in zip(ordered[1:], returns):
            if abs(r) > max_abs_return or (abs(r) >= min_spike_return and abs(r - median) / scale > spike_mad):
                issues.append({"kind": "SPIKE", "end_at": iso(bar.end_at), "detail": f"return {r:+.2%}"})
    issues += [{"kind": "ZERO_VOLUME", "end_at": iso(b.end_at), "detail": ""} for b in ordered if b.volume == 0]
    run = 1
    for a, b in zip(ordered, ordered[1:]):
        run = run + 1 if math.isclose(a.close, b.close, rel_tol=0, abs_tol=1e-12) else 1
        if run == stale_run:
            issues.append({"kind": "STALE_PRICE", "end_at": iso(b.end_at), "detail": f"{stale_run} identical closes"})
    return {"rows": len(ordered), "first": iso(ordered[0].end_at), "last": iso(ordered[-1].end_at),
            "issues": issues, "counts": dict(Counter(i["kind"] for i in issues))}

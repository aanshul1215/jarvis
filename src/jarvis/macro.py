"""Market-stress and rate series from FRED, stored point-in-time (situational awareness inputs).

FRED serves each series as a keyless CSV download. Every value gets an ``available_at`` time: the earliest moment
it would really have been known. Backtests must only read values with ``available_at <= decision time``.

Deliberately excluded:
- ``BAMLH0A0HYM2`` (high-yield spread): FRED only provides about three years of history (checked 2026-10-19).
  ``BAA10Y`` is the long-history credit-stress series instead.
- ``NFCI`` and ``STLFSI4``: estimated indices that are revised after publication, so today's history would leak
  future information into backtests. Add them only with vintage (ALFRED) support.
"""

from __future__ import annotations

import bisect
import csv
import io
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Callable

from .contracts import LedgerEvent, iso, new_id, parse_utc, utc_now
from .storage import LocalStorage

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"


@dataclass(frozen=True)
class MacroSeries:
    series_id: str
    description: str
    lag_business_days: int  # business days after the observation date before the value is published
    available_hour_utc: int  # hour (UTC) on that day from which the value is treated as known


# ASSUMPTION (conservative, to verify against publication schedules): VIX closes are final shortly after the
# 16:15 ET close, i.e. by 22:00 UTC the same day; Treasury and Moody's series appear on FRED the next business
# day. Exchange holidays are not modelled, which can only make a value look available slightly early on a
# holiday; the error is at most one day.
SERIES = (
    MacroSeries("VIXCLS", "CBOE VIX close (30-day implied volatility of the S&P 500)", 0, 22),
    MacroSeries("VXVCLS", "CBOE 3-month VIX close (VIX term structure with VIXCLS)", 0, 22),
    MacroSeries("DGS10", "10-year Treasury constant-maturity yield", 1, 22),
    MacroSeries("DGS2", "2-year Treasury constant-maturity yield", 1, 22),
    MacroSeries("T10Y2Y", "10-year minus 2-year Treasury spread", 1, 22),
    MacroSeries("DTB3", "3-month Treasury bill rate (cash yield)", 1, 22),
    MacroSeries("BAA10Y", "Moody's Baa corporate yield minus 10-year Treasury (credit stress)", 1, 22),
)
# Daily closing prices with long histories, used only as inputs to the Phase 5 model studies (volatility, regime,
# correlation), never for orders. They are copyrighted by their providers (S&P Dow Jones Indices, Nasdaq, Coinbase:
# "reproduction prohibited" on each FRED page, checked 2026-10-19), so they stay in JARVIS_HOME and are never
# committed. FRED shows only ten years of S&P and Dow Jones history; NASDAQCOM starts in 1971. Coinbase prices are
# taken at 17:00 Pacific. All are treated as published the next business day.
PRICE_SERIES = (
    MacroSeries("NASDAQCOM", "NASDAQ Composite index close", 1, 22),
    MacroSeries("SP500", "S&P 500 index close (last ten years only)", 1, 22),
    MacroSeries("DJIA", "Dow Jones Industrial Average close (last ten years only)", 1, 22),
    MacroSeries("CBBTCUSD", "Coinbase bitcoin price in US dollars (17:00 Pacific)", 1, 22),
    MacroSeries("CBETHUSD", "Coinbase ether price in US dollars (17:00 Pacific)", 1, 22),
)
PRICE_GROUPS = {"NASDAQCOM": "EQUITY", "SP500": "EQUITY", "DJIA": "EQUITY", "CBBTCUSD": "CRYPTO", "CBETHUSD": "CRYPTO"}
SERIES_BY_ID = {s.series_id: s for s in SERIES + PRICE_SERIES}


def available_at(series: MacroSeries, observed: date) -> datetime:
    day = observed
    added = 0
    while added < series.lag_business_days:
        day += timedelta(days=1)
        if day.weekday() < 5:
            added += 1
    return datetime(day.year, day.month, day.day, series.available_hour_utc, tzinfo=timezone.utc)


def fetch_fred_csv(series_id: str, *, attempts: int = 3, timeout: float = 120) -> str:
    """Download one series; FRED is occasionally slow, so retry with a growing pause."""
    # Python's default User-Agent is accepted; FRED reset connections for a custom label (checked 2026-10-19).
    request = urllib.request.Request(FRED_CSV.format(series=series_id))
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed https URL
                return response.read().decode("utf-8")
        except (TimeoutError, urllib.error.URLError, ConnectionError) as exc:
            if attempt == attempts:
                raise ConnectionError(f"FRED download failed for {series_id} after {attempts} attempts") from exc
            time.sleep(5 * attempt)
    raise AssertionError("unreachable")


def parse_fred_csv(text: str, series_id: str) -> list[tuple[date, float]]:
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or len(rows[0]) != 2 or rows[0][1] != series_id:
        raise ValueError(f"unexpected FRED CSV header for {series_id}: {rows[0] if rows else 'empty'}")
    values = []
    for when, value in rows[1:]:
        if value in ("", "."):
            continue  # FRED marks missing observations (holidays) with '.'
        values.append((date.fromisoformat(when), float(value)))
    return values


def update_macro(store: LocalStorage, *, series: tuple[MacroSeries, ...] = SERIES,
                 fetch: Callable[[str], str] = fetch_fred_csv, now: Callable[[], datetime] = utc_now) -> dict:
    """Download each series and merge it into ``macro/<series>.parquet``.

    A changed historical value is stored as a new revision that becomes available when it was first seen, so
    earlier decisions remain reproducible. Identical re-downloads change nothing.
    """
    report = {}
    for item in series:
        observed = parse_fred_csv(fetch(item.series_id), item.series_id)
        existing = store.read_table("macro", item.series_id)
        latest: dict[str, dict] = {}
        for row in existing:
            if row["observation_date"] not in latest or row["revision"] > latest[row["observation_date"]]["revision"]:
                latest[row["observation_date"]] = row
        rows = list(existing)
        added = revised = 0
        for when, value in observed:
            key = when.isoformat()
            previous = latest.get(key)
            if previous is None:
                rows.append({"series_id": item.series_id, "observation_date": key, "value": value,
                             "available_at": iso(available_at(item, when)), "revision": 1,
                             "source": FRED_CSV.format(series=item.series_id)})
                added += 1
            elif previous["value"] != value:
                rows.append({**previous, "value": value, "revision": previous["revision"] + 1,
                             "available_at": iso(max(now(), parse_utc(previous["available_at"])))})
                revised += 1
        if added or revised:
            rows.sort(key=lambda r: (r["observation_date"], r["revision"]))
            store.write_table("macro", item.series_id, rows=rows)
        report[item.series_id] = {"observations": len(observed), "added": added, "revised": revised,
                                  "first": observed[0][0].isoformat() if observed else None,
                                  "last": observed[-1][0].isoformat() if observed else None}
    store.append_event(LedgerEvent(new_id("evt"), "MACRO_UPDATE", now(), new_id("macro"),
                                   source_id="FRED", payload={"series": report}))
    return report


def load_macro(store: LocalStorage, series_id: str, *, as_of: datetime | None = None) -> list[dict]:
    """Latest revision of each observation known at ``as_of`` (all history when ``as_of`` is None)."""
    chosen: dict[str, dict] = {}
    for row in store.read_table("macro", series_id):
        if as_of is not None and parse_utc(row["available_at"]) > as_of:
            continue
        key = row["observation_date"]
        if key not in chosen or row["revision"] > chosen[key]["revision"]:
            chosen[key] = row
    return [chosen[k] for k in sorted(chosen)]


def latest_value(store: LocalStorage, series_id: str, as_of: datetime) -> float | None:
    rows = load_macro(store, series_id, as_of=as_of)
    return rows[-1]["value"] if rows else None


class AsOfSeries:
    """Value of a revised series as known at a moment: the newest observation (latest revision) published by then."""

    def __init__(self, rows: list[dict]):
        ordered = sorted(rows, key=lambda r: (parse_utc(r["available_at"]), r["observation_date"], r["revision"]))
        self.times = [parse_utc(r["available_at"]) for r in ordered]
        self.best, best = [], None
        for row in ordered:  # running "newest observation, latest revision" over everything published so far
            key = (row["observation_date"], row["revision"])
            if best is None or key >= (best["observation_date"], best["revision"]):
                best = row
            self.best.append(best)

    def at(self, moment: datetime) -> float | None:
        i = bisect.bisect_right(self.times, moment) - 1
        return float(self.best[i]["value"]) if i >= 0 else None


def as_of_series(store: LocalStorage, series_id: str) -> AsOfSeries:
    return AsOfSeries(store.read_table("macro", series_id))

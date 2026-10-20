"""Scheduled macro events: FOMC decisions, CPI and jobs-report releases (situational awareness, Phase 2).

Sources (parsed 2026-10-19):
- Federal Reserve meeting calendar (current page covers recent and next years; historical pages cover older years).
  The policy decision is announced at 14:00 New York time on the last day of each scheduled meeting.
- BLS release archives (past release dates are in each archive link, e.g. ``cpi_01142020.htm``) and the BLS release
  schedule pages (future dates). CPI and the Employment Situation report are released at 08:30 New York time.

Availability: these are scheduled in advance, so a backtest may know an event before it happens. ASSUMPTION: the Fed
publishes the next year's meetings around mid-year and BLS publishes the next year's schedule in the autumn, so
events are treated as known from 1 July (Fed) and 1 October (BLS) of the previous year. Unscheduled meetings and
notation votes are not treated as scheduled: an unscheduled (emergency) meeting is stored as
``FOMC_UNSCHEDULED`` and is known only from the end of its day. A cancelled meeting (17-18 March 2020) is kept with
``cancelled=True`` and never counts as upcoming; before the cancellation was announced it was in fact expected, a
small point-in-time simplification that affects only early March 2020.
"""

from __future__ import annotations

import re
from datetime import date, datetime, time, timezone
from typing import Callable
from zoneinfo import ZoneInfo

from .contracts import LedgerEvent, iso, new_id, parse_utc, utc_now
from .storage import LocalStorage

NEW_YORK = ZoneInfo("America/New_York")
FOMC_CURRENT = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
FOMC_HISTORICAL = "https://www.federalreserve.gov/monetarypolicy/fomchistorical{year}.htm"
BLS_ARCHIVE = "https://www.bls.gov/bls/news-release/{release}.htm"
BLS_SCHEDULE = "https://www.bls.gov/schedule/news_release/{release}.htm"
RELEASES = {"CPI_RELEASE": "cpi", "JOBS_RELEASE": "empsit"}
MONTHS = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}


def _month(label: str) -> int:
    return MONTHS[label.strip().lower()[:3]]


def _event_utc(day: date, hour: int, minute: int) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=NEW_YORK).astimezone(timezone.utc)


def fomc_decision_day(year: int, month_label: str, day_label: str) -> date | None:
    """Last day of a scheduled meeting, e.g. ('Apr/May', '30-1') -> 1 May. None for notation votes and the like."""
    if "(" in day_label or not re.fullmatch(r"\s*\d+(-\d+)?\*?\s*", day_label):
        return None
    last_day = int(day_label.strip().rstrip("*").split("-")[-1])
    return date(year, _month(month_label.split("/")[-1]), last_day)


def parse_fomc_current(html: str) -> list[date]:
    days = []
    for match in re.finditer(r'<h4><a id="\d+">(\d{4}) FOMC Meetings</a></h4>(.*?)(?=<h4><a id="\d+">\d{4} FOMC Meetings|$)',
                             html, re.S):
        year, body = int(match.group(1)), match.group(2)
        months = re.findall(r'fomc-meeting__month[^>]*><strong>([^<]+)</strong>', body)
        labels = re.findall(r'fomc-meeting__date[^>]*>([^<]+)<', body)
        days += [d for d in (fomc_decision_day(year, m, l) for m, l in zip(months, labels)) if d]
    return sorted(days)


def parse_fomc_historical(html: str, year: int) -> list[tuple[date, str]]:
    """(decision day, status) with status SCHEDULED, UNSCHEDULED or CANCELLED."""
    found = []
    pattern = rf'<h5[^>]*>\s*([A-Za-z]+(?:/[A-Za-z]+)?) (\d+(?:-\d+)?)(?: \((unscheduled|cancelled)\))? Meeting - {year}\s*</h5>'
    for month_label, day_label, note in re.findall(pattern, html):
        day = fomc_decision_day(year, month_label, day_label)
        if day:
            found.append((day, note.upper() if note else "SCHEDULED"))
    return sorted(found)


def parse_bls_archive(html: str, release: str) -> list[date]:
    found = re.findall(rf'/news\.release/archives/{release}_(\d{{2}})(\d{{2}})(\d{{4}})\.htm', html)
    return sorted({date(int(y), int(m), int(d)) for m, d, y in found})


def parse_bls_schedule(html: str) -> list[tuple[date, int, int]]:
    rows = []
    for when, clock in re.findall(r'<td>([A-Z][a-z]{2,4}\.? \d{1,2}, \d{4})</td>\s*<td>(\d{2}:\d{2} [AP]M)</td>', html):
        month, day, year = re.match(r'([A-Za-z]+)\.? (\d+), (\d{4})', when).groups()
        hour, minute = (int(x) for x in clock[:5].split(":"))
        hour = hour % 12 + (12 if clock.endswith("PM") else 0)
        rows.append((date(int(year), _month(month), int(day)), hour, minute))
    return sorted(set(rows))


def update_calendars(store: LocalStorage, fetch: Callable[[str], str], *, first_year: int = 2016) -> dict:
    events: dict[tuple[str, str], dict] = {}

    def add(kind: str, day: date, hour: int, minute: int, source: str, known_from: date | None, *,
            scheduled: bool = True, cancelled: bool = False) -> None:
        event_at = _event_utc(day, hour, minute)
        known = datetime.combine(known_from, time(0), tzinfo=timezone.utc) if known_from else event_at
        events[(kind, day.isoformat())] = {
            "event_type": kind, "local_date": day.isoformat(), "local_time": f"{hour:02d}:{minute:02d}",
            "event_at": iso(event_at), "scheduled": scheduled, "cancelled": cancelled,
            "available_at": iso(known), "source_url": source}

    current = parse_fomc_current(fetch(FOMC_CURRENT))
    for day in current:
        add("FOMC_DECISION", day, 14, 0, FOMC_CURRENT, date(day.year - 1, 7, 1))
    earliest_current = min(d.year for d in current) if current else datetime.now(timezone.utc).year
    for year in range(first_year, earliest_current):
        url = FOMC_HISTORICAL.format(year=year)
        for day, status in parse_fomc_historical(fetch(url), year):
            if status == "UNSCHEDULED":  # time not published on the page: known only at the end of that day
                add("FOMC_UNSCHEDULED", day, 23, 59, url, None, scheduled=False)
            else:
                add("FOMC_DECISION", day, 14, 0, url, date(year - 1, 7, 1), cancelled=status == "CANCELLED")
    for kind, release in RELEASES.items():
        archive = BLS_ARCHIVE.format(release=release)
        for day in parse_bls_archive(fetch(archive), release):
            if day.year >= first_year:
                add(kind, day, 8, 30, archive, date(day.year - 1, 10, 1))
        schedule = BLS_SCHEDULE.format(release=release)
        for day, hour, minute in parse_bls_schedule(fetch(schedule)):
            add(kind, day, hour, minute, schedule, date(day.year - 1, 10, 1))
    rows = sorted(events.values(), key=lambda r: (r["event_at"], r["event_type"]))
    store.write_table("calendar", "events", rows=rows)
    counts = {kind: sum(r["event_type"] == kind for r in rows)
              for kind in ("FOMC_DECISION", "FOMC_UNSCHEDULED", *RELEASES)}
    counts["cancelled"] = sum(r["cancelled"] for r in rows)
    report = {"events": len(rows), "by_type": counts, "first": rows[0]["local_date"], "last": rows[-1]["local_date"]}
    store.append_event(LedgerEvent(new_id("evt"), "CALENDAR_UPDATE", utc_now(), new_id("calendar"), payload=report))
    return report


def upcoming(store: LocalStorage, as_of: datetime, *, event_type: str | None = None) -> list[dict]:
    """Scheduled events after ``as_of`` that were already known at ``as_of``, soonest first."""
    return [r for r in store.read_table("calendar", "events")
            if parse_utc(r["event_at"]) > as_of and parse_utc(r["available_at"]) <= as_of and not r["cancelled"]
            and (event_type is None or r["event_type"] == event_type)]


def hours_until_next(store: LocalStorage, as_of: datetime, event_type: str) -> float | None:
    """Situational-awareness feature: hours from ``as_of`` to the next known event of this type."""
    events = upcoming(store, as_of, event_type=event_type)
    return (parse_utc(events[0]["event_at"]) - as_of).total_seconds() / 3600 if events else None


def http_text(url: str, user_agent: str) -> str:
    import urllib.request

    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - fixed official hosts
        return response.read().decode("utf-8", "replace")

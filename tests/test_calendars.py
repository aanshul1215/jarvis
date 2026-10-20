"""Event calendar parsing and point-in-time lookups, using fragments shaped like the official pages."""

from datetime import date, datetime, timezone

from jarvis.calendars import (fomc_decision_day, hours_until_next, parse_bls_archive, parse_bls_schedule,
                              parse_fomc_current, parse_fomc_historical, update_calendars, upcoming)
from jarvis.storage import LocalStorage

UTC = timezone.utc
CURRENT = """<h4><a id="1">2021 FOMC Meetings</a></h4>
<div class="fomc-meeting__month col-xs-5"><strong>Jan/Feb</strong></div><div class="fomc-meeting__date col-xs-4">31-1</div>
<div class="fomc-meeting__month col-xs-5"><strong>August</strong></div><div class="fomc-meeting__date col-xs-4">22 (notation vote)</div>
<div class="fomc-meeting__month col-xs-5"><strong>March</strong></div><div class="fomc-meeting__date col-xs-4">16-17*</div>"""
HISTORICAL = """<h5 class="panel-heading">March 2 (unscheduled) Meeting - 2020</h5>
<h5 class="panel-heading">March 17-18 (cancelled) Meeting - 2020</h5>
<h5 class="panel-heading">April 28-29 Meeting - 2020</h5>"""
ARCHIVE = '<a href="/news.release/archives/cpi_01142020.htm">December 2019</a><a href="/news.release/archives/cpi_02132020.htm">x</a>'
SCHEDULE = "<tr><td>October 2026</td> <td>Nov. 10, 2026</td> <td>08:30 AM</td></tr><tr><td>May</td><td>May 12, 2027</td><td>08:30 AM</td></tr>"


def test_parsers_follow_the_official_page_formats():
    assert fomc_decision_day(2024, "Apr/May", "30-1") == date(2024, 5, 1)
    assert fomc_decision_day(2025, "August", "22 (notation vote)") is None
    assert parse_fomc_current(CURRENT) == [date(2021, 2, 1), date(2021, 3, 17)]
    assert parse_fomc_historical(HISTORICAL, 2020) == [(date(2020, 3, 2), "UNSCHEDULED"),
                                                       (date(2020, 3, 18), "CANCELLED"),
                                                       (date(2020, 4, 29), "SCHEDULED")]
    assert parse_bls_archive(ARCHIVE, "cpi") == [date(2020, 1, 14), date(2020, 2, 13)]
    assert parse_bls_schedule(SCHEDULE) == [(date(2026, 11, 10), 8, 30), (date(2027, 5, 12), 8, 30)]


def test_calendar_is_point_in_time(tmp_path):
    pages = {"fomccalendars": CURRENT, "fomchistorical2020": HISTORICAL}

    def fetch(url):
        for key, html in pages.items():
            if key in url:
                return html
        if "fomchistorical" in url:
            return ""
        return ARCHIVE if "news-release" in url else SCHEDULE

    with LocalStorage(tmp_path / "desk") as store:
        report = update_calendars(store, fetch, first_year=2020)
        assert report["by_type"]["FOMC_UNSCHEDULED"] == 1 and report["by_type"]["cancelled"] == 1
        feb = datetime(2020, 2, 20, tzinfo=UTC)
        next_fomc = upcoming(store, feb, event_type="FOMC_DECISION")[0]
        assert next_fomc["local_date"] == "2020-04-29"                       # cancelled meeting never upcoming
        assert next_fomc["event_at"] == "2020-04-29T18:00:00Z"                # 14:00 New York (EDT)
        assert not upcoming(store, datetime(2020, 3, 1, tzinfo=UTC), event_type="FOMC_UNSCHEDULED")
        assert hours_until_next(store, datetime(2020, 1, 14, 12, 0, tzinfo=UTC), "CPI_RELEASE") == 1.5
        cpi = upcoming(store, datetime(2020, 1, 14, 13, 0, tzinfo=UTC), event_type="CPI_RELEASE")[0]
        assert cpi["local_date"] == "2020-01-14" and cpi["event_at"] == "2020-01-14T13:30:00Z"  # 08:30 EST

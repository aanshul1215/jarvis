"""SEC EDGAR loader, offline: fake responses mirror the real JSON and index-page structures (checked 2026-10-19)."""

import json
import urllib.error
from datetime import datetime, timezone

import pytest

from jarvis.edgar import (EdgarClient, earnings_events, end_of_filing_day, fundamentals, parse_accepted,
                          update_edgar)
from jarvis.storage import LocalStorage

UTC = timezone.utc
UA = "Test Owner owner@example.com"


def _index(accepted):
    return f'<div class="formGrouping"><div class="infoHead">Accepted</div>\n<div class="info">{accepted}</div></div>'


def _block(filings):
    keys = ("accessionNumber", "filingDate", "reportDate", "acceptanceDateTime", "form", "items", "primaryDocument")
    return {k: [f.get(k, "") for f in filings] for k in keys}


RECENT = [
    {"accessionNumber": "0000000001-26-000018", "filingDate": "2026-07-30", "form": "8-K", "items": "2.02,9.01",
     "acceptanceDateTime": "2026-07-31T00:30:28.000Z"},  # the unreliable JSON field: 8 hours ahead
    {"accessionNumber": "0000000001-26-000020", "filingDate": "2026-07-31", "form": "10-Q", "items": ""},
    {"accessionNumber": "0000000001-26-000005", "filingDate": "2026-01-29", "form": "8-K", "items": "2.02,9.01"},
    {"accessionNumber": "0000000001-26-000003", "filingDate": "2026-01-10", "form": "S-8", "items": ""},
]
OLDER = [{"accessionNumber": "0000000001-16-000002", "filingDate": "2016-01-26", "form": "8-K", "items": "2.02"}]
FACTS = {"facts": {"us-gaap": {"EarningsPerShareDiluted": {"units": {"USD/shares": [
    {"start": "2026-03-29", "end": "2026-06-27", "val": 2.02, "accn": "0000000001-26-000020", "fy": 2026,
     "fp": "Q3", "form": "10-Q", "filed": "2026-07-31"},
    {"start": "2025-09-28", "end": "2026-06-27", "val": 6.88, "accn": "0000000001-26-000020", "fy": 2026,
     "fp": "Q3", "form": "10-Q", "filed": "2026-07-31"}]}}},
    "dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [
        {"end": "2026-07-17", "val": 14700000000, "accn": "0000000001-26-000020", "fy": 2026, "fp": "Q3",
         "form": "10-Q", "filed": "2026-07-31"}]}}}}}


class FakeSec:
    def __init__(self):
        self.urls = []

    def __call__(self, url, user_agent):
        assert user_agent == UA
        self.urls.append(url)
        if url.endswith("company_tickers.json"):
            return json.dumps({"0": {"cik_str": 1, "ticker": "TEST"}, "1": {"cik_str": 2, "ticker": "FUND"}}).encode()
        if url.endswith("CIK0000000001.json") and "submissions" in url:
            return json.dumps({"filings": {"recent": _block(RECENT), "files": [
                {"name": "CIK0000000001-submissions-001.json", "filingFrom": "2010-01-01", "filingTo": "2016-03-01"}]}}).encode()
        if url.endswith("CIK0000000001-submissions-001.json"):
            return json.dumps(_block(OLDER)).encode()
        if url.endswith("CIK0000000002.json") and "submissions" in url:
            return json.dumps({"filings": {"recent": _block([]), "files": []}}).encode()
        if "companyfacts/CIK0000000001" in url:
            return json.dumps(FACTS).encode()
        if "companyfacts/CIK0000000002" in url:
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        accepted = {"000000000126000018": "2026-07-30 16:30:28", "000000000126000005": "2026-01-29 16:30:33",
                    "000000000116000002": "2016-01-26 16:31:06"}
        for key, when in accepted.items():
            if key in url:
                return _index(when).encode()
        raise AssertionError(f"unexpected URL {url}")


def _client(fake):
    return EdgarClient(UA, fetch=fake, sleep=lambda s: None)


def test_user_agent_must_identify_a_person():
    with pytest.raises(ValueError, match="User-Agent"):
        EdgarClient("jarvis-research")


def test_new_york_time_conversion_handles_daylight_saving():
    assert parse_accepted(_index("2026-07-30 16:30:28")) == datetime(2026, 7, 30, 20, 30, 28, tzinfo=UTC)  # EDT
    assert parse_accepted(_index("2026-01-29 16:30:33")) == datetime(2026, 1, 29, 21, 30, 33, tzinfo=UTC)  # EST
    assert end_of_filing_day("2026-07-31") == datetime(2026, 8, 1, 3, 59, 59, tzinfo=UTC)


def test_filings_events_and_fundamentals_are_point_in_time(tmp_path):
    fake = FakeSec()
    with LocalStorage(tmp_path / "desk") as store:
        report = update_edgar(store, _client(fake), ["TEST", "FUND", "NOPE"])
        assert report["NOPE"] == {"status": "NOT_IN_SEC_TICKER_MAP"}
        assert report["FUND"]["filings"] == 0 and report["FUND"]["fact_rows"] == 0
        assert report["TEST"]["earnings_releases"] == 3 and report["TEST"]["filings"] == 4  # S-8 dropped
        events = earnings_events(store, "TEST")
        assert events[-1]["available_at"] == "2026-07-30T20:30:28Z"           # index page, not the JSON field
        assert events[-1]["acceptance_source"] == "INDEX_PAGE"
        assert events[0]["filing_date"] == "2016-01-26"                        # older page followed
        before = datetime(2026, 7, 30, 20, 0, tzinfo=UTC)
        assert earnings_events(store, "TEST", as_of=before)[-1]["filing_date"] == "2026-01-29"
        quarterly = fundamentals(store, "TEST", "eps_diluted", as_of=datetime(2026, 8, 15, tzinfo=UTC),
                                 quarterly_only=True)
        assert [r["value"] for r in quarterly] == [2.02]                      # year-to-date 6.88 excluded
        assert fundamentals(store, "TEST", "eps_diluted", as_of=datetime(2026, 7, 31, 12, tzinfo=UTC)) == []
        assert fundamentals(store, "TEST", "shares_outstanding",
                            as_of=datetime(2026, 8, 1, 4, tzinfo=UTC))[0]["value"] == 14700000000
        index_calls = sum("-index.htm" in u for u in fake.urls)
        update_edgar(store, _client(fake), ["TEST"])
        assert sum("-index.htm" in u for u in fake.urls) == index_calls      # resolved times are never re-fetched

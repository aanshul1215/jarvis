"""SEC EDGAR filings, earnings-release events and fundamentals, stored point-in-time (Phase 2).

SEC requires every automated client to identify itself with a name and contact email in the User-Agent header
and to stay under 10 requests per second. The contact is read from ``JARVIS_SEC_USER_AGENT`` and is never stored
in Git.

Timing (checked 2026-10-19): the ``acceptanceDateTime`` field in the submissions JSON is not reliable. For Apple's
earnings 8-Ks it was 8 hours ahead of the official acceptance time, while for a Form 4 it was correct UTC. The
authoritative time is the "Accepted" line on each filing's index page, in New York time. Earnings releases (8-K
item 2.02) therefore use the index-page time; every other filing is treated as known at the end of its filing day,
which is conservative.
"""

from __future__ import annotations

import gzip
import json
import re
import time
import urllib.error
import urllib.request
from datetime import date, datetime, time as clock_time, timezone
from typing import Callable
from zoneinfo import ZoneInfo

from .contracts import LedgerEvent, iso, new_id, parse_utc, utc_now
from .storage import LocalStorage

NEW_YORK = ZoneInfo("America/New_York")
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/{name}"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
INDEX_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{nodash}/{accession}-index.htm"
FORMS = ("8-K", "10-Q", "10-K", "4")
EARNINGS_ITEM = "2.02"  # Form 8-K item 2.02: Results of Operations and Financial Condition
CONCEPTS = {  # stored name -> us-gaap / dei concepts tried in order (companies use different tags over time)
    "revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"),
    "net_income": ("NetIncomeLoss",),
    "eps_diluted": ("EarningsPerShareDiluted",),
    "assets": ("Assets",),
    "liabilities": ("Liabilities",),
    "equity": ("StockholdersEquity",),
    "operating_cash_flow": ("NetCashProvidedByUsedInOperatingActivities",),
    "shares_outstanding": ("dei:EntityCommonStockSharesOutstanding",),
}
_ACCEPTED = re.compile(r'Accepted</div>\s*<div class="info">(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})</div>')


class EdgarClient:
    """Polite HTTP client: identifies the owner, spaces requests, retries transient failures."""

    def __init__(self, user_agent: str, *, min_interval: float = 0.15,
                 fetch: Callable[[str, str], bytes] | None = None, sleep: Callable[[float], None] = time.sleep):
        if "@" not in user_agent or len(user_agent.split()) < 2:
            raise ValueError("SEC User-Agent must be 'Name email@domain' (set JARVIS_SEC_USER_AGENT)")
        self.user_agent, self.min_interval, self.sleep = user_agent, min_interval, sleep
        self._fetch = fetch or self._http
        self._last = 0.0
        self.requests = 0

    def _http(self, url: str, user_agent: str) -> bytes:
        request = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept-Encoding": "gzip"})
        with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - fixed SEC hosts
            body = response.read()
            return gzip.decompress(body) if response.headers.get("Content-Encoding") == "gzip" else body

    def get(self, url: str, *, attempts: int = 3) -> bytes:
        for attempt in range(1, attempts + 1):
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                self.sleep(wait)
            self._last = time.monotonic()
            self.requests += 1
            try:
                return self._fetch(url, self.user_agent)
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    raise
                if attempt == attempts:
                    raise ConnectionError(f"SEC request failed: {url} ({exc.code})") from exc
            except (TimeoutError, urllib.error.URLError, ConnectionError) as exc:
                if attempt == attempts:
                    raise ConnectionError(f"SEC request failed: {url}") from exc
            self.sleep(2 * attempt)
        raise AssertionError("unreachable")

    def get_json(self, url: str) -> dict:
        return json.loads(self.get(url).decode("utf-8"))


def end_of_filing_day(filing_date: str) -> datetime:
    """Conservative availability: 23:59:59 New York time on the filing date, in UTC."""
    local = datetime.combine(date.fromisoformat(filing_date), clock_time(23, 59, 59), tzinfo=NEW_YORK)
    return local.astimezone(timezone.utc)


def parse_accepted(index_html: str) -> datetime:
    match = _ACCEPTED.search(index_html)
    if not match:
        raise ValueError("no Accepted timestamp on the filing index page")
    local = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=NEW_YORK)
    return local.astimezone(timezone.utc)


def ticker_map(client: EdgarClient) -> dict[str, int]:
    return {v["ticker"].upper(): int(v["cik_str"]) for v in client.get_json(TICKERS_URL).values()}


def _rows(block: dict) -> list[dict]:
    return [dict(zip(block, values)) for values in zip(*block.values())] if block else []


def load_filings(client: EdgarClient, cik: int, since: date) -> list[dict]:
    """All filings since ``since``: the recent block plus any older pages that reach back that far."""
    document = client.get_json(SUBMISSIONS_URL.format(name=f"CIK{cik:010d}.json"))
    filings = _rows(document["filings"]["recent"])
    for page in document["filings"].get("files", []):
        if date.fromisoformat(page["filingTo"]) >= since:
            filings += _rows(client.get_json(SUBMISSIONS_URL.format(name=page["name"])))
    return [f for f in filings if date.fromisoformat(f["filingDate"]) >= since]


def _facts(document: dict, ticker: str, cik: int) -> list[dict]:
    rows = []
    for name, candidates in CONCEPTS.items():
        for candidate in candidates:
            taxonomy, concept = candidate.split(":") if ":" in candidate else ("us-gaap", candidate)
            units = document.get("facts", {}).get(taxonomy, {}).get(concept, {}).get("units", {})
            if not units:
                continue
            for unit, values in units.items():
                for v in values:
                    start = v.get("start")
                    duration = (date.fromisoformat(v["end"]) - date.fromisoformat(start)).days if start else None
                    rows.append({"ticker": ticker, "cik": cik, "metric": name, "concept": f"{taxonomy}:{concept}",
                                 "unit": unit, "period_start": start, "period_end": v["end"], "duration_days": duration,
                                 "value": float(v["val"]), "fiscal_year": v.get("fy"), "fiscal_period": v.get("fp"),
                                 "form": v.get("form"), "accession": v["accn"], "filed": v["filed"],
                                 "available_at": iso(end_of_filing_day(v["filed"]))})
            break  # first concept that exists wins for this metric
    return rows


def update_edgar(store: LocalStorage, client: EdgarClient, tickers: list[str], *,
                 since: date = date(2016, 1, 1)) -> dict:
    """Refresh filings and fundamentals for ``tickers``; tickers SEC does not know (e.g. some ETFs) are reported."""
    ciks = ticker_map(client)
    report: dict[str, dict] = {}
    for ticker in tickers:
        cik = ciks.get(ticker.upper())
        if cik is None:
            report[ticker] = {"status": "NOT_IN_SEC_TICKER_MAP"}
            continue
        known = {row["accession"]: row for row in store.read_table("edgar", "filings", ticker)}
        rows, index_lookups = [], 0
        for filing in load_filings(client, cik, since):
            if filing["form"] not in FORMS:
                continue
            accession = filing["accessionNumber"]
            earnings = filing["form"] == "8-K" and EARNINGS_ITEM in (filing.get("items") or "").split(",")
            previous = known.get(accession)
            if previous is not None and (previous["acceptance_source"] == "INDEX_PAGE" or not earnings):
                rows.append(previous)  # already resolved; never re-fetch
                continue
            available, source = end_of_filing_day(filing["filingDate"]), "END_OF_FILING_DAY"
            if earnings:
                html = client.get(INDEX_URL.format(cik=cik, nodash=accession.replace("-", ""),
                                                   accession=accession)).decode("utf-8", "replace")
                available, source = parse_accepted(html), "INDEX_PAGE"
                index_lookups += 1
            rows.append({"ticker": ticker, "cik": cik, "accession": accession, "form": filing["form"],
                         "filing_date": filing["filingDate"], "report_date": filing.get("reportDate") or None,
                         "items": filing.get("items") or "", "earnings_release": earnings,
                         "available_at": iso(available), "acceptance_source": source,
                         "primary_document": filing.get("primaryDocument") or ""})
        rows.sort(key=lambda r: (r["available_at"], r["accession"]))
        if rows:
            store.write_table("edgar", "filings", ticker, rows=rows)
        try:
            facts = _facts(client.get_json(FACTS_URL.format(cik=cik)), ticker, cik)
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
            facts = []  # no XBRL facts (typical for ETF trusts)
        if facts:
            facts.sort(key=lambda r: (r["metric"], r["period_end"], r["filed"], r["accession"], r["unit"]))
            store.write_table("edgar", "facts", ticker, rows=facts)
        report[ticker] = {"cik": cik, "filings": len(rows), "earnings_releases": sum(r["earnings_release"] for r in rows),
                          "index_page_lookups": index_lookups, "fact_rows": len(facts)}
    store.append_event(LedgerEvent(new_id("evt"), "EDGAR_UPDATE", utc_now(), new_id("edgar"), source_id="SEC_EDGAR",
                                   payload={"since": since.isoformat(), "tickers": report,
                                            "requests": client.requests}))
    return report


def earnings_events(store: LocalStorage, ticker: str, *, as_of: datetime | None = None) -> list[dict]:
    """Earnings releases (8-K item 2.02) known at ``as_of``, oldest first."""
    rows = [r for r in store.read_table("edgar", "filings", ticker) if r["earnings_release"]]
    return [r for r in rows if as_of is None or parse_utc(r["available_at"]) <= as_of]


QUARTER_DAYS = (80, 100)  # a fiscal quarter; longer durations are year-to-date or annual totals


def fundamentals(store: LocalStorage, ticker: str, metric: str, *, as_of: datetime,
                 quarterly_only: bool = False) -> list[dict]:
    """Every reported value of ``metric`` known at ``as_of``; for each period the latest filing wins.

    Flow metrics (revenue, EPS, cash flow) are reported for quarters and for year-to-date periods ending on the same
    date; ``quarterly_only`` keeps only quarter-length periods. Balance-sheet metrics have no start date.
    """
    chosen: dict[tuple, dict] = {}
    for row in store.read_table("edgar", "facts", ticker):
        if row["metric"] != metric or parse_utc(row["available_at"]) > as_of:
            continue
        if quarterly_only and not (row["duration_days"] and QUARTER_DAYS[0] <= row["duration_days"] <= QUARTER_DAYS[1]):
            continue
        key = (row["period_start"], row["period_end"], row["unit"])
        if key not in chosen or row["filed"] >= chosen[key]["filed"]:
            chosen[key] = row
    return sorted(chosen.values(), key=lambda r: r["period_end"])

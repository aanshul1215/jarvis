"""Daily data refresh for the live stock book (read-only market data; no orders).

1. Universe: when the current month has no entry, rebuild it from the previous month's dollar volume across the
   same survivorship-aware candidate list (data.candidates), exactly as in research.
2. Industry codes: SEC SIC codes for any universe stock not yet classified (needs JARVIS_SEC_USER_AGENT).
3. Prices: daily adjusted and raw bars for the current and previous month's universes, from about 15 months back
   (enough for 12-1 momentum, 63-day volatility and the 20-day event window), into live_daily_*.parquet.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import data as D

LOOKBACK_DAYS = 460


def _months_back(day: datetime, n: int) -> datetime:
    y, m = day.year, day.month - n
    while m <= 0:
        y, m = y - 1, m + 12
    return datetime(y, m, 1, tzinfo=timezone.utc)


def update(home: Path, key: str, secret: str, *, now: datetime | None = None) -> dict:
    from alpaca.data import StockHistoricalDataClient
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
    from alpaca.trading.client import TradingClient
    from alpaca.trading.enums import AssetClass, AssetStatus
    from alpaca.trading.requests import GetAssetsRequest

    now = now or datetime.now(timezone.utc)
    folder = Path(home) / "shortterm"
    client = StockHistoricalDataClient(key, secret, raw_data=True)
    universe_path = folder / "universe_top300.json"
    universe = json.loads(universe_path.read_text())
    month = f"{now.year:04d}-{now.month:02d}"
    report = {"month": month}
    if month not in universe:
        trading = TradingClient(key, secret, paper=True, raw_data=True)
        assets = []
        for status in (AssetStatus.ACTIVE, AssetStatus.INACTIVE):
            assets += trading.get_all_assets(GetAssetsRequest(status=status, asset_class=AssetClass.US_EQUITY))
        monthly = D.fetch_bars(client, D.candidates(assets), TimeFrame(1, TimeFrameUnit.Month),
                               _months_back(now, 1), now - timedelta(minutes=16))
        fresh = D.monthly_universe(monthly)
        if month in fresh:
            universe[month] = fresh[month]
            D.save(universe, home, "universe_top300", {"what": "top 300 by prior-month dollar volume, price >= $5",
                                                        "updated_month": month})
        report["universe_added"] = month in universe
    previous = _months_back(now, 1)
    names = sorted(set(universe.get(month, [])) | set(universe.get(f"{previous.year:04d}-{previous.month:02d}", [])))
    sic_path = folder / "sic.json"
    sic = json.loads(sic_path.read_text())
    missing = [s for s in names if s not in sic]
    if missing and os.environ.get("JARVIS_SEC_USER_AGENT"):
        from ..edgar import SUBMISSIONS_URL, EdgarClient, ticker_map

        edgar = EdgarClient(os.environ["JARVIS_SEC_USER_AGENT"])
        ciks = ticker_map(edgar)
        for s in missing:
            cik = ciks.get(s)
            code = str(edgar.get_json(SUBMISSIONS_URL.format(name=f"CIK{cik:010d}.json")).get("sic") or "") if cik else ""
            sic[s] = {"sic": code or None, "group": code[:2] if code else "UNKNOWN"}
        D.save(sic, home, "sic", {"what": "SEC SIC codes; delisted or unmatched -> UNKNOWN"})
    report["sic_added"] = len([s for s in missing if s in sic])
    start = now - timedelta(days=LOOKBACK_DAYS)
    # Completed sessions only: the desks run in the morning, so today's bar would be a partial session.
    from ..timeframes import NEW_YORK

    end = datetime.combine(now.astimezone(NEW_YORK).date(), datetime.min.time(), tzinfo=NEW_YORK).astimezone(timezone.utc)
    for adjustment, name in (("all", "live_daily_adjusted"), ("raw", "live_daily_raw")):
        bars = D.fetch_bars(client, names, TimeFrame.Day, start, end, adjustment=adjustment)
        bars = bars[bars["timestamp"] < end]  # the vendor's end bound is inclusive; today's bar starts at it
        D.save(bars, home, name, {"what": f"daily SIP bars ({adjustment}) for the live stock book", "symbols": len(names)})
        report[name] = {"rows": len(bars), "last": str(bars["timestamp"].max()) if len(bars) else None}
    return report

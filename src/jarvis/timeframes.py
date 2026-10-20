"""Bar timeframes: how a vendor timestamp maps to a bar's real time window, and the runner settings per timeframe."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from .contracts import AssetClass, require_utc

NEW_YORK = ZoneInfo("America/New_York")
TIMEFRAMES = ("1Hour", "1Day")
STEP = {"1Hour": timedelta(hours=1), "1Day": timedelta(days=1)}
SESSION_OPEN, SESSION_CLOSE = time(9, 30), time(16, 0)


def bar_window(asset_class: AssetClass, timeframe: str, timestamp: datetime) -> tuple[datetime, datetime]:
    """Start and end of the period a bar covers.

    Alpaca stamps a daily stock bar at midnight New York time, but the trading it summarises happens 09:30-16:00.
    Using the session times means the bar is known only after the close and an order placed at the next open is
    filled at that open, not at a price from before the decision. Early-close days are treated as closing at 16:00,
    which can only make the bar look available later than it was.
    """
    start = require_utc(timestamp)
    if timeframe == "1Day" and asset_class == AssetClass.EQUITY:
        day = start.astimezone(NEW_YORK).date()
        return (datetime.combine(day, SESSION_OPEN, tzinfo=NEW_YORK).astimezone(timezone.utc),
                datetime.combine(day, SESSION_CLOSE, tzinfo=NEW_YORK).astimezone(timezone.utc))
    return start, start + STEP[timeframe]


@dataclass(frozen=True)
class RunnerSettings:
    lookback: timedelta        # history requested each cycle (enough for the 20-bar features)
    max_bar_age: timedelta     # newer than this or the asset is blocked as stale
    feature_horizon: timedelta  # how long a snapshot stays usable for decisions


SETTINGS = {
    ("1Hour", AssetClass.EQUITY): RunnerSettings(timedelta(days=30), timedelta(hours=2), timedelta(hours=1)),
    ("1Hour", AssetClass.CRYPTO): RunnerSettings(timedelta(hours=72), timedelta(hours=2), timedelta(hours=1)),
    # Daily stock bars: a Friday close must still count on Tuesday after a Monday holiday.
    ("1Day", AssetClass.EQUITY): RunnerSettings(timedelta(days=60), timedelta(days=4), timedelta(days=4)),
    ("1Day", AssetClass.CRYPTO): RunnerSettings(timedelta(days=40), timedelta(days=2), timedelta(days=2)),
}


def settings(timeframe: str, asset_class: AssetClass) -> RunnerSettings:
    if timeframe not in TIMEFRAMES:
        raise ValueError(f"unsupported timeframe {timeframe}")
    return SETTINGS[(timeframe, asset_class)]

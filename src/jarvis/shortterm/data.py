"""Survivorship-aware liquid stock universe and bar downloads for the short-horizon lane.

Why: a list of today's popular stocks only contains companies that survived. For a strategy that buys after a fall
that bias is severe (it would only ever buy losers that recovered). So:
1. candidates = every US stock Alpaca lists, active **and** inactive (delisted), on NYSE, NASDAQ or AMEX (OTC and
   the ETF venues ARCA/BATS excluded; names that look like funds are dropped), plus ``KNOWN_FAILURES``: large,
   heavily traded companies that went bankrupt or were delisted 2016-2026 and are missing from Alpaca's asset list
   (RECALLED list, each checked against Alpaca's price data; their data is cut at ``until`` because some tickers
   were later reused by other companies);
2. monthly bars for every candidate give each month's dollar volume;
3. the universe for month M is the ``N`` highest dollar-volume stocks of month M - 1 with a last price of at least
   ``MIN_PRICE`` (known before month M starts, so no look-ahead);
4. daily bars are downloaded for every stock that is ever in the universe.

Residual bias (stated, not hidden): a failed company missing from both Alpaca's asset list and ``KNOWN_FAILURES``
is missing from the research. That favours strategies that buy losers, so reversal results are stress-tested
separately.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

LISTED_EXCHANGES = {"NYSE", "NASDAQ", "AMEX"}
FUND_WORDS = (" etf", " etn", " fund", " trust", "proshares", "direxion", "ishares", "spdr", "invesco", "vanguard",
              " index", "leveraged", " 2x", " 3x", "ultra", "bull ", "bear ", "notes due", "warrant", " rights",
              " units", "preferred", " depositary shares representing", "acquisition corp")
# (symbol, last date to use): bankruptcies / forced delistings of large, actively traded companies (RECALLED).
KNOWN_FAILURES = (("SIVB", date(2023, 3, 9)), ("FRC", date(2023, 4, 28)), ("SBNY", date(2023, 3, 10)),
                  ("BBBY", date(2023, 4, 21)), ("SI", date(2023, 3, 31)), ("LK", date(2020, 6, 26)),
                  ("JCP", date(2020, 5, 15)), ("HTZ", date(2020, 10, 29)), ("CHK", date(2020, 6, 26)),
                  ("WLL", date(2020, 3, 31)), ("FTR", date(2020, 4, 14)), ("WE", date(2023, 11, 6)),
                  ("RAD", date(2023, 10, 13)), ("YELL", date(2023, 8, 4)), ("REV", date(2022, 6, 15)),
                  ("GNC", date(2020, 6, 23)), ("DO", date(2020, 4, 24)), ("NE", date(2020, 7, 31)),
                  ("VAL", date(2020, 8, 18)), ("CBL", date(2020, 11, 1)), ("PRTY", date(2023, 1, 17)),
                  ("TUP", date(2024, 9, 17)), ("SPCE", date(2100, 1, 1)), ("NKLA", date(2025, 2, 19)),
                  ("FSR", date(2024, 3, 25)), ("GOEV", date(2025, 1, 31)))
MIN_PRICE, UNIVERSE_SIZE = 5.0, 300
TICKER = re.compile(r"^[A-Z]{1,5}$")  # inactive listings also carry placeholder codes such as '0029900E0'
CHUNK = 100  # symbols per request


def looks_like_fund(name: str) -> bool:
    n = f" {name.lower()} "
    return any(w in n for w in FUND_WORDS)


def candidates(assets: list[dict]) -> list[str]:
    """Common-stock candidates from Alpaca's raw asset list (active and inactive)."""
    out = {a["symbol"] for a in assets if a.get("exchange") in LISTED_EXCHANGES and TICKER.match(a["symbol"])
           and not looks_like_fund(a.get("name") or "")}
    return sorted(out | {s for s, _ in KNOWN_FAILURES})


def fetch_bars(client, symbols: list[str], timeframe, start: datetime, end: datetime, *, adjustment: str = "raw",
               pause: float = 0.35) -> pd.DataFrame:
    """Long table (symbol, timestamp, open, high, low, close, volume, vwap, trades) from a raw-data Alpaca client."""
    from alpaca.data.enums import Adjustment, DataFeed
    from alpaca.data.requests import StockBarsRequest

    frames, skipped = [], []

    def request(part):
        req = StockBarsRequest(symbol_or_symbols=part, timeframe=timeframe, start=start, end=end,
                               adjustment=Adjustment(adjustment), feed=DataFeed.SIP)
        for attempt in range(3):
            try:
                return client.get_stock_bars(req)
            except Exception as exc:  # rate limit or transient error: back off; a bad symbol fails every time
                error = exc
                time.sleep(3 * (attempt + 1))
        if len(part) == 1:
            skipped.append((part[0], type(error).__name__))
            return {}
        half = len(part) // 2  # find the bad symbol by splitting the request
        return {**(request(part[:half]) or {}), **(request(part[half:]) or {})}

    for i in range(0, len(symbols), CHUNK):
        part = symbols[i:i + CHUNK]
        data = request(part)
        rows = [{"symbol": s, "timestamp": b["t"], "open": b["o"], "high": b["h"], "low": b["l"], "close": b["c"],
                 "volume": b["v"], "vwap": b.get("vw"), "trades": b.get("n")}
                for s, bars in (data or {}).items() for b in bars]
        if rows:
            frames.append(pd.DataFrame(rows))
        time.sleep(pause)
    if skipped:
        print(f"skipped {len(skipped)} symbols the data API refused: {skipped[:10]}", flush=True)
    if not frames:
        return pd.DataFrame(columns=["symbol", "timestamp", "open", "high", "low", "close", "volume", "vwap", "trades"])
    df = pd.concat(frames, ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    cut = dict(KNOWN_FAILURES)
    if cut:
        last = df["symbol"].map(lambda s: cut.get(s, date(2100, 1, 1)))
        df = df[df["timestamp"].dt.date <= last]
    return df.sort_values(["symbol", "timestamp"]).reset_index(drop=True)


def monthly_universe(monthly: pd.DataFrame, n: int = UNIVERSE_SIZE, min_price: float = MIN_PRICE) -> dict[str, list[str]]:
    """{'YYYY-MM': symbols} for each month M: the n highest dollar-volume stocks of month M - 1 (price >= min)."""
    m = monthly.copy()
    m["month"] = m["timestamp"].dt.tz_convert("America/New_York").dt.strftime("%Y-%m")
    m["dollar_volume"] = m["volume"] * m["vwap"].fillna(m["close"])
    out = {}
    months = sorted(m["month"].unique())
    for prev, cur in zip(months, months[1:]):
        rows = m[(m["month"] == prev) & (m["close"] >= min_price)]
        out[cur] = rows.nlargest(n, "dollar_volume")["symbol"].tolist()
    return out


def save(df: pd.DataFrame | dict, home: Path, name: str, meta: dict) -> Path:
    """Write a Parquet (or JSON for dicts) file under JARVIS_HOME/shortterm with a SHA-256 manifest."""
    folder = Path(home) / "shortterm"
    folder.mkdir(parents=True, exist_ok=True)
    if isinstance(df, dict):
        path = folder / f"{name}.json"
        path.write_text(json.dumps(df, indent=0))
    else:
        path = folder / f"{name}.parquet"
        df.to_parquet(path, index=False)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (folder / f"{name}.manifest.json").write_text(json.dumps({**meta, "file": path.name, "sha256": digest,
                                                             "written_at": datetime.now(timezone.utc).isoformat()}, indent=2))
    return path

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

Adjusted bars are checked against raw bars and cleaned when loaded (``clean_adjusted``,
docs/10-shortterm/DATA_CLEANING.md): Alpaca sometimes adjusts a spin-off, rights issue or merger as if it were a
reverse split, which puts a jump of up to -99% into the adjusted history while the raw prices are sensible.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
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
# Adjustment check: a day is flagged when the adjusted and raw close-to-close returns differ by more than
# ADJUSTMENT_GAP and the raw close ratio is not within SPLIT_TOLERANCE (relative) of a common split ratio.
SPLIT_RATIOS = (1 / 2, 1 / 3, 2 / 3, 1 / 4, 1 / 5, 1 / 10, 2, 3, 4, 5, 10)
SPLIT_TOLERANCE, ADJUSTMENT_GAP = 0.03, 0.15
PRICE_COLUMNS = ("open", "high", "low", "close", "vwap")


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

    returned: set[str] = set()

    def add(data):
        rows = [{"symbol": s, "timestamp": b["t"], "open": b["o"], "high": b["h"], "low": b["l"], "close": b["c"],
                 "volume": b["v"], "vwap": b.get("vw"), "trades": b.get("n")}
                for s, bars in (data or {}).items() for b in bars]
        returned.update(s for s, bars in (data or {}).items() if bars)
        if rows:
            frames.append(pd.DataFrame(rows))

    for i in range(0, len(symbols), CHUNK):
        add(request(symbols[i:i + CHUNK]))
        time.sleep(pause)
    # The data API can leave a symbol out of a long multi-page answer without any error (DOW, 2026-10-22: missing
    # from a 100-symbol daily request, complete when asked with a few others), so the symbols that came back empty
    # are asked for once more, together; a symbol with no bars in the window simply stays empty.
    refused = {s for s, _ in skipped}
    empty = [s for s in symbols if s not in returned and s not in refused]
    before = set(returned)
    for i in range(0, len(empty), CHUNK):
        add(request(empty[i:i + CHUNK]))
        time.sleep(pause)
    if returned - before:
        print(f"recovered {len(returned - before)} symbols missing from the first answer: "
              f"{sorted(returned - before)[:10]}", flush=True)
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


def split_like(ratio) -> np.ndarray:
    """True where a raw close-to-close ratio is within SPLIT_TOLERANCE (relative) of a common split ratio."""
    r = np.asarray(ratio, dtype=float)[..., None]
    with np.errstate(invalid="ignore"):
        return (np.abs(r / np.asarray(SPLIT_RATIOS) - 1) <= SPLIT_TOLERANCE).any(axis=-1)


def adjustment_flags(adjusted: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    """Symbol-days whose adjusted close-to-close return differs from the raw one by more than ADJUSTMENT_GAP while
    the raw close ratio is not a split ratio: symbol, timestamp, previous (the bar before), r_adj, r_raw, spurious,
    price_step, volume_step.

    ``spurious``: the adjusted move is the larger one (in log terms), so the vendor's adjustment made the jump.
    Otherwise the adjustment removed a raw jump and is kept: a split ratio outside the list (20:1, 50:1, 1:15 ...),
    a listed split on a day the stock also moved more than 3%, or a large distribution adjusted correctly.
    ``price_step`` / ``volume_step``: the change of the vendor's factor (adjusted / raw) from the bar before to this
    one, for prices and volume (1 where the volume factor is unknown, e.g. a zero-volume bar)."""
    cols = ["symbol", "timestamp", "close", "volume"]
    m = adjusted[cols].merge(raw[cols], on=["symbol", "timestamp"], suffixes=("_adj", "_raw"))
    m = m.sort_values(["symbol", "timestamp"], kind="stable").reset_index(drop=True)
    g = m.groupby("symbol", sort=False)
    r_adj = m["close_adj"] / g["close_adj"].shift() - 1
    ratio = m["close_raw"] / g["close_raw"].shift()
    factor = (m["volume_adj"] / m["volume_raw"].where(m["volume_raw"] > 0)).groupby(m["symbol"], sort=False)
    known_before = factor.ffill().groupby(m["symbol"], sort=False).shift()  # last known factor before this bar
    volume_step = (factor.bfill() / known_before).where(lambda x: np.isfinite(x) & (x > 0), 1.0)
    hit = ((r_adj - (ratio - 1)).abs() > ADJUSTMENT_GAP) & ~split_like(ratio)
    with np.errstate(divide="ignore", invalid="ignore"):
        spurious = np.abs(np.log1p(r_adj)) > np.abs(np.log(ratio))
    out = pd.DataFrame({"symbol": m["symbol"], "timestamp": m["timestamp"], "previous": g["timestamp"].shift(),
                        "r_adj": r_adj, "r_raw": ratio - 1, "spurious": spurious, "price_step": (1 + r_adj) / ratio,
                        "volume_step": volume_step})
    return out[hit.to_numpy()].reset_index(drop=True)


def clean_adjusted(adjusted: pd.DataFrame, raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The cleaning rule (docs/10-shortterm/DATA_CLEANING.md). On each spurious day the vendor's factor change is
    undone: that symbol's earlier adjusted prices are multiplied by ``price_step`` (and its earlier volumes by
    ``volume_step``), so the day's adjusted return equals the raw return and the history before it lines up with
    the prices after it. Every other adjustment (dividends, real splits) is kept. Returns (adjusted, flags); the
    input is returned unchanged when nothing is spurious."""
    flags = adjustment_flags(adjusted, raw)
    fix = flags[flags["spurious"]]
    if fix.empty:
        return adjusted, flags
    out = adjusted.copy()
    price, volume = np.ones(len(out)), np.ones(len(out))
    rows = out.groupby("symbol", sort=False).indices
    for f in fix.itertuples():
        idx = rows[f.symbol]
        earlier = idx[(out["timestamp"].iloc[idx] < f.timestamp).to_numpy()]
        price[earlier] *= f.price_step
        volume[earlier] *= f.volume_step
    for c in PRICE_COLUMNS:
        if c in out:
            out[c] = out[c] * price
    out["volume"] = np.rint(out["volume"].to_numpy(dtype=float) * volume).astype(out["volume"].dtype)
    return out, flags


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

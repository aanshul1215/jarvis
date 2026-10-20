"""Information collectors (Phase 6): archive news, Reddit posts and crypto sentiment with honest timestamps.

Sentiment can only be tested on history we hold, so collection starts before any sentiment model exists. Every item
records two times: ``published_at`` (what the source says) and ``available_at`` (the earliest moment a backtest may
use it). Nothing here places orders or feeds the order path directly.

Sources (owner decision 2026-10-20):
- **Alpaca news** (Benzinga headlines for the universe; history from 2015): ``available_at`` is the article's
  creation time plus one minute. If the article was updated more than ten minutes after creation, today's headline
  may not be the one first published, so ``available_at`` becomes the update time (conservative).
- **Reddit** (chosen subreddits, newest posts): history beyond the latest posts is not available through the API, so
  the archive grows forward only. ``available_at`` is when this collector first saw the post. Author names are stored
  only as a salted hash. Requires the owner's Reddit app credentials and acceptance of Reddit's API terms.
- **Crypto Fear & Greed index** (alternative.me, daily since 2018): the value stamped for day D is treated as known
  from D + 1 day, 00:00 UTC (conservative; the publisher updates around the day change).

Archives live in ``JARVIS_HOME/information/<source>/<YYYY-MM>.parquet``, de-duplicated by item id; the first
observation of an item is never overwritten.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable

from .contracts import AssetClass, LedgerEvent, iso, new_id, parse_utc, utc_now
from .history import UniverseAsset
from .storage import LocalStorage

UTC = timezone.utc
NEWS_DELAY, NEWS_REVISION = timedelta(minutes=1), timedelta(minutes=10)
SUBREDDITS = ("wallstreetbets", "stocks", "investing", "StockMarket", "CryptoCurrency", "Bitcoin", "ethereum")
REDDIT_TEXT_LIMIT = 2_000
CRYPTO_WORDS = {"BTC/USD": ("bitcoin", "btc"), "ETH/USD": ("ethereum", "eth", "ether")}
FEAR_GREED_URL = "https://api.alternative.me/fng/?limit={limit}&format=json"


# --- archive -------------------------------------------------------------------------------------------------------

def _month(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m")


def archive(store: LocalStorage, source: str, items: Iterable[dict]) -> dict:
    """Add items to the monthly archive. An item already archived keeps its first observation."""
    by_month: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        by_month[_month(parse_utc(item["published_at"]))].append(item)
    added = 0
    for month, rows in by_month.items():
        existing = store.read_table("information", source, month)
        seen = {r["item_id"] for r in existing}
        new = []
        for row in rows:
            if row["item_id"] not in seen:
                seen.add(row["item_id"])
                new.append(row)
        if new:
            store.write_table("information", source, month,
                              rows=sorted(existing + new, key=lambda r: (r["published_at"], r["item_id"])))
            added += len(new)
    return {"received": sum(len(v) for v in by_month.values()), "added": added, "months": len(by_month)}


def load_items(store: LocalStorage, source: str, *, start: datetime, end: datetime,
               as_of: datetime | None = None) -> list[dict]:
    """Archived items published in [start, end) and available at ``as_of`` (default ``end``)."""
    as_of = as_of or end
    out, month = [], datetime(start.year, start.month, 1, tzinfo=UTC)
    while month < end:
        for row in store.read_table("information", source, month.strftime("%Y-%m")):
            if start <= parse_utc(row["published_at"]) < end and parse_utc(row["available_at"]) <= as_of:
                out.append(row)
        month = datetime(month.year + month.month // 12, month.month % 12 + 1, 1, tzinfo=UTC)
    return sorted(out, key=lambda r: (r["available_at"], r["item_id"]))


# --- Alpaca news ---------------------------------------------------------------------------------------------------

def news_symbol(asset: UniverseAsset) -> str:
    return asset.symbol.replace("/", "") if asset.asset_class == AssetClass.CRYPTO else asset.symbol


def news_rows(articles: Iterable, universe: list[UniverseAsset], collected_at: datetime) -> list[dict]:
    """Normalise Alpaca news objects (or dicts) to archive rows, keeping only universe symbols."""
    lookup = {news_symbol(a): a.symbol for a in universe}
    rows = []
    for article in articles:
        a = article if isinstance(article, dict) else article.model_dump()
        created = a["created_at"] if isinstance(a["created_at"], datetime) else parse_utc(str(a["created_at"]))
        updated = a.get("updated_at") or created
        updated = updated if isinstance(updated, datetime) else parse_utc(str(updated))
        created, updated = created.astimezone(UTC), updated.astimezone(UTC)
        revised = updated - created > NEWS_REVISION
        symbols = sorted({lookup[s] for s in (a.get("symbols") or []) if s in lookup})
        if not symbols:
            continue
        rows.append({"item_id": f"alpaca-news-{a['id']}", "source": "alpaca_news", "published_at": iso(created),
                     "available_at": iso(updated if revised else created + NEWS_DELAY),
                     "first_seen_at": iso(collected_at), "revised_after_publication": revised,
                     "symbols": ",".join(symbols), "title": a.get("headline") or "",
                     "text": (a.get("summary") or "")[:REDDIT_TEXT_LIMIT], "author": a.get("author") or "",
                     "url": a.get("url") or "", "provider": a.get("source") or "benzinga"})
    return rows


def collect_news(store: LocalStorage, client, universe: list[UniverseAsset], *, start: datetime, end: datetime,
                 now: Callable[[], datetime] = utc_now) -> dict:
    """Download news month by month (the SDK pages within each request) and archive it."""
    from alpaca.data.requests import NewsRequest

    symbols = ",".join(news_symbol(a) for a in universe)
    report = {"received": 0, "added": 0, "months": 0}
    month = datetime(start.year, start.month, 1, tzinfo=UTC)
    while month < end:
        following = datetime(month.year + month.month // 12, month.month % 12 + 1, 1, tzinfo=UTC)
        window_start, window_end = max(month, start), min(following, end)
        response = client.get_news(NewsRequest(symbols=symbols, start=window_start, end=window_end, sort="asc",
                                               include_content=False, limit=None))
        articles = response.data.get("news", []) if hasattr(response, "data") else response
        result = archive(store, "alpaca_news", news_rows(articles, universe, now()))
        for key in report:
            report[key] += result[key]
        month = following
    return report


# --- Reddit --------------------------------------------------------------------------------------------------------

def mentions(text: str, universe: list[UniverseAsset]) -> list[str]:
    """Universe assets a post mentions: '$AAPL' or the bare ticker in capitals, and crypto names."""
    found = set()
    for asset in universe:
        if asset.asset_class == AssetClass.CRYPTO:
            words = CRYPTO_WORDS.get(asset.symbol, ())
            if any(re.search(rf"(?<![A-Za-z]){w}(?![A-Za-z])", text, re.IGNORECASE) for w in words):
                found.add(asset.symbol)
        elif re.search(rf"(?<![A-Za-z$])\$?{re.escape(asset.symbol)}(?![A-Za-z])", text):
            found.add(asset.symbol)
    return sorted(found)


class RedditClient:
    """Application-only OAuth client for reading public subreddits (no user login, read-only)."""

    TOKEN_URL = "https://www.reddit.com/api/v1/access_token"

    def __init__(self, client_id: str, client_secret: str, user_agent: str, *, fetch=None):
        if not re.match(r"^[^:]+:[^:]+:[^ ]+ \(by /u/[A-Za-z0-9_-]+\)$", user_agent):
            raise ValueError("Reddit asks for a User-Agent like 'windows:jarvis-research:0.1 (by /u/yourname)'")
        self.client_id, self.client_secret, self.user_agent = client_id, client_secret, user_agent
        self.fetch = fetch or self._http
        self._token, self._expires = None, 0.0

    def _http(self, request: urllib.request.Request) -> bytes:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed https hosts
            return response.read()

    def _authorise(self) -> str:
        if self._token and time.time() < self._expires - 60:
            return self._token
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        request = urllib.request.Request(self.TOKEN_URL, data=b"grant_type=client_credentials", method="POST",
                                         headers={"Authorization": f"Basic {auth}", "User-Agent": self.user_agent})
        payload = json.loads(self.fetch(request))
        if "access_token" not in payload:
            raise PermissionError(f"Reddit refused the credentials: {payload.get('error', 'unknown error')}")
        self._token, self._expires = payload["access_token"], time.time() + float(payload.get("expires_in", 3600))
        return self._token

    def newest(self, subreddit: str, limit: int = 100) -> list[dict]:
        query = urllib.parse.urlencode({"limit": limit, "raw_json": 1})
        request = urllib.request.Request(f"https://oauth.reddit.com/r/{subreddit}/new?{query}",
                                         headers={"Authorization": f"bearer {self._authorise()}",
                                                  "User-Agent": self.user_agent})
        listing = json.loads(self.fetch(request))
        return [child["data"] for child in listing.get("data", {}).get("children", [])]


def reddit_rows(posts: Iterable[dict], universe: list[UniverseAsset], seen_at: datetime, salt: str) -> list[dict]:
    rows = []
    for post in posts:
        text = f"{post.get('title', '')}\n{post.get('selftext', '')}"
        created = datetime.fromtimestamp(float(post["created_utc"]), tz=UTC)
        author = post.get("author") or ""
        rows.append({"item_id": f"reddit-{post['id']}", "source": "reddit", "published_at": iso(created),
                     "available_at": iso(max(seen_at, created)), "first_seen_at": iso(seen_at),
                     "revised_after_publication": False, "symbols": ",".join(mentions(text, universe)),
                     "title": post.get("title", ""), "text": (post.get("selftext") or "")[:REDDIT_TEXT_LIMIT],
                     "author": hashlib.sha256(f"{salt}:{author}".encode()).hexdigest()[:16] if author else "",
                     "url": f"https://www.reddit.com{post.get('permalink', '')}", "provider": f"r/{post.get('subreddit', '')}",
                     "score_at_first_seen": int(post.get("score") or 0),
                     "comments_at_first_seen": int(post.get("num_comments") or 0)})
    return rows


def collect_reddit(store: LocalStorage, client: RedditClient, universe: list[UniverseAsset], *, salt: str,
                   subreddits: tuple[str, ...] = SUBREDDITS, now: Callable[[], datetime] = utc_now) -> dict:
    report = {"received": 0, "added": 0, "months": 0, "by_subreddit": {}}
    for subreddit in subreddits:
        rows = reddit_rows(client.newest(subreddit), universe, now(), salt)
        result = archive(store, "reddit", rows)
        report["by_subreddit"][subreddit] = result["added"]
        for key in ("received", "added", "months"):
            report[key] += result[key]
        time.sleep(1)  # far inside Reddit's published limit; be a polite client
    return report


# --- Crypto Fear & Greed -------------------------------------------------------------------------------------------

def fear_greed_rows(payload: dict, seen_at: datetime) -> list[dict]:
    rows = []
    for point in payload.get("data", []):
        day = datetime.fromtimestamp(int(point["timestamp"]), tz=UTC)
        rows.append({"item_id": f"fng-{day.date().isoformat()}", "source": "fear_greed", "published_at": iso(day),
                     "available_at": iso(day + timedelta(days=1)), "first_seen_at": iso(seen_at),
                     "revised_after_publication": False, "symbols": "BTC/USD,ETH/USD",
                     "title": point.get("value_classification", ""), "text": "", "author": "", "url": FEAR_GREED_URL,
                     "provider": "alternative.me", "value": int(point["value"])})
    return rows


def collect_fear_greed(store: LocalStorage, *, history: bool = False, fetch=None,
                       now: Callable[[], datetime] = utc_now) -> dict:
    def http(url: str) -> bytes:
        with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310 - fixed https URL
            return response.read()

    payload = json.loads((fetch or http)(FEAR_GREED_URL.format(limit=0 if history else 10)))
    return archive(store, "fear_greed", fear_greed_rows(payload, now()))


def record_collection(store: LocalStorage, report: dict) -> None:
    store.append_event(LedgerEvent(new_id("evt"), "INFORMATION_COLLECTION", utc_now(), new_id("collect"),
                                   source_id="COLLECTORS", payload=report))

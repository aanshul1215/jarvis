"""Phase 6 collectors: honest availability times, first observation kept, ticker matching, no network in tests."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from jarvis import collectors
from jarvis.contracts import AssetClass
from jarvis.history import UniverseAsset
from jarvis.storage import LocalStorage

UTC = timezone.utc
UNIVERSE = [UniverseAsset("AAPL", AssetClass.EQUITY), UniverseAsset("SPY", AssetClass.EQUITY),
            UniverseAsset("BTC/USD", AssetClass.CRYPTO)]
NOW = datetime(2026, 10, 20, 15, tzinfo=UTC)


def article(i, created, updated=None, symbols=("AAPL",)):
    return {"id": i, "headline": f"headline {i}", "summary": "s", "author": "Benzinga", "source": "benzinga",
            "url": f"https://example.test/{i}", "symbols": list(symbols), "created_at": created,
            "updated_at": updated or created}


def test_news_availability_is_conservative_for_revised_articles():
    t = datetime(2020, 3, 2, 14, 30, tzinfo=UTC)
    rows = collectors.news_rows([article(1, t), article(2, t, t + timedelta(hours=3)),
                                 article(3, t, symbols=("XYZ",)), article(4, t, symbols=("BTCUSD", "AAPL"))],
                                UNIVERSE, NOW)
    by_id = {r["item_id"]: r for r in rows}
    assert by_id["alpaca-news-1"]["available_at"] == "2020-03-02T14:31:00Z"          # creation + 1 minute
    assert by_id["alpaca-news-2"]["available_at"] == "2020-03-02T17:30:00Z"          # edited later: update time
    assert by_id["alpaca-news-2"]["revised_after_publication"]
    assert "alpaca-news-3" not in by_id                                               # no universe symbol
    assert by_id["alpaca-news-4"]["symbols"] == "AAPL,BTC/USD"


def test_archive_keeps_the_first_observation_and_filters_by_availability(tmp_path):
    t = datetime(2020, 3, 2, 14, 30, tzinfo=UTC)
    with LocalStorage(tmp_path / "home") as store:
        first = collectors.news_rows([article(1, t)], UNIVERSE, NOW)
        assert collectors.archive(store, "alpaca_news", first)["added"] == 1
        later = [dict(first[0], title="changed", first_seen_at="2027-01-01T00:00:00Z")]
        assert collectors.archive(store, "alpaca_news", later)["added"] == 0
        rows = collectors.load_items(store, "alpaca_news", start=t - timedelta(days=1), end=t + timedelta(days=40))
        assert [r["title"] for r in rows] == ["headline 1"]
        early = collectors.load_items(store, "alpaca_news", start=t - timedelta(days=1), end=t + timedelta(days=1),
                                      as_of=t + timedelta(seconds=30))
        assert early == []                                                            # not yet available


def test_ticker_mentions_need_capitals_or_a_dollar_sign():
    assert collectors.mentions("Bought $AAPL and some SPY calls", UNIVERSE) == ["AAPL", "SPY"]
    assert collectors.mentions("I spy an apple; aapl lowercase", UNIVERSE) == []
    assert collectors.mentions("Bitcoin to the moon, BTC halving", UNIVERSE) == ["BTC/USD"]
    assert collectors.mentions("SPYDER is not SPY", UNIVERSE) == ["SPY"]


class FakeReddit:
    def __init__(self):
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        if request.full_url.endswith("access_token"):
            return json.dumps({"access_token": "t", "expires_in": 3600}).encode()
        post = {"id": "abc", "title": "$AAPL earnings play", "selftext": "long", "author": "someone",
                "created_utc": 1792500000, "score": 12, "num_comments": 3, "permalink": "/r/stocks/abc",
                "subreddit": "stocks"}
        return json.dumps({"data": {"children": [{"data": post}]}}).encode()


def test_reddit_collector_is_read_only_hashes_authors_and_uses_first_seen_time(tmp_path, monkeypatch):
    monkeypatch.setattr(collectors.time, "sleep", lambda s: None)
    fake = FakeReddit()
    with pytest.raises(ValueError, match="User-Agent"):
        collectors.RedditClient("id", "secret", "jarvis", fetch=fake)
    client = collectors.RedditClient("id", "secret", "windows:jarvis-research:0.1 (by /u/someone)", fetch=fake)
    with LocalStorage(tmp_path / "home") as store:
        report = collectors.collect_reddit(store, client, UNIVERSE, salt="pepper", subreddits=("stocks",),
                                           now=lambda: NOW)
        row = store.read_table("information", "reddit", "2026-10")[0]
    assert report["added"] == 1 and row["symbols"] == "AAPL"
    assert row["available_at"] == "2026-10-20T15:00:00Z"                              # when we saw it
    assert row["author"] != "someone" and len(row["author"]) == 16                    # never the username
    assert all(r.get_method() in ("GET", "POST") for r in fake.requests)
    assert fake.requests[0].data == b"grant_type=client_credentials"                  # app-only token, no login


def test_fear_greed_is_known_only_the_next_day(tmp_path):
    payload = {"data": [{"value": "55", "value_classification": "Greed", "timestamp": "1792454400"}]}
    with LocalStorage(tmp_path / "home") as store:
        collectors.collect_fear_greed(store, fetch=lambda url: json.dumps(payload).encode(), now=lambda: NOW)
        row = store.read_table("information", "fear_greed", "2026-10")[0]
    assert row["published_at"] == "2026-10-20T00:00:00Z" and row["available_at"] == "2026-10-21T00:00:00Z"
    assert row["value"] == 55


class FakeBluesky:
    def __init__(self):
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        if request.full_url.endswith("createSession"):
            return json.dumps({"accessJwt": "jwt", "did": "did:plc:me"}).encode()
        post = {"uri": "at://did:plc:abc/app.bsky.feed.post/1", "cid": "bafy1", "author": {"did": "did:plc:abc", "handle": "x.bsky.social"},
                "record": {"text": "Loading up on $AAPL and some bitcoin", "createdAt": "2026-10-20T14:00:00Z"},
                "indexedAt": "2026-10-20T14:00:05Z", "likeCount": 4, "replyCount": 1}
        return json.dumps({"posts": [post]}).encode()


def test_bluesky_collector_signs_in_with_an_app_password_and_archives_once(tmp_path, monkeypatch):
    monkeypatch.setattr(collectors.time, "sleep", lambda s: None)
    fake = FakeBluesky()
    client = collectors.BlueskyClient("me.bsky.social", "app-pass", fetch=fake)
    assert collectors.bluesky_queries(UNIVERSE) == {"$AAPL": "AAPL", "$SPY": "SPY", "$BTC": "BTC/USD", "bitcoin": "BTC/USD"}
    with LocalStorage(tmp_path / "home") as store:
        report = collectors.collect_bluesky(store, client, UNIVERSE, salt="pepper", now=lambda: NOW)
        rows = store.read_table("information", "bluesky", "2026-10")
    assert report["received"] == 4 and report["added"] == 1                 # the same post found by four searches
    loose = {"cid": "c2", "record": {"text": "Meta announced something; un bon dia"}, "indexedAt": "2026-10-20T14:00:00Z",
             "author": {"did": "d"}}
    assert collectors.bluesky_rows([loose], UNIVERSE + [UniverseAsset("META", AssetClass.EQUITY)], "META", NOW, "s") == []
    row = rows[0]
    assert row["symbols"] == "AAPL,BTC/USD" and row["available_at"] == "2026-10-20T15:00:00Z"
    assert row["author"] != "did:plc:abc" and "x.bsky.social" not in json.dumps(row)
    sessions = [r for r in fake.requests if r.full_url.endswith("createSession")]
    assert len(sessions) == 1 and all(r.get_method() == "GET" for r in fake.requests if r not in sessions)

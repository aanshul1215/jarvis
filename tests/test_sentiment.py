"""Phase 6 sentiment: scores are stored once, features use only items available at the decision time, and the
news-sentiment strategy follows its pre-registered rule. A keyword stand-in replaces FinBERT (no model download)."""

from datetime import datetime, timedelta, timezone

import pytest

from jarvis import collectors
from jarvis.contracts import AssetClass, FeatureSnapshot
from jarvis.history import UniverseAsset
from jarvis.sentiment import SentimentIndex, score_archive
from jarvis.storage import LocalStorage
from jarvis.strategies import DecisionContext, NewsSentiment, OpenPosition, sentiment_specs

UTC = timezone.utc
UNIVERSE = [UniverseAsset("AAPL", AssetClass.EQUITY)]
START = datetime(2020, 1, 1, tzinfo=UTC)


class KeywordScorer:
    name, version = "finbert", "keyword-test"

    def __init__(self):
        self.calls = 0

    def score(self, texts):
        self.calls += len(texts)
        return [1.0 if "surge" in t else -1.0 if "plunge" in t else 0.0 for t in texts]


def headlines(store, spec):
    """spec: list of (hours after START, headline)."""
    articles = [{"id": i, "headline": h, "summary": "", "author": "", "source": "", "url": "", "symbols": ["AAPL"],
                 "created_at": START + timedelta(hours=t)} for i, (t, h) in enumerate(spec)]
    collectors.archive(store, "alpaca_news", collectors.news_rows(articles, UNIVERSE, START))


def test_scores_are_written_once_and_features_respect_availability(tmp_path):
    with LocalStorage(tmp_path / "h") as store:
        # 30 neutral-ish baseline headlines over 40 days, then three positive ones on day 45.
        headlines(store, [(24 * d, "quiet day" if d % 2 else "plunge") for d in range(30)] +
                  [(24 * 45 + h, "shares surge") for h in (1, 2, 3)])
        scorer = KeywordScorer()
        assert score_archive(store, "alpaca_news", scorer)["scored"] == 33
        assert score_archive(store, "alpaca_news", scorer)["scored"] == 0 and scorer.calls == 33  # never rescored
        index = SentimentIndex(store)
    burst = START + timedelta(days=45, hours=4)
    news = index("AAPL", burst)
    assert news["news_count_24h"] == 3 and news["news_sentiment_24h"] == 1.0 and news["news_sentiment_z"] > 2
    before = index("AAPL", START + timedelta(days=45, hours=1, seconds=59))       # 1st headline counts after +1 min
    assert before["news_count_24h"] == 0
    assert index("MSFT", burst) == {"news_count_24h": 0, "news_sentiment_24h": None, "news_sentiment_z": None}


def snap(at):
    return FeatureSnapshot("s", "AAPL", AssetClass.EQUITY, at, at, at + timedelta(days=1), (), {})


def test_news_sentiment_strategy_follows_the_registered_rule():
    strategy = NewsSentiment(sentiment_specs()[0])
    now = datetime(2024, 3, 6, 21, 15, tzinfo=UTC)
    cases = {"strong": {"news_count_24h": 4, "news_sentiment_24h": 0.6, "news_sentiment_z": 2.5},
             "few": {"news_count_24h": 2, "news_sentiment_24h": 0.9, "news_sentiment_z": 4.0},
             "mild": {"news_count_24h": 5, "news_sentiment_24h": 0.2, "news_sentiment_z": 1.2},
             "turned": {"news_count_24h": 5, "news_sentiment_24h": -0.7, "news_sentiment_z": -2.4}}
    seen = []

    def context(case):
        def information(asset, as_of):
            seen.append(as_of)
            return cases[case]
        return DecisionContext(now, {}, None, None, information)

    assert strategy.entry_score(snap(now), context("strong")) == pytest.approx(2.5)
    assert strategy.entry_score(snap(now), context("few")) is None                 # fewer than 3 headlines
    assert strategy.entry_score(snap(now), context("mild")) is None
    assert strategy.exit_reason(snap(now), OpenPosition("AAPL", 100, 1), context("turned")) == "SENTIMENT_TURNED"
    assert strategy.entry_score(snap(now), DecisionContext(now, {})) is None       # no information source
    assert set(seen) == {now}                                                      # always the decision time

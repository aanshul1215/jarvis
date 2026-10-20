"""Synthetic markets written through the real back-fill path. Not market evidence."""

import math
import random
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from jarvis.contracts import AssetClass
from jarvis.history import UniverseAsset, backfill

UTC = timezone.utc


class RandomWalkHistory:
    """Daily bars on a zero-drift random walk: no strategy has a real edge here."""

    def __init__(self, seed: int = 1, daily_vol: float = 0.012):
        self.seed, self.vol = seed, daily_vol

    def _serve(self, request):
        symbol = request.symbol_or_symbols
        start = request.start if request.start.tzinfo else request.start.replace(tzinfo=UTC)
        end = request.end if request.end.tzinfo else request.end.replace(tzinfo=UTC)
        rng = random.Random(f"{self.seed}:{symbol}")
        day, price, models = datetime(2015, 1, 1, 5, tzinfo=UTC), 100.0, []
        while day < end:
            if day.weekday() < 5:
                open_ = price * (1 + rng.gauss(0, self.vol / 3))
                close = open_ * (1 + rng.gauss(0, self.vol))
                high = max(open_, close) * (1 + abs(rng.gauss(0, self.vol / 2)))
                low = min(open_, close) * (1 - abs(rng.gauss(0, self.vol / 2)))
                volume = 1_000_000 * math.exp(rng.gauss(0, 0.5))
                if start <= day < end:
                    models.append(SimpleNamespace(timestamp=day, open=open_, high=high, low=low, close=close,
                                                  volume=volume))
                price = close
            day += timedelta(days=1)
        return SimpleNamespace(data={symbol: models})

    get_stock_bars = _serve
    get_crypto_bars = _serve


SYMBOLS = ("AAA", "BBB", "CCC", "DDD")


def build_market(store, *, seed=1, start=datetime(2016, 1, 1, tzinfo=UTC), end=datetime(2018, 7, 1, tzinfo=UTC)):
    client = RandomWalkHistory(seed)
    return backfill(store, client, client, [UniverseAsset(s, AssetClass.EQUITY) for s in SYMBOLS],
                    start=start, end=end, timeframes=("1Day",))

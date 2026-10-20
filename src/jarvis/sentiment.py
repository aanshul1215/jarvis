"""Sentiment scoring (Phase 6): a local model scores archived headlines; strategies read point-in-time aggregates.

Scorer: FinBERT (ProsusAI/finbert, pinned revision), run locally on the CPU, so it costs nothing per headline and
no text leaves the machine. Score = P(positive) - P(negative), from -1 to 1. Licence: CC BY-NC-SA 4.0
(non-commercial, checked on huggingface.co 2026-10-20). That covers research and paper trading; before any live
trading the model must be replaced by one whose licence allows it, or the licence question resolved.

Scores are stored beside the archive (``information/<source>-<scorer>/<YYYY-MM>.parquet``) and never change once
written, so a backtest always reads the same numbers. ``SentimentIndex`` turns them into features that use only
items available at the decision time:
- ``news_count_24h``: headlines that became available in the last 24 hours;
- ``news_sentiment_24h``: their mean score;
- ``news_sentiment_z``: how unusual that mean is against the asset's own previous 60 days (excluding the last day),
  in standard errors: (mean_24h - mean_60d) / (std_60d / sqrt(count_24h)). Needs 20 baseline headlines.
"""

from __future__ import annotations

import bisect
import math
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from .contracts import parse_utc
from .storage import LocalStorage

FINBERT, FINBERT_REVISION = "ProsusAI/finbert", "0bc2ac10dda6929bcb1f77ccc43c7ec5c424f031"
WINDOW, BASELINE, MIN_BASELINE = timedelta(hours=24), timedelta(days=60), 20


class FinbertScorer:
    name = "finbert"
    version = f"{FINBERT}@{FINBERT_REVISION[:12]}"

    def __init__(self, cache_dir: Path | None = None, batch: int = 64):
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        kwargs = {"revision": FINBERT_REVISION, "cache_dir": str(cache_dir) if cache_dir else None}
        self.tokenizer = AutoTokenizer.from_pretrained(FINBERT, **kwargs)
        self.model = AutoModelForSequenceClassification.from_pretrained(FINBERT, use_safetensors=True, **kwargs).eval()
        labels = {v.lower(): k for k, v in self.model.config.id2label.items()}
        self.positive, self.negative = labels["positive"], labels["negative"]
        self.batch = batch

    def score(self, texts: list[str]) -> list[float]:
        import torch

        out: list[float] = []
        with torch.no_grad():
            for i in range(0, len(texts), self.batch):
                encoded = self.tokenizer(texts[i:i + self.batch], padding=True, truncation=True, max_length=64,
                                         return_tensors="pt")
                probs = torch.softmax(self.model(**encoded).logits, dim=-1)
                out.extend((probs[:, self.positive] - probs[:, self.negative]).tolist())
        return out


def score_archive(store: LocalStorage, source: str, scorer, *, months: list[str] | None = None) -> dict:
    """Score every archived item not yet scored (headline text) and store the scores beside the archive."""
    folder = store.home / "information" / source
    months = months or sorted(p.stem for p in folder.glob("*.parquet"))
    report = {"months": 0, "scored": 0, "scorer": scorer.version}
    for month in months:
        items = store.read_table("information", source, month)
        existing = store.read_table("information", f"{source}-{scorer.name}", month)
        done = {r["item_id"] for r in existing}
        todo = [r for r in items if r["item_id"] not in done and (r.get("title") or "").strip()]
        if not todo:
            continue
        scores = scorer.score([r["title"] for r in todo])
        rows = existing + [{"item_id": r["item_id"], "symbols": r["symbols"], "available_at": r["available_at"],
                            "score": float(s), "scorer": scorer.version} for r, s in zip(todo, scores)]
        store.write_table("information", f"{source}-{scorer.name}", month,
                          rows=sorted(rows, key=lambda r: (r["available_at"], r["item_id"])))
        report["months"] += 1
        report["scored"] += len(todo)
    return report


class SentimentIndex:
    """Point-in-time sentiment features per asset from stored scores. Callable as ``index(asset, as_of)``."""

    def __init__(self, store: LocalStorage, source: str = "alpaca_news", scorer: str = "finbert"):
        by_asset: dict[str, list[tuple[datetime, float]]] = {}
        for path in sorted((store.home / "information" / f"{source}-{scorer}").glob("*.parquet")):
            for row in store.read_table("information", f"{source}-{scorer}", path.stem):
                moment = parse_utc(row["available_at"])
                for symbol in filter(None, row["symbols"].split(",")):
                    by_asset.setdefault(symbol, []).append((moment, float(row["score"])))
        self.times, self.scores = {}, {}
        for symbol, rows in by_asset.items():
            rows.sort()
            self.times[symbol] = [t for t, _ in rows]
            self.scores[symbol] = np.array([s for _, s in rows])

    def __bool__(self) -> bool:
        return bool(self.times)

    def __call__(self, asset: str, as_of: datetime) -> dict:
        times = self.times.get(asset)
        if not times:
            return {"news_count_24h": 0, "news_sentiment_24h": None, "news_sentiment_z": None}
        end = bisect.bisect_right(times, as_of)
        recent_start = bisect.bisect_right(times, as_of - WINDOW)
        base_start = bisect.bisect_right(times, as_of - WINDOW - BASELINE)
        recent = self.scores[asset][recent_start:end]
        baseline = self.scores[asset][base_start:recent_start]
        mean = float(recent.mean()) if len(recent) else None
        z = None
        if len(recent) and len(baseline) >= MIN_BASELINE and baseline.std() > 0:
            z = (mean - float(baseline.mean())) / (float(baseline.std()) / math.sqrt(len(recent)))
        return {"news_count_24h": int(len(recent)), "news_sentiment_24h": mean, "news_sentiment_z": z}

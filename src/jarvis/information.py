"""Event-driven local information features, deliberately outside the trading path."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .contracts import AssetClass, LedgerEvent, iso, parse_utc, require_utc, utc_now
from .storage import LocalStorage


POSITIVE = {"beat", "growth", "profit", "profitable", "upgrade", "approved", "record"}
NEGATIVE = {"miss", "loss", "decline", "downgrade", "fraud", "breach", "lawsuit"}


@dataclass(frozen=True)
class InformationDocument:
    asset_id: str
    asset_class: AssetClass
    source_id: str
    source_url: str
    published_at: datetime
    first_available_at: datetime
    category: str
    text: str

    def __post_init__(self) -> None:
        require_utc(self.published_at)
        require_utc(self.first_available_at)
        if not self.asset_id or not self.source_id or not self.text.strip() or len(self.text) > 200_000:
            raise ValueError("information identity/text invalid")
        if self.published_at > self.first_available_at:
            raise ValueError("publication after availability")


def load_document(path: Path) -> InformationDocument:
    data = json.loads(path.read_text())
    expected = {"asset_id", "asset_class", "source_id", "source_url", "published_at", "first_available_at", "category", "text"}
    if set(data) != expected:
        raise ValueError("information document schema mismatch")
    return InformationDocument(data["asset_id"], AssetClass(data["asset_class"]), data["source_id"],
                               data["source_url"], parse_utc(data["published_at"]),
                               parse_utc(data["first_available_at"]), data["category"], data["text"])


def summarize(document: InformationDocument) -> dict:
    """Transparent extractive summary and lexical score, with no trade permission."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", document.text.strip()) if s.strip()]
    scores = []
    for index, sentence in enumerate(sentences):
        words = set(re.findall(r"[a-z]+", sentence.lower()))
        score = 2 * int(document.asset_id.lower().replace("/", "") in sentence.lower().replace("/", ""))
        score += len(words & (POSITIVE | NEGATIVE))
        scores.append((score, index))
    selected = sorted(sorted(scores, reverse=True)[:2], key=lambda x: x[1])
    summary = " ".join(sentences[index] for _, index in selected)[:500]
    tokens = re.findall(r"[a-z]+", document.text.lower())
    positive = sum(token in POSITIVE for token in tokens)
    negative = sum(token in NEGATIVE for token in tokens)
    return {"summary": summary, "positive_terms": positive, "negative_terms": negative,
            "lexical_balance": (positive - negative) / max(1, positive + negative),
            "method": "EXTRACTIVE_LEXICON_V1", "validation": "UNVALIDATED",
            "trade_authority": "NONE"}


def ingest(store: LocalStorage, document: InformationDocument) -> dict:
    store._require_writer()
    if document.first_available_at > utc_now():
        raise ValueError("future information cannot be ingested")
    canonical = {"asset_id": document.asset_id, "asset_class": document.asset_class.value,
                 "source_id": document.source_id, "source_url": document.source_url,
                 "published_at": iso(document.published_at), "first_available_at": iso(document.first_available_at),
                 "category": document.category, "text": document.text}
    doc_id = "info_" + hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()[:24]
    feature_path = store.home / "information" / "features" / f"{doc_id}.json"
    if feature_path.exists():
        feature = json.loads(feature_path.read_text())
    else:
        feature = {"schema_version": 1, "record_id": doc_id, "timestamp_utc": iso(utc_now()),
               "asset_id": document.asset_id, "asset_class": document.asset_class.value,
               "source_id": document.source_id, "source_url": document.source_url,
               "published_at": iso(document.published_at), "first_available_at": iso(document.first_available_at),
                   "category": document.category, **summarize(document)}
        store.save_information(doc_id, canonical, feature)
    if not any(row["event"]["event_id"] == doc_id for row in store.read_events()):
        store.append_event(LedgerEvent(doc_id, "INFO_FEATURE", utc_now(), doc_id,
                                   asset_id=document.asset_id, asset_class=document.asset_class,
                                   source_id=document.source_id, source_event_at=document.published_at,
                                   first_available_at=document.first_available_at,
                                   status="UNVALIDATED", payload={"feature_path": str(feature_path.relative_to(store.home)),
                                                                  "trade_authority": "NONE"}))
    return feature

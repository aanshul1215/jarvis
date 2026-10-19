"""Offline, point-in-time research. Nothing here grants trading approval."""

from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import joblib
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .contracts import AssetClass, Bar, FeatureSnapshot, iso, utc_now
from .market import features_for, scan
from .storage import LocalStorage, atomic_bytes
from .storage import StorageError


FEATURES = ("return_1", "momentum_5", "volatility_20", "relative_volume", "breakout_20", "trend_strength")


@dataclass(frozen=True)
class Observation:
    snapshot: FeatureSnapshot
    future_return: float
    label: int


def observations(bars: list[Bar], *, horizon: int = 1) -> list[Observation]:
    """The label is formed only after the decision bar; features see only known bars."""
    if horizon < 1:
        raise ValueError("horizon must be positive")
    ordered = sorted(bars, key=lambda b: b.end_at)
    if len({(b.asset_id, b.asset_class) for b in ordered}) != 1:
        raise ValueError("one asset per research series")
    if any(a.end_at >= b.end_at for a, b in zip(ordered, ordered[1:])):
        raise ValueError("duplicate or unordered bars")
    result = []
    for index in range(21, len(ordered) - horizon):
        current, future = ordered[index], ordered[index + horizon]
        snapshot = features_for(ordered[:index + 1], current.available_at)
        if snapshot.as_of != current.end_at or snapshot.available_at != current.available_at:
            raise ValueError("point-in-time feature violation")
        if any(snapshot.values.get(name) is None or not math.isfinite(snapshot.values[name]) for name in FEATURES):
            continue
        change = future.close / current.close - 1
        result.append(Observation(snapshot, change, int(change > 0)))
    return result


def _split(rows: list[Observation]) -> tuple[list[Observation], list[Observation], list[Observation]]:
    """Chronological train/validation/holdout with one observation embargo."""
    if len(rows) < 60:
        raise ValueError("at least 60 labeled observations required")
    first, second = int(len(rows) * 0.6), int(len(rows) * 0.8)
    train, validation, holdout = rows[:first], rows[first + 1:second], rows[second + 1:]
    if min(map(len, (train, validation, holdout))) < 10:
        raise ValueError("insufficient split size")
    return train, validation, holdout


def _xy(rows: list[Observation]):
    return np.asarray([[float(row.snapshot.values[name]) for name in FEATURES] for row in rows]), np.asarray([row.label for row in rows])


def _metrics(rows: list[Observation], probabilities, *, cost_bps: float) -> dict:
    predictions = np.asarray(probabilities, dtype=float)
    labels = np.asarray([row.label for row in rows])
    gross = np.asarray([row.future_return for row in rows])
    take = predictions > 0.55
    net = np.where(take, gross - cost_bps / 10000, 0.0)
    curve = np.cumprod(1 + net)
    peak = np.maximum.accumulate(np.r_[1.0, curve])[1:]
    losses = np.sort(net)[:max(1, math.ceil(len(net) * 0.05))]
    calibration = []
    for low, high in ((0, .25), (.25, .5), (.5, .75), (.75, 1.000001)):
        mask = (predictions >= low) & (predictions < high)
        if mask.any():
            calibration.append({"probability_bin": f"{low:.2f}-{min(high,1):.2f}",
                                "count": int(mask.sum()), "mean_prediction": float(predictions[mask].mean()),
                                "observed_positive_rate": float(labels[mask].mean())})
    return {"n": len(rows), "trades": int(take.sum()), "accuracy": float(np.mean((predictions >= .5) == labels)),
            "brier": float(brier_score_loss(labels, predictions)),
            "log_loss": float(log_loss(labels, np.clip(predictions, 1e-6, 1 - 1e-6), labels=[0, 1])),
            "mean_net_return_per_observation": float(np.mean(net)),
            "compounded_net_return": float(curve[-1] - 1),
            "max_drawdown": float(np.min(curve / peak - 1)),
            "expected_shortfall_5pct": float(np.mean(losses)), "calibration": calibration}


def _walk_forward(rows: list[Observation], prototype, cost_bps: float) -> list[dict]:
    """Expanding training windows; each validation slice follows a one-row embargo."""
    cutoff = int(len(rows) * .5)
    stop = int(len(rows) * .8)
    step = max(10, int(len(rows) * .1))
    folds = []
    while cutoff + 1 < stop:
        training, validation = rows[:cutoff], rows[cutoff + 1:min(cutoff + 1 + step, stop)]
        x, y = _xy(training)
        if len(set(y)) < 2 or not validation:
            break
        model = deepcopy(prototype)
        model.fit(x, y)
        val_x, _ = _xy(validation)
        folds.append({"train_end_at": iso(training[-1].snapshot.as_of),
                      "validation_start_at": iso(validation[0].snapshot.as_of),
                      "validation_end_at": iso(validation[-1].snapshot.as_of),
                      "metrics": _metrics(validation, model.predict_proba(val_x)[:, 1], cost_bps=cost_bps)})
        cutoff += step
    return folds


def _record_registry(store: LocalStorage, report: dict, rows: list[Observation]) -> None:
    try:
        registry = store.load_json("model-registry")
    except FileNotFoundError:
        registry = {"models": {}}
    for name, result in report["models"].items():
        key = f"{report['run_id']}:{name}"
        item = {"model_id": name, "version": report["run_id"], "asset_id": report["asset_id"],
                "asset_class": report["asset_class"], "status": "RESEARCH",
                "feature_schema": list(FEATURES), "artifact": result["artifact"],
                "sha256": result["sha256"], "holdout_start_at": iso(rows[int(len(rows)*.8)+1].snapshot.as_of),
                "holdout_end_at": iso(rows[-1].snapshot.as_of), "approval_change": "NONE"}
        old = registry["models"].get(key)
        if old is not None and old != item:
            raise StorageError("registered model version conflict")
        registry["models"][key] = item
    store.publish_json("model-registry", registry)


def train_fixture(store: LocalStorage, bars: list[Bar], *, cost_bps: float = 20) -> dict:
    """Evaluate baseline and challenger on untouched holdout; register as RESEARCH only."""
    if cost_bps < 0:
        raise ValueError("negative costs")
    rows = observations(bars)
    train, validation, holdout = _split(rows)
    train_x, train_y = _xy(train)
    if len(set(train_y)) < 2:
        raise ValueError("training labels have one class")
    models = {"constant": DummyClassifier(strategy="prior"),
              "logistic": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=7))}
    report = {"schema_version": 1, "run_id": hashlib.sha256((bars[0].asset_id + iso(bars[-1].end_at) + str(cost_bps)).encode()).hexdigest()[:20],
              "asset_id": bars[0].asset_id, "asset_class": bars[0].asset_class.value,
              "source_id": bars[0].source_id, "feature_version": "features-v1", "horizon_bars": 1,
              "cost_bps": cost_bps, "approval": "RESEARCH", "split": {"train": len(train), "validation": len(validation), "holdout": len(holdout), "embargo": 1},
              "models": {}}
    for name, model in models.items():
        walk_forward = _walk_forward(rows, model, cost_bps)
        model.fit(train_x, train_y)
        val_x, _ = _xy(validation)
        hold_x, _ = _xy(holdout)
        report["models"][name] = {"walk_forward": walk_forward,
                                  "validation": _metrics(validation, model.predict_proba(val_x)[:, 1], cost_bps=cost_bps),
                                  "holdout": _metrics(holdout, model.predict_proba(hold_x)[:, 1], cost_bps=cost_bps)}
        model_path = store.home / "models" / report["run_id"] / f"{name}.joblib"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        # joblib is native model serialization; never deserialize untrusted files.
        import io
        buffer = io.BytesIO()
        joblib.dump(model, buffer)
        if model_path.exists() and hashlib.sha256(model_path.read_bytes()).hexdigest() != hashlib.sha256(buffer.getvalue()).hexdigest():
            raise StorageError("immutable model artifact conflict")
        digest = atomic_bytes(model_path, buffer.getvalue())
        report["models"][name]["artifact"] = str(model_path.relative_to(store.home))
        report["models"][name]["sha256"] = digest
    report["selection"] = "NO_AUTOMATIC_PROMOTION"
    _record_registry(store, report, rows)
    store.publish_json(f"experiment-{report['run_id']}", report)
    store.export_csv(f"model-comparison-{report['run_id']}", [
        {"run_id": report["run_id"], "asset_id": report["asset_id"], "model": name, "split": split, **metrics}
        for name, item in report["models"].items() for split, metrics in (("validation", item["validation"]), ("holdout", item["holdout"]))])
    return report


def backtest_fixture(store: LocalStorage, bars: list[Bar], *, cost_bps: float = 20) -> dict:
    """Deterministic event replay; signals and returns are kept separate in time."""
    if cost_bps < 0:
        raise ValueError("negative costs")
    rows = observations(bars)
    records = []
    for row in rows:
        candidates = scan(row.snapshot, row.snapshot.available_at)
        entered = any(c.trigger == "BREAKOUT_VOLUME" for c in candidates)
        records.append({"record_id": row.snapshot.snapshot_id, "timestamp_utc": iso(row.snapshot.available_at),
                        "asset_id": row.snapshot.asset_id, "asset_class": row.snapshot.asset_class.value,
                        "strategy_id": "breakout-volume", "strategy_version": "1.0.0", "model_version": "baseline-v1",
                        "opportunity_id": candidates[0].candidate_id if candidates else "", "event": "SIGNAL" if entered else "NO_SIGNAL",
                        "data_source": bars[0].source_id, "processing_latency_ms": 0,
                        "status": "HYPOTHETICAL", "reason_codes": "BREAKOUT_VOLUME" if entered else "NO_TRIGGER",
                        "correlation_id": row.snapshot.snapshot_id, "gross_return": row.future_return if entered else 0,
                        "net_return": row.future_return - cost_bps / 10000 if entered else 0})
    net = np.asarray([r["net_return"] for r in records])
    curve = np.cumprod(1 + net)
    peak = np.maximum.accumulate(np.r_[1.0, curve])[1:]
    report = {"schema_version": 1, "asset_id": bars[0].asset_id, "asset_class": bars[0].asset_class.value,
              "fixture": bars[0].source_id == "SYNTHETIC_FIXTURE", "strategy_id": "breakout-volume",
              "approval": "RESEARCH", "observations": len(records), "trades": sum(r["event"] == "SIGNAL" for r in records),
              "cost_bps": cost_bps, "compounded_net_return": float(curve[-1] - 1),
              "max_drawdown": float(np.min(curve / peak - 1)), "status": "HYPOTHETICAL"}
    name = hashlib.sha256((bars[0].asset_id + iso(bars[-1].end_at) + str(cost_bps)).encode()).hexdigest()[:20]
    store.export_csv(f"backtest-trades-{name}", records)
    store.publish_json(f"backtest-{name}", report)
    return report

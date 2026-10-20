"""Phase 5 model studies: load price histories, run a pre-registered comparison, and record it.

Sources: ``fred`` (long-history index and crypto closes from FRED, available without broker keys) and ``bars``
(the universe's stored Alpaca daily bars after ``backfill``). Every run is appended to
``research/model_studies.jsonl`` (hash-chained, like the strategy experiment registry), and the holdout split may
be evaluated only once per study configuration.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np

from . import regime, riskmodel, volatility
from .contracts import AssetClass, iso, utc_now
from .harness import ExperimentRegistry, _code_version
from .history import load_universe
from .macro import PRICE_GROUPS, as_of_series, load_macro
from .storage import LocalStorage, _canonical, _hash
from .volatility import PriceSeries, bar_returns

STUDY_VERSION = "1.0.0"  # docs/07-awareness/MODEL_REGISTER.md; any change to a rule or constant is a new version
KINDS = ("volatility", "regime", "risk")


class StudyRegistry(ExperimentRegistry):
    def __init__(self, home: Path):
        self.path = Path(home) / "research" / "model_studies.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)


def fred_prices(store: LocalStorage) -> list[PriceSeries]:
    out = []
    for series_id, group in PRICE_GROUPS.items():
        rows = load_macro(store, series_id)
        if len(rows) > 2:
            out.append(PriceSeries(series_id, group, tuple(datetime.fromisoformat(r["observation_date"]).date()
                                                           for r in rows), np.asarray([r["value"] for r in rows])))
    return out


def bar_prices(store: LocalStorage, universe: Path, dataset: str = "1Day-adjusted") -> list[PriceSeries]:
    out = []
    for asset in load_universe(universe):
        bars = store.load_bars(asset.symbol, asset.asset_class, dataset=dataset)
        if len(bars) > 2:
            _, dates, closes = bar_returns(bars)  # dates of the 2nd..last bars; prepend the first bar's date
            day0 = bars[0].start_at.astimezone(volatility.NEW_YORK).date() \
                if asset.asset_class == AssetClass.EQUITY else bars[0].start_at.date()
            out.append(PriceSeries(asset.symbol, asset.asset_class.value.upper(), (day0, *dates), closes))
    return out


def stress_source(store: LocalStorage):
    vix, vxv = as_of_series(store, "VIXCLS"), as_of_series(store, "VXVCLS")
    if not vix.times:
        return None
    return lambda item, dates: regime.stress_flags(dates, item.group, vix.at, vxv.at)


def _fingerprint(kind: str, source: str, assets: list[str]) -> str:
    constants = {"window": volatility.WINDOW, "vol_horizon": volatility.PRIMARY_HORIZON,
                 "regime_horizon": regime.HORIZON, "risk_window": riskmodel.WINDOW, "risk_step": riskmodel.STEP}
    key = {"kind": kind, "source": source, "assets": sorted(assets), "version": STUDY_VERSION, "constants": constants}
    return _hash(_canonical(key))[:20]


def run_study(home: Path, kind: str, *, source: str = "fred", split: str = "DEVELOPMENT",
              universe: Path | None = None, dataset: str = "1Day-adjusted") -> dict:
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    with LocalStorage(Path(home), writer=False) as store:
        series = fred_prices(store) if source == "fred" else bar_prices(store, universe, dataset)
        stress = stress_source(store) if kind == "regime" else None
    if not series:
        raise ValueError(f"no price history for source {source}: run macro-update (fred) or backfill (bars) first")
    assets = [s.asset for s in series]
    registry = StudyRegistry(Path(home))
    fingerprint = _fingerprint(kind, source, assets)
    if split == "HOLDOUT":
        if registry.holdout_used(fingerprint):
            raise PermissionError("holdout already evaluated for this study; it may be used once")
        if not any(r["fingerprint"] == fingerprint and r["spec"]["split"] == "DEVELOPMENT" and r["status"] == "COMPLETED"
                   for r in registry.records()):
            raise PermissionError("record the development result before the holdout (pre-registered order)")
    record = {"created_at": iso(utc_now()), "code_version": _code_version(), "fingerprint": fingerprint,
              "study_version": STUDY_VERSION, "spec": {"kind": kind, "source": source, "split": split, "assets": assets},
              "evidence": "RESEARCH"}
    try:
        if kind == "volatility":
            result = {"primary": volatility.compare(series, horizon=volatility.PRIMARY_HORIZON, split=split),
                      "secondary": {str(h): volatility.compare(series, horizon=h, split=split)
                                    for h in volatility.HORIZONS if h != volatility.PRIMARY_HORIZON}}
            result["winner"] = result["primary"]["winner"]
        elif kind == "regime":
            result = regime.compare(series, stress_for=stress, split=split)
        else:
            result = riskmodel.compare(series, split=split)
        record.update({"status": "COMPLETED", "result": result})
    except Exception as exc:
        record.update({"status": "FAILED", "error": f"{type(exc).__name__}: {exc}"})
        registry.append(record)
        raise
    return registry.append(record)

"""Transaction costs (Phase 5): a per-order estimate, and a record of what orders really cost.

Baseline: the fixed assumption the replay uses (``replay.CostModel``: 5 bps per side for stocks; 25 bps fee plus
5 bps spread for crypto). Model: half the quoted spread at decision time, plus the asset-class fee, plus a
square-root market-impact term, impact = ``IMPACT_COEFFICIENT`` x daily volatility x sqrt(order value / average
daily traded value). The square-root form and a coefficient near 1 are standard in the market-impact literature
(RECALLED, e.g. Almgren et al. 2005; Toth et al. 2011); for orders of a few thousand dollars in liquid assets the
impact term is close to zero and the spread dominates.

The comparison needs real fills. ``realised_costs`` turns the journal into one row per filled order: the price the
decision was based on, the average fill price, and the signed shortfall in basis points (positive = paid more than
the reference when buying, or received less when selling). ``compare`` scores both predictions against that once
``MIN_FILLS`` paper fills exist; until then it reports INSUFFICIENT_DATA rather than a verdict.
"""

from __future__ import annotations

import math

import numpy as np

from .contracts import AssetClass
from .metrics import diebold_mariano
from .replay import CostModel
from .storage import LocalStorage

IMPACT_COEFFICIENT = 1.0
MIN_FILLS = 50
FIXED = CostModel()


def fixed_bps(asset_class: AssetClass, costs: CostModel = FIXED) -> float:
    return (costs.half_spread(asset_class) + costs.fee(asset_class)) * 10_000


def estimate_bps(asset_class: AssetClass, *, spread_bps: float | None, daily_vol: float | None = None,
                 order_notional: float | None = None, average_daily_value: float | None = None,
                 costs: CostModel = FIXED) -> float:
    """Expected one-way cost of an order in basis points, from what is known at decision time."""
    half_spread = spread_bps / 2 if spread_bps is not None and spread_bps >= 0 else costs.half_spread(asset_class) * 10_000
    impact = 0.0
    if daily_vol and order_notional and average_daily_value and average_daily_value > 0:
        impact = IMPACT_COEFFICIENT * daily_vol * math.sqrt(order_notional / average_daily_value) * 10_000
    return half_spread + costs.fee(asset_class) * 10_000 + impact


def realised_costs(store: LocalStorage) -> list[dict]:
    """One row per filled entry or exit: decision mid price, fill price and shortfall in basis points (fees excluded:
    the broker's fill price does not include them, so fees are added separately from the fee schedule)."""
    intents = {}
    for row in store.read_events():
        event = row["event"]
        payload = event["payload"]
        if event["event_type"] in ("ORDER_INTENT", "EXIT_INTENT") and payload.get("reference_price"):
            intents[payload["client_order_id"]] = {**payload, "kind": event["event_type"], "asset_id": event.get("asset_id"),
                                                   "side": payload.get("side", "SELL")}
    fills = {}
    for row in store.read_events():
        event = row["event"]
        payload = event["payload"]
        cid = payload.get("client_order_id")
        if cid in intents and payload.get("average_price") and float(payload.get("filled_quantity") or 0) > 0:
            fills[cid] = payload  # the latest report of each order wins
    out = []
    for cid, fill in fills.items():
        intent = intents[cid]
        # Shortfall is measured from the mid price at decision time (entries record the quote mid; exits use the last
        # bar close as the best available mid), so it is comparable with half-spread predictions.
        reference = float(intent.get("decision_mid") or intent["reference_price"])
        price = float(fill["average_price"])
        sign = 1 if intent["side"] == "BUY" else -1
        cls = AssetClass(intent["asset_class"]) if intent.get("asset_class") else None
        out.append({"client_order_id": cid, "asset_id": intent.get("asset_id"), "asset_class": cls,
                    "side": intent["side"], "reference_price": reference, "fill_price": price,
                    "shortfall_bps": sign * (price - reference) / reference * 10_000,
                    "spread_bps": intent.get("spread_bps"), "daily_vol": intent.get("forecast_daily_vol"),
                    "notional": float(fill["filled_quantity"]) * price})
    return out


def compare(rows: list[dict], costs: CostModel = FIXED) -> dict:
    """Mean absolute error of the fixed assumption and the model against realised costs (spread part only).

    The fee is identical in both predictions and not in the fill price, so it is removed from both before scoring.
    Pass rule (pre-registered): the model is adopted if its absolute errors are lower than the fixed assumption's
    with a one-sided Diebold-Mariano p-value below 0.05 over at least ``MIN_FILLS`` fills.
    """
    usable = [r for r in rows if r["asset_class"] is not None]
    if len(usable) < MIN_FILLS:
        return {"result": "INSUFFICIENT_DATA", "fills": len(usable), "needed": MIN_FILLS}
    actual = np.asarray([r["shortfall_bps"] for r in usable])
    fixed = np.asarray([fixed_bps(r["asset_class"], costs) - costs.fee(r["asset_class"]) * 10_000 for r in usable])
    model = np.asarray([estimate_bps(r["asset_class"], spread_bps=r["spread_bps"], daily_vol=r["daily_vol"],
                                     costs=costs) - costs.fee(r["asset_class"]) * 10_000 for r in usable])
    test = diebold_mariano(np.abs(actual - fixed) - np.abs(actual - model), 1)
    return {"result": "PASS" if test["p_value"] < 0.05 else "FAIL", "fills": len(usable),
            "mean_realised_bps": float(actual.mean()), "mae_fixed_bps": float(np.mean(np.abs(actual - fixed))),
            "mae_model_bps": float(np.mean(np.abs(actual - model))), "test": test}

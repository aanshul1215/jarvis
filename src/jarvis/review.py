"""Post-trade evidence summaries. Reviews never change strategy or risk approval."""

from __future__ import annotations

from collections import defaultdict

from .storage import LocalStorage


def review_outcomes(store: LocalStorage) -> dict:
    groups = defaultdict(list)
    rejected = defaultdict(int)
    for row in store.read_events():
        event = row["event"]
        if event["event_type"] == "TRADE_OUTCOME":
            payload = event["payload"]
            groups[(payload.get("evidence_class", "UNKNOWN"), payload.get("strategy_id") or "UNKNOWN")].append(payload)
        elif event["event_type"] == "RISK_DECISION" and event["payload"].get("result") != "ALLOW":
            for reason in event.get("reason_codes", []):
                rejected[reason] += 1
    results = []
    for (evidence, strategy), outcomes in sorted(groups.items()):
        pnls = [float(item["gross_pnl_estimate"]) for item in outcomes]
        wins = sum(p > 0 for p in pnls)
        results.append({"evidence_class": evidence, "strategy_id": strategy, "trades": len(pnls),
                        "gross_pnl_estimate": sum(pnls), "winning_trades": wins,
                        "bayesian_win_probability_mean": (wins + 1) / (len(pnls) + 2),
                        "net_pnl": "UNVERIFIED_FEES_AND_SLIPPAGE", "approval_change": "NONE"})
    report = {"schema_version": 1, "approval_change": "NONE", "outcomes": results,
              "rejection_reason_counts": dict(sorted(rejected.items()))}
    store.publish_json("learning-review", report)
    store.export_csv("learning-review", results)
    return report

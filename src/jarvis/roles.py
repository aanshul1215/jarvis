"""The 18 logical responsibilities and their observable evidence contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Responsibility:
    department: str
    name: str
    purpose: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    event_types: tuple[str, ...]
    implementation: str


ROLES = (
    Responsibility("Market Intelligence", "Data Trust", "Validate source quality and time availability", ("bars", "quotes"), ("quality decisions",), ("DATA_ACCESS", "DATA_BLOCK", "DATA_QUARANTINE"), "PARTIAL"),
    Responsibility("Market Intelligence", "Market / Technical", "Build point-in-time price and volume features", ("validated bars",), ("feature snapshots",), ("FEATURE_SNAPSHOT",), "IMPLEMENTED"),
    Responsibility("Market Intelligence", "Flow / Microstructure", "Measure executable quote quality", ("bid", "ask"), ("spread evidence",), ("QUOTE_ACCESS", "QUOTE_BLOCK"), "PARTIAL"),
    Responsibility("Market Intelligence", "News & Event", "Summarize local dated asset events", ("versioned source documents",), ("event features",), ("INFO_FEATURE",), "PARTIAL"),
    Responsibility("Market Intelligence", "Fundamental / Macro", "Extract reported company and macro features", ("filings", "macro releases"), ("dated fundamentals",), (), "UNAVAILABLE"),
    Responsibility("Market Intelligence", "Crypto", "Apply crypto-specific market clock and eligibility", ("crypto bars", "broker asset status"), ("crypto features",), ("QUOTE_ACCESS", "ASSET_BLOCK"), "PARTIAL"),
    Responsibility("Market Intelligence", "Manipulation Surveillance", "Flag suspicious market behavior", ("market data",), ("surveillance flags",), (), "UNAVAILABLE"),
    Responsibility("Market Intelligence", "Opportunity Scanner", "Detect bounded candidate opportunities", ("feature snapshots",), ("candidates",), ("CANDIDATE",), "IMPLEMENTED"),
    Responsibility("Quantitative Research", "Bull / Bear", "Compare alternative market hypotheses", ("historical features",), ("experiments",), (), "PARTIAL"),
    Responsibility("Quantitative Research", "Goal & Capital Planner", "Constrain sizing to owner limits", ("policy", "portfolio state"), ("size decisions",), ("SIZE_BLOCK", "RISK_DECISION"), "PARTIAL"),
    Responsibility("Model Intelligence & Validation", "Model Ensemble", "Evaluate baseline and challenger models", ("labeled observations",), ("model comparison",), (), "PARTIAL"),
    Responsibility("Model Intelligence & Validation", "Confidence Calibrator", "Measure probability quality", ("predictions", "labels"), ("Brier and log loss",), (), "PARTIAL"),
    Responsibility("Model Intelligence & Validation", "Ledger / Review", "Attribute decisions and outcomes", ("journal",), ("review reports",), ("TRADE_OUTCOME", "RISK_DECISION"), "IMPLEMENTED"),
    Responsibility("Autonomous Trading", "Strategy / Portfolio", "Select approved strategy or stay flat", ("candidate", "strategy registry"), ("intent or no-trade",), ("ORDER_INTENT", "NO_TRADE"), "PARTIAL"),
    Responsibility("Autonomous Trading", "Execution", "Submit and reconcile idempotent paper orders", ("approved intent",), ("broker orders",), ("BROKER_ORDER", "ORDER_UPDATE"), "ACCOUNT_UNVERIFIED"),
    Responsibility("Autonomous Trading", "Position Manager", "Apply recorded exit contract", ("open position", "bars"), ("exit order",), ("EXIT_INTENT", "EXIT_ORDER"), "PARTIAL"),
    Responsibility("Risk & Governance", "Orchestrator / Supervisor", "Reconcile and enter SAFE on disagreement", ("journal", "broker state"), ("operating state",), ("RECONCILED", "CYCLE_ERROR"), "IMPLEMENTED"),
    Responsibility("Risk & Governance", "Capital Governor / Risk", "Apply deterministic owner limits", ("intent", "policy", "broker state"), ("ALLOW/BLOCK",), ("RISK_DECISION",), "IMPLEMENTED"),
)

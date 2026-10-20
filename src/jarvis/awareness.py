"""Situational awareness (Phase 5): one point-in-time picture of the market and of the desk itself.

Built once per decision cycle from information available at that moment and recorded in the journal, so the regime
detector, the risk gate and (Phase 7) the strategy selector can learn from exactly what was known. Signals:

- market stress (FRED): VIX level and 5-day change, VIX / VXV term structure, 10y-2y slope, Baa credit spread and
  its 3-month change, 3-month T-bill; a stress flag using the regime study's rule;
- breadth (the universe's stocks/ETFs this cycle): share above the 200-bar average, with a positive 20-bar
  return, at a 252-bar high, up on the last bar;
- scheduled events: hours to the next FOMC decision, CPI and jobs release; weekday and weekend;
- crypto: BTC minus ETH 20-bar return;
- per asset: trend/volatility regime label and the volatility forecast used for sizing;
- the desk's own state: drawdown from peak, open positions, gross exposure.

Every signal must still earn its place: the workflow adds a signal to a downstream decision only if it improves that
decision out of sample (the regime study's stress ablation is the first such test). Recording them costs nothing.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .contracts import AssetClass, FeatureSnapshot, parse_utc
from .macro import AsOfSeries
from .regime import is_stressed
from .storage import LocalStorage

MACRO = ("VIXCLS", "VXVCLS", "T10Y2Y", "BAA10Y", "DTB3")
EVENTS = {"FOMC_DECISION": "hours_to_fomc", "CPI_RELEASE": "hours_to_cpi", "JOBS_RELEASE": "hours_to_jobs"}

class SituationBuilder:
    def __init__(self, store: LocalStorage):
        self.series = {s: AsOfSeries(store.read_table("macro", s)) for s in MACRO}
        self.events = [r for r in store.read_table("calendar", "events") if not r.get("cancelled")]

    def _hours_to(self, now: datetime, event_type: str) -> float | None:
        future = [parse_utc(r["event_at"]) for r in self.events if r["event_type"] == event_type
                  and parse_utc(r["event_at"]) > now and parse_utc(r["available_at"]) <= now]
        return (min(future) - now).total_seconds() / 3600 if future else None

    def market(self, now: datetime) -> dict:
        value = {s: series.at(now) for s, series in self.series.items()}
        vix, vxv = value["VIXCLS"], value["VXVCLS"]
        vix_week = self.series["VIXCLS"].at(now - timedelta(days=7))
        baa_quarter = self.series["BAA10Y"].at(now - timedelta(days=91))
        stress = is_stressed(vix, vxv)
        return {"vix": vix, "vix_change_5d": vix - vix_week if vix is not None and vix_week is not None else None,
                "vix_term": vix / vxv if vix is not None and vxv else None, "slope_10y_2y": value["T10Y2Y"],
                "baa_spread": value["BAA10Y"],
                "baa_spread_change_63d": value["BAA10Y"] - baa_quarter
                if value["BAA10Y"] is not None and baa_quarter is not None else None,
                "tbill_3m": value["DTB3"], "stress": stress}

    def build(self, now: datetime, snapshots: dict[str, FeatureSnapshot], *, assets: dict[str, dict] | None = None,
              desk: dict | None = None) -> dict:
        stocks = [s.values for s in snapshots.values() if s.asset_class == AssetClass.EQUITY]

        def share(feature: str, test) -> float | None:
            known = [v[feature] for v in stocks if v.get(feature) is not None]
            return sum(1 for x in known if test(x)) / len(known) if known else None

        btc, eth = snapshots.get("BTC/USD"), snapshots.get("ETH/USD")
        crypto = None
        if btc and eth and btc.values.get("ret_20") is not None and eth.values.get("ret_20") is not None:
            crypto = btc.values["ret_20"] - eth.values["ret_20"]
        return {
            "as_of": now.isoformat().replace("+00:00", "Z"),
            "market": self.market(now),
            "breadth": {"stocks": len(stocks), "above_sma_200": share("dist_sma_200", lambda x: x > 0),
                        "positive_20": share("ret_20", lambda x: x > 0),
                        "at_252_high": share("dist_high_252", lambda x: x >= 0),
                        "up_last_bar": share("return_1", lambda x: x > 0)},
            "calendar": {**{name: self._hours_to(now, kind) for kind, name in EVENTS.items()},
                         "weekday": now.weekday(), "weekend": now.weekday() >= 5},
            "crypto": {"btc_minus_eth_ret_20": crypto},
            "assets": assets or {},
            "desk": desk or {},
        }

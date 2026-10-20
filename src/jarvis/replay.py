"""Historical replay for the evaluation harness (Phase 3).

The real PaperDesk, TradingEngine, strategies and Governor run unchanged; only the clock, the market data and the
broker are replaced:

- ``ReplayData`` serves stored bars only once their ``available_at`` has passed and raises ``LookAheadError`` if it
  is ever about to return one that has not (a structural guard, not a convention).
- ``ReplayBroker`` fills each order at the open of the first bar that starts at or after the order (a five-minute
  grace covers a bar that began a moment before the decision). That is the standard "decide on the close, trade the
  next open" convention. Buy limits fill only if the price traded at or below the limit; costs come from
  ``CostModel``. Fees are charged in dollars for every asset class: the same cost as Alpaca taking the crypto fee
  from the coin received, without tripping the reconciliation tolerance in doubled-cost stress runs (the coin-fee
  path is covered by the soak and mock-broker tests).
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, replace
from datetime import datetime, time, timedelta
from typing import Iterable

from .broker import BrokerAdapter, BrokerError
from .contracts import AssetClass, Bar, BrokerOrder, require_utc
from .market_data import Quote
from .risk import BrokerState
from .storage import LocalStorage
from .timeframes import NEW_YORK

FILL_GRACE = timedelta(minutes=5)


class LookAheadError(RuntimeError):
    """A component asked for data that was not yet available at the simulated time."""


@dataclass(frozen=True)
class CostModel:
    """Per-side trading costs in basis points. Defaults are deliberately on the expensive side.

    Equities: Alpaca charges no commission; half-spread on liquid ETFs and large caps is roughly 1-5 bps
    (research briefs 11 and 18), so 5 bps per side is conservative. Crypto: Alpaca's lowest-tier taker fee is
    25 bps per side (brief 21) plus about 5 bps half-spread. ``multiplier`` scales every cost for stress tests.
    """

    equity_half_spread_bps: float = 5.0
    equity_fee_bps: float = 0.0
    crypto_half_spread_bps: float = 5.0
    crypto_fee_bps: float = 25.0
    multiplier: float = 1.0

    def half_spread(self, asset_class: AssetClass) -> float:
        bps = self.equity_half_spread_bps if asset_class == AssetClass.EQUITY else self.crypto_half_spread_bps
        return bps * self.multiplier / 10_000

    def fee(self, asset_class: AssetClass) -> float:
        bps = self.equity_fee_bps if asset_class == AssetClass.EQUITY else self.crypto_fee_bps
        return bps * self.multiplier / 10_000

    def as_dict(self) -> dict:
        return {"equity_half_spread_bps": self.equity_half_spread_bps, "equity_fee_bps": self.equity_fee_bps,
                "crypto_half_spread_bps": self.crypto_half_spread_bps, "crypto_fee_bps": self.crypto_fee_bps,
                "multiplier": self.multiplier}


class ReplayClock:
    def __init__(self, start: datetime):
        self.now = require_utc(start)

    def __call__(self) -> datetime:
        return self.now


class ReplayData:
    """Point-in-time view of stored bars for a set of assets and one dataset (e.g. ``1Day-adjusted``)."""

    def __init__(self, store: LocalStorage, assets: Iterable[tuple[str, AssetClass]], dataset: str,
                 clock: ReplayClock, costs: CostModel):
        self.clock, self.costs, self.dataset = clock, costs, dataset
        self.bars: dict[str, list[Bar]] = {}
        self.classes: dict[str, AssetClass] = {}
        for symbol, cls in assets:
            bars = sorted(store.load_bars(symbol, cls, dataset=dataset), key=lambda b: b.available_at)
            if not bars:
                raise ValueError(f"no stored bars for {symbol} in dataset {dataset}")
            self.bars[symbol], self.classes[symbol] = bars, cls
        self._available = {s: [b.available_at for b in bars] for s, bars in self.bars.items()}
        self._starts = {s: [b.start_at for b in sorted(bars, key=lambda b: b.start_at)] for s, bars in self.bars.items()}
        self._by_start = {s: sorted(bars, key=lambda b: b.start_at) for s, bars in self.bars.items()}
        self.lookahead_violations: list[str] = []

    def visible(self, symbol: str) -> list[Bar]:
        count = bisect.bisect_right(self._available[symbol], self.clock.now)
        return self.bars[symbol][:count]

    def _checked(self, symbol: str) -> list[Bar]:
        """Every public read goes through here: a bar not yet available is a hard error, never a value."""
        bars = self.visible(symbol)
        if bars and bars[-1].available_at > self.clock.now:
            message = f"{symbol} bar ending {bars[-1].end_at} served before it was available ({self.clock.now})"
            self.lookahead_violations.append(message)
            raise LookAheadError(message)
        return bars

    def recent_bars(self, symbol, cls, *, start, end, limit, timeframe="1Hour"):
        bars = [b for b in self._checked(symbol)[-max(limit, 1) * 2:] if start <= b.end_at <= end][-limit:]
        return bars, {"feed": f"REPLAY:{self.dataset}", "rows": len(bars)}

    def latest_quote(self, symbol, cls) -> Quote:
        bars = self._checked(symbol)
        if not bars:
            raise ValueError("quote missing")
        price, half = bars[-1].close, self.costs.half_spread(cls)
        now = self.clock.now
        return Quote(symbol, cls, price * (1 - half), price * (1 + half), now, now, f"REPLAY:{self.dataset}", 0.0)

    def last_close(self, symbol: str) -> float | None:
        bars = self._checked(symbol)
        return bars[-1].close if bars else None

    def fill_bar(self, symbol: str, submitted_at: datetime) -> Bar | None:
        """First bar starting at or after the order (minus a small grace for a bar that just began)."""
        bars = self._by_start[symbol]
        index = bisect.bisect_left(self._starts[symbol], submitted_at - FILL_GRACE)
        return bars[index] if index < len(bars) else None

    def bars_after(self, symbol: str, bar: Bar) -> list[Bar]:
        bars = self._by_start[symbol]
        return bars[bisect.bisect_right(self._starts[symbol], bar.start_at):]

    def schedule(self, start: datetime, end: datetime) -> list[datetime]:
        """Decision times: whenever a new bar becomes available, plus each stock session open for daily bars."""
        times: set[datetime] = set()
        for symbol, bars in self.bars.items():
            for bar in bars:
                if start <= bar.available_at <= end:
                    times.add(bar.available_at)
                if self.classes[symbol] == AssetClass.EQUITY and bar.end_at - bar.start_at > timedelta(hours=2) \
                        and start <= bar.start_at <= end:
                    times.add(bar.start_at)  # daily stock bars: decide at the open, fill at that open
        return sorted(times)


class ReplayBroker(BrokerAdapter):
    evidence_class = "BACKTEST"

    def __init__(self, clock: ReplayClock, data: ReplayData, costs: CostModel, *, cash: float):
        self.clock, self.data, self.costs = clock, data, costs
        self.cash = cash
        self.positions: dict[str, float] = {}
        self.orders: dict[str, BrokerOrder] = {}
        self.pending: dict[str, dict] = {}
        self.fills: list[dict] = []
        self._day, self._day_start_equity = None, cash

    def asset_eligible(self, asset_id: str, asset_class: AssetClass) -> bool:
        return asset_id in self.data.bars

    def equity_market_open(self) -> bool:
        local = self.clock.now.astimezone(NEW_YORK)
        return local.weekday() < 5 and time(9, 30) <= local.time() < time(16, 0)

    def _value(self) -> tuple[float, dict[str, float]]:
        values = {}
        for asset, quantity in self.positions.items():
            price = self.data.last_close(asset)
            values[asset] = quantity * (price or 0.0)
        return self.cash + sum(values.values()), values

    def state(self) -> BrokerState:
        equity, values = self._value()
        day = self.clock.now.astimezone(NEW_YORK).date()
        if day != self._day:
            self._day, self._day_start_equity = day, equity
        open_ids = tuple(k for k, v in self.orders.items() if v.status in ("ACCEPTED", "PARTIALLY_FILLED"))
        return BrokerState(self.cash, self.cash, equity, dict(self.positions), values, open_ids, reconciled=True,
                           daily_pnl=equity - self._day_start_equity)

    def find_order(self, client_order_id: str) -> BrokerOrder | None:
        return self.orders.get(client_order_id)

    def submit(self, client_order_id, asset_id, asset_class, side, quantity, reference_price) -> BrokerOrder:
        if client_order_id in self.orders:
            return self.orders[client_order_id]
        if quantity <= 0 or reference_price <= 0 or side not in ("BUY", "SELL"):
            raise BrokerError("invalid replay order")
        if side == "SELL" and quantity > self.positions.get(asset_id, 0) + 1e-9:
            raise BrokerError("replay sell exceeds position")
        order = BrokerOrder(client_order_id, f"replay_{len(self.orders) + 1}", asset_id, side, quantity, 0.0, None,
                            "ACCEPTED", self.clock.now)
        self.orders[client_order_id] = order
        self.pending[client_order_id] = {"class": asset_class, "limit": reference_price if side == "BUY" else None}
        self.step()
        return self.orders[client_order_id]

    def cancel(self, client_order_id: str) -> None:
        order = self.orders.get(client_order_id)
        if order is None:
            raise BrokerError("unknown replay order")
        if client_order_id in self.pending:
            del self.pending[client_order_id]
            self.orders[client_order_id] = replace(order, status="CANCELED")

    def step(self) -> None:
        """Fill working orders whose fill bar has started by now."""
        for client_id in list(self.pending):
            order, meta = self.orders[client_id], self.pending[client_id]
            bar = self.data.fill_bar(order.asset_id, order.submitted_at)
            while bar is not None and bar.start_at <= self.clock.now:
                price = self._fill_price(order.side, meta, bar)
                if price is not None:
                    self._fill(client_id, order, meta["class"], price, bar)
                    break
                following = self.data.bars_after(order.asset_id, bar)
                bar = following[0] if following else None

    def _fill_price(self, side: str, meta: dict, bar: Bar) -> float | None:
        half = self.costs.half_spread(meta["class"])
        if side == "SELL":
            return bar.open * (1 - half)
        limit, at_open = meta["limit"], bar.open * (1 + half)
        if at_open <= limit:
            return at_open
        if bar.low * (1 + half) <= limit:
            return limit  # the price traded down to the limit during the bar
        return None

    def _fill(self, client_id: str, order: BrokerOrder, cls: AssetClass, price: float, bar: Bar) -> None:
        quantity, fee = order.quantity, self.costs.fee(cls)
        if order.side == "BUY":
            cost = quantity * price * (1 + fee)
            if cost > self.cash + 1e-9:
                del self.pending[client_id]
                self.orders[client_id] = replace(order, status="REJECTED")
                return
            self.cash -= cost
            self.positions[order.asset_id] = self.positions.get(order.asset_id, 0.0) + quantity
        else:
            self.cash += quantity * price * (1 - fee)
            self.positions[order.asset_id] = self.positions.get(order.asset_id, 0.0) - quantity
        del self.pending[client_id]
        self.orders[client_id] = replace(order, filled_quantity=quantity, average_price=price, status="FILLED")
        self.fills.append({"client_order_id": client_id, "asset_id": order.asset_id, "side": order.side,
                           "quantity": quantity, "price": price, "bar_start": bar.start_at, "fee_rate": fee})

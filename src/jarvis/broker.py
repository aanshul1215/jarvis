"""Broker boundary. Mock is deterministic; Alpaca adapter is paper-only."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4

from .contracts import AssetClass, BrokerOrder, utc_now
from .risk import BrokerState


class BrokerError(RuntimeError):
    pass


class UncertainSubmission(BrokerError):
    """The broker may have accepted the order; lookup before retry."""


class BrokerAdapter(ABC):
    @abstractmethod
    def asset_eligible(self, asset_id: str, asset_class: AssetClass) -> bool: ...

    @abstractmethod
    def equity_market_open(self) -> bool: ...

    @abstractmethod
    def state(self) -> BrokerState: ...

    @abstractmethod
    def find_order(self, client_order_id: str) -> BrokerOrder | None: ...

    @abstractmethod
    def submit(self, client_order_id: str, asset_id: str, asset_class: AssetClass,
               side: str, quantity: float, reference_price: float) -> BrokerOrder: ...

    @abstractmethod
    def cancel(self, client_order_id: str) -> None: ...


class MockBroker(BrokerAdapter):
    def __init__(self, *, cash: float = 1000.0, fill_fraction: float = 1.0):
        if not 0 <= fill_fraction <= 1:
            raise ValueError("fill_fraction outside 0..1")
        self.cash = cash
        self.initial_cash = cash
        self.fill_fraction = fill_fraction
        self.positions: dict[str, float] = {}
        self.last_prices: dict[str, float] = {}
        self.orders: dict[str, BrokerOrder] = {}
        self.raise_after_accept = False

    def state(self) -> BrokerState:
        equity = self.cash + sum(q * self.last_prices.get(asset, 0) for asset, q in self.positions.items())
        return BrokerState(cash=self.cash, buying_power=self.cash, equity=equity,
                           positions=dict(self.positions),
                           position_values={asset: q * self.last_prices.get(asset, 0) for asset, q in self.positions.items()},
                           open_order_ids=tuple(k for k, v in self.orders.items() if v.status in ("PARTIALLY_FILLED", "ACCEPTED")),
                           reconciled=True, daily_pnl=0.0, drawdown=0.0)

    def find_order(self, client_order_id: str) -> BrokerOrder | None:
        return self.orders.get(client_order_id)

    def asset_eligible(self, asset_id: str, asset_class: AssetClass) -> bool:
        return bool(asset_id)

    def equity_market_open(self) -> bool:
        return True

    def submit(self, client_order_id: str, asset_id: str, asset_class: AssetClass,
               side: str, quantity: float, reference_price: float) -> BrokerOrder:
        if client_order_id in self.orders:
            return self.orders[client_order_id]
        if quantity <= 0 or reference_price <= 0 or side not in ("BUY", "SELL"):
            raise BrokerError("invalid mock order")
        filled = round(quantity * self.fill_fraction, 8)
        cost = filled * reference_price
        if side == "BUY" and cost > self.cash:
            raise BrokerError("insufficient mock cash")
        if side == "SELL" and filled > self.positions.get(asset_id, 0):
            raise BrokerError("insufficient mock position")
        if filled:
            self.cash += -cost if side == "BUY" else cost
            self.positions[asset_id] = self.positions.get(asset_id, 0) + (filled if side == "BUY" else -filled)
            self.last_prices[asset_id] = reference_price
        status = "FILLED" if filled == quantity else ("PARTIALLY_FILLED" if filled else "ACCEPTED")
        order = BrokerOrder(client_order_id, f"mock_{uuid4().hex}", asset_id, side, quantity,
                            filled, reference_price if filled else None, status, utc_now())
        self.orders[client_order_id] = order
        if self.raise_after_accept:
            self.raise_after_accept = False
            raise UncertainSubmission("mock timeout after acceptance")
        return order

    def cancel(self, client_order_id: str) -> None:
        old = self.orders.get(client_order_id)
        if old is None:
            raise BrokerError("unknown mock order")
        self.orders[client_order_id] = BrokerOrder(old.client_order_id, old.broker_order_id, old.asset_id, old.side,
                                                  old.quantity, old.filled_quantity, old.average_price,
                                                  "CANCELED", old.submitted_at)


class AlpacaPaperBroker(BrokerAdapter):
    """Official SDK wrapper. No live URL or live mode parameter is exposed."""

    def __init__(self, key_id: str, secret: str, *, enable_orders: bool = False):
        if not key_id or not secret:
            raise BrokerError("paper credentials required")
        from alpaca.trading.client import TradingClient

        self.client = TradingClient(key_id, secret, paper=True)
        self.enable_orders = enable_orders

    def state(self) -> BrokerState:
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        account = self.client.get_account()
        positions = self.client.get_all_positions()
        orders = self.client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN))
        if isinstance(account, dict):
            raise BrokerError("unexpected account response")
        return BrokerState(float(account.cash), float(account.buying_power), float(account.equity),
                           {p.symbol: float(p.qty) for p in positions},
                           {p.symbol: float(p.market_value) for p in positions},
                           tuple(o.client_order_id for o in orders if o.client_order_id),
                           reconciled=True)

    def find_order(self, client_order_id: str) -> BrokerOrder | None:
        from alpaca.common.exceptions import APIError

        try:
            result = self.client.get_order_by_client_id(client_order_id)
        except APIError as exc:
            if getattr(exc, "status_code", None) == 404:
                return None
            raise BrokerError("paper order lookup failed") from exc
        return BrokerOrder(client_order_id, str(result.id), result.symbol, result.side.value.upper(),
                           float(result.qty or 0), float(result.filled_qty or 0),
                           float(result.filled_avg_price) if result.filled_avg_price else None,
                           result.status.value.upper(), result.submitted_at or utc_now())

    def asset_eligible(self, asset_id: str, asset_class: AssetClass) -> bool:
        try:
            asset = self.client.get_asset(asset_id)
        except Exception:
            return False
        return bool(asset.tradable and asset.status.value == "active" and
                    ((asset_class == AssetClass.CRYPTO and asset.asset_class.value == "crypto") or
                     (asset_class == AssetClass.EQUITY and asset.asset_class.value == "us_equity")))

    def equity_market_open(self) -> bool:
        return bool(self.client.get_clock().is_open)

    def submit(self, client_order_id: str, asset_id: str, asset_class: AssetClass,
               side: str, quantity: float, reference_price: float) -> BrokerOrder:
        if not self.enable_orders:
            raise BrokerError("paper orders disabled; explicit enablement required")
        if not self.asset_eligible(asset_id, asset_class):
            raise BrokerError("asset eligibility unverified")
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

        existing = self.find_order(client_order_id)
        if existing is not None:
            return existing
        common = {"symbol": asset_id, "qty": quantity,
                  "side": OrderSide.BUY if side == "BUY" else OrderSide.SELL,
                  "time_in_force": TimeInForce.GTC if asset_class == AssetClass.CRYPTO else TimeInForce.DAY,
                  "client_order_id": client_order_id}
        req = LimitOrderRequest(**common, limit_price=round(reference_price, 2)) if side == "BUY" else MarketOrderRequest(**common)
        try:
            result = self.client.submit_order(req)
        except Exception as exc:
            raise UncertainSubmission("paper submission uncertain; reconcile by client order ID") from exc
        return BrokerOrder(client_order_id, str(result.id), result.symbol, side, quantity,
                           float(result.filled_qty or 0),
                           float(result.filled_avg_price) if result.filled_avg_price else None,
                           result.status.value.upper(), result.submitted_at or utc_now())

    def cancel(self, client_order_id: str) -> None:
        order = self.find_order(client_order_id)
        if order is None:
            raise BrokerError("order missing; cannot cancel")
        self.client.cancel_order_by_id(order.broker_order_id)

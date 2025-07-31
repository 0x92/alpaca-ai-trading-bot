from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType


@dataclass
class Portfolio:
    """Simple wrapper around Alpaca TradingClient for a single portfolio."""

    name: str
    api_key: str
    secret_key: str
    base_url: str
    history: List[Dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        paper = "paper" in self.base_url
        self.client = TradingClient(
            self.api_key, self.secret_key, paper=paper, url_override=self.base_url
        )

    def get_account_info(self):
        """Return basic account information as a dictionary."""
        account = self.client.get_account()
        # `model_dump` returns a dictionary on pydantic models
        return account.model_dump()

    def place_order(self, symbol: str, qty: float, side: str = "buy"):
        """Place a market order and store it in history."""
        side_enum = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side_enum,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
        )
        order = self.client.submit_order(order_data)
        self.history.append(order.model_dump())
        return order


class MultiPortfolioManager:
    """Manage multiple Portfolio instances."""

    def __init__(self, portfolios: List[Portfolio] | None = None):
        self.portfolios: List[Portfolio] = portfolios or []

    def add_portfolio(self, portfolio: Portfolio) -> None:
        self.portfolios.append(portfolio)

    def step_all(self):
        """Execute a dummy trade for all portfolios."""
        for p in self.portfolios:
            # simple dummy: place a single share order for AAPL
            try:
                p.place_order("AAPL", 1)
            except Exception as exc:
                # In a real system, logging should be used
                print(f"Failed to place order for {p.name}: {exc}")


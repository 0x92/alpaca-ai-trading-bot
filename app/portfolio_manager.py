from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime

import openai

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType

from .config import load_env
from .research_engine import get_research

ENV = load_env()
openai.api_key = ENV.get("OPENAI_API_KEY")


@dataclass
class Portfolio:
    """Simple wrapper around Alpaca TradingClient for a single portfolio."""

    name: str
    api_key: str
    secret_key: str
    base_url: str
    strategy_type: str = "default"
    history: List[Dict] = field(default_factory=list)
    equity_curve: List[Dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        paper = "paper" in self.base_url
        self.client = TradingClient(
            self.api_key, self.secret_key, paper=paper, url_override=self.base_url
        )

    def get_account_info(self):
        """Return basic account information as a dictionary."""
        account = self.client.get_account()
        # `model_dump` returns a dictionary on pydantic models
        info = account.model_dump()
        value = info.get("portfolio_value")
        if value is not None:
            self.equity_curve.append({"time": datetime.utcnow().isoformat(), "value": float(value)})
        return info

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


def get_strategy_from_openai(
    portfolio: Portfolio, research: dict, strategy_type: str = "default"
) -> str:
    """Return a trading instruction string from OpenAI."""
    if not openai.api_key or "your_openai_api_key" in openai.api_key:
        return f"no_api_key_for_{strategy_type}"

    account = portfolio.get_account_info()
    prompt = (
        "Provide a short trading decision (buy/sell/hold) for the next step.\n"
        f"Strategy: {strategy_type}\n"
        f"Portfolio: {json.dumps(account)}\n"
        f"Research: {json.dumps(research)}"
    )
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        return f"error: {exc}"


class MultiPortfolioManager:
    """Manage multiple Portfolio instances."""

    def __init__(self, portfolios: List[Portfolio] | None = None):
        self.portfolios: List[Portfolio] = portfolios or []

    def add_portfolio(self, portfolio: Portfolio) -> None:
        self.portfolios.append(portfolio)

    def step_all(self, symbol: str = "AAPL"):
        """Get research and ask OpenAI for a trade decision for each portfolio."""
        for p in self.portfolios:
            research = get_research(symbol)
            decision = get_strategy_from_openai(p, research, p.strategy_type)
            print(p.name, "decision", decision)
            if decision.lower().startswith("buy"):
                try:
                    p.place_order(symbol, 1, "buy")
                except Exception as exc:
                    print(f"Failed to place order for {p.name}: {exc}")
            elif decision.lower().startswith("sell"):
                try:
                    p.place_order(symbol, 1, "sell")
                except Exception as exc:
                    print(f"Failed to place order for {p.name}: {exc}")
            # record latest account value
            try:
                p.get_account_info()
            except Exception:
                pass


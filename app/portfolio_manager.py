from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Dict
from pathlib import Path
from datetime import datetime

import openai

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType

from .config import load_env
from .research_engine import get_research
from .logger import get_logger
from .benchmark import get_latest_benchmark_price, normalize_curve

logger = get_logger(__name__)

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
        try:
            account = self.client.get_account()
            info = account.model_dump()
            value = info.get("portfolio_value")
            if value is not None:
                self.equity_curve.append({"time": datetime.utcnow().isoformat(), "value": float(value)})
            return info
        except Exception as exc:
            logger.error("Failed to get account info for %s: %s", self.name, exc)
            return {}

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
        try:
            order = self.client.submit_order(order_data)
            self.history.append(order.model_dump())
            return order
        except Exception as exc:
            logger.error("Order failed for %s: %s", self.name, exc)
            raise


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
    except openai.error.RateLimitError:
        logger.warning("OpenAI rate limit reached for %s", portfolio.name)
        return "rate_limit"
    except Exception as exc:
        logger.error("OpenAI error for %s: %s", portfolio.name, exc)
        return f"error: {exc}"


class MultiPortfolioManager:
    """Manage multiple Portfolio instances."""

    def __init__(self, portfolios: List[Portfolio] | None = None, benchmark_symbol: str = "^spx"):
        self.portfolios: List[Portfolio] = portfolios or []
        self.benchmark_symbol = benchmark_symbol
        self.benchmark_curve: List[Dict] = []

    # --- Persistence helpers -------------------------------------------------
    def load_from_file(
        self,
        path: str | Path,
        api_key: str,
        secret_key: str,
        base_url: str,
    ) -> None:
        """Load portfolio definitions from JSON file."""
        file_path = Path(path)
        if not file_path.exists():
            return
        try:
            data = json.loads(file_path.read_text())
            self.portfolios = [
                Portfolio(
                    item.get("name"),
                    api_key,
                    secret_key,
                    base_url,
                    item.get("strategy_type", "default"),
                )
                for item in data
            ]
        except Exception:
            # ignore malformed json
            pass

    def save_to_file(self, path: str | Path) -> None:
        """Persist portfolio definitions (name + strategy) to JSON file."""
        file_path = Path(path)
        data = [
            {"name": p.name, "strategy_type": p.strategy_type}
            for p in self.portfolios
        ]
        file_path.write_text(json.dumps(data, indent=2))

    # -------------------------------------------------------------------------

    def add_portfolio(self, portfolio: Portfolio) -> None:
        self.portfolios.append(portfolio)

    def remove_portfolio(self, name: str) -> None:
        """Remove a portfolio by name."""
        self.portfolios = [p for p in self.portfolios if p.name != name]

    # --- Benchmark helpers ---------------------------------------------------
    def update_benchmark(self) -> None:
        """Fetch latest benchmark price and append to history."""
        data = get_latest_benchmark_price(self.benchmark_symbol)
        if data:
            self.benchmark_curve.append(data)

    def get_normalized_benchmark(self) -> List[Dict]:
        return normalize_curve(self.benchmark_curve)

    def get_normalized_equity(self, portfolio: Portfolio) -> List[Dict]:
        return normalize_curve(portfolio.equity_curve)

    def step_all(self, symbol: str = "AAPL"):
        """Get research and ask OpenAI for a trade decision for each portfolio."""
        self.update_benchmark()
        for p in self.portfolios:
            research = get_research(symbol)
            decision = get_strategy_from_openai(p, research, p.strategy_type)
            logger.info("%s decision %s", p.name, decision)
            if decision.lower().startswith("buy"):
                try:
                    p.place_order(symbol, 1, "buy")
                except Exception as exc:
                    logger.error("Failed to place order for %s: %s", p.name, exc)
            elif decision.lower().startswith("sell"):
                try:
                    p.place_order(symbol, 1, "sell")
                except Exception as exc:
                    logger.error("Failed to place order for %s: %s", p.name, exc)
            # record latest account value
            try:
                p.get_account_info()
            except Exception as exc:
                logger.error("Failed to fetch account info for %s: %s", p.name, exc)


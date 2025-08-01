from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional, Sequence, Union
from pathlib import Path
from datetime import datetime

import openai

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType

from .config import load_env
from .research_engine import get_ai_research, get_trending_symbols
from .logger import get_logger
from .benchmark import (
    get_latest_benchmark_price,
    get_latest_price,
    normalize_curve,
)
from .diversification import analyze_portfolio

logger = get_logger(__name__)

ENV = load_env()
openai.api_key = ENV.get("OPENAI_API_KEY")


activity_callback: Optional[Callable[[str, Dict], None]] = None


def set_activity_callback(cb: Optional[Callable[[str, Dict], None]]) -> None:
    """Register a callback for activity log events."""
    global activity_callback
    activity_callback = cb


@dataclass
class Portfolio:
    """Simple wrapper around Alpaca TradingClient for a single portfolio."""

    name: str
    api_key: str
    secret_key: str
    base_url: str
    strategy_type: str = "default"
    custom_prompt: str = ""
    history: List[Dict] = field(default_factory=list)
    equity_curve: List[Dict] = field(default_factory=list)
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.1
    max_drawdown_pct: float = 0.2
    trade_pnl_limit_pct: float = 0.05
    risk_level: float = 0.02  # fraction of cash to risk per trade
    holdings: Dict[str, float] = field(default_factory=dict)
    avg_prices: Dict[str, float] = field(default_factory=dict)
    risk_alerts: List[str] = field(default_factory=list)
    open_orders: List[Dict] = field(default_factory=list)
    correlation_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    diversification_score: float = 0.0
    diversification_warnings: List[str] = field(default_factory=list)
    activity_log: List[Dict] = field(default_factory=list)
    initial_value: float | None = None
    high_water: float = 0.0
    last_prompt: str = ""
    last_research: Dict | None = field(default_factory=dict)
    last_response: str = ""

    def __post_init__(self) -> None:
        paper = "paper" in self.base_url
        self.client = TradingClient(
            self.api_key, self.secret_key, paper=paper, url_override=self.base_url
        )

    def log_event(self, event_type: str, message: str) -> None:
        """Store an activity log entry and trigger callback."""
        entry = {
            "time": datetime.utcnow().isoformat(),
            "type": event_type,
            "message": message,
        }
        self.activity_log.append(entry)
        if activity_callback:
            try:
                activity_callback(self.name, entry)
            except Exception:
                pass

    def get_account_info(self):
        """Return basic account information as a dictionary."""
        try:
            account = self.client.get_account()
            info = account.model_dump()
            value = info.get("portfolio_value")
            if value is not None:
                self.equity_curve.append(
                    {"time": datetime.utcnow().isoformat(), "value": float(value)}
                )
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
            order_dict = order.model_dump()
            order_dict["notes"] = ""
            order_dict["tags"] = []
            if side.lower() == "buy":
                self.holdings[symbol] = self.holdings.get(symbol, 0) + qty
                price_info = get_latest_price(symbol)
                price = price_info.get("value")
                if price:
                    prev_qty = self.holdings.get(symbol, 0) - qty
                    if prev_qty > 0 and symbol in self.avg_prices:
                        avg = (self.avg_prices[symbol] * prev_qty + price * qty) / (
                            prev_qty + qty
                        )
                        self.avg_prices[symbol] = avg
                    else:
                        self.avg_prices[symbol] = price
            else:
                avg_price = self.avg_prices.get(symbol, 0)
                filled = float(order_dict.get("filled_avg_price") or 0)
                order_dict["pnl"] = (filled - avg_price) * qty
                if symbol in self.holdings:
                    self.holdings.pop(symbol, None)
                    self.avg_prices.pop(symbol, None)
            order_dict["decision_explainer"] = {
                "prompt": self.last_prompt,
                "research": self.last_research,
                "response": self.last_response,
            }
            self.history.append(order_dict)
            self.log_event("trade", f"{side} {qty} {symbol}")

            # check realized pnl against limit on sell orders
            if side.lower() == "sell" and "pnl" in order_dict:
                account = self.get_account_info()
                value = float(account.get("portfolio_value") or 0)
                pnl = float(order_dict.get("pnl") or 0)
                if value > 0:
                    pnl_pct = abs(pnl) / value
                    if pnl_pct >= self.trade_pnl_limit_pct:
                        alert = f"Trade PnL {pnl:.2f} exceeded limit"
                        self.risk_alerts.append(alert)
                        self.log_event("alert", alert)
            return order
        except Exception as exc:
            logger.error("Order failed for %s: %s", self.name, exc)
            raise

    def smart_allocation(self, symbol: str) -> float:
        """Determine position size based on risk level and latest price."""
        info = self.get_account_info()
        cash = float(info.get("cash") or 0)
        price_info = get_latest_price(symbol)
        price = price_info.get("value", 0)
        if price == 0:
            return 0.0
        allocation = cash * self.risk_level
        qty = allocation / price
        return round(max(qty, 0), 4)

    def get_positions(self) -> List[Dict]:
        """Return a list of open positions with live PnL information."""
        positions = []
        for sym, qty in self.holdings.items():
            price_info = get_latest_price(sym)
            price = price_info.get("value")
            avg = self.avg_prices.get(sym, 0)
            if price is None or avg == 0:
                continue
            pnl = (price - avg) * qty
            pnl_pct = (price - avg) / avg if avg else 0
            positions.append(
                {
                    "symbol": sym,
                    "qty": qty,
                    "price": price,
                    "avg_price": avg,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                }
            )
        return positions

    def get_orders(self, status: str = "open") -> List[Dict]:
        """Return orders with the given status using the Alpaca API."""
        try:
            orders = self.client.get_orders(status=status)
            return [o.model_dump() for o in orders]
        except Exception as exc:
            logger.error("Failed to fetch orders for %s: %s", self.name, exc)
            return []

    def refresh_open_orders(self) -> None:
        """Update cached list of open orders."""
        self.open_orders = self.get_orders(status="open")

    def get_allocation(self) -> List[Dict]:
        """Return current allocation including cash as percentage per asset."""
        info = self.get_account_info()
        cash = float(info.get("cash") or 0)
        total_value = float(info.get("portfolio_value") or 0)
        holdings_data: List[Dict] = []
        total_positions = cash
        for sym, qty in self.holdings.items():
            price_info = get_latest_price(sym)
            price = price_info.get("value")
            if price is None:
                continue
            value = qty * price
            total_positions += value
            holdings_data.append({"symbol": sym, "value": value})

        # fall back to sum if portfolio value not available
        if total_value <= 0:
            total_value = total_positions

        allocation = []
        for item in holdings_data:
            pct = item["value"] / total_value * 100 if total_value else 0.0
            allocation.append({"symbol": item["symbol"], "percent": pct})
        if cash > 0:
            pct = cash / total_value * 100 if total_value else 0.0
            allocation.append({"symbol": "CASH", "percent": pct})
        allocation.sort(key=lambda x: x["percent"], reverse=True)
        return allocation

    def get_pnl_history(self, interval: str = "day") -> List[Dict]:
        """Return PnL time series aggregated by interval."""
        if not self.equity_curve:
            return []
        try:
            import pandas as pd

            df = pd.DataFrame(self.equity_curve)
            df["time"] = pd.to_datetime(df["time"])
            df = df.set_index("time")
            rule = {"week": "W", "month": "M"}.get(interval, "D")
            values = df["value"].resample(rule).last()
            pnl = values.diff().fillna(0)
            return [{"time": t.isoformat(), "pnl": float(v)} for t, v in pnl.items()]
        except Exception as exc:
            logger.error("Failed to compute pnl history for %s: %s", self.name, exc)
            return []

    def get_top_flop_trades(self, limit: int = 5) -> Dict[str, List[Dict]]:
        """Return lists of top and flop trades by PnL."""
        sells = []
        for trade in self.history:
            if trade.get("side") == "sell":
                pnl = trade.get("pnl")
                if pnl is None:
                    qty = float(trade.get("qty") or 0)
                    filled = float(trade.get("filled_avg_price") or 0)
                    symbol = trade.get("symbol")
                    buy_avg = 0.0
                    for t in self.history:
                        if (
                            t.get("side") == "buy"
                            and t.get("symbol") == symbol
                            and float(t.get("qty") or 0) == qty
                        ):
                            buy_avg = float(t.get("filled_avg_price") or 0)
                            break
                    pnl = (filled - buy_avg) * qty
                sells.append({"symbol": trade.get("symbol"), "pnl": pnl})
        if not sells:
            return {"top": [], "flop": []}
        sells.sort(key=lambda x: x["pnl"])
        flop = sells[:limit]
        top = sells[-limit:][::-1]
        return {"top": top, "flop": flop}

    def check_risk(
        self, account_value: float | None = None, simulate: bool = False
    ) -> None:
        """Check risk parameters and act if limits are hit."""
        if account_value is None:
            info = self.get_account_info()
            value = info.get("portfolio_value")
            if value is None:
                return
            account_value = float(value)
        if self.initial_value is None:
            self.initial_value = account_value
            self.high_water = account_value
            return
        self.high_water = max(self.high_water, account_value)
        drawdown = (self.high_water - account_value) / self.high_water
        if drawdown >= self.max_drawdown_pct:
            alert = f"Max drawdown {drawdown:.2%} exceeded"
            self.risk_alerts.append(alert)
            self.log_event("alert", alert)
            if (
                not simulate
                and self.api_key
                and "your_alpaca_api_key" not in self.api_key
            ):
                try:
                    self.client.close_all_positions(cancel_orders=True)
                except Exception as exc:
                    logger.error("Failed to close positions for %s: %s", self.name, exc)
        for symbol, qty in list(self.holdings.items()):
            price_info = get_latest_price(symbol)
            price = price_info.get("value")
            avg = self.avg_prices.get(symbol)
            if not price or not avg:
                continue
            change = (price - avg) / avg
            if change <= -self.stop_loss_pct:
                alert = f"Stop-loss triggered for {symbol}"
                self.risk_alerts.append(alert)
                self.log_event("alert", alert)
                if not simulate:
                    try:
                        self.place_order(symbol, qty, "sell")
                    except Exception as exc:
                        logger.error(
                            "Stop-loss order failed for %s: %s", self.name, exc
                        )
                self.holdings.pop(symbol, None)
                self.avg_prices.pop(symbol, None)
            elif change >= self.take_profit_pct:
                alert = f"Take-profit triggered for {symbol}"
                self.risk_alerts.append(alert)
                self.log_event("alert", alert)
                if not simulate:
                    try:
                        self.place_order(symbol, qty, "sell")
                    except Exception as exc:
                        logger.error(
                            "Take-profit order failed for %s: %s", self.name, exc
                        )
                self.holdings.pop(symbol, None)
                self.avg_prices.pop(symbol, None)

    def find_trade(self, trade_id: str) -> Optional[Dict]:
        """Return trade dictionary matching id or None."""
        for trade in self.history:
            tid = str(trade.get("id") or trade.get("client_order_id"))
            if tid == trade_id:
                return trade
        return None

    def set_trade_notes(self, trade_id: str, notes: str) -> bool:
        """Set notes for a given trade."""
        trade = self.find_trade(trade_id)
        if not trade:
            return False
        trade["notes"] = notes
        return True

    def set_trade_tags(self, trade_id: str, tags: List[str]) -> bool:
        """Set tags list for a trade."""
        trade = self.find_trade(trade_id)
        if not trade:
            return False
        trade["tags"] = tags
        return True


def get_strategy_from_openai(
    portfolio: Portfolio, research: dict, strategy_type: str = "default"
) -> str:
    """Return a trading instruction string from OpenAI."""
    if not openai.api_key or "your_openai_api_key" in openai.api_key:
        return f"no_api_key_for_{strategy_type}"

    account = portfolio.get_account_info()
    if portfolio.custom_prompt:
        try:
            prompt = portfolio.custom_prompt.format(
                strategy_type=strategy_type,
                portfolio=json.dumps(account, default=str),
                research=json.dumps(research, default=str),
            )
        except Exception as exc:
            logger.error(
                "Failed to format custom prompt for %s: %s", portfolio.name, exc
            )
            prompt = portfolio.custom_prompt
    else:
        prompt = (
            "Provide a short trading decision (buy/sell/hold) for the next step.\n"
            f"Strategy: {strategy_type}\n"
            f"Portfolio: {json.dumps(account, default=str)}\n"
            f"Research: {json.dumps(research, default=str)}"
        )
    portfolio.last_prompt = prompt
    portfolio.last_research = research
    portfolio.log_event("prompt", prompt)
    try:
        client = openai.OpenAI(api_key=openai.api_key)
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        decision = resp.choices[0].message.content.strip()
        portfolio.last_response = decision
        portfolio.log_event("response", decision)
        return decision
    except openai.RateLimitError:
        logger.warning("OpenAI rate limit reached for %s", portfolio.name)
        portfolio.last_response = "rate_limit"
        portfolio.log_event("response", "rate_limit")
        return "rate_limit"
    except Exception as exc:
        logger.error("OpenAI error for %s: %s", portfolio.name, exc)
        portfolio.last_response = f"error: {exc}"
        portfolio.log_event("response", f"error: {exc}")
        return f"error: {exc}"


class MultiPortfolioManager:
    """Manage multiple Portfolio instances."""

    def __init__(
        self, portfolios: List[Portfolio] | None = None, benchmark_symbol: str = "^spx"
    ):
        self.portfolios: List[Portfolio] = portfolios or []
        self.benchmark_symbol = benchmark_symbol
        self.benchmark_curve: List[Dict] = []

    # --- Persistence helpers -------------------------------------------------
    def load_from_file(self, path: str | Path) -> None:
        """Load portfolio definitions including credentials from JSON file."""
        file_path = Path(path)
        if not file_path.exists():
            return
        try:
            data = json.loads(file_path.read_text())
        except Exception:
            return

        self.portfolios = []
        for item in data:
            try:
                p = Portfolio(
                    item.get("name"),
                    item.get("api_key", ""),
                    item.get("secret_key", ""),
                    item.get("base_url", ENV.get("ALPACA_BASE_URL")),
                    item.get("strategy_type", "default"),
                    item.get("custom_prompt", ""),
                )
                self.add_portfolio(p)
            except Exception:
                continue

    def save_to_file(self, path: str | Path) -> None:
        """Persist portfolio definitions (name + strategy) to JSON file."""
        file_path = Path(path)
        data = [
            {
                "name": p.name,
                "strategy_type": p.strategy_type,
                "custom_prompt": p.custom_prompt,
                "api_key": p.api_key,
                "secret_key": p.secret_key,
                "base_url": p.base_url,
            }
            for p in self.portfolios
        ]
        file_path.write_text(json.dumps(data, indent=2))

    # -------------------------------------------------------------------------

    def add_portfolio(self, portfolio: Portfolio) -> None:
        """Add a portfolio ensuring unique and valid API credentials."""
        if (
            not portfolio.api_key
            or not portfolio.secret_key
            or "your_alpaca_api_key" in portfolio.api_key
            or "your_alpaca_secret_key" in portfolio.secret_key
        ):
            raise ValueError("invalid_api_credentials")
        for p in self.portfolios:
            if p.api_key == portfolio.api_key and p.secret_key == portfolio.secret_key:
                raise ValueError("duplicate_api_credentials")
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

    def step_all(self, symbols: Union[str, Sequence[str], None] = None):
        """Get research and ask OpenAI for trade decisions for each portfolio."""
        self.update_benchmark()

        if symbols is None or (isinstance(symbols, str) and symbols.lower() == "auto"):
            symbols_list = get_trending_symbols()
        else:
            symbols_list = [symbols] if isinstance(symbols, str) else list(symbols)

        for symbol in symbols_list:
            for p in self.portfolios:
                research = get_ai_research(symbol)
                topics = [k for k in research.keys() if k != "symbol"]
                p.log_event("research", f"fetched {', '.join(topics)} for {symbol}")
                decision = get_strategy_from_openai(p, research, p.strategy_type)
                p.log_event("decision", decision)
                logger.info("%s decision %s", p.name, decision)
                if decision.lower().startswith("buy"):
                    qty = p.smart_allocation(symbol)
                    if qty > 0:
                        try:
                            p.place_order(symbol, qty, "buy")
                        except Exception as exc:
                            logger.error(
                                "Failed to place order for %s: %s", p.name, exc
                            )
                elif decision.lower().startswith("sell"):
                    qty = p.holdings.get(symbol, 0)
                    if qty > 0:
                        try:
                            p.place_order(symbol, qty, "sell")
                        except Exception as exc:
                            logger.error(
                                "Failed to place order for %s: %s", p.name, exc
                            )
                # record latest account value
                try:
                    info = p.get_account_info()
                    value = info.get("portfolio_value")
                    if value is not None:
                        p.check_risk(float(value))
                except Exception as exc:
                    logger.error("Failed to fetch account info for %s: %s", p.name, exc)

    def buy_opportunities(self, symbols: Union[str, Sequence[str], None] = None) -> None:
        """Scan symbols for buy signals only and execute market orders."""
        self.update_benchmark()

        if symbols is None or (isinstance(symbols, str) and symbols.lower() == "auto"):
            symbols_list = get_trending_symbols()
        else:
            symbols_list = [symbols] if isinstance(symbols, str) else list(symbols)

        for symbol in symbols_list:
            for p in self.portfolios:
                research = get_ai_research(symbol)
                topics = [k for k in research.keys() if k != "symbol"]
                p.log_event("research", f"fetched {', '.join(topics)} for {symbol}")
                decision = get_strategy_from_openai(p, research, p.strategy_type)
                p.log_event("decision", decision)
                logger.info("%s decision %s", p.name, decision)
                if decision.lower().startswith("buy"):
                    qty = p.smart_allocation(symbol)
                    if qty > 0:
                        try:
                            p.place_order(symbol, qty, "buy")
                        except Exception as exc:
                            logger.error("Failed to place order for %s: %s", p.name, exc)
                try:
                    info = p.get_account_info()
                    value = info.get("portfolio_value")
                    if value is not None:
                        p.check_risk(float(value))
                except Exception as exc:
                    logger.error("Failed to fetch account info for %s: %s", p.name, exc)

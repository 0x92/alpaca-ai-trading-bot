from pathlib import Path
from datetime import datetime, timedelta

from flask import Flask, render_template, redirect, url_for, request, send_file
from flask_socketio import SocketIO

from app.logger import get_logger

from app.config import load_env
from app.portfolio_manager import (
    Portfolio,
    MultiPortfolioManager,
    get_strategy_from_openai,
    set_activity_callback,
)
from app.research_engine import get_research
from app.reporting import export_trades_csv, generate_reports
from app.diversification import analyze_portfolio
from app.price_history import get_price_history

ENV = load_env()
API_KEY = ENV.get("ALPACA_API_KEY")
SECRET_KEY = ENV.get("ALPACA_SECRET_KEY")
BASE_URL = ENV.get("ALPACA_BASE_URL")
PORTFOLIO_FILE = Path("portfolios.json")

manager = MultiPortfolioManager()
logger = get_logger(__name__)

# load persisted portfolios or create defaults if none exist
manager.load_from_file(PORTFOLIO_FILE, API_KEY, SECRET_KEY, BASE_URL)
if not manager.portfolios and API_KEY and "your_alpaca_api_key" not in API_KEY:
    manager.add_portfolio(Portfolio("P1", API_KEY, SECRET_KEY, BASE_URL))
    manager.add_portfolio(Portfolio("P2", API_KEY, SECRET_KEY, BASE_URL))
    manager.save_to_file(PORTFOLIO_FILE)

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")
set_activity_callback(lambda name, evt: socketio.emit("activity_update", {"name": name, "event": evt}, broadcast=True))

# placeholders required for custom prompts
REQUIRED_PLACEHOLDERS = ["{strategy_type}", "{portfolio}", "{research}"]


def validate_prompt(prompt: str) -> bool:
    """Basic validation for a custom prompt."""
    if not prompt or len(prompt) > 1000:
        return False
    return all(ph in prompt for ph in REQUIRED_PLACEHOLDERS)


def _portfolio_snapshot():
    manager.update_benchmark()
    bench = manager.get_normalized_benchmark()
    data = []
    for p in manager.portfolios:
        try:
            info = p.get_account_info()
            cash = info.get("cash")
            value = info.get("portfolio_value")
        except Exception as exc:
            logger.error("Failed to get info for %s: %s", p.name, exc)
            cash = "N/A"
            value = "N/A"
        p.refresh_open_orders()
        divers = analyze_portfolio(p)
        p.correlation_matrix = divers["matrix"]
        p.diversification_score = divers["score"]
        p.diversification_warnings = divers["warnings"]
        data.append(
            {
                "name": p.name,
                "cash": cash,
                "portfolio_value": value,
                "positions": p.get_positions(),
                "history": p.history[-5:],
                "open_orders": p.open_orders,
                "allocation": p.get_allocation(),
                "equity": p.equity_curve[-50:],
                "equity_norm": manager.get_normalized_equity(p)[-50:],
                "benchmark": bench[-50:],
                "strategy_type": p.strategy_type,
                "custom_prompt": p.custom_prompt,
                "risk_alerts": p.risk_alerts[-5:] + p.diversification_warnings,
                "stop_loss_pct": p.stop_loss_pct,
                "take_profit_pct": p.take_profit_pct,
                "max_drawdown_pct": p.max_drawdown_pct,
                "diversification_score": p.diversification_score,
                "correlation": p.correlation_matrix,
            }
        )
    return data


@app.route("/")
def index():
    portfolios = _portfolio_snapshot()
    return render_template("dashboard.html", portfolios=portfolios)


@app.route("/step", methods=["POST"])
def step():
    logger.info("Running simulation step")
    manager.step_all()
    portfolios = _portfolio_snapshot()
    socketio.emit("trade_update", portfolios, broadcast=True)
    return redirect(url_for("index"))


@app.route("/portfolio/<name>/set_strategy", methods=["POST"])
def set_strategy(name: str):
    strategy = request.form.get("strategy_type", "default")
    for p in manager.portfolios:
        if p.name == name:
            p.strategy_type = strategy
            p.log_event("strategy", f"set to {strategy}")
            break
    manager.save_to_file(PORTFOLIO_FILE)
    logger.info("Set strategy for %s to %s", name, strategy)
    return redirect(url_for("index"))


@app.route("/portfolio/<name>/set_prompt", methods=["POST"])
def set_prompt(name: str):
    prompt = request.form.get("custom_prompt", "")
    if not validate_prompt(prompt):
        return "Invalid prompt", 400
    for p in manager.portfolios:
        if p.name == name:
            p.custom_prompt = prompt
            p.log_event("prompt", "updated custom prompt")
            break
    manager.save_to_file(PORTFOLIO_FILE)
    logger.info("Updated custom prompt for %s", name)
    return redirect(url_for("index"))


@app.route("/portfolio/<name>/preview_prompt", methods=["POST"])
def preview_prompt(name: str):
    prompt = request.form.get("custom_prompt", "")
    if not validate_prompt(prompt):
        return "Invalid prompt", 400
    symbol = request.form.get("symbol", "AAPL")
    research = get_research(symbol)
    temp_portfolio = None
    for p in manager.portfolios:
        if p.name == name:
            temp_portfolio = p
            break
    if temp_portfolio is None:
        return "Unknown portfolio", 404
    original_prompt = temp_portfolio.custom_prompt
    temp_portfolio.custom_prompt = prompt
    decision = get_strategy_from_openai(
        temp_portfolio, research, temp_portfolio.strategy_type
    )
    temp_portfolio.custom_prompt = original_prompt
    return decision


@app.route("/api/portfolio/<name>/orders")
def api_orders(name: str):
    """Return orders for a portfolio filtered by status."""
    status = request.args.get("status", "open")
    for p in manager.portfolios:
        if p.name == name:
            return {"orders": p.get_orders(status=status)}
    return {"orders": []}


@app.route("/api/portfolio/<name>/allocation")
def api_allocation(name: str):
    """Return current asset allocation for a portfolio."""
    for p in manager.portfolios:
        if p.name == name:
            return {"allocation": p.get_allocation()}
    return {"allocation": []}


@app.route("/api/portfolio/<name>/trade_history")
def api_trade_history(name: str):
    """Return trade history for a portfolio with optional filtering."""
    symbol = request.args.get("symbol")
    side = request.args.get("side")
    limit = request.args.get("limit", type=int)
    for p in manager.portfolios:
        if p.name == name:
            trades = p.history
            if symbol:
                trades = [t for t in trades if t.get("symbol") == symbol]
            if side:
                trades = [t for t in trades if t.get("side") == side]
            if limit:
                trades = trades[-limit:]
            buy = sum(1 for t in trades if t.get("side") == "buy")
            sell = sum(1 for t in trades if t.get("side") == "sell")
            summary = {"count": len(trades), "buy_count": buy, "sell_count": sell}
            return {"trades": trades, "summary": summary}
    return {"trades": [], "summary": {}}


@app.route("/api/portfolio/<name>/activity_log")
def api_activity_log(name: str):
    """Return activity log for a portfolio."""
    type_filter = request.args.get("type", "all")
    limit = request.args.get("limit", type=int) or 100
    for p in manager.portfolios:
        if p.name == name:
            events = p.activity_log
            if type_filter == "trades":
                events = [e for e in events if e.get("type") == "trade"]
            elif type_filter == "alerts":
                events = [e for e in events if e.get("type") == "alert"]
            return {"log": events[-limit:]}
    return {"log": []}


@app.route("/api/portfolio/<name>/pnl_history")
def api_pnl_history(name: str):
    """Return pnl history and top/flop trades for a portfolio."""
    interval = request.args.get("interval", "day")
    for p in manager.portfolios:
        if p.name == name:
            return {
                "pnl": p.get_pnl_history(interval=interval),
                **p.get_top_flop_trades(),
            }
    return {"pnl": [], "top": [], "flop": []}


@app.route("/api/trade/<trade_id>/price_history")
def api_trade_price_history(trade_id: str):
    """Return price history for a trade identified by its id."""
    for p in manager.portfolios:
        for trade in p.history:
            tid = str(trade.get("id") or trade.get("client_order_id"))
            if tid == trade_id:
                symbol = trade.get("symbol")
                submitted = trade.get("submitted_at") or trade.get("created_at")
                filled = trade.get("filled_at") or submitted
                if not symbol or not submitted:
                    break
                try:
                    start = datetime.fromisoformat(str(submitted))
                except ValueError:
                    start = datetime.utcnow()
                try:
                    end = datetime.fromisoformat(str(filled))
                except ValueError:
                    end = start
                # fetch a few extra days around the trade
                start = start - timedelta(days=1)
                end = end + timedelta(days=1)
                prices = get_price_history(symbol, start, end)
                return {"symbol": symbol, "prices": prices}
    return {"symbol": "", "prices": []}


@app.route("/portfolio/create", methods=["POST"])
def create_portfolio():
    name = request.form.get("name")
    strategy = request.form.get("strategy_type", "default")
    if name:
        manager.add_portfolio(Portfolio(name, API_KEY, SECRET_KEY, BASE_URL, strategy))
        manager.save_to_file(PORTFOLIO_FILE)
        logger.info("Created portfolio %s", name)
    return redirect(url_for("index"))


@app.route("/portfolio/<name>/delete", methods=["POST"])
def delete_portfolio(name: str):
    manager.remove_portfolio(name)
    manager.save_to_file(PORTFOLIO_FILE)
    logger.info("Deleted portfolio %s", name)
    return redirect(url_for("index"))


@app.route("/portfolio/<name>/export")
def export_trades(name: str):
    for p in manager.portfolios:
        if p.name == name:
            paths = export_trades_csv([p])
            if paths:
                return send_file(paths[0], as_attachment=True)
    return redirect(url_for("index"))


@app.route("/portfolio/<name>/report")
def get_report(name: str):
    for p in manager.portfolios:
        if p.name == name:
            paths = generate_reports([p])
            if paths:
                return send_file(paths[0], as_attachment=True)
    return redirect(url_for("index"))


if __name__ == "__main__":
    socketio.run(app, debug=True)

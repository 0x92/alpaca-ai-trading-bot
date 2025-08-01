from pathlib import Path

from flask import Flask, render_template, redirect, url_for, request, send_file
from flask_socketio import SocketIO

from app.logger import get_logger

from app.config import load_env
from app.portfolio_manager import (
    Portfolio,
    MultiPortfolioManager,
    get_strategy_from_openai,
)
from app.research_engine import get_research
from app.reporting import export_trades_csv, generate_reports
from app.diversification import analyze_portfolio

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

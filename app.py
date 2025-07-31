from pathlib import Path

from flask import Flask, render_template, redirect, url_for, request
from flask_socketio import SocketIO

from app.logger import get_logger

from app.config import load_env
from app.portfolio_manager import Portfolio, MultiPortfolioManager

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


def _portfolio_snapshot():
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
        data.append({
            "name": p.name,
            "cash": cash,
            "portfolio_value": value,
            "history": p.history[-5:],
            "equity": p.equity_curve[-50:],
            "strategy_type": p.strategy_type,
        })
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


if __name__ == "__main__":
    socketio.run(app, debug=True)

from flask import Flask, render_template, redirect, url_for
from flask_socketio import SocketIO

from app.config import load_env
from app.portfolio_manager import Portfolio, MultiPortfolioManager

ENV = load_env()
API_KEY = ENV.get("ALPACA_API_KEY")
SECRET_KEY = ENV.get("ALPACA_SECRET_KEY")
BASE_URL = ENV.get("ALPACA_BASE_URL")

manager = MultiPortfolioManager()

# Only create live portfolios if proper credentials are provided
if API_KEY and "your_alpaca_api_key" not in API_KEY:
    manager.add_portfolio(Portfolio("P1", API_KEY, SECRET_KEY, BASE_URL))
    manager.add_portfolio(Portfolio("P2", API_KEY, SECRET_KEY, BASE_URL))

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")


def _portfolio_snapshot():
    data = []
    for p in manager.portfolios:
        try:
            info = p.get_account_info()
            cash = info.get("cash")
            value = info.get("portfolio_value")
        except Exception:
            cash = "N/A"
            value = "N/A"
        data.append({
            "name": p.name,
            "cash": cash,
            "portfolio_value": value,
            "history": p.history[-5:],
        })
    return data


@app.route("/")
def index():
    portfolios = _portfolio_snapshot()
    return render_template("dashboard.html", portfolios=portfolios)


@app.route("/step", methods=["POST"])
def step():
    manager.step_all()
    portfolios = _portfolio_snapshot()
    socketio.emit("trade_update", portfolios, broadcast=True)
    return redirect(url_for("index"))


if __name__ == "__main__":
    socketio.run(app, debug=True)

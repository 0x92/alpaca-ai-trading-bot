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
from app.reporting import (
    export_trades_csv,
    generate_reports,
    export_dashboard_data,
)
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
manager.load_from_file(PORTFOLIO_FILE)
if not manager.portfolios and API_KEY and "your_alpaca_api_key" not in API_KEY:
    try:
        manager.add_portfolio(Portfolio("P1", API_KEY, SECRET_KEY, BASE_URL))
        manager.save_to_file(PORTFOLIO_FILE)
    except ValueError:
        pass

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")
# broadcast activity updates to all connected clients
set_activity_callback(
    lambda name, evt: socketio.emit(
        "activity_update",
        {"name": name, "event": evt},
    )
)

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
                "key_hint": (p.api_key[:4] + "***") if p.api_key else "",
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
                "trade_pnl_limit_pct": p.trade_pnl_limit_pct,
                "diversification_score": p.diversification_score,
                "correlation": p.correlation_matrix,
            }
        )
    return data


@app.route("/")
def index():
    portfolios = _portfolio_snapshot()
    return render_template("dashboard.html", portfolios=portfolios)


@app.route("/compare")
def compare_view():
    names_param = request.args.get("names", "")
    names = [n.strip() for n in names_param.split(",") if n.strip()] or [
        p.name for p in manager.portfolios
    ]
    return render_template("compare.html", names=names)


@app.route("/step", methods=["POST"])
def step():
    logger.info("Running simulation step")
    manager.step_all()
    portfolios = _portfolio_snapshot()
    # notify all connected clients with the latest portfolio snapshot
    socketio.emit("trade_update", portfolios)
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


@app.route("/portfolio/<name>/set_alerts", methods=["POST"])
def set_alerts(name: str):
    """Update alert threshold settings for a portfolio."""
    sl = request.form.get("stop_loss_pct", type=float)
    tp = request.form.get("take_profit_pct", type=float)
    dd = request.form.get("max_drawdown_pct", type=float)
    pnl = request.form.get("trade_pnl_limit_pct", type=float)
    for p in manager.portfolios:
        if p.name == name:
            if sl is not None:
                p.stop_loss_pct = sl
            if tp is not None:
                p.take_profit_pct = tp
            if dd is not None:
                p.max_drawdown_pct = dd
            if pnl is not None:
                p.trade_pnl_limit_pct = pnl
            p.log_event("config", "updated alert thresholds")
            break
    manager.save_to_file(PORTFOLIO_FILE)
    logger.info("Updated alerts for %s", name)
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


@app.route("/api/portfolio/<name>/alerts")
def api_alerts(name: str):
    """Return risk alerts for a portfolio."""
    for p in manager.portfolios:
        if p.name == name:
            return {"alerts": p.risk_alerts}
    return {"alerts": []}


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


@app.route("/api/portfolio/<name>/export")
def api_export_portfolio(name: str):
    """Export dashboard data in various formats."""
    fmt = request.args.get("format", "json")
    for p in manager.portfolios:
        if p.name == name:
            if fmt == "json":
                data = export_dashboard_data(p, manager, "json")
                return data
            try:
                path = export_dashboard_data(p, manager, fmt, "reports")
            except ValueError:
                return {"error": "invalid format"}, 400
            return send_file(path, as_attachment=True)
    return {"error": "not_found"}, 404


@app.route("/api/portfolios/compare")
def api_compare_portfolios():
    """Return key metrics for multiple portfolios."""
    names_param = request.args.get("names", "")
    names = [n.strip() for n in names_param.split(",") if n.strip()] or [
        p.name for p in manager.portfolios
    ]
    bench = manager.get_normalized_benchmark()[-50:]
    result = []
    for p in manager.portfolios:
        if p.name not in names:
            continue
        info = p.get_account_info()
        value = float(info.get("portfolio_value") or 0)
        cash = float(info.get("cash") or 0)
        pnl = 0.0
        if len(p.equity_curve) >= 2:
            pnl = float(p.equity_curve[-1]["value"])
            pnl -= float(p.equity_curve[0]["value"])
        result.append(
            {
                "name": p.name,
                "portfolio_value": value,
                "cash": cash,
                "pnl": pnl,
                "allocation": p.get_allocation(),
                "equity_norm": manager.get_normalized_equity(p)[-50:],
                "risk_alerts": p.risk_alerts[-5:],
            }
        )
    return {"bench": bench, "portfolios": result}


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


@app.route("/api/trade/<trade_id>/decision_explainer")
def api_trade_decision_explainer(trade_id: str):
    """Return stored prompt, research and AI response for a trade."""
    for p in manager.portfolios:
        for trade in p.history:
            tid = str(trade.get("id") or trade.get("client_order_id"))
            if tid == trade_id:
                data = trade.get("decision_explainer") or {}
                return data
    return {}


@app.route("/api/trade/<trade_id>/notes", methods=["GET", "POST", "DELETE"])
def api_trade_notes(trade_id: str):
    """Manage notes for a trade."""
    for p in manager.portfolios:
        trade = p.find_trade(trade_id) if hasattr(p, "find_trade") else None
        if trade:
            if request.method == "GET":
                return {"notes": trade.get("notes", "")}
            elif request.method == "POST":
                data = request.get_json(silent=True) or {}
                notes = data.get("notes") or request.form.get("notes", "")
                p.set_trade_notes(trade_id, notes)
                p.log_event("note", f"updated trade {trade_id} note")
                return {"notes": notes}
            else:
                p.set_trade_notes(trade_id, "")
                p.log_event("note", f"deleted trade {trade_id} note")
                return {"notes": ""}
    return {"notes": ""}, 404


@app.route("/api/trade/<trade_id>/tags", methods=["GET", "POST", "DELETE"])
def api_trade_tags(trade_id: str):
    """Manage tags for a trade."""
    for p in manager.portfolios:
        trade = p.find_trade(trade_id) if hasattr(p, "find_trade") else None
        if trade:
            if request.method == "GET":
                return {"tags": trade.get("tags", [])}
            elif request.method == "POST":
                data = request.get_json(silent=True) or {}
                tags = data.get("tags") or request.form.get("tags", "")
                if isinstance(tags, str):
                    tags_list = [t.strip() for t in tags.split(',') if t.strip()]
                else:
                    tags_list = tags if isinstance(tags, list) else []
                p.set_trade_tags(trade_id, tags_list)
                p.log_event("tag", f"updated trade {trade_id} tags")
                return {"tags": tags_list}
            else:
                p.set_trade_tags(trade_id, [])
                p.log_event("tag", f"deleted trade {trade_id} tags")
                return {"tags": []}
    return {"tags": []}, 404


@app.route("/portfolio/create", methods=["POST"])
def create_portfolio():
    name = request.form.get("name")
    strategy = request.form.get("strategy_type", "default")
    api_key = request.form.get("api_key")
    secret_key = request.form.get("secret_key")
    base_url = request.form.get("base_url") or ENV.get("ALPACA_BASE_URL")
    if name and api_key and secret_key:
        try:
            manager.add_portfolio(Portfolio(name, api_key, secret_key, base_url, strategy))
            manager.save_to_file(PORTFOLIO_FILE)
            logger.info("Created portfolio %s", name)
        except ValueError as exc:
            logger.error("Create portfolio failed: %s", exc)
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

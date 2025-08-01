import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from fpdf import FPDF

from .portfolio_manager import Portfolio, MultiPortfolioManager
from .diversification import analyze_portfolio


def export_trades_csv(portfolios: List[Portfolio], output_dir: str | Path = "reports") -> List[Path]:
    """Export trade history of each portfolio to a CSV file."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []
    for p in portfolios:
        if not p.history:
            continue
        file_path = output_dir / f"{p.name}_trades.csv"
        with file_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=p.history[0].keys())
            writer.writeheader()
            for item in p.history:
                writer.writerow(item)
        paths.append(file_path)
    return paths


def calculate_stats(portfolio: Portfolio) -> dict:
    """Return simple performance statistics for a portfolio."""
    profit = 0.0
    if portfolio.equity_curve:
        profit = portfolio.equity_curve[-1]["value"] - portfolio.equity_curve[0]["value"]
    wins = 0
    trades = 0
    for order in portfolio.history:
        if order.get("side", "").lower() == "sell":
            trades += 1
            filled = float(order.get("filled_avg_price") or 0)
            symbol = order.get("symbol")
            avg = portfolio.avg_prices.get(symbol)
            if avg and filled > avg:
                wins += 1
    winrate = (wins / trades * 100) if trades else 0.0
    return {"profit": profit, "winrate": winrate}


def generate_reports(portfolios: List[Portfolio], output_dir: str | Path = "reports") -> List[Path]:
    """Generate a simple CSV report with profit and winrate for each portfolio."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []
    for p in portfolios:
        stats = calculate_stats(p)
        file_path = output_dir / f"{p.name}_report.csv"
        with file_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["portfolio", "profit", "winrate"])
            writer.writerow([p.name, f"{stats['profit']:.2f}", f"{stats['winrate']:.2f}"])
        paths.append(file_path)
    return paths


def dashboard_snapshot(portfolio: Portfolio, manager: MultiPortfolioManager) -> Dict[str, Any]:
    """Return a data dictionary similar to the dashboard view."""
    manager.update_benchmark()
    bench = manager.get_normalized_benchmark()
    info = portfolio.get_account_info()
    portfolio.refresh_open_orders()
    divers = analyze_portfolio(portfolio)
    portfolio.correlation_matrix = divers["matrix"]
    portfolio.diversification_score = divers["score"]
    portfolio.diversification_warnings = divers["warnings"]
    return {
        "name": portfolio.name,
        "cash": info.get("cash"),
        "portfolio_value": info.get("portfolio_value"),
        "positions": portfolio.get_positions(),
        "history": portfolio.history,
        "open_orders": portfolio.open_orders,
        "allocation": portfolio.get_allocation(),
        "equity": portfolio.equity_curve,
        "equity_norm": manager.get_normalized_equity(portfolio),
        "benchmark": bench,
        "strategy_type": portfolio.strategy_type,
        "custom_prompt": portfolio.custom_prompt,
        "risk_alerts": portfolio.risk_alerts,
        "stop_loss_pct": portfolio.stop_loss_pct,
        "take_profit_pct": portfolio.take_profit_pct,
        "max_drawdown_pct": portfolio.max_drawdown_pct,
        "trade_pnl_limit_pct": portfolio.trade_pnl_limit_pct,
        "diversification_score": portfolio.diversification_score,
        "correlation": portfolio.correlation_matrix,
    }


def export_dashboard_data(
    portfolio: Portfolio,
    manager: MultiPortfolioManager,
    fmt: str = "json",
    output_dir: str | Path = "reports",
) -> Path | Dict[str, Any]:
    """Export dashboard data in the given format and return path or dict."""
    data = dashboard_snapshot(portfolio, manager)
    if fmt == "json":
        return data

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if fmt == "csv":
        file_path = output_dir / f"{portfolio.name}_dashboard.csv"
        with file_path.open("w", newline="") as f:
            writer = csv.writer(f)
            for key, val in data.items():
                writer.writerow([key, json.dumps(val, default=str)])
        return file_path
    if fmt == "pdf":
        file_path = output_dir / f"{portfolio.name}_dashboard.pdf"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Dashboard Export: {portfolio.name}", ln=True)
        for key, val in data.items():
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, key, ln=True)
            pdf.set_font("Arial", size=10)
            txt = json.dumps(val, default=str)[:1000]
            for line in txt.splitlines():
                pdf.multi_cell(0, 5, line)
        pdf.output(str(file_path))
        return file_path
    raise ValueError("unknown format")

import csv
from datetime import datetime
from pathlib import Path
from typing import List

from .portfolio_manager import Portfolio


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

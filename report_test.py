from app.portfolio_manager import Portfolio
from app.reporting import export_trades_csv, generate_reports


def main():
    # create dummy portfolio with fake trade history
    p = Portfolio("Test", "key", "secret", "https://paper-api.alpaca.markets")
    p.history = [
        {"symbol": "AAPL", "side": "buy", "qty": 1, "filled_avg_price": 150},
        {"symbol": "AAPL", "side": "sell", "qty": 1, "filled_avg_price": 155},
    ]
    p.avg_prices = {"AAPL": 150}
    p.equity_curve = [
        {"time": "2023-01-01T00:00:00", "value": 1000.0},
        {"time": "2023-01-02T00:00:00", "value": 1005.0},
    ]

    export_trades_csv([p], "reports")
    generate_reports([p], "reports")
    print("exported", "reports/Test_trades.csv")
    print("report", "reports/Test_report.csv")


if __name__ == "__main__":
    main()

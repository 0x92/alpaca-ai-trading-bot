import importlib.util
from app.portfolio_manager import Portfolio

spec = importlib.util.spec_from_file_location("flask_app", "app.py")
flask_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flask_app)
manager = flask_app.manager


def main():
    p = Portfolio("Hist", "key", "secret", "https://paper-api.alpaca.markets")
    p.history = [
        {"symbol": "AAPL", "side": "buy", "qty": 1, "submitted_at": "2023-01-01"},
        {"symbol": "AAPL", "side": "sell", "qty": 1, "submitted_at": "2023-01-02"},
    ]
    manager.portfolios = [p]
    client = flask_app.app.test_client()
    resp = client.get("/api/portfolio/Hist/trade_history")
    print("status", resp.status_code)
    print("data", resp.json)


if __name__ == "__main__":
    main()

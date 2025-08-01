import importlib.util
from datetime import datetime

from app.portfolio_manager import Portfolio

spec = importlib.util.spec_from_file_location("flask_app", "app.py")
flask_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flask_app)
manager = flask_app.manager


def main():
    p = Portfolio("Hist", "key", "secret", "https://paper-api.alpaca.markets")
    p.history = [
        {
            "id": "t1",
            "symbol": "AAPL",
            "side": "buy",
            "qty": 1,
            "submitted_at": "2023-01-01T00:00:00",
        }
    ]
    manager.portfolios = [p]
    client = flask_app.app.test_client()
    resp = client.get("/api/trade/t1/price_history")
    print("status", resp.status_code)
    data = resp.json
    print("prices", len(data.get("prices", [])))


if __name__ == "__main__":
    main()

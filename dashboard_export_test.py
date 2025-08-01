import importlib.util
from app.portfolio_manager import Portfolio

spec = importlib.util.spec_from_file_location("flask_app", "app.py")
flask_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flask_app)
manager = flask_app.manager


def main():
    p = Portfolio("ExportTest", "key", "secret", "https://paper-api.alpaca.markets")
    p.history = [{"id": "1", "symbol": "AAPL", "side": "buy", "qty": 1}]
    manager.portfolios = [p]
    client = flask_app.app.test_client()
    resp = client.get("/api/portfolio/ExportTest/export?format=json")
    print("status", resp.status_code)
    if resp.is_json:
        print("name", resp.json.get("name"))

if __name__ == "__main__":
    main()

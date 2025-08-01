import importlib.util
from app.portfolio_manager import Portfolio

spec = importlib.util.spec_from_file_location("flask_app", "app.py")
flask_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flask_app)
manager = flask_app.manager


def main():
    p = Portfolio("Notes", "key", "secret", "https://paper-api.alpaca.markets")
    p.history = [
        {"id": "1", "symbol": "AAPL", "side": "buy", "qty": 1, "submitted_at": "2023-01-01", "notes": "", "tags": []}
    ]
    manager.portfolios = [p]
    client = flask_app.app.test_client()
    resp = client.post("/api/trade/1/notes", json={"notes": "test note"})
    print("notes", resp.status_code, resp.json)
    resp = client.post("/api/trade/1/tags", json={"tags": "a,b"})
    print("tags", resp.status_code, resp.json)
    print("get", client.get("/api/trade/1/notes").json, client.get("/api/trade/1/tags").json)


if __name__ == "__main__":
    main()

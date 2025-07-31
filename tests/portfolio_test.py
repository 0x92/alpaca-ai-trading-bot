from app.config import load_env
from app.portfolio_manager import Portfolio, MultiPortfolioManager


def main():
    env = load_env()
    api_key = env.get("ALPACA_API_KEY")
    secret_key = env.get("ALPACA_SECRET_KEY")
    base_url = env.get("ALPACA_BASE_URL")

    # skip if no real credentials are set
    if not api_key or "your_alpaca_api_key" in api_key:
        print("No Alpaca API keys provided. Skipping live portfolio test.")
        return

    p1 = Portfolio("P1", api_key, secret_key, base_url)
    p2 = Portfolio("P2", api_key, secret_key, base_url)

    manager = MultiPortfolioManager([p1, p2])

    for p in manager.portfolios:
        info = p.get_account_info()
        print(p.name, "account status", info.get("status"))

    manager.step_all()

    for p in manager.portfolios:
        print(p.name, "history size", len(p.history))


if __name__ == "__main__":
    main()

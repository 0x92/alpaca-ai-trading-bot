from app.config import load_env
from app.portfolio_manager import Portfolio, MultiPortfolioManager


def main():
    env = load_env()
    api_key = env.get("ALPACA_API_KEY")
    secret_key = env.get("ALPACA_SECRET_KEY")
    base_url = env.get("ALPACA_BASE_URL")

    # skip if no real credentials are set
    if not api_key or "your_alpaca_api_key" in api_key:
        print("No Alpaca API keys provided. Skipping strategy test.")
        return

    p1 = Portfolio("Momentum", api_key, secret_key, base_url, "momentum")
    p2 = Portfolio("MeanRev", api_key, secret_key, base_url, "mean_reversion")
    manager = MultiPortfolioManager([p1, p2])
    manager.step_all("AAPL")
    for p in manager.portfolios:
        print(p.name, p.strategy_type, "trades", len(p.history))


if __name__ == "__main__":
    main()

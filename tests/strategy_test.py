from app.config import load_env
from app.portfolio_manager import Portfolio, get_strategy_from_openai
from app.research_engine import get_research


def main():
    env = load_env()
    api_key = env.get("ALPACA_API_KEY")
    secret_key = env.get("ALPACA_SECRET_KEY")
    base_url = env.get("ALPACA_BASE_URL")

    # skip if no real credentials are set
    if not api_key or "your_alpaca_api_key" in api_key:
        print("No Alpaca API keys provided. Skipping strategy test.")
        return

    p = Portfolio("Test", api_key, secret_key, base_url)
    research = get_research("AAPL")
    strat1 = get_strategy_from_openai(p, research, "momentum")
    strat2 = get_strategy_from_openai(p, research, "mean_reversion")
    print("momentum:", strat1)
    print("mean_reversion:", strat2)


if __name__ == "__main__":
    main()

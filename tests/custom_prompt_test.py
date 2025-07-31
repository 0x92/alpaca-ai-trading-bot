from app.config import load_env
from app.portfolio_manager import Portfolio, MultiPortfolioManager, get_strategy_from_openai
from app.research_engine import get_research


def main():
    env = load_env()
    api_key = env.get("ALPACA_API_KEY")
    secret_key = env.get("ALPACA_SECRET_KEY")
    base_url = env.get("ALPACA_BASE_URL")

    if not api_key or "your_alpaca_api_key" in api_key:
        print("No Alpaca API keys provided. Skipping custom prompt test.")
        return

    portfolio = Portfolio("Custom", api_key, secret_key, base_url, "default", "Buy {research[symbol]} if sentiment > 0")
    manager = MultiPortfolioManager([portfolio])
    research = get_research("AAPL")
    decision = get_strategy_from_openai(portfolio, research, portfolio.strategy_type)
    print("Decision:", decision)


if __name__ == "__main__":
    main()

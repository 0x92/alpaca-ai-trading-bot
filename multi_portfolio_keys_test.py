from app.portfolio_manager import Portfolio, MultiPortfolioManager


def main():
    manager = MultiPortfolioManager()
    p1 = Portfolio("P1", "key1", "secret1", "https://paper-api.alpaca.markets")
    manager.add_portfolio(p1)
    try:
        manager.add_portfolio(Portfolio("P2", "key1", "secret1", "https://paper-api.alpaca.markets"))
    except ValueError as exc:
        print("duplicate", str(exc))
    try:
        p_invalid = Portfolio("P3", "", "", "https://paper-api.alpaca.markets")
        manager.add_portfolio(p_invalid)
    except Exception as exc:
        print("invalid", str(exc))
    print("portfolios", len(manager.portfolios))


if __name__ == "__main__":
    main()

from app.portfolio_manager import Portfolio


def main():
    # create portfolio with dummy keys
    p = Portfolio("Risk", "key", "secret", "https://paper-api.alpaca.markets")
    p.max_drawdown_pct = 0.1
    p.initial_value = 100.0
    p.high_water = 100.0
    p.check_risk(85.0, simulate=True)
    print("alerts", p.risk_alerts)


if __name__ == "__main__":
    main()

from app.portfolio_manager import Portfolio, MultiPortfolioManager
import tempfile
import os


def main():
    p = Portfolio("PromptTest", "key", "secret", "paper", "default", "Always hold")
    manager = MultiPortfolioManager([p])
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = f.name
    manager.save_to_file(path)
    manager.portfolios = []
    manager.load_from_file(path, "key", "secret", "paper")
    loaded = manager.portfolios[0]
    print("loaded_prompt", loaded.custom_prompt)
    os.remove(path)


if __name__ == "__main__":
    main()

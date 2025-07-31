# Alpaca Trading Simulator

This project is a multi-portfolio trading simulator built with Python. It uses Alpaca's API along with other data sources and OpenAI for strategy generation.

## Setup

1. Create a `.env` file based on `.env.example` and fill in your API keys.
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the environment test:
   ```bash
   python env_test.py
   ```
4. Test the portfolio manager (requires Alpaca paper account keys):
   ```bash
   python portfolio_test.py
   ```
5. Run the research engine test (requires network and API keys for best results):
   ```bash
   python research_test.py
   ```

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
   python -m tests.env_test
   ```
4. Test the portfolio manager (requires Alpaca paper account keys):
   ```bash
   python -m tests.portfolio_test
   ```
5. Run the research engine test (requires network and API keys for best results):
   ```bash
   python -m tests.research_test
   ```
6. Try the OpenAI strategy demo:
   ```bash
   python -m tests.strategy_test
   ```
7. Run the risk management test:
   ```bash
   python -m tests.risk_test
   ```
8. Run the diversification analysis test:
   ```bash
   python -m tests.diversification_test
   ```
9. Generate an example trade export and report:
   ```bash
   python -m tests.report_test
   ```

10. Run the Flask dashboard:
   ```bash
   python app.py
   ```
   The dashboard lets you pick a strategy for each portfolio from a dropdown.
   Each portfolio requires its **own** Alpaca API key and secret. The create form
   in the dashboard asks for these credentials – one key pair cannot be shared
   between multiple portfolios. The "Step" button accepts an optional comma-
   separated list of symbols. If left blank, the simulator will trade a set of
   trending tickers automatically. Set `TRENDING_SOURCE=openai` in your `.env`
   file to let ChatGPT suggest trending symbols instead of using Yahoo Finance.
   The **Buy Only** button works similarly but ignores sell signals and only
   executes trades when a buy recommendation is returned.

## Custom Prompt Editor

Within the dashboard each portfolio provides a textarea to configure a custom
prompt for OpenAI. The prompt must contain the placeholders `{strategy_type}`,
`{portfolio}` and `{research}` which will automatically be filled in before the
request is sent. Use the "Preview" button to see the generated decision before
saving the prompt.

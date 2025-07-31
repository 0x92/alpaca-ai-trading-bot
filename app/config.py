import os
from pathlib import Path
from dotenv import load_dotenv


def load_env():
    """Load environment variables from the project root .env file."""
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # fallback: load default environment variables
        load_dotenv()

    return {
        'ALPACA_API_KEY': os.getenv('ALPACA_API_KEY'),
        'ALPACA_SECRET_KEY': os.getenv('ALPACA_SECRET_KEY'),
        'ALPACA_BASE_URL': os.getenv('ALPACA_BASE_URL'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'FINNHUB_API_KEY': os.getenv('FINNHUB_API_KEY'),
        'NEWS_API_KEY': os.getenv('NEWS_API_KEY'),
    }

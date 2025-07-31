import os
import requests
from textblob import TextBlob

from .config import load_env
from .logger import get_logger

logger = get_logger(__name__)


ENV = load_env()
FINNHUB_API_KEY = ENV.get("FINNHUB_API_KEY")
NEWS_API_KEY = ENV.get("NEWS_API_KEY")


def get_fundamentals_yahoo(symbol: str) -> dict:
    """Fetch basic fundamentals from Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as exc:
        if resp.status_code == 429:
            logger.warning("Yahoo Finance rate limit hit")
        else:
            logger.error("Yahoo Finance HTTP error: %s", exc)
    except Exception as exc:
        logger.error("Yahoo Finance error: %s", exc)
    return {"error": "fetch_failed"}


def get_news_finnhub(symbol: str) -> list:
    """Fetch recent news for a symbol from Finnhub or NewsAPI."""
    if FINNHUB_API_KEY:
        url = (
            f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2020-01-01&to=2020-12-31&token={FINNHUB_API_KEY}"
        )
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as exc:
            if resp.status_code == 429:
                logger.warning("Finnhub rate limit hit")
            else:
                logger.error("Finnhub HTTP error: %s", exc)
        except Exception as exc:
            logger.error("Finnhub error: %s", exc)
    if NEWS_API_KEY:
        url = (
            f"https://newsapi.org/v2/everything?q={symbol}&apiKey={NEWS_API_KEY}"
        )
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get("articles", [])
        except requests.exceptions.HTTPError as exc:
            if resp.status_code == 429:
                logger.warning("NewsAPI rate limit hit")
            else:
                logger.error("NewsAPI HTTP error: %s", exc)
        except Exception as exc:
            logger.error("NewsAPI error: %s", exc)
    return []


def analyze_sentiment(news_items: list) -> float:
    """Very basic sentiment score based on news headlines."""
    if not news_items:
        return 0.0
    scores = []
    for item in news_items:
        text = item.get("headline") or item.get("title") or ""
        blob = TextBlob(text)
        scores.append(blob.sentiment.polarity)
    return sum(scores) / len(scores) if scores else 0.0


def get_research(symbol: str) -> dict:
    """Return combined research data for a symbol."""
    fundamentals = get_fundamentals_yahoo(symbol)
    news = get_news_finnhub(symbol)
    sentiment = analyze_sentiment(news)
    return {
        "symbol": symbol,
        "fundamentals": fundamentals,
        "news": news,
        "sentiment": sentiment,
    }

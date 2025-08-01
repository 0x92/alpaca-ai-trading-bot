import os
import requests
import openai
from textblob import TextBlob

from .config import load_env
from .logger import get_logger

logger = get_logger(__name__)


ENV = load_env()
FINNHUB_API_KEY = ENV.get("FINNHUB_API_KEY")
NEWS_API_KEY = ENV.get("NEWS_API_KEY")
openai.api_key = ENV.get("OPENAI_API_KEY")
TRENDING_SOURCE = ENV.get("TRENDING_SOURCE", "yahoo").lower()


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
        url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2020-01-01&to=2020-12-31&token={FINNHUB_API_KEY}"
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
        url = f"https://newsapi.org/v2/everything?q={symbol}&apiKey={NEWS_API_KEY}"
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


def select_research_topics(symbol: str) -> list[str]:
    """Use OpenAI to determine which research types to fetch."""
    if not openai.api_key or "your_openai_api_key" in openai.api_key:
        return ["fundamentals", "news", "sentiment"]
    prompt = (
        "For analyzing the stock {symbol}, which of the following research types "
        "are most relevant: fundamentals, news, sentiment? "
        "Respond with a comma separated list of the chosen types only."
    ).format(symbol=symbol)
    try:
        client = openai.OpenAI(api_key=openai.api_key)
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        text = resp.choices[0].message.content.lower()
        return [t.strip() for t in text.split(",") if t.strip()]
    except Exception as exc:
        logger.error("OpenAI research topic selection error: %s", exc)
        return ["fundamentals", "news", "sentiment"]


def get_ai_research(symbol: str) -> dict:
    """Fetch research based on an AI-selected set of topics."""
    topics = select_research_topics(symbol)
    result = {"symbol": symbol}
    news_items = []
    if "fundamentals" in topics:
        result["fundamentals"] = get_fundamentals_yahoo(symbol)
    if "news" in topics or "sentiment" in topics:
        news_items = get_news_finnhub(symbol)
    if "news" in topics:
        result["news"] = news_items
    if "sentiment" in topics:
        result["sentiment"] = analyze_sentiment(news_items)
    return result


def _get_trending_from_yahoo(limit: int) -> list[str]:
    url = "https://query1.finance.yahoo.com/v1/finance/trending/US"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("finance", {}).get("result", [])
    if results:
        quotes = results[0].get("quotes", [])
        return [q.get("symbol") for q in quotes[:limit] if q.get("symbol")]
    return []


def _get_trending_from_openai(limit: int) -> list[str]:
    prompt = (
        f"List the top {limit} U.S. stock ticker symbols currently trending "
        "with high trading volume and media coverage. Respond with a comma "
        "separated list of tickers only."
    )
    client = openai.OpenAI(api_key=openai.api_key)
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    text = resp.choices[0].message.content
    return [t.strip().upper() for t in text.split(",") if t.strip()]


def get_trending_symbols(limit: int = 5) -> list[str]:
    """Return a list of trending tickers from Yahoo or OpenAI."""
    try:
        if TRENDING_SOURCE == "openai":
            if not openai.api_key or "your_openai_api_key" in openai.api_key:
                return ["AAPL"]
            return _get_trending_from_openai(limit)
        return _get_trending_from_yahoo(limit)
    except Exception as exc:
        logger.error("Failed to fetch trending symbols: %s", exc)
        return ["AAPL"]

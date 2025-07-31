import csv
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
import requests

from .logger import get_logger

logger = get_logger(__name__)

_STOOQ_HISTORY_URL = "https://stooq.com/q/d/l/?s={symbol}&i=d"


def fetch_price_history(symbol: str, days: int = 90) -> pd.Series:
    """Return a series of closing prices for the last given days."""
    url = _STOOQ_HISTORY_URL.format(symbol=symbol.lower())
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        reader = csv.DictReader(resp.text.splitlines())
        data = [
            (row.get("Date"), row.get("Close"))
            for row in reader
            if row.get("Date") and row.get("Close")
        ]
        df = pd.DataFrame(data, columns=["date", "close"])
        df["date"] = pd.to_datetime(df["date"])
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna()
        cutoff = datetime.utcnow() - timedelta(days=days)
        df = df[df["date"] >= cutoff]
        return df.set_index("date")["close"]
    except Exception as exc:
        logger.error("Failed to fetch history for %s: %s", symbol, exc)
        return pd.Series(dtype="float64")


def calculate_correlation(symbols: List[str], days: int = 90) -> pd.DataFrame:
    """Return correlation matrix of daily returns for given symbols."""
    if not symbols:
        return pd.DataFrame()
    prices = {}
    for sym in symbols:
        series = fetch_price_history(sym, days)
        if not series.empty:
            prices[sym] = series
    if not prices:
        return pd.DataFrame()
    df = pd.DataFrame(prices)
    returns = df.pct_change().dropna()
    if returns.empty:
        return pd.DataFrame()
    return returns.corr()


def diversification_score(corr: pd.DataFrame) -> float:
    """Simple diversification score between 0 and 1 (1=perfectly diversified)."""
    if corr.empty:
        return 0.0
    # exclude self-correlation (diagonal)
    vals = corr.where(~pd.eye(len(corr), dtype=bool)).abs().values.flatten()
    vals = [v for v in vals if pd.notna(v)]
    if not vals:
        return 1.0
    avg_corr = sum(vals) / len(vals)
    return max(0.0, 1 - avg_corr)


def analyze_portfolio(portfolio) -> Dict:
    """Compute correlation matrix and diversification score for portfolio holdings."""
    symbols = list(portfolio.holdings.keys())
    corr = calculate_correlation(symbols)
    score = diversification_score(corr)
    warnings = []
    if score < 0.5 and symbols:
        warnings.append("Low diversification")
    # check concentration risk (>50% in one asset)
    total = sum(portfolio.holdings.values())
    for sym, qty in portfolio.holdings.items():
        if total > 0 and qty / total > 0.5:
            warnings.append(f"Concentration risk: {sym}")
            break
    return {
        "matrix": corr.round(2).to_dict() if not corr.empty else {},
        "score": round(score, 2),
        "warnings": warnings,
    }

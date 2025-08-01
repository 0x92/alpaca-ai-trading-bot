import csv
from datetime import datetime
from typing import List, Dict
import requests

from .logger import get_logger

logger = get_logger(__name__)

_STOOQ_HISTORY_URL = "https://stooq.com/q/d/l/?s={symbol}&i=d"


def get_price_history(symbol: str, start: datetime, end: datetime) -> List[Dict[str, float]]:
    """Return daily close prices for symbol between start and end dates."""
    url = _STOOQ_HISTORY_URL.format(symbol=symbol.lower())
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        reader = csv.DictReader(resp.text.splitlines())
        data = []
        for row in reader:
            date_str = row.get("Date")
            close = row.get("Close")
            if not date_str or not close:
                continue
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue
            if start.date() <= dt.date() <= end.date():
                data.append({"time": dt.isoformat(), "close": float(close)})
        return data
    except Exception as exc:
        logger.error("Failed to fetch price history for %s: %s", symbol, exc)
        return []

import csv
from datetime import datetime
from typing import Dict, List

import requests

from .logger import get_logger

logger = get_logger(__name__)

_STOOQ_URL = "https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"


def get_latest_benchmark_price(symbol: str = "^spx") -> Dict[str, str | float]:
    """Return latest close price for a benchmark symbol from Stooq."""
    url = _STOOQ_URL.format(symbol=symbol)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        reader = csv.DictReader(resp.text.splitlines())
        row = next(reader, None)
        if row:
            date = row.get("Date")
            close = row.get("Close")
            if date and close:
                ts = datetime.strptime(date, "%Y-%m-%d").isoformat()
                return {"time": ts, "value": float(close)}
    except Exception as exc:
        logger.error("Failed to fetch benchmark price: %s", exc)
    return {}


def normalize_curve(curve: List[Dict[str, float]]) -> List[Dict[str, float]]:
    """Normalize time series values to start at 100."""
    if not curve:
        return []
    start = curve[0]["value"]
    if start == 0:
        start = 1
    return [
        {"time": c["time"], "value": c["value"] / start * 100}
        for c in curve
    ]


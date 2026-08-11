"""Market-data access helpers."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
import yfinance as yf


def clean_ticker(value: str) -> str:
    """Normalize a user-entered ticker."""
    return value.strip().upper().replace(" ", "")


def parse_tickers(value: str, limit: int = 5) -> list[str]:
    """Return unique, normalized comma-separated tickers."""
    tickers: list[str] = []
    for item in value.split(","):
        ticker = clean_ticker(item)
        if ticker and ticker not in tickers:
            tickers.append(ticker)
    return tickers[:limit]


def fetch_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Fetch adjusted historical prices for one ticker."""
    symbol = clean_ticker(ticker)
    if not symbol:
        raise ValueError("Enter a ticker symbol.")

    frame = yf.download(
        symbol,
        period=period,
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    if frame.empty:
        raise ValueError(f"No market data was returned for {symbol}.")

    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)

    required = {"Open", "High", "Low", "Close", "Volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Market data for {symbol} is missing: {', '.join(sorted(missing))}.")

    return frame.sort_index().dropna(subset=["Close"])


def fetch_company_info(ticker: str) -> dict:
    """Fetch headline company information, tolerating unavailable fields."""
    symbol = clean_ticker(ticker)
    try:
        return yf.Ticker(symbol).info or {}
    except Exception:
        return {}


def fetch_comparison(tickers: Iterable[str], period: str = "1y") -> pd.DataFrame:
    """Fetch closing prices and normalize each series to a starting value of 100."""
    closes: dict[str, pd.Series] = {}
    for ticker in tickers:
        symbol = clean_ticker(ticker)
        if not symbol:
            continue
        try:
            history = fetch_history(symbol, period)
        except Exception:
            continue
        closes[symbol] = history["Close"]

    if not closes:
        return pd.DataFrame()

    prices = pd.DataFrame(closes).dropna(how="all").ffill()

    def normalize(series: pd.Series) -> pd.Series:
        valid_prices = series.dropna()
        if valid_prices.empty or valid_prices.iloc[0] == 0:
            return series * pd.NA
        return series / valid_prices.iloc[0] * 100

    normalized = prices.apply(normalize)
    return normalized

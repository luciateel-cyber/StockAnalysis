"""Market-data access helpers."""

from __future__ import annotations

from collections.abc import Iterable
import html
import re
import urllib.parse
import urllib.request
from xml.etree import ElementTree

import pandas as pd
import yfinance as yf


PEER_GROUPS = {
    "mega_cap_tech": {
        "label": "large-cap technology",
        "market_symbol": "XLK",
        "market_label": "technology sector",
        "symbols": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMZN"],
    },
    "semiconductors": {
        "label": "semiconductors",
        "market_symbol": "SMH",
        "market_label": "semiconductor market",
        "symbols": ["NVDA", "AMD", "AVGO", "INTC", "TSM", "QCOM", "MU"],
    },
    "ev_auto": {
        "label": "electric vehicles and autos",
        "market_symbol": "CARZ",
        "market_label": "auto and EV market",
        "symbols": ["TSLA", "RIVN", "GM", "F", "TM", "NIO"],
    },
    "banks": {
        "label": "banks and financials",
        "market_symbol": "XLF",
        "market_label": "financial sector",
        "symbols": ["JPM", "BAC", "WFC", "C", "GS", "MS"],
    },
    "healthcare": {
        "label": "healthcare",
        "market_symbol": "XLV",
        "market_label": "healthcare sector",
        "symbols": ["LLY", "UNH", "JNJ", "MRK", "PFE", "ABBV"],
    },
    "consumer": {
        "label": "consumer and retail",
        "market_symbol": "XLY",
        "market_label": "consumer discretionary sector",
        "symbols": ["AMZN", "WMT", "COST", "TGT", "HD", "LOW", "NKE"],
    },
    "energy": {
        "label": "energy",
        "market_symbol": "XLE",
        "market_label": "energy sector",
        "symbols": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC"],
    },
    "indexes": {
        "label": "broad market funds",
        "market_symbol": "SPY",
        "market_label": "U.S. equity market",
        "symbols": ["SPY", "VOO", "IVV", "QQQ", "DIA", "IWM"],
    },
}

PEER_LOOKUP = {
    symbol: group
    for group in PEER_GROUPS.values()
    for symbol in group["symbols"]
}


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
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Market data for {symbol} is missing: {missing_list}.")

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

    return prices.apply(normalize)


def peer_context(ticker: str) -> dict:
    """Return a small peer group and market proxy for a ticker."""
    symbol = clean_ticker(ticker)
    group = PEER_LOOKUP.get(symbol, PEER_GROUPS["indexes"])
    suggestions = [peer for peer in group["symbols"] if peer != symbol][:4]
    if symbol not in PEER_LOOKUP:
        suggestions = ["SPY", "QQQ", "IWM", "DIA"]
    return {
        "symbol": symbol,
        "peer_label": group["label"],
        "market_symbol": group["market_symbol"],
        "market_label": group["market_label"],
        "suggestions": suggestions[:4],
    }


def _strip_markup(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _fetch_yahoo_news(ticker: str, limit: int = 5) -> list[dict[str, str]]:
    symbol = urllib.parse.quote(clean_ticker(ticker), safe="")
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "StockLens/1.0",
            "Accept": "application/rss+xml,text/xml,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        root = ElementTree.fromstring(response.read())

    articles: list[dict[str, str]] = []
    for item in root.findall(".//item")[:limit]:
        title = _strip_markup(item.findtext("title", ""))
        if not title:
            continue
        articles.append(
            {
                "title": title,
                "description": _strip_markup(item.findtext("description", "")),
                "link": item.findtext("link", ""),
                "published": item.findtext("pubDate", ""),
            }
        )
    return articles


def summarize_news(subject: str, articles: list[dict[str, str]]) -> str:
    """Create one compact news paragraph from recent headlines."""
    if not articles:
        return f"No recent headlines were available for {subject}."

    phrases = []
    for article in articles[:3]:
        title = article["title"].rstrip(".")
        description = article.get("description", "").rstrip(".")
        if description and description.lower() not in title.lower():
            phrases.append(f"{title}: {description}")
        else:
            phrases.append(title)
    return f"Latest coverage for {subject} is centered on {'; '.join(phrases)}."


def fetch_news_context(ticker: str) -> dict:
    """Fetch stock-specific and peer-market news context."""
    context = peer_context(ticker)
    try:
        stock_articles = _fetch_yahoo_news(context["symbol"])
    except Exception:
        stock_articles = []
    try:
        market_articles = _fetch_yahoo_news(context["market_symbol"])
    except Exception:
        market_articles = []

    return {
        **context,
        "stock_paragraph": summarize_news(context["symbol"], stock_articles),
        "market_paragraph": summarize_news(context["market_label"], market_articles),
        "stock_articles": stock_articles,
        "market_articles": market_articles,
    }

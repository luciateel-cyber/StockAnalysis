"""Technical indicators and summary metrics."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


TRADING_DAYS = 252


def add_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    """Add common technical indicators without mutating the input."""
    data = frame.copy()
    close = data["Close"].astype(float)

    data["SMA 20"] = close.rolling(20).mean()
    data["SMA 50"] = close.rolling(50).mean()

    change = close.diff()
    gain = change.clip(lower=0)
    loss = -change.clip(upper=0)
    average_gain = gain.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    average_loss = loss.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    relative_strength = average_gain / average_loss.replace(0, np.nan)
    data["RSI 14"] = 100 - (100 / (1 + relative_strength))
    data.loc[(average_loss == 0) & (average_gain > 0), "RSI 14"] = 100
    data.loc[(average_loss == 0) & (average_gain == 0), "RSI 14"] = 50

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    data["MACD"] = ema_12 - ema_26
    data["MACD Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()

    returns = close.pct_change()
    data["Daily Return"] = returns
    data["Volatility 20"] = returns.rolling(20).std() * math.sqrt(TRADING_DAYS)
    data["Drawdown"] = close / close.cummax() - 1
    return data


def summary_metrics(frame: pd.DataFrame) -> dict[str, float]:
    """Calculate a compact set of risk and return metrics."""
    close = frame["Close"].dropna().astype(float)
    if close.empty:
        raise ValueError("Price history is empty.")

    returns = close.pct_change().dropna()
    total_return = close.iloc[-1] / close.iloc[0] - 1 if len(close) > 1 else 0.0
    annualized_volatility = (
        returns.std(ddof=1) * math.sqrt(TRADING_DAYS) if len(returns) > 1 else 0.0
    )
    annualized_return = (
        (close.iloc[-1] / close.iloc[0]) ** (TRADING_DAYS / (len(close) - 1)) - 1
        if len(close) > 1 and close.iloc[0] > 0
        else 0.0
    )
    sharpe = (
        annualized_return / annualized_volatility
        if annualized_volatility and not np.isnan(annualized_volatility)
        else np.nan
    )
    max_drawdown = (close / close.cummax() - 1).min()

    return {
        "latest_price": float(close.iloc[-1]),
        "total_return": float(total_return),
        "annualized_return": float(annualized_return),
        "annualized_volatility": float(annualized_volatility),
        "sharpe_zero_rf": float(sharpe),
        "max_drawdown": float(max_drawdown),
    }


def compact_number(value: object) -> str:
    """Format a large numeric value for display."""
    if value is None:
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    if np.isnan(number):
        return "—"

    for threshold, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(number) >= threshold:
            return f"{number / threshold:.2f}{suffix}"
    return f"{number:,.2f}"

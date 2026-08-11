# StockLens

A small, interactive stock-analysis project built with Python and Streamlit.

It includes:

- Market-data download from Yahoo Finance through `yfinance`
- Historical price, volume, return, and drawdown charts
- Moving averages, daily returns, RSI, MACD, volatility, and drawdown
- Headline company and valuation metrics
- Normalized performance comparison across several tickers
- A personal session watchlist for quick check-ins
- Suggested peer stocks to compare or research
- Structured stock research bullets covering profitability, efficiency, balance-sheet strength, moat, and management quality
- Structured sector research bullets covering macro conditions, demand drivers, competition, regulation, SWOT, risks, sentiment, and recent headlines
- CSV export for both raw market data and analyzed data

## Run it

Python 3.11–3.13 is recommended. Some data-science packages may not yet support
newer Python releases immediately.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the local address shown by Streamlit.

## Test it

```bash
pytest
```

## Notes

- Market data is fetched from Yahoo Finance through `yfinance`.
- Quotes may be delayed or incomplete.
- Watchlists are saved for the active Streamlit session. Add persistent storage
  if you want saved tickers to follow users across devices or visits.
- This project is for research and education, not investment advice.

## Project layout

```text
app.py                    Streamlit interface
stock_analysis/data.py    Market-data access and cleanup
stock_analysis/metrics.py Calculations and formatting
tests/                    Unit tests for calculations
```

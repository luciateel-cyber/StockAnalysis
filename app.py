from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from stock_analysis.data import (
    fetch_comparison,
    fetch_company_info,
    fetch_history,
    fetch_news_context,
    parse_tickers,
)
from stock_analysis.metrics import add_indicators, compact_number, summary_metrics


st.set_page_config(page_title="StockLens", page_icon="📈", layout="wide")


@st.cache_data(ttl=900, show_spinner=False)
def cached_history(ticker: str, period: str):
    return fetch_history(ticker, period)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_company_info(ticker: str):
    return fetch_company_info(ticker)


@st.cache_data(ttl=900, show_spinner=False)
def cached_comparison(tickers: tuple[str, ...], period: str):
    return fetch_comparison(tickers, period)


@st.cache_data(ttl=900, show_spinner=False)
def cached_news_context(ticker: str):
    return fetch_news_context(ticker)


def initialize_state() -> None:
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []
    if "primary_ticker" not in st.session_state:
        st.session_state.primary_ticker = "AAPL"
    if "comparison_tickers" not in st.session_state:
        st.session_state.comparison_tickers = "MSFT, GOOGL, SPY"


def save_to_watchlist(ticker: str) -> None:
    symbol = ticker.strip().upper()
    if not symbol:
        return
    st.session_state.watchlist = [
        symbol,
        *[item for item in st.session_state.watchlist if item != symbol],
    ][:20]


def price_chart(data, ticker: str):
    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.76, 0.24],
    )
    figure.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name=ticker,
        ),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Scatter(x=data.index, y=data["SMA 20"], name="20-day average", line_width=1.5),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Scatter(x=data.index, y=data["SMA 50"], name="50-day average", line_width=1.5),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Bar(x=data.index, y=data["Volume"], name="Volume", marker_color="#8796a5"),
        row=2,
        col=1,
    )
    figure.update_layout(
        height=620,
        margin=dict(l=10, r=10, t=45, b=10),
        title=f"{ticker} price history",
        xaxis_rangeslider_visible=False,
        legend_orientation="h",
        hovermode="x unified",
    )
    return figure


def indicator_chart(data):
    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.09,
        subplot_titles=("RSI (14)", "MACD"),
    )
    figure.add_trace(
        go.Scatter(x=data.index, y=data["RSI 14"], name="RSI"),
        row=1,
        col=1,
    )
    figure.add_hline(y=70, line_dash="dot", line_color="#d65f5f", row=1, col=1)
    figure.add_hline(y=30, line_dash="dot", line_color="#4c9f70", row=1, col=1)
    figure.add_trace(
        go.Scatter(x=data.index, y=data["MACD"], name="MACD"),
        row=2,
        col=1,
    )
    figure.add_trace(
        go.Scatter(x=data.index, y=data["MACD Signal"], name="Signal"),
        row=2,
        col=1,
    )
    figure.update_yaxes(range=[0, 100], row=1, col=1)
    figure.update_layout(
        height=500,
        margin=dict(l=10, r=10, t=55, b=10),
        legend_orientation="h",
        hovermode="x unified",
    )
    return figure


def return_chart(data, ticker: str):
    data = data.copy()
    cumulative_return = (1 + data["Daily Return"].fillna(0)).cumprod() - 1

    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("Cumulative return", "Drawdown"),
    )
    figure.add_trace(
        go.Scatter(
            x=data.index,
            y=cumulative_return,
            name=f"{ticker} return",
            fill="tozeroy",
        ),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Drawdown"],
            name="Drawdown",
            fill="tozeroy",
            line_color="#d65f5f",
        ),
        row=2,
        col=1,
    )
    figure.update_yaxes(tickformat=".0%", row=1, col=1)
    figure.update_yaxes(tickformat=".0%", row=2, col=1)
    figure.update_layout(
        height=430,
        margin=dict(l=10, r=10, t=55, b=10),
        legend_orientation="h",
        hovermode="x unified",
    )
    return figure


st.title("📈 StockLens")
st.caption("A compact research dashboard for exploring public-market data.")

initialize_state()

with st.sidebar:
    st.header("Analysis settings")
    ticker = st.text_input("Primary ticker", key="primary_ticker").strip().upper()
    period = st.selectbox(
        "History",
        options=["3mo", "6mo", "1y", "2y", "5y", "10y"],
        index=2,
        format_func={
            "3mo": "3 months",
            "6mo": "6 months",
            "1y": "1 year",
            "2y": "2 years",
            "5y": "5 years",
            "10y": "10 years",
        }.get,
    )
    comparison_text = st.text_input(
        "Compare with",
        key="comparison_tickers",
        help="Up to five comma-separated ticker symbols.",
    )
    if st.button("Save primary ticker", use_container_width=True):
        save_to_watchlist(ticker)
        st.success(f"{ticker} saved to your watchlist.")

    st.subheader("Personal watchlist")
    if st.session_state.watchlist:
        for saved_ticker in st.session_state.watchlist:
            load_column, remove_column = st.columns([2, 1])
            if load_column.button(saved_ticker, key=f"load-{saved_ticker}", use_container_width=True):
                st.session_state.primary_ticker = saved_ticker
                st.rerun()
            if remove_column.button("Remove", key=f"remove-{saved_ticker}", use_container_width=True):
                st.session_state.watchlist = [
                    item for item in st.session_state.watchlist if item != saved_ticker
                ]
                st.rerun()
    else:
        st.caption("Saved tickers will appear here for quick check-ins.")

    st.caption("Data may be delayed. For education and research—not investment advice.")

if not ticker:
    st.info("Enter a ticker in the sidebar to begin.")
    st.stop()

try:
    with st.spinner(f"Loading {ticker}…"):
        raw_history = cached_history(ticker, period)
        history = add_indicators(raw_history)
        company = cached_company_info(ticker)
        news_context = cached_news_context(ticker)
        metrics = summary_metrics(history)
except Exception as exc:
    st.error(f"Could not load {ticker}: {exc}")
    st.info("Check the ticker and your internet connection, then try again.")
    st.stop()

name = company.get("longName") or company.get("shortName") or ticker
st.subheader(name)
if company.get("sector") or company.get("industry"):
    st.caption(" · ".join(filter(None, [company.get("sector"), company.get("industry")])))

metric_columns = st.columns(5)
metric_columns[0].metric("Latest price", f"${metrics['latest_price']:,.2f}")
metric_columns[1].metric("Period return", f"{metrics['total_return']:.1%}")
metric_columns[2].metric("Annualized volatility", f"{metrics['annualized_volatility']:.1%}")
metric_columns[3].metric("Max drawdown", f"{metrics['max_drawdown']:.1%}")
metric_columns[4].metric(
    "Sharpe (0% rate)",
    "—" if metrics["sharpe_zero_rf"] != metrics["sharpe_zero_rf"] else f"{metrics['sharpe_zero_rf']:.2f}",
)

overview_tab, technical_tab, compare_tab, data_tab = st.tabs(
    ["Overview", "Technical indicators", "Comparison", "Data"]
)

with overview_tab:
    st.plotly_chart(price_chart(history, ticker), use_container_width=True)
    st.plotly_chart(return_chart(history, ticker), use_container_width=True)
    st.markdown("#### Company snapshot")
    snapshot = st.columns(4)
    snapshot[0].metric("Market cap", compact_number(company.get("marketCap")))
    snapshot[1].metric("Trailing P/E", compact_number(company.get("trailingPE")))
    snapshot[2].metric("Forward P/E", compact_number(company.get("forwardPE")))
    snapshot[3].metric("Dividend yield", (
        f"{company['dividendYield']:.2%}" if company.get("dividendYield") is not None else "—"
    ))
    st.markdown("#### Latest news")
    st.write(f"**{ticker}:** {news_context['stock_paragraph']}")
    st.write(f"**{news_context['market_label'].title()}:** {news_context['market_paragraph']}")

with technical_tab:
    st.plotly_chart(indicator_chart(history), use_container_width=True)
    latest_rsi = history["RSI 14"].dropna()
    latest_volatility = history["Volatility 20"].dropna()
    details = st.columns(3)
    details[0].metric("RSI (14)", f"{latest_rsi.iloc[-1]:.1f}" if not latest_rsi.empty else "—")
    details[1].metric(
        "20-day volatility",
        f"{latest_volatility.iloc[-1]:.1%}" if not latest_volatility.empty else "—",
    )
    details[2].metric("Annualized return", f"{metrics['annualized_return']:.1%}")

with compare_tab:
    st.markdown("#### Similar stocks to research")
    st.caption(f"{ticker} is grouped with {news_context['peer_label']} names.")
    suggestion_columns = st.columns(max(len(news_context["suggestions"]), 1))
    current_comparisons = parse_tickers(comparison_text)
    for index, suggestion in enumerate(news_context["suggestions"]):
        with suggestion_columns[index]:
            st.write(f"**{suggestion}**")
            if st.button("View", key=f"view-{suggestion}", use_container_width=True):
                st.session_state.primary_ticker = suggestion
                st.rerun()
            if st.button("Compare", key=f"compare-{suggestion}", use_container_width=True):
                if suggestion not in current_comparisons and suggestion != ticker:
                    st.session_state.comparison_tickers = ", ".join(
                        [*current_comparisons, suggestion]
                    )
                st.rerun()

    comparison_tickers = parse_tickers(f"{ticker},{comparison_text}")
    comparison = cached_comparison(tuple(comparison_tickers), period)
    if comparison.empty:
        st.warning("No comparison data is available.")
    else:
        figure = go.Figure()
        for symbol in comparison.columns:
            figure.add_trace(
                go.Scatter(x=comparison.index, y=comparison[symbol], name=symbol)
            )
        figure.update_layout(
            title="Growth of 100",
            yaxis_title="Indexed value",
            height=540,
            margin=dict(l=10, r=10, t=45, b=10),
            legend_orientation="h",
            hovermode="x unified",
        )
        st.plotly_chart(figure, use_container_width=True)

with data_tab:
    display_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "SMA 20",
        "SMA 50",
        "RSI 14",
        "MACD",
    ]
    st.dataframe(history[display_columns].sort_index(ascending=False), use_container_width=True)
    download_columns = st.columns(2)
    download_columns[0].download_button(
        "Download market data CSV",
        raw_history.to_csv().encode("utf-8"),
        file_name=f"{ticker}_{period}_market_data.csv",
        mime="text/csv",
    )
    download_columns[1].download_button(
        "Download analyzed CSV",
        history.to_csv().encode("utf-8"),
        file_name=f"{ticker}_{period}_analysis.csv",
        mime="text/csv",
    )

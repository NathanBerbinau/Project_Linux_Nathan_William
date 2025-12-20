import streamlit as st
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from modules.Quant_A.data_fetcher import DataFetcher
from modules.Quant_A.strategies import TradingStrategies
from modules.Quant_A.metrics import PerformanceMetrics

def render_quant_a_dashboard(refresh_count: int):
    """Main dashboard for single asset analysis"""

    st.header("Single Asset Analysis - Module A")

    if refresh_count > 0:
        st.session_state["last_update"] = time.time()

    # Initialize data fetcher
    fetcher = DataFetcher()

    # Sidebar controls
    st.sidebar.subheader("Asset Selection")
    ticker = st.sidebar.selectbox(
        "Select Asset",
        options=list(fetcher.supported_tickers.keys()),
        format_func=lambda x: fetcher.supported_tickers[x]
    )

    period = st.sidebar.selectbox(
        "Historical Period",
        ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=3
    )

    # Real-time data display
    st.subheader("Current Market Data")
    realtime_data = fetcher.fetch_realtime_price(ticker)

    if realtime_data:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Current Price", f"${realtime_data['current_price']:.2f}")
        col2.metric("Open", f"${realtime_data['open']:.2f}")
        col3.metric("High", f"${realtime_data['high']:.2f}")
        col4.metric("Low", f"${realtime_data['low']:.2f}")

        st.caption(f"Last updated: {realtime_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")

    # Fetch historical data
    historical_data = fetcher.fetch_historical_data(ticker, period)

    if historical_data.empty:
        st.error("Unable to fetch historical data")
        return

    # Strategy selection
    st.sidebar.subheader("Strategy Configuration")
    strategy_type = st.sidebar.selectbox(
        "Select Strategy",
        ["Buy & Hold", "SMA Crossover", "Momentum", "Mean Reversion"]
    )

    initial_capital = st.sidebar.number_input(
        "Initial Capital ($)",
        min_value=1000,
        max_value=1000000,
        value=10000,
        step=1000
    )

    # Strategy-specific parameters
    prices = historical_data['Close']

    if strategy_type == "Buy & Hold":
        strategy_df = TradingStrategies.buy_and_hold(prices, initial_capital)

    elif strategy_type == "SMA Crossover":
        short_window = st.sidebar.slider("Short MA Window", 5, 50, 20)
        long_window = st.sidebar.slider("Long MA Window", 20, 200, 50)
        strategy_df = TradingStrategies.sma_crossover(prices, short_window, long_window, initial_capital)

    elif strategy_type == "Momentum":
        lookback = st.sidebar.slider("Lookback Period (days)", 5, 60, 20)
        strategy_df = TradingStrategies.momentum(prices, lookback, initial_capital)

    else:  # Mean Reversion
        window = st.sidebar.slider("Bollinger Band Window", 10, 50, 20)
        entry_std = st.sidebar.slider("Entry Std Dev", 1.0, 3.0, 2.0, 0.1)
        strategy_df = TradingStrategies.mean_reversion(prices, window, entry_std, initial_capital)

    # Main chart: Price + Strategy Performance
    st.subheader("Asset Price vs Strategy Performance")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add price trace
    fig.add_trace(
        go.Scatter(
            x=strategy_df.index,
            y=strategy_df['Price'],
            name="Asset Price",
            line=dict(color='#1f77b4', width=2)
        ),
        secondary_y=False
    )

    # Add strategy portfolio value trace
    fig.add_trace(
        go.Scatter(
            x=strategy_df.index,
            y=strategy_df['Portfolio_Value'],
            name="Portfolio Value",
            line=dict(color='#2ca02c', width=2)
        ),
        secondary_y=True
    )

    fig.update_layout(
        height=600,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.update_yaxes(title_text="Asset Price ($)", secondary_y=False)
    fig.update_yaxes(title_text="Portfolio Value ($)", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)

    # Performance metrics
    st.subheader("Performance Metrics")

    metrics = PerformanceMetrics.calculate_all_metrics(strategy_df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Return", f"{metrics['Total Return (%)']:.2f}%")
    col2.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
    col3.metric("Max Drawdown", f"{metrics['Max Drawdown (%)']:.2f}%")

    col4, col5, col6 = st.columns(3)
    col4.metric("Annualized Return", f"{metrics['Annualized Return (%)']:.2f}%")
    col5.metric("Volatility", f"{metrics['Volatility (Annual %)']:.2f}%")
    col6.metric("Win Rate", f"{metrics['Win Rate (%)']:.2f}%")

    # Detailed metrics table
    with st.expander("Detailed Metrics"):
        metrics_df = pd.DataFrame.from_dict(metrics, orient='index', columns=['Value'])
        st.dataframe(metrics_df, use_container_width=True)


if __name__ == "__main__":
    render_quant_a_dashboard()
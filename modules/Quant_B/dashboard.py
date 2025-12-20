import streamlit as st
import time
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from modules.Quant_B.qwant_b import (
    fetch_price_series,
    compute_returns,
    compute_portfolio_value,
    max_drawdown,
    annualized_sharpe
)

def render_quant_b_dashboard():
    """Main dashboard for multi assets analysis"""
    st.title("Quant B — Portfolio Analysis")

    st.sidebar.header("Data & Parameters")
    default_tickers = ["AAPL", "MSFT", "GOOGL"]  # example - change to assets you want
    tickers_input = st.sidebar.text_input("Tickers (comma separated)", value=",".join(default_tickers),help="Enter stock tickers separated by commas")
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    period = st.sidebar.selectbox("Historical Period", options=["6mo", "1y", "2y", "5y"], index=1, key="quant_b_period")
    interval = st.sidebar.selectbox("Interval", options=["1d", "1wk", "1mo"], index=0, key="quant_b_interval")

    st.sidebar.markdown("---")
    st.sidebar.header("Portfolio Strategy")
    strategy = st.sidebar.selectbox("Strategy", ["Equal Weight", "Custom Weights", "Buy & Hold"])
    start_capital = st.sidebar.number_input("Start capital (EUR)", value=1_000_000, step=10_000, min_value=1000)

    if strategy == "Custom Weights":
        st.sidebar.write("Enter weights separated by commas (must sum to 1)")
        w_input = st.sidebar.text_input("Weights", value=",".join(["{:.2f}".format(1 / len(tickers))] * len(tickers)))
        try:
            weights = np.array([float(x) for x in w_input.split(",")])
            if len(weights) != len(tickers):
                st.sidebar.error("Number of weights ≠ number of tickers")
            elif abs(weights.sum() - 1.0) > 0.01:
                st.sidebar.warning("Weights don't sum to 1, normalizing...")
                weights = weights / weights.sum()
        except Exception:
            weights = np.array([1 / len(tickers)] * len(tickers))
            st.sidebar.error("Invalid weights, using equal-weight by default")
    else:
        weights = None

    rebal_option = st.sidebar.selectbox("Rebalancing",
                                        ["No rebalancing (Buy&Hold)", "Daily", "Weekly", "Monthly", "Custom days"])
    if rebal_option == "Daily":
        rebal_days = 1
    elif rebal_option == "Weekly":
        rebal_days = 5
    elif rebal_option == "Monthly":
        rebal_days = 21
    elif rebal_option == "Custom days":
        rebal_days = st.sidebar.number_input("Rebalance every X trading days", min_value=1, value=21)
    else:
        rebal_days = None

    # Fetch data
    with st.spinner("Fetching market data..."):
        prices = fetch_price_series(tickers, period=period, interval=interval)

    if prices.empty:
        st.error("No data retrieved — check tickers and connection.")
        st.stop()

    # compute weights
    if strategy == "Equal Weight":
        w = np.array([1 / len(tickers)] * len(tickers))
    elif strategy == "Buy & Hold":
        w = np.array([1 / len(tickers)] * len(tickers))  # initial equal allocation for display; no rebalancing
    elif strategy == "Custom Weights":
        w = weights / np.sum(weights)
    else:
        w = np.array([1 / len(tickers)] * len(tickers))

    # Portfolio valuation
    rebal_days_used = None if (rebal_days is None or strategy == "Buy & Hold") else int(rebal_days)
    portfolio_nav = compute_portfolio_value(prices, w, rebal_freq_days=rebal_days_used, start_capital=start_capital)

    # Metrics
    returns = compute_returns(prices)
    portfolio_returns = portfolio_nav.pct_change().dropna()
    ann_sharpe = annualized_sharpe(portfolio_returns)
    ann_return = (portfolio_nav.iloc[-1] / portfolio_nav.iloc[0]) ** (252 / len(portfolio_nav)) - 1 if len(
        portfolio_nav) > 1 else np.nan
    ann_vol = portfolio_returns.std() * np.sqrt(252)
    mdd = max_drawdown(portfolio_nav)

    # Layout: main plots + side metrics
    col1, col2 = st.columns((3, 1))

    with col1:
        st.subheader("Asset Prices & Portfolio Value")
        fig = go.Figure()
        # asset prices normalized to 1 at start for overlay
        normalized = prices / prices.iloc[0]
        for c in normalized.columns:
            fig.add_trace(go.Scatter(x=normalized.index, y=normalized[c], mode="lines", name=c))
        # add portfolio nav normalized
        norm_portfolio = portfolio_nav / portfolio_nav.iloc[0]
        fig.add_trace(go.Scatter(x=norm_portfolio.index, y=norm_portfolio, mode="lines", name="Portfolio (NAV)",
                                 line=dict(width=3, dash='dash', color='green')))

        fig.update_layout(height=600, xaxis_title="Date", yaxis_title="Normalized value (start=1)",
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Metrics (Portfolio)")
        st.metric("Current NAV", f"{portfolio_nav.iloc[-1]:,.0f} €")
        st.write(f"CAGR (approx): {ann_return:.2%}")
        st.metric("Sharpe Ratio", f"{ann_sharpe:.2f}" if not np.isnan(ann_sharpe) else "N/A")
        st.write(f"Annualized Volatility: {ann_vol:.2%}")
        st.write(f"Max Drawdown: {mdd:.2%}")

    st.markdown("---")
    # Correlation matrix
    st.subheader("Correlation Matrix (Returns)")
    corr = returns.corr()

    fig_corr = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns,
        y=corr.columns,
        colorscale='RdBu',
        zmid=0,
        text=corr.values.round(2),
        texttemplate='%{text}',
        textfont={"size": 10}
    ))
    fig_corr.update_layout(height=400)
    st.plotly_chart(fig_corr, use_container_width=True)

    col_perf1, col_perf2 = st.columns(2)

    with col_perf1:
        st.subheader("Asset Performance")
        perf_table = pd.DataFrame({
            "Ticker": prices.columns,
            "Start Price": prices.iloc[0].round(2),
            "Last Price": prices.iloc[-1].round(2),
            "Total Return": ((prices.iloc[-1] / prices.iloc[0] - 1) * 100).round(2)
        })
        perf_table["Total Return"] = perf_table["Total Return"].astype(str) + "%"
        st.dataframe(perf_table, use_container_width=True, hide_index=True)

    with col_perf2:
        st.subheader("Portfolio Weights")
        w_df = pd.DataFrame({
            "Ticker": prices.columns,
            "Weight": (w * 100).round(2)
        })
        w_df["Weight"] = w_df["Weight"].astype(str) + "%"
        st.dataframe(w_df, use_container_width=True, hide_index=True)

        # Download section
    st.markdown("---")
    st.subheader("Download Data")

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            "Download Prices (.csv)",
            data=prices.to_csv().encode(),
            file_name="prices.csv",
        )
    with col_dl2:
        st.download_button(
            "Download Portfolio NAV (.csv)",
            data=portfolio_nav.to_frame("NAV").to_csv().encode(),
            file_name="portfolio_nav.csv",
        )



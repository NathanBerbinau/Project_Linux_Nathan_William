# qwant_b.py

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from math import sqrt

@st.cache_data(ttl=300)  # cache 5 minutes
@st.cache_data(ttl=300)
def fetch_price_series(tickers, period="1y", interval="1d"):
    data = yf.download(tickers, period=period, interval=interval, progress=False)

    if data is None or len(data) == 0:
        return pd.DataFrame()

    # --- CAS 1 : Multi-index (plusieurs tickers) ---
    if isinstance(data.columns, pd.MultiIndex):
        # Essayer Adj Close
        if ("Adj Close" in data.columns.levels[0]):
            prices = data["Adj Close"]
        # Sinon fallback sur Close
        elif ("Close" in data.columns.levels[0]):
            prices = data["Close"]
        else:
            # fallback ultimate : prendre dernière colonne disponible
            first_level = data.columns.levels[0][0]
            prices = data[first_level]

    # --- CAS 2 : Single-ticker → colonnes simples ---
    else:
        # Priorité à Adj Close
        if "Adj Close" in data.columns:
            prices = data["Adj Close"]
        elif "Close" in data.columns:
            prices = data["Close"]
        else:
            # fallback ultime : prendre n’importe quelle colonne numérique
            prices = data.select_dtypes(include=[np.number]).iloc[:, 0]

        prices = prices.to_frame()
        prices.columns = tickers if isinstance(tickers, list) else [tickers]

    prices = prices.dropna(how="all")
    return prices


def compute_returns(prices):
    return prices.pct_change().dropna()

def compute_portfolio_value(prices, weights, rebal_freq_days=None, start_capital=1_000_000):
    # prices: DataFrame of adj close
    # weights: np.array aligned with columns (sum to 1)
    # rebal_freq_days: None => buy and hold; otherwise int days
    dates = prices.index
    n_assets = prices.shape[1]
    # compute number of shares at each rebal date
    pv = pd.Series(index=dates, dtype=float)  # portfolio value
    if rebal_freq_days is None:
        # buy-and-hold: initial allocation and hold
        init_prices = prices.iloc[0]
        shares = (weights * start_capital) / init_prices
        holdings = prices.mul(shares, axis=1)
        pv = holdings.sum(axis=1)
        return pv
    else:
        # discrete rebalancing
        shares = None
        cash = 0.0
        last_rebal_idx = 0
        current_shares = np.zeros(n_assets)
        for i, date in enumerate(dates):
            if i == 0 or (i - last_rebal_idx) >= rebal_freq_days:
                # rebalance at this date (use close price of this date)
                px = prices.iloc[i]
                current_shares = (weights * start_capital) / px.values
                last_rebal_idx = i
            pv.iloc[i] = (prices.iloc[i].values * current_shares).sum()
        pv.index = dates
        return pv

def annualized_sharpe(returns, risk_free=0.0, periods_per_year=252):
    # returns: daily returns series or DataFrame
    mu = returns.mean() * periods_per_year
    sigma = returns.std() * sqrt(periods_per_year)
    # avoid division by zero
    sharpe = (mu - risk_free) / (sigma.replace(0, np.nan))
    return sharpe

def max_drawdown(series):
    # series: cumulative NAV (pd.Series)
    cum_max = series.cummax()
    drawdown = (series - cum_max) / cum_max
    return drawdown.min()








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

# --- UI ------------------------------------------------------------------
st.set_page_config(page_title="Quant B — Multi-Asset Portfolio", layout="wide")
st.title("Quant B — Multivariate Portfolio Module")

# Auto-refresh every 5 minutes (300000 ms)
from streamlit_autorefresh import st_autorefresh
count = st_autorefresh(interval=300_000, key="autorefresh")  # 5 minutes

# Sidebar controls
st.sidebar.header("Données & paramètres")
default_tickers = ["AAPL", "MSFT", "GOOGL"]  # example - change to assets you want
tickers_input = st.sidebar.text_input("Tickers (comma separated)", value=",".join(default_tickers))
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

period = st.sidebar.selectbox("Historique", options=["6mo", "1y", "2y", "5y"], index=1)
interval = st.sidebar.selectbox("Intervalle", options=["1d", "1wk", "1mo"], index=0)

st.sidebar.markdown("---")
st.sidebar.header("Stratégie portfolio")
strategy = st.sidebar.selectbox("Strategy", ["Equal Weight", "Custom Weights", "Buy & Hold"])
start_capital = st.sidebar.number_input("Start capital (EUR)", value=1_000_000, step=10_000)

if strategy == "Custom Weights":
    st.sidebar.write("Entrez les poids séparés par des virgules (doivent sommer à 1)")
    w_input = st.sidebar.text_input("Poids", value=",".join(["{:.2f}".format(1/len(tickers))]*len(tickers)))
    try:
        weights = np.array([float(x) for x in w_input.split(",")])
        if len(weights) != len(tickers):
            st.sidebar.error("Nombre de poids != nombre de tickers")
    except Exception:
        weights = np.array([1/len(tickers)]*len(tickers))
        st.sidebar.error("Poids invalides, on utilise equal-weight par défaut")
else:
    weights = None

rebal_option = st.sidebar.selectbox("Rebalancing", ["No rebalancing (Buy&Hold)", "Daily", "Weekly", "Monthly", "Custom days"])
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
with st.spinner("Récupération des données..."):
    prices = fetch_price_series(tickers, period=period, interval=interval)

if prices.empty:
    st.error("Aucune donnée récupérée — vérifie les tickers et la connexion.")
    st.stop()

# compute weights
if strategy == "Equal Weight":
    w = np.array([1/len(tickers)]*len(tickers))
elif strategy == "Buy & Hold":
    w = np.array([1/len(tickers)]*len(tickers))  # initial equal allocation for display; no rebalancing
elif strategy == "Custom Weights":
    w = weights / np.sum(weights)
else:
    w = np.array([1/len(tickers)]*len(tickers))

# Portfolio valuation
rebal_days_used = None if (rebal_days is None or strategy == "Buy & Hold") else int(rebal_days)
portfolio_nav = compute_portfolio_value(prices, w, rebal_freq_days=rebal_days_used, start_capital=start_capital)

# Metrics
returns = compute_returns(prices)
portfolio_returns = portfolio_nav.pct_change().dropna()
#ann_sharpe = annualized_sharpe(portfolio_returns)
ann_return = (portfolio_nav.iloc[-1] / portfolio_nav.iloc[0]) ** (252/len(portfolio_nav)) - 1 if len(portfolio_nav)>1 else np.nan
ann_vol = portfolio_returns.std() * sqrt(252)
mdd = max_drawdown(portfolio_nav)

# Layout: main plots + side metrics
col1, col2 = st.columns((3,1))

with col1:
    st.subheader("Prix des actifs & Valeur cumulée du portefeuille")
    fig = go.Figure()
    # asset prices normalized to 1 at start for overlay
    normalized = prices / prices.iloc[0]
    for c in normalized.columns:
        fig.add_trace(go.Scatter(x=normalized.index, y=normalized[c], mode="lines", name=c))
    # add portfolio nav normalized
    norm_portfolio = portfolio_nav / portfolio_nav.iloc[0]
    fig.add_trace(go.Scatter(x=norm_portfolio.index, y=norm_portfolio, mode="lines", name="Portfolio (NAV)", line=dict(width=3, dash='dash')))

    fig.update_layout(height=600, xaxis_title="Date", yaxis_title="Normalized value (start=1)",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Metrics (Portfolio)")
    st.metric("Current NAV", f"{portfolio_nav.iloc[-1]:,.0f} €")
    #st.write(f"Annualized Sharpe (est.): {ann_sharpe:.2f}")
    st.write(f"Annualized Volatility: {ann_vol:.2%}")
    st.write(f"CAGR (approx): {ann_return:.2%}")
    st.write(f"Max Drawdown: {mdd:.2%}")

st.markdown("---")
# Correlation matrix
st.subheader("Matrice de corrélation (retours)")
corr = returns.corr()
st.dataframe(corr.style.format("{:.3f}"))

# Asset performance table
perf_table = pd.DataFrame({
    "Ticker": prices.columns,
    "Start Price": prices.iloc[0].round(4),
    "Last Price": prices.iloc[-1].round(4),
    "Total Return": (prices.iloc[-1] / prices.iloc[0] - 1).round(4)
})
st.subheader("Synthèse actifs")
st.dataframe(perf_table)

# Display portfolio weights used
st.subheader("Poids utilisés")
w_df = pd.DataFrame({"Ticker": prices.columns, "Weight": np.round(w, 4)})
st.table(w_df.set_index("Ticker"))

# Download buttons
st.markdown("---")
st.subheader("Télécharger")
st.download_button("Télécharger prix (.csv)", data=prices.to_csv().encode(), file_name="prices.csv")
st.download_button("Télécharger NAV (.csv)", data=portfolio_nav.to_frame("NAV").to_csv().encode(), file_name="portfolio_nav.csv")

st.info("Module prêt à être intégré dans la page principale. N'oublie pas de créer une branche 'quant-b' et d'ouvrir une PR.")
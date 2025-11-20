import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import numpy as np

class DataFetcher:
    """Fetch and cache financial data for single assets"""

    def __init__(self):
        self.supported_tickers = {
            "ENGI.PA": "Engie (Paris)",
            "EUR=X": "EUR/USD",
            "GC=F": "Gold Futures",
            "BTC-USD": "Bitcoin",
            "^GSPC": "S&P 500"
        }

    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def fetch_realtime_price(_self, ticker: str) -> dict:
        """Fetch current price and basic info"""
        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period="1d", interval="1m")

            if history.empty:
                return None

            return {
                "ticker": ticker,
                "current_price": float(history['Close'].iloc[-1]),
                "timestamp": datetime.now(),
                "open": float(history['Open'].iloc[0]),
                "high": float(history['High'].max()),
                "low": float(history['Low'].min()),
                "volume": int(history['Volume'].sum())
            }
        except Exception as e:
            st.error(f"Error fetching data for {ticker}: {e}")
            return None

    @st.cache_data(ttl=600)
    def fetch_historical_data(_self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """Fetch historical OHLCV data"""
        try:
            data = yf.download(ticker, period=period, progress=False)
            return data
        except Exception as e:
            st.error(f"Error fetching historical data: {e}")
            return pd.DataFrame()
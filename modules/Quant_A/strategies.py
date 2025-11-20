import pandas as pd
import numpy as np
class TradingStrategies:
    """Implementation of various backtesting strategies"""

    @staticmethod
    def buy_and_hold(prices: pd.Series, initial_capital: float = 10000) -> pd.DataFrame:
        """
        Simple buy and hold strategy

        Args:
            prices: Series of closing prices
            initial_capital: Starting capital

        Returns:
            DataFrame with position, returns, and cumulative value
        """
        df = pd.DataFrame(index=prices.index)
        df['Price'] = prices
        df['Position'] = 1.0  # Always long
        df['Returns'] = prices.pct_change()
        df['Strategy_Returns'] = df['Returns'] * df['Position']
        df['Cumulative_Returns'] = (1 + df['Strategy_Returns']).cumprod()
        df['Portfolio_Value'] = initial_capital * df['Cumulative_Returns']

        return df

    @staticmethod
    def sma_crossover(prices: pd.Series, short_window: int = 20,
                      long_window: int = 50, initial_capital: float = 10000) -> pd.DataFrame:
        """
        Simple Moving Average crossover strategy

        Buy signal: Short MA crosses above Long MA
        Sell signal: Short MA crosses below Long MA
        """
        df = pd.DataFrame(index=prices.index)
        df['Price'] = prices
        df['SMA_Short'] = prices.rolling(window=short_window).mean()
        df['SMA_Long'] = prices.rolling(window=long_window).mean()

        # Generate signals
        df['Signal'] = 0.0
        df.loc[df['SMA_Short'] > df['SMA_Long'], 'Signal'] = 1.0  # Long
        df.loc[df['SMA_Short'] <= df['SMA_Long'], 'Signal'] = 0.0  # Exit

        # Calculate returns
        df['Position'] = df['Signal'].shift(1)  # Trade on next day
        df['Returns'] = prices.pct_change()
        df['Strategy_Returns'] = df['Returns'] * df['Position']
        df['Cumulative_Returns'] = (1 + df['Strategy_Returns']).cumprod()
        df['Portfolio_Value'] = initial_capital * df['Cumulative_Returns']

        return df

    @staticmethod
    def momentum(prices: pd.Series, lookback: int = 20,
                 initial_capital: float = 10000) -> pd.DataFrame:
        """
        Momentum strategy: Buy if price > price N days ago
        """
        df = pd.DataFrame(index=prices.index)
        df['Price'] = prices
        df['Momentum'] = prices - prices.shift(lookback)

        # Generate signals
        df['Signal'] = 0.0
        df.loc[df['Momentum'] > 0, 'Signal'] = 1.0
        df.loc[df['Momentum'] <= 0, 'Signal'] = 0.0

        # Calculate returns
        df['Position'] = df['Signal'].shift(1)
        df['Returns'] = prices.pct_change()
        df['Strategy_Returns'] = df['Returns'] * df['Position']
        df['Cumulative_Returns'] = (1 + df['Strategy_Returns']).cumprod()
        df['Portfolio_Value'] = initial_capital * df['Cumulative_Returns']

        return df

    @staticmethod
    def mean_reversion(prices: pd.Series, window: int = 20,
                       entry_std: float = 2.0, initial_capital: float = 10000) -> pd.DataFrame:
        """
        Mean reversion strategy using Bollinger Bands

        Buy when price < lower band
        Sell when price > upper band
        """
        df = pd.DataFrame(index=prices.index)
        df['Price'] = prices
        df['SMA'] = prices.rolling(window=window).mean()
        df['STD'] = prices.rolling(window=window).std()
        df['Upper_Band'] = df['SMA'] + (entry_std * df['STD'])
        df['Lower_Band'] = df['SMA'] - (entry_std * df['STD'])

        # Generate signals
        df['Signal'] = 0.0
        df.loc[df['Price'] < df['Lower_Band'], 'Signal'] = 1.0  # Buy
        df.loc[df['Price'] > df['Upper_Band'], 'Signal'] = -1.0  # Sell/Short
        df['Signal'] = df['Signal'].replace(0, np.nan).ffill().fillna(0)

        # Calculate returns
        df['Position'] = df['Signal'].shift(1)
        df['Returns'] = prices.pct_change()
        df['Strategy_Returns'] = df['Returns'] * df['Position']
        df['Cumulative_Returns'] = (1 + df['Strategy_Returns']).cumprod()
        df['Portfolio_Value'] = initial_capital * df['Cumulative_Returns']

        return df

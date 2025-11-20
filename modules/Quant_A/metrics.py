import pandas as pd
import numpy as np

class PerformanceMetrics:
    """Calculate trading strategy performance metrics"""

    @staticmethod
    def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """
        Calculate annualized Sharpe ratio

        Args:
            returns: Series of strategy returns
            risk_free_rate: Annual risk-free rate

        Returns:
            Sharpe ratio
        """
        excess_returns = returns - risk_free_rate/252  # Daily risk-free rate
        if excess_returns.std() == 0:
            return 0.0
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

    @staticmethod
    def max_drawdown(cumulative_returns: pd.Series) -> dict:
        """
        Calculate maximum drawdown

        Returns:
            Dictionary with max_drawdown (%), peak date, trough date
        """
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - running_max) / running_max * 100

        max_dd = drawdown.min()
        max_dd_date = drawdown.idxmin()

        # Find peak before max drawdown
        peak_date = running_max[:max_dd_date].idxmax()

        return {
            "max_drawdown_pct": max_dd,
            "peak_date": peak_date,
            "trough_date": max_dd_date
        }

    @staticmethod
    def calculate_all_metrics(strategy_df: pd.DataFrame) -> dict:
        """Calculate comprehensive performance metrics"""
        returns = strategy_df['Strategy_Returns'].dropna()
        cum_returns = strategy_df['Cumulative_Returns'].iloc[-1] - 1

        metrics = {
            "Total Return (%)": cum_returns * 100,
            "Annualized Return (%)": (1 + cum_returns) ** (252 / len(returns)) - 1 if len(returns) > 0 else 0,
            "Volatility (Annual %)": returns.std() * np.sqrt(252) * 100,
            "Sharpe Ratio": PerformanceMetrics.sharpe_ratio(returns),
            "Max Drawdown (%)": PerformanceMetrics.max_drawdown(strategy_df['Cumulative_Returns'])["max_drawdown_pct"],
            "Win Rate (%)": (returns > 0).sum() / len(returns) * 100 if len(returns) > 0 else 0,
            "Best Day (%)": returns.max() * 100,
            "Worst Day (%)": returns.min() * 100
        }

        return metrics
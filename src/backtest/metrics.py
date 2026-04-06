import pandas as pd
import numpy as np
from typing import List, Dict

def total_return(portfolio_values: pd.Series) -> float:
    if len(portfolio_values) == 0: return 0.0
    return (portfolio_values.iloc[-1] - portfolio_values.iloc[0]) / portfolio_values.iloc[0]

def annualized_return(portfolio_values: pd.Series, trading_days=242) -> float:
    tr = total_return(portfolio_values)
    days = len(portfolio_values)
    if days == 0: return 0.0
    return (1 + tr) ** (trading_days / days) - 1

def max_drawdown(portfolio_values: pd.Series) -> float:
    if len(portfolio_values) == 0: return 0.0
    roll_max = portfolio_values.expanding().max()
    drawdown = (portfolio_values - roll_max) / roll_max
    return drawdown.min()

def sharpe_ratio(returns: pd.Series, risk_free=0.03, trading_days=242) -> float:
    if len(returns) == 0 or returns.std() == 0: return 0.0
    excess_returns = returns - risk_free / trading_days
    return np.sqrt(trading_days) * excess_returns.mean() / returns.std()

def sortino_ratio(returns: pd.Series, risk_free=0.03, trading_days=242) -> float:
    if len(returns) == 0: return 0.0
    excess_returns = returns - risk_free / trading_days
    downside_returns = excess_returns[excess_returns < 0]
    if len(downside_returns) == 0 or downside_returns.std() == 0: return 0.0
    return np.sqrt(trading_days) * excess_returns.mean() / downside_returns.std()

def win_rate(trades: List[Dict]) -> float:
    if not trades: return 0.0
    winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
    return len(winning_trades) / len(trades)

def profit_loss_ratio(trades: List[Dict]) -> float:
    winning_pnl = [t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0]
    losing_pnl = [abs(t.get('pnl', 0)) for t in trades if t.get('pnl', 0) <= 0]
    
    avg_win = sum(winning_pnl) / len(winning_pnl) if winning_pnl else 0
    avg_loss = sum(losing_pnl) / len(losing_pnl) if losing_pnl else 0
    
    if avg_loss == 0: return float('inf') if avg_win > 0 else 0.0
    return avg_win / avg_loss

def calmar_ratio(ann_return: float, max_dd: float) -> float:
    if max_dd == 0: return float('inf') if ann_return > 0 else 0.0
    return ann_return / abs(max_dd)

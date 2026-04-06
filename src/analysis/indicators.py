import pandas as pd
import numpy as np

def ma(series: pd.Series, period: int) -> pd.Series:
    """简单移动平均 (Simple Moving Average)"""
    return series.rolling(window=period, min_periods=max(1, period//2)).mean()

def ema(series: pd.Series, period: int) -> pd.Series:
    """指数移动平均 (Exponential Moving Average)"""
    return series.ewm(span=period, adjust=False).mean()

def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD (Moving Average Convergence Divergence)"""
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    dif = ema_fast - ema_slow
    dea = ema(dif, signal)
    macd_bar = (dif - dea) * 2
    return dif, dea, macd_bar

def kdj(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 9, m1: int = 3, m2: int = 3):
    """KDJ 随机指标"""
    run_min = low.rolling(window=n, min_periods=1).min()
    run_max = high.rolling(window=n, min_periods=1).max()
    rsv = (close - run_min) / (run_max - run_min + 1e-8) * 100
    
    # 采用 ewm 平滑
    k = rsv.ewm(com=m1-1, adjust=False).mean()
    d = k.ewm(com=m2-1, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """RSI (Relative Strength Index)"""
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    
    # Wilder's moving average
    roll_up = up.ewm(com=period-1, adjust=False).mean()
    roll_down = down.ewm(com=period-1, adjust=False).mean()
    
    rs = roll_up / (roll_down + 1e-8)
    return 100 - (100 / (1 + rs))

def bollinger(close: pd.Series, period: int = 20, std_dev: float = 2.0):
    """Bollinger Bands (布林带)"""
    middle = close.rolling(window=period, min_periods=max(1, period//2)).mean()
    std = close.rolling(window=period, min_periods=max(1, period//2)).std()
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return upper, middle, lower

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """ATR (Average True Range)"""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    return tr.ewm(com=period-1, adjust=False).mean()

def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """OBV (On-Balance Volume)"""
    direction = np.sign(close.diff().fillna(0))
    # 若平盘则 direction 为 0，成交量不参与累加
    obv_values = (volume * direction).cumsum()
    return obv_values

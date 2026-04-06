import pandas as pd
import numpy as np
import pytest
from src.analysis import indicators

def test_ma():
    s = pd.Series([1, 2, 3, 4, 5])
    res = indicators.ma(s, 3)
    np.testing.assert_allclose(res.values, [1., 1.5, 2., 3., 4.])

def test_ema():
    s = pd.Series([1, 2, 3, 4, 5])
    res = indicators.ema(s, 3)
    assert len(res) == 5
    assert not pd.isna(res.iloc[0])

def test_macd():
    close = pd.Series(np.random.randn(50).cumsum())
    dif, dea, macd_bar = indicators.macd(close)
    assert len(dif) == 50
    assert len(dea) == 50
    assert len(macd_bar) == 50

def test_rsi():
    close = pd.Series(np.linspace(10, 20, 20)) # 一直涨，RSI应该是100
    res = indicators.rsi(close, 14)
    # 因为有平滑，最开始可能由于默认值而不完全等于100，但后期逼近
    assert res.iloc[-1] > 90

def test_bollinger():
    close = pd.Series(np.random.randn(50).cumsum())
    upper, middle, lower = indicators.bollinger(close, 20, 2)
    assert len(upper) == 50
    # upper 应该大于 lower
    assert (upper.dropna() >= lower.dropna()).all()

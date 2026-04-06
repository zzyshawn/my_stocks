import pandas as pd
import numpy as np
import pytest
from src.backtest import BacktestEngine, Strategy

class MTFTestStrategy(Strategy):
    def __init__(self):
        self.triggered_periods = []

    def init(self, engine):
        pass

    def on_bar(self, period, bar, engine):
        self.triggered_periods.append((period, bar.name))

def test_multitf_alignment():
    # 模拟数据
    # daily: 2天
    idx_d = pd.to_datetime(['2023-01-01 15:00:00', '2023-01-02 15:00:00'])
    df_d = pd.DataFrame({'收盘': [10, 11]}, index=idx_d)

    # min30: 第1天2根，第2天2根
    idx_m30 = pd.to_datetime([
        '2023-01-01 14:00:00', '2023-01-01 15:00:00',
        '2023-01-02 14:00:00', '2023-01-02 15:00:00'
    ])
    df_m30 = pd.DataFrame({'收盘': [9.5, 10, 10.5, 11]}, index=idx_m30)

    engine = BacktestEngine(symbol="TEST")
    engine.set_data({"daily": df_d, "min30": df_m30})
    strategy = MTFTestStrategy()
    engine.set_strategy(strategy)
    
    engine.run()
    
    # 验证事件触发总数
    assert len(strategy.triggered_periods) == 6
    
    # 期望触发顺序：14:00 (m30) -> 15:00 (m30) -> 15:00 (d) -> 14:00(m30) -> 15:00(m30) -> 15:00(d)
    expected = [
        ('min30', pd.Timestamp('2023-01-01 14:00:00')),
        ('min30', pd.Timestamp('2023-01-01 15:00:00')),
        ('daily', pd.Timestamp('2023-01-01 15:00:00')),
        ('min30', pd.Timestamp('2023-01-02 14:00:00')),
        ('min30', pd.Timestamp('2023-01-02 15:00:00')),
        ('daily', pd.Timestamp('2023-01-02 15:00:00'))
    ]
    
    assert strategy.triggered_periods == expected

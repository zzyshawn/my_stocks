import pandas as pd
import numpy as np
import pytest
from src.backtest import BacktestEngine, Strategy

class BuyHoldStrategy(Strategy):
    def init(self, engine):
        pass
    def on_bar(self, bar, engine):
        pos = engine.portfolio.positions.get(engine.symbol)
        if not pos or pos.shares == 0:
            # 简化全买
            price = bar['收盘']
            shares = int(engine.portfolio.cash / price // 100) * 100
            if shares > 0:
                engine.buy(shares)

def test_backtest_engine_run():
    # 构造一段只涨不跌的数据
    dates = pd.date_range('2023-01-01', periods=10)
    df = pd.DataFrame({
        '收盘': np.linspace(10, 20, 10)
    }, index=dates)

    engine = BacktestEngine(symbol="TEST", initial_capital=100000)
    engine.set_data(df)
    engine.set_strategy(BuyHoldStrategy())
    
    res = engine.run()
    
    assert len(res.trades) == 1
    assert res.trades[0].direction == 'BUY'
    
    metrics = res.metrics
    assert 'total_return' in metrics
    # 应该赚钱
    assert metrics['total_return'] > 0
    # 最大回撤应该是 0
    assert metrics['max_drawdown'] == 0.0

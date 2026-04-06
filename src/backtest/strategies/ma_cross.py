import pandas as pd
from ..engine import Strategy
from ...analysis.indicators import ma

class MACrossStrategy(Strategy):
    """双均线交叉策略"""
    def __init__(self, fast=5, slow=20):
        self.fast_period = fast
        self.slow_period = slow
        self.data_fast = None
        self.data_slow = None
        
    def init(self, engine):
        # 预先计算所有 MA
        df = engine.data['default']
        self.data_fast = ma(df['收盘'], self.fast_period)
        self.data_slow = ma(df['收盘'], self.slow_period)

    def on_bar(self, period: str, bar: pd.Series, engine):
        if period != 'default': return
        date = bar.name
        price = bar['收盘']
        
        fast = self.data_fast.loc[date]
        slow = self.data_slow.loc[date]
        
        # 简单持仓逻辑：上穿全仓买入，下穿全部卖出
        pos = engine.portfolio.positions.get(engine.symbol)
        current_shares = pos.shares if pos else 0
        
        if pd.notna(fast) and pd.notna(slow):
            if fast > slow and current_shares == 0:
                # 全量买入 (向下取整到100股)
                available_cash = engine.portfolio.cash
                shares_to_buy = int(available_cash / (price * (1+engine.broker.slippage)) // 100) * 100
                if shares_to_buy > 0:
                    engine.buy(shares_to_buy)
            elif fast < slow and current_shares > 0:
                # 全仓卖出
                engine.sell(current_shares)

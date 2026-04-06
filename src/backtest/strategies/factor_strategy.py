import pandas as pd
from typing import List, Union
from ..engine import Strategy
from ...analysis.factors import Factor, FactorEngine

class FactorStrategy(Strategy):
    """单因子/多因子策略基类示例"""
    def __init__(self, factor_engine: FactorEngine, buy_threshold=0.8, sell_threshold=0.2):
        self.factor_engine = factor_engine
        self.buy_threshold = buy_threshold 
        self.sell_threshold = sell_threshold
        self.factor_df = None

    def init(self, engine):
        # 回测前计算所有因子
        self.factor_df = self.factor_engine.compute_all(engine.data['default'])
        # 用前一天的因子值决定今天的交易，以此避免使用未来函数
        self.factor_df = self.factor_df.shift(1)

    def on_bar(self, period: str, bar: pd.Series, engine):
        if period != 'default': return
        date = bar.name
        price = bar['收盘']
        
        # 获取昨日因子值
        factors = self.factor_df.loc[date]
        
        # 这个示例简化为：将多个因子的值标准化并简单求和作为最终得分
        # (真实情况可能会动态计算横截面分位数或进行滚动 z-score)
        # 这里仅作演示，假设我们只看一个主因子 MOM_20（动量）
        
        score = factors.get('MOM_20', 0)
        
        pos = engine.portfolio.positions.get(engine.symbol)
        current_shares = pos.shares if pos else 0
        
        if pd.notna(score):
            # 动量大于0买入，小于0卖出
            if score > 0.05 and current_shares == 0:
                available_cash = engine.portfolio.cash
                shares = int(available_cash / (price * (1+engine.broker.slippage)) // 100) * 100
                if shares > 0:
                    engine.buy(shares)
            elif score < -0.05 and current_shares > 0:
                engine.sell(current_shares)

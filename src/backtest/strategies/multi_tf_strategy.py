import pandas as pd
from ..engine import Strategy

class MultiTFStrategy(Strategy):
    """
    多周期共振策略示例
    逻辑：
    1. 在 daily 级别判断大趋势（例如当前收盘价 > 昨收盘价，或某均线上方），为了简单，只用 "收盘价变化" 判断趋势向上。
    2. 在 min30 级别判断入场点（比如当前收盘价突破当天均价，此处简化为 min30的收盘价与开盘价的关系）。
    """
    def __init__(self):
        self.daily_trend_up = False
        
    def init(self, engine):
        pass

    def on_bar(self, period: str, bar: pd.Series, engine):
        date = bar.name
        price = bar['收盘']
        
        # 1. 记录日常趋势
        if period == 'daily':
            # 获取昨日数据（这里用引擎提供的一般方法获取可能会有未来函数，
            # 这里简化直接判断当天的涨跌，真实大周期趋势最好看缓存的昨日或早些时候的 bar）
            open_p, close_p = bar['开盘'], bar['收盘']
            self.daily_trend_up = close_p > open_p
            return
            
        # 2. 如果是 30 分钟，执行买卖交易
        if period == 'min30':
            pos = engine.portfolio.positions.get(engine.symbol)
            current_shares = pos.shares if pos else 0
            
            # 由于可能在盘中并没有最新的 daily_trend_up（每日结束才更新 daily_trend_up），
            # 实际上更标准的做法是: 在 30min bar 获取 'daily' 上一根已经确定的 bar。
            # engine.get_latest_bar('daily') 返回昨天收盘确定的日线。
            latest_daily = engine.get_latest_bar('daily')
            trend_is_good = False
            if latest_daily is not None:
                trend_is_good = latest_daily['收盘'] > latest_daily['开盘']
            
            # 买入逻辑：昨日日线收阳，且当前30分钟K线收阳
            is_30m_bull = bar['收盘'] > bar['开盘']
            is_30m_bear = bar['收盘'] < bar['开盘']
            
            if trend_is_good and is_30m_bull and current_shares == 0:
                available_cash = engine.portfolio.cash
                shares = int(available_cash / (price * (1+engine.broker.slippage)) // 100) * 100
                if shares > 0:
                    engine.buy(shares)
            
            # 卖出逻辑：如果30分钟收阴，则平仓
            elif is_30m_bear and current_shares > 0:
                engine.sell(current_shares)

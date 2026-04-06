import pandas as pd
from typing import Dict, Any

try:
    from qlib.backtest import backtest, executor
    from qlib.backtest.executor import SimulatorExecutor
    from qlib.strategy.base import BaseStrategy
    from qlib.contrib.evaluate import risk_analysis
except ImportError:
    pass

class QlibBacktestEngine:
    """包装 QLib 原生回测执行器的接口引擎"""
    
    def __init__(self, start_time: str, end_time: str, init_cash: float = 1000000.0, 
                 deal_price: str = 'close', freq: str = 'day'):
        """
        :param start_time: 回测开始时间，如 "2020-01-01"
        :param end_time: 回测结束时间，如 "2023-01-01"
        :param init_cash: 初始资金
        :param deal_price: 撮合价格，通常用 "close" 或 "open"
        :param freq: 撮合频率，"day", "1min", "5min"
        """
        self.start_time = start_time
        self.end_time = end_time
        self.init_cash = init_cash
        self.freq = freq
        
        # 内部 Executor 配置
        self.executor_config = {
            "class": "SimulatorExecutor",
            "module_path": "qlib.backtest.executor",
            "kwargs": {
                "time_per_step": freq,
                "generate_portfolio_metrics": True,
                "verbose": True
            },
        }
        
        # 交易账号与手续费设定 (中国 A 股标准)
        self.exchange_kwargs = {
            "freq": freq,
            "limit_threshold": 0.099, # 涨跌停限制
            "deal_price": deal_price,
            "open_cost": 0.0003,      # 买入手续费
            "close_cost": 0.0013,     # 卖出手续费+印花税
            "min_cost": 5             # 最小费用
        }
        
        self.strategy = None

    def set_strategy(self, strategy: Any):
        """
        设置原生 Qlib 的 Strategy 对象，
        例如 TopkDropoutStrategy 或自定义的继承自 BaseStrategy 的策略
        """
        self.strategy = strategy

    def run(self) -> tuple:
        """
        执行原生的 QLib 回测并生成收益风控指标
        :return: (portfolio_metrics, indicator_dict) 
        - portfolio_metrics 记录了每日账户价值流水
        - indicator_dict 记录了夏普比率、最大回撤、年化收益等
        """
        if self.strategy is None:
            raise ValueError("Strategy is not set. Call `set_strategy_config` first.")
            
        return_dict, indicator_dict = backtest(
            executor=self.executor_config,
            strategy=self.strategy,
            start_time=self.start_time,
            end_time=self.end_time,
            benchmark="SH000300" # 假设基准为沪深300
        )
        
        return return_dict, indicator_dict


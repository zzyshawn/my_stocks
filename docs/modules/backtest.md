# 回测模块 (`my_stocks.src.backtest`)

提供本地纯 Python 实现的事件驱动型回测引擎，支持因子策略与传统技术指标策略回测。

## 架构

- `BacktestEngine`: 核心回测引擎，负责行情步进、订单路由与状态保存。
- `Portfolio`: 资金与持仓管理模块。
- `Broker`: 模拟撮合系统，处理滑点和交易摩擦成分（印花税及佣金）。
- `Strategy`: 抽象基类，用户需继承并实现 `init()` 和 `on_bar()`。
- `BacktestReport`: 负责生成指标和Markdown格式分析报告。

## 使用示例

```python
from src.data import load_kline
from src.backtest import BacktestEngine, BacktestReport
from src.backtest.strategies import MACrossStrategy

df = load_kline("000001", "daily")

# 实例化引擎
engine = BacktestEngine(symbol="000001", initial_capital=1000000)
engine.set_data(df)
engine.set_strategy(MACrossStrategy(fast=5, slow=20))

# 运行回测并获取结果
result = engine.run()
result.summary()

# 生成报告
report = BacktestReport(result)
report.to_markdown("backtest_000001.md")
```
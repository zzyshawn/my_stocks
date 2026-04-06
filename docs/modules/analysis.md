# 技术分析与因子模块 (`my_stocks.src.analysis`)

提供经典技术指标计算以及类似 QLib 风格的 Alpha 因子挖掘。目前采用纯 pandas 和 numpy 实现，不依赖 TA-Lib。

## 子模块

- `indicators.py`: 基础技术指标（MA, EMA, MACD, KDJ, RSI, BOLL, ATR, OBV）。
- `factors.py`: 因子库及因子计算引擎 (`FactorEngine`)，支持内置因子。
- `factor_analyzer.py`: 因子性能分析，包含单资产时序 IC 或多资产截面 IC 分析扩展设计。

## 使用示例

### 技术指标

```python
from src.analysis import ma, macd

dif, dea, macd_bar = macd(df['收盘'])
ma20 = ma(df['收盘'], 20)
```

### 因子引擎

```python
from src.analysis import FactorEngine

engine = FactorEngine()
engine.load_builtin("alpha158")
factor_df = engine.compute_all(df)
print(factor_df.head())
```
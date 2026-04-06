# Python 缠论画线功能

基于Python开发的缠论技术分析工具，提供K线缠论画线功能。

## 功能特性

- K线数据处理和特征提取
- 缠论核心概念实现（笔、线段、中枢）
- 自动画线算法
- 多种可视化支持
- 技术指标计算

## 安装依赖

```bash
pip install -r requirements.txt
```

## 项目结构

```
├── chanlun/
│   ├── core/           # 核心数据结构
│   ├── algorithms/     # 算法实现
│   ├── visualization/  # 可视化模块
│   └── utils/          # 工具函数
├── examples/           # 使用示例
├── tests/              # 测试用例
└── data/               # 示例数据
```

## 快速开始

```python
from chanlun.core import ChanLunAnalyzer
from chanlun.visualization import plot_kline_with_chanlun

# 创建分析器
analyzer = ChanLunAnalyzer()

# 分析K线数据
result = analyzer.analyze(kline_data)

# 可视化结果
plot_kline_with_chanlun(kline_data, result)
```
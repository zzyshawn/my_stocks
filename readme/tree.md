# 项目目录结构

## 概览

my_stocks 智能股票分析系统 - 一个基于 Python 的量化交易系统，包含数据获取、分析、回测和决策模块。

## 目录树

```
.
├── config                      # 配置文件目录
├── docs                        # 文档目录
│   └── modules                 # 模块文档
├── readme                      # 项目说明和任务追踪
├── scripts                     # 脚本工具
├── src                         # 源代码目录
│   ├── analysis                # 分析模块
│   ├── backtest                # 回测模块
│   │   └── strategies          # 回测策略
│   ├── communication           # 通讯模块
│   ├── data                    # 数据模块
│   │   ├── history             # 历史数据
│   │   ├── history_demo        # 历史数据演示
│   │   ├── history_tdx         # 通达信历史数据
│   │   ├── qlib_data           # Qlib 数据
│   │   ├── realtime            # 实时数据
│   │   └── realtime_demo       # 实时数据演示
│   ├── decision                # 决策模块
│   ├── knowledge               # 知识库模块
│   ├── models                  # 模型目录
│   ├── python-biduan           # Python 笔端模块
│   │   ├── chanlun             # 缠论模块
│   │   ├── config_docs         # 配置文档
│   │   └── excel_export        # Excel 导出
│   ├── python-biduan_demo      # Python 笔端演示
│   │   ├── chanlun             # 缠论演示
│   │   ├── config_docs         # 配置文档
│   │   ├── data_output         # 数据输出
│   │   ├── debug               # 调试
│   │   ├── debug_output        # 调试输出
│   │   ├── examples            # 示例
│   │   ├── excel_export        # Excel 导出
│   │   ├── test_output         # 测试输出
│   │   └── tests               # 测试
│   ├── simulation              # 实时模拟编排模块
│   │   ├── analysis_runner.py  # 模块3 指标/缠论输出编排
│   │   ├── data_preparation.py # 旧版数据准备实现
│   │   ├── realtime_generator.py # 模块2 单日实时K线生成
│   │   ├── splitter.py         # 模块1 历史数据拆分
│   │   └── test_data_preparation.py # 旧版数据准备测试
│   └── utils                   # 工具模块
├── tests                       # 测试目录
│   ├── test_analysis_runner_603906.py      # 模块3联调验证
│   ├── test_realtime_generator_603906.py   # 模块2验证
│   ├── test_single_day_realtime_print_603906.py # 单日逐步打印验证
│   └── test_splitter_603906.py             # 模块1验证
└── tmp_data                    # 临时数据
    └── 涨停数据                # 涨停数据
```

## 模块说明

### analysis
- **路径**: src/analysis/
- **功能**: 股票分析模块，提供技术指标计算和因子分析
- **关键文件**:
  - `indicators.py` - 技术指标
  - `factors.py` - 因子分析
  - `factor_analyzer.py` - 因子分析器

### backtest
- **路径**: src/backtest/
- **功能**: 回测引擎和策略执行
- **关键文件**:
  - `engine.py` - 回测引擎
  - `strategies/` - 回测策略集合
  - `metrics.py` - 回测指标
  - `report.py` - 回测报告

### data
- **路径**: src/data/
- **功能**: 数据获取和管理，包括历史和实时数据
- **关键文件**:
  - `history/` - 历史数据获取
  - `realtime/` - 实时数据获取
  - `knowledge/` - 知识存储和模板

### decision
- **路径**: src/decision/
- **功能**: 交易决策模块
- **关键文件**:
  - `realtime_agent_interface.py` - 实时 Agent 接口占位

### simulation
- **路径**: src/simulation/
- **功能**: 实时模拟编排模块，负责数据拆分、单日实时生成、指标/缠论编排
- **关键文件**:
  - `splitter.py` - 模块1 历史数据拆分
  - `realtime_generator.py` - 模块2 单日实时K线与回调入口
  - `analysis_runner.py` - 模块3 指标/缠论输出编排
  - `data_preparation.py` - 旧版模拟实现

### models
- **路径**: src/models/
- **功能**: 机器学习模型

### python-biduan
- **路径**: src/python-biduan/
- **功能**: 缠论分析模块，提供K线笔段分析
- **关键文件**:
  - `chanlun/` - 缠论核心算法
  - `excel_export/` - Excel导出功能

## 更新记录

- 2026-03-29: 增加 simulation 模块、模块1~3测试文件与 decision 接口说明
- 2026-03-25: 初始版本创建

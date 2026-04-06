# 任务: 缠论实时交易模拟系统

## 信息
- **创建时间**: 2026-03-26
- **状态**: in_progress
- **优先级**: high

## 进度历史

### 2026-04-01 JSON结构与多股票编排更新
- **状态**: in_progress
- **进度**: 完成单股票/多股票 JSON 外形重构、IPC 重试与主要指标补全
- **备注**:
  - 单股票 JSON 顶层去掉 `now`
  - 多股票 JSON 新增 `now + field_descriptions + stocks`
  - 单股票阶段只生成 history JSON，不发送 IPC
  - 多股票 step 合并后才发送 `DATA_READY`
  - `splitter` 改为每次覆盖切分，不复用旧 `_1/_2`
  - `analysis.max_records` 从 3000 降到 1000
  - 已新增耗时打印：`[SPLIT]` / `[ANALYSIS]` / `[STEP]`
  - 缠论字段优先从生成的 `*_chanlun.xlsx` 行数据回读
  - 已补主要指标：MA、RSI_L6/H6、MACD、VOL、换手率、量比、VOL_MA5/20、VWAP
  - 下一步重点：realtime 模式真实链路接线与整体验证

### 2026-03-30 模块3与编排层更新
- **状态**: in_progress
- **进度**: 完成 JSON 打包与 simulation orchestrator 第一版骨架
- **备注**:
  - 新增 `src/simulation/orchestrator.py`
  - 新增每步 JSON 打包 `StepDataPackager`
  - JSON 保存目录区分 `real` / `backtest`
  - 通知协议固定为 `DATA_READY + data_path + user_id + conversation_id`
  - `analysis_runner` 已补充结构化摘要，供 JSON 组装复用
  - 下一步实现 realtime 模式 `_1` 基线复制与真实 IPC Client 发送

### 2026-03-29 模块3阶段更新
- **状态**: in_progress
- **进度**: 完成模块3第一版 - 指标/缠论输出编排与配置化
- **备注**:
  - 新增 `src/simulation/analysis_runner.py`
  - 输出统一到 `backtest/out/real` 与 `backtest/out/test`
  - `test` 支持 debug 过程目录保留
  - `test` 输出前按配置截窗：日线30根、30分钟240根、5分钟1440根
  - 已接入 `realtime_generator.step_callback`

### 2026-03-26 模块1完成
- **状态**: in_progress
- **进度**: 完成模块1 - 数据准备模块 (src/simulation/data_preparation.py)
- **备注**:
  - 成功实现数据读取、分割、保存功能
  - 测试603906通过，生成6个分割文件
  - 支持日线/30分钟/5分钟多周期处理

### 2026-03-26 规划完成
- **状态**: pending → in_progress
- **进度**: 完成详细设计文档 (C:\Users\zzy\.claude\plans\composed-inventing-alpaca.md)
- **备注**: 计划已审批，开始实现

## 待办事项

### P0 - 核心模块
- [x] 子任务1: 详细设计文档编写
- [x] 子任务2: 模块1 - 数据准备模块 (读取配置、数据分割)
- [x] 子任务3: 模块2 - 缠论分析验证模块 (生成参考文件)
- [x] 子任务4: 模块3 - 技术指标生成模块 (全量指标计算)

### P1 - 实时模拟模块
- [ ] 子任务5: 模块4 - 实时数据生成 (逐根模拟、多时间框架)
- [ ] 子任务6: 模块5 - 实时缠论分析 (累积模式)

### P2 - Agent与回测
- [ ] 子任务7: 模块6 - 模拟交易 (Agent接口预留)
- [ ] 子任务8: 模块7 - 评价指标模块
- [ ] 子任务9: 模块8 - 多股循环与组合配置

## 相关文件
- 设计文档: C:\Users\zzy\.claude\plans\composed-inventing-alpaca.md
- 配置: config/config.yaml
- 数据: H:/股票信息/股票数据库/daban/股票数据
- 缠论核心: src/python-biduan/chanlun/core/analyzer.py
- Excel导出: src/python-biduan/excel_export/export_to_excel.py

## 当前工作
已完成: **模块1 - 数据准备模块**、**模块2 - 单日实时K线与拼接**、**模块3第一版 - 指标/缠论输出编排**
下一步: **模块4 - 单日 Agent + 日终评估接口与验证流程**

## 备注
- 复用现有 `src/utils/config.py` 配置管理器
- 复用 `src/python-biduan` 缠论分析代码
- 所有路径从配置读取，不硬编码

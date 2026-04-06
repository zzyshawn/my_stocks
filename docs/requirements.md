# My Stocks 需求分析文档

## 项目概述

### 项目背景
构建一个智能股票分析系统，集成实时数据获取、技术分析、决策支持、通信通知、回测验证和知识总结等功能，为投资者提供全面的股票分析工具。

### 项目目标
- 提供实时、准确的股票数据获取能力
- 实现多维度技术分析
- 提供智能化的投资决策支持
- 支持多渠道消息推送
- 支持策略回测验证
- 实现知识沉淀与总结

---

## 文档索引

### 模块需求文档

| 模块 | 文档路径 | 说明 |
|------|----------|------|
| 数据模块 | [modules/data.md](modules/data.md) | 数据获取、数据源、数据合并 |
| 技术分析模块 | [modules/analysis.md](modules/analysis.md) | 技术指标计算、形态识别 |
| 决策模块 | [modules/decision.md](modules/decision.md) | 信号生成、策略管理 |
| 通信模块 | [modules/communication.md](modules/communication.md) | 消息推送、通知管理 |
| 回测模块 | [modules/backtest.md](modules/backtest.md) | 策略回测、报告生成 |
| 知识总结模块 | [modules/knowledge.md](modules/knowledge.md) | 知识管理、经验积累 |
| 量化投研模块 | [modules/quant.md](modules/quant.md) | QLib 数据桥接、因子提取、机器学习与原生回测执行 |

### 设计文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 配置设计 | [config.md](config.md) | 全局配置文件设计 |
| 项目规划 | [project.md](project.md) | 非功能性需求、技术选型、项目结构、里程碑、风险评估 |
| 全景进度 | [project_progress.md](project_progress.md) | 整个项目的全局进度跟踪与各需求模块实际完成度 |

---

## 功能模块概览

```
┌─────────────────────────────────────────────────────────────┐
│                      My Stocks 系统                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐   ┌──────────┐   ┌──────────┐                 │
│  │ 数据模块 │──▶│ 分析模块 │──▶│ 决策模块 │                 │
│  └─────────┘   └──────────┘   └──────────┘                 │
│       │              │              │                       │
│       ▼              ▼              ▼                       │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐                 │
│  │ 数据缓存 │   │ 回测模块 │   │ 通信模块 │                 │
│  └─────────┘   └──────────┘   └──────────┘                 │
│                      │                                      │
│                      ▼                                      │
│               ┌──────────┐   ┌──────────┐                   │
│               │ 知识模块 │   │ 量化模块 │                   │
│               └──────────┘   └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 环境要求
- Python 3.10+
- 依赖库见 [requirements.txt](../requirements.txt)
- QLib 源码环境部署 (挂载至 sys.path)

### 配置文件
- 主配置：[config/config.yaml](../config/config.yaml)
- 修改 `data.base_dir` 指向股票数据目录
- 修改 `data.qlib_dir` 指向 QLib 二进制中心数据库

### 数据访问示例

```python
from src.utils import get_config
from src.data import load_kline

# 获取K线数据
df = load_kline("000001", "daily")

# 获取配置
config = get_config()
path = config.get_kline_file_path("000001", "min30")
```

---

*文档版本：v1.2*
*最后更新：2026-03-21*
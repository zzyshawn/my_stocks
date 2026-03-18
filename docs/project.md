# 项目规划

## 1. 非功能性需求

### 1.1 性能需求

| 编号 | 需求项 | 描述 |
|------|--------|------|
| NFR1 | 响应时间 | 实时数据获取响应时间 < 3秒 |
| NFR2 | 并发能力 | 支持同时监控 >= 50只股票 |
| NFR3 | 数据处理 | 技术指标计算响应时间 < 1秒 |

### 1.2 可靠性需求

| 编号 | 需求项 | 描述 |
|------|--------|------|
| NFR4 | 可用性 | 系统可用性 >= 99% |
| NFR5 | 容错 | 数据源故障时自动切换备用数据源 |
| NFR6 | 数据完整性 | 保证数据不丢失、不重复 |

### 1.3 安全性需求

| 编号 | 需求项 | 描述 |
|------|--------|------|
| NFR7 | 配置安全 | 敏感信息（API Key等）加密存储 |
| NFR8 | 访问控制 | 支持用户认证和权限管理 |

### 1.4 可扩展性需求

| 编号 | 需求项 | 描述 |
|------|--------|------|
| NFR9 | 插件化 | 支持插件化扩展新的数据源和策略 |
| NFR10 | 配置化 | 核心参数支持配置化管理 |

---

## 2. 技术选型建议

### 2.1 开发语言
- **Python 3.10+** - 主要开发语言，丰富的量化库生态

### 2.2 核心依赖库

| 库名 | 用途 |
|------|------|
| akshare/tushare | 股票数据获取 |
| pandas | 数据处理 |
| numpy | 数值计算 |
| talib | 技术指标计算 |
| matplotlib/plotly | 数据可视化 |
| schedule/APScheduler | 定时任务 |
| requests | HTTP请求 |
| openpyxl | Excel文件读写 |
| PyYAML | 配置文件解析 |

### 2.3 数据存储

| 存储类型 | 用途 |
|----------|------|
| SQLite | 本地数据缓存 |
| CSV/JSON | 配置文件和历史数据 |
| Markdown | 知识库文档 |

---

## 3. 项目结构

```
my_stocks/
├── docs/                    # 文档目录
│   ├── requirements.md      # 主需求文档（索引）
│   ├── config.md            # 配置设计文档
│   ├── project.md           # 项目规划文档
│   └── modules/             # 模块需求文档
│       ├── data.md          # 数据模块
│       ├── analysis.md      # 技术分析模块
│       ├── decision.md      # 决策模块
│       ├── communication.md # 通信模块
│       ├── backtest.md      # 回测模块
│       └── knowledge.md     # 知识总结模块
├── src/                     # 源代码目录
│   ├── data/               # 数据获取模块
│   │   ├── __init__.py
│   │   ├── data_source.py  # 数据源基类
│   │   ├── akshare_source.py
│   │   ├── data_merger.py  # 数据合并
│   │   └── data_cache.py   # 数据缓存
│   ├── analysis/           # 技术分析模块
│   │   ├── __init__.py
│   │   ├── indicators.py   # 技术指标计算
│   │   └── patterns.py     # 形态识别
│   ├── decision/           # 决策模块
│   │   ├── __init__.py
│   │   ├── signals.py      # 信号生成
│   │   └── strategies.py   # 策略管理
│   ├── communication/      # 通信模块
│   │   ├── __init__.py
│   │   ├── email_notify.py
│   │   ├── wechat_notify.py
│   │   └── dingtalk_notify.py
│   ├── backtest/           # 回测模块
│   │   ├── __init__.py
│   │   ├── engine.py       # 回测引擎
│   │   └── report.py       # 报告生成
│   ├── knowledge/          # 知识总结模块
│   │   ├── __init__.py
│   │   ├── summary.py      # 知识总结
│   │   ├── storage.py      # Obsidian 存储
│   │   └── templates.py    # 知识模板
│   └── utils/              # 工具模块
│       ├── __init__.py
│       ├── config.py       # 配置管理
│       └── logger.py       # 日志管理
├── config/                  # 配置文件目录
│   ├── config.yaml         # 主配置
│   └── secrets.yaml        # 敏感配置
├── tests/                   # 测试目录
├── requirements.txt         # 依赖清单
└── main.py                  # 主入口
```

---

## 4. 开发里程碑

### 阶段一：基础框架（Week 1-2）
- [x] 项目结构搭建
- [x] 配置管理模块
- [ ] 日志系统
- [x] 数据获取模块基础框架
- [x] 数据更新模块 (data_updater.py, kline_fetcher.py, zt_pool_fetcher.py)
- [x] 通信推送模块 (飞书通知)
- [x] 知识总结模块

### 阶段二：核心功能（Week 3-4）
- [ ] 实时数据获取
- [ ] 技术指标计算
- [ ] 基础决策信号

### 阶段三：高级功能（Week 5-6）
- [x] 通信推送模块
- [ ] 回测模块
- [x] 知识总结模块

### 阶段四：优化完善（Week 7-8）
- [ ] 性能优化
- [ ] 单元测试
- [ ] 文档完善
- [ ] 部署上线

---

## 5. 风险评估

| 风险项 | 可能性 | 影响 | 应对措施 |
|--------|--------|------|----------|
| 数据源不稳定 | 高 | 高 | 多数据源备份，本地缓存 |
| 网络延迟 | 中 | 中 | 异步请求，超时重试 |
| 数据准确性 | 低 | 高 | 数据校验，多源对比 |
| 策略失效 | 中 | 中 | 持续回测，策略更新 |

---

*文档版本：v1.0*
*创建日期：2026-03-17*
*最后更新：2026-03-17*
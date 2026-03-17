# 全局配置文件设计

## 1. 配置文件概述
系统采用 YAML 格式的全局配置文件，支持以下可配置项：
- 股票数据目录路径
- 股票目录文件夹命名规则
- 文件命名规则
- 数据源配置
- 技术分析参数
- 决策参数
- 通信配置
- 回测配置

## 2. 配置文件结构
配置文件位于 `config/config.yaml`，主要包含以下配置节：

| 配置节 | 描述 |
|--------|------|
| app | 程序基本配置 |
| data | 数据目录配置 |
| naming | 文件/文件夹命名规则 |
| data_source | 数据源配置 |
| analysis | 技术分析配置 |
| decision | 决策配置 |
| communication | 通信配置 |
| backtest | 回测配置 |
| cache | 缓存配置 |
| logging | 日志配置 |

## 3. 数据目录配置

```yaml
data:
  # 数据根目录 (支持相对路径和绝对路径)
  # 默认使用已有的股票数据目录
  base_dir: "H:/股票信息/股票数据库/daban/股票数据"

  # 子目录配置（程序生成的数据）
  directories:
    cache: "cache"
    backtest: "backtest"
    knowledge: "knowledge"
    logs: "logs"
```

**配置说明：**
- `base_dir`: 股票数据根目录，支持相对路径或绝对路径
- 股票数据直接存放在 `{base_dir}/{股票代码}/` 目录下
- `directories`: 程序运行时生成的数据子目录

**实际目录结构示例：**
```
H:/股票信息/股票数据库/daban/股票数据/
├── 000001/                    # 平安银行
│   ├── 000001_d.xlsx         # 日线数据
│   ├── 000001_30.xlsx        # 30分钟数据
│   └── 000001_5.xlsx         # 5分钟数据
├── 600000/                    # 浦发银行
│   ├── 600000_d.xlsx
│   ├── 600000_30.xlsx
│   └── 600000_5.xlsx
└── ...
```

## 4. 文件夹命名规则配置

```yaml
naming:
  folder:
    # 文件夹命名模式（仅使用股票代码）
    pattern: "{symbol}"
    # 不创建市场子目录
    use_market_subdir: false
```

**支持变量：**
| 变量 | 说明 | 示例 |
|------|------|------|
| `{symbol}` | 股票代码 | 000001 |

## 5. 文件命名规则配置

```yaml
naming:
  files:
    kline:
      # 文件命名模式
      pattern: "{symbol}_{period}"
      extension: ".xlsx"
      # 周期映射
      period_map:
        daily: "d"        # 日线
        min30: "30"       # 30分钟线
        min5: "5"         # 5分钟线
```

**K线周期标识：**
| 周期名称 | 文件标识 | 文件示例 |
|----------|----------|----------|
| 日线 | `d` | `000001_d.xlsx` |
| 30分钟线 | `30` | `000001_30.xlsx` |
| 5分钟线 | `5` | `000001_5.xlsx` |

**其他文件类型配置：**
| 类型 | 默认扩展名 | 说明 |
|------|------------|------|
| cache | .json | 缓存数据文件 |
| report | .md | 分析报告文件 |
| backtest | .html | 回测结果文件 |
| knowledge | .md | 知识库文件 |
| log | .log | 日志文件 |

## 6. 配置管理模块

配置管理模块 `src/utils/config.py` 提供以下功能：

### 6.1 核心类
- `ConfigManager`: 配置管理器类，单例模式

### 6.2 便捷函数

| 函数 | 说明 |
|------|------|
| `get_config()` | 获取全局配置实例 |
| `get(key, default)` | 获取配置值 |
| `set_value(key, value)` | 设置配置值 |
| `get_data_dir(subdir)` | 获取数据目录路径 |
| `format_folder_name(...)` | 格式化文件夹名称 |
| `format_file_name(...)` | 格式化文件名称 |

### 6.3 K线数据访问方法

| 方法 | 说明 |
|------|------|
| `get_kline_file_path(symbol, period)` | 获取K线数据文件路径 |
| `list_available_periods(symbol)` | 列出股票可用的数据周期 |

### 6.4 使用示例

```python
from src.utils import get_config, get_data_dir

config = get_config()

# 获取K线数据文件路径
kline_path = config.get_kline_file_path("000001", "daily")
# 结果: H:/股票信息/股票数据库/daban/股票数据/000001/000001_d.xlsx

# 获取30分钟数据
min30_path = config.get_kline_file_path("000001", "min30")
# 结果: H:/股票信息/股票数据库/daban/股票数据/000001/000001_30.xlsx

# 列出可用周期
periods = config.list_available_periods("000001")
# 结果: ["daily", "min30", "min5"]
```

## 7. 通信配置

### 7.1 飞书机器人配置

```yaml
communication:
  feishu:
    enabled: true
    webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
    secret: ""
    timeout: 10
    retry: 3
```

**配置说明：**
| 参数 | 说明 |
|------|------|
| `enabled` | 是否启用飞书通知 |
| `webhook_url` | 飞书机器人 Webhook 地址 |
| `secret` | 签名密钥（可选） |
| `timeout` | 请求超时时间(秒) |
| `retry` | 失败重试次数 |

### 7.2 获取飞书 Webhook

1. 打开飞书群组，点击"设置" → "群机器人" → "添加机器人"
2. 选择"自定义机器人"
3. 设置机器人名称和描述
4. 复制 Webhook 地址
5. （可选）开启签名验证，获取签名密钥

### 7.3 推送配置

```yaml
communication:
  push:
    enabled: true
    min_strength: 6          # 最低信号强度阈值
    signal_types:            # 推送的信号类型
      - "强烈买入"
      - "买入"
      - "卖出"
      - "强烈卖出"
    quiet_hours:             # 安静时段
      enabled: true
      start: "23:00"
      end: "07:00"
```
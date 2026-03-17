# 通信模块需求

## 1. 功能描述
通过飞书机器人向用户推送股票信号和通知。

## 2. 功能需求

| 编号 | 需求项 | 优先级 | 描述 |
|------|--------|--------|------|
| R6.1 | 飞书机器人推送 | P0 | 支持飞书自定义机器人 Webhook 推送 |
| R6.2 | 消息模板 | P0 | 支持自定义推送消息模板 |
| R6.3 | 消息类型 | P1 | 支持文本、卡片、富文本等多种消息类型 |
| R6.4 | 条件触发 | P0 | 支持条件触发推送（如达到买卖信号时） |
| R6.5 | 定时推送 | P1 | 支持定时推送日报/周报 |
| R6.6 | 推送记录 | P2 | 记录历史推送记录 |
| R6.7 | 错误重试 | P1 | 推送失败时自动重试 |

## 3. 推送消息格式

### 3.1 股票信号提醒

```
【股票信号提醒】
股票代码: {symbol}
股票名称: {name}
当前价格: {price}
信号类型: {signal_type}
信号强度: {strength}
技术指标: {indicators}
建议操作: {suggestion}
时间: {timestamp}
```

### 3.2 日报推送

```
【每日股票分析报告】
日期: {date}
分析股票数: {count}
买入信号: {buy_count}
卖出信号: {sell_count}
持仓建议: {hold_count}
详情请查看附件
```

## 4. 模块结构

```
src/communication/
├── __init__.py
├── base.py              # 通知器基类
├── feishu.py            # 飞书机器人通知
├── message.py           # 消息模板
└── notify_manager.py    # 通知管理器
```

## 5. 飞书机器人配置

### 5.1 获取 Webhook 地址

1. 在飞书群组中添加"自定义机器人"
2. 获取 Webhook 地址：`https://open.feishu.cn/open-apis/bot/v2/hook/xxx`
3. 可选：配置签名密钥用于安全验证

### 5.2 配置参数

```yaml
communication:
  feishu:
    enabled: true
    webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
    secret: ""                    # 签名密钥（可选）
    timeout: 10                   # 请求超时时间(秒)
    retry: 3                      # 重试次数
```

## 6. 使用示例

```python
from src.communication import FeishuNotifier, MessageBuilder

# 创建飞书通知器
notifier = FeishuNotifier()

# 发送文本消息
notifier.send_text("【提醒】股票 000001 出现买入信号")

# 发送股票信号
message = MessageBuilder.build_signal_message(
    symbol="000001",
    name="平安银行",
    price=12.50,
    signal_type="买入",
    strength=8,
    suggestion="建议积极建仓"
)
notifier.send_card(message)

# 发送日报
report = MessageBuilder.build_daily_report(
    date="2026-03-17",
    buy_count=5,
    sell_count=2,
    hold_count=10
)
notifier.send_card(report)
```
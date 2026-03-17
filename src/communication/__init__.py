"""
My Stocks 通信模块

提供飞书机器人等通知功能。
"""

from .base import BaseNotifier, Message
from .feishu import (
    FeishuNotifier,
    get_feishu_notifier,
    send_feishu_text,
    send_feishu_card,
)
from .message import MessageBuilder
from .notify_manager import NotifyManager, get_notify_manager

__all__ = [
    # 基类
    "BaseNotifier",
    "Message",
    # 飞书通知
    "FeishuNotifier",
    "get_feishu_notifier",
    "send_feishu_text",
    "send_feishu_card",
    # 消息构建
    "MessageBuilder",
    # 通知管理
    "NotifyManager",
    "get_notify_manager",
]
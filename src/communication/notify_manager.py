"""
通知管理器

统一管理各种通知渠道。
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BaseNotifier, Message
from .feishu import FeishuNotifier


class NotifyManager:
    """通知管理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化通知管理器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.notifiers: Dict[str, BaseNotifier] = {}

        self._init_notifiers()

    def _init_notifiers(self):
        """初始化所有通知器"""
        # 飞书通知器
        feishu_config = self.config.get("feishu", {})
        if feishu_config.get("enabled", False):
            self.notifiers["feishu"] = FeishuNotifier(feishu_config)

    def get_notifier(self, name: str) -> Optional[BaseNotifier]:
        """
        获取指定通知器

        Args:
            name: 通知器名称

        Returns:
            通知器实例
        """
        return self.notifiers.get(name)

    def send_text(self, content: str, channels: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        发送文本消息到多个渠道

        Args:
            content: 文本内容
            channels: 渠道列表，None 表示所有启用的渠道

        Returns:
            各渠道发送结果
        """
        results = {}

        if channels is None:
            channels = list(self.notifiers.keys())

        for channel in channels:
            notifier = self.notifiers.get(channel)
            if notifier and notifier.is_enabled():
                results[channel] = notifier.send_text(content)
            else:
                results[channel] = False

        return results

    def send_card(self, card: Dict[str, Any], channels: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        发送卡片消息到多个渠道

        Args:
            card: 卡片内容
            channels: 渠道列表

        Returns:
            各渠道发送结果
        """
        results = {}

        if channels is None:
            channels = list(self.notifiers.keys())

        for channel in channels:
            notifier = self.notifiers.get(channel)
            if notifier and notifier.is_enabled():
                results[channel] = notifier.send_card(card)
            else:
                results[channel] = False

        return results

    def send_signal(
        self,
        symbol: str,
        name: str,
        price: float,
        signal_type: str,
        strength: int,
        **kwargs
    ) -> Dict[str, bool]:
        """
        发送股票信号通知

        Args:
            symbol: 股票代码
            name: 股票名称
            price: 当前价格
            signal_type: 信号类型
            strength: 信号强度
            **kwargs: 其他参数

        Returns:
            各渠道发送结果
        """
        from .message import MessageBuilder

        card = MessageBuilder.build_signal_message(
            symbol=symbol,
            name=name,
            price=price,
            signal_type=signal_type,
            strength=strength,
            **kwargs
        )

        return self.send_card(card)

    def test_all(self) -> Dict[str, bool]:
        """
        测试所有通知渠道

        Returns:
            各渠道测试结果
        """
        results = {}

        for name, notifier in self.notifiers.items():
            if hasattr(notifier, 'test_connection'):
                results[name] = notifier.test_connection()
            else:
                results[name] = notifier.send_text("【测试】通知渠道连接测试")

        return results


# 全局实例
_manager_instance: Optional[NotifyManager] = None


def get_notify_manager(config: Optional[Dict[str, Any]] = None) -> NotifyManager:
    """
    获取通知管理器实例

    Args:
        config: 配置字典

    Returns:
        NotifyManager 实例
    """
    global _manager_instance

    if _manager_instance is None or config:
        if config is None:
            try:
                from ..utils.config import get_config
                config = get_config().get("communication", {})
            except:
                config = {}
        _manager_instance = NotifyManager(config)

    return _manager_instance
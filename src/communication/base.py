"""
通信模块基类

定义通知器的基类接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime


class BaseNotifier(ABC):
    """通知器基类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化通知器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.enabled = self.config.get("enabled", False)

    @abstractmethod
    def send_text(self, content: str, **kwargs) -> bool:
        """
        发送文本消息

        Args:
            content: 文本内容
            **kwargs: 其他参数

        Returns:
            是否发送成功
        """
        pass

    @abstractmethod
    def send_card(self, card: Dict[str, Any], **kwargs) -> bool:
        """
        发送卡片消息

        Args:
            card: 卡片内容
            **kwargs: 其他参数

        Returns:
            是否发送成功
        """
        pass

    def is_enabled(self) -> bool:
        """检查通知器是否启用"""
        return self.enabled


class Message:
    """消息类"""

    def __init__(
        self,
        msg_type: str = "text",
        content: Any = None,
        timestamp: Optional[datetime] = None
    ):
        """
        初始化消息

        Args:
            msg_type: 消息类型
            content: 消息内容
            timestamp: 时间戳
        """
        self.msg_type = msg_type
        self.content = content
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "msg_type": self.msg_type,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
"""
飞书机器人通知模块

通过飞书自定义机器人 Webhook 发送消息通知。
"""

import hashlib
import hmac
import time
from typing import Any, Dict, List, Optional

import requests

from .base import BaseNotifier


class FeishuNotifier(BaseNotifier):
    """飞书机器人通知器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化飞书通知器

        Args:
            config: 配置字典，包含:
                - enabled: 是否启用
                - webhook_url: Webhook 地址
                - secret: 签名密钥（可选）
                - timeout: 请求超时时间
                - retry: 重试次数
        """
        super().__init__(config)

        self.webhook_url = self.config.get("webhook_url", "")
        self.secret = self.config.get("secret", "")
        self.timeout = self.config.get("timeout", 10)
        self.retry = self.config.get("retry", 3)

    def _generate_signature(self, timestamp: str) -> str:
        """
        生成签名

        Args:
            timestamp: 时间戳字符串

        Returns:
            签名字符串
        """
        if not self.secret:
            return ""

        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()

        import base64
        signature = base64.b64encode(hmac_code).decode('utf-8')
        return signature

    def _build_request_body(self, msg_type: str, content: Any) -> Dict[str, Any]:
        """
        构建请求体

        Args:
            msg_type: 消息类型
            content: 消息内容

        Returns:
            请求体字典
        """
        body = {
            "msg_type": msg_type,
            "content": content
        }

        # 添加签名
        if self.secret:
            timestamp = str(int(time.time()))
            body["timestamp"] = timestamp
            body["sign"] = self._generate_signature(timestamp)

        return body

    def _send_request(self, body: Dict[str, Any]) -> bool:
        """
        发送请求

        Args:
            body: 请求体

        Returns:
            是否成功
        """
        if not self.webhook_url:
            print("错误: 未配置 Webhook URL")
            return False

        for attempt in range(self.retry):
            try:
                response = requests.post(
                    self.webhook_url,
                    json=body,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("code") == 0 or result.get("StatusCode") == 0:
                        return True
                    else:
                        print(f"飞书返回错误: {result}")
                else:
                    print(f"请求失败，状态码: {response.status_code}")

            except requests.exceptions.Timeout:
                print(f"请求超时，第 {attempt + 1} 次重试...")
            except requests.exceptions.RequestException as e:
                print(f"请求异常: {e}")

            if attempt < self.retry - 1:
                time.sleep(1)

        return False

    def send_text(self, content: str, **kwargs) -> bool:
        """
        发送文本消息

        Args:
            content: 文本内容

        Returns:
            是否发送成功
        """
        if not self.enabled:
            return False

        body = self._build_request_body("text", {"text": content})
        return self._send_request(body)

    def send_card(self, card: Dict[str, Any], **kwargs) -> bool:
        """
        发送卡片消息

        Args:
            card: 卡片内容

        Returns:
            是否发送成功
        """
        if not self.enabled:
            return False

        body = self._build_request_body("interactive", card)
        return self._send_request(body)

    def send_post(
        self,
        title: str,
        content: List[List[Dict[str, Any]]]
    ) -> bool:
        """
        发送富文本消息

        Args:
            title: 标题
            content: 富文本内容

        Returns:
            是否发送成功
        """
        if not self.enabled:
            return False

        post_content = {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": content
                }
            }
        }

        body = self._build_request_body("post", post_content)
        return self._send_request(body)

    def send_share_card(self, share_url: str) -> bool:
        """
        发送分享卡片

        Args:
            share_url: 分享链接

        Returns:
            是否发送成功
        """
        if not self.enabled:
            return False

        body = self._build_request_body("share_chat", {"share_chat_id": share_url})
        return self._send_request(body)

    def test_connection(self) -> bool:
        """
        测试连接

        Returns:
            是否连接成功
        """
        if not self.webhook_url:
            return False

        # 发送测试消息
        return self.send_text("【测试】飞书机器人连接测试成功")


# 便捷函数
_notifier_instance: Optional[FeishuNotifier] = None


def get_feishu_notifier(config: Optional[Dict[str, Any]] = None) -> FeishuNotifier:
    """
    获取飞书通知器实例

    Args:
        config: 配置字典

    Returns:
        FeishuNotifier 实例
    """
    global _notifier_instance

    if _notifier_instance is None or config:
        if config is None:
            from ..utils.config import get_config
            config = get_config().get("communication.feishu", {})
        _notifier_instance = FeishuNotifier(config)

    return _notifier_instance


def send_feishu_text(content: str) -> bool:
    """
    发送飞书文本消息（便捷函数）

    Args:
        content: 文本内容

    Returns:
        是否发送成功
    """
    notifier = get_feishu_notifier()
    return notifier.send_text(content)


def send_feishu_card(card: Dict[str, Any]) -> bool:
    """
    发送飞书卡片消息（便捷函数）

    Args:
        card: 卡片内容

    Returns:
        是否发送成功
    """
    notifier = get_feishu_notifier()
    return notifier.send_card(card)
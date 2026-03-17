"""
消息模板模块

提供各种消息模板的构建功能。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class MessageBuilder:
    """消息构建器"""

    @staticmethod
    def build_text(content: str) -> str:
        """
        构建文本消息

        Args:
            content: 文本内容

        Returns:
            格式化的文本
        """
        return content

    @staticmethod
    def build_signal_message(
        symbol: str,
        name: str,
        price: float,
        signal_type: str,
        strength: int,
        indicators: Optional[Dict[str, Any]] = None,
        suggestion: str = "",
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        构建股票信号卡片消息

        Args:
            symbol: 股票代码
            name: 股票名称
            price: 当前价格
            signal_type: 信号类型（买入/卖出/持有）
            strength: 信号强度（1-10）
            indicators: 技术指标字典
            suggestion: 操作建议
            timestamp: 时间戳

        Returns:
            卡片消息字典
        """
        timestamp = timestamp or datetime.now()

        # 信号类型颜色
        color_map = {
            "强烈买入": "green",
            "买入": "green",
            "持有": "grey",
            "卖出": "red",
            "强烈卖出": "red"
        }
        signal_color = color_map.get(signal_type, "grey")

        # 构建指标描述
        indicator_text = ""
        if indicators:
            indicator_items = []
            for key, value in indicators.items():
                if isinstance(value, float):
                    indicator_items.append(f"{key}: {value:.2f}")
                else:
                    indicator_items.append(f"{key}: {value}")
            indicator_text = "\n".join(indicator_items)

        # 构建卡片
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"【股票信号提醒】{symbol} {name}"
                },
                "template": signal_color
            },
            "elements": [
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**股票代码**\n{symbol}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**股票名称**\n{name}"
                            }
                        }
                    ]
                },
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**当前价格**\n{price:.2f}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**信号类型**\n{signal_type}"
                            }
                        }
                    ]
                },
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**信号强度**\n{'⭐' * min(strength, 10)} ({strength}/10)"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**时间**\n{timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        }
                    ]
                }
            ]
        }

        # 添加技术指标
        if indicator_text:
            card["elements"].append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**技术指标**\n{indicator_text}"
                }
            })

        # 添加操作建议
        if suggestion:
            card["elements"].append({
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": f"💡 建议: {suggestion}"
                    }
                ]
            })

        return card

    @staticmethod
    def build_daily_report(
        date: str,
        buy_count: int,
        sell_count: int,
        hold_count: int,
        total_count: int,
        details: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        构建每日报告卡片

        Args:
            date: 日期
            buy_count: 买入信号数量
            sell_count: 卖出信号数量
            hold_count: 持有信号数量
            total_count: 总分析数量
            details: 详细信息列表

        Returns:
            卡片消息字典
        """
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"【每日股票分析报告】{date}"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**分析股票数**\n{total_count}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**日期**\n{date}"
                            }
                        }
                    ]
                },
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**🟢 买入信号**\n{buy_count}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**🔴 卖出信号**\n{sell_count}"
                            }
                        }
                    ]
                },
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**⚪ 持有信号**\n{hold_count}"
                            }
                        }
                    ]
                }
            ]
        }

        # 添加详细列表
        if details:
            detail_elements = []
            for item in details[:10]:  # 最多显示10条
                detail_elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"- {item.get('symbol', '')} {item.get('name', '')}: {item.get('signal', '')}"
                    }
                })

            if detail_elements:
                card["elements"].extend(detail_elements)

        return card

    @staticmethod
    def build_alert(
        title: str,
        content: str,
        level: str = "info"
    ) -> Dict[str, Any]:
        """
        构建告警卡片

        Args:
            title: 标题
            content: 内容
            level: 级别 (info, warning, error)

        Returns:
            卡片消息字典
        """
        color_map = {
            "info": "blue",
            "warning": "orange",
            "error": "red"
        }

        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "template": color_map.get(level, "blue")
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "plain_text",
                        "content": content
                    }
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                    ]
                }
            ]
        }

        return card

    @staticmethod
    def build_post_content(
        title: str,
        paragraphs: List[str]
    ) -> List[List[Dict[str, Any]]]:
        """
        构建富文本内容

        Args:
            title: 标题
            paragraphs: 段落列表

        Returns:
            富文本内容
        """
        content = []

        # 添加标题
        content.append([
            {
                "tag": "text",
                "text": title,
                "style": ["bold"]
            }
        ])

        # 添加段落
        for para in paragraphs:
            content.append([
                {
                    "tag": "text",
                    "text": para
                }
            ])

        return content
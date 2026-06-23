"""
飞书 API 客户端
支持通过群机器人 Webhook 发送消息
"""

import httpx
import json
from typing import Literal


class FeishuClient:
    """飞书群机器人 Webhook 客户端"""

    def __init__(self, webhook_key: str):
        """
        初始化飞书客户端

        Args:
            webhook_key: 飞书群机器人的 Webhook Key
        """
        self.webhook_url = f"https://open.feishu.cn/open-apis/bot/v2/hook/{webhook_key}"

    def send_text_message(self, text: str) -> dict:
        """
        发送纯文本消息

        Args:
            text: 消息内容

        Returns:
            飞书 API 响应
        """
        payload = {
            "msg_type": "text",
            "content": {
                "text": text
            }
        }

        return self._send_request(payload)

    def send_card_message(
        self,
        title: str,
        content: str,
        card_type: Literal["info", "success", "warning", "error"] = "info"
    ) -> dict:
        """
        发送卡片消息

        Args:
            title: 卡片标题
            content: Markdown 格式内容
            card_type: 卡片类型（info/success/warning/error）

        Returns:
            飞书 API 响应
        """
        # 卡片颜色映射
        template_colors = {
            "info": "blue",
            "success": "green",
            "warning": "orange",
            "error": "red"
        }

        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title
                    },
                    "template": template_colors.get(card_type, "blue")
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": content
                    }
                ]
            }
        }

        return self._send_request(payload)

    def _send_request(self, payload: dict) -> dict:
        """
        发送 HTTP 请求到飞书 Webhook

        Args:
            payload: 消息负载

        Returns:
            响应 JSON
        """
        try:
            response = httpx.post(
                self.webhook_url,
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "StatusCode": -1,
                "error": str(e)
            }


def determine_card_type(message: str) -> Literal["info", "success", "warning", "error"]:
    """
    根据消息内容判断卡片类型

    Args:
        message: 审批结果消息

    Returns:
        卡片类型
    """
    # 先检查拒绝（包含"未通过"），避免"通过"误匹配
    if "拒绝" in message or "❌" in message or "未通过" in message:
        return "error"
    elif "人工审批" in message or "📋" in message or "待审批" in message:
        return "warning"
    elif "通过" in message or "✅" in message or "恭喜" in message:
        return "success"
    else:
        return "info"

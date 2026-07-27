"""
飞书 API 客户端
支持通过群机器人 Webhook 发送消息
支持通过消息API发送交互卡片（可触发回调）
"""

import httpx
import json
import os
from typing import Literal, Optional
import lark_oapi as lark
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody


class FeishuClient:
    """飞书群机器人客户端"""

    def __init__(self, webhook_key: str, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        """
        初始化飞书客户端

        Args:
            webhook_key: 飞书群机器人的 Webhook Key
            app_id: 飞书应用 APP_ID（用于消息API，可选）
            app_secret: 飞书应用 APP_SECRET（用于消息API，可选）
        """
        self.webhook_url = f"https://open.feishu.cn/open-apis/bot/v2/hook/{webhook_key}"
        self.app_id = app_id or os.getenv("FEISHU_APP_ID")
        self.app_secret = app_secret or os.getenv("FEISHU_APP_SECRET")

        # 初始化 lark 客户端（用于消息API）
        if self.app_id and self.app_secret:
            self.lark_client = lark.Client.builder() \
                .app_id(self.app_id) \
                .app_secret(self.app_secret) \
                .build()
        else:
            self.lark_client = None

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

    def send_approval_card(
        self,
        approval_id: str,
        user_id: str,
        applicant: str,
        destination: str,
        days: int,
        amount: float
    ) -> dict:
        """
        发送带交互按钮的审批卡片

        Args:
            approval_id: 审批ID
            user_id: 申请人用户ID
            applicant: 申请人姓名
            destination: 出差目的地
            days: 出差天数
            amount: 报销金额

        Returns:
            飞书 API 响应
        """
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "[CLIPBOARD] 待审批：出差报销申请"
                    },
                    "template": "orange"
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": (
                            f"**申请人**: {applicant}\n"
                            f"**目的地**: {destination}\n"
                            f"**天数**: {days}天\n"
                            f"**金额**: ¥{amount}"
                        )
                    },
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {
                                    "tag": "plain_text",
                                    "content": "[OK] 通过"
                                },
                                "type": "primary",
                                "value": {
                                    "operation": "approve",
                                    "approval_id": approval_id,
                                    "user_id": user_id
                                }
                            },
                            {
                                "tag": "button",
                                "text": {
                                    "tag": "plain_text",
                                    "content": "[ERROR] 拒绝"
                                },
                                "type": "danger",
                                "value": {
                                    "operation": "reject",
                                    "approval_id": approval_id,
                                    "user_id": user_id
                                }
                            }
                        ]
                    }
                ]
            }
        }

        return self._send_request(payload)

    def send_approval_card_to_chat(
        self,
        chat_id: str,
        approval_id: str,
        user_id: str,
        applicant: str,
        destination: str,
        days: int,
        amount: float
    ) -> dict:
        """
        使用消息API发送带交互按钮的审批卡片到群聊（可触发回调）

        Args:
            chat_id: 群聊ID
            approval_id: 审批ID
            user_id: 申请人用户ID
            applicant: 申请人姓名
            destination: 出差目的地
            days: 出差天数
            amount: 报销金额

        Returns:
            飞书 API 响应
        """
        if not self.lark_client:
            return {
                "code": -1,
                "msg": "消息API未初始化，请提供 app_id 和 app_secret"
            }

        # 构造卡片内容
        card_content = {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "[CLIPBOARD] 待审批：出差报销申请"
                },
                "template": "orange"
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": (
                        f"**申请人**: {applicant}\n"
                        f"**目的地**: {destination}\n"
                        f"**天数**: {days}天\n"
                        f"**金额**: ¥{amount}"
                    )
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "[OK] 通过"
                            },
                            "type": "primary",
                            "value": {
                                "operation": "approve",
                                "approval_id": approval_id,
                                "user_id": user_id
                            }
                        },
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "[ERROR] 拒绝"
                            },
                            "type": "danger",
                            "value": {
                                "operation": "reject",
                                "approval_id": approval_id,
                                "user_id": user_id
                            }
                        }
                    ]
                }
            ]
        }

        # 创建消息请求
        request = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(
                CreateMessageRequestBody.builder()
                .receive_id(chat_id)
                .msg_type("interactive")
                .content(json.dumps(card_content))
                .build()
            ) \
            .build()

        # 发送消息
        try:
            response = self.lark_client.im.v1.message.create(request)
            if response.success():
                return {
                    "code": 0,
                    "msg": "success",
                    "data": {
                        "message_id": response.data.message_id
                    }
                }
            else:
                return {
                    "code": response.code,
                    "msg": response.msg
                }
        except Exception as e:
            return {
                "code": -1,
                "msg": str(e)
            }

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
    if "拒绝" in message or "[ERROR]" in message or "未通过" in message:
        return "error"
    elif "人工审批" in message or "[CLIPBOARD]" in message or "待审批" in message:
        return "warning"
    elif "通过" in message or "[OK]" in message or "恭喜" in message:
        return "success"
    else:
        return "info"

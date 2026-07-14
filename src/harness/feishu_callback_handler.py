# -*- coding: utf-8 -*-
"""
飞书回调处理器
处理卡片交互回调（审批通过/拒绝）
"""

import logging
from typing import Optional
from lark_oapi.event.callback.model.p2_card_action_trigger import (
    P2CardActionTrigger,
    P2CardActionTriggerResponse
)

logger = logging.getLogger(__name__)


class FeishuCallbackHandler:
    """
    飞书卡片回调处理器

    处理审批人点击卡片按钮的交互回调
    """

    def __init__(self, approval_engine=None):
        """
        初始化回调处理器

        Args:
            approval_engine: 审批引擎实例（用于处理审批结果）
        """
        self.approval_engine = approval_engine

    def handle_card_action(
        self,
        event: P2CardActionTrigger
    ) -> P2CardActionTriggerResponse:
        """
        处理卡片交互回调

        Args:
            event: 卡片交互事件

        Returns:
            回调响应（更新卡片内容或显示toast）
        """
        try:
            # 提取回调数据
            action = event.event.action
            action_value = action.value if action else {}

            # 获取操作类型和审批ID
            operation = action_value.get("operation")  # "approve" or "reject"
            approval_id = action_value.get("approval_id")
            user_id = action_value.get("user_id")

            logger.info(
                f"[FeishuCallback] 收到审批操作: operation={operation}, "
                f"approval_id={approval_id}, user_id={user_id}"
            )

            if not operation or not approval_id:
                return self._error_response("缺少必要参数")

            # 处理审批结果
            if operation == "approve":
                result = self._handle_approve(approval_id, user_id)
            elif operation == "reject":
                result = self._handle_reject(approval_id, user_id)
            else:
                return self._error_response(f"未知操作类型: {operation}")

            # 返回成功响应（更新卡片）
            return self._success_response(result)

        except Exception as e:
            logger.error(f"[FeishuCallback] 处理回调失败: {e}", exc_info=True)
            return self._error_response(f"处理失败: {str(e)}")

    def _handle_approve(self, approval_id: str, approver_id: str) -> dict:
        """
        处理审批通过

        Args:
            approval_id: 审批ID
            approver_id: 审批人ID

        Returns:
            处理结果
        """
        if not self.approval_engine:
            raise ValueError("ApprovalEngine 未初始化")

        # 调用审批引擎处理通过操作
        result = self.approval_engine.process_approval_result(
            approval_id=approval_id,
            operation="approve",
            approver_id=approver_id
        )

        return result

    def _handle_reject(self, approval_id: str, approver_id: str) -> dict:
        """
        处理审批拒绝

        Args:
            approval_id: 审批ID
            approver_id: 审批人ID

        Returns:
            处理结果
        """
        if not self.approval_engine:
            raise ValueError("ApprovalEngine 未初始化")

        # 调用审批引擎处理拒绝操作
        result = self.approval_engine.process_approval_result(
            approval_id=approval_id,
            operation="reject",
            approver_id=approver_id
        )

        return result

    def _success_response(self, result: dict) -> P2CardActionTriggerResponse:
        """
        生成成功响应

        Args:
            result: 处理结果

        Returns:
            回调响应对象
        """
        # 构造更新后的卡片内容
        status = result.get("status", "unknown")
        message = result.get("message", "操作成功")
        applicant = result.get("applicant", "申请人")
        amount = result.get("amount", 0)

        # 根据状态显示不同颜色
        if status == "approved":
            card_color = "green"
            status_emoji = "✅"
            status_text = "已通过"
        elif status == "rejected":
            card_color = "red"
            status_emoji = "❌"
            status_text = "已拒绝"
        else:
            card_color = "grey"
            status_emoji = "📋"
            status_text = "已处理"

        # 更新后的卡片
        updated_card = {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"{status_emoji} 审批{status_text}"
                },
                "template": card_color
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": (
                        f"**申请人**: {applicant}\n"
                        f"**金额**: ¥{amount}\n"
                        f"**状态**: {status_text}\n"
                        f"**备注**: {message}"
                    )
                }
            ]
        }

        response = {
            "toast": {
                "type": "success" if status == "approved" else "error",
                "content": message
            },
            "card": updated_card
        }

        return P2CardActionTriggerResponse(response)

    def _error_response(self, error_message: str) -> P2CardActionTriggerResponse:
        """
        生成错误响应

        Args:
            error_message: 错误信息

        Returns:
            回调响应对象
        """
        response = {
            "toast": {
                "type": "error",
                "content": error_message
            }
        }

        return P2CardActionTriggerResponse(response)

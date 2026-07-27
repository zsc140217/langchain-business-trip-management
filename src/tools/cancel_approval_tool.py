# -*- coding: utf-8 -*-
"""
取消审批申请工具
Phase 5: Tool Layer

用于取消用户提交的待审批报销申请
"""
from src.tools.base_tool import BaseTool
from typing import Optional
import logging
from datetime import datetime


logger = logging.getLogger(__name__)


class CancelApprovalTool(BaseTool):
    """
    取消审批申请工具

    允许用户取消尚未审批完成的报销申请
    """

    name: str = "cancel_approval"
    description: str = """取消待审批的报销申请。

适用场景：
- 用户要取消之前提交的报销申请
- 撤回还未审批的申请
- 取消待审批的单据

输入参数：
- user_id: 用户ID（必需）
- approval_id: 审批单号（可选，不填则取消最近一条待审批单据）
- reason: 取消原因（可选）

返回信息：
- 取消结果（成功/失败）
- 被取消的审批单号
- 取消原因说明

约束条件：
- 只能取消状态为 "pending"（待审批）的单据
- 已通过或已拒绝的单据不能取消

示例：
- cancel_approval("user123")
  → "已取消审批单 APV20260715001"
- cancel_approval("user123", "APV20260715001", "行程变更")
  → "已取消审批单 APV20260715001，原因：行程变更"
"""

    cache_enabled: bool = False  # 取消操作不缓存

    def __init__(self, memory_service=None, feishu_client=None, **kwargs):
        """
        初始化取消审批工具

        Args:
            memory_service: MemoryService 实例（可选，支持延迟初始化）
            feishu_client: FeishuClient 实例（可选）
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self._memory_service = memory_service
        self._feishu_client = feishu_client
        self._initialized = False

    def _lazy_init(self):
        """延迟初始化依赖服务"""
        if self._initialized:
            return

        # 初始化 MemoryService
        if self._memory_service is None:
            logger.info("[CancelApprovalTool] 延迟初始化 MemoryService")
            try:
                from src.memory.memory_service import MemoryService
                self._memory_service = MemoryService()
                logger.info("[CancelApprovalTool] MemoryService 初始化完成")
            except Exception as e:
                logger.error(f"[CancelApprovalTool] MemoryService 初始化失败: {e}")
                raise RuntimeError(f"MemoryService 初始化失败: {e}")

        # 初始化 FeishuClient（可选）
        if self._feishu_client is None:
            logger.info("[CancelApprovalTool] 尝试初始化 FeishuClient")
            try:
                import os
                from src.harness.feishu_client import FeishuClient

                feishu_webhook_key = os.getenv("FEISHU_WEBHOOK_KEY", "")
                if feishu_webhook_key:
                    self._feishu_client = FeishuClient(webhook_key=feishu_webhook_key)
                    logger.info("[CancelApprovalTool] FeishuClient 初始化完成")
                else:
                    logger.warning("[CancelApprovalTool] 未配置 FEISHU_WEBHOOK_KEY，飞书通知将不可用")
                    self._feishu_client = None
            except Exception as e:
                logger.warning(f"[CancelApprovalTool] FeishuClient 初始化失败: {e}")
                self._feishu_client = None

        self._initialized = True

    def _run(
        self,
        user_id: str,
        approval_id: Optional[str] = None,
        reason: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        执行取消审批操作

        Args:
            user_id: 用户ID
            approval_id: 审批单号（可选，不填则取消最近一条待审批单据）
            reason: 取消原因（可选）
            **kwargs: 其他参数

        Returns:
            取消结果文本
        """
        # 参数验证
        if not user_id or not user_id.strip():
            raise ValueError("user_id 不能为空")

        logger.info(
            f"[CancelApprovalTool] 取消审批: user_id={user_id}, "
            f"approval_id={approval_id}, reason={reason}"
        )

        try:
            # 延迟初始化
            self._lazy_init()

            # 获取用户的工作记忆
            working_memory = self._memory_service.working_memory_manager.get_or_create(user_id)
            approvals = working_memory.get_all_approvals()

            if not approvals:
                return "[ERROR] 取消失败：您没有待审批的申请。"

            # 确定要取消的审批单
            target_approval = None
            target_id = None

            if approval_id:
                # 取消指定的审批单
                if approval_id not in approvals:
                    return f"[ERROR] 取消失败：未找到审批单 {approval_id}。"
                target_approval = approvals[approval_id]
                target_id = approval_id
            else:
                # 取消最近一条待审批单据
                pending_approvals = {
                    aid: details for aid, details in approvals.items()
                    if details.get("status") == "pending"
                }

                if not pending_approvals:
                    return "[ERROR] 取消失败：您没有待审批的申请（所有申请已处理完成）。"

                # 按提交时间排序，取最新的
                sorted_approvals = sorted(
                    pending_approvals.items(),
                    key=lambda x: x[1].get("submit_time", ""),
                    reverse=True
                )
                target_id, target_approval = sorted_approvals[0]

            # 检查审批状态
            status = target_approval.get("status", "unknown")
            if status != "pending":
                status_text = {
                    "approved": "已通过",
                    "rejected": "已拒绝",
                    "cancelled": "已取消"
                }.get(status, status)
                return f"[ERROR] 取消失败：审批单 {target_id} 的状态为「{status_text}」，无法取消。"

            # 更新审批状态为 cancelled
            working_memory = self._memory_service.working_memory_manager.get_or_create(user_id)
            working_memory.update_approval_status(
                approval_id=target_id,
                status="cancelled",
                comment=reason or "用户主动取消"
            )

            logger.info(f"[CancelApprovalTool] 审批单 {target_id} 已取消")

            # 发送飞书通知（如果可用）
            self._send_feishu_notification(
                user_id=user_id,
                approval_id=target_id,
                approval_details=target_approval,
                reason=reason
            )

            # 格式化返回结果
            return self._format_result(target_id, target_approval, reason)

        except Exception as e:
            logger.error(f"[CancelApprovalTool] 取消审批失败: {e}", exc_info=True)
            return f"[ERROR] 取消失败：系统错误 - {str(e)}"

    def _send_feishu_notification(
        self,
        user_id: str,
        approval_id: str,
        approval_details: dict,
        reason: Optional[str]
    ):
        """
        发送飞书取消通知

        Args:
            user_id: 用户ID
            approval_id: 审批单号
            approval_details: 审批详情
            reason: 取消原因
        """
        if self._feishu_client is None:
            logger.debug("[CancelApprovalTool] FeishuClient 不可用，跳过通知")
            return

        try:
            destination = approval_details.get("destination", "未知")
            amount = approval_details.get("amount", 0)
            days = approval_details.get("days", 0)

            content = f"""审批申请已取消

审批单号：{approval_id}
目的地：{destination}
天数：{days}天
金额：¥{amount}
取消原因：{reason or '用户主动取消'}
取消时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

            self._feishu_client.send_card_message(
                title="🚫 审批申请已取消",
                content=content,
                card_type="info"
            )

            logger.info(f"[CancelApprovalTool] 飞书取消通知已发送: {approval_id}")

        except Exception as e:
            logger.warning(f"[CancelApprovalTool] 飞书通知发送失败: {e}")

    def _format_result(
        self,
        approval_id: str,
        approval_details: dict,
        reason: Optional[str]
    ) -> str:
        """
        格式化取消结果

        Args:
            approval_id: 审批单号
            approval_details: 审批详情
            reason: 取消原因

        Returns:
            格式化的文本结果
        """
        destination = approval_details.get("destination", "未知")
        amount = approval_details.get("amount", 0)
        days = approval_details.get("days", 0)

        result = f"[OK] 取消成功\n\n"
        result += f"【审批单号】{approval_id}\n"
        result += f"【目的地】{destination} | 【天数】{days}天 | 【金额】¥{amount}\n"

        if reason:
            result += f"【取消原因】{reason}\n"

        result += f"\n您可以随时重新提交报销申请。"

        return result


# 创建全局单例（延迟初始化）
_cancel_approval_tool_instance: Optional[CancelApprovalTool] = None


def get_cancel_approval_tool(
    memory_service=None,
    feishu_client=None
) -> CancelApprovalTool:
    """
    获取取消审批工具单例

    Args:
        memory_service: 可选的 MemoryService 实例
        feishu_client: 可选的 FeishuClient 实例

    Returns:
        CancelApprovalTool 实例
    """
    global _cancel_approval_tool_instance

    if _cancel_approval_tool_instance is None:
        _cancel_approval_tool_instance = CancelApprovalTool(
            memory_service=memory_service,
            feishu_client=feishu_client
        )

    return _cancel_approval_tool_instance

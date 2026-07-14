"""
提交报销申请工具
Phase 3.3: Tool Layer

用于提交差旅报销申请，路由到 ApprovalEngine 进行审批
"""
from src.tools.base_tool import BaseTool
from typing import Optional
import logging


logger = logging.getLogger(__name__)


class SubmitReimbursementTool(BaseTool):
    """
    提交报销申请工具

    将用户的报销申请提交到审批引擎进行处理
    """

    name: str = "submit_reimbursement"
    description: str = """提交差旅报销申请。

适用场景：
- 用户要报销出差费用
- 提交差旅报销申请
- 申请差旅补贴

输入参数：
- user_id: 用户ID（必需）
- query: 报销申请描述，包含目的地、天数、金额等信息（必需）
- conversation_id: 会话ID（可选）

返回信息：
- 审批结果（自动通过/待审批）
- 审批单号
- 审批状态说明

示例：
- submit_reimbursement("user123", "我去北京出差3天，花了800元")
  → "审批通过，审批单号：APV20260712001"
- submit_reimbursement("user456", "报销上海出差费用2500元")
  → "申请已提交，审批单号：APV20260712002，需要人工审批"
"""

    cache_enabled: bool = False  # 报销申请不缓存

    def __init__(self, approval_engine=None, **kwargs):
        """
        初始化提交报销工具

        Args:
            approval_engine: ApprovalEngine 实例（可选，支持延迟初始化）
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self._approval_engine = approval_engine
        self._initialized = False

    def _lazy_init(self):
        """延迟初始化 ApprovalEngine"""
        if self._initialized:
            return

        if self._approval_engine is None:
            logger.info("[SubmitReimbursementTool] 延迟初始化 ApprovalEngine")
            try:
                from src.agents.approval_engine import ApprovalEngine
                from src.config import get_llm
                from src.memory.memory_service import MemoryService
                from src.harness.feishu_client import FeishuClient
                from src.modules.module_5_langgraph.graphs.approval_graph import create_approval_graph
                import os

                # 初始化依赖
                llm = get_llm()
                memory_service = MemoryService()

                # 飞书客户端（如果没有 webhook key，创建一个空的）
                feishu_webhook_key = os.getenv("FEISHU_WEBHOOK_KEY", "")
                if feishu_webhook_key:
                    feishu_client = FeishuClient(webhook_key=feishu_webhook_key)
                else:
                    logger.warning("[SubmitReimbursementTool] 未配置 FEISHU_WEBHOOK_KEY，飞书通知将不可用")
                    # 创建一个假的 client，避免初始化失败
                    feishu_client = type('FakeFeishuClient', (), {
                        'send_card_message': lambda *args, **kwargs: {"StatusCode": 0}
                    })()

                approval_graph = create_approval_graph()

                self._approval_engine = ApprovalEngine(
                    llm=llm,
                    memory_service=memory_service,
                    feishu_client=feishu_client,
                    approval_graph=approval_graph
                )

                logger.info("[SubmitReimbursementTool] ApprovalEngine 初始化完成")

            except Exception as e:
                logger.error(f"[SubmitReimbursementTool] ApprovalEngine 初始化失败: {e}")
                raise RuntimeError(f"ApprovalEngine 初始化失败: {e}")

        self._initialized = True

    def _run(
        self,
        user_id: str,
        query: str,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        执行报销申请提交

        Args:
            user_id: 用户ID
            query: 报销申请描述
            conversation_id: 会话ID（可选）
            **kwargs: 其他参数

        Returns:
            审批结果文本
        """
        # 参数验证
        if not user_id or not user_id.strip():
            raise ValueError("user_id 不能为空")

        if not query or not query.strip():
            raise ValueError("query 不能为空")

        # 使用默认 conversation_id（如果未提供）
        if not conversation_id:
            conversation_id = f"{user_id}_default"

        logger.info(f"[SubmitReimbursementTool] 提交报销申请: user_id={user_id}, query={query}")

        try:
            # 延迟初始化
            self._lazy_init()

            # 调用 ApprovalEngine
            result = self._approval_engine.execute(
                query=query,
                user_id=user_id,
                conversation_id=conversation_id
            )

            # 格式化返回结果
            return self._format_result(result)

        except Exception as e:
            logger.error(f"[SubmitReimbursementTool] 报销申请提交失败: {e}", exc_info=True)
            raise

    def _format_result(self, result: dict) -> str:
        """
        格式化审批结果

        Args:
            result: ApprovalEngine 返回的结果字典

        Returns:
            格式化的文本结果
        """
        status = result.get("status", "unknown")
        approval_id = result.get("approval_id", "未知")
        message = result.get("message", "")

        if status == "approved":
            return f"✅ 审批通过\n\n审批单号：{approval_id}\n{message}"
        elif status == "pending":
            return f"⏳ 待审批\n\n审批单号：{approval_id}\n{message}"
        elif status == "rejected":
            return f"❌ 审批拒绝\n\n审批单号：{approval_id}\n{message}"
        else:
            return f"审批单号：{approval_id}\n状态：{status}\n{message}"


# 创建全局单例（延迟初始化）
_submit_reimbursement_tool_instance: Optional[SubmitReimbursementTool] = None


def get_submit_reimbursement_tool(approval_engine=None) -> SubmitReimbursementTool:
    """
    获取提交报销工具单例

    Args:
        approval_engine: 可选的 ApprovalEngine 实例

    Returns:
        SubmitReimbursementTool 实例
    """
    global _submit_reimbursement_tool_instance

    if _submit_reimbursement_tool_instance is None:
        _submit_reimbursement_tool_instance = SubmitReimbursementTool(
            approval_engine=approval_engine
        )

    return _submit_reimbursement_tool_instance

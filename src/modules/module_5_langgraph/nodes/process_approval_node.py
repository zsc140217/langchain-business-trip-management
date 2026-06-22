"""
处理审批结果节点：根据审批状态生成最终响应
T1.4核心实现
"""
from typing import Dict, Any
import logging
from ..state import TravelAgentState

logger = logging.getLogger(__name__)


def process_approval_node(state: TravelAgentState) -> Dict[str, Any]:
    """
    处理审批结果

    根据 approval_status 决定：
    - approved: 继续执行后续流程
    - rejected: 终止流程并返回拒绝消息

    Args:
        state: 当前状态

    Returns:
        answer: 审批结果说明
    """
    status = state.get("approval_status")
    reasons = state.get("approval_reason", [])
    query = state.get("query", "")

    if status == "approved":
        logger.info("✅ 审批通过，继续处理")
        message = f"✅ 审批通过\n\n触发原因：\n" + "\n".join(f"- {r}" for r in reasons)
        message += f"\n\n您的查询「{query}」将继续处理..."

        return {
            "answer": message
        }
    else:
        logger.warning("❌ 审批被拒绝，终止流程")
        message = f"❌ 审批被拒绝\n\n触发原因：\n" + "\n".join(f"- {r}" for r in reasons)
        message += f"\n\n您的查询「{query}」已终止。"

        return {
            "answer": message
        }

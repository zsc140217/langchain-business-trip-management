"""
人工审批节点：使用interrupt()暂停执行等待人工决策
T1.4核心实现
"""
from typing import Dict, Any
import logging
from langgraph.types import interrupt
from ..state import TravelAgentState

logger = logging.getLogger(__name__)


def approval_node(state: TravelAgentState) -> Dict[str, Any]:
    """
    人工审批节点

    使用 interrupt() 暂停执行，等待外部提供审批决策
    图必须有 checkpointer 才能使用 interrupt

    Args:
        state: 当前状态

    Returns:
        approval_status: "approved" 或 "rejected"
    """
    logger.info("⏸️  等待人工审批...")

    # 构建审批提示信息
    approval_prompt = {
        "question": "差旅申请需要人工审批",
        "query": state.get("query", ""),
        "reasons": state.get("approval_reason", []),
        "instruction": "请输入决策: 'approve' 批准 或 'reject' 拒绝"
    }

    # 核心：使用 interrupt() 暂停执行
    # 图会在此处中断，等待外部调用 graph.invoke() 提供输入
    decision = interrupt(approval_prompt)

    # 解析决策（支持多种输入格式）
    approved = decision in ["approve", "approved", "yes", True]

    status = "approved" if approved else "rejected"
    logger.info(f"{'[OK]' if approved else '[ERROR]'} 审批结果：{status}")

    return {
        "approval_status": status
    }

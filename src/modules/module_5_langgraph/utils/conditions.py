"""
条件判断函数
用于LangGraph的conditional_edges
"""
from typing import Literal
import logging
from ..state import TravelAgentState

logger = logging.getLogger(__name__)


def should_continue(state: TravelAgentState) -> Literal["tools", "end"]:
    """
    判断是否继续执行工具调用

    ReAct循环的关键：检查是否有待执行的tool_calls

    Args:
        state: 当前状态

    Returns:
        "tools" - 有tool_calls，执行工具
        "end" - 无tool_calls，结束循环
    """
    # 检查迭代次数限制
    if state["iteration"] >= state["max_iterations"]:
        logger.warning(f"达到最大迭代次数 {state['max_iterations']}，强制结束")
        return "end"

    # 检查是否有待执行的工具调用
    tool_calls = state.get("tool_calls", [])
    if tool_calls and len(tool_calls) > 0:
        logger.info(f"发现 {len(tool_calls)} 个工具调用，继续执行")
        return "tools"

    logger.info("无工具调用，结束循环")
    return "end"


def needs_approval(state: TravelAgentState) -> Literal["approval", "agent"]:
    """
    判断是否需要人工审批

    用于check_approval节点后的条件路由

    Args:
        state: 当前状态

    Returns:
        "approval" - 需要审批，进入审批流程
        "agent" - 无需审批，直接进入agent节点
    """
    if state.get("approval_required", False):
        logger.info("→ 路由到审批节点")
        return "approval"

    logger.info("→ 路由到agent节点")
    return "agent"


def after_approval(state: TravelAgentState) -> Literal["agent", "end"]:
    """
    审批后的路由判断

    Args:
        state: 当前状态

    Returns:
        "agent" - 审批通过，继续执行
        "end" - 审批拒绝，直接结束
    """
    status = state.get("approval_status")

    if status == "rejected":
        logger.info("→ 审批拒绝，结束流程")
        return "end"

    logger.info("→ 审批通过，继续执行")
    return "agent"

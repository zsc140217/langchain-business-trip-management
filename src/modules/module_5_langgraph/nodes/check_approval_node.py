"""
检查审批节点：判断是否需要人工审批
T1.4核心实现
"""
from typing import Dict, Any
import logging
import re
from ..state import TravelAgentState

logger = logging.getLogger(__name__)


def check_approval_node(state: TravelAgentState) -> Dict[str, Any]:
    """
    检查是否需要人工审批

    触发审批的条件：
    1. 超预算：住宿标准高（五星/豪华等关键词）
    2. 超天数：出差天数 > 5天
    3. 特殊城市：国际出差

    Args:
        state: 当前状态

    Returns:
        approval_required, approval_reason, approval_status
    """
    logger.info("🔍 检查是否需要审批...")

    reasons = []
    query = state.get("query", "")

    # 规则1: 检查住宿预算（高级关键词）
    high_budget_keywords = ["五星", "豪华", "高级", "奢华", "顶级"]
    if any(keyword in query for keyword in high_budget_keywords):
        reasons.append("住宿标准超出预算（五星级/豪华酒店需审批）")

    # 规则2: 检查出差天数
    days_match = re.search(r'(\d+)天', query)
    if days_match:
        days = int(days_match.group(1))
        if days > 5:
            reasons.append(f"出差天数超限（{days}天 > 5天标准）")

    # 规则3: 检查国际出差
    international_cities = ["东京", "首尔", "新加坡", "纽约", "伦敦", "巴黎"]
    if any(city in query for city in international_cities):
        reasons.append("国际出差需要审批")

    approval_needed = len(reasons) > 0

    if approval_needed:
        logger.warning(f"⚠️  需要审批，原因：{reasons}")
    else:
        logger.info("✅ 无需审批，继续执行")

    return {
        "approval_required": approval_needed,
        "approval_reason": reasons,
        "approval_status": "pending" if approval_needed else None
    }

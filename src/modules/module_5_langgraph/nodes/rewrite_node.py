"""
查询改写节点
将口语化查询改写为标准检索查询
"""
from typing import Dict, Any
import logging
from ..state import TravelAgentState

logger = logging.getLogger(__name__)


def rewrite_node(state: TravelAgentState) -> Dict[str, Any]:
    """
    查询改写节点：优化用户查询用于检索
    
    口语化 → 标准化
    例如："我想去上海玩3天" → "上海差旅住宿标准 3天"
    
    Args:
        state: 当前状态
        
    Returns:
        包含rewritten_query字段的字典
    """
    query = state["query"]
    
    # 简化版：直接返回原查询（可选集成EnterpriseQueryRewriter）
    # 如果需要LLM改写，在这里调用query_rewriter
    
    logger.info(f"[刷新] 查询改写节点：'{query}'")
    logger.info(f"   保持原查询（简化实现）")
    
    return {
        "rewritten_query": query  # 简化：直接使用原查询
    }

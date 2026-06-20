"""
工具执行节点
执行Agent生成的tool_calls
"""
from typing import Dict, Any
import logging
from ..state import TravelAgentState
from langchain_core.messages import ToolMessage

logger = logging.getLogger(__name__)


def tools_node(state: TravelAgentState) -> Dict[str, Any]:
    """
    工具执行节点：执行所有待处理的tool_calls
    
    这是ReAct的"Acting"部分
    
    Args:
        state: 当前状态
        
    Returns:
        工具执行结果（ToolMessage列表）
    """
    tool_calls = state.get("tool_calls", [])
    
    if not tool_calls:
        logger.warning("⚠️  工具节点被调用但没有tool_calls")
        return {"messages": [], "tool_calls": []}
    
    logger.info(f"🔧 工具执行节点：执行 {len(tool_calls)} 个工具")
    
    tool_messages = []
    
    # 简化实现：模拟工具执行
    for i, tool_call in enumerate(tool_calls, 1):
        tool_name = tool_call.get('name', 'unknown')
        tool_args = tool_call.get('args', {})
        tool_id = tool_call.get('id', f'call_{i}')
        
        logger.info(f"   执行工具 {i}: {tool_name}({tool_args})")
        
        # 模拟结果
        result = f"工具 {tool_name} 执行结果（模拟）"
        
        tool_messages.append(ToolMessage(
            content=result,
            tool_call_id=tool_id
        ))
    
    logger.info(f"✅ 工具执行完成，返回 {len(tool_messages)} 个结果")
    
    return {
        "messages": tool_messages,
        "tool_calls": []  # 清空，等待下次agent决策
    }

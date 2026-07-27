"""
工具执行节点
执行Agent生成的tool_calls
"""
from typing import Dict, Any
import logging
from ..state import TravelAgentState
from langchain_core.messages import ToolMessage

logger = logging.getLogger(__name__)


def create_tool_map():
    """
    创建工具名称到工具函数的映射

    Returns:
        工具映射字典
    """
    from src.modules.module_3_react_agent.tools import get_all_tools

    tools = get_all_tools()
    return {tool.name: tool for tool in tools}


def tools_node(state: TravelAgentState) -> Dict[str, Any]:
    """
    工具执行节点：执行所有待处理的tool_calls（真实版本）

    这是ReAct的"Acting"部分

    Args:
        state: 当前状态

    Returns:
        工具执行结果（ToolMessage列表）
    """
    tool_calls = state.get("tool_calls", [])

    if not tool_calls:
        logger.warning("[WARNING]  工具节点被调用但没有tool_calls")
        return {"messages": [], "tool_calls": []}

    logger.info(f"[工具] 工具执行节点：执行 {len(tool_calls)} 个工具")

    # 创建工具映射
    tool_map = create_tool_map()

    tool_messages = []

    # 真实执行工具
    for i, tool_call in enumerate(tool_calls, 1):
        tool_name = tool_call.get('name', 'unknown')
        tool_args = tool_call.get('args', {})
        tool_id = tool_call.get('id', f'call_{i}')

        logger.info(f"   执行工具 {i}: {tool_name}({tool_args})")

        try:
            # 检查工具是否存在
            if tool_name not in tool_map:
                error_msg = f"工具 '{tool_name}' 不存在。可用工具：{list(tool_map.keys())}"
                logger.error(f"[ERROR] {error_msg}")

                tool_messages.append(ToolMessage(
                    content=error_msg,
                    tool_call_id=tool_id,
                    name=tool_name
                ))
                continue

            # 真实执行工具
            tool_func = tool_map[tool_name]
            result = tool_func.invoke(tool_args)

            logger.info(f"[OK] 工具执行成功：{tool_name} → {str(result)[:100]}...")

            tool_messages.append(ToolMessage(
                content=str(result),
                tool_call_id=tool_id,
                name=tool_name
            ))

        except Exception as e:
            error_msg = f"工具执行失败：{str(e)}"
            logger.error(f"[ERROR] {tool_name} - {error_msg}")

            tool_messages.append(ToolMessage(
                content=error_msg,
                tool_call_id=tool_id,
                name=tool_name
            ))

    logger.info(f"[OK] 工具执行完成，返回 {len(tool_messages)} 个结果")

    return {
        "messages": tool_messages,
        "tool_calls": []  # 清空，等待下次agent决策
    }

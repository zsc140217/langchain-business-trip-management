"""
Agent节点：LLM推理和工具调用决策
ReAct模式的Think步骤
"""
from typing import Dict, Any, List
import logging
from ..state import TravelAgentState
from src.models.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

logger = logging.getLogger(__name__)

REACT_SYSTEM_PROMPT = """你是一个企业差旅政策助手Agent。

你可以使用以下工具获取信息（如果需要）：
- query_weather：查询城市实时天气
- get_weather_forecast：查询未来天气预报
- search_flights：搜索航班信息
- get_flight_price：查询航班价格
- search_hotels：搜索酒店
- get_hotel_details：查询酒店详情

工作流程：
1. 分析用户问题
2. 判断是否需要更多信息
3. 如果需要，调用工具获取信息
4. 基于所有信息给出最终答案

注意：
- 优先基于检索到的文档回答
- 如果已有足够信息，直接回答，不要调用工具
- 每次只调用必要的工具
"""


def extract_tool_calls(response: AIMessage) -> List[Dict[str, Any]]:
    """
    从LLM响应中提取tool_calls

    Args:
        response: LLM的AIMessage响应

    Returns:
        工具调用列表，每个元素包含 name, args, id
    """
    if not hasattr(response, 'tool_calls') or not response.tool_calls:
        return []

    tool_calls = []
    for tc in response.tool_calls:
        tool_calls.append({
            "name": tc["name"],
            "args": tc["args"],
            "id": tc["id"]
        })

    return tool_calls


def agent_node(state: TravelAgentState) -> Dict[str, Any]:
    """
    Agent推理节点：决定下一步行动（真实LLM版本）

    这是ReAct的"Reasoning"部分
    - 分析当前状态
    - 决定是否需要调用工具
    - 或直接生成答案

    Args:
        state: 当前状态

    Returns:
        更新的messages、tool_calls、iteration
    """
    logger.info(f"🤔 Agent推理节点（迭代 {state['iteration'] + 1}/{state['max_iterations']}）")

    try:
        # 获取LLM并绑定工具
        llm = get_llm(temperature=0.7)

        # 导入工具
        from src.modules.module_3_react_agent.tools import get_all_tools
        tools = get_all_tools()

        # 绑定工具到LLM
        llm_with_tools = llm.bind_tools(tools)

        # 构建消息历史
        messages = state.get("messages", [])
        if not messages:
            # 首次调用：添加系统提示和用户查询
            system_msg = SystemMessage(content=REACT_SYSTEM_PROMPT)

            # 包含检索到的文档
            context = ""
            if state.get("documents"):
                context = "\n\n相关政策文档：\n"
                for i, doc in enumerate(state["documents"][:3], 1):
                    context += f"\n文档{i}:\n{doc.page_content}\n"

            user_content = f"{context}\n\n用户问题：{state['query']}"
            human_msg = HumanMessage(content=user_content)
            messages = [system_msg, human_msg]

        # 调用LLM
        response = llm_with_tools.invoke(messages)

        # 提取tool_calls
        tool_calls = extract_tool_calls(response)

        logger.info(f"[OK] Agent决策完成：{'生成答案' if not tool_calls else f'{len(tool_calls)}个工具调用'}")

        return {
            "messages": [response],
            "tool_calls": tool_calls,
            "iteration": state["iteration"] + 1
        }

    except Exception as e:
        logger.error(f"[ERROR] Agent节点执行失败：{e}")
        # 降级处理：返回Mock响应
        mock_response = AIMessage(content=f"抱歉，我遇到了一些技术问题。基于已有信息回答您的问题：{state.get('query', '')}")

        return {
            "messages": [mock_response],
            "tool_calls": [],
            "iteration": state["iteration"] + 1
        }

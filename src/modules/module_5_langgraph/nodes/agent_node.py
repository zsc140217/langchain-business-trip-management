"""
Agent节点：LLM推理和工具调用决策
ReAct模式的Think步骤
"""
from typing import Dict, Any
import logging
from ..state import TravelAgentState
from src.models.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

logger = logging.getLogger(__name__)

REACT_SYSTEM_PROMPT = """你是一个企业差旅政策助手Agent。

你可以使用以下工具获取信息（如果需要）：
- 检索工具：查询差旅政策文档
- 分析工具：对比不同城市的标准

工作流程：
1. 分析用户问题
2. 判断是否需要更多信息
3. 如果需要，调用工具获取信息
4. 基于所有信息给出最终答案

注意：
- 基于检索到的文档回答，不要编造
- 如果已有足够信息，直接回答，不要调用工具
- 每次只调用必要的工具
"""


def agent_node(state: TravelAgentState) -> Dict[str, Any]:
    """
    Agent推理节点：决定下一步行动
    
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
    
    # 获取LLM（简化：不绑定工具，因为需要工具定义）
    llm = get_llm(temperature=0.7)
    
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
    
    # 简化实现：模拟LLM响应（避免API调用问题）
    # 生产环境中，这里应该调用真实的LLM
    mock_response = AIMessage(content=f"我已分析您的问题：{state['query']}")

    # 简化：不生成tool_calls，直接进入answer阶段
    tool_calls = []

    logger.info(f"✅ Agent决策完成：{'生成答案' if not tool_calls else f'{len(tool_calls)}个工具调用'}")

    return {
        "messages": [mock_response],
        "tool_calls": tool_calls,
        "iteration": state["iteration"] + 1
    }

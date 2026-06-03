"""
简化版 ReAct Agent - 使用 LangChain 最新 API

由于 create_react_agent 和 AgentExecutor 已被移除，
这里使用简化的工具调用方式
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatTongyi
from langchain_core.tools import tool
from typing import List
import os


def create_simple_agent_executor(tools: List, llm=None, verbose: bool = True):
    """
    创建简化的 Agent 执行器
    
    使用 LLM 的工具调用能力直接实现 Agent 功能
    """
    if llm is None:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("未找到DASHSCOPE_API_KEY环境变量")
        
        llm = ChatTongyi(
            model_name="qwen-plus",
            dashscope_api_key=api_key,
            temperature=0.7,
        )
    
    # 绑定工具到 LLM
    llm_with_tools = llm.bind_tools(tools)
    
    return llm_with_tools


def run_agent_simple(query: str, tools: List, llm=None, verbose: bool = True) -> dict:
    """
    简化的 Agent 执行
    """
    agent = create_simple_agent_executor(tools, llm, verbose)
    
    # 创建消息
    from langchain_core.messages import HumanMessage
    
    messages = [HumanMessage(content=query)]
    result = agent.invoke(messages)
    
    return {"output": result.content}


# 兼容接口
create_react_agent_with_tools = create_simple_agent_executor
run_react_agent = run_agent_simple

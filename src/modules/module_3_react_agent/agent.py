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
    简化的 Agent 执行 - 支持多轮工具调用
    """
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

    # 创建 LLM
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

    # 创建工具映射
    tool_map = {tool.name: tool for tool in tools}

    # 初始化消息列表
    messages = [HumanMessage(content=query)]

    # 执行 Agent 循环（最多10轮）
    intermediate_steps = []
    max_iterations = 10

    for i in range(max_iterations):
        if verbose:
            print(f"\n{'='*60}")
            print(f"第 {i+1} 轮推理")
            print(f"{'='*60}")

        # 调用 LLM
        response = llm_with_tools.invoke(messages)

        if verbose:
            print(f"\n💭 LLM 响应:")
            if hasattr(response, 'content') and response.content:
                print(f"   内容: {response.content[:200]}")

        # 检查是否有工具调用
        if not hasattr(response, 'tool_calls') or not response.tool_calls:
            # 没有工具调用，返回最终答案
            if verbose:
                print(f"\n✅ Agent 完成推理，返回最终答案")
            return {
                "output": response.content,
                "intermediate_steps": intermediate_steps
            }

        # 执行工具调用
        messages.append(response)

        for tool_call in response.tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']

            if verbose:
                print(f"\n🔧 调用工具: {tool_name}")
                print(f"   参数: {tool_args}")

            # 执行工具
            if tool_name in tool_map:
                try:
                    tool_result = tool_map[tool_name].invoke(tool_args)
                    if verbose:
                        print(f"   结果: {tool_result[:200]}...")

                    # 记录中间步骤
                    intermediate_steps.append((tool_name, tool_args, tool_result))

                    # 添加工具结果到消息列表
                    messages.append(ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call['id']
                    ))
                except Exception as e:
                    error_msg = f"工具执行错误: {str(e)}"
                    if verbose:
                        print(f"   ❌ {error_msg}")
                    messages.append(ToolMessage(
                        content=error_msg,
                        tool_call_id=tool_call['id']
                    ))
            else:
                error_msg = f"未找到工具: {tool_name}"
                if verbose:
                    print(f"   ❌ {error_msg}")
                messages.append(ToolMessage(
                    content=error_msg,
                    tool_call_id=tool_call['id']
                ))

    # 达到最大迭代次数
    if verbose:
        print(f"\n⚠️  达到最大迭代次数 ({max_iterations})")

    return {
        "output": "抱歉，任务太复杂，无法在限定步骤内完成。",
        "intermediate_steps": intermediate_steps
    }


# 兼容接口
create_react_agent_with_tools = create_simple_agent_executor
run_react_agent = run_agent_simple

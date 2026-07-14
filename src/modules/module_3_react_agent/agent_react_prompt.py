"""
基于Prompt工程的ReAct Agent实现
适用于不完全支持工具调用的LLM（如通义千问）
"""
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Any
import os
import re
import json


REACT_SYSTEM_PROMPT = """你是一个智能助手，可以使用工具来回答用户问题。

你有以下工具可用：
{tool_descriptions}

使用 ReAct 模式思考：

1. Thought（思考）：分析问题，决定下一步做什么
2. Action（行动）：选择一个工具并指定参数
   格式：Action: 工具名
   参数：{{"参数名": "参数值"}}
3. Observation（观察）：查看工具执行结果
4. 重复上述步骤直到得到最终答案
5. Final Answer（最终答案）：给出完整答案

示例：

Question: 北京今天天气怎么样？

Thought: 用户想知道北京的实时天气，我需要使用 query_weather 工具
Action: query_weather
参数: {{"city": "北京"}}

Observation: 📍 北京实时天气：晴天，25°C

Thought: 我已经获得了北京的天气信息，可以给出最终答案了
Final Answer: 北京今天天气晴朗，气温25°C，适合出行。

现在开始！记住：
- 每次只执行一个Action
- 必须等待Observation后才能继续
- 参数必须是有效的JSON格式
- 最后用"Final Answer:"给出完整答案
"""


def format_tool_descriptions(tools: List) -> str:
    """格式化工具描述"""
    descriptions = []
    for tool in tools:
        desc = f"- {tool.name}: {tool.description}\n"
        desc += f"  参数: {json.dumps(tool.args, ensure_ascii=False)}"
        descriptions.append(desc)
    return "\n\n".join(descriptions)


def parse_action(text: str) -> tuple[str, dict]:
    """
    从LLM输出中解析Action和参数

    返回: (action_name, action_args)
    """
    # 查找 Action: 工具名
    action_match = re.search(r'Action:\s*(\w+)', text)
    if not action_match:
        return None, None

    action_name = action_match.group(1)

    # 查找参数（JSON格式）
    params_match = re.search(r'参数[:：]\s*(\{[^}]+\})', text)
    if not params_match:
        return action_name, {}

    try:
        params_str = params_match.group(1)
        action_args = json.loads(params_str)
        return action_name, action_args
    except json.JSONDecodeError:
        return action_name, {}


def run_react_agent_with_prompt(
    query: str,
    tools: List,
    llm=None,
    verbose: bool = True,
    max_iterations: int = 10
) -> dict:
    """
    使用Prompt工程实现ReAct Agent
    """
    # 创建LLM
    if llm is None:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("未找到DASHSCOPE_API_KEY环境变量")

        llm = ChatTongyi(
            model_name="qwen-plus",
            dashscope_api_key=api_key,
            temperature=0.7,
        )

    # 创建工具映射
    tool_map = {tool.name: tool for tool in tools}

    # 格式化系统提示
    system_prompt = REACT_SYSTEM_PROMPT.format(
        tool_descriptions=format_tool_descriptions(tools)
    )

    # 初始化对话历史
    conversation_history = []
    intermediate_steps = []

    # 开始ReAct循环
    current_input = f"Question: {query}"

    for iteration in range(max_iterations):
        if verbose:
            print(f"\n{'='*60}")
            print(f"第 {iteration + 1} 轮推理")
            print(f"{'='*60}")

        # 构建完整的提示
        full_prompt = system_prompt + "\n\n" + "\n\n".join(conversation_history) + "\n\n" + current_input

        # 调用LLM
        response = llm.invoke(full_prompt)
        response_text = response.content

        if verbose:
            print(f"\n💭 LLM 响应:")
            print(response_text)

        # 将响应加入历史
        conversation_history.append(current_input)
        conversation_history.append(response_text)

        # 检查是否完成
        if "Final Answer:" in response_text or "最终答案：" in response_text:
            # 提取最终答案
            final_answer = response_text.split("Final Answer:")[-1].strip()
            if not final_answer:
                final_answer = response_text.split("最终答案：")[-1].strip()

            if verbose:
                print(f"\n✅ Agent 完成，返回最终答案")

            return {
                "output": final_answer,
                "intermediate_steps": intermediate_steps
            }

        # 解析Action
        action_name, action_args = parse_action(response_text)

        if not action_name:
            if verbose:
                print(f"\n⚠️  未找到有效的Action，继续下一轮")
            current_input = "请明确指定要使用的工具。格式：Action: 工具名\\n参数: {{...}}"
            continue

        # 执行工具
        if action_name not in tool_map:
            observation = f"❌ 错误：工具 '{action_name}' 不存在。可用工具：{', '.join(tool_map.keys())}"
            if verbose:
                print(f"\n{observation}")
        else:
            try:
                if verbose:
                    print(f"\n[工具] 执行工具: {action_name}")
                    print(f"   参数: {action_args}")

                tool_result = tool_map[action_name].invoke(action_args)
                observation = f"Observation: {tool_result}"

                # 记录中间步骤
                intermediate_steps.append((action_name, action_args, tool_result))

                if verbose:
                    print(f"\n📊 工具结果:")
                    print(tool_result[:300] + "..." if len(tool_result) > 300 else tool_result)

            except Exception as e:
                observation = f"Observation: ❌ 工具执行错误：{str(e)}"
                if verbose:
                    print(f"\n{observation}")

        # 准备下一轮输入
        current_input = observation

    # 达到最大迭代次数
    if verbose:
        print(f"\n⚠️  达到最大迭代次数 ({max_iterations})")

    return {
        "output": "抱歉，任务太复杂，无法在限定步骤内完成。请尝试简化问题。",
        "intermediate_steps": intermediate_steps
    }


# 兼容接口
def create_react_agent_with_tools(tools: List, llm=None, verbose: bool = True):
    """兼容接口"""
    return lambda query: run_react_agent_with_prompt(query, tools, llm, verbose)


def run_react_agent(query: str, tools: List, llm=None, verbose: bool = True) -> dict:
    """兼容接口"""
    return run_react_agent_with_prompt(query, tools, llm, verbose)

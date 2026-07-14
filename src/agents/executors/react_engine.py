"""
ReactEngine - ReAct 循环推理引擎

职责：
1. 使用 ReAct (Reasoning + Acting) 模式处理开放式查询
2. 支持多轮工具调用和推理
3. 适用于比较、推荐、评价类问题

对应架构文档：
- 通道类型：开放通道（OPEN）
- 适用场景：比较/推荐/评价类问题
- 示例："飞机和高铁哪个划算"、"夏天适合去哪里出差"
"""
from typing import Dict, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import logging

logger = logging.getLogger(__name__)


class ReactEngine:
    """
    ReAct 循环推理引擎

    使用 ReAct 模式处理开放式查询：
    1. Reasoning - LLM 分析问题，决定下一步行动
    2. Acting - 调用工具获取信息
    3. 循环迭代直到得出最终答案
    """

    def __init__(
        self,
        llm,
        tools: Dict,
        max_iterations: int = 5
    ):
        """
        初始化 ReAct 引擎

        Args:
            llm: 语言模型
            tools: 工具字典 {tool_name: tool}
            max_iterations: 最大迭代次数（防止死循环）
        """
        self.llm = llm
        self.tools = tools
        self.max_iterations = max_iterations

        # 转换工具为 LangChain 格式并绑定到 LLM
        langchain_tools = self._convert_tools_to_langchain_format()
        self.llm_with_tools = llm.bind_tools(langchain_tools)

    def execute(
        self,
        query: str,
        context: Optional[str] = None,
        max_iterations: Optional[int] = None
    ) -> str:
        """
        执行 ReAct 循环推理

        流程：
        1. 初始化消息列表
        2. 循环：LLM 推理 → 工具调用 → 继续推理
        3. 返回最终答案

        Args:
            query: 用户查询
            context: 上下文信息（可选）
            max_iterations: 最大迭代次数（覆盖默认值）

        Returns:
            最终答案
        """
        logger.info(f"[ReactEngine] 开始 ReAct 推理: {query}")

        max_iter = max_iterations or self.max_iterations

        # 构建初始提示
        initial_prompt = self._build_initial_prompt(query, context)

        # 初始化消息列表
        messages = [HumanMessage(content=initial_prompt)]

        # 中间步骤记录
        intermediate_steps = []

        try:
            # ReAct 循环
            for iteration in range(max_iter):
                logger.info(f"[ReactEngine] 第 {iteration + 1} 轮推理")

                # 调用 LLM
                response = self.llm_with_tools.invoke(messages)

                # 检查是否有工具调用
                if not hasattr(response, 'tool_calls') or not response.tool_calls:
                    # 没有工具调用，返回最终答案
                    logger.info("[ReactEngine] LLM 返回最终答案")
                    return self._format_final_answer(
                        response.content,
                        intermediate_steps
                    )

                # 将 LLM 响应添加到消息列表
                messages.append(response)

                # 执行工具调用
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']

                    logger.info(f"[ReactEngine] 调用工具: {tool_name}({tool_args})")

                    # 执行工具
                    tool_result = self._execute_tool(tool_name, tool_args)

                    # 记录中间步骤
                    intermediate_steps.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": tool_result
                    })

                    # 添加工具结果到消息列表
                    messages.append(ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call['id']
                    ))

            # 达到最大迭代次数
            logger.warning(f"[ReactEngine] 达到最大迭代次数 {max_iter}")
            return self._build_fallback_answer(query, intermediate_steps)

        except Exception as e:
            logger.error(f"[ReactEngine] 执行失败: {e}", exc_info=True)
            return f"抱歉，推理过程中出现错误：{str(e)}"

    def _build_initial_prompt(self, query: str, context: Optional[str]) -> str:
        """
        构建初始提示词

        Args:
            query: 用户查询
            context: 上下文信息

        Returns:
            初始提示词
        """
        prompt = f"""你是一个智能助手，需要通过推理和工具调用来回答用户问题。

用户问题：{query}

"""

        if context:
            prompt += f"上下文信息：\n{context}\n\n"

        prompt += """请按照以下步骤思考：
1. 分析问题需要哪些信息
2. 调用合适的工具获取信息
3. 基于获取的信息进行推理
4. 如果信息足够，给出最终答案；否则继续获取信息

你可以调用工具获取实时信息，也可以基于常识进行推理。
"""

        return prompt

    def _execute_tool(self, tool_name: str, tool_args: dict) -> str:
        """
        执行工具调用

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            工具执行结果
        """
        try:
            if tool_name not in self.tools:
                logger.warning(f"[ReactEngine] 工具 {tool_name} 不存在")
                return f"工具 {tool_name} 不可用"

            tool = self.tools[tool_name]

            # 执行工具
            result = tool.invoke(tool_args)

            logger.info(f"[ReactEngine] 工具 {tool_name} 执行成功")
            return result

        except Exception as e:
            logger.error(f"[ReactEngine] 工具 {tool_name} 执行失败: {e}")
            return f"工具执行错误: {str(e)}"

    def _convert_tools_to_langchain_format(self) -> List:
        """
        将工具转换为 LangChain 格式

        Returns:
            LangChain 工具列表
        """
        langchain_tools = []

        for tool_name, tool in self.tools.items():
            try:
                # 如果工具已经是 LangChain 格式，直接使用
                if hasattr(tool, 'name') and hasattr(tool, 'description'):
                    langchain_tools.append(tool)
                # 如果工具有 to_langchain_tool 方法，调用转换
                elif hasattr(tool, 'to_langchain_tool'):
                    langchain_tools.append(tool.to_langchain_tool())
                else:
                    logger.warning(f"[ReactEngine] 工具 {tool_name} 不支持 LangChain 格式")

            except Exception as e:
                logger.warning(f"[ReactEngine] 转换工具 {tool_name} 失败: {e}")

        logger.info(f"[ReactEngine] 转换了 {len(langchain_tools)} 个工具")
        return langchain_tools

    def _format_final_answer(
        self,
        answer: str,
        intermediate_steps: List[dict]
    ) -> str:
        """
        格式化最终答案

        Args:
            answer: LLM 返回的答案
            intermediate_steps: 中间步骤

        Returns:
            格式化后的答案
        """
        # 直接返回 LLM 的答案
        return answer

    def _build_fallback_answer(
        self,
        query: str,
        intermediate_steps: List[dict]
    ) -> str:
        """
        构建降级答案（达到最大迭代次数时）

        Args:
            query: 原始查询
            intermediate_steps: 中间步骤

        Returns:
            降级答案
        """
        if not intermediate_steps:
            return "抱歉，我无法在限定步骤内完成这个任务，请尝试简化您的问题。"

        # 基于中间步骤构建答案
        fallback = f"根据您的问题「{query}」，我收集到以下信息：\n\n"

        for step in intermediate_steps:
            tool_name = step['tool']
            result = step['result']
            fallback += f"• {tool_name}: {result}\n"

        fallback += "\n虽然我还没有完全理解这些信息的关联，但希望这些数据对您有帮助。"

        return fallback
